import pandas as pd
from config import *
from util import *
import re
from typing import Tuple, List, Dict

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare and clean the schedule dataframe."""
    df = clean_df(df)
    df["Date"] = df["SessionTime"].str.extract(r'(\w{3} \d{1,2})')[0].str.strip()
    df["Date"] = df["Date"].ffill()
    df["StartTime"] = df["SessionTime"].str.extract(r'(\d{1,2}:\d{2})')[0]
    df["IsMorning"] = df["StartTime"].apply(
        lambda x: pd.to_datetime(x, format="%H:%M").hour < 12 if pd.notnull(x) else False
    )
    df["OrderInSchedule"] = df["OrderInSchedule"].astype(int)
    return df.sort_values(["OrderInSchedule"])

def extract_time_from_session(session_time: str) -> Tuple[str, str]:
    """Extract start and end times from session time string."""
    time_match = re.search(r'(\d{1,2}:\d{2})[–-](\d{1,2}:\d{2})', session_time)
    return time_match.groups() if time_match else ("", "")

def generate_session_latex(row: pd.Series) -> str:
    """Generate LaTeX content for a single session."""
    session_id = str(row.get("SessionID", "")).strip()
    session_title = str(row.get("SessionTitle", "")).strip()
    session_time = str(row.get("SessionTime", "")).strip()
    room = str(row.get("Room", "")).strip() or "TBD"
    chair = str(row.get("Chair", "")).strip() or "TBD"

    if session_id.startswith("P"):
        return f"\\input{{sess{session_id}.tex}}\n"
    elif not session_id:
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

def process_session_talks(sess_content: str) -> List[Tuple[str, str, str]]:
    """Extracts talks from session LaTeX content."""
    talks = re.findall(
        r'\\sessionTalk\{([^\}]*)\}\s*\{([^\}]*)\}\s*\{([^\}]*)\}',
        sess_content, 
        re.DOTALL
    )
    talk_tuples = []
    for title, speaker, code in talks:
        speaker_clean = speaker.replace('\n', ' ').strip()
        title_clean = title.replace('\n', ' ').strip()
        code_clean = code.strip()
        talk_tuples.append((title_clean, speaker_clean, code_clean))
    return talk_tuples

def load_session_tex_dict(group: pd.DataFrame, outdir: str) -> Dict[str, str]:
    """Loads LaTeX content for each session in the group."""
    session_tex_dict = {}
    for sid in group['SessionID']:
        sid_str = str(sid).strip()
        if sid_str.startswith(("S", "T")):
            sess_file = f"{outdir}sess{sid_str}.tex"
            try:
                with open(sess_file, "r") as sf:
                    session_tex_dict[sid_str] = sf.read()
            except FileNotFoundError:
                print(f"WARN: {sess_file} not found.")
    return session_tex_dict

def get_session_talks_dict(group: pd.DataFrame, outdir: str) -> Dict[str, List[Tuple[str, str, str]]]:
    """Loads LaTeX content for each session and extracts talks."""
    session_tex_dict = load_session_tex_dict(group, outdir)
    session_talks_dict = {}
    for sid, sess_content in session_tex_dict.items():
        session_talks_dict[sid] = process_session_talks(sess_content)
    return session_talks_dict

def generate_talks_latex(session_talks_dict: Dict[str, List[Tuple[str, str, str]]], row: pd.Series) -> str:
    """Generate LaTeX for all talks in parallel sessions."""
    talks_latex = ""
    max_talks = max((len(talks) for talks in session_talks_dict.values()), default=0)
    talks_by_index = {}
    for talks in session_talks_dict.values():
        for i in range(max_talks):
            if i < len(talks):
                title, speaker, code = talks[i]
                talks_by_index.setdefault(i, []).append((title, speaker, code))
            else:
                talks_by_index.setdefault(i, [])

    start_time, end_time = extract_time_from_session(row.get("SessionTime", ""))
    time_str = f"\\tableTime{{{start_time}}}{{{end_time}}}"

    for i in range(max_talks):
        talks_latex += "\n\\rowcolor{\\SessionLightColor}\n"
        talks_latex += f"{time_str}\n"
        for title, speaker, code in talks_by_index.get(i, []):
            talks_latex += f"&\\tableTalk{{ {speaker} }}\n{{ {title} }}\n{{{code}}}\n"
        talks_latex += "\\\\\\hline\n"
    return talks_latex

def generate_schedule_latex(df: pd.DataFrame, outdir: str) -> str:
    """Generate the full LaTeX schedule."""
    latex_content = "\\begin{center}\n\\hspace*{-1.2cm}\n"
    grouped = df.groupby(["Date", "IsMorning"])
    grouped = sorted(grouped, key=lambda x: (pd.to_datetime(x[0][0], format="%b %d"), not x[0][1]))

    for (date, is_morning), group in grouped:
        time_str = "Morning" if is_morning else "Afternoon"
        latex_content += "\\begin{sideways}\\small\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}\n"
        latex_content += f"\\TableHeading{{ {date}, 2025 -- {time_str} }}\n\\\\\\hline\n"
        talks_latex = ""
        for _, row in group.sort_values("OrderInSchedule").iterrows():
            session_title = str(row.get("SessionTitle", "")).strip()
            is_first_parallel_talk = session_title.lower().startswith("track") and group['SessionTitle'].str.lower().str.startswith("track").idxmax() == row.name
            if is_first_parallel_talk:
                latex_content += r"\rowcolor{\SessionTitleColor}\cellcolor{\EmptyColor}" + "\n"
            session_latex = generate_session_latex(row)
            latex_content += session_latex
            is_last_parallel_talk = (session_title.lower().startswith("track") and row.name == group[group['SessionTitle'].str.lower().str.startswith("track")].index[-1])
            if is_last_parallel_talk:
                latex_content += "\\\\\\hline\n"
                session_talks_dict = get_session_talks_dict(group, outdir)
                talks_latex += generate_talks_latex(session_talks_dict, row)
        if talks_latex:
            latex_content += talks_latex
        latex_content += "\n\n\\end{tabularx}\n\n\\end{sideways}\n\n"
    latex_content += "\\end{center}\n\n\\clearpage"
    return latex_content

def main():
    df = pd.read_csv(f"{outdir}schedule_full.csv", dtype=str).fillna("")
    df = prepare_dataframe(df)
    latex_content = generate_schedule_latex(df, outdir)
    schedule_tex = f"{outdir}Schedule.tex"
    with open(schedule_tex, "w") as f:
        f.write(latex_content)
    print(f"Output: {schedule_tex}")

if __name__ == '__main__':
    main()