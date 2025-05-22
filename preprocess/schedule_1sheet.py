
import pandas as pd
from config import *
from util import *
import re

def get_row_color(row):
    """Return LaTeX color command based on keywords in the row (case insensitive)."""
    row_str = ' '.join(str(x) for x in row).lower()
    if "plenary" in row_str:
        return r'\cellcolor{\PlenaryColor}'
    elif any(kw in row_str for kw in ["break", "registration", "opening", "reception", "dinner", "closing"]):
        return r'\cellcolor{\EmptyColor}'
    elif "technical" in row_str:
        return r'\cellcolor{\SessionLightColor}'
    else:
        return r'\cellcolor{\SessionTitleColor}'

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

def clean_column_names(df):
    """Remove newlines and excess whitespace from column names."""
    df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()
    # Change Monday to Mon, etc.
    df.columns = df.columns.str.replace(r"Monday", "Mon", regex=False)
    df.columns = df.columns.str.replace(r"Tuesday", "Tue", regex=False)
    df.columns = df.columns.str.replace(r"Wednesday", "Wed", regex=False)
    df.columns = df.columns.str.replace(r"Thursday", "Thu", regex=False)
    df.columns = df.columns.str.replace(r"Friday", "Fri", regex=False)
    return df

def df_to_latex(df, filename, is_sideway=False):
    """Write a two-column DataFrame as a LaTeX tabularx table."""
    df = df[~df.apply(lambda x: x.str.contains('//', na=False)).any(axis=1)]   # remove rows with '//'
    df = clean_column_names(df)
    df = df.map(escape_cell).map(shorten_cell)
    df = move_plenary_to_second_column(df)  

    with open(filename, 'a') as f:
        if is_sideway: 
            f.write("\\begin{sideways}\n")
        else:
            f.write("\\begin{table}\n")
        # Make second column wider, first, third and fourth columns narrower
        #col_spec = '>{\\hsize=0.75\\hsize}X|>{\\hsize=2\\hsize}X|>{\\hsize=0.22\\hsize}X'
        col_spec = '>{\\hsize=0.47\\hsize}X|>{\\hsize=1.53\\hsize}X'
        f.write(f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}\n")
        f.write("\\hline\n")
        # Write header (merge two columns, large bold font)
        #f.write(f'\\multicolumn{{4}}{{l}}{{\\large\\textbf{{{df.columns[0]}}}}} \\\\\n')
        f.write(' & '.join([f'\\textbf{{{col}}}' for col in df.columns]) + ' \\\\\n')
        f.write("\\hline\n")
        # Write rows
        for _, row in df.iterrows():
            # Skip row if both cells are empty
            if all(str(cell).strip() == "" for cell in row.values):
                continue
            color = get_row_color(row.values)
            row_str = ' & '.join([f'{color}{cell}' for cell in row.values])
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

    schedule_tex = f"{outdir}Schedule.tex"
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

        # create a new df with first 2 columns of subdf for 1-sheet schedle
        subdf2 = subdf.iloc[:, :2]
        subdf2 = df_to_latex(subdf2, schedule_tex)
        subdf2.to_csv(f"{interimdir}schedule_day{j}.csv", index=False, quoting=1)
        j+=1
  
    print(f"Output: {schedule_tex}")