# backend/app/api/sheet_config.py

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.database.db import get_db
from app.services.sheet_config_service import (
    create_sheet_config,
    get_sheet_configurations,
    get_sheet_configuration,
    get_active_configuration,
    set_active_configuration,
    delete_configuration,
    update_sheet_headers,
)
from app.services.sheets_service import get_sheet_values, test_spreadsheet_connection

router = APIRouter(prefix="/api/sheet-config", tags=["Sheet Configuration"])


# Pydantic models for request/response
class CreateSheetConfigRequest(BaseModel):
    name: str
    spreadsheet_id: str
    match_scouting_sheet: str
    event_key: str
    year: int
    pit_scouting_sheet: Optional[str] = None
    super_scouting_sheet: Optional[str] = None
    set_active: bool = True


class SetActiveRequest(BaseModel):
    config_id: int


class TestConnectionRequest(BaseModel):
    spreadsheet_id: str
    sheet_name: Optional[str] = None


class UpdateHeadersRequest(BaseModel):
    config_id: int
    sheet_type: str  # 'match', 'pit', or 'super'
    headers: List[str]


@router.post("/create")
async def create_configuration(request: CreateSheetConfigRequest, db: Session = Depends(get_db)):
    """
    Create a new sheet configuration or update an existing one.
    """
    result = await create_sheet_config(
        db=db,
        name=request.name,
        spreadsheet_id=request.spreadsheet_id,
        match_scouting_sheet=request.match_scouting_sheet,
        event_key=request.event_key,
        year=request.year,
        pit_scouting_sheet=request.pit_scouting_sheet,
        super_scouting_sheet=request.super_scouting_sheet,
        set_active=request.set_active,
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/list")
async def list_configurations(
    event_key: Optional[str] = None, year: Optional[int] = None, db: Session = Depends(get_db)
):
    """
    Get a list of sheet configurations, optionally filtered by event and year.
    """
    result = await get_sheet_configurations(db, event_key, year)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/active")
async def get_active(
    event_key: Optional[str] = None, year: Optional[int] = None, db: Session = Depends(get_db)
):
    """
    Get the active sheet configuration for an event.
    """
    result = await get_active_configuration(db, event_key, year)

    if result["status"] == "error":
        # Not finding an active configuration is not a critical error
        if result["message"] == "No active configuration found":
            return {
                "status": "warning",
                "message": "No active configuration found",
                "configuration": None,
            }

        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/{config_id}")
async def get_configuration(config_id: int, db: Session = Depends(get_db)):
    """
    Get a specific sheet configuration by ID.
    """
    result = await get_sheet_configuration(db, config_id)

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])

    return result


@router.post("/set-active")
async def activate_configuration(request: SetActiveRequest, db: Session = Depends(get_db)):
    """
    Set a configuration as active and deactivate others for the same event.
    """
    result = await set_active_configuration(db, request.config_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.delete("/{config_id}")
async def delete_config(config_id: int, db: Session = Depends(get_db)):
    """
    Delete a sheet configuration.
    """
    result = await delete_configuration(db, config_id)

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])

    return result


@router.post("/test-connection")
async def test_connection(request: TestConnectionRequest):
    """
    Test the connection to a Google Sheet.
    """
    # Modified to allow testing with just a spreadsheet ID
    # We'll use the first sheet or just check spreadsheet metadata if no sheet name provided

    from app.services.sheets_service import get_all_sheet_names

    try:
        if request.sheet_name:
            # Test with specified sheet
            result = await test_spreadsheet_connection(
                spreadsheet_id=request.spreadsheet_id, sheet_name=request.sheet_name
            )
        else:
            # Just get all sheets
            result = await get_all_sheet_names(request.spreadsheet_id)

            # If success, add found_requested_sheet = True
            if result["status"] == "success":
                result["found_requested_sheet"] = True

        return result
    except Exception as e:
        return {"status": "error", "message": f"Connection test failed: {str(e)}"}


@router.post("/update-headers")
async def update_headers(request: UpdateHeadersRequest, db: Session = Depends(get_db)):
    """
    Update the cached headers for a sheet configuration.
    """
    result = await update_sheet_headers(
        db=db, config_id=request.config_id, sheet_type=request.sheet_type, headers=request.headers
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


# Fixed the endpoint to prevent 422 errors
@router.get("/available-sheets")
async def get_available_sheets(
    spreadsheet_id: Optional[str] = Query(None, description="Spreadsheet ID to fetch sheets from"),
    event_key: Optional[str] = Query(None, description="Event key to find configuration"),
    year: Optional[int] = Query(None, description="Year to find configuration"),
    validate: bool = Query(False, description="Whether to validate the sheets"),
):
    """
    Get a list of available sheets/tabs in a spreadsheet.

    Args:
        spreadsheet_id: Optional spreadsheet ID (will use active config if not provided)

    Returns:
        Dict with sheet names
    """
    try:
        from app.services.sheets_service import get_all_sheet_names
        import logging

        logger = logging.getLogger("sheet_config")

        logger.info(
            f"Available sheets requested with parameters: spreadsheet_id={spreadsheet_id}, event_key={event_key}, year={year}"
        )

        # Get the database session manually to avoid parameter binding issues
        from app.database.db import get_db_session

        db = None
        try:
            db_generator = get_db_session()
            db = next(db_generator)
            logger.info("Successfully obtained database session")
        except Exception as db_error:
            logger.warning(f"Could not get database session: {str(db_error)}")

        # If spreadsheet_id not provided, check if we have event_key and year to get the active config
        if not spreadsheet_id and db:
            try:
                # First, try using event_key and year if they were provided in the request
                if event_key and year:
                    from app.services.sheet_config_service import get_active_configuration

                    # Get the active configuration for the specified event
                    result = await get_active_configuration(db, event_key, year)
                    if result["status"] == "success" and "configuration" in result:
                        spreadsheet_id = result["configuration"]["spreadsheet_id"]
                        logger.info(
                            f"Found spreadsheet ID using event_key and year: {spreadsheet_id}"
                        )
                    else:
                        logger.warning(
                            f"No active configuration found for event {event_key} and year {year}"
                        )

                # If still no spreadsheet_id, try getting it from global cache
                if not spreadsheet_id:
                    from app.services.sheets_service import get_active_spreadsheet_id

                    spreadsheet_id = await get_active_spreadsheet_id(db)
                    if spreadsheet_id:
                        logger.info(f"Found active spreadsheet ID: {spreadsheet_id}")
                    else:
                        logger.warning("Could not find active spreadsheet ID")
            except Exception as e:
                logger.warning(f"Error getting active spreadsheet ID: {str(e)}")

        # No fallback to environment variable - require explicit configuration
        if not spreadsheet_id:
            logger.warning("No spreadsheet ID available and no active configuration found")

        if not spreadsheet_id:
            logger.warning("No spreadsheet ID available")
            return {
                "status": "error",
                "message": "No spreadsheet ID provided and no active configuration found",
            }

        logger.info(f"Getting all sheet names for spreadsheet_id: {spreadsheet_id}")
        # Get sheet names without db parameter
        result = await get_all_sheet_names(spreadsheet_id)

        if result["status"] == "error":
            logger.warning(f"Error getting sheet names: {result['message']}")
            return {"status": "error", "message": result["message"]}

        logger.info(f"Successfully retrieved sheet names: {result.get('sheet_names', [])}")
        return {"status": "success", "sheet_names": result.get("sheet_names", [])}

    except Exception as e:
        import traceback

        logger = logging.getLogger("sheet_config")
        logger.error(f"Error getting available sheets: {str(e)}\n{traceback.format_exc()}")
        return {"status": "error", "message": f"Error getting available sheets: {str(e)}"}
