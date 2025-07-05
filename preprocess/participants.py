import pandas as pd
import os
import csv
import re
from config import *
from util import *

# Utility functions

def print_wrong_group_counts(df, groupby="SessionID", title="Special Organizers", min_count=4, max_count=4):
    counts = df.groupby(groupby).size().reset_index(name=title).sort_values(by=title)
    filtered = counts[(counts[title] > max_count) | (counts[title] < min_count)]
    if not filtered.empty:
        print(filtered)

def clean_name(name):
    if pd.isna(name): return ""
    name = name.strip().lower()
    name = re.sub(r'\b\w', lambda m: m.group(0).upper(), name)
    name = re.sub(r'(?<=-)\w', lambda m: m.group(0).upper(), name)
    return name

def format_organization(org):
    if pd.isna(org) or not isinstance(org, str): return ""
    org = org.strip().rstrip(',').lower()
    lowercase = {'of','and','the','for','in','at','by','with','to','de','del','di','la','el'}
    words = org.split()
    def fmt_word(i, w):
        if i == 0 or '-' in w:
            return '-'.join(sw.capitalize() for sw in w.split('-'))
        return w if w in lowercase else w.capitalize()
    return ' '.join(fmt_word(i, w) for i, w in enumerate(words))

def cleanup_participant_data(df):
    df["FirstName"] = df["FirstName"].apply(clean_name)
    df["LastName"] = df["LastName"].apply(clean_name)
    df["Organization"] = df["Organization"].apply(format_organization)
    df = apply_name_corrections(df)
    df = apply_organization_corrections(df)
    validate_participant_names(df)
    df["Organization"] = df["Organization"].str.replace("&", "and", regex=False)
    return df.sort_values(["LastName", "FirstName"])

def apply_name_corrections(df):
    name_dict = {
        "Noor Ul Amin": "Noor ul Amin"
    }
    for old, new in name_dict.items():
        df.loc[df["LastName"] == old, "LastName"] = new
    return df

def apply_organization_corrections(df):
    for old, new in org_dict.items():
        df["Organization"] = df["Organization"].str.replace(old, new)
    return df

def validate_participant_names(df):
    mask = (df["FirstName"].str.len() == 1) | (df["LastName"].str.len() == 1)
    for first, last in df[mask][["FirstName", "LastName"]].values.tolist():
        print(f"ERROR: Invalid name length for participant: {first} {last}")

def extract_participants(dfs):
    participants = []
    if "plenary_abstracts" in dfs:
        participants += extract_plenary_participants(dfs["plenary_abstracts"])
    if "special_session_submissions" in dfs:
        participants += extract_special_session_participants(dfs["special_session_submissions"], dfs)
    if "contributed_talk_submissions" in dfs:
        participants += extract_contributed_talk_participants(dfs["contributed_talk_submissions"])
    if "special_session_abstracts" in dfs:
        participants += extract_special_abstracts_participants(dfs["special_session_abstracts"], dfs)
    df = pd.DataFrame(participants) if participants else pd.DataFrame()
    if df.empty: return df
    df = df.drop_duplicates(["FirstName", "LastName", "SessionID"]).loc[~((df["FirstName"].str.contains("-")) & (df["LastName"].str.contains("-")))]
    df = cleanup_participant_data(df)
    # Print potential duplicated names defined as same first and last name but different organizations
    dupes = df.groupby(["FirstName", "LastName"])["Organization"].nunique()
    dupes = dupes[dupes > 1]
    if not dupes.empty:
        print("\nWARNING: Potential duplicated names with different organizations:")
        print(df[df.set_index(["FirstName", "LastName"]).index.isin(dupes.index)][["FirstName", "LastName", "Organization"]])

    return df.sort_values(["LastName", "FirstName"])

def extract_plenary_participants(df):
    if df.empty: return []
    cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    if not all(c in df.columns for c in cols): return []
    return pd.DataFrame({
        "FirstName": df[cols[0]],
        "LastName": df[cols[1]],
        "SessionID": df.get("SessionID", pd.Series("P", index=df.index)),
        "PageNumber": "",
        "Organization": df.get("Institution of presenter", pd.Series("", index=df.index))
    }).to_dict('records')

def extract_special_session_participants(df, dfs):
    for idx, i in enumerate(["first", "second", "third"], 1):
        org_col = f"Institution of {i} organizer"
        if org_col in df.columns and f"Organizer{idx} institution" not in df.columns:
            df[f"Organizer{idx} institution"] = df[org_col]
    org_cols = [f"Organizer{i}" for i in range(1, 4)]
    org_inst_cols = [f"Organizer{i} institution" for i in range(1, 4)]
    org_df = pd.melt(df, id_vars=["SessionID"] if "SessionID" in df.columns else [], value_vars=org_cols, var_name="OrganizerNum", value_name="FullName")
    org_inst_df = pd.melt(df, id_vars=["SessionID"] if "SessionID" in df.columns else [], value_vars=org_inst_cols, var_name="OrganizerNum", value_name="Organization")
    org_df["Organization"] = org_inst_df["Organization"]
    org_df = org_df.dropna(subset=["FullName"])
    name_split = org_df["FullName"].str.rsplit(" ", n=1, expand=True)
    org_df["FirstName"] = name_split[0]
    org_df["LastName"] = name_split[1] if name_split.shape[1] > 1 else ""
    org_df["PageNumber"] = ""
    org_participants = org_df.to_dict("records")
    presenter_participants = []
    for i in range(1, 5):
        pcols = [f"Presenter {i} first or given name(s)", f"Presenter {i} last or family name(s)"]
        org_col = f"Presenter {i} institution"
        if all(c in df.columns for c in pcols):
            valid = df[pcols[0]].notna() & df[pcols[1]].notna()
            subset = df.loc[valid]
            if not subset.empty:
                presenter_participants += pd.DataFrame({
                    "FirstName": subset[pcols[0]],
                    "LastName": subset[pcols[1]],
                    "SessionID": subset.get("SessionID", pd.Series([f"S{j+1}" for j in range(len(subset))], index=subset.index)),
                    "PageNumber": "",
                    "Organization": subset.get(org_col, pd.Series("", index=subset.index))
                }).to_dict("records")
    presenter_df = pd.DataFrame(presenter_participants)
    print_wrong_group_counts(presenter_df, groupby="SessionID", title='Special Presenters')
    organizers_df = pd.DataFrame(org_participants)
    participants = pd.concat([organizers_df, presenter_df], ignore_index=True)
    print_wrong_group_counts(organizers_df, groupby="SessionID", title='Special Organizers', min_count=1, max_count=3)
    return participants.to_dict('records')

def extract_contributed_talk_participants(df):
    participants = []
    cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    for _, row in df.iterrows():
        if all(c in df.columns for c in cols):
            talk_id = extract_technical_talk_id(row)
            participants.append({
                "FirstName": row[cols[0]],
                "LastName": row[cols[1]],
                "SessionID": talk_id or row.get("TalkID", "T"),
                "PageNumber": "",
                "Organization": row.get("Institution of presenter", "")
            })
    return participants

def extract_special_abstracts_participants(df, dfs):
    cols = ["First or given name(s) of presenter", "Last or family name of presenter"]
    if not all(c in df.columns for c in cols): return []
    result_df = pd.DataFrame({
        "FirstName": df[cols[0]],
        "LastName": df[cols[1]],
        "SessionID": "",
        "PageNumber": "",
        "Organization": df.get("Institution of presenter", pd.Series("", index=df.index))
    })
    if "Special Session Title" in df.columns and "special_session_submissions" in dfs:
        ss_titles = df["Special Session Title"].str.lower().str.strip()
        ss_df = dfs["special_session_submissions"]
        ss_map = dict(zip(
            ss_df["Session Title"].str.lower().str.strip(),
            ss_df["SessionID"] if "SessionID" in ss_df.columns else ["" for _ in range(len(ss_df))]
        ))
        result_df["SessionID"] = ss_titles.map(ss_map).fillna(df.get("SessionID", "SS"))
    else:
        result_df["SessionID"] = df.get("SessionID", "SS")
    return result_df.to_dict("records")

def extract_technical_session_id(row):
    if "SESSION" in row and pd.notna(row["SESSION"]):
        m = re.search(r'Technical Session (\d+)', str(row["SESSION"]), re.IGNORECASE)
        if m: return f"T{m.group(1)}"
    return ""

def extract_technical_talk_id(row):
    if "SESSION" in row and pd.notna(row["SESSION"]):
        m = re.search(r'T(\d+)-{\d}', str(row["TalkID"]), re.IGNORECASE)
        if m: return f"T{m.group(1)}"
    return ""

def find_matching_special_session_id(row, dfs):
    if "Special Session Title" in row and pd.notna(row["Special Session Title"]):
        title = row["Special Session Title"].lower().strip()
        if "special_session_submissions" in dfs:
            ss_df = dfs["special_session_submissions"]
            if "Session Title" in ss_df.columns and "SessionID" in ss_df.columns:
                matches = ss_df[ss_df["Session Title"].str.lower().str.strip() == title]
                if not matches.empty:
                    return matches.iloc[0].get("SessionID", "")
    return ""

def validate_session_participants(df):
    grouped = df.groupby("SessionID")
    issues = []
    for name, group in grouped:
        if str(name).startswith("P"):
            if len(group) != 1:
                issues.append(f"ERROR: Plenary SessionID {name} has {len(group)} participants (expected 1)")
        elif str(name).startswith("S"):
            minp, maxp = 4, 7
            if not (minp <= len(group) <= maxp):
                title = group["Session Title"].iloc[0] if "Session Title" in group.columns else ""
                issues.append(f"ERROR: {name} {title} has {len(group)} participants (expected {minp}-{maxp})")
    for issue in issues: print(issue)
    return not issues

def parse_committee(file_path):
    """Parse organizing committee members from a LaTeX file.
    
    Parses lines like "Sou-Cheng Choi, \\emph{Illinois Institute of Technology} \\\\", 
    or "Miguel Arratia (Department of Physics and Astronomy, U California, Riverside)"
    into structured participant data. 

    If input contains department information, e.g., "Department of Statistics and Actuarial Science, U Waterloo", then it will return "U Waterloo"
    
    Args:
        file_path (str): Path to the organizing committee LaTeX file
        
    Returns:
        list: List of participant dictionaries with FirstName, LastName, etc.
    """
    if not os.path.exists(file_path):
        return []
    
    organizers = []
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('%'):  # Skip empty lines and comments
            continue
            
        # Remove trailing backslashes and clean up
        line = re.sub(r'\\+$', '', line).strip()
        
        full_name = ""
        org = ""
        
        # Pattern 1: "Name, \emph{Organization}"
        match = re.match(r'^(.+?),\s*\\emph\{(.+?)\}', line)
        if match:
            full_name = match.group(1).strip()
            org = match.group(2).strip()
        else:
            # Pattern 2: "Name (Organization)"
            match = re.match(r'^(.+?)\s*\((.+?)\)$', line)
            if match:
                full_name = match.group(1).strip()
                org = match.group(2).strip()
            else:
                # If no organization pattern found, treat entire line as name
                full_name = line.strip()
                org = ""
        
        # if org contains 'U' as short name for 'University', replace it with "University"
        if org:
            # Replace standalone 'U' with 'University' (word boundary matching)
            org = re.sub(r'\bU\b', 'University', org)
        
        if full_name:
            # Split name into first and last
            name_parts = full_name.rsplit(' ', 1)
            if len(name_parts) == 2:
                first, last = name_parts
            else:
                first = full_name
                last = ""
            
            # Extract university from department information if present
            # e.g., "Department of Statistics and Actuarial Science, U Waterloo" -> "U Waterloo"
            if org and ',' in org:
                # Split by comma and take the last part (usually the university)
                org_parts = [part.strip() for part in org.split(',')]
                if len(org_parts) >= 2:
                    # Take the last part as the university name
                    org = org_parts[-1]
        
            # if first name contains middle initial, remove middle
            
            organizers.append({
                "FirstName": first,
                "LastName": last,
                "SessionID": "org_com" if file_path.endswith("organizing_com.tex") else "sci_com" if file_path.endswith("sci_com.tex") else "steer_com" if file_path.endswith("steering_com.tex") else "students" if file_path.endswith("students.tex") else "",
                "PageNumber": "",
                "Organization": org if org else "Organizing Committee"
            })
    
    return organizers

def add_committee_members():
    """Add committee members from various committee files to the participants DataFrame.
    
    Args:
        df (pd.DataFrame): Existing participants DataFrame
        
    Returns:
        pd.DataFrame: Updated DataFrame with committee members added
    """
    committee_df = pd.DataFrame()
    committees = [
        ("organizing_com.tex", "organizing committee"),
        ("sci_com.tex", "scientific committee"), 
        ("steering_com.tex", "steering committee"),
        ("students.tex", "student assistants")
    ]
    
    for filename, committee_name in committees:
        committee_file = os.path.join(indir, filename)
        committee_members = parse_committee(committee_file)
        if committee_members:
            committee_df = pd.concat([committee_df, pd.DataFrame(committee_members)], ignore_index=True)
            print(f"Added {len(committee_members)} {committee_name} members")
    
    return committee_df

def add_session_chairs():
    """Add session chairs from schedule_day{i}_room_chair.csv files.
    """
    chairs = []
    
    for day in range(1, 6):  # Days 1 to 5
        chair_file = os.path.join(interimdir, f"schedule_day{day}_room_chair.csv")
        if not os.path.exists(chair_file):
            print(f"Warning: {chair_file} not found")
            continue
            
        try:
            df_day = pd.read_csv(chair_file)
            
            # Check if Chair column exists and has data
            if 'Chair' not in df_day.columns:
                print(f"Warning: 'Chair' column not found in {chair_file}")
                continue
                
            # Filter out empty chairs and non-person entries
            valid_chairs = df_day[
                df_day['Chair'].notna() & 
                (df_day['Chair'].str.strip() != '') &
                ~df_day['Chair'].str.contains('Coffee Break|Registration|Lunch', case=False, na=False)
            ]['Chair'].unique()
            
            # Process each chair name
            for chair_name in valid_chairs:
                chair_name = chair_name.strip()
                if not chair_name:
                    continue
                    
                # Split name into first and last
                name_parts = chair_name.rsplit(' ', 1)
                if len(name_parts) == 2:
                    first_name, last_name = name_parts
                else:
                    first_name = chair_name
                    last_name = ""
                
                chairs.append({
                    "FirstName": first_name,
                    "LastName": last_name,
                    "SessionID": f"schedule{day}",
                    "PageNumber": "",
                    "Organization": ""
                })
                
        except Exception as e:
            print(f"Error reading {chair_file}: {e}")
            continue
    
    chairs_df = pd.DataFrame(chairs)
    if not chairs_df.empty:
        # Remove duplicates (same person might chair multiple sessions)
        chairs_df = chairs_df.drop_duplicates(subset=['FirstName', 'LastName'])
        print(f"Found {len(chairs_df)} unique session chairs")
    
    return chairs_df

def generate_participants_latex(participants_csv_file):
    """Generate LaTeX content for the participants list from the CSV file."""
    from collections import defaultdict
    
    latex_content = ""
    latex_content += "\\chapter{List of Participants and Committee Members}\n"
    latex_content += "\\setlength{\\columnsep}{1cm}\n"
    latex_content += "\\begin{multicols}{2}\n"
    latex_content += "\\small\\raggedright\n"
    
    # Read all participants and group by name
    participants = defaultdict(list)
    with open(participants_csv_file, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        for val in reader:
            key = (val[0].strip(), val[1].strip(), val[4].strip())  # (FirstName, LastName, Organization)
            participants[key].append(val)

    for (first, last, org), vals in participants.items():
        # Collect all session IDs for this participant
        session_ids = [v[2] for v in vals if v[2]]
        # Use the first session as the main one, up to 6 more as extra braces
        main_session = session_ids[0] if session_ids else ''
        extra_sessions = session_ids[1:5] if len(session_ids) > 1 else []
        extra_sessions += [''] * (6 - len(extra_sessions))
        org_str = "Unknown org" if not org else org
        partstrng = f"\\participantne{{{first} {last}}}\n{{{org_str}}}\n"
        partstrng += f"{{{main_session}}}"
        for s in extra_sessions:
            partstrng += f"\n{{{s}}}"
        latex_content += partstrng + "\n"

    latex_content += "\\end{multicols}\n"
    latex_content = clean_tex_content(latex_content)  # Apply common text fixes
    
    return latex_content
    
if __name__ == "__main__":

    # Add committee members from various committee files
    df = add_committee_members()

    # Add chairs from interim/schedule_day{i}_room_chair.csv, for i = 1 to 5
    chairs_df = add_session_chairs()
    if not chairs_df.empty:
        df = pd.concat([df, chairs_df], ignore_index=True)
        print(f"Added {len(chairs_df)} session chairs")
    
    # Add chairs_df to df
    df = pd.concat([df, chairs_df], ignore_index=True)

    # Generate participants CSV file
    dfs = {}
    for key in ["special_session_submissions", "plenary_abstracts", "contributed_talk_submissions", "special_session_abstracts"]:
        try:
            dfs[key] = pd.read_csv(os.path.join(interimdir, f"{key}_talkid.csv"))
        except:
            dfs[key] = pd.read_csv(os.path.join(interimdir, f"{key}_sessionid.csv"))
    df2 = extract_participants(dfs)

    # Include only committee members in df if they are also participants in df2
    df = df.merge(df2[['FirstName', 'LastName']].drop_duplicates(), 
                  on=['FirstName', 'LastName'], 
                  how='inner')
    print(f"Filtered to {len(df)} committee members or chairs who are also session participants")
    
    # Add all session participants to the final list
    df = pd.concat([df, df2], ignore_index=True)

    # if Organization is empty (e.g., in chair_df), groupby first and last name, and fill from other non-empty rows
    df["Organization"] = df.groupby(["FirstName", "LastName"])["Organization"].transform(lambda x: x.ffill().bfill().iloc[0] if not x.empty else "")

    validate_session_participants(df)
    # output organization to a csv file
    pd.Series(df["Organization"].unique(), name="Organization").sort_values().to_csv(f"{outdir}orgs.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
    with open(f'{interimdir}short_org_dict.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Full Organization', 'Short Name'])
        for k, v in short_org_dict.items():
            writer.writerow([k, v])
    
    # Save participants CSV
    participants_csv_file = os.path.join(outdir, "Participants.csv")
    df.to_csv(participants_csv_file, index=False, header=False, quoting=csv.QUOTE_NONNUMERIC)
    print("Output:", participants_csv_file)
    
    # Generate participants LaTeX file
    latex_content = generate_participants_latex(participants_csv_file)
    participants_tex_file = f"{outdir}Participants.tex"
    with open(participants_tex_file, 'w') as fpart:
        fpart.write(latex_content)
    print(f"Output: {participants_tex_file}")