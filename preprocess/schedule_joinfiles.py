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

    # assert number of rows in SessionList is 8 plenary + 26 special + 16 technical
    assert len(merged_df) == 8 + 26 + 16
