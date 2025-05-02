# backend/app/services/tba_client.py

import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=ENV_PATH)

TBA_API_KEY = os.getenv("TBA_API_KEY")
TBA_BASE_URL = "https://www.thebluealliance.com/api/v3"

HEADERS = {
    "X-TBA-Auth-Key": TBA_API_KEY
}

async def get_event_teams(event_key: str) -> List[Dict[str, Any]]:
    """
    Pulls simple team listings at an event.
    """
    url = f"{TBA_BASE_URL}/event/{event_key}/teams/simple"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()

async def get_event_matches(event_key: str) -> List[Dict[str, Any]]:
    """
    Pulls simple match listings at an event.
    """
    url = f"{TBA_BASE_URL}/event/{event_key}/matches/simple"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()

async def get_event_rankings(event_key: str) -> Optional[Dict[str, Any]]:
    """
    Pulls event rankings (qual RP, tie-breakers, etc.).
    """
    url = f"{TBA_BASE_URL}/event/{event_key}/rankings"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 404:
            return None  # Rankings might not exist yet
        response.raise_for_status()
        return response.json()

async def get_match_detail(match_key: str) -> Dict[str, Any]:
    """
    Pulls detailed match breakdown for a specific match.
    """
    url = f"{TBA_BASE_URL}/match/{match_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()

async def get_team_status_at_event(team_key: str, event_key: str) -> Optional[Dict[str, Any]]:
    """
    Pulls a team's current status at an event (alliance selection, playoff advancement, awards).
    """
    url = f"{TBA_BASE_URL}/team/{team_key}/event/{event_key}/status"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
