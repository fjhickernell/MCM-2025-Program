"""
Statistics script to count different types of talks from SessionList.csv and TalkID files.
Provides comprehensive breakdown of MCM 2025 conference sessions and talks.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple
from config import *

def load_session_data() -> pd.DataFrame:
    """Load session list data."""
    try:
        return pd.read_csv(f"{outdir}SessionList.csv")
    except FileNotFoundError:
        print(f"ERROR: SessionList.csv not found in {outdir}")
        return pd.DataFrame()

def load_talk_data() -> Dict[str, pd.DataFrame]:
    """Load talk data from TalkID files."""
    talk_files = {
        'plenary': f"{interimdir}plenary_abstracts_talkid.csv",
        'special': f"{interimdir}special_session_abstracts_talkid.csv", 
        'contributed': f"{interimdir}contributed_talk_submissions_talkid.csv"
    }
    
    talk_dfs = {}
    for talk_type, filepath in talk_files.items():
        try:
            talk_dfs[talk_type] = pd.read_csv(filepath)
        except FileNotFoundError:
            print(f"WARN: {Path(filepath).name} not found")
            talk_dfs[talk_type] = pd.DataFrame()
    
    return talk_dfs

def count_sessions_by_type(session_df: pd.DataFrame) -> Dict[str, int]:
    """Count sessions by type from SessionList."""
    if session_df.empty:
        return {'plenary': 0, 'special': 0, 'contributed': 0}
    
    return {
        'plenary': len(session_df[session_df['SessionID'].str.startswith('P')]),
        'special': len(session_df[session_df['SessionID'].str.startswith('S')]),
        'contributed': len(session_df[session_df['SessionID'].str.startswith('T')])
    }

def get_talk_counts(talk_dfs: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    """Get talk counts from loaded dataframes."""
    return {talk_type: len(df) for talk_type, df in talk_dfs.items()}

def print_session_summary(session_counts: Dict[str, int]):
    """Print session count summary."""
    print("="*50)
    print("MCM 2025 Conference Talk Statistics")
    print("="*50)
    print(f"Plenary Sessions:         {session_counts['plenary']:3d}")
    print(f"Special Sessions:         {session_counts['special']:3d}")
    print(f"Contributed Sessions:     {session_counts['contributed']:3d}")
    print("-"*50)

def print_talk_summary(talk_counts: Dict[str, int]):
    """Print detailed talk count summary."""
    print("\nDetailed Talk Counts from TalkID files:")
    print("-"*50)
    print(f"Plenary Talks:            {talk_counts['plenary']:3d}")
    print(f"Special Session Talks:    {talk_counts['special']:3d}")
    print(f"Contributed Talks:        {talk_counts['contributed']:3d}")
    print("-"*50)
    total = sum(talk_counts.values())
    print(f"Total Individual Talks:   {total:3d}")
    print("="*50)

def print_special_session_breakdown(df: pd.DataFrame):
    """Print special session breakdown."""
    if df.empty:
        return
    
    unique_sessions = df['SessionID'].dropna().unique()
    print(f"\nSpecial Session Breakdown:")
    print(f"Number of Special Sessions: {len(unique_sessions)}")
    
    for session in sorted(unique_sessions):
        session_data = df[df['SessionID'] == session]
        session_talks = len(session_data)
        session_title = session_data['Special Session Title'].iloc[0]
        print(f"  {session}: {session_talks} talks - {session_title}")

def print_contributed_session_breakdown(df: pd.DataFrame):
    """Print contributed session breakdown."""
    if df.empty:
        return
    
    unique_sessions = df['SessionID'].dropna().unique()
    print(f"\nContributed Session Breakdown:")
    print(f"Number of Technical Sessions: {len(unique_sessions)}")
    
    for session in sorted(unique_sessions):
        session_talks = len(df[df['SessionID'] == session])
        print(f"  {session}: {session_talks} talks")

if __name__ == '__main__':

    session_df = load_session_data()
    
    talk_dfs = load_talk_data()
    session_counts = count_sessions_by_type(session_df)
    talk_counts = get_talk_counts(talk_dfs)
    
    print_session_summary(session_counts)
    print_talk_summary(talk_counts)
    
    #print_special_session_breakdown(talk_dfs['special'])
    #print_contributed_session_breakdown(talk_dfs['contributed'])


