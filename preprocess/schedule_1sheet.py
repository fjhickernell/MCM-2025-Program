
import pandas as pd
from config import *
from util import *
import re



def get_row_color(row):
    """Return LaTeX color command based on keywords in the row (case insensitive)."""
    row_str = ' '.join(str(x) for x in row).lower()
    if any(kw in row_str for kw in ["plenary", "opening", "closing"]): 
        return r'\cellcolor{\PlenaryColor}'
    elif any(kw in row_str for kw in ["break", "registration", "reception", "dinner"]):
        return r'\cellcolor{\EmptyColor}'
    elif "technical" in row_str:
        return r'\cellcolor{\SessionLightColor}'
    else:
        return r'\cellcolor{\SessionTitleColor}'


def shorten_room_names(df):
    """Shorten room names in the DataFrame."""
    room_replacements = [
        (r"\bAuditorium\b", "Aud."),
        (r"\bBallroom\b", "Ballrm"),
        (r"\bLobby\b", "Lby"),
        (r"\bAlumni Lounge\b", "Alum."),
        (r"\bArts Center\b", "Arts Ctr.")
    ]
    return shorten_text(df, "Room", room_replacements)


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

def preprocess_dataframe(df):
    """Clean and preprocess the DataFrame."""
    df = df[~df.apply(lambda x: x.str.contains('//', na=False)).any(axis=1)]  # Remove rows with '//'
    df = clean_column_names(df)
    df = df.map(escape_cell).map(shorten_cell)
    df = move_plenary_to_second_column(df)
    df = move_track_to_second_column(df)
    return df

def add_room_information(df):
    """Add room information to the second column if available."""
    if 'Room' in df.columns:
        df.iloc[:, 1] = df.apply(
            lambda row: f"{row.iloc[1]} ({row['Room']})" if pd.notna(row.iloc[1]) and pd.notna(row['Room']) else row.iloc[1],
            axis=1
        )
    return df

def write_latex_table_header(f, df, is_sideway):
    """Write the LaTeX table header."""
    if is_sideway:
        f.write("\\begin{sideways}\n")
    else:
        f.write("\\begin{table}\n")
    f.write("{\\footnotesize\n")
    col_spec = '>{\\hsize=0.32\\hsize}X|>{\\hsize=1.7\\hsize}X'
    f.write(f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}\n")
    f.write("\\hline\n")
    f.write(' & '.join([f'\\textbf{{{col}}}' for col in df.columns]) + ' \\\\\n')
    f.write("\\hline\n")

def write_latex_table_rows(f, df):
    """Write the rows of the LaTeX table."""
    for _, row in df.iterrows():
        if all(str(cell).strip() == "" for cell in row.values):  # Skip empty rows
            continue
        color = get_row_color(row.values)
        row_str = ' & '.join([f'{color}{cell}' for cell in row.values])
        row_str = row_str.replace("Part ", "Part~")  # Replace "Part " with "Part~" in LaTeX
        f.write(row_str + " \\\\\n")

def write_latex_table_footer(f, is_sideway):
    """Write the LaTeX table footer."""
    f.write("\\hline\n")
    f.write("\\end{tabularx}\n")
    f.write("}\n")
    if is_sideway:
        f.write("\\end{sideways}\n\n")
    else:
        f.write("\\end{table}\n\n")


def df_to_latex(df, filename, is_sideway=False):
    """Write a two-column DataFrame as a LaTeX tabularx table."""

    df = add_room_information(df)
    df = df.iloc[:, :2]  # Keep only the first two columns

    # Write the LaTeX table to the file
    with open(filename, 'a') as f:
        write_latex_table_header(f, df, is_sideway)
        write_latex_table_rows(f, df)
        write_latex_table_footer(f, is_sideway)
    return df
 
if __name__ == '__main__':

    # Read the google sheet Schedule, 
    # https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0
    df = read_gsheet(sheet_id= "1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4", 
                     sheet_name= "SCHEDULE", 
                     indir=interimdir, 
                     out_csv="session_wide.csv")
    df = clean_df(df)

    # Read preprocess/interim/plenary_abstracts_gsheet.csv
    plenary_df = pd.read_csv(f"{interimdir}plenary_abstracts_gsheet.csv", dtype=str).fillna("")
    plenary_df = clean_df(plenary_df)
    plenary_df["join_key"] = (
        plenary_df["First or given name(s) of presenter"].str.strip().str.lower() + " " +
        plenary_df["Last or family name of presenter"].str.strip().str.lower()
    ).str.strip()
    
    schedule_tex = f"{outdir}Schedule_1sheet.tex"
    with open(schedule_tex, "w") as f:
        f.write("")  # Clear the file
        f.write("\\chapter{Schedule}\n")

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

        # If both "Institution of presenter" and "Talk Title" are present, append them to "Session"
        session = subdf["Session"].fillna("").str.strip()

        institution = subdf["Institution of presenter"].fillna("").str.strip()
        institution = institution.where(
            subdf["Institution of presenter"].notna() & (institution != ""), ""
        )
        institution = ", " + institution
        institution = institution.where(institution != ", ", "")

        talk_title = subdf["Talk Title"].fillna("").str.strip()
        talk_title = talk_title.where(
            subdf["Talk Title"].notna() & (talk_title != ""), ""
        )
        talk_title = ", " + talk_title
        talk_title = talk_title.where(talk_title != ", ", "")

        subdf["Session"] = session + institution + talk_title

        # Shorten values like "University" as U in subdf["Session"]
        subdf["Session"] = subdf["Session"].str.replace(r"\bUniversity\b", "U", regex=True)
        subdf["Session"] = subdf["Session"].str.replace(r"\bENSAE, \b", "", regex=True)
        
        # Shorten room names
        #subdf = shorten_room_names(subdf)

        # create a new df with first 2 columns of subdf for 1-sheet schedule
        subdf2 = subdf.iloc[:, :4].copy(deep=True)
        subdf2 = preprocess_dataframe(subdf2)
        subdf2.to_csv(f"{interimdir}schedule_day{j}.csv", index=False, quoting=1)

        # Preprocess the DataFrame
        df_to_latex(subdf2, schedule_tex)

        # apply shorten_titles() to subdf["Session"] values for latex table
        #subdf2["Session"] = subdf2["Session"].apply(shorten_titles)
    
        j+=1
  
    print(f"Output: {schedule_tex}")