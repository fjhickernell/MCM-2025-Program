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
        raise ValueError("No talk environment found in content.")
    return match.group(0)


def generate_plenary_talks(csv_path: str = "plenary_abstracts_talkid.csv",
                           tex_dir: str = ".",
                           output_path: str = "plenary_talks.tex",
                           strict: bool = False):
    """
    Reads the CSV of plenary abstracts, extracts each talk environment
    from its corresponding .tex file, and writes them in order to
    a single plenary_talks.tex file with a chapter header.

    It also fills any empty-brace placeholders for talk ID:
    - {}% [8]
    - {}% [6]
    with the actual TalkID (e.g., P2, P3, ...).

    Parameters:
    - csv_path: Path to the CSV listing TalkID values.
    - tex_dir: Directory where P2.tex, P3.tex, ... are located.
    - output_path: Path for the generated plenary_talks.tex.
    - strict: If True, abort on missing .tex files; otherwise warn and continue.
    """
    # Read the CSV; assume it has a column 'TalkID' listing file prefixes
    df = pd.read_csv(csv_path, dtype=str)
    if 'TalkID' not in df.columns:
        raise KeyError("CSV must contain a 'TalkID' column with file prefixes.")

    # Prepare output file
    with open(output_path, 'w', encoding='utf-8') as out_file:
        out_file.write("\\chapter{Plenary Talks}\n")
        out_file.write("\\newpage\n\n")

        missing = []
        # Iterate in CSV order
        for raw_id in df['TalkID']:
            talk_id = raw_id.strip()
            tex_filename = os.path.join(tex_dir, f"{talk_id}.tex")
            if not os.path.isfile(tex_filename):
                msg = f"File not found: {tex_filename}"
                if strict:
                    raise FileNotFoundError(msg)
                else:
                    print(f"Warning: {msg}; skipping.")
                    missing.append(talk_id)
                    continue

            # Read .tex and extract talk environment
            with open(tex_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                talk_env = extract_talk_environment(content)
            except ValueError as e:
                print(f"Error in {tex_filename}: {e}")
                continue

            # Fill in any empty talk-ID placeholders:
            # Replace {}% [8]
            talk_env = re.sub(
                r"\{\}\s*%\s*\[8\]",
                f"{{{talk_id}}}% [8]",
                talk_env
            )
            # Replace {}% [6]
            talk_env = re.sub(
                r"\{\}\s*%\s*\[6\]",
                f"{{{talk_id}}}% [6]",
                talk_env
            )

            # Write the extracted (and modified) environment into output
            out_file.write(talk_env)
            out_file.write("\n\n")

    if missing:
        print(f"Warning: Missing talks for IDs: {', '.join(missing)}.")
    print(f"Successfully generated '{output_path}'.")


if __name__ == '__main__':
    generate_plenary_talks(csv_path=f"{interimdir}plenary_abstracts_talkid.csv", tex_dir=f"{indir}/abstracts/", output_path=f"{outdir}plenary_talks.tex")
