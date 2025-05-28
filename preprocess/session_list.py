import pandas as pd
import os
import re
import numpy as np
from typing import List, Tuple

from config import *
from util import *


def _create_presenter_mapping(session_df: pd.DataFrame) -> List[Tuple[Tuple[str, str], str]]:
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
            first_col = f"Presenter {i} first or given name(s)"
            last_col = f"Presenter {i} last or family name(s)"
            
            if first_col not in row or last_col not in row:
                continue
                
            first = str(row[first_col]).strip() if pd.notna(row[first_col]) else ""
            last = str(row[last_col]).strip() if pd.notna(row[last_col]) else ""
            
            if first or last:
                presenter = f"{first} {last}".strip()
                talk_id = f"{session_id}-{i}"
                presenter_map.append(((join_key, presenter), talk_id))
                
    return presenter_map

def _validate_talk_ids(df: pd.DataFrame) -> None:
    """
    Validate that all talks have been assigned talk IDs.
    
    Args:
        df: DataFrame containing talk data with TalkID column
    """
    empty_talk_ids = df[df["TalkID"].isna() | (df["TalkID"] == "")]
    if not empty_talk_ids.empty:
        print("\nWARNING: Found talks with missing TalkIDs:")
        print(empty_talk_ids[["join_key", "Presenter", "SessionID", "SessionTitle"]])

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
    presenter_map = _create_presenter_mapping(session_df)
    
    # Create mapping DataFrame
    talk_id_df = pd.DataFrame(
        [(k[0], k[1], v) for k, v in dict(presenter_map).items()],
        columns=["join_key", "Presenter", "TalkID"]
    )
    
    # Save mapping for debugging
    print("\nTalkID mapping sample:")
    print(talk_id_df.head(2))
    talk_id_df.to_csv(f"{interimdir}talkid_map_df.csv", index=False)
    
    # Merge abstracts with talk IDs
    result_df = abstracts_df.merge(
        talk_id_df, 
        how="left",
        on=["join_key", "Presenter"]
    )
    
    # Save merged results for debugging
    print("\nMerged abstracts sample:")
    print(result_df.head(2))
    result_df.to_csv(f"{interimdir}ssa_df.csv", index=False)
    
    # Validate results
    _validate_talk_ids(result_df)
    
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
        print("\nWARNING: Duplicated records in special session abstracts:")
        print(dupes[presenter_cols])
    
    # Deduplicate by presenter name
    df = df.drop_duplicates(subset=presenter_cols, keep="last")
    
    # Create combined presenter column and clean up
    df["Presenter"] = df[presenter_cols[0]] + " " + df[presenter_cols[1]]
    df = df.drop(columns=presenter_cols)
    df["IsSpecialSession"] = 1
    
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
    print("\nWARN: Contributed talks that are not accepted:")
    not_accepted = df.loc[df["Acceptance"].str.lower() != "yes", [*presenter_cols, "Acceptance"]]
    if not_accepted.shape[0]>0: print(not_accepted)
    
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

    # replace hyphen with space in join key
    for key in dfs.keys():
        if "join_key" in dfs[key].columns:
            dfs[key]["join_key"] = dfs[key]["join_key"].str.replace("-", " ", regex=False)
            # remove any leading or trailing spaces
            dfs[key]["join_key"] = dfs[key]["join_key"].str.strip()

        # print ERROR if any value in the column join_key of df is empty or contains invalid values
        if dfs[key]["join_key"].isna().any() or dfs[key]["join_key"].str.contains(r"add to shane|//", case=False, na=False).any():
            print(f"\nERROR: join_key column in {key} contains invalid values.")
            print(dfs[key][dfs[key]["join_key"].isna()].iloc[:, :2]) # print first two columns
            print("\n")
                  
    return dfs


def add_technical_sessions_talkid(df):
    """
    Adds a 'TalkID' column to df for technical sessions
    TalkID == SessionID + '-' + a counter within that SessionID.
    """

    # 1) Flag technical sessions
    technical     = df['SessionID'].str.startswith('T', na=False)

    # 2) Only number those non-plenary rows with a real SessionID
    mask = technical & df['SessionID'].notna()
    seq  = df.loc[mask].groupby('SessionID').cumcount() + 1  # always ints, no NaN

    # 3) Build the “-n” suffix
    suffix = pd.Series('', index=df.index, dtype='object')
    suffix.loc[mask] = '-' + seq.astype(str)

    # 4) Combine
    df['TalkID'] = df['SessionID'].fillna('') + suffix

    return df

 
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
        # replace hyphen with space in join key
        df["join_key"] = df["join_key"].str.replace("-", " ", regex=False)
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
    schedule_df = schedule_df[schedule_df["join_key"].notna()]
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
    for key in dfs:
        dfs[key] = dfs[key].merge(merged_df[["join_key", "SessionTime", "SessionID", "SessionTitle"]], how="left", on="join_key")

    save_dfs(dfs, interimdir, "sessionid")  # Save updated session dataframes with SessionID

    ### Add TalkIDs
    talks_keys = ["special_session_abstracts",  "plenary_abstracts", "contributed_talk_submissions"]
    talks_dict = {k: dfs[k] for k in talks_keys if k in dfs.keys()}   
    talks_dict["contributed_talk_submissions"] = add_technical_sessions_talkid(talks_dict["contributed_talk_submissions"])
    talks_dict["plenary_abstracts"]["TalkID"] = talks_dict["plenary_abstracts"]["SessionID"]
    talks_dict["special_session_abstracts"] = add_special_sessions_talkid(dfs["special_session_submissions"], talks_dict["special_session_abstracts"])
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

    # assert rows is no_special_sessions + no_technical_sessions + no_plenary_sessions
    assert merged_df.shape[0] == no_sessions, \
        f"ERROR: Number of rows in SessionList.csv = {merged_df.shape[0]} and it is not equal to {no_sessions} "
    
    # merge schedule_full_df with merged_df and output to schedule_full.csv
    # Only include columns from SessionListCols except for SessionTime, Organizer1, Organizer2, Organizer3, IsSpecialSession
    exclude_cols = {"SessionTime", "Organizer1", "Organizer2", "Organizer3", "IsSpecialSession", "OrderInSchedule"}
    merge_cols = [col for col in SessionListCols if col not in exclude_cols]
    schedule_full_df = schedule_full_df.merge(
        merged_df[merge_cols],
        how="left",
        on="SessionTitle"
    )
    schedule_full_df["OrderInSchedule"] = range(1, len(schedule_full_df) + 1)
    schedule_full_df.to_csv(os.path.join(outdir, "schedule_full.csv"), index=False)



