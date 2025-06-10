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
    apply_name_corrections(df)
    apply_organization_corrections(df)
    validate_participant_names(df)
    df["Organization"] = df["Organization"].str.replace("&", "and", regex=False)
    return df.sort_values(["LastName", "FirstName"])

def apply_name_corrections(df):
    for old, new in {"Noor Ul Amin": "Noor ul Amin"}.items():
        df.loc[df["LastName"] == old, "LastName"] = new

def apply_organization_corrections(df):
    for old, new in org_dict.items():
        df["Organization"] = df["Organization"].str.replace(old, new)
    df.loc[df["Organization"] == "RWTH Aachen", "Organization"] = "RWTH Aachen University"

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

if __name__ == "__main__":
    dfs = {}
    for key in ["special_session_submissions", "plenary_abstracts", "contributed_talk_submissions", "special_session_abstracts"]:
        try:
            dfs[key] = pd.read_csv(os.path.join(interimdir, f"{key}_talkid.csv"))
        except:
            dfs[key] = pd.read_csv(os.path.join(interimdir, f"{key}_sessionid.csv"))
    df = extract_participants(dfs)
    validate_session_participants(df)
    pd.Series(df["Organization"].unique(), name="Organization").sort_values().to_csv(f"{outdir}orgs.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)
    with open(f'{interimdir}short_org_dict.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Full Organization', 'Short Name'])
        for k, v in short_org_dict.items():
            writer.writerow([k, v])
    output_file = os.path.join(outdir, "Participants.csv")
    df.to_csv(output_file, index=False, header=False, quoting=csv.QUOTE_NONNUMERIC)
    print("Output:", output_file)