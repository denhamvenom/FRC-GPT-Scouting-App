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
    result = await start_learning_setup(year, manual_url, manual_file, event_key)

    # Add the event_key to the result if provided
    if event_key:
        result["event_key"] = event_key

        # Store the event key in the global cache for other components to use
        from app.services.global_cache import cache
        cache["active_event_key"] = event_key
        cache["active_event_year"] = year

        print(f"Stored event_key in cache: {event_key}")
    else:
        print("Warning: No event_key provided, cache not updated")

    return result

@router.get("/info")
async def get_setup_info():
    """
    Get the current setup information, including active event key and year.

    This information is used by other components of the application to
    avoid requiring users to re-enter the event key.

    Returns:
        Dictionary with active event information
    """
    from app.services.global_cache import cache

    try:
        # Attempt to get active event information from cache
        event_key = cache.get("active_event_key")
        year = cache.get("active_event_year", 2025)  # Default to 2025 if not set

        print(f"Cache contains: event_key={event_key}, year={year}")

        # Also check if there's an active sheet configuration
        sheet_config = None
        try:
            from app.database.db import get_db_session
            from app.services.sheet_config_service import get_active_configuration

            db = next(get_db_session())

            # Try with event_key from cache, but if none, get any active configuration
            if event_key:
                config_result = await get_active_configuration(db, event_key, year)
            else:
                # If no event_key in cache, get any active configuration
                config_result = await get_active_configuration(db)

                # If we find an active configuration, update the cache with its event_key
                if config_result["status"] == "success":
                    config_event_key = config_result["configuration"]["event_key"]
                    if config_event_key:
                        cache["active_event_key"] = config_event_key
                        event_key = config_event_key
                        print(f"Updated cache with event_key from config: {config_event_key}")

            if config_result["status"] == "success":
                sheet_config = {
                    "id": config_result["configuration"]["id"],
                    "name": config_result["configuration"]["name"],
                    "spreadsheet_id": config_result["configuration"]["spreadsheet_id"],
                    "match_scouting_sheet": config_result["configuration"]["match_scouting_sheet"],
                    "pit_scouting_sheet": config_result["configuration"]["pit_scouting_sheet"],
                    "super_scouting_sheet": config_result["configuration"]["super_scouting_sheet"],
                    "event_key": config_result["configuration"]["event_key"],
                }
        except Exception as e:
            # Non-critical error, just log it
            print(f"Error getting active sheet configuration: {str(e)}")

        # Print detailed debug info
        print(f"Setup Info - Event Key: {event_key}, Year: {year}")
        print(f"Setup Info - Sheet Config: {sheet_config}")

        # Return gathered information
        return {
            "status": "success",
            "event_key": event_key,
            "year": year,
            "sheet_config": sheet_config
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving setup info: {str(e)}"
        }
