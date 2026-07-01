import sys
import json
import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

load_dotenv()
gh_client = OpenAI(
    base_url="https://models.inference.ai.azure.com", 
    api_key=os.environ.get("GITHUB_TOKEN", "dummy_token_to_prevent_startup_crash")
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlaybookRequest(BaseModel):
    mode: str  # "batting" or "bowling"
    target_entity: str  # team_name if batting, player_name if bowling
    venue: str
    format: str # "T20", "ODI", or "Test"

async def call_mcp_tool(tool_name: str, args: dict) -> str:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=args)
            return result.content[0].text

def generate_langchain_playbook(mode: str, target: str, venue: str, match_format: str) -> str:
    # 1. Fetch Data from MCP
    try:
        venue_data = asyncio.run(call_mcp_tool("get_venue_historical_metrics", {"stadium_name": venue, "format": match_format}))
    except Exception as e:
        venue_data = str(e)

    if mode == "batting":
        try:
            target_data = asyncio.run(call_mcp_tool("get_team_bowling_metrics", {"team_name": target, "venue_name": venue, "format": match_format}))
        except Exception as e:
            target_data = str(e)
            
        prompt = f"""You are a world-renowned cricket tactical strategist and data analyst.
Analyze the following raw {match_format} data for {target}'s bowling lineup at {venue}.

Raw Venue Data: {venue_data}
Raw Bowling Data: {target_data}

Please generate a highly descriptive, beautifully formatted, and comprehensive tactical playbook on how to BAT against {target} at {venue}.
Your analysis should be deeply analytical. Use bolding, bullet points, and headers to structure the output. Discuss historical trends at the venue, the strengths/weaknesses of the opposition's top bowlers, and formulate a step-by-step master plan for the batting innings. Do not skimp on the details!
"""
    else:
        try:
            target_data = asyncio.run(call_mcp_tool("get_player_matchup_metrics", {"player_name": target, "format": match_format}))
        except Exception as e:
            target_data = str(e)
            
        prompt = f"""You are a world-renowned cricket tactical strategist and data analyst.
Analyze the following raw {match_format} data for {target}'s batting at {venue}.

Raw Venue Data: {venue_data}
Raw Batter Data: {target_data}

Please generate a highly descriptive, beautifully formatted, and comprehensive tactical playbook on how to BOWL to {target} at {venue}.
Your analysis should be deeply analytical. Use bolding, bullet points, and headers to structure the output. Discuss historical trends at the venue, the batter's tendencies, their strike rate and dismissal records against specific bowlers, and formulate a step-by-step master plan to dismiss or contain them. Do not skimp on the details!
"""

    # 3. Generate Single-Shot Playbook via GitHub Models API
    try:
        response = gh_client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o",
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Failed to connect to GitHub Models API: {str(e)}"

@app.post("/generate")
def generate_playbook(request: PlaybookRequest):
    playbook = generate_langchain_playbook(request.mode, request.target_entity, request.venue, request.format)
    return {"playbook": playbook}
