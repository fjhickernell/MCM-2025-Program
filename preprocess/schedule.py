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


if __name__ == '__main__':

    # Read preprocess/out/schedule_full.csv
    df = pd.read_csv(f"{outdir}schedule_full.csv", dtype=str).fillna("")
    df = clean_df(df)

    # Add a column to extract the date, e.g., Jul 28
    df["Date"] = df["SessionTime"].str.extract(r'(\w{3} \d{1,2})')[0].str.strip()
    df["Date"] = df["Date"].ffill()
    # df["SessionTime"] contains strings like "Mon, Jul 28 08:00–17:30". Add a column to decide from start time (08:00) if it is morning
    # Extract the start time (e.g., 08:00) and determine if it is morning (before 12:00)
    df["StartTime"] = df["SessionTime"].str.extract(r'(\d{1,2}:\d{2})')[0]
    df["IsMorning"] = df["StartTime"].apply(lambda x: pd.to_datetime(x, format="%H:%M").hour < 12 if pd.notnull(x) else False)
    # Change column OrderInScheule to int
    df["OrderInSchedule"] = df["OrderInSchedule"].astype(int)
    # Sort the DataFrame before grouping
    df = df.sort_values(["OrderInSchedule"])
    

    # Create a LaTeX file for the schedule
    schedule_tex = f"{outdir}Schedule.tex"
    latex_content = ""
    #latex_content += "\\chapter{Schedule}\n\n"
    latex_content += "\\begin{center}\n\\hspace*{-1.2cm}\n"

    # group by Date and IsMorning
    grouped = df.groupby(["Date", "IsMorning"])

    # Iterate over each group in order of Date and IsMorning (morning first)
    grouped = sorted(grouped, key=lambda x: (pd.to_datetime(x[0][0], format="%b %d"), not x[0][1]))
    for (date, is_morning), group in grouped:
        talks_latex = ""
        # Sort by OrderInSchedule to ensure correct order within the group
        group = group.sort_values("OrderInSchedule")
        # Write section header
        numcols = 4  # Set this to the desired number of columns
        latex_content += "\\begin{sideways}\\small\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}\n"
        # write date and time, e.g., \TableHeading{ Mon, Aug 19, 2024 -- Morning }
        time_str = "Morning" if is_morning else "Afternoon"
        latex_content += f"\\TableHeading{{ {date}, 2025 -- {time_str} }}\n"
        latex_content += "\\\\\hline\n"

        last_time = None
        for idx, row in group.iterrows():
         
            session_id = str(row.get("SessionID", "")).strip()
            session_title = str(row.get("SessionTitle", "")).strip()
            session_time = str(row.get("SessionTime", "")).strip()
            speaker = str(row.get("Speaker", "")).strip()
            room = str(row.get("Room", "")).strip() or "Room TBD"
            chair = str(row.get("Chair", "")).strip() or "Chair TBD"
            order = row.get("OrderInSchedule", "")
            #print(f"{session_id = }, {session_title = }, {order = }")
            # Extract start/end time for \tableTime
            time_match = re.search(r'(\d{1,2}:\d{2})[–-](\d{1,2}:\d{2})', session_time)
            start_time, end_time = (time_match.groups() if time_match else ("", ""))
            ### Write row
            # TableEvent: SessionID empty or startswith P
            if session_id.startswith("P"):
                # write "\input{P1.tex}" where P1 is the SessionID value
                if session_id:
                    latex_content += f"\\input{{sess{session_id}.tex}}\n"
            elif session_id == "": # Coffee breaks, etc
                if start_time and end_time:
                    latex_content += f"\\TableEvent{{{start_time} -- {end_time}}}{{{session_title}}}\\\\\n"
                else:
                    latex_content += f"\\TableEvent{{}}{{{session_title}}}\\\\\n"
            # tableSpecialCL: SessionID startswith S
            elif session_title.lower().startswith("track"):
                if group[group["SessionTitle"].str.lower().str.startswith("track")].index[0] == idx:
                    latex_content += "\\rowcolor{\\SessionTitleColor}\\cellcolor{\\EmptyColor}\n"
                    
                if session_id.startswith("S"):
                    latex_content += f"\\tableSpecialCL{{ {room} }}\n"
                    latex_content += f"{{ {session_title} }}\n"
                    latex_content += f"{{ {session_id} }}\n"
                    latex_content += f"{{ {chair} }}\n"
                elif session_id.startswith("T"):
                    latex_content += f"\\tableContributedCL{{ {room} }}\n"
                    latex_content += f"{{ {session_title} }}\n"
                    latex_content += f"{{ {chair} }}\n"
            # Default: just print session info
            else:
                latex_content += f"{session_time} & {session_title} \\\\\n"

            ### Now process the talks for each parallel session
            # For each session in the group, if session_id startswith "P" or "T", process the corresponding sess<session_id>.tex file
            if session_id.startswith("S") or session_id.startswith("T"):
                sess_file = f"{outdir}sess{session_id}.tex"
                try:
                    with open(sess_file, "r") as sf:
                        sess_content = sf.read()
                except FileNotFoundError:
                    print(f"WARN: {sess_file} not found.")
                    continue

                # Extract session time from \sessionPart line if present
                #print(f"\n{sess_content = }\n")
                part_match = re.search(r'\\sessionPart\{.*?\}.*?\\timeslot\{.*?\}\{(\d{1,2}:\d{2})\}\{(\d{1,2}:\d{2})\}', sess_content, re.DOTALL)
                if part_match:
                    start, end = part_match.groups()
                else:
                    # fallback to row2's SessionTime
                    session_time2 = str(row.get("SessionTime", "")).strip()
                    time_match2 = re.search(r'(\d{1,2}:\d{2})[–-](\d{1,2}:\d{2})', session_time2)
                    start, end = (time_match2.groups() if time_match2 else ("", ""))
                    #print(f"\n{session_time2 = }, {start = }, {end = }\n")
                
                # Choose row color
                row_color = r"\rowcolor{\SessionLightColor}" if session_id.startswith("P") else r"\rowcolor{\SessionDarkColor}"

                # Find all talks: \sessionTalk{title}{speaker}{code}
                talks = re.findall(
                    r'\\sessionTalk\{([^\}]*)\}\s*\{([^\}]*)\}\s*\{([^\}]*)\}',
                    sess_content, re.DOTALL
                )
                #print(f"{session_id = }, {talks =}")

                # Build the row: \rowcolor ... \tableTime ... &\tableTalk{...}{...}{...} ...
                row_tex = f"{row_color}\n\\tableTime{{{start}}}{{{end}}}\n"
                for t in talks:
                    speaker = t[1].replace('\n', ' ').strip()
                    title = t[0].replace('\n', ' ').strip()
                    code = t[2].strip()
                    row_tex += f"&\\tableTalk{{ {speaker} }}\n{{ {title} }}\n{{{code}}}\n"
                    #print(f"\n{speaker = }, {title = }, {code = }\n")
            
 
                row_tex += "\\\\\hline\n\n"
                talks_latex += row_tex

        latex_content += "\\\\\hline\n\n"
        

        # After all rows, insert talks_latex if any
        if talks_latex:
            latex_content += talks_latex

        # Close the tabularx environment
        latex_content += "\\end{tabularx}\n\n\\end{sideways}\n\n"
    latex_content += "\\end{center}\n\n\\clearpage"

    with open(schedule_tex, "w") as f:
        f.write(latex_content)

    print(f"Output: {schedule_tex}")