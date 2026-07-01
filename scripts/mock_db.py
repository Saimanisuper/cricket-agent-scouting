import sqlite3
import os

DB_PATH = "data/cricket.db"

def seed_mock_data():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Matches Table
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
        winner TEXT
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
        player_dismissed TEXT
    )
    ''')
    
    # Clear existing mock data
    cursor.execute("DELETE FROM matches")
    cursor.execute("DELETE FROM deliveries")
    
    # Insert Mock Matches
    matches = [
        ("M1", "2023", "2023-11-19", "M. Chinnaswamy Stadium", "India", "Australia", "Australia", "field", "Australia"),
        ("M2", "2023", "2023-10-08", "Wankhede Stadium", "India", "Australia", "India", "bat", "India"),
        ("M3", "2023", "2023-07-01", "Lord's", "England", "Australia", "England", "field", "Australia"),
        # 3 from Australia
        ("M4", "2023", "2023-12-26", "Melbourne Cricket Ground", "Australia", "India", "Australia", "field", "Australia"),
        ("M5", "2024", "2024-01-03", "Sydney Cricket Ground", "Australia", "England", "England", "bat", "Australia"),
        ("M6", "2023", "2023-11-01", "The Gabba", "Australia", "India", "India", "bat", "India"),
        # 2 from England
        ("M7", "2023", "2023-06-16", "Edgbaston", "England", "Australia", "England", "bat", "Australia"),
        ("M8", "2023", "2023-07-19", "Old Trafford", "England", "India", "India", "field", "England"),
        # 1 from India
        ("M9", "2024", "2024-03-22", "Eden Gardens", "India", "England", "India", "bat", "India")
    ]
    cursor.executemany("INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", matches)
    
    # Insert Mock Deliveries
    deliveries = []
    
    # M. Chinnaswamy Stadium: Australia bowling to Virat Kohli
    for i in range(1, 31):
        deliveries.append(("M1", 1, "India", "Australia", i//6, i%6, "Virat Kohli", "Pat Cummins", "Rohit Sharma", 1 if i%2==0 else 4, 0, 1 if i%2==0 else 4, 0, None, None))
    deliveries.append(("M1", 1, "India", "Australia", 5, 1, "Virat Kohli", "Mitchell Starc", "Rohit Sharma", 0, 0, 0, 1, "caught", "Virat Kohli"))
    
    # Wankhede Stadium: Travis Head batting against India
    for i in range(1, 41):
        deliveries.append(("M2", 2, "Australia", "India", i//6, i%6, "Travis Head", "Jasprit Bumrah", "David Warner", 2, 0, 2, 0, None, None))
    deliveries.append(("M2", 2, "Australia", "India", 7, 1, "Travis Head", "Ravindra Jadeja", "David Warner", 0, 0, 0, 1, "lbw", "Travis Head"))

    # Lord's: England batting against Australia
    for i in range(1, 41):
        deliveries.append(("M3", 1, "England", "Australia", i//6, i%6, "Joe Root", "Pat Cummins", "Ben Stokes", 1, 0, 1, 0, None, None))
    deliveries.append(("M3", 1, "England", "Australia", 7, 1, "Joe Root", "Mitchell Starc", "Ben Stokes", 0, 0, 0, 1, "bowled", "Joe Root"))

    # Eden Gardens: Abhishek Sharma batting against England
    for i in range(1, 31):
        deliveries.append(("M9", 1, "India", "England", i//6, i%6, "Abhishek Sharma", "Jofra Archer", "Shubman Gill", 4 if i%3==0 else 0, 0, 4 if i%3==0 else 0, 0, None, None))
    deliveries.append(("M9", 1, "India", "England", 5, 1, "Abhishek Sharma", "Adil Rashid", "Shubman Gill", 0, 0, 0, 1, "caught", "Abhishek Sharma"))

    # MCG: Mitchell Marsh batting against India
    for i in range(1, 35):
        deliveries.append(("M4", 2, "Australia", "India", i//6, i%6, "Mitchell Marsh", "Mohammed Siraj", "Steve Smith", 6 if i%5==0 else 1, 0, 6 if i%5==0 else 1, 0, None, None))
    deliveries.append(("M4", 2, "Australia", "India", 6, 1, "Mitchell Marsh", "Ravichandran Ashwin", "Steve Smith", 0, 0, 0, 1, "lbw", "Mitchell Marsh"))

    # Edgbaston: Jos Buttler batting against Australia
    for i in range(1, 25):
        deliveries.append(("M7", 1, "England", "Australia", i//6, i%6, "Jos Buttler", "Josh Hazlewood", "Jonny Bairstow", 2, 0, 2, 0, None, None))
    deliveries.append(("M7", 1, "England", "Australia", 4, 2, "Jos Buttler", "Adam Zampa", "Jonny Bairstow", 0, 0, 0, 1, "stumped", "Jos Buttler"))
    
    cursor.executemany("INSERT INTO deliveries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", deliveries)
    
    conn.commit()
    conn.close()
    print("Mock database seeded successfully.")

if __name__ == "__main__":
    seed_mock_data()
