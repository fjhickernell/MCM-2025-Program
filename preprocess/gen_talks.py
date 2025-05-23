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

def process_talk(id_val: str, prefix: str, tex_dir: str, session_time:str) -> str | None:
    """
    Extracts and normalizes a talk environment from a .tex file.
    Ensures exactly 9 argument slots, fills missing with "",
    overrides talk-id ([8]) with full_id, sets field 9 to "photo",
    preserves the abstract body, and optionally adds \clearpage for plenary.
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

    # Extract the talk block
    try:
        block = extract_talk_environment(content)
    except ValueError:
        return None

    # Split into lines for body extraction
    raw_lines = block.splitlines()
    # Locate begin/end
    try:
        begin_idx = next(i for i, l in enumerate(raw_lines) if re.match(r"^\\begin\{talk\}", l))
        end_idx   = next(i for i, l in enumerate(raw_lines) if re.match(r"^\\end\{talk\}", l))
    except StopIteration:
        return None
    # Identify field lines (slots 1–9)
    field_idxs = [i for i, l in enumerate(raw_lines)
                  if re.match(r"^\s*\{.*\}\s*%\s*\[\d+\]", l)]
    last_field_idx = max(field_idxs) if field_idxs else begin_idx
    # Abstract body is between last field and \end{talk}
    body_lines = raw_lines[last_field_idx+1:end_idx]

    # --- Parse existing fields by position ---
    raw_args = [re.match(r"^\s*\{([^}]*)\}", l).group(1)
                for i, l in enumerate(raw_lines)
                if re.match(r"^\s*\{([^}]*)\}", l)]
    # Initialize slots 1–9 to empty
    args = {i: '' for i in range(1, 10)}
    # Fill from parsed values, in order
    for idx, val in enumerate(raw_args, start=1):
        if idx > 9:
            break
        args[idx] = val.strip()

    # Override specific slots
    args[7] = session_time
    args[8] = full_id       # talk id
    args[9] = 'photo'       # always use "photo" for field 9

    # Build normalized talk block with descriptions
    descriptions = {
        1: 'talk title',
        2: 'speaker name',
        3: 'affiliations',
        4: 'email',
        5: 'coauthors',
        6: 'special session',
        7: 'time slot',
        8: 'talk id',
        9: 'session id or photo',
    }
    lines = ['\\begin{talk}']
    for i in range(1, 10):
        lines.append(f"  {{{args[i]}}}% [{i}] {descriptions[i]}")
    # Append existing abstract body, preserving indent
    for bl in body_lines:
        lines.append(bl)
    lines.append('\\end{talk}')

    # For plenary talks (prefix 'P'), add a page break after
    if prefix == 'P':
        lines.append('')
        lines.append('\\clearpage')

    return '\n'.join(lines)


def write_output(blocks: list[str], output_path: str, chapter: str = 'Plenary Talks') -> None:
    """
    Writes header and talk blocks to the output .tex file.
    """
    header = f"\\chapter{{{chapter}}}\n\\newpage\n\n"
    body = "\n".join(blocks)
    # remove a trailing “\clearpage” (plus any blank lines after it)
    #body = re.sub(r"\\clearpage\s*\\?$", "", body, flags=re.MULTILINE)

    # Now open-and-write *everything* inside the with-block
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write(header)
        out.write(body)

    print(f"Output: {output_path}")


def generate_tex_talks(csv_path: str = "plenary_abstracts_talkid.csv",
                       tex_dir: str = ".",
                       output_path: str = "plenary_talks.tex",
                       strict: bool = False,
                       prefix: str = ""):
    """
    Main entry: load IDs, sort them, process each talk, and write output.
    """
    # Read full table so we can build an ID → SessionTime lookup
    df = pd.read_csv(csv_path, dtype=str)
    id_col = "TalkID" if "TalkID" in df.columns else "SessionID"
    time_map = dict(
        zip(
            df[id_col].astype(str).str.strip(),
            df.get("SessionTime", pd.Series()).fillna("").astype(str)
        )
    )

    # Load and sort IDs 
    ids = load_ids(csv_path)
    sorted_ids = sort_ids(ids)

    blocks = []
    missing = []

    for id_val in sorted_ids:
        session_time = time_map.get(id_val, "")
        block = process_talk(id_val, prefix, tex_dir, session_time)
        if block is None:
            missing.append(format_full_id(id_val, prefix))
        else:
            blocks.append(block)

    # If strict mode, error out on any missing talks
    if strict and missing:
        raise RuntimeError(f"Missing talks for IDs: {', '.join(missing)}")

    write_output(blocks, output_path)

    # Warn if any were missing
    if missing:
        print(f"WARN: Missing talks for IDs: {missing}")


if __name__ == '__main__':
    # map sheet keys to filename prefixes
    prefix_map = {
        'plenary_abstracts': 'P',
        'special_session_abstracts': 'S',
        'contributed_talk_submissions': 'T'
    }

    for key in ["plenary_abstracts"]: # "special_session_submissions", "contributed_talk_submissions", "special_session_abstracts",
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
    
    
   