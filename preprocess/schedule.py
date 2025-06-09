import pandas as pd
from config import *
from util import *
import re
from typing import Tuple, List, Dict

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
        (r'\bTechnical Session\b', 'Tech. Sess.'),
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
        (r'\bMachine Learning\b', 'ML'),
        (r'\bTrack [A-Z]:\s*\b', ''),
        (r'\band\b', '\&~'),
    ]
    for pattern, repl in replacements:
        title = re.sub(pattern, repl, title, flags=re.IGNORECASE)
    
    return title

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
    time_match = re.search(r'(\d{1,2}:\d{2})\s*[-–—]{1,2}\s*(\d{1,2}:\d{2})', session_time)
    return time_match.groups() if time_match else ("", "")

def generate_session_latex(row: pd.Series) -> str:
    """Generate LaTeX content for a single session."""
    session_id = str(row.get("SessionID", "")).strip()
    session_title = str(row.get("SessionTitle", "")).strip()
    session_time = str(row.get("SessionTime", "")).strip()
    start_time, end_time = extract_time_from_session(session_time)
    session_time = f"{start_time} -- {end_time}" if start_time and end_time else ""
    room = str(row.get("Room", "")).strip() or "TBD"
    chair = str(row.get("Chair", "")).strip() or "TBD"

    #short_session_title = shorten_titles(session_title)

    if session_id.startswith("P"):  # Plenary sessions
        return f"\\input{{sess{session_id}.tex}}\n"
    elif not session_id:  # breaks or opening/closing events
        #print(f"{session_title = }, {session_time = }")
        start_time, end_time = extract_time_from_session(session_time)
        time_str = f"{start_time}--{end_time}" if start_time and end_time else ""
        if session_title.lower().startswith("conference opening") or session_title.lower().startswith("closing"):
            event_details = f"{session_title} by {chair}, {room}"
            return f"\\OpeningClosingEvent{{{time_str}}}{{{event_details}}}\\\\\n"
        else: 
            return f"\\TableEvent{{{time_str}}}{{{session_title}, {room}}}\\\\\n"
    elif session_title.lower().startswith("track"):  # Parallel special/technical sessions
        # take out Track A, B, C, etc. from the title
        session_title = re.sub(r'Track [A-Z]:\s*', '', session_title, flags=re.IGNORECASE).strip()
        if session_id.startswith("S"):
            return (f"&\\tableSpecialCL{{{room}}}\n"
                    f"{{{session_title}}}\n"
                    f"{{{session_id}}}\n"
                    f"{{{chair}}}\n")
        elif session_id.startswith("T"):
            return (f"&\\tableContributedCL{{{room}}}\n"
                    f"{{{session_title}}}\n"
                    f"{{{chair}}}\n")
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
        speaker_clean = speaker.replace('\n', ' ').replace("å", "{\\aa}").strip()
        title_clean = title.replace('\n', ' ').replace('Φ','$\Phi$').replace("–", "---").replace("å", "{\\aa}").strip()
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
                continue 
    return session_tex_dict

def get_session_talks_dict(group: pd.DataFrame, outdir: str) -> Dict[str, List[Tuple[str, str, str]]]:
    """Loads LaTeX content for each session and extracts talks."""
    session_tex_dict = load_session_tex_dict(group, outdir)
    session_talks_dict = {}
    for sid, sess_content in session_tex_dict.items():
        session_talks_dict[sid] = process_session_talks(sess_content)
    return session_talks_dict

def generate_parallel_talks_latex(session_talks_dict: Dict[str, List[Tuple[str, str, str]]], row: pd.Series) -> str:
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
                talks_by_index.setdefault(i, []).append((None, None, None))

    start_time, end_time = extract_time_from_session(row.get("SessionTime", ""))

    for i in range(max_talks):
        # compute start_talk_time= start_time + i *30 mins and end_talk_time=start_talk_time + 30 mins
        start_talk_time = pd.to_datetime(start_time, format="%H:%M") + pd.Timedelta(minutes=i * 30)
        end_talk_time   = start_talk_time + pd.Timedelta(minutes=30)
        start_str       = start_talk_time.strftime("%H:%M")
        end_str         = end_talk_time.strftime("%H:%M")
        time_str        = f"\\tableTime{{{start_str}}}{{{end_str}}}"
        talks_latex += "\n\\rowcolor{\\SessionLightColor}\n"
        talks_latex += f"{time_str}\n"
        #print(f"{talks_by_index.get(i)}")
        for title, speaker, code in talks_by_index.get(i, []):
            if any(isinstance(x, str) and x.strip() for x in [title, speaker, code]):
                #print(f"title: {title}, speaker: {speaker}, code: {code}")
                #short_title = shorten_titles(title)
                talks_latex += f"&\\tableTalk{{ {speaker} }}\n{{ {title} }}\n{{{code}}}\n"
            else:
                talks_latex += "&\n"
        talks_latex += "\\\\\\hline\n"
    return talks_latex


def generate_schedule_latex(df: pd.DataFrame, outdir: str) -> str:
    """Generate the full LaTeX schedule."""
    latex_content = "\\begin{center}\n\n"
    grouped = df.groupby(["Date", "IsMorning"])
    grouped = sorted(grouped, key=lambda x: (pd.to_datetime(x[0][0], format="%b %d"), not x[0][1]))
    last_date = df["Date"].iloc[-1] if not df.empty else None

    for (date, is_morning), group in grouped:
        is_last_day = date == last_date
        #print(f"{date = }, {is_last_day = }")
        time_str = "Morning" if is_morning else "Afternoon"
        latex_content += "\\vspace{-10ex}\n" if (not (is_last_day and not is_morning)) else "" 
        latex_content += "\\begin{sideways}\\footnotesize\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}\n" if (not (is_last_day and not is_morning)) else "" 
        # Extract day of the week from date, e.g., Mon, Tue, etc.
        day_of_week = pd.to_datetime(date + " 2025", format="%b %d %Y").strftime("%a")
        # Add table heading for each group (morning/afternoon or last day)
        if not is_last_day:
            latex_content += f"\\TableHeading{{ {day_of_week}, {date}, 2025 -- {time_str} }}\n\\\\\\hline\n"
        else:
            if is_morning:
                latex_content += f"\\TableHeading{{ {day_of_week}, {date}, 2025 }}\n\\\\\\hline\n"
            else:
                latex_content += "\\hline\n"
        talks_latex = ""
        for _, row in group.sort_values("OrderInSchedule").iterrows():
            session_title = str(row.get("SessionTitle", "")).strip()

            is_first_parallel_talk = session_title.lower().startswith("track") and group['SessionTitle'].str.lower().str.startswith("track").idxmax() == row.name
            if is_first_parallel_talk:
                latex_content += r"\rowcolor{\SessionTitleColor}\cellcolor{\EmptyColor}" + "\n"
            session_latex = generate_session_latex(row)
            latex_content += session_latex
            is_last_parallel_talk = (session_title.lower().startswith("track") and row.name == group[group['SessionTitle'].str.lower().str.startswith("track")].index[-1])
            if is_last_parallel_talk:  # create talks in latex
                latex_content += "\\\\\\hline\n"
                session_talks_dict = get_session_talks_dict(group, outdir)
                talks_latex += generate_parallel_talks_latex(session_talks_dict, row)
                if talks_latex:
                    latex_content += talks_latex
        latex_content += "\n\n\\end{tabularx}\n\n\\end{sideways}\n\n" if (not (is_last_day and is_morning)) else "" 
    latex_content += "\\end{center}\n\n\\clearpage"

    # Remove "Track A:", "Track B:", etc. from the LaTeX content
    latex_content = re.sub(r'Track [A-Z]:\s*', '', latex_content, flags=re.IGNORECASE)
    # Remove number from "Technical Session 1", "Technical Session 2", etc.
    latex_content = re.sub(r'Technical Session \d+', 'Technical Session', latex_content, flags=re.IGNORECASE)
  
    return latex_content

if __name__ == '__main__':
    df = pd.read_csv(f"{outdir}schedule_full.csv", dtype=str).fillna("")
    df = prepare_dataframe(df)
    latex_content = generate_schedule_latex(df, outdir)
    schedule_tex = f"{outdir}Schedule.tex"
    with open(schedule_tex, "w") as f:
        f.write(latex_content)
    print(f"Output: {schedule_tex}")


