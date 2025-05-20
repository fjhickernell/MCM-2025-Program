import pandas as pd
import os
from config import *
from util import *
import re

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
    for idx, i in enumerate(["first", "second", "third"], 1):
        df[f"Organizer{idx}"] = df[f"First or given name(s) of {i} organizer"] + " " + df[f"Last or family name(s) of {i} organizer"]
        df = df.drop(columns=[f"First or given name(s) of {i} organizer", f"Last or family name(s) of {i} organizer"])
    df = df[~df["Session Title"].str.contains("by Nathan Kirk", case=False, na=False)]
    df["IsSpecialSession"] = 1
    dfs["special_session_submissions"] = df

    assert df["Session Title"].notna().all(), "Special Session Title contains Null values"
    
    # --- Contributed talk submissions
    df = dfs["contributed_talk_submissions"].copy()
    df = df[df["Acceptance"] == "Yes"]
    df["IsSpecialSession"] = 0
    presenter_cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    # print duplicated records
    dupes = df[df.duplicated(subset=presenter_cols, keep=False)]
    if not dupes.empty:  
        print("ERROR: Duplicated records in contributed talk submissions:")
        print(dupes[presenter_cols])
    # deduplicate df by first and last names of presenter
    df = df.drop_duplicates(subset=presenter_cols, keep="last") 
    dfs["contributed_talk_submissions"] = df

    return dfs

def add_sessions_join_keys(dfs):
    """Add join_key columns to each DataFrame in dfs."""
    dfs["special_session_submissions"]["join_key"] = (
        dfs["special_session_submissions"]["Session Title"].str.strip().str.lower()
    )
    dfs["special_session_abstracts"]["join_key"] = (
        dfs["special_session_abstracts"]["Special Session Title"].str.strip().str.lower()
    )
    dfs["contributed_talk_submissions"]["join_key"] = (
        dfs["contributed_talk_submissions"]["SESSION"].str.strip().str.lower()
    )

    df = dfs["plenary_abstracts"]
    df["join_key"] = (df["First or given name(s) of presenter"].str.strip() + " " + 
                      df["Last or family name of presenter"].str.strip()).str.lower()
    dfs["plenary_abstracts"] = df.copy(deep=True)
    return dfs

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

def add_schedule_join_keys(schedules):
    """Add join_key column to each schedule DataFrame."""
    for key, df in schedules.items():
        df["join_key"] = df.iloc[:, 1].str.extract(r'Plenary Talk by (.+)')[0]
        mask = df.iloc[:, 0].str.contains("Track", na=False) & ~df.iloc[:, 1].str.contains("Technical Session", na=False)
        df.loc[mask, "join_key"] = df.loc[mask].iloc[:, 1]
        mask2 = df.iloc[:, 1].str.contains(r'Technical Session \d+ .+', case=False, na=False)
        df.loc[mask2, "join_key"] = df.loc[mask2].iloc[:, 1].str.extract(r'(Technical Session \d+)')[0]
        df["join_key"] = df["join_key"].str.strip().str.lower()
        schedules[key] = df
    return schedules

def merge_schedules_sessions(df, df2):
    """Merge all schedule DataFrames with df2 using join_key, and add email columns."""
    merge_cols = ["Presenter", "Organizer1", "Organizer2", "Organizer3", "IsSpecialSession", "SessionID"]
    cols_to_merge = [c for c in merge_cols if c in df2.columns]
    suffix = "_df2"
    df_merged = df.merge(df2[["join_key"] + cols_to_merge], how="left", on="join_key", suffixes=("", suffix))
    for c in cols_to_merge:
        c2 = c + suffix
        if c2 in df_merged.columns:
            df_merged[c] = df_merged[c2].combine_first(df_merged[c]) if c in df_merged.columns else df_merged[c2]
            df_merged = df_merged.drop(columns=[c2])
    df = df_merged

    return df

def assign_session_ids(df):
        # Assign Technical Session IDs
        df["SessionID"] = df["SessionTitle"].str.extract(
            r'Technical Session (\d+)', flags=re.IGNORECASE
        )[0].apply(lambda x: f"T{x}" if pd.notna(x) else "")

        # Assign SessionID for Plenary sessions
        plenary_mask = df["SessionTitle"].str.contains("Plenary", na=False)
        df.loc[plenary_mask, "SessionID"] = [
            f"P{i+1}" for i in range(plenary_mask.sum())
        ]

        # Assign SessionID for missing values, which should be special sessions
        df["SessionID"] = df["SessionID"].replace("", pd.NA)
        missing_mask = df["SessionID"].isna()
        df.loc[missing_mask, "SessionID"] = [
            f"S{i+1}" for i in range(missing_mask.sum())
        ]

        return df

def ensure_columns(df, SessionListCols):
    """Ensure all required columns exist and are in the correct order."""
    for c in SessionListCols:
        if c not in df.columns:
            df[c] = ""
    # replace any cell value that is NA in IsSpecialSession column with 0
    df["IsSpecialSession"] = df["IsSpecialSession"].fillna(0).astype(int)
    df["OrderInSchedule"] = range(1, len(df) + 1)
    df = df[SessionListCols]
    
    return df

def extract_participants(dfs):
    """Extract participant information from all dataframes."""
    participants = []
    
    # --- Process plenary abstracts
    if "plenary_abstracts" in dfs:
        df = dfs["plenary_abstracts"]
        for _, row in df.iterrows():
            # Add presenter
            if all(col in df.columns for col in ["First or given name(s) of presenter", "Last or family name of presenter"]):
                participants.append({
                    "FirstName": row["First or given name(s) of presenter"],
                    "LastName": row["Last or family name of presenter"],
                    "SessionID": row.get("SessionID", "P"),  # Default to P if no SessionID
                    "PageNumber": "",
                    "Organization": row.get("Institution of presenter", "")
                })
    
    # --- Process special session submissions 
    if "special_session_submissions" in dfs:
        df = dfs["special_session_submissions"]
        # First, add institution columns if they don't exist
        for idx, i in enumerate(["first", "second", "third"], 1):
            if f"Institution of {i} organizer" in df.columns and f"Organizer{idx} institution" not in df.columns:
                df[f"Organizer{idx} institution"] = df[f"Institution of {i} organizer"]
                
        for idx, row in df.iterrows():
            # Add organizers 
            for i in range(1, 4):
                organizer_col = f"Organizer{i}"
                org_col = f"Institution of {'first' if i==1 else 'second' if i==2 else 'third'} organizer"
                
                if organizer_col in df.columns and pd.notna(row[organizer_col]) and row[organizer_col]:
                    # Split the combined name back into first and last
                    name_parts = row[organizer_col].split()
                    if len(name_parts) >= 2:
                        firstName = " ".join(name_parts[:-1])  # All but last part
                        lastName = name_parts[-1]              # Last part
                        organization = row.get(org_col, "")    # Get organization directly
                        session_id = row.get("SessionID", f"S{idx+1}")  # Use row's SessionID or generate one
                        
                        participants.append({
                            "FirstName": firstName,
                            "LastName": lastName,
                            "SessionID": session_id,
                            "PageNumber": "",
                            "Organization": organization
                        })
            
            # Add presenter 
            if "Presenter 1 first or given name(s)" in df.columns and "Presenter 1 last or family name(s)" in df.columns:
                participants.append({
                    "FirstName": row["Presenter 1 first or given name(s)"],
                    "LastName": row["Presenter 1 last or family name(s)"],
                    "SessionID": row.get("SessionID", f"S{idx+1}"),
                    "PageNumber": "",
                    "Organization": row.get("Presenter 1 institution", "")
                })
    
    # --- Process contributed talk submissions
    if "contributed_talk_submissions" in dfs:
        df = dfs["contributed_talk_submissions"]
        for _, row in df.iterrows():
            # Add presenter
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
    
    # --- Process special session abstracts
    if "special_session_abstracts" in dfs:
        df = dfs["special_session_abstracts"]
        for _, row in df.iterrows():
            if all(col in df.columns for col in ["First or given name(s) of presenter", "Last or family name of presenter"]):
                # Try to extract session ID from Special Session Title
                session_id = ""
                if "Special Session Title" in row and pd.notna(row["Special Session Title"]):
                    # Try to match with existing special sessions to get proper ID
                    title = row["Special Session Title"].lower().strip()
                    if "special_session_submissions" in dfs:
                        ss_df = dfs["special_session_submissions"]
                        if "Session Title" in ss_df.columns and "SessionID" in ss_df.columns:
                            # Find matching session title
                            matches = ss_df[ss_df["Session Title"].str.lower().str.strip() == title]
                            if not matches.empty:
                                session_id = matches.iloc[0].get("SessionID", "")
                
                participants.append({
                    "FirstName": row["First or given name(s) of presenter"],
                    "LastName": row["Last or family name of presenter"],
                    "SessionID": session_id if session_id else row.get("SessionID", "SS"),
                    "PageNumber": "",
                    "Organization": row.get("Institution of presenter", "")
                })

    # Create DataFrame from participants list
    participants_df = pd.DataFrame(participants)
    
    # Remove duplicates based on FirstName and LastName
    participants_df = participants_df.drop_duplicates(subset=["FirstName", "LastName", "SessionID"], keep="last")

    # Cleaning up content
    # Make sure first letter of FirstName and LastName is capital letter. 
    # Also, the first letter after Hyphen in the Names should be capital letter. 
    # Other letters in names should be in small case.
    # Clean up FirstName and LastName columns in participants_df
    def clean_name(name):
        if pd.isna(name):
            return ""
        # Lowercase all, then capitalize first letter of each part, including after hyphens
        name = name.strip().lower()
        # Capitalize first letter and after hyphens
        name = re.sub(r'\b\w', lambda m: m.group(0).upper(), name)
        name = re.sub(r'(?<=-)\w', lambda m: m.group(0).upper(), name)
        return name

    participants_df["FirstName"] = participants_df["FirstName"].apply(clean_name)
    participants_df["LastName"] = participants_df["LastName"].apply(clean_name

    # If first or last name has length equal to 1, print errors
    for participant in participants:
        if len(participant["FirstName"]) == 1 or len(participant["LastName"]) == 1:
            print(f"ERROR: Invalid name length for participant: {participant['FirstName']} {participant['LastName']}")
    
    # Sort by LastName, then FirstName
    participants_df = participants_df.sort_values(by=["LastName", "FirstName"])
    
    return participants_df


if __name__ == '__main__':

    SessionListCols = [
        "SessionID", "SessionTitle", "IsSpecialSession", "Organizer1", "Organizer2", "Organizer3", "Chair",
        "SessionTime", "Room", "OrderInSchedule"
    ]

    # Step 1: Read and process session data from google sheets 
    sheets = get_sheets_dict()
    dfs = read_google_sheets(sheets)
    dfs = process_sessions(dfs)
    dfs = add_sessions_join_keys(dfs)
    save_dfs(dfs, interimdir, "joined")

    # Step 2: Read and process schedule data
    schedules = read_schedule_days(num_days=5)
    schedules = add_schedule_join_keys(schedules)
    save_dfs(schedules, interimdir, "joined")

    # Step 3: Concatenate and clean schedule DataFrames
    schedule_df = pd.concat(schedules.values(), ignore_index=True)
    schedule_df = schedule_df[schedule_df["join_key"].notna()]
    schedule_df.to_csv(os.path.join(interimdir, "schedule.csv"), index=False)

    # Step 4: Merge schedule with session data
    merged_df = schedule_df
    for key in ["special_session_submissions", "plenary_abstracts"]:
        merged_df = merge_schedules_sessions(merged_df, dfs[key])

    # Step 5: Assign SessionID based on SessionTitle patterns
    merged_df = assign_session_ids(merged_df)

    # Step 6: Order all required columns  
    merged_df = ensure_columns(merged_df, SessionListCols)

    # Step 7: Output final CSV
    csv_file = os.path.join(outdir, "SessionList.csv")
    merged_df.to_csv(csv_file, index=False)
    print("Output:", csv_file)

    # assert merged_df.shape[0] == 8 + 29 + 16, "SessionList.csv does not have the expected number of rows"
    
    # Step 7: Generate Participants.csv
    participants_df = extract_participants(dfs)

    participants_csv = os.path.join(outdir, "Participants.csv")
    participants_df.to_csv(participants_csv, index=False)
    print("Output:", participants_csv)
