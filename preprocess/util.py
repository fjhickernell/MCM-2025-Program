import os
import pandas as pd
import urllib.parse
import requests
import re

from config import *


pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)


def save_dfs(dfs, interimdir, filedes):
    """Save each schedule DataFrame in a dictionary to CSV"""
    for key, df in dfs.items():
        #print(df.head(10))
        csv_file = os.path.join(interimdir, f"{key}_{filedes}.csv")
        df.to_csv(csv_file, index=False)
        print("Output: ",  f"{csv_file}")


def clean_df(df):
    """Remove all columns and rows with only NaN values."""
    df = df.dropna(axis=1, how='all')
    df = df.dropna(axis=0, how='all')
    # for each str column, remove leading and trailing whitespace
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    return df.copy(deep=True)


def read_gsheet(sheet_id, sheet_name, indir, out_csv, always_download=True):
    """Read a Google Sheet into a DataFrame, downloading only if the local CSV does not exist."""
    csv_path = os.path.join(indir, out_csv)
    
    # Check if the file exists and should be downloaded
    if (not always_download) and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        df = pd.read_csv(url)
        df = clean_df(df)
        df.to_csv(csv_path, index=False, quoting=1)
    
    return df

def download_file(url, output_dir, session_id):
    """Download a file from a URL and save it in output_dir with session_id as the filename."""
    if not url or not isinstance(url, str) or not url.startswith("http"):
        print(f"Invalid URL for session {session_id}: {url}")
        return
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        filename = f"{session_id}.tex"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Failed to download {url} for session {session_id}: {e}")

def gdrive_direct_download(url):
    """Convert a Google Drive share/view URL to a direct download URL if possible."""
    patterns = [
        r"drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/uc\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/uc\?export=download&id=([a-zA-Z0-9_-]+)"
    ]
    
    for pat in patterns:
        match = re.search(pat, url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    return url  # Return original if not matched


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
        
        if meta["columns"] is not None:
            df = df[meta["columns"]]
        
        dfs[key] = df.copy(deep=True)
    
    return dfs


