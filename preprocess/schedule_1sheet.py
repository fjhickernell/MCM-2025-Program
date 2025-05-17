
import pandas as pd
from config import *
from util import *

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

def df_to_latex(df, filename, is_sideway=False):
    """Write a two-column DataFrame as a LaTeX tabularx table."""
    df = df.pipe(lambda d: d.map(escape_cell)).pipe(lambda d: d.map(shorten_cell))
    df = move_plenary_to_second_column(df)

    with open(filename, 'a') as f:
        if is_sideway:
            f.write("\\begin{sideways}\n")
        else:
            f.write("\\begin{table}\n")
        # Make first column narrower, second wider
        colspec = '>{\hsize=.5\hsize}X|>{\hsize=1.5\hsize}X'
        f.write(f"\\begin{{tabularx}}{{\\textwidth}}{{{colspec}}}\n")
        f.write("\\hline\n")
        # Write header (merge two columns, large bold font)
        f.write(f'\\multicolumn{{2}}{{l}}{{\\large\\textbf{{{df.columns[0]}}}}} \\\\\n')
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


if __name__ == '__main__':

    # Read the google sheet https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0
    df = read_gsheet(sheet_id= "1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4", 
                     sheet_name= "Sheet1", 
                     indir=indir, 
                     out_csv="SessionList.csv")

    schedule_tex = f"{outdir}Schedule.tex"
    with open(schedule_tex, "w") as f:
        f.write("")  # Clear the file
        f.write("\\chapter{Schedule}\n")

    num_cols = df.shape[1]
    for i in range(0, num_cols, 2):
        subdf = df.iloc[:, i:i+2]
        # Only rename columns if both exist
        if subdf.shape[1] == 2:
            subdf.columns = [subdf.columns[1], ""]
        subdf = clean_df(subdf)
        subdf = subdf.fillna("")
        df_to_latex(subdf, schedule_tex)
  
    print(f"Output: {schedule_tex}")