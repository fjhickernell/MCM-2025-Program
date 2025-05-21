import pandas as pd
import os
from config import indir, interimdir, gsheets
import util as ut


def read_google_sheets(sheets):
    """Read all sheets into a dictionary of DataFrames, selecting only needed columns."""
    dfs = {}
    for key, meta in sheets.items():
        df = ut.read_gsheet(
            sheet_id=meta["sheet_id"],
            sheet_name=meta["sheet_name"],
            indir=indir,
            out_csv=f"{key}.csv"
        )
        if meta["columns"] is not None:
            df = df[meta["columns"]]
        dfs[key] = df.copy(deep=True)
        print(f"Downloaded and filtered sheet: {indir}{key}.csv")
    return dfs


if __name__ == "__main__":
    talks_tex_dict = pd.read_csv()
    dfs = read_google_sheets(gsheets)
    ut.save_dfs(dfs, interimdir, "gsheet")