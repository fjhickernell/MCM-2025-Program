
import pandas as pd
from config import *
from util import *
import re

def get_row_color(row):
    """Return LaTeX color command based on keywords in the row (case insensitive)."""
    row_str = ' '.join(str(x) for x in row).lower()
    if any(kw in row_str for kw in ["plenary", "opening"]): 
        return r'\cellcolor{\PlenaryColor}'
    elif any(kw in row_str for kw in ["break", "registration", "reception", "dinner", "closing"]):
        return r'\cellcolor{\EmptyColor}'
    elif "technical" in row_str:
        return r'\cellcolor{\SessionLightColor}'
    else:
        return r'\cellcolor{\SessionTitleColor}'

def shorten_titles(title):
    replacements = [
        (r'\bQuasi[- ]?Monte Carlo\b', 'QMC'),
        (r'\(Quasi-?\)?Monte Carlo', '(Q)MC'),
        (r'\bMonte Carlo\b', 'MC'),
        (r'\bMarkov Chain Monte Carlo\b', 'MCMC'),
        (r'\bMarkov Chain MC\b', 'MC'),
        (r'\bUncertainty Quantification\b', 'UQ'),
        (r'\bNext-generation\b', 'Next-gen'),
        (r'\bLow-discrepancy\b', 'LD'),
        (r'\bPartial Differential Equations\b', 'PDEs'),
        (r'\bStochastic Differential Equations\b', 'SDEs'),
        (r'\bExperimental Design\b', 'Exp. Design'),
        (r'\bBayesian\b', 'Bayes'),
        (r'\bRare Event Simulation\b', 'Rare Event Sim.'),
        (r'\bHamiltonian Monte Carlo\b', 'HMC'),
        (r'\bRandomized QMC\b', 'RQMC'),
        (r'\bImportance Sampling\b', 'IS'),
        (r'\bMultilevel\b', 'ML'),
        (r'\bSimulation\b', 'Sim.'),
        (r'\bOptimization\b', 'Opt.'),
        (r'\bSampling\b', 'Sampl.'),
        (r'\bAnalysis\b', 'Anal.'),
        (r'\bApplications\b', 'Appl.'),
        (r'\bComputational Methods\b', 'Comp. Methods'),
        (r'\bStatistical\b', 'Stat.'),
        (r'\bStatistics\b', 'Stat.'),
        (r'\bMathematical\b', 'Math.'),
        (r'\bMathematics\b', 'Math.'),
        (r'\bDesign of Experiments\b', 'DOE'),
        (r'\bAdaptive Hamiltonian MC\b', 'Adaptive HMC'),
        (r'\bDiscrepancy Theory\b', 'Discr. Theory'),
        (r'\bHigh-performance Computing\b', 'HPC'),
        (r'\bMachine Learning\b', 'ML')
    ]
    for pattern, repl in replacements:
        title = re.sub(pattern, repl, title, flags=re.IGNORECASE)
    
    return title

def escape_cell(x):
    """Escape special LaTeX characters."""
    return str(x).replace('&', r'\&')

def shorten_cell(x):
    """Shorten session/timing descriptions for LaTeX output."""
    s = str(x)
    s = s.replace(' Morning Parallel Sessions', '')
    s = s.replace(' Afternoon Parallel Sessions', '')
    s = s.replace('Morning', '')
    s = s.replace('Afternoon', '')
    s = s.replace(' — ', ' ')
    s = s.replace(' Lunch Break', '')
    s = s.replace(' Coffee Break', '')
    s = s.replace('Plenary Lecture', 'Plenary Talk')
    s = s.replace(' - Closing', '')
    s = re.sub(r'\s+', ' ', s)
    return s

def move_plenary_to_second_column(df):
    """If 'Plenary Talk' is in the first column, move it to the beginning of the second column."""
    plen = "Plenary Talk"
    for idx, row in df.iterrows():
        if plen in str(row.iloc[0]):
            # Remove 'Plenary Talk' from first column
            row.iloc[0] = str(row.iloc[0]).replace(plen, "").strip()
            # Prepend to second column
            row.iloc[1] = plen + " by " + str(row.iloc[1])

    return df

def move_track_to_second_column(df):
    """If 'Track X' (X = A, B, C, ...) is in the first column, move it to the beginning of the second column."""
    track_pattern = re.compile(r"(Track [A-Z])", re.IGNORECASE)
    for idx, row in df.iterrows():
        match = track_pattern.search(str(row.iloc[0]))
        if match:
            track = match.group(1)
            # Remove 'Track X' from first column
            row.iloc[0] = str(row.iloc[0]).replace(track, "").strip()
            # Prepend to second column
            row.iloc[1] = f"{track}: {row.iloc[1]}"
    return df

def clean_column_names(df):
    """Remove newlines and excess whitespace from column names."""
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()
    # Change Monday to Mon, etc.
    df.columns = df.columns.str.replace(r"Monday", "Mon", regex=False)
    df.columns = df.columns.str.replace(r"Tuesday", "Tue", regex=False)
    df.columns = df.columns.str.replace(r"Wednesday", "Wed", regex=False)
    df.columns = df.columns.str.replace(r"Thursday", "Thu", regex=False)
    df.columns = df.columns.str.replace(r"Friday", "Fri", regex=False)
    # Shorten months
    df.columns = df.columns.str.replace(r"July", "Jul", regex=False)
    df.columns = df.columns.str.replace(r"August", "Aug", regex=False)
    
    return df

def df_to_latex(df, filename, is_sideway=False):
    """Write a two-column DataFrame as a LaTeX tabularx table."""
    df = df[~df.apply(lambda x: x.str.contains('//', na=False)).any(axis=1)]   # remove rows with '//'
    df = clean_column_names(df)
    df = df.map(escape_cell).map(shorten_cell)
    df = move_plenary_to_second_column(df)  
    df = move_track_to_second_column(df)

    with open(filename, 'a') as f:
        if is_sideway: 
            f.write("\\begin{sideways}\n")
        else:
            f.write("\\begin{table}\n")
            # Add vertical space if first column header is "Wed, Jul 30"
            #if df.columns[0] == "Wed, Jul 30":
            f.write("\\vspace{-3ex}\n")
        # Make second column wider
        col_spec = '>{\\hsize=0.32\\hsize}X|>{\\hsize=1.7\\hsize}X'
        f.write(f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}\n")
        f.write("\\hline\n")
        # Write header (merge two columns, large bold font)
        f.write(' & '.join([f'\\textbf{{{col}}}' for col in df.columns]) + ' \\\\\n')
        f.write("\\hline\n")
        # Write rows
        for _, row in df.iterrows():
            # Skip row if both cells are empty
            if all(str(cell).strip() == "" for cell in row.values):
                continue
            color = get_row_color(row.values)
            row_str = ' & '.join([f'{color}{cell}' for cell in row.values])
            # Replace "Part " with "Part~" in LaTeX
            row_str = row_str.replace("Part ", "Part~")
            f.write(row_str + " \\\\\n")
        f.write("\\hline\n")
        f.write("\\end{tabularx}\n")
        if is_sideway:
            f.write("\\end{sideways}\n\n")
        else:
            f.write("\\end{table}\n\n")
 
    return df


if __name__ == '__main__':

    # Read the google sheet Schedule, 
    # https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0
    df = read_gsheet(sheet_id= "1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4", 
                     sheet_name= "SCHEDULE", 
                     indir=interimdir, 
                     out_csv="session_wide.csv")
    df = clean_df(df)

    # Read preprocess/interim/plenary_abstracts_talkid.csv
    plenary_df = pd.read_csv(f"{interimdir}plenary_abstracts_gsheet.csv", dtype=str).fillna("")
    plenary_df = clean_df(plenary_df)
    plenary_df["join_key"] = (
        plenary_df["First or given name(s) of presenter"].str.strip().str.lower() + " " +
        plenary_df["Last or family name of presenter"].str.strip().str.lower()
    ).str.strip()
    
    schedule_tex = f"{outdir}Schedule_1sheet.tex"
    with open(schedule_tex, "w") as f:
        f.write("")  # Clear the file
        #f.write("\\chapter{Schedule}\n")

    num_cols = df.shape[1]
    j=1
    sub_cols_len = 4
    for i in range(0, num_cols, sub_cols_len):
        subdf = df.iloc[:, i:i+sub_cols_len]
        # Only rename columns if both exist
        if subdf.shape[1] == sub_cols_len:
            subdf.columns = [subdf.columns[1], "Session", "Room", "Chair"]
        subdf = clean_df(subdf)
        subdf = subdf.fillna("")
        subdf.to_csv(f"{interimdir}schedule_day{j}_room_chair.csv", index=False, quoting=1)
        
        # Join with plenary_df
        subdf["join_key"] = subdf["Session"].str.lower().str.strip()
        subdf = subdf.merge(plenary_df[["Institution of presenter", "Talk Title", "join_key"]], how='left', on="join_key")
        
        # if "Institution of presenter", "Talk Title" both has non-NaN values, then join them to the value in "Session",
        # Session <- Session, Institution, Talk Title
        subdf["Session"] = (
            subdf["Session"].fillna("").str.strip() +
            (", " + subdf["Institution of presenter"].fillna("").str.strip()).where(subdf["Institution of presenter"].notna() & (subdf["Institution of presenter"].str.strip() != ""), "") +
            (", " + subdf["Talk Title"].fillna("").str.strip()).where(subdf["Talk Title"].notna() & (subdf["Talk Title"].str.strip() != ""), "")
        )

        # Shorten values like "University" as U in subdf["Session"]
        subdf["Session"] = subdf["Session"].str.replace(r"\bUniversity\b", "U", regex=True)
        subdf["Session"] = subdf["Session"].str.replace(r"\bENSAE, \b", "", regex=True)
        # apply shorten_titles() to subdf["Session"] values
        subdf["Session"] = subdf["Session"].apply(shorten_titles)
        
        # create a new df with first 2 columns of subdf for 1-sheet schedule
        subdf2 = subdf.iloc[:, :2].copy(deep=True)
        subdf2 = df_to_latex(subdf2, schedule_tex)
        subdf2.to_csv(f"{interimdir}schedule_day{j}.csv", index=False, quoting=1)
        
        j+=1
  
    print(f"Output: {schedule_tex}")