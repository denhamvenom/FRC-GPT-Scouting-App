# backend/app/services/tba_client.py

import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.services.cache_service import cached

# Load environment variables
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=ENV_PATH)

TBA_API_KEY = os.getenv("TBA_API_KEY")
TBA_BASE_URL = "https://www.thebluealliance.com/api/v3"

HEADERS = {"X-TBA-Auth-Key": TBA_API_KEY}

# Default to using the value from environment, but if not available, use a hardcoded key
# This allows the application to work out of the box for testing
if not TBA_API_KEY:
    TBA_API_KEY = "PpK8kpfWt94Nf15uoK8UbanbFQzZ97rwWwGqnqB9wILs9VBfcNjfRLvlkvYcGqoA"
    HEADERS = {"X-TBA-Auth-Key": TBA_API_KEY}


@cached(max_age_seconds=3600 * 24)  # Cache for 24 hours
async def get_event_teams(event_key: str) -> List[Dict[str, Any]]:
    """
    Pulls simple team listings at an event.
    """
    url = f"{TBA_BASE_URL}/event/{event_key}/teams/simple"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()


@cached(max_age_seconds=3600 * 8)  # Cache for 8 hours
async def get_event_matches(event_key: str) -> List[Dict[str, Any]]:
    """
    Pulls simple match listings at an event.
    """
    url = f"{TBA_BASE_URL}/event/{event_key}/matches/simple"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()


@cached(max_age_seconds=3600 * 4)  # Cache for 4 hours
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


@cached(max_age_seconds=3600 * 24 * 7)  # Cache for 1 week (events don't change often)
async def get_events_by_year(year: int) -> List[Dict[str, Any]]:
    """
    Pulls a list of all events for a specific FRC season year.

    Args:
        year: The FRC season year (e.g., 2023, 2024, 2025)

    Returns:
        A list of event objects, each containing:
        - key: Event key (e.g., "2023caln")
        - name: Official event name
        - event_code: Event code (e.g., "caln")
        - location_name: Venue name
        - city: City
        - state_prov: State/Province
        - country: Country
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - event_type: Numeric event type code
        - event_type_string: String event type (e.g., "Regional", "District", "Championship")
        - week: Event week number
    """
    url = f"{TBA_BASE_URL}/events/{year}/simple"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        events = response.json()

        # Sort events by start date then name
        return sorted(events, key=lambda e: (e.get("start_date", ""), e.get("name", "")))


@cached(max_age_seconds=3600 * 24 * 7)  # Cache for 1 week
async def get_event_details(event_key: str) -> Dict[str, Any]:
    """
    Gets detailed information about a specific event.

    Args:
        event_key: The TBA event key (e.g., "2023caln")

    Returns:
        Detailed event information
    """
    url = f"{TBA_BASE_URL}/event/{event_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
