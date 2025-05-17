# Read the google sheet https://docs.google.com/spreadsheets/d/1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4/edit?gid=0#gid=0

import pandas as pd

from config import *

def df_to_latex(df, filename, is_sideway=False):
    # Define row-level coloring based on keywords (case insensitive)
    def get_row_color(row):
        row_str = ' '.join(str(x) for x in row).lower()
        if any(kw.lower() in row_str for kw in ["Plenary"]):
            return r'\cellcolor{\PlenaryColor}'
        elif any(kw.lower() in row_str for kw in ["Break", "Registration", "Opening", "Reception", "Dinner", "Closing"]):
            return r'\cellcolor{\EmptyColor}'
        elif any(kw.lower() in row_str for kw in ["Technical"]):
            return r'\cellcolor{\SessionLightColor}'
        else:
            return r'\cellcolor{\SessionTitleColor}'

    # Escape '&' for LaTeX compatibility
    def escape_cell(x):
        return str(x).replace('&', r'\&')
    
    # Shorten timings description
    def shorten_cell(x):
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

    df = df.applymap(escape_cell).applymap(shorten_cell)

    # Move "Plenary Talk" from first to beginning of second column
    plen = "Plenary Talk"
    for idx, row in df.iterrows():
        if plen in str(row.iloc[0]):
            # Remove `plen` from first column
            row.iloc[0] = str(row.iloc[0]).replace(plen, "").strip()
            # Prepend to second column
            row.iloc[1] = plen + " by " + str(row.iloc[1])

    with open(filename, 'a') as f:
        if is_sideway:
            f.write("\\begin{sideways}\n")
        else:
            f.write("\\begin{table}\n")
        # Make first column narrower, rest normal width
        colspec = '>{\hsize=.5\hsize}X|>{\hsize=1.5\hsize}X'
        f.write(f"\\begin{{tabularx}}{{\\textwidth}}{{{colspec}}}\n")
        f.write("\\hline\n")
        # Write header
        f.write(f'\\multicolumn{{2}}{{l}}{{\\large\\textbf{{{df.columns[0]}}}}} \\\\\n')
        f.write("\\hline\n")
        # Write rows
        for idx, (_, row) in enumerate(df.iterrows()):
            color = get_row_color(row.values)
            row_str = ' & '.join([f'{color}{cell}' for cell in row.values])
            f.write(row_str + " \\\\\n")
        f.write("\\hline\n")
        f.write("\\end{tabularx}\n")
        if is_sideway:
            f.write("\\end{sideways}\n\n")
        else:
            f.write("\\end{table}\n\n")


def clean_df(df):
    # Remove all columns with NaN only
    df = df.dropna(axis=1, how='all')
    # Remove all row with NaN only
    df = df.dropna(axis=0, how='all')
    df_new = df.copy(deep=True)
    return df_new


if __name__ == '__main__':

    # Publish the sheet to the web or set sharing to "Anyone with the link"
    sheet_id = "1GR7LoeFuSbpomrHPnWqR9soJVkIkh56AAbAGx5zQGr4"
    sheet_name = "Sheet1"  # Change to your actual sheet name
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)

    df = clean_df(df)

    # save to SessionList.csv
    df.to_csv(f"{indir}SessionList.csv", index=False, quoting=1)

    schedule_tex = f"{outdir}Schedule.tex"
    with open(schedule_tex, "w") as f:
        f.write("")  # Clear the file

    num_cols = df.shape[1]

    for i in range(0, num_cols, 2):
        subdf = df.iloc[:, i:i+2]
        subdf.columns = [subdf.columns[1], ""]
        subdf = clean_df(subdf)
        subdf = subdf.fillna("")

        # Append mode for all but the first write
        df_to_latex(subdf, schedule_tex)

    print(f"Output: {schedule_tex}")