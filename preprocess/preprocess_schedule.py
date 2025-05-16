# Read the google sheet https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0

import pandas as pd

from config import *

def df_to_latex(df, filename, is_sideway=True):
    # Define row-level coloring based on keywords (case insensitive)
    def get_row_color(row):
        row_str = ' '.join(str(x) for x in row).lower()
        if any(kw.lower() in row_str for kw in ["Plenary"]):
            return r'\cellcolor{\PlenaryColor}'
        elif any(kw.lower() in row_str for kw in ["Break", "Registration", "Opening", "Reception"]):
            return r'\cellcolor{\EmptyColor}'
        elif any(kw.lower() in row_str for kw in ["Technical"]):
            return r'\cellcolor{\SessionLightColor}'
        else:
            return r'\cellcolor{\SessionTitleColor}'
    

    # Escape '&' for LaTeX compatibility
    def escape_cell(x):
        return str(x).replace('&', r'\&')

    df = df.applymap(escape_cell)

    with open(filename, 'a') as f:
        if is_sideway:
            f.write("\\begin{sideways}\n")
        else:
            f.write("\\begin{table}\n")
        f.write("\\begin{tabular}{%s}\n" % ('|'.join(['l'] + ['l'] * (df.shape[1] - 1))))
        f.write("\\hline\n")
        # Write header
        f.write(' & '.join([f'\\large\\textbf{{{col}}}' for col in df.columns]) + " \\\\\n")
        f.write("\\hline\n")
        # Write rows
        for idx, (_, row) in enumerate(df.iterrows()):
            color = get_row_color(row.values)
            row_str = ' & '.join([f'{color}{cell}' for cell in row.values])
            f.write(row_str + " \\\\\n")
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        if is_sideway:
            f.write("\\end{sideways}\n\n")
        else:
            f.write("\\end{table}\n\n")

 
if __name__ == '__main__':

    # Publish the sheet to the web or set sharing to "Anyone with the link"
    sheet_id = "1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4"
    sheet_name = "Sheet1"  # Change to your actual sheet name
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)

    # Remove all columns with NaN only
    df = df.dropna(axis=1, how='all')
    # Remove all row with NaN only
    df = df.dropna(axis=0, how='all')
    # Replace NaN with ""
    df = df.fillna("")

    # save to SessionList.csv
    df.to_csv(f"{indir}SessionList.csv", index=False, quoting=1)

    schedule_tex = f"{outdir}Schedule.tex"
    with open(schedule_tex, "w") as f:
        f.write("")  # Clear the file

    num_cols = df.shape[1]
    for i in range(0, num_cols, 2):
        subdf = df.iloc[:, i:i+2]
        subdf.columns = ["Timings, "+subdf.columns[1], ""]
        # Append mode for all but the first write
        df_to_latex(subdf, schedule_tex)

    print(f"Output: {schedule_tex}")