import os
import re
import pandas as pd
from config import *
import datetime


def parse_session_time(session_time: str) -> tuple[str, str, str, str]:
    """
    Parse session time string into components.
    Returns: (formatted_time, session_period, start_time, end_time)
    """
    m = re.match(
        r"([A-Za-z]+),\s*([A-Za-z]+\s+\d{1,2})(?:\s+(\d{1,2}:\d{2})?(?:[-–—]\s*(\d{1,2}:\d{2}))?)?\s*(.*)", 
        session_time
    )
    if not m:
        return session_time, "", "", ""

    day_of_week = m.group(1)
    date_str = m.group(2)
    start_time = m.group(3) or ""
    end_time = m.group(4) or ""
    
    try:
        if start_time:
            st = datetime.datetime.strptime(start_time, "%H:%M")
            session_period = "Morning" if st.hour < 12 else "Afternoon"
        else:
            session_period = ""
    except Exception:
        session_period = ""
        
    session_time_fmt = f"{day_of_week}, {date_str}, 2025 -- {session_period}"
    return session_time_fmt, session_period, start_time, end_time

def format_session_header(session_time_fmt: str, start_time: str, end_time: str, room: str) -> list[str]:
    """Generate the LaTeX header lines for a session."""
    return [
        r"\sessionPart{}% [1] part",
        r"{" + r"\hfill\timeslot{" + session_time_fmt + "}",
        "{" + start_time + "}{" + end_time + "} % Start and End time",
        "{" + room + "}} % Room "
    ]

def format_session_talk(title: str, presenter: str, talk_id: str) -> list[str]:
    """Generate the LaTeX lines for a single talk."""
    return [
        r"\sessionTalk{" + title + "}",
        "{" + presenter + "}",
        "{" + talk_id + "}"
    ]

def process_session_talks(df: pd.DataFrame) -> None:
    """Process all sessions and generate their LaTeX files."""
    for session_id, session_group in df.groupby("SessionID"):
        if not session_id:
            continue

        # Get session info from first row
        first_row = session_group.iloc[0]
        session_time = first_row.get("SessionTime", "")
        room = first_row.get("Room", "")

        # Parse session time
        session_time_fmt, _, start_time, end_time = parse_session_time(session_time)
        
        # Generate header
        lines = format_session_header(session_time_fmt, start_time, end_time, room)
        
        # Process talks
        talks_processed = 0
        for _, row in session_group.iterrows():
            if talks_processed >= 4:  # Max 4 talks per session
                break
                
            title = row.get("Talk Title", "").replace('Φ','$\Phi$').strip()
            presenter = row.get("Presenter", "").strip()
            if presenter == "":
                first_name = row.get("First or given name(s) of presenter", "").strip()
                last_name = row.get("Last or family name of presenter", "").strip()
                presenter = f"{first_name} {last_name}".strip()
            talk_id = row.get("TalkID", "").strip()
            
            if title and presenter and talk_id:
                lines.extend(format_session_talk(title, presenter, talk_id))
                talks_processed += 1

        # Write output file
        out_path = os.path.join(outdir, f"sess{session_id}.tex")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Wrote {out_path}")

def format_plenary_talk(
    time: str,
    room: str, 
    chair: str,
    speaker: str,
    title: str,
    talk_id: str
) -> str:
    """Generate LaTeX content for a plenary talk."""
    return "\n".join([
        r"\tablePlenary{" + time + "} % [1] time",
        "{" + room + "}\t% [2] room",
        "{" + chair + "}\t\t% [3] chair", 
        "{" + speaker + "}\t% [4] speaker",
        "{" + title + "}\t\t% [5] talk title",
        "{" + talk_id + "}\t\t% [6] talk id",
        r"\\\hline"
    ])

def process_plenary_talks(csv_path: str) -> None:
    """Process plenary talks CSV and generate individual .tex files with commented LaTeX block."""
    df = pd.read_csv(csv_path, dtype=str).fillna("")

    for _, row in df.iterrows():
        talk_id = row.get("TalkID", "").strip()
        if not talk_id:
            continue

        # Extract fields
        session_time_str = row.get("SessionTime", "").strip()
        # Extract time from SessionTime, e.g., "09:00-10:00" from "Wed, July 30 09:00–10:00"
        m = re.search(r"(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})", session_time_str)
        if m:
            time = f"{m.group(1)}--{m.group(2)}"
        else:
            time = ""

        #print(f"{session_time_str = }, {time = }")
        room = row.get("Room", "").strip()
        chair = row.get("Chair", "").strip()
        speaker = row.get("SessionTitle", "").strip()
        if speaker.startswith("Plenary Talk by "):
            speaker = speaker[len("Plenary Talk by "):]
        title = row.get("Talk Title", "").strip()

        # Compose LaTeX content with commented block
        content = "\n".join([
            "%\\begin{sideways}\\small",
            "%\\begin{tabularx}{\\textheight}{l*{\\numcols}{|Y}}",
            "%\t\\TableHeading{Monday, August 19, 2024 -- Afternoon }",
            "%\t\\\\\\toprule",
            "    %\\TableEvent{08:30 -- 12:30}{Registration}",
            "    %\\\\\\hline",
            "    %",
            format_plenary_talk(
                time=time,
                room=room,
                chair=chair,
                speaker=speaker,
                title=title,
                talk_id=talk_id
            ),
            "    %\\TableEvent{08:00 -- 12:30}{Registration -- Hall B (outside Lecture Hall 1)}",
            "    %\\\\",
            "%\\end{tabularx}",
            "%\\end{sideways}"
        ])

        # Write output file
        out_path = os.path.join(outdir, f"sess{talk_id}.tex")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content + "\n")

        print(f"Wrote {out_path}")

if __name__ == '__main__':
    # Generate `sess<SessionID>.tex` LaTeX files for contributed talks
    df = pd.read_csv(
        os.path.join(interimdir, "contributed_talk_submissions_talkid.csv"), 
        dtype=str
    ).fillna("")
    
    process_session_talks(df)

    # Generate `sess<SessionID>.tex` LaTeX files for special session talks
    df = pd.read_csv(
        os.path.join(interimdir, "special_session_abstracts_talkid.csv"), 
        dtype=str
    ).fillna("")
    
    process_session_talks(df)

    # Generate `sess<SessionID>.tex` LaTeX files for plenary talks
    plenary_csv = os.path.join(interimdir, "plenary_abstracts_talkid.csv")
    process_plenary_talks(plenary_csv)
