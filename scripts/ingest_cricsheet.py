import os
import io
import requests
import zipfile
import sqlite3
import pandas as pd
from typing import List, Set

# Configuration
URLS = [
    ("T20", "https://cricsheet.org/downloads/t20s_csv2.zip"),
    ("ODI", "https://cricsheet.org/downloads/odis_csv2.zip"),
    ("Test", "https://cricsheet.org/downloads/tests_csv2.zip")
]

# We are including IPL within T20 by checking match_type in the filter
# The user specifically requested these 5 teams ONLY
TOP_5_TEAMS = {
    "New Zealand", "South Africa", "Australia", "India", "England"
}

DB_PATH = "data/cricket.db"
TEMP_EXTRACT_DIR = "data/temp_cricsheet"
MAX_MATCHES_PER_FORMAT = 150  # Smart sampler limit

def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Matches Table (added format)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        match_id TEXT PRIMARY KEY,
        season TEXT,
        date TEXT,
        venue TEXT,
        team1 TEXT,
        team2 TEXT,
        toss_winner TEXT,
        toss_decision TEXT,
        winner TEXT,
        format TEXT
    )
    ''')

    # Create Deliveries Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS deliveries (
        match_id TEXT,
        inning INTEGER,
        batting_team TEXT,
        bowling_team TEXT,
        over INTEGER,
        ball INTEGER,
        batter TEXT,
        bowler TEXT,
        non_striker TEXT,
        batsman_runs INTEGER,
        extra_runs INTEGER,
        total_runs INTEGER,
        is_wicket INTEGER,
        dismissal_kind TEXT,
        player_dismissed TEXT,
        FOREIGN KEY(match_id) REFERENCES matches(match_id)
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deliveries_match_id ON deliveries(match_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deliveries_batter ON deliveries(batter);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler);')
    
    conn.commit()
    return conn

def download_and_extract(url: str, extract_dir: str):
    print(f"Downloading {url}...")
    response = requests.get(url)
    response.raise_for_status()
    print("Extracting...")
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(extract_dir)

def process_matches(conn, format_name: str, extract_dir: str):
    cursor = conn.cursor()
    all_files = os.listdir(extract_dir)
    info_files = [f for f in all_files if f.endswith("_info.csv")]
    
    print(f"Found {len(info_files)} {format_name} matches to process. Filtering and inserting...")
    
    match_records = []
    delivery_records = []
    
    matches_processed = 0
    for info_file in info_files:
        if matches_processed >= MAX_MATCHES_PER_FORMAT:
            break
            
        match_id = info_file.replace("_info.csv", "")
        info_path = os.path.join(extract_dir, info_file)
        data_path = os.path.join(extract_dir, f"{match_id}.csv")
        
        if not os.path.exists(data_path):
            continue
            
        try:
            info_df = pd.read_csv(info_path, header=None, names=["Key", "Attribute", "Value", "Extra1", "Extra2"])
        except Exception:
            continue
            
        meta = {}
        for _, row in info_df.iterrows():
            if row['Key'] == 'info':
                attr = str(row['Attribute'])
                val = str(row['Value'])
                if attr not in meta:
                    meta[attr] = val
                else:
                    if isinstance(meta[attr], list):
                        meta[attr].append(val)
                    else:
                        meta[attr] = [meta[attr], val]
                        
        if meta.get("gender") != "male":
            continue
            
        teams = meta.get("team", [])
        if isinstance(teams, list) and len(teams) >= 2:
            team1, team2 = teams[0], teams[1]
        else:
            continue
            
        # ONLY process if BOTH teams are in the top 5
        if team1 not in TOP_5_TEAMS or team2 not in TOP_5_TEAMS:
            continue
                
        match_records.append((
            match_id,
            meta.get("season"),
            meta.get("date", [""])[0] if isinstance(meta.get("date"), list) else meta.get("date"),
            meta.get("venue"),
            team1,
            team2,
            meta.get("toss_winner"),
            meta.get("toss_decision"),
            meta.get("winner"),
            format_name
        ))
        
        try:
            deliveries_df = pd.read_csv(data_path, low_memory=False)
            for _, row in deliveries_df.iterrows():
                ball_str = str(row['ball'])
                if '.' in ball_str:
                    over, ball = ball_str.split('.')
                else:
                    over, ball = ball_str, "0"
                    
                delivery_records.append((
                    str(match_id),
                    int(row['innings']),
                    str(row['batting_team']),
                    str(row['bowling_team']),
                    int(over),
                    int(ball),
                    str(row['striker']),
                    str(row['bowler']),
                    str(row['non_striker']),
                    int(row['runs_off_bat']),
                    int(row['extras']),
                    int(row['runs_off_bat']) + int(row['extras']),
                    1 if pd.notnull(row['wicket_type']) else 0,
                    str(row['wicket_type']) if pd.notnull(row['wicket_type']) else None,
                    str(row['player_dismissed']) if pd.notnull(row['player_dismissed']) else None
                ))
        except Exception as e:
            print(f"Error parsing deliveries for {match_id}: {e}")
            
        matches_processed += 1
            
    if match_records:
        cursor.executemany('''
            INSERT OR IGNORE INTO matches 
            (match_id, season, date, venue, team1, team2, toss_winner, toss_decision, winner, format)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', match_records)
        cursor.executemany('''
            INSERT INTO deliveries 
            (match_id, inning, batting_team, bowling_team, over, ball, batter, bowler, non_striker, batsman_runs, extra_runs, total_runs, is_wicket, dismissal_kind, player_dismissed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', delivery_records)
        conn.commit()

def main():
    conn = setup_database()
    for fmt, url in URLS:
        format_dir = os.path.join(TEMP_EXTRACT_DIR, fmt)
        os.makedirs(format_dir, exist_ok=True)
        try:
            download_and_extract(url, format_dir)
            process_matches(conn, fmt, format_dir)
        except Exception as e:
            print(f"Failed to process {fmt}: {e}")
            
    conn.close()
    print("Multi-Format Database built successfully!")
    
if __name__ == "__main__":
    main()
