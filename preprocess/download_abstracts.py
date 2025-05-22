import pandas as pd
import os
from config import gsheets, interimdir, indir
import util as ut


def download_abstracts_from_csv(key, always_download=False):
    """Download abstracts for a given key from its TalkID or SessionID CSV."""
    suffix = "sessionid" if key == "special_session_submissions" else "talkid"
    csv_path = os.path.join(interimdir, f"{key}_{suffix}.csv")
    
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print(f"CSV file {csv_path} does not exist. Skipping {key}.")
        return
    
    df = pd.read_csv(csv_path)
    url_col = "FirstNameLastNameAbstract.tex file with Talk Title and Abstract" if key != "special_session_submissions" else "FirstNameLastNameSession.tex file with Session Title and Description"

    # Determine which ID column to use
    id_col = "SessionID" if key == "special_session_submissions" else "TalkID"
    
    # Check for required columns
    if url_col not in df.columns or id_col not in df.columns:
        print(f"Required columns '{url_col}' or '{id_col}' not found in {csv_path}. Skipping {key}.")
        return
    
    abstracts_dict = dict(zip(df[id_col], df[url_col]))
    abstracts_dir = os.path.join(indir, "abstracts")
    
    # Ensure the directory exists
    os.makedirs(abstracts_dir, exist_ok=True)
    
    for item_id, url in abstracts_dict.items():
        direct_url = ut.gdrive_direct_download(url) 
        
        try:
            local_filename = os.path.join(abstracts_dir, f"{item_id}.tex")
            
            # Check if the file already exists and item_id not NaN   
            if not pd.isna(item_id) and (not os.path.exists(local_filename) or always_download):
                ut.download_file(direct_url, abstracts_dir, item_id)
                print(f"Downloaded {item_id}.tex to {local_filename}")
            
            if pd.isna(item_id):
                print(f"ERROR: {key} {suffix} is missing,  {url = } ")
        except Exception as e:
            print(f"ERROR: {item_id = }, {direct_url = }, {url = } - {e}")


if __name__ == "__main__":
    # Process all gsheets keys except 'schedule'
    for key, meta in gsheets.items():
        if key == "schedule":
            continue
        download_abstracts_from_csv(key)
