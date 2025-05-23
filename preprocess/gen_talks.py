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
        raise ValueError("ERROR: No talk environment found in content.")
    return match.group(0)


def generate_tex_talks(csv_path: str = "plenary_abstracts_talkid.csv",
                       tex_dir: str = ".",
                       output_path: str = "plenary_talks.tex",
                       strict: bool = False,
                       prefix: str = ""):
    """
    Reads a CSV with either 'TalkID' or 'SessionID', extracts each \begin{talk}...
    \end{talk} from corresponding .tex files, and writes them sorted into one .tex.

    Placeholders {}% [8] and {}% [6] are replaced by the full ID (prefix+ID).

    Parameters:
    - csv_path: CSV listing ID values.
    - tex_dir: Directory containing the .tex files named by prefix+ID.
    - output_path: Path for the generated .tex file.
    - strict: If True, abort on missing files; otherwise log and continue.
    - prefix: Letter prefix for filenames (e.g., 'P', 'S', 'T').
    """
    df = pd.read_csv(csv_path, dtype=str)
    # pick ID column
    if 'TalkID' in df.columns:
        id_col = 'TalkID'
    elif 'SessionID' in df.columns:
        id_col = 'SessionID'
    else:
        raise KeyError("CSV must contain 'TalkID' or 'SessionID'.")

    # raw IDs (without prefix)
    raw_series = df[id_col].dropna().astype(str).str.strip()
    raw_ids = [rid for rid in raw_series if rid and rid.lower() != 'nan']
    # natural sort (handles hyphens)
    try:
        sorted_ids = sorted(
            raw_ids,
            key=lambda s: [int(tok) if tok.isdigit() else tok for tok in re.split(r'(\d+)', s)]
        )
    except Exception:
        sorted_ids = raw_ids[:]
    #print(f"{sorted_ids = }")

    with open(output_path, 'w', encoding='utf-8') as out_file:
        out_file.write("\\chapter{Plenary Talks}\n")
        out_file.write("\\newpage\n\n")
        missing = []

        for id_val in sorted_ids:
            if prefix and not id_val.startswith(prefix):
                full_id = f"{prefix}{id_val}"
            else:
                full_id = id_val
            tex_file = os.path.join(tex_dir, f"{full_id}.tex")
            if not os.path.isfile(tex_file):
                msg = f"File not found: {tex_file}"
                if strict:
                    raise FileNotFoundError(msg)
                print(f"WARN: {msg}; skipping.")
                missing.append(full_id)
                continue

            content = open(tex_file, 'r', encoding='latin-1').read()
            try:
                talk_env = extract_talk_environment(content)
            except ValueError as e:
                print(f"Error in {tex_file}: {e}")
                continue

            # replace placeholders with full_id
            talk_env = re.sub(r"\{\}\s*%\s*\[8\]", f"{{{full_id}}}% [8]", talk_env)
            talk_env = re.sub(r"\{\}\s*%\s*\[6\]", f"{{{full_id}}}% [6]", talk_env)

            out_file.write(talk_env)
            out_file.write("\n\n")

        if missing:
            print(f"Warning: Missing talks for IDs: {', '.join(missing)}.")
        print(f"Output: {output_path}")


if __name__ == '__main__':
    # map sheet keys to filename prefixes
    prefix_map = {
        'plenary_abstracts': 'P',
        'special_session_abstracts': 'S',
        'contributed_talk_submissions': 'T'
    }

    for key in ["contributed_talk_submissions", "special_session_abstracts", "plenary_abstracts"]:
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
    
    
        #  ["special_session_submissions"]: