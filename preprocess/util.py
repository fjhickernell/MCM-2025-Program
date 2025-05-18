import os
import pandas as pd
import urllib.parse

def clean_df(df):
    """Remove all columns and rows with only NaN values."""
    df = df.dropna(axis=1, how='all')
    df = df.dropna(axis=0, how='all')
    return df.copy(deep=True)

def read_gsheet(sheet_id, sheet_name, indir, out_csv, download_if_missing=True):
    """Read a Google Sheet into a DataFrame, downloading only if the local CSV does not exist."""
    # Publish the Google sheet to the web or set sharing to "Anyone with the link"
    csv_path = os.path.join(indir, out_csv)
    if not download_if_missing and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        #url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        sheet_name_encoded = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name_encoded}"
        df = pd.read_csv(url)
        df = clean_df(df)
        # Save to csv with double quotes for strings
        df.to_csv(csv_path, index=False, quoting=1)
        
    return df