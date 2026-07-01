import os
import json
import pandas as pd
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

# Local Intel Layer Configuration
local_ollama_llm = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434"
)

# Seed Data Generation
def setup_mock_cricket_database():
    mock_matchups = {
        "batsman": ["Virat Kohli", "Rohit Sharma", "KL Rahul"],
        "vs_left_arm_pace_avg": [24.5, 21.2, 35.0],
        "vs_left_arm_pace_sr": [118.4, 110.5, 130.2],
        "vs_leg_spin_avg": [28.0, 22.0, 42.1],
        "vs_leg_spin_sr": [112.1, 145.0, 122.0]
    }
    mock_venue = {
        "stadium": ["M. Chinnaswamy Stadium"],
        "avg_first_inn_score": [172],
        "spin_wicket_percentage": [32.4],
        "pace_wicket_percentage": [67.6],
        "chasing_win_ratio": [0.58]
    }
    pd.DataFrame(mock_matchups).to_csv("cricsheet_matchups_clean.csv", index=False)
    pd.DataFrame(mock_venue).to_csv("cricsheet_stadiums_clean.csv", index=False)

setup_mock_cricket_database()

# Deterministic Tools
@tool("Matchup Data Retriever Tool")
def get_player_matchup_metrics(player_name: str) -> str:
    """Queries local data sheets to fetch player performance stats vs bowler styles."""
    try:
        df = pd.read_csv("cricsheet_matchups_clean.csv")
        record = df[df['batsman'].str.lower() == player_name.lower()]
        if record.empty:
            return f"No data found for: {player_name}"
        return record.to_json(orient="records")
    except Exception as e:
        return str(e)

@tool("Venue Analysis Tool")
def get_venue_historical_metrics(stadium_name: str) -> str:
    """Retrieves average historical metrics and win ratios for a stadium."""
    try:
        df = pd.read_csv("cricsheet_stadiums_clean.csv")
        record = df[df['stadium'].str.lower().str.contains(stadium_name.lower())]
        if record.empty:
            return f"No venue patterns found for: {stadium_name}"
        return record.to_json(orient="records")
    except Exception as e:
        return str(e)

# Agent Definitions
retriever_agent = Agent(
    role="Data Retriever Specialist",
    goal="Accurately fetch local historical records for specified players and venues.",
    backstory="An expert automated crawler specializing in parsing historical sports data sheets.",
    tools=[get_player_matchup_metrics, get_venue_historical_metrics],
    llm=local_ollama_llm,
    verbose=True
)

matchup_analyst = Agent(
    role="Matchup Analyst",
    goal="Extract strategic vulnerabilities by evaluating player performance metrics.",
    backstory="A specialized performance analyst who discovers statistical anomalies and execution risks.",
    tools=[get_player_matchup_metrics],
    llm=local_ollama_llm,
    verbose=True
)

venue_analyst = Agent(
    role="Venue Specialist",
    goal="Map out operational pitch and environmental match dynamics.",
    backstory="An expert pitch configuration engineer tracking seasonal variance across stadium locations.",
    tools=[get_venue_historical_metrics],
    llm=local_ollama_llm,
    verbose=True
)

lead_strategist = Agent(
    role="Lead Tactical Strategist",
    goal="Synthesize granular analysis into a clean, actionable tactical match playbook.",
    backstory="A world-renowned cricket mastermind who transforms analytical data profiles into real-world victories.",
    llm=local_ollama_llm,
    verbose=True
)

# Flow Pipeline Tasks
task_data_gather = Task(
    description="Locate and aggregate raw data sheets for player 'Rohit Sharma' and stadium 'M. Chinnaswamy Stadium'.",
    expected_output="A raw JSON array containing match profiles for the targeted player and venue.",
    agent=retriever_agent
)

task_analyze_matchups = Task(
    description="Examine the aggregated data profile for Rohit Sharma. Isolate his weaknesses vs spin and pace.",
    expected_output="An analytical summary explaining specific bowling plans to limit the batter's scoring.",
    agent=matchup_analyst
)

task_analyze_venue = Task(
    description="Analyze historical performance metrics at M. Chinnaswamy Stadium to identify pitch deterioration curves.",
    expected_output="An executive brief highlighting boundary profiles, chasing success rates, and optimal target metrics.",
    agent=venue_analyst
)

task_compile_playbook = Task(
    description="Synthesize reports into a complete Pre-Match Tactical Playbook in markdown format.",
    expected_output="A clean, markdown-formatted document containing concrete team match-day tactical plans.",
    agent=lead_strategist
)

cricket_scouting_crew = Crew(
    agents=[retriever_agent, matchup_analyst, venue_analyst, lead_strategist],
    tasks=[task_data_gather, task_analyze_matchups, task_analyze_venue, task_compile_playbook],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    final_playbook_output = cricket_scouting_crew.kickoff()
    print(final_playbook_output)
