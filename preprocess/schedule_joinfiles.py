import pandas as pd
import os
from config import *
from util import *

# print many rows and columns in dataframes
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)


def read_google_sheets(sheets, indir):
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

def process_plenary_presenter(dfs):
    """Combine first and last name into Presenter and drop originals."""
    df = dfs["plenary_abstracts"]
    df["Presenter"] = df["First or given name(s) of presenter"] + " " + df["Last or family name of presenter"]
    df = df.drop(columns=["First or given name(s) of presenter", "Last or family name of presenter"])
    # flag for special session
    df["IsSpecialSession"] = int(0)
    # Update df in dictionary
    dfs["plenary_abstracts"] = df
    return dfs

def process_special_organizers(dfs):
    """Combine first and last name into Organizer1, ..., Organizer3 and drop originals."""
    df = dfs["special_session_submissions"]
    for idx, i in enumerate(["first", "second", "third"], 1):
        df[f"Organizer{idx}"] = df[f"First or given name(s) of {i} organizer"] + " " + df[f"Last or family name(s) of {i} organizer"]
        df = df.drop(columns=[f"First or given name(s) of {i} organizer", f"Last or family name(s) of {i} organizer"])
    # Combine Presenter 1 first and last name into Presenter1 and drop originals
    df["Presenter"] = df["Presenter 1 first or given name(s)"] + " " + df["Presenter 1 last or family name(s)"]
    df = df.drop(columns=["Presenter 1 first or given name(s)", "Presenter 1 last or family name(s)"])
    # flag for special session
    df["IsSpecialSession"] = int(1)
    # Update df in dictionary
    dfs["special_session_submissions"] = df
    
    return dfs

def process_contributed_talk_presenter(dfs):
    """Combine first and last name into Presenter and drop originals for contributed talk submissions."""
    df = dfs["contributed_talk_submissions"]
    df["Presenter"] = df["First or given name(s) of presenter"] + " " + df["Last or family name of presenter"]
    df = df.drop(columns=["First or given name(s) of presenter", "Last or family name of presenter"])
    # flag for special session
    df["IsSpecialSession"] = int(0)
    # Update df in dictionary
    dfs["contributed_talk_submissions"] = df
    return dfs


def read_schedule_days(interimdir, num_days=5):
    """Read schedule_day1.csv ... schedule_dayN.csv into a dictionary."""
    schedules = {}
    for i in range(1, num_days + 1):
        day_df = pd.read_csv(os.path.join(interimdir, f"schedule_day{i}.csv"))
        day_df = clean_df(day_df)
        date = day_df.columns[0]
        day_df.columns =["SessionTime", "SessionTitle"]
        day_df["SessionTime"] = date + " " + day_df["SessionTime"]
        day_df = day_df[["SessionTime",  "SessionTitle"]]

        schedules[f"day{i}"] = day_df
        
    return schedules

def add_join_keys(dfs):
    """Add join_key columns to each DataFrame in dfs."""
    # Plenary abstracts: join_key = first name + last name 
    df = dfs["plenary_abstracts"]
    df["join_key"] = (df["First or given name(s) of presenter"] + " " + df["Last or family name of presenter"]).str.strip()

    # Special session submissions: join_key = Session Title
    df = dfs["special_session_submissions"]
    df["join_key"] = df["Session Title"].str.strip()

    # Special session abstracts: join_key = Special Session Title
    df = dfs["special_session_abstracts"]
    df["join_key"] = df["Special Session Title"].str.strip()

    # Contributed talk submissions: join_key = SESSION
    df = dfs["contributed_talk_submissions"]
    df["join_key"] = df["SESSION"].str.strip()

    return dfs

def add_schedule_join_keys(schedules):
    """Add join_key column to each schedule DataFrame."""
    for df in schedules.values():
        # Plenary Talk
        df["join_key"] = df.iloc[:, 1].str.extract(r'Plenary Talk by (.+)')[0]

        # Track rows (not technical session)
        mask = df.iloc[:, 0].str.contains("Track", na=False) & ~df.iloc[:, 1].str.contains("Technical Session", na=False)
        df.loc[mask, "join_key"] = df.loc[mask].iloc[:, 1]

        # Technical Session rows
        mask2 = df.iloc[:, 1].str.contains(r'Technical Session \d+ .+', na=False)
        df.loc[mask2, "join_key"] = df.loc[mask2].iloc[:, 1].str.extract(r'(Technical Session \d+)')[0]
    
    return schedules

def merge_schedules_with_dfs(df, dfs):
    """Merge all schedule DataFrames with dfs using join_key, and add email columns."""
    for key, df2 in dfs.items():
        # Handle Presenter columns
        speaker = "Presenter"
        if speaker not in df.columns:
            speaker_cols = df2.columns.str.contains(speaker, case=False)
            cols = list(df2.columns[speaker_cols])
            df = df.merge(df2[[*cols, "join_key"]], on="join_key", how="left")
        else:
            # fill NaN values in the existing  column from the corresponding column in df2
            df[speaker] = df[speaker].fillna(df2["Presenter"])

        # Handle Organizer1, Organizer2, Organizer3 columns
        for i in range(1, 4):
            organizer = f"Organizer{i}"
            if organizer not in df.columns:
                organize_col = df2.columns.str.contains(organizer, case=False)
                cols = list(df2.columns[organize_col])
                if organizer in df2.columns:
                    df = df.merge(df2[[organizer, "join_key"]], on="join_key", how="left")
            else:
                # fill NaN values in the existing  column from the corresponding column in df2
                if organizer in df2.columns:
                    df[organizer] = df[organizer].fillna(df2[organizer])

        # Handle IsSpecialSession column
        if "IsSpecialSession" not in df.columns:
            df = df.merge(df2[["IsSpecialSession", "join_key"]], on="join_key", how="left")
        else:
            # fill NaN values in the existing  column from the corresponding column in df2
            df["IsSpecialSession"] = df["IsSpecialSession"].fillna(df2["IsSpecialSession"])

    return df



if __name__ == '__main__':
    #  `SessionID,SessionTitle,IsSpecialSession,Organizer1,Organizer2,Organizer3,Chair,SessionTime,Room,OrderInSchedule`

     # Read and process Google Sheets
    sheets = get_sheets_dict()
    dfs = read_google_sheets(sheets, indir)
    dfs = add_join_keys(dfs)
    dfs = process_plenary_presenter(dfs)
    dfs = process_special_organizers(dfs)
    dfs = process_contributed_talk_presenter(dfs)
    save_dfs(dfs, interimdir, "joined")

    # Read and process daily schedules
    schedules = read_schedule_days(interimdir, num_days=5)
    schedules = add_schedule_join_keys(schedules)
    save_dfs(schedules, interimdir, "joined")

    # Concatenate all schedules into one DataFrame
    schedule_df = pd.concat(schedules.values(), ignore_index=True)
    # remove rows in schedule_df such that join_key is NaN
    schedule_df = schedule_df[schedule_df["join_key"].notna()]

    # Merge schedule with other dataframes
    # select only sub-dictionary whose keys are in ["plenary_abstracts"]
    dfs2 = {key: dfs[key] for key in ["special_session_submissions", "contributed_talk_submissions", "plenary_abstracts"  #, "special_session_abstracts"
                                     ]}
    merged_df = merge_schedules_with_dfs(schedule_df, dfs2)

    # Add first column called SessionID with values S1, S2,...if a row is a special session, i.e., isSpecialSession = True
    #merged_df["SessionID"] = merged_df["IsSpecialSession"].apply(lambda x: "S" + str(x))

    # Add a few columns not yet have values TODO
    merged_df["SessionID"] = ""
    merged_df["Chair"] = ""
    merged_df["Room"] = ""
    # cast column isSpecialSession to int
    merged_df["IsSpecialSession"] = merged_df["IsSpecialSession"].astype(int)
      
    # Add last column called OrderInSchedule with values 1, 2, ... in the order of the rows
    merged_df["OrderInSchedule"] = range(1, len(merged_df) + 1)

    # Reorder columns to SessionID,SessionTitle,IsSpecialSession,Organizer1,Organizer2,Organizer3,Chair,SessionTime,Room,OrderInSchedule`
    merged_df = merged_df[["SessionID", "SessionTitle", "IsSpecialSession",  "Organizer1", "Organizer2", "Organizer3", "Chair",
                             "SessionTime", "Room", "OrderInSchedule"]]

    # Save final merged schedule
    csv_file = os.path.join(outdir, "SessionList.csv")
    merged_df.to_csv(csv_file, index=False)
    print("Output: ",  f"{csv_file}")
  
    
 
