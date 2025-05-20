import pandas as pd
import os
from config import *
from util import *
import re
import csv

def read_google_sheets(sheets):
    """Read all sheets into a dictionary of DataFrames, selecting only needed columns."""
    dfs = {}
    for key, meta in sheets.items():
        df = read_gsheet(
            sheet_id=meta["sheet_id"],
            sheet_name=meta["sheet_name"],
            indir=indir,
            out_csv=f"{key}.csv"
        )
        dfs[key] = df[meta["columns"]]
    return dfs

def process_sessions(dfs):
    """Process presenter and organizer columns for all relevant sheets."""
    # --- Plenary abstracts
    df = dfs["plenary_abstracts"].copy()
    df["IsSpecialSession"] = 0
    dfs["plenary_abstracts"] = df
    
    # --- Special session submissions
    df = dfs["special_session_submissions"].copy()
    # Process organizer names and institutions
    for idx, i in enumerate(["first", "second", "third"], 1):
        df[f"Organizer{idx}"] = df[f"First or given name(s) of {i} organizer"] + " " + df[f"Last or family name(s) of {i} organizer"]
        df[f"Organizer{idx} institution"] = df[f"Institution of {i} organizer"]
        df = df.drop(columns=[f"First or given name(s) of {i} organizer", f"Last or family name(s) of {i} organizer"])
    
    df = df[~df["Session Title"].str.contains("by Nathan Kirk", case=False, na=False)]
    df["IsSpecialSession"] = 1
    dfs["special_session_submissions"] = df

    assert df["Session Title"].notna().all(), "Special Session Title contains Null values"
    
    # --- Contributed talk submissions
    df = dfs["contributed_talk_submissions"].copy()
    df = df[df["Acceptance"] == "Yes"]
    df["IsSpecialSession"] = 0
    
    # Check for duplicates
    presenter_cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    dupes = df[df.duplicated(subset=presenter_cols, keep=False)]
    if not dupes.empty:  
        print("ERROR: Duplicated records in contributed talk submissions:")
        print(dupes[presenter_cols])
    
    df = df.drop_duplicates(subset=presenter_cols, keep="last") 
    dfs["contributed_talk_submissions"] = df

    return dfs

def add_join_keys(dfs, schedules=None):
    """Add join_key columns to DataFrames for merging."""
    # Add join keys to session data
    if dfs:
        # Special session submissions
        if "special_session_submissions" in dfs:
            dfs["special_session_submissions"]["join_key"] = (
                dfs["special_session_submissions"]["Session Title"].str.strip().str.lower()
            )
        
        # Special session abstracts
        if "special_session_abstracts" in dfs:
            dfs["special_session_abstracts"]["join_key"] = (
                dfs["special_session_abstracts"]["Special Session Title"].str.strip().str.lower()
            )
        
        # Contributed talk submissions
        if "contributed_talk_submissions" in dfs:
            dfs["contributed_talk_submissions"]["join_key"] = (
                dfs["contributed_talk_submissions"]["SESSION"].str.strip().str.lower()
            )
        
        # Plenary abstracts
        if "plenary_abstracts" in dfs:
            df = dfs["plenary_abstracts"]
            df["join_key"] = (df["First or given name(s) of presenter"].str.strip() + " " + 
                            df["Last or family name of presenter"].str.strip()).str.lower()
            dfs["plenary_abstracts"] = df.copy(deep=True)
    
    # Add join keys to schedule data
    if schedules:
        for key, df in schedules.items():
            # Extract plenary speaker names
            df["join_key"] = df.iloc[:, 1].str.extract(r'Plenary Talk by (.+)')[0]
            
            # Extract special session titles
            mask = df.iloc[:, 0].str.contains("Track", na=False) & ~df.iloc[:, 1].str.contains("Technical Session", na=False)
            df.loc[mask, "join_key"] = df.loc[mask].iloc[:, 1]
            
            # Extract technical session IDs
            mask2 = df.iloc[:, 1].str.contains(r'Technical Session \d+ .+', case=False, na=False)
            df.loc[mask2, "join_key"] = df.loc[mask2].iloc[:, 1].str.extract(r'(Technical Session \d+)')[0]
            
            df["join_key"] = df["join_key"].str.strip().str.lower()
            schedules[key] = df
    
    return dfs, schedules

def read_schedule_days(num_days=5):
    """Read schedule_day1.csv ... schedule_dayN.csv into a dictionary."""
    schedules = {}
    for i in range(1, num_days + 1):
        day_df = pd.read_csv(os.path.join(interimdir, f"schedule_day{i}.csv"))
        day_df = clean_df(day_df)
        date = day_df.columns[0]
        day_df.columns = ["SessionTime", "SessionTitle"]
        day_df["SessionTime"] = date + " " + day_df["SessionTime"]
        day_df = day_df[["SessionTime", "SessionTitle"]]
        schedules[f"day{i}"] = day_df
    return schedules

def merge_and_process_schedule(schedule_df, dfs):
    """Merge schedule with session data and assign IDs."""
    # Merge with each dataset
    for key in ["special_session_submissions", "plenary_abstracts"]:
        if key in dfs:
            schedule_df = merge_schedules_sessions(schedule_df, dfs[key])

    # Assign session IDs
    schedule_df = assign_session_ids(schedule_df)
    
    return schedule_df

def merge_schedules_sessions(df, df2):
    """Merge schedule DataFrame with session data using join_key."""
    merge_cols = ["Presenter", "Organizer1", "Organizer2", "Organizer3", "IsSpecialSession", "SessionID"]
    cols_to_merge = [c for c in merge_cols if c in df2.columns]
    
    suffix = "_df2"
    df_merged = df.merge(df2[["join_key"] + cols_to_merge], how="left", on="join_key", suffixes=("", suffix))
    
    # Combine columns from both DataFrames
    for c in cols_to_merge:
        c2 = c + suffix
        if c2 in df_merged.columns:
            df_merged[c] = df_merged[c2].combine_first(df_merged[c]) if c in df_merged.columns else df_merged[c2]
            df_merged = df_merged.drop(columns=[c2])
            
    return df_merged

def assign_session_ids(df):
    """Assign session ID codes based on session type."""
    # Assign Technical Session IDs (T1, T2, etc.)
    df["SessionID"] = df["SessionTitle"].str.extract(
        r'Technical Session (\d+)', flags=re.IGNORECASE
    )[0].apply(lambda x: f"T{x}" if pd.notna(x) else "")

    # Assign Plenary Session IDs (P1, P2, etc.)
    plenary_mask = df["SessionTitle"].str.contains("Plenary", na=False)
    df.loc[plenary_mask, "SessionID"] = [f"P{i+1}" for i in range(plenary_mask.sum())]

    # Assign Special Session IDs (S1, S2, etc.) for missing values
    df["SessionID"] = df["SessionID"].replace("", pd.NA)
    missing_mask = df["SessionID"].isna()
    df.loc[missing_mask, "SessionID"] = [f"S{i+1}" for i in range(missing_mask.sum())]

    return df

def ensure_columns(df, columns_list):
    """Ensure all required columns exist with proper defaults and ordering."""
    # Add missing columns
    for c in columns_list:
        if c not in df.columns:
            df[c] = ""
    
    # Fix special values
    df["IsSpecialSession"] = df["IsSpecialSession"].fillna(0).astype(int)
    df["OrderInSchedule"] = range(1, len(df) + 1)
    
    # Reorder columns
    df = df[columns_list]
    return df

def format_text(text, is_organization=False):
    """Format names or organizations with proper capitalization."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
        
    # Strip whitespace and convert to lowercase
    text = text.strip().lower()
    
    if is_organization:
        # Words that should remain lowercase in organizations
        lowercase_words = ['of', 'and', 'the', 'for', 'in', 'at', 'by', 'with', 'to', 'de', 'del', 'di', 'la', 'el']
        
        words = text.split()
        formatted_words = []
        
        for i, word in enumerate(words):
            # Always capitalize first word and after hyphen
            if i == 0 or '-' in word:
                if '-' in word:
                    subwords = word.split('-')
                    word = '-'.join([sw.capitalize() for sw in subwords])
                else:
                    word = word.capitalize()
            # Keep certain words lowercase unless they're the first word
            elif word in lowercase_words:
                word = word.lower()
            else:
                word = word.capitalize()
                
            formatted_words.append(word)
            
        return ' '.join(formatted_words)
    else:
        # For names: capitalize first letter of each part and after hyphens
        text = re.sub(r'\b\w', lambda m: m.group(0).upper(), text)
        text = re.sub(r'(?<=-)\w', lambda m: m.group(0).upper(), text)
        return text

def apply_corrections(df):
    """Apply manual corrections to names and organizations."""
    # Name corrections
    name_corrections = {
        "Noor Ul Amin": "Noor ul Amin",
        # Add more name corrections as needed
    }
    for old_name, new_name in name_corrections.items():
        df.loc[df["LastName"] == old_name, "LastName"] = new_name
    
    # Organization corrections
    org_corrections = {
        "Work done during C. Huang's Ph.D. studies at Georgia Institute of Technology": "Georgia Institute of Technology",
        "INESC-ID, Rua Alves Redol 9, Lisbon, Portugal 1000-029": "INESC-ID",
        "Department of Mathematical Sciences, Tsinghua University": "Tsinghua University",
        "Illinois Institute of Technology, Department of Applied Mathematics. Sandia National Laboratories.": 
            "Illinois Institute of Technology and Sandia National Laboratories",
        "Department of Statistics, Columbia University": "Columbia University",
        "Department of Mathematics, Univeristy of Washington": "University of Washington",
        "KAUST: King Abdullah University of Science and Technology (KAUST)": "King Abdullah University of Science and Technology",
        "King Abdullah University of Science and Technology (KAUST)": "King Abdullah University of Science and Technology",
        "Istituto Nazionale di Fisica Nucleare (INFN), Laboratori Nazionali del Sud (LNS), Catania, Italy": 
            "Laboratori Nazionali del Sud",
        "Chair of Mathematics for Uncertainty Quantification, Department of Mathematics, RWTH- Aachen University": 
            "RWTH Aachen University",
    }
    for old_org, new_org in org_corrections.items():
        df.loc[df["Organization"] == old_org, "Organization"] = new_org
    
    # Validate data quality
    validate_participant_names(df)
    
    return df

def validate_participant_names(df):
    """Validate participant names and print warnings for issues."""
    mask = (df["FirstName"].str.len() == 1) | (df["LastName"].str.len() == 1)
    if mask.any():
        problem_names = df[mask][["FirstName", "LastName"]].values.tolist()
        for first, last in problem_names:
            print(f"ERROR: Invalid name length for participant: {first} {last}")
    return df

def extract_participants(dfs):
    """Extract participant information from all dataframes."""
    participants = []
    
    # Extract from plenary abstracts
    if "plenary_abstracts" in dfs:
        df = dfs["plenary_abstracts"]
        for _, row in df.iterrows():
            if all(col in df.columns for col in ["First or given name(s) of presenter", "Last or family name of presenter"]):
                participants.append({
                    "FirstName": row["First or given name(s) of presenter"],
                    "LastName": row["Last or family name of presenter"],
                    "SessionID": row.get("SessionID", "P"),
                    "PageNumber": "",
                    "Organization": row.get("Institution of presenter", "")
                })
    
    # Extract from special session submissions
    if "special_session_submissions" in dfs:
        df = dfs["special_session_submissions"]
        
        for idx, row in df.iterrows():
            session_id = row.get("SessionID", f"S{idx+1}")
            
            # Add organizers
            for i in range(1, 4):
                organizer_col = f"Organizer{i}"
                org_col = f"Institution of {'first' if i==1 else 'second' if i==2 else 'third'} organizer"
                if organizer_col in df.columns and pd.notna(row[organizer_col]) and row[organizer_col]:
                    name_parts = row[organizer_col].split()
                    if len(name_parts) >= 2:
                        participants.append({
                            "FirstName": " ".join(name_parts[:-1]),
                            "LastName": name_parts[-1],
                            "SessionID": session_id,
                            "PageNumber": "",
                            "Organization": row.get(org_col, "")
                        })
            
            # Add presenter
            if "Presenter 1 first or given name(s)" in df.columns and "Presenter 1 last or family name(s)" in df.columns:
                participants.append({
                    "FirstName": row["Presenter 1 first or given name(s)"],
                    "LastName": row["Presenter 1 last or family name(s)"],
                    "SessionID": session_id,
                    "PageNumber": "",
                    "Organization": row.get("Presenter 1 institution", "")
                })
    
    # Extract from contributed talks
    if "contributed_talk_submissions" in dfs:
        df = dfs["contributed_talk_submissions"]
        for _, row in df.iterrows():
            if all(col in df.columns for col in ["First or given name(s) of presenter", "Last or family name of presenter"]):
                # Extract session ID from SESSION column
                session_id = ""
                if "SESSION" in row and pd.notna(row["SESSION"]):
                    match = re.search(r'Technical Session (\d+)', str(row["SESSION"]), re.IGNORECASE)
                    if match:
                        session_id = f"T{match.group(1)}"
                
                participants.append({
                    "FirstName": row["First or given name(s) of presenter"],
                    "LastName": row["Last or family name of presenter"],
                    "SessionID": session_id if session_id else row.get("SessionID", ""),
                    "PageNumber": "",
                    "Organization": row.get("Institution of presenter", "")
                })
    
    # Extract from special session abstracts
    if "special_session_abstracts" in dfs:
        df = dfs["special_session_abstracts"]
        for _, row in df.iterrows():
            if all(col in df.columns for col in ["First or given name(s) of presenter", "Last or family name of presenter"]):
                # Try to match with existing special sessions to get proper ID
                session_id = "SS"  # Default
                if "Special Session Title" in row and pd.notna(row["Special Session Title"]):
                    title = row["Special Session Title"].lower().strip()
                    if "special_session_submissions" in dfs:
                        ss_df = dfs["special_session_submissions"]
                        if "Session Title" in ss_df.columns and "SessionID" in ss_df.columns:
                            matches = ss_df[ss_df["Session Title"].str.lower().str.strip() == title]
                            if not matches.empty:
                                session_id = matches.iloc[0].get("SessionID", "SS")
                
                participants.append({
                    "FirstName": row["First or given name(s) of presenter"],
                    "LastName": row["Last or family name of presenter"],
                    "SessionID": session_id,
                    "PageNumber": "",
                    "Organization": row.get("Institution of presenter", "")
                })

    # Process participants data
    df = pd.DataFrame(participants)
    if df.empty:
        return df
        
    # Clean and standardize the data
    df["FirstName"] = df["FirstName"].apply(lambda x: format_text(x, False))
    df["LastName"] = df["LastName"].apply(lambda x: format_text(x, False))
    df["Organization"] = df["Organization"].apply(lambda x: format_text(x, True))
    
    # Apply corrections
    df = apply_corrections(df)
    
    # Remove duplicates and sort
    df = df.drop_duplicates(subset=["FirstName", "LastName", "SessionID"], keep="last")
    df = df.sort_values(by=["LastName", "FirstName"]) # "SessionID", 
    
    return df

if __name__ == '__main__':
    SessionListCols = [
        "SessionID", "SessionTitle", "IsSpecialSession", "Organizer1", "Organizer2", "Organizer3", "Chair",
        "SessionTime", "Room", "OrderInSchedule"
    ]

    # Step 1: Process session data
    sheets = get_sheets_dict()
    dfs = read_google_sheets(sheets)
    dfs = process_sessions(dfs)
    
    # Step 2: Process schedule data
    schedules = read_schedule_days(num_days=5)
    
    # Step 3: Add join keys to all dataframes
    dfs, schedules = add_join_keys(dfs, schedules)
    
    # Step 4: Save intermediate results
    save_dfs(dfs, interimdir, "joined")
    save_dfs(schedules, interimdir, "joined")

    # Step 5: Create and process combined schedule
    schedule_df = pd.concat(schedules.values(), ignore_index=True)
    schedule_df = schedule_df[schedule_df["join_key"].notna()]
    schedule_df = merge_and_process_schedule(schedule_df, dfs)
    
    # Step 6: Format and save final schedule
    final_schedule = ensure_columns(schedule_df, SessionListCols)
    csv_file = os.path.join(outdir, "SessionList.csv")
    final_schedule.to_csv(csv_file, index=False)
    print("Output:", csv_file)
    
    # Step 7: Generate and save participants list
    participants_df = extract_participants(dfs)
    participants_csv = os.path.join(outdir, "Participants.csv")
    participants_df.to_csv(participants_csv, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print("Output:", participants_csv)