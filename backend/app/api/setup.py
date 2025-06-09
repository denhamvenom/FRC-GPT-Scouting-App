"""
Setup API Router

This module handles the initial application setup including event selection,
manual parsing, and configuration management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import (
    EventDetailResponse,
    EventsRequest,
    EventsResponse,
    SetupInfoResponse,
    StartSetupRequest,
    StartSetupResponse,
)
from app.api.utils.response_formatters import format_error_response
from app.database.db import get_db_session
from app.services.global_cache import cache
from app.services.learning_setup_service import start_learning_setup
from app.services.sheet_config_service import get_active_configuration
from app.services.tba_client import get_event_details, get_events_by_year

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/events")
async def get_events(
    year: int = Query(..., ge=1992, le=2030, description="FRC Season Year"),
    event_type: Optional[int] = Query(None, description="Filter by event type"),
    district_key: Optional[str] = Query(None, description="Filter by district"),
    week: Optional[int] = Query(None, ge=0, le=8, description="Filter by competition week"),
) -> EventsResponse:
    """
    Get all FRC events for a specific season year.
    
    Event types:
    - 0: Regional
    - 1: District
    - 2: District Championship
    - 3: Championship Division
    - 4: Championship Finals
    - 5: District Championship Division
    - 6: Festival of Champions
    - 7: Remote
    - 99: Offseason
    - 100: Preseason
    """
    try:
        events = await get_events_by_year(year)
        
        # Transform events to match schema
        event_infos = []
        for event in events:
            event_info = {
                "key": event.get("key"),
                "name": event.get("name"),
                "event_code": event.get("event_code"),
                "event_type": event.get("event_type"),
                "event_type_string": event.get("event_type_string"),
                "district": event.get("district"),
                "city": event.get("city"),
                "state_prov": event.get("state_prov"),
                "country": event.get("country"),
                "start_date": event.get("start_date"),
                "end_date": event.get("end_date"),
                "year": event.get("year"),
                "week": event.get("week"),
                "timezone": event.get("timezone"),
                "website": event.get("website"),
                "first_event_code": event.get("first_event_code"),
            }
            event_infos.append(event_info)
        
        # Apply filters
        filtered_events = event_infos
        
        if event_type is not None:
            filtered_events = [e for e in filtered_events if e["event_type"] == event_type]
        
        if district_key:
            filtered_events = [
                e for e in filtered_events 
                if e.get("district") and e["district"].get("key") == district_key
            ]
        
        if week is not None:
            filtered_events = [e for e in filtered_events if e.get("week") == week]
        
        # Group events by type for frontend compatibility
        grouped_events = {}
        for event in filtered_events:
            event_type_name = event.get("event_type_string") or f"Type {event.get('event_type', 'Unknown')}"
            if event_type_name not in grouped_events:
                grouped_events[event_type_name] = []
            
            # Transform to frontend Event interface format
            event_for_frontend = {
                "key": event["key"],
                "name": event["name"],
                "code": event["event_code"],
                "location": f"{event.get('city', '')}, {event.get('state_prov', '')}".strip(", "),
                "dates": f"{event.get('start_date', '')} - {event.get('end_date', '')}".strip(" - "),
                "type": event_type_name,
                "week": event.get("week", 0) or 0
            }
            grouped_events[event_type_name].append(event_for_frontend)
        
        # Create all_events list in the same format
        all_events = []
        for events_list in grouped_events.values():
            all_events.extend(events_list)
        
        # Return custom response with frontend compatibility
        from fastapi.responses import JSONResponse
        
        response_data = {
            "status": "success",
            "message": None,
            "data": None,
            "year": year,
            "events": filtered_events,
            "total": len(event_infos),
            "filtered": len(filtered_events),
            "all_events": all_events,
            "grouped_events": grouped_events,
        }
        
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_key}", response_model=EventDetailResponse)
async def get_event(event_key: str) -> EventDetailResponse:
    """
    Get detailed information about a specific FRC event.
    
    Includes event details, team list, and match count.
    """
    try:
        # Get event details
        event_data = await get_event_details(event_key)
        
        # Transform to match schema
        event_info = {
            "key": event_data.get("key"),
            "name": event_data.get("name"),
            "event_code": event_data.get("event_code"),
            "event_type": event_data.get("event_type"),
            "event_type_string": event_data.get("event_type_string"),
            "district": event_data.get("district"),
            "city": event_data.get("city"),
            "state_prov": event_data.get("state_prov"),
            "country": event_data.get("country"),
            "start_date": event_data.get("start_date"),
            "end_date": event_data.get("end_date"),
            "year": event_data.get("year"),
            "week": event_data.get("week"),
            "timezone": event_data.get("timezone"),
            "website": event_data.get("website"),
            "first_event_code": event_data.get("first_event_code"),
        }
        
        # Get teams if available
        teams = []
        if "teams" in event_data:
            for team in event_data["teams"]:
                team_info = {
                    "team_number": team.get("team_number"),
                    "nickname": team.get("nickname"),
                    "name": team.get("name"),
                    "city": team.get("city"),
                    "state_prov": team.get("state_prov"),
                    "country": team.get("country"),
                    "rookie_year": team.get("rookie_year"),
                }
                teams.append(team_info)
        
        # Get match count if available
        matches_scheduled = event_data.get("matches_scheduled", 0)
        
        return EventDetailResponse(
            status="success",
            event=event_info,
            teams=teams,
            team_count=len(teams),
            matches_scheduled=matches_scheduled,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", response_model=StartSetupResponse)
async def start_setup(
    year: int = Form(..., ge=1992, le=2030),
    event_key: Optional[str] = Form(None),
    manual_file: Optional[UploadFile] = File(None),
) -> StartSetupResponse:
    """
    Start the learning setup process.
    
    This initializes the application for a specific FRC season,
    optionally with a specific event and game manual.
    """
    try:
        # Start the setup process
        result = await start_learning_setup(year, manual_file, event_key)
        
        # Store event information in cache if provided
        if event_key:
            cache["active_event_key"] = event_key
            cache["active_event_year"] = year
        
        # Generate setup ID
        setup_id = f"setup_{event_key or 'global'}_{year}"
        
        # Determine next steps based on what was provided
        next_steps = []
        if not event_key:
            next_steps.append("Select an event")
        next_steps.extend([
            "Configure Google Sheet connection",
            "Learn schema from spreadsheet headers",
            "Load team data",
            "Build unified dataset",
        ])
        
        # Return custom response with sample teams data for frontend compatibility
        from fastapi.responses import JSONResponse
        
        response_data = {
            "status": "success",
            "event_key": event_key or "",
            "setup_id": setup_id,
            "setup_status": "in_progress",
            "message": result.get("message", "Setup started successfully"),
            "next_steps": next_steps,
            "sample_teams": result.get("sample_teams", []),  # Include sample teams
            "manual_info": result.get("manual_info", {}),    # Include manual info
            "year": year,
        }
        
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", response_model=SetupInfoResponse)
async def get_setup_info(
    db: Session = Depends(get_db_session),
) -> SetupInfoResponse:
    """
    Get current setup information and progress.
    
    Returns the active configuration, setup steps, and overall progress.
    """
    try:
        # Get cached event information
        event_key = cache.get("active_event_key")
        year = cache.get("active_event_year", 2025)
        
        # Try to get active sheet configuration
        sheet_config = None
        config_result = None
        if event_key:
            config_result = await get_active_configuration(db, event_key, year)
        else:
            # Get any active configuration
            config_result = await get_active_configuration(db)
            
            # Update cache if we found a configuration
            if config_result["status"] == "success" and config_result["configuration"]:
                config = config_result["configuration"]
                if config.get("event_key"):
                    cache["active_event_key"] = config["event_key"]
                    event_key = config["event_key"]
        
        # Extract sheet config for frontend compatibility
        if config_result and config_result["status"] == "success" and config_result["configuration"]:
            sheet_config = config_result["configuration"]
        
        # Build setup configuration
        setup_config = {
            "event_key": event_key or "",
            "event_name": "",  # TODO: Get from TBA if event_key exists
            "year": year,
            "sheet_id": None,
            "sheet_configured": False,
            "schema_learned": False,
            "teams_loaded": False,
            "dataset_built": False,
            "setup_complete": False,
            "last_updated": None,
        }
        
        # Update from sheet configuration if available
        if config_result and config_result["status"] == "success" and config_result["configuration"]:
            config = config_result["configuration"]
            setup_config["sheet_id"] = config.get("spreadsheet_id")
            setup_config["sheet_configured"] = bool(config.get("spreadsheet_id"))
            setup_config["event_name"] = config.get("name", "")
        
        # Check other setup steps
        # TODO: Add checks for schema, teams, and dataset
        
        # Calculate overall completion
        setup_config["setup_complete"] = all([
            setup_config["sheet_configured"],
            setup_config["schema_learned"],
            setup_config["teams_loaded"],
            setup_config["dataset_built"],
        ])
        
        # Build setup steps
        steps = [
            {
                "id": "select_event",
                "name": "Select Event",
                "description": "Choose the FRC event to set up",
                "status": "completed" if event_key else "pending",
                "required": True,
                "order": 1,
            },
            {
                "id": "configure_sheet",
                "name": "Configure Google Sheet",
                "description": "Set up Google Sheet connection and tab mappings",
                "status": "completed" if setup_config["sheet_configured"] else "pending",
                "required": True,
                "order": 2,
            },
            {
                "id": "learn_schema",
                "name": "Learn Schema",
                "description": "Analyze spreadsheet headers to build data schema",
                "status": "completed" if setup_config["schema_learned"] else "pending",
                "required": True,
                "order": 3,
            },
            {
                "id": "load_teams",
                "name": "Load Teams",
                "description": "Import team data from The Blue Alliance",
                "status": "completed" if setup_config["teams_loaded"] else "pending",
                "required": True,
                "order": 4,
            },
            {
                "id": "build_dataset",
                "name": "Build Dataset",
                "description": "Combine all data sources into unified dataset",
                "status": "completed" if setup_config["dataset_built"] else "pending",
                "required": True,
                "order": 5,
            },
        ]
        
        # Calculate progress
        completed_steps = sum(1 for step in steps if step["status"] == "completed")
        progress = (completed_steps / len(steps)) * 100
        
        # Determine next step
        next_step = None
        for step in steps:
            if step["status"] == "pending":
                next_step = step["id"]
                break
        
        # Return custom response with sheet config for frontend compatibility
        from fastapi.responses import JSONResponse
        
        response_data = {
            "status": "success",
            "setup": setup_config,
            "steps": steps,
            "progress": progress,
            "next_step": next_step,
            "event_key": event_key,
            "year": year,
            "sheet_config": sheet_config,  # Include sheet config for FieldSelection
        }
        
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))