import pandas as pd
import os
import re
import numpy as np
from typing import List, Tuple
import datetime
from config import *
from util import *


def _create_session_talk_df(session_df: pd.DataFrame) -> List[Tuple[Tuple[str, str], str]]:
    """
    Create mapping between presenters and their talk IDs.
    
    Args:
        session_df: DataFrame containing session submission data
        
    Returns:
        List of tuples mapping (join_key, presenter) to talk ID
    """
    presenter_map = []
    
    for _, row in session_df.iterrows():
        session_id = str(row.get("SessionID", ""))
        session_title = str(row.get("Session Title", ""))
        join_key = session_title.strip().lower()
        
        for i in range(1, 5):
            last_col = f"Presenter {i} last or family name(s)"
            
            if last_col not in row:
                continue

            last = str(row[last_col]).strip() if pd.notna(row[last_col]) else ""
            
            if last:
                presenter = last.strip().split()[-1].split('-')[-1].strip().lower()
                talk_id = f"{session_id}-{i}"
                presenter_map.append(((join_key, presenter), talk_id))
    
    # Create mapping DataFrame
    talk_id_df = pd.DataFrame(
        [(k[0], k[1], v) for k, v in dict(presenter_map).items()],
        columns=["join_key", "PresenterLast", "TalkID"]
    )

    # clean or standardize key column
    talk_id_df["join_key"] = (
        talk_id_df["join_key"]
        .str.replace(r'[-():,.]', ' ', regex=True)  # Replace special chars with space
        .str.replace(r'\s+', ' ', regex=True)      # Collapse multiple spaces
        .str.strip()                               # Remove leading/trailing space
    )
    # sort frames by "join_key", "Presenter"
    talk_id_df = talk_id_df.sort_values(by=["join_key", "PresenterLast"]).reset_index(drop=True)
    # abstracts_df = abstracts_df.sort_values(by=["join_key", "PresenterLast"]).reset_index(drop=True)
    
    # Save frame for debugging
    #print("\nTalkID mapping sample:")
    #print(talk_id_df.head(2))
    talk_id_df.to_csv(f"{interimdir}talkid_map_df.csv", index=False)

    return talk_id_df

def _validate_talk_ids(df: pd.DataFrame) -> None:
    """
    Validate that all talks have been assigned talk IDs.
    
    Args:
        df: DataFrame containing talk data with TalkID column
    """
    empty_talk_ids = df[df["TalkID"].isna() | (df["TalkID"] == "")]
    if not empty_talk_ids.empty:
        print("\nERROR: Found talks with missing TalkIDs:\n")
        print(empty_talk_ids[["join_key", "PresenterLast", "SessionID", "SessionTitle"]])

def add_special_sessions_talkid(session_df: pd.DataFrame, abstracts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate and assign talk IDs for special session abstracts.
    
    Args:
        session_df: DataFrame containing special session submission data
        abstracts_df: DataFrame containing special session abstracts
        
    Returns:
        DataFrame with TalkIDs assigned to abstracts
    """
    # Create deep copies to avoid modifying original data
    session_df = session_df.copy(deep=True)
    abstracts_df = abstracts_df.copy(deep=True)
    # Generate presenter to talk ID mapping
    talk_id_df = _create_session_talk_df(session_df)
    #print(talk_id_df[talk_id_df["TalkID"].str.startswith("S8")])
    # extract Last name of Presenter
    abstracts_df["PresenterLast"] = abstracts_df["Presenter"].str.split(r"[ \-]").str[-1].str.lower()
    abstracts_df[["join_key", "PresenterLast", "SessionID", 'SessionTitle']].to_csv(f"{interimdir}abstracts_df.csv", index=False)
    
    # Merge abstracts with talk IDs
    # Merge using lower-cased join_key and Presenter, but keep original columns unchanged
    result_df = abstracts_df.copy()

    result_df = result_df.merge(
        talk_id_df[["join_key", "PresenterLast", "TalkID"]],
        how="outer",
        left_on=["join_key", "PresenterLast"],
        right_on=["join_key", "PresenterLast"]
    )

    # Sort result_df by TalkID
    result_df = result_df.sort_values(by="TalkID").reset_index(drop=True)

    # If SessionID is missing or empty, extract it from TalkID (e.g., "S8-1" → "S8")
    missing_mask = result_df["SessionID"].isna() | (result_df["SessionID"] == "")
    result_df.loc[missing_mask, "SessionID"] = result_df.loc[missing_mask, "TalkID"].str.extract(r'^(S\d+|P\d+|T\d+)')[0]
    # group by SessionID and use forward fill for missing values in SessionTime, SessionTitle, Room, Chair, Include, Special Session Title
    fill_cols = ["SessionTime", "SessionTitle", "Room", "Chair", "Include", "Special Session Title", "IsSpecialSession"]
    result_df[fill_cols] = result_df.groupby("SessionID")[fill_cols].ffill()
    result_df[fill_cols] = result_df.groupby("SessionID")[fill_cols].bfill()
    # For missing values in Talk Title, set "TBD"
    result_df["Talk Title"] = result_df["Talk Title"].fillna("TBD")
    result_df["Institution of presenter"] = result_df["Institution of presenter"].fillna("TBD")
    result_df["Presenter"] = result_df["Presenter"].fillna(result_df["PresenterLast"]).fillna("TBD")

    # Save merged results for debugging
    #print("\nMerged abstracts sample:")
    #print(result_df.head(2))
    result_df.to_csv(f"{interimdir}ssa_df.csv", index=False)

    # Validate results
    _validate_talk_ids(result_df)
    #print(result_df.loc[result_df["TalkID"].str.startswith("S8"), ["join_key", "PresenterLast", "TalkID", "SessionID"]])
    return result_df

def process_sessions(dfs):
    """Process presenter and organizer columns for all relevant sheets."""
    # Process each session type using dedicated helper functions
    dfs["plenary_abstracts"] = process_plenary_abstracts(dfs["plenary_abstracts"])
    
    if "special_session_abstracts" in dfs:
        dfs["special_session_abstracts"] = process_special_session_abstracts(dfs["special_session_abstracts"])
    
    dfs["special_session_submissions"] = process_special_session_submissions(dfs["special_session_submissions"])
    dfs["contributed_talk_submissions"] = process_contributed_talks(dfs["contributed_talk_submissions"])
    
    return dfs

def process_plenary_abstracts(df):
    """Process plenary abstracts data."""
    df = df.copy()
    df["IsSpecialSession"] = 0
    return df

def process_special_session_abstracts(df):
    """Process special session abstracts data."""
    df = df.copy()
    presenter_cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    
    # Check for duplicates
    dupes = df[df.duplicated(subset=presenter_cols, keep=False)]
    if not dupes.empty:
        print(f"\nWARNING: {dupes.shape[0]} duplicated records in special session abstracts --- will be deduplicated by keeping last records.\n")
        #print(dupes[presenter_cols])
    
    not_accepted = df.loc[df["Include"].str.lower() != "yes", [presenter_cols[-1], "Include"]]

    if not_accepted.shape[0]>0:  
        print(f"\nWARN: {not_accepted.shape[0]} special talks are not accepted (Include = No)\n")
    #   print(not_accepted)

    # Deduplicate by presenter name
    df = df.drop_duplicates(subset=presenter_cols, keep="last")
    
    # Create combined presenter column and clean up
    df["Presenter"] = df[presenter_cols[0]] + " " + df[presenter_cols[1]]
    df = df.drop(columns=presenter_cols)
    df["IsSpecialSession"] = 1
        
    # Filter out accepted talks
    df = df[df["Include"].str.lower() == "yes"]

    # Validate data
    if df["Special Session Title"].isna().any():
        raise ValueError("Special Session Title contains Null values")
    
    return df

def process_special_session_submissions(df):
    """Process special session submissions data."""
    df = df.copy()
    
    # Process organizers
    for idx, i in enumerate(["first", "second", "third"], 1):
        # Combine first and last name
        name_cols = [f"First or given name(s) of {i} organizer", f"Last or family name(s) of {i} organizer"]
        if all(col in df.columns for col in name_cols):
            df[f"Organizer{idx}"] = df[name_cols[0]] + " " + df[name_cols[1]]
            # Preserve institution data
            if f"Institution of {i} organizer" in df.columns:
                df[f"Organizer{idx} institution"] = df[f"Institution of {i} organizer"]
            df = df.drop(columns=name_cols)
    
    # Filter out specific sessions
    df = df[~df["Session Title"].str.contains("by Nathan Kirk", case=False, na=False)]
    df["IsSpecialSession"] = 1
    
    # Validate data
    if df["Session Title"].isna().any():
        raise ValueError("Special Session Title contains Null values")
    
    return df

def process_contributed_talks(df):
    """Process contributed talk submissions data."""
    df = df.copy()
    
    presenter_cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    #print("\nWARN: Contributed talks that are not accepted:\n")
    #not_accepted = df.loc[df["Acceptance"].str.lower() != "yes", [presenter_cols[-1], "Acceptance"]].sort_values("Acceptance")
    #if not_accepted.shape[0]>0: 
    #    print(not_accepted)
    
    # Filter by acceptance status
    df = df[df["Acceptance"] == "Yes"]
    df["IsSpecialSession"] = 0

    # Handle duplicates
    dupes = df[df.duplicated(subset=presenter_cols, keep=False)]
    
    if not dupes.empty:  
        print("ERROR: Duplicated records in contributed talk submissions:")
        print(dupes[presenter_cols])
    
    # Deduplicate
    df = df.drop_duplicates(subset=presenter_cols, keep="last")
    
    return df

def add_sessions_join_keys(dfs):
    """Add join_key columns to each DataFrame in dfs."""
    # Assign join_key columns
    dfs["special_session_submissions"]["join_key"] = (
        dfs["special_session_submissions"]["Session Title"].str.strip().str.lower()
    )
    if "special_session_abstracts" in dfs:
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

    # Clean and standardize join_key column for all DataFrames
    for key in dfs.keys():
        tmp_df = dfs[key].copy(deep=True)
        if "join_key" in tmp_df.columns:
            tmp_df["join_key"] = (
                tmp_df["join_key"]
                .str.replace(r'[-():,.]', ' ', regex=True)  # Replace special chars with space
                .str.replace(r'\s+', ' ', regex=True)       # Collapse multiple spaces
                .str.strip()                                # Remove leading/trailing space
            )
            dfs[key] = tmp_df

            # print ERROR if any value in the column join_key of df is empty or contains invalid values in column `SESSION`
            invalid_mask = tmp_df["join_key"].isna() | tmp_df["join_key"].str.contains(r"add to shane|//", case=False, na=False) | (tmp_df["join_key"] == "")
            
            # Add check for technical sessions that don't start with "Technical" when they should
            if key == "contributed_talk_submissions" and "SESSION" in tmp_df.columns:
                technical_mask = tmp_df["SESSION"].notna() & (
                    tmp_df["SESSION"].str.lower().str.startswith("technical") == False)
                invalid_mask = invalid_mask | technical_mask
                
            invalid_rows = tmp_df[invalid_mask]
            if not invalid_rows.empty:
                print(f"\nERROR: SESSION or join_key column in '{key}' contains invalid values like 'add to shane', '//'\n")
                print(invalid_rows.iloc[:, :2])  # Print first two columns
                print("\n")
                  
    return dfs

def add_technical_sessions_talkid(df):
    """
    Adds a 'TalkID' column to df for technical sessions
    TalkID == SessionID + '-' + a counter within that SessionID.
    """

    # 1) Flag technical sessions
    technical = df['SessionID'].str.startswith('T', na=False)

    # 2) Only number those non-plenary rows with a real SessionID
    mask = technical & df['SessionID'].notna()
    seq  = df.loc[mask].groupby('SessionID').cumcount() + 1  # always ints, no NaN

    # output ERROR if seq is not 1, 2, 3, 4 and print the corresponding SessionID
    invalid_seq = seq[~seq.isin([1, 2, 3, 4])]
    if not invalid_seq.empty:
        print("\n")
        for session_id, values in df.loc[invalid_seq.index, 'SessionID'].value_counts().items():
            print(f"ERROR:  Session {session_id} has > 4 talks")
        print("\n")
        
    # 3) Build the “-n” suffix
    suffix = pd.Series('', index=df.index, dtype='object')
    suffix.loc[mask] = '-' + seq.astype(str)

    # 4) Combine
    df['TalkID'] = df['SessionID'].fillna('') + suffix

    return df

def add_parallel_talk_eventtime(df):
    """Create EventTime in similar format as SessionTime in df"""
    # normalize en-dash to hyphen and parse start datetime from SessionTime
    # replace en-dash with hyphen and fill missing values
    clean_time = df["SessionTime"].fillna("").str.replace("–", "-", regex=False)
    # split on hyphen (no matter spacing) and take the start segment
    start_time_str = clean_time.str.split(r'\s*-\s*', regex=True).str[0]
    # Convert from "Thu, Jul 31 15:30" format to "2024-07-31 15:30"
    current_year = datetime.datetime.now().year
    session_start_time = pd.to_datetime(f"{current_year} " + start_time_str.str.strip(), 
                            format=f"%Y %a, %b %d %H:%M", 
                            errors='coerce') 
    
    # extract the talk index j from TalkID (e.g. "T4-3" → 3), defaulting to 1 if missing
    j = df["TalkID"].str.extract(r"-(\d+)$")[0].fillna(1).astype(int)
    # compute start and end time 
    event_start_time = session_start_time + pd.to_timedelta((j - 1) * 30, unit="m")
    event_end_time = event_start_time + pd.to_timedelta(30, unit="m")
    # format EventTime as "YYYY-MM-DD HH:MM - HH:MM"
    df["EventTime"] = (
        event_start_time.dt.strftime("%Y-%m-%d %H:%M")
        + " - "
        + event_end_time.dt.strftime("%H:%M")
    )
    ### Format df["EventTime"] to match the format of df["SessionTime"]
    # Extract the date part from SessionTime (e.g., "Thu, Jul 31")
    date_part = df["SessionTime"].str.extract(r'([^,]+, [^,]+\s+\d+)(?=\s+\d+:)')[0]
    # Extract start and end times from EventTime (e.g., "2024-07-31 15:30 - 16:00")
    start_time = pd.to_datetime(df["EventTime"].str.split(" - ").str[0]).dt.strftime("%H:%M")
    end_time = df["EventTime"].str.split(" - ").str[1]
    # Combine into the same format as SessionTime: "Thu, Jul 31 15:30--16:00"
    df["EventTime"] = date_part + " " + start_time + "–" + end_time

    return df
 
def read_schedule_days(num_days=5):
    """Read schedule_day1.csv ... schedule_dayN.csv into a dictionary."""
    schedules = {}
    for i in range(1, num_days + 1):
        day_df = pd.read_csv(os.path.join(interimdir, f"schedule_day{i}.csv"))
        #day_df = clean_df(day_df)
        date = day_df.columns[0]
        day_df.columns = ["SessionTime", "SessionTitle", "Room", "Chair"]
        day_df["SessionTime"] = date + " " + day_df["SessionTime"]
        day_df = day_df[["SessionTime", "SessionTitle", "Room", "Chair"]]
        schedules[f"day{i}"] = day_df
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


def add_schedule_join_keys(schedules):
    """Add join_key column to each schedule DataFrame."""
    for key, df in schedules.items():
        df["join_key"] = df.iloc[:, 1].str.extract(r'Plenary Talk by\s+([^,]+)')[0]
        mask = df.iloc[:, 1].str.contains("Track", na=False) & ~df.iloc[:, 1].str.contains("Technical Session", na=False)
        # Extract join_key by removing "Track X: " prefix (where X is any single uppercase letter)
        df.loc[mask, "join_key"] = df.loc[mask].iloc[:, 1].str.replace(r'^Track [A-Z]:\s*', '', regex=True)
        mask2 = df.iloc[:, 1].str.contains(r'Technical Session \d+ .+', case=False, na=False)
        df.loc[mask2, "join_key"] = df.loc[mask2].iloc[:, 1].str.extract(r'(Technical Session \d+)')[0]
        df["join_key"] = df["join_key"].str.strip().str.lower()
        # clean and standardize key column
        df["join_key"] = (
            df["join_key"]
            .str.replace(r'[-():,.]', ' ', regex=True)  # Replace special chars with space
            .str.replace(r'\s+', ' ', regex=True)       # Collapse multiple spaces
            .str.strip()                                # Remove leading/trailing space
        )
        # remove any leading or trailing spaces
        df["join_key"] = df["join_key"].str.strip()
        schedules[key] = df
    return schedules

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

if __name__ == "__main__":
    # --- Read and process schedule data
    schedules_dict = read_schedule_days(num_days=5)
    schedules_dict = add_schedule_join_keys(schedules_dict)
    save_dfs(schedules_dict, interimdir, "joined")

    # Concatenate and clean schedule DataFrames
    schedule_df = pd.concat(schedules_dict.values(), ignore_index=True)
    schedule_full_df = schedule_df.copy(deep=True)  # contains all sessions, including breaks

    schedule_df = schedule_df[schedule_df["join_key"].notna()].copy(deep=True) # contains all sessions but NOT breaks
    schedule_df.to_csv(os.path.join(interimdir, "schedule_joined.csv"), index=False)

    # --- Read in session data
    dfs = {}
    for key in ["special_session_abstracts", "special_session_submissions",  "plenary_abstracts", "contributed_talk_submissions"]:
        dfs[key] = pd.read_csv(os.path.join(interimdir, f"{key}_gsheet.csv"))
    dfs = process_sessions(dfs)
    dfs = add_sessions_join_keys(dfs)

    # --- Merge schedule with session data
    merged_df = schedule_df
    for key in ["special_session_submissions", "plenary_abstracts"]:
        merged_df = merge_schedules_sessions(merged_df, dfs[key])

    # Assign SessionID based on SessionTitle patterns
    merged_df = assign_session_ids(merged_df)

    # Merge SessionID back into session dataframes
    sel_cols = ["join_key", "SessionTime", "SessionID", "SessionTitle", "Room", "Chair"]
    for key in dfs:
        dfs[key] = dfs[key].merge(merged_df[sel_cols], how="left", on="join_key")

    save_dfs(dfs, interimdir, "sessionid")  # Save updated session dataframes with SessionID

    ### Add TalkIDs 
    talks_keys = ["special_session_abstracts",  "plenary_abstracts", "contributed_talk_submissions"]
    talks_dict = {k: dfs[k] for k in talks_keys if k in dfs.keys()}   
    talks_dict["contributed_talk_submissions"] = add_technical_sessions_talkid(talks_dict["contributed_talk_submissions"])
    talks_dict["special_session_abstracts"] = add_special_sessions_talkid(dfs["special_session_submissions"], talks_dict["special_session_abstracts"])
    talks_dict["plenary_abstracts"]["TalkID"] = talks_dict["plenary_abstracts"]["SessionID"]
    
    # Add EventTime
    talks_dict["plenary_abstracts"]["EventTime"] = talks_dict["plenary_abstracts"]["SessionTime"]
    talks_dict["contributed_talk_submissions"]=  add_parallel_talk_eventtime(talks_dict["contributed_talk_submissions"])
    talks_dict["special_session_abstracts"] =  add_parallel_talk_eventtime(talks_dict["special_session_abstracts"])
    save_dfs(talks_dict, interimdir, "talkid")  # Save updated session dataframes with TalkID
  
    # Step 7: Order all required columns in SessionList
    SessionListCols = [
        "SessionID", "SessionTitle", "IsSpecialSession", "Organizer1", "Organizer2",
        "Organizer3", "Chair", "SessionTime", "Room", "OrderInSchedule"
    ]
    merged_df = ensure_columns(merged_df, SessionListCols)

    # Step 8: Output final SessionList.csv
    output_file = os.path.join(outdir, "SessionList.csv")
    merged_df.to_csv(output_file, index=False)
    print("Output:", output_file)

    # merge schedule_full_df with merged_df and output to schedule_full.csv
    # Only include columns from SessionListCols except for SessionTime, Organizer1, Organizer2, Organizer3, IsSpecialSession
    exclude_cols = {"SessionTime", "Organizer1", "Organizer2", "Organizer3", "IsSpecialSession", "OrderInSchedule", "Chair", "Room"}
    merge_cols = [col for col in SessionListCols if col not in exclude_cols]
    schedule_full_df = schedule_full_df.merge(merged_df[merge_cols],how="left", on="SessionTitle")
    schedule_full_df["OrderInSchedule"] = range(1, len(schedule_full_df) + 1)
    schedule_full_df.to_csv(os.path.join(outdir, "schedule_full.csv"), index=False)

    # assert rows is no_special_sessions + no_technical_sessions + no_plenary_sessions
    assert merged_df.shape[0] == no_sessions, \
        f"ERROR: Number of rows in SessionList.csv = {merged_df.shape[0]} and it is not equal to {no_sessions} "