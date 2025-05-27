import pandas as pd
from config import *
from util import *
import re
from typing import Tuple, List, Dict

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare and clean the schedule dataframe."""
    df = clean_df(df)
    
    # Add date column
    df["Date"] = df["SessionTime"].str.extract(r'(\w{3} \d{1,2})')[0].str.strip()
    df["Date"] = df["Date"].ffill()
    
    # Add time-related columns
    df["StartTime"] = df["SessionTime"].str.extract(r'(\d{1,2}:\d{2})')[0]
    df["IsMorning"] = df["StartTime"].apply(
        lambda x: pd.to_datetime(x, format="%H:%M").hour <= 12 if pd.notnull(x) else False
    )
    
    # Convert and sort
    df["OrderInSchedule"] = df["OrderInSchedule"].astype(int)
    return df.sort_values(["OrderInSchedule"])

def extract_time_from_session(session_time: str) -> Tuple[str, str]:
    """Extract start and end times from session time string."""
    time_match = re.search(r'(\d{1,2}:\d{2})[–-](\d{1,2}:\d{2})', session_time)
    return time_match.groups() if time_match else ("", "")

def process_session_talks(session_id: str, outdir: str) -> str:
    """Process talks for a given session and return LaTeX content."""
    sess_file = f"{outdir}sess{session_id}.tex"
    try:
        with open(sess_file, "r") as sf:
            sess_content = sf.read()
    except FileNotFoundError:
        print(f"WARN: {sess_file} not found.")
        return ""

    # Extract session time
    part_match = re.search(
        r'\\sessionPart\{.*?\}.*?\\timeslot\{.*?\}\{(\d{1,2}:\d{2})\}\{(\d{1,2}:\d{2})\}', 
        sess_content, 
        re.DOTALL
    )
    start, end = part_match.groups() if part_match else ("", "")
    
    # Process talks
    row_color = r"\rowcolor{\SessionLightColor}" if session_id.startswith("P") else r"\rowcolor{\SessionDarkColor}"
    talks = re.findall(
        r'\\sessionTalk\{([^\}]*)\}\s*\{([^\}]*)\}\s*\{([^\}]*)\}',
        sess_content, 
        re.DOTALL
    )
    
    # Build LaTeX content
    row_tex = f"{row_color}\n\\tableTime{{{start}}}{{{end}}}\n"
    for title, speaker, code in talks:
        speaker_clean = speaker.replace('\n', ' ').strip()
        title_clean = title.replace('\n', ' ').strip()
        code_clean = code.strip()
        row_tex += (
            f"&\\tableTalk{{ {speaker_clean} }}\n"
            f"{{ {title_clean} }}\n"
            f"{{ {code_clean} }}\n"
        )
    
    return row_tex + "\\\\\hline\n\n"

def generate_session_latex(row: pd.Series) -> str:
    """Generate LaTeX content for a single session."""
    session_id = str(row.get("SessionID", "")).strip()
    session_title = str(row.get("SessionTitle", "")).strip()
    session_time = str(row.get("SessionTime", "")).strip()
    room = str(row.get("Room", "")).strip() or "Room TBD"
    chair = str(row.get("Chair", "")).strip() or "Chair TBD"

    if session_id.startswith("P"):
        return f"\\input{{sess{session_id}.tex}}\n"
    elif not session_id:  # Coffee breaks, etc
        start_time, end_time = extract_time_from_session(session_time)
        time_str = f"{start_time} -- {end_time}" if start_time and end_time else ""
        return f"\\TableEvent{{{time_str}}}{{{session_title}}}\\\\\n"
    elif session_title.lower().startswith("track"):
        if session_id.startswith("S"):
            return (f"&\\tableSpecialCL{{ {room} }}\n"
                   f"{{ {session_title} }}\n"
                   f"{{ {session_id} }}\n"
                   f"{{ {chair} }}\n")
        elif session_id.startswith("T"):
            return (f"&\\tableContributedCL{{ {room} }}\n"
                   f"{{ {session_title} }}\n"
                   f"{{ {chair} }}\n")
    
    return f"{session_time} & {session_title} \\\\\n"

def main():
    # Read input file
    df = pd.read_csv(f"{outdir}schedule_full.csv", dtype=str).fillna("")
    df = prepare_dataframe(df)

    # Create LaTeX content
    latex_content = "\\begin{center}\n\\hspace*{-1.2cm}\n"
    
    # Group and sort by date and time
    grouped = df.groupby(["Date", "IsMorning"])
    grouped = sorted(grouped, key=lambda x: (pd.to_datetime(x[0][0], format="%b %d"), not x[0][1]))
    
    for (date, is_morning), group in grouped:
        time_str = "Morning" if is_morning else "Afternoon"
        
        # Start table environment
        latex_content += "\\begin{sideways}\\small\\begin{tabularx}{\\textheight}{l*{\\numcols2}{|Y}}\n"
        latex_content += f"\\TableHeading{{ {date}, 2025 -- {time_str} }}\n\\\\\\hline\n"
        
        # Process sessions
        talks_latex = ""
        for _, row in group.sort_values("OrderInSchedule").iterrows():
            session_title = str(row.get("SessionTitle", "")).strip()
            if session_title.lower().startswith("track") and group['SessionTitle'].str.lower().str.startswith("track").idxmax() == row.name:
                latex_content += r"\rowcolor{\SessionTitleColor}\cellcolor{\EmptyColor}" + "\n"
            session_latex = generate_session_latex(row)
            latex_content += session_latex
            # Add \\\\hline after the last row that starts with "Track" in the group
            if (session_title.lower().startswith("track") and row.name == group[group['SessionTitle'].str.lower().str.startswith("track")].index[-1]):
                latex_content += "\\\\\\hline\n"
            
            # Process talks if applicable
            """
            session_id = str(row.get("SessionID", "")).strip()
            if session_id.startswith(("S", "T")):
                talks_latex += process_session_talks(session_id, outdir)
            """
        # Add talks and close table
        if talks_latex:
            latex_content += talks_latex
        latex_content += "\n\n\\end{tabularx}\n\n\\end{sideways}\n\n"
    
    latex_content += "\\end{center}\n\n\\clearpage"
    
    # Write output
    schedule_tex = f"{outdir}Schedule.tex"
    with open(schedule_tex, "w") as f:
        f.write(latex_content)
    
    print(f"Output: {schedule_tex}")

if __name__ == '__main__':
    main()