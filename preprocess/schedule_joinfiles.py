import pandas as pd
import os
from config import *
from util import *

def get_sheets_dict():
    """Return the dictionary describing all Google Sheets and their columns."""
    return {
        "plenary_abstracts": {
            "sheet_id": "1xNO88DO2COTkJ1vOzCXQiTrxKa7_pxW3a2yU06JoDEY",
            "sheet_name": "Form Responses 1",
            "columns": [
                "First or given name(s) of presenter", "Last or family name of presenter",
                "Institution of presenter", "Email of presenter", "Talk Title",
                "FirstNameLastNameAbstract.tex file with Talk Title and Abstract"
            ]
        },
        "special_session_submissions": {
            "sheet_id": "1i6OUgAZSI_evTy0E8X5NUB0IzGwLIjwtu_cSnGwl960",
            "sheet_name": "Form Responses 1",
            "columns": [
                "First or given name(s) of first organizer", "Last or family name(s) of first organizer",
                "Institution of first organizer", "Email of first organizer",
                "First or given name(s) of second organizer", "Last or family name(s) of second organizer",
                "Institution of second organizer",
                "First or given name(s) of third organizer", "Last or family name(s) of third organizer",
                "Institution of third organizer",
                "Presenter 1 first or given name(s)", "Presenter 1 last or family name(s)",
                "Presenter 1 institution", "Presenter 1 email", "Session Title",
                "FirstNameLastNameSession.tex file with Session Title and Description"
            ]
        },
        "special_session_abstracts": {
            "sheet_id": "10o80tZl1f5XGXT4WpqYe7v4nzzFyBEvgUYxDAkT5LlI",
            "sheet_name": "Form Responses 1",
            "columns": [
                "First or given name(s) of presenter", "Last or family name of presenter",
                "Institution of presenter", "Email of presenter", "Talk Title",
                "FirstNameLastNameAbstract.tex file with Talk Title and Abstract", "Special Session Title"
            ]
        },
        "contributed_talk_submissions": {
            "sheet_id": "1o1WeviV-MTGQMFHqsiAkZwMVOO0_h3GNekgCS2fojGM",
            "sheet_name": "Form Responses 1",
            "columns": [
                "First or given name(s) of presenter", "Last or family name of presenter",
                "Institution of presenter", "Email of presenter", "Talk Title", "SESSION", "Topic",
                "FirstNameLastNameAbstract.tex file with Talk Title and Abstract", "Acceptance"
            ]
        }
    }

def read_all_sheets(sheets, indir):
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

def read_schedule_days(interimdir, num_days=5):
    """Read schedule_day1.csv ... schedule_dayN.csv into a dictionary."""
    schedules = {}
    for i in range(1, num_days + 1):
        day_df = pd.read_csv(os.path.join(interimdir, f"schedule_day{i}.csv"))
        day_df = clean_df(day_df)
        schedules[f"day{i}"] = day_df
    return schedules

def add_join_keys(dfs):
    """Add join_key columns to each DataFrame in dfs."""
    # Plenary abstracts: join_key = last name + institution
    df = dfs["plenary_abstracts"]
    df["join_key"] = (df.iloc[:, 1] + " " + df.iloc[:, 2]).str.strip()

    # Special session submissions: join_key = Session Title
    df = dfs["special_session_submissions"]
    df["join_key"] = df["Session Title"].str.strip()

    # Special session abstracts: join_key = Special Session Title
    df = dfs["special_session_abstracts"]
    df["join_key"] = df["Special Session Title"].str.strip()

    # Contributed talk submissions: join_key = SESSION
    df = dfs["contributed_talk_submissions"]
    df["join_key"] = df["SESSION"].str.strip()

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

def merge_schedules_with_dfs(schedules, dfs):
    """Merge all schedule DataFrames with dfs using join_key, and add email columns."""
    for key, df1 in schedules.items():
        for key2, df2 in dfs.items():
            # select columns in df2 whose headers contains 'email'
            cols = df2.columns[df2.columns.str.contains("email", case=False)]
            # Create column called `email` in df1 with NaN 
            df1["email"] = pd.NA
            df1 = df1.merge(df2[[*cols, "join_key"]], on="join_key", how="left")
            # fill df1["email"] with values from df2[cols[0]], ..., df2[cols[-1]]
            for col in cols:
                df1["email"] = df1["email"].fillna(df2[col])
            break  # Only merge with the first matching df2
        schedules[key] = df1

def save_schedules(schedules, interimdir):
    """Save each schedule DataFrame to CSV and print head."""
    for key, df1 in schedules.items():
        print(df1.head(10))
        csv_file = os.path.join(interimdir, f"schedule_{key}_joined.csv")
        df1.to_csv(csv_file, index=False)
        print("Output saved to",  f"{csv_file}")

if __name__ == '__main__':
    sheets = get_sheets_dict()
    dfs = read_all_sheets(sheets, indir)
    schedules = read_schedule_days(interimdir, num_days=5)
    add_join_keys(dfs)
    add_schedule_join_keys(schedules)
    merge_schedules_with_dfs(schedules, dfs)
    save_schedules(schedules, interimdir)