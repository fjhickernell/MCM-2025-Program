import os
import re
import pandas as pd
from config import *
import datetime
import util as ut


def parse_session_time(session_time: str) -> tuple[str, str, str, str]:
    """Parse session time string into components."""
    m = re.match(
        r"([A-Za-z]+),\s*([A-Za-z]+\s+\d{1,2})(?:\s+(\d{1,2}:\d{2})?(?:[-–—]\s*(\d{1,2}:\d{2}))?)?\s*(.*)", 
        session_time
    )
    if not m:
        return session_time, "", "", ""

    day_of_week, date_str, start_time, end_time = m.group(1), m.group(2), m.group(3) or "", m.group(4) or ""
    session_period = "Morning" if start_time and datetime.datetime.strptime(start_time, "%H:%M").hour < 12 else "Afternoon"
    session_time_fmt = f"{day_of_week}, {date_str}, 2025 -- {session_period}"
    return session_time_fmt, session_period, start_time, end_time


def format_session_header(session_time_fmt: str, start_time: str, end_time: str, room: str) -> list[str]:
    """Generate the LaTeX header lines for a session."""
    return [
        r"\sessionPart{}% [1] part",
        r"{\hfill\timeslot{" + session_time_fmt + "}",
        f"{{{start_time}}}{{{end_time}}} % Start and End time",
        f"{{{room}}}}} % Room "
    ]


def format_session_talk(title: str, presenter: str, talk_id: str) -> list[str]:
    """Generate the LaTeX lines for a single talk."""
    return [f"\\sessionTalk{{{title}}}", f"{{{presenter}}}", f"{{{talk_id}}}"]


def process_session_talks(df: pd.DataFrame, max_talks: int = 4) -> None:
    """Process all sessions and generate their LaTeX files."""
    for session_id, session_group in df.groupby("SessionID"):
        if not session_id:
            continue

        first_row = session_group.iloc[0]
        session_time_fmt, _, start_time, end_time = parse_session_time(first_row.get("SessionTime", ""))
        room = first_row.get("Room", "")
        lines = format_session_header(session_time_fmt, start_time, end_time, room)

        for _, row in session_group.head(max_talks).iterrows():
            title = (row.get("Talk Title", "")
                     .replace('Φ', '$\Phi$')
                     .replace("–", "---")
                     .strip())
            title = ut.clean_tex_content(title)  # Apply common text fixes
            presenter = row.get("Presenter", "").replace("å", "{\\aa}").strip()
            if not presenter:
                presenter = f"{row.get('First or given name(s) of presenter', '').strip()} {row.get('Last or family name of presenter', '').strip()}".strip()
            talk_id = row.get("TalkID", "").strip()
            if title and presenter and talk_id:
                lines.extend(format_session_talk(title, presenter, talk_id))

        out_path = os.path.join(outdir, f"sess{session_id}.tex")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Wrote {out_path}")


def format_plenary_talk(time: str, room: str, chair: str, speaker: str, title: str, talk_id: str) -> str:
    """Generate LaTeX content for a plenary talk."""
    return "\n".join([
        f"\\tablePlenary{{{time}}} % [1] time",
        f"{{{room}}}\t% [2] room",
        f"{{{chair}}}\t\t% [3] chair", 
        f"{{{speaker}}}\t% [4] speaker",
        f"{{{title}}}\t\t% [5] talk title",
        f"{{{talk_id}}}\t\t% [6] talk id",
        r"\\\hline"
    ])


def process_plenary_talks(csv_path: str) -> None:
    """Process plenary talks CSV and generate individual .tex files."""
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    for _, row in df.iterrows():
        talk_id = row.get("TalkID", "").strip()
        if not talk_id:
            continue

        session_time_str = row.get("SessionTime", "").strip()
        m = re.search(r"(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})", session_time_str)
        time = f"{m.group(1)}--{m.group(2)}" if m else ""

        content = format_plenary_talk(
            time=time,
            room=row.get("Room", "").strip(),
            chair=row.get("Chair", "").strip(),
            speaker=row.get("SessionTitle", "").replace("Plenary Talk by ", "").strip(),
            title=ut.clean_tex_content(row.get("Talk Title", "").strip()),
            talk_id=talk_id
        )

        out_path = os.path.join(outdir, f"sess{talk_id}.tex")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"Wrote {out_path}")


if __name__ == '__main__':
    # Generate LaTeX files for contributed talks
    for csv_file in ["contributed_talk_submissions_talkid.csv", "special_session_abstracts_talkid.csv"]:
        df = pd.read_csv(os.path.join(interimdir, csv_file), dtype=str).fillna("")
        process_session_talks(df)

    # Generate LaTeX files for plenary talks
    process_plenary_talks(os.path.join(interimdir, "plenary_abstracts_talkid.csv"))