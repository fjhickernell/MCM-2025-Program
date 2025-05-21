#!/usr/bin/env python3
import pandas as pd
import os
import csv
from config import *
from util import * 
import re


def clean_name(name):
    # Make sure first letter of FirstName and LastName is capital letter. 
    # Also, the first letter after Hyphen in the Names should be capital letter. 
    # Other letters in names should be in small case.
    # Clean up FirstName and LastName columns in participants_df
    if pd.isna(name):
        return ""
    # Lowercase all, then capitalize first letter of each part, including after hyphens
    name = name.strip().lower()
    # Capitalize first letter and after hyphens
    name = re.sub(r'\b\w', lambda m: m.group(0).upper(), name)
    name = re.sub(r'(?<=-)\w', lambda m: m.group(0).upper(), name)

    return name

def format_organization(org):
    # Change df["Organization"] so that values such as "COMSATS UNIVERSITY ISLAMABAD-LAHORE" will have first capital letters and "University of Mannheim" will have "of" remaining as small letters
    
    if pd.isna(org) or not isinstance(org, str):
        return ""
    
    # First normalize to lowercase
    org = org.strip().lower()
    
    # List of words that should remain lowercase
    lowercase_words = ['of', 'and', 'the', 'for', 'in', 'at', 'by', 'with', 'to', 'de', 'del', 'di', 'la', 'el']
    
    # Split by spaces and capitalize each word unless in lowercase_words list
    words = org.split()
    formatted_words = []
    
    for i, word in enumerate(words):
        # Always capitalize first word and after hyphen/dash regardless of it being in lowercase_words
        if i == 0 or '-' in word:
            # Handle words with hyphens
            if '-' in word:
                subwords = word.split('-')
                word = '-'.join([sw.capitalize() for sw in subwords])
            else:
                word = word.capitalize()
        # Otherwise check if it's in the lowercase_words list
        elif word in lowercase_words:
            word = word.lower()
        else:
            word = word.capitalize()
        
        formatted_words.append(word)
    
    # Join words back together
    return ' '.join(formatted_words)

def cleanup_participant_data(df):
    """Clean and standardize participant data."""
    # Apply name formatting
    df["FirstName"] = df["FirstName"].apply(clean_name)
    df["LastName"] = df["LastName"].apply(clean_name)
    df["Organization"] = df["Organization"].apply(format_organization)
    
    # Apply manual corrections for special cases
    apply_name_corrections(df)
    apply_organization_corrections(df)
    
    # Validate data quality
    validate_participant_names(df)
    
    # Sort by LastName, FirstName
    return df.sort_values(by=["LastName", "FirstName"])

def apply_name_corrections(df):
    """Apply manual corrections to specific names."""
    last_name_dict = {
        "Noor Ul Amin": "Noor ul Amin",
        # Add other corrections here
    }
    for old_last_name, new_last_name in last_name_dict.items():
        df.loc[df["LastName"] == old_last_name, "LastName"] = new_last_name

def apply_organization_corrections(df):
    """Apply standardization to organization names."""
    org_dict = {
        "Work done during C. Huang's Ph.D. studies at Georgia Institute of Technology": "Georgia Institute of Technology",
        "INESC-ID, Rua Alves Redol 9, Lisbon, Portugal 1000-029": "INESC-ID",
        "Department of Mathematical Sciences, Tsinghua University": 'Tsinghua University',
        "Illinois Institute of Technology, Department of Applied Mathematics. Sandia National Laboratories.": 
            "Illinois Institute of Technology and Sandia National Laboratories.",
        "Department of Statistics, Columbia University": "Columbia University",
        "Department of Mathematics, Univeristy of Washington": "University of Washington",
        "KAUST: King Abdullah University of Science and Technology (KAUST)": "King Abdullah University of Science and Technology",
        "King Abdullah University of Science and Technology (KAUST)": "King Abdullah University of Science and Technology",
        "Istituto Nazionale di Fisica Nucleare (INFN), Laboratori Nazionali del Sud (LNS), Catania, Italy": 
            "Laboratori Nazionali del Sud",
        "Chair of Mathematics for Uncertainty Quantification, Department of Mathematics, RWTH- Aachen University": 
            "RWTH Aachen University",
        "Rwth--Aachen": "RWTH Aachen University",
    }
    for old_org, new_org in org_dict.items():
        df.loc[df["Organization"] == old_org, "Organization"] = new_org

def validate_participant_names(df):
    """Validate participant names and print warnings for issues."""
    mask = (df["FirstName"].str.len() == 1) | (df["LastName"].str.len() == 1)
    if mask.any():
        problem_names = df[mask][["FirstName", "LastName"]].values.tolist()
        for first, last in problem_names:
            print(f"ERROR: Invalid name length for participant: {first} {last}")



def extract_participants(dfs):
    """Extract participant information from all dataframes."""
    participants = []
    
    # Process each data source using specific helper functions
    if "plenary_abstracts" in dfs:
        participants.extend(extract_plenary_participants(dfs["plenary_abstracts"]))
    
    if "special_session_submissions" in dfs:
        participants.extend(extract_special_session_participants(dfs["special_session_submissions"], dfs))
    
    if "contributed_talk_submissions" in dfs:
        participants.extend(extract_contributed_talk_participants(dfs["contributed_talk_submissions"]))
    
    if "special_session_abstracts" in dfs:
        participants.extend(extract_special_abstracts_participants(dfs["special_session_abstracts"], dfs))

    # Create DataFrame from participants list
    df = pd.DataFrame(participants) if participants else pd.DataFrame()
    
    # Skip processing if the DataFrame is empty
    if df.empty:
        return df
    
    # Remove duplicates and problematic entries
    df = df.drop_duplicates(subset=["FirstName", "LastName", "SessionID"], keep="last")
    df = df[~((df["FirstName"].str.contains("-")) & (df["LastName"].str.contains("-")))]

    # Clean and standardize data
    df = cleanup_participant_data(df)
    
    # Sort by SessionID, LastName, FirstName for consistent output
    df = df.sort_values(by=["SessionID","LastName", "FirstName"])
    
    return df

def extract_plenary_participants(df):
    """Extract participants from plenary abstracts."""
    participants = []
    name_cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    
    for _, row in df.iterrows():
        if all(col in df.columns for col in name_cols):
            participants.append({
                "FirstName": row[name_cols[0]],
                "LastName": row[name_cols[1]],
                "SessionID": row.get("SessionID", "P"),
                "PageNumber": "",
                "Organization": row.get("Institution of presenter", "")
            })
            
    return participants

def extract_special_session_participants(df, dfs):
    """Extract participants from special session submissions."""
    participants = []
    
    # First, ensure institution columns exist
    for idx, i in enumerate(["first", "second", "third"], 1):
        org_col = f"Institution of {i} organizer"
        if org_col in df.columns and f"Organizer{idx} institution" not in df.columns:
            df[f"Organizer{idx} institution"] = df[org_col]
    
    # Process each row
    for idx, row in df.iterrows():
        session_id = row.get("SessionID", f"S{idx+1}")
        
        # Add organizers
        for i in range(1, 4):
            organizer_col = f"Organizer{i}"
            org_col = f"Institution of {'first' if i==1 else 'second' if i==2 else 'third'} organizer"
            
            if organizer_col in df.columns and pd.notna(row[organizer_col]):
                name_parts = row[organizer_col].split()
                if len(name_parts) >= 2:
                    participants.append({
                        "FirstName": " ".join(name_parts[:-1]),
                        "LastName": name_parts[-1],
                        "SessionID": session_id,
                        "PageNumber": "",
                        "Organization": row.get(org_col, "")
                    })
        
        # Add presenter if columns exist
        presenter_cols = ["Presenter 1 first or given name(s)", "Presenter 1 last or family name(s)"]
        if all(col in df.columns for col in presenter_cols):
            if pd.notna(row[presenter_cols[0]]) and pd.notna(row[presenter_cols[1]]):
                participants.append({
                    "FirstName": row[presenter_cols[0]],
                    "LastName": row[presenter_cols[1]],
                    "SessionID": session_id,
                    "PageNumber": "",
                    "Organization": row.get("Presenter 1 institution", "")
                })
                
    return participants

def extract_contributed_talk_participants(df):
    """Extract participants from contributed talk submissions."""
    participants = []
    name_cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    
    for _, row in df.iterrows():
        if all(col in df.columns for col in name_cols):
            # Extract session ID from SESSION column
            session_id = extract_technical_session_id(row)
            
            participants.append({
                "FirstName": row[name_cols[0]],
                "LastName": row[name_cols[1]],
                "SessionID": session_id or row.get("SessionID", "T"),
                "PageNumber": "",
                "Organization": row.get("Institution of presenter", "")
            })
                
    return participants

def extract_special_abstracts_participants(df, dfs):
    """Extract participants from special session abstracts."""
    participants = []
    name_cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    
    for _, row in df.iterrows():
        if all(col in df.columns for col in name_cols):
            # Find matching session ID
            session_id = find_matching_special_session_id(row, dfs)
            
            participants.append({
                "FirstName": row[name_cols[0]],
                "LastName": row[name_cols[1]],
                "SessionID": session_id or row.get("SessionID", "SS"),
                "PageNumber": "",
                "Organization": row.get("Institution of presenter", "")
            })
                
    return participants

def extract_technical_session_id(row):
    """Extract technical session ID from row data."""
    if "SESSION" in row and pd.notna(row["SESSION"]):
        match = re.search(r'Technical Session (\d+)', str(row["SESSION"]), re.IGNORECASE)
        if match:
            return f"T{match.group(1)}"
    return ""

def find_matching_special_session_id(row, dfs):
    """Find matching special session ID based on session title."""
    session_id = ""
    if "Special Session Title" in row and pd.notna(row["Special Session Title"]):
        title = row["Special Session Title"].lower().strip()
        if "special_session_submissions" in dfs:
            ss_df = dfs["special_session_submissions"]
            if "Session Title" in ss_df.columns and "SessionID" in ss_df.columns:
                matches = ss_df[ss_df["Session Title"].str.lower().str.strip() == title]
                if not matches.empty:
                    session_id = matches.iloc[0].get("SessionID", "")
    return session_id

def validate_session_participants(df):
    """Validate that each session has the expected number of participants.
    
    For plenary sessions (P*): Exactly 1 participant expected
    For all other sessions (S*, T*): Between 3-7 participants expected
    """
    grouped = df.groupby("SessionID")
    validation_issues = []
    
    for name, group in grouped:
        if str(name).startswith("P"):
            # Plenary sessions should have exactly 1 participant
            if len(group) != 1:
                validation_issues.append(f"ERROR: Plenary SessionID {name} has {len(group)} participants (expected 1)")
        else:
            # All other sessions should have 3-4 participants 
            if len(group) < 3 or len(group) > 7:
                session_title = group["SessionTitle"].iloc[0] if "SessionTitle" in group.columns else ""
                validation_issues.append(
                    f"ERROR: {name} {session_title} has {len(group)} participants (expected 3-7)"
                )
    
    # Print all validation issues
    for issue in validation_issues:
        print(issue)
    
    return len(validation_issues) == 0  # Return True if no issues found

if __name__ == "__main__":
    # Generate Participants.csv
    dfs = {}
    for key in ["special_session_submissions", "plenary_abstracts", "contributed_talk_submissions", "special_session_abstracts"]:
        dfs[key] = pd.read_csv(os.path.join(interimdir, f"{key}_sessionid.csv"))

    participants_df = extract_participants(dfs)
    validate_session_participants(participants_df)

    # Output Participants.csv
    output_file = os.path.join(outdir, "Participants.csv")
    participants_df.to_csv(output_file, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print("Output:", output_file)

