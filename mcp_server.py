import sqlite3
import json
import pandas as pd
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("CricketScoutingMCP")

DB_PATH = "data/cricket.db"

@mcp.tool()
def get_player_matchup_metrics(player_name: str, format: str) -> str:
    """Queries the local cricket database to fetch a batsman's overall performance and their matchups against their most faced bowlers."""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Overall Stats
        overall_query = """
            SELECT 
                SUM(d.batsman_runs) as total_runs,
                COUNT(d.ball) as balls_faced,
                SUM(d.is_wicket) as times_dismissed
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE d.batter COLLATE NOCASE = ? AND m.format COLLATE NOCASE = ?
        """
        overall_df = pd.read_sql_query(overall_query, conn, params=(player_name, format))
        if overall_df.empty or pd.isna(overall_df['total_runs'].iloc[0]):
            conn.close()
            return f"No data found for player: {player_name}"
            
        runs = int(overall_df['total_runs'].iloc[0])
        balls = int(overall_df['balls_faced'].iloc[0])
        dismissals = int(overall_df['times_dismissed'].iloc[0])
        avg = runs / dismissals if dismissals > 0 else runs
        sr = (runs / balls) * 100 if balls > 0 else 0

        # Top 5 Bowler Matchups
        matchup_query = """
            SELECT 
                d.bowler,
                SUM(d.batsman_runs) as runs_scored,
                COUNT(d.ball) as balls_faced,
                SUM(d.is_wicket) as times_dismissed
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE d.batter COLLATE NOCASE = ? AND m.format COLLATE NOCASE = ?
            GROUP BY d.bowler
            ORDER BY balls_faced DESC
            LIMIT 5
        """
        matchup_df = pd.read_sql_query(matchup_query, conn, params=(player_name, format))
        
        matchups = []
        for _, row in matchup_df.iterrows():
            m_runs = row['runs_scored']
            m_balls = row['balls_faced']
            m_diss = row['times_dismissed']
            matchups.append({
                "bowler": row['bowler'],
                "runs": m_runs,
                "balls_faced": m_balls,
                "times_dismissed": m_diss,
                "strike_rate": round((m_runs / m_balls) * 100, 2) if m_balls > 0 else 0,
                "average": round(m_runs / m_diss, 2) if m_diss > 0 else m_runs
            })
            
        conn.close()
        
        result = {
            "batsman": player_name,
            "overall_runs": runs,
            "overall_average": round(avg, 2),
            "overall_strike_rate": round(sr, 2),
            "top_bowler_matchups": matchups
        }
        return json.dumps(result)
        
    except Exception as e:
        return f"Database Error: {str(e)}"

@mcp.tool()
def get_venue_historical_metrics(stadium_name: str, format: str) -> str:
    """Retrieves average historical metrics, average scores, and chasing win ratios for a specific stadium."""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Win ratio
        matches_query = """
            SELECT 
                COUNT(*) as total_matches,
                SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END) as toss_win_match_win,
                SUM(CASE WHEN toss_decision = 'field' AND winner = toss_winner THEN 1 
                         WHEN toss_decision = 'bat' AND winner != toss_winner THEN 1 ELSE 0 END) as chasing_wins
            FROM matches 
            WHERE venue COLLATE NOCASE LIKE ? AND format COLLATE NOCASE = ?
        """
        matches_df = pd.read_sql_query(matches_query, conn, params=(f"%{stadium_name}%", format))
        
        if matches_df.empty or matches_df['total_matches'].iloc[0] == 0:
            conn.close()
            return f"No venue patterns found for: {stadium_name}"
            
        total_matches = int(matches_df['total_matches'].iloc[0])
        chasing_wins = int(matches_df['chasing_wins'].iloc[0])
        chasing_win_ratio = chasing_wins / total_matches
        
        # Avg First Innings Score
        inn_query = """
            SELECT 
                d.match_id,
                SUM(d.total_runs) as inn_score
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE m.venue COLLATE NOCASE LIKE ? AND m.format COLLATE NOCASE = ?
            AND d.inning = 1
            GROUP BY d.match_id
        """
        inn_df = pd.read_sql_query(inn_query, conn, params=(f"%{stadium_name}%", format))
        avg_first_inn = inn_df['inn_score'].mean() if not inn_df.empty else 0
        
        # Wicket types (Pace vs Spin rough proxy: caught/bowled vs lbw/stumped - not perfect without registry, but we provide total wickets)
        wicket_query = """
            SELECT 
                d.dismissal_kind,
                COUNT(*) as count
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE m.venue COLLATE NOCASE LIKE ? AND m.format COLLATE NOCASE = ?
            AND d.is_wicket = 1
            GROUP BY d.dismissal_kind
        """
        wicket_df = pd.read_sql_query(wicket_query, conn, params=(f"%{stadium_name}%", format))
        
        wicket_stats = {}
        for _, row in wicket_df.iterrows():
            wicket_stats[row['dismissal_kind']] = int(row['count'])
            
        conn.close()
        
        result = {
            "stadium": stadium_name,
            "total_matches_analyzed": total_matches,
            "avg_first_innings_score": round(avg_first_inn, 2),
            "chasing_win_ratio": round(chasing_win_ratio, 2),
            "historical_wicket_types": wicket_stats
        }
        return json.dumps(result)
        
    except Exception as e:
        return f"Database Error: {str(e)}"

@mcp.tool()
def get_team_bowling_metrics(team_name: str, venue_name: str, format: str) -> str:
    """Queries the local database for an opposition team's top 5 bowlers globally and their top 5 bowlers at a specific venue."""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Overall Top 5 Bowlers (by wickets)
        overall_query = """
            SELECT 
                d.bowler,
                COUNT(d.ball) as balls_bowled,
                SUM(d.batsman_runs + d.extra_runs) as runs_conceded,
                SUM(d.is_wicket) as wickets
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE d.bowling_team COLLATE NOCASE = ? AND m.format COLLATE NOCASE = ?
            GROUP BY d.bowler
            ORDER BY wickets DESC, balls_bowled DESC
            LIMIT 5
        """
        overall_df = pd.read_sql_query(overall_query, conn, params=(team_name, format))
        
        overall_bowlers = []
        for _, row in overall_df.iterrows():
            w = row['wickets']
            b = row['balls_bowled']
            r = row['runs_conceded']
            overall_bowlers.append({
                "bowler": row['bowler'],
                "wickets": int(w),
                "economy_rate": round((r / b) * 6, 2) if b > 0 else 0,
                "strike_rate": round(b / w, 2) if w > 0 else 0
            })
            
        # Venue-specific Top 5 Bowlers
        venue_query = """
            SELECT 
                d.bowler,
                COUNT(d.ball) as balls_bowled,
                SUM(d.batsman_runs + d.extra_runs) as runs_conceded,
                SUM(d.is_wicket) as wickets
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE d.bowling_team COLLATE NOCASE = ? AND m.venue COLLATE NOCASE LIKE ? AND m.format COLLATE NOCASE = ?
            GROUP BY d.bowler
            ORDER BY wickets DESC, balls_bowled DESC
            LIMIT 5
        """
        venue_df = pd.read_sql_query(venue_query, conn, params=(team_name, f"%{venue_name}%", format))
        
        venue_bowlers = []
        for _, row in venue_df.iterrows():
            w = row['wickets']
            b = row['balls_bowled']
            r = row['runs_conceded']
            venue_bowlers.append({
                "bowler": row['bowler'],
                "wickets": int(w),
                "economy_rate": round((r / b) * 6, 2) if b > 0 else 0,
                "strike_rate": round(b / w, 2) if w > 0 else 0
            })
            
        conn.close()
        
        result = {
            "opposition_team": team_name,
            "venue": venue_name,
            "overall_top_bowlers": overall_bowlers,
            "venue_top_bowlers": venue_bowlers
        }
        return json.dumps(result)
        
    except Exception as e:
        return f"Database Error: {str(e)}"

if __name__ == "__main__":
    # Run via stdio when executed directly
    mcp.run()
