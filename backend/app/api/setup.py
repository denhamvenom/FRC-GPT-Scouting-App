# backend/app/api/setup.py

from fastapi import APIRouter, UploadFile, File, Form, Query
from typing import Optional, List, Dict, Any
from app.services.learning_setup_service import start_learning_setup
from app.services.tba_client import get_events_by_year, get_event_details

router = APIRouter(prefix="/api/setup", tags=["Setup"])

@router.get("/events")
async def get_events(year: int = Query(..., description="FRC Season Year")):
    """
    Get a list of all FRC events for a specific season year.

    Args:
        year: The FRC season year (e.g., 2023, 2024, 2025)

    Returns:
        A list of all events for the specified year, with basic information.
    """
    try:
        events = await get_events_by_year(year)

        # Transform to a more compact format with essential info
        simplified_events = []
        for event in events:
            simplified_event = {
                "key": event.get("key"),
                "name": event.get("name"),
                "code": event.get("event_code"),
                "location": ", ".join(filter(None, [
                    event.get("city"),
                    event.get("state_prov"),
                    event.get("country")
                ])),
                "dates": f"{event.get('start_date')} to {event.get('end_date')}",
                "type": event.get("event_type_string"),
                "week": event.get("week")
            }
            simplified_events.append(simplified_event)

        # Group by type
        grouped_events = {}
        for event in simplified_events:
            event_type = event.get("type", "Other")
            if event_type not in grouped_events:
                grouped_events[event_type] = []
            grouped_events[event_type].append(event)

        return {
            "status": "success",
            "year": year,
            "grouped_events": grouped_events,
            "all_events": simplified_events
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "year": year
        }

@router.get("/event/{event_key}")
async def get_event(event_key: str):
    """
    Get detailed information about a specific FRC event.

    Args:
        event_key: The TBA event key (e.g., "2023caln")

    Returns:
        Detailed event information
    """
    try:
        event_details = await get_event_details(event_key)
        return {
            "status": "success",
            "event": event_details
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "event_key": event_key
        }

@router.post("/start")
async def start_setup(
    year: int = Form(...),
    event_key: Optional[str] = Form(None),
    manual_url: Optional[str] = Form(None),
    manual_file: Optional[UploadFile] = File(None)
):
    """
    Starts the learning setup process.

    Args:
        year: The FRC season year (e.g., 2023, 2024, 2025)
        event_key: Optional TBA event key (e.g., "2024caln")
        manual_url: Optional URL to the game manual PDF
        manual_file: Optional uploaded game manual file

    Returns:
        Setup process results
    """
    result = await start_learning_setup(year, manual_url, manual_file)

    # Add the event_key to the result if provided
    if event_key:
        result["event_key"] = event_key

    return result
