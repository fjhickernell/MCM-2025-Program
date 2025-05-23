import os
import re
import pandas as pd
from config import *

def extract_talk_environment(tex_content: str) -> str:
    """
    Extracts the \begin{talk}...\end{talk} environment from a .tex file content.
    Raises ValueError if no talk environment is found in content.
    """
    pattern = re.compile(r"\\begin\{talk\}.*?\\end\{talk\}", re.DOTALL)
    match = pattern.search(tex_content)
    if not match:
        raise ValueError("No talk environment found")
    return match.group(0)


def load_ids(csv_path: str) -> list[str]:
    """
    Reads CSV and returns a cleaned list of IDs from TalkID or SessionID column.
    """
    df = pd.read_csv(csv_path, dtype=str)
    for col in ('TalkID', 'SessionID'):
        if col in df.columns:
            series = df[col].dropna().astype(str).str.strip()
            return [val for val in series if val and val.lower() != 'nan']
    raise KeyError("CSV must contain 'TalkID' or 'SessionID'.")


def sort_ids(ids: list[str]) -> list[str]:
    """
    Performs a natural sort on IDs, handling numeric and hyphen components.
    """
    try:
        return sorted(
            ids,
            key=lambda s: [int(tok) if tok.isdigit() else tok for tok in re.split(r'(\d+)', s)]
        )
    except Exception:
        return ids


def format_full_id(id_val: str, prefix: str) -> str:
    """
    Prepends prefix to id_val if not already present.
    """
    return f"{prefix}{id_val}" if prefix and not id_val.startswith(prefix) else id_val


def process_talk(id_val: str, prefix: str, tex_dir: str) -> str | None:
    """
    Extracts and updates a single talk environment for a given ID.
    Returns the processed talk block or None if missing/error.
    """
    full_id = format_full_id(id_val, prefix)
    tex_path = os.path.join(tex_dir, f"{full_id}.tex")
    if not os.path.isfile(tex_path):
        print(f"WARN: File not found: {tex_path}")
        return None

    # Read file with fallback encoding
    try:
        content = open(tex_path, 'r', encoding='utf-8').read()
    except UnicodeDecodeError:
        content = open(tex_path, 'r', encoding='latin-1').read()

    try:
        block = extract_talk_environment(content)
    except ValueError as e:
        #print(f"WARN: {e} in {tex_path}")
        return None

    # Replace placeholders
    for placeholder in ('[6]', '[8]'):
        pattern = r"\{\}\s*%\s*" + re.escape(placeholder)
        replacement = f"{{{full_id}}}% {placeholder}"
        block = re.sub(pattern, replacement, block)
    return block


def write_output(blocks: list[str], output_path: str, chapter: str = 'Plenary Talks') -> None:
    """
    Writes header and talk blocks to the output .tex file.
    """
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write(f"\\chapter{{{chapter}}}\n\\newpage\n\n")
        for block in blocks:
            out.write(block)
            out.write("\n\n")
    print(f"Output: {output_path}")


def generate_tex_talks(csv_path: str = "plenary_abstracts_talkid.csv",
                       tex_dir: str = ".",
                       output_path: str = "plenary_talks.tex",
                       strict: bool = False,
                       prefix: str = ""):
    """
    Main entry: loads IDs, sorts them, processes each talk, and writes output.
    """
    ids = load_ids(csv_path)
    sorted_ids = sort_ids(ids)

    blocks = []
    missing = []
    for id_val in sorted_ids:
        block = process_talk(id_val, prefix, tex_dir)
        if block is None:
            missing.append(format_full_id(id_val, prefix))
        else:
            blocks.append(block)

    if missing:
        msg = f"No talk or session environment found in .tex files:  {', '.join(missing)}"
        if strict:
            raise FileNotFoundError(msg)
        print(f"ERROR: {msg}")

    write_output(blocks, output_path)


if __name__ == '__main__':
    # map sheet keys to filename prefixes
    prefix_map = {
        'plenary_abstracts': 'P',
        'special_session_abstracts': 'S',
        'contributed_talk_submissions': 'T'
    }

    for key in ["contributed_talk_submissions", "special_session_abstracts", "plenary_abstracts"]: # "special_session_submissions", 
        if key in prefix_map:
            csv_path = os.path.join(interimdir, f"{key}_talkid.csv")
            tex_dir = os.path.join(indir, 'abstracts')
            out_path = os.path.join(outdir, f"{key}_talks.tex")
            generate_tex_talks(
                csv_path=csv_path,
                tex_dir=tex_dir,
                output_path=out_path,
                strict=False,
                prefix=prefix_map[key]
            )
    
    
   