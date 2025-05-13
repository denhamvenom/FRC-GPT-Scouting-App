# backend/app/api/sheets_headers.py

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List

from app.services.sheets_service import get_sheet_values, get_sheet_headers
from app.database.db import get_db

router = APIRouter(prefix="/api/sheets", tags=["Sheets"])

@router.get("/headers")
async def get_headers(
    tab: str = Query(..., description="Sheet tab name"),
    optional: bool = Query(False, description="If True, return empty headers instead of error for missing tabs"),
    spreadsheet_id: Optional[str] = Query(None, description="Spreadsheet ID to use (if not provided, uses active config)"),
    db: Session = Depends(get_db)
):
    """
    Get headers from a specific tab in the Google Sheet.

    Args:
        tab: The name of the sheet tab (e.g., "Scouting", "SuperScouting")
        optional: If True, return empty headers instead of error for missing tabs
        spreadsheet_id: Optional spreadsheet ID (will use active config if not provided)
        db: Database session for getting active configuration

    Returns:
        Dict with headers array
    """
    try:
        import logging
        logger = logging.getLogger("sheets_headers_endpoint")
        logger.debug(f"Headers requested for tab={tab}, spreadsheet_id={spreadsheet_id}, optional={optional}")

        # Handle both required and optional tabs
        if optional:
            # For optional tabs like PitScouting, use graceful error handling
            headers: List[str] = []
            try:
                # Fetch first row (headers) from the specified tab
                range_name = f"{tab}!A1:ZZ1"

                # Only log at debug level
                logger.debug(f"Calling get_sheet_values with range_name={range_name}, spreadsheet_id={spreadsheet_id}")

                if not spreadsheet_id:
                    logger.warning("No spreadsheet_id provided - this will likely fail")

                result = await get_sheet_values(range_name, spreadsheet_id, db)

                # Removed excessive logging

                if result and len(result) > 0:
                    headers = result[0]
                    logger.debug(f"Found {len(headers)} headers for {tab}")
                else:
                    logger.warning(f"No headers found for {tab}")
            except Exception as e:
                # Log but don't raise for optional tabs
                logger.warning(f"Error fetching optional tab '{tab}': {str(e)}")

            return {
                "status": "success",
                "tab": tab,
                "headers": headers,
                "count": len(headers),
                "is_empty": len(headers) == 0
            }
        else:
            # For required tabs, use standard error handling
            range_name = f"{tab}!A1:ZZ1"

            # Only log at debug level
            logger.debug(f"Calling get_sheet_values with range_name={range_name}, spreadsheet_id={spreadsheet_id}")

            if not spreadsheet_id:
                logger.warning("No spreadsheet_id provided for required tab - this will likely fail")

            result = await get_sheet_values(range_name, spreadsheet_id, db)

            # Removed excessive logging

            if not result or len(result) == 0:
                logger.warning(f"No headers found in {tab} tab")
                return {
                    "status": "error",
                    "message": f"No headers found in {tab} tab"
                }

            # Return the headers (first row)
            headers = result[0]
            logger.debug(f"Found {len(headers)} headers for {tab}")

            return {
                "status": "success",
                "tab": tab,
                "headers": headers,
                "count": len(headers)
            }

    except Exception as e:
        if optional:
            # For optional tabs, return empty result rather than error
            return {
                "status": "success",
                "tab": tab,
                "headers": [],
                "count": 0,
                "is_empty": True,
                "error": str(e)
            }
        else:
            # For required tabs, raise error
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching headers from {tab}: {str(e)}"
            )

# Fix for 404 Not Found error
@router.get("/available-tabs")
async def get_available_tabs(
    spreadsheet_id: Optional[str] = Query(None, description="Spreadsheet ID to fetch tabs from"),
    event_key: Optional[str] = Query(None, description="Event key to find configuration"),
    year: Optional[int] = Query(None, description="Year to find configuration"),
    validate: bool = Query(False, description="Whether to validate the tabs")
):
    """Standard endpoint for available tabs"""
    return await _get_available_tabs(spreadsheet_id, event_key, year)

@router.get("/sheets")
async def get_sheets(spreadsheet_id: str = Query(..., description="Google Sheet ID to access")):
    """Simple direct endpoint just for getting sheet names by ID"""
    try:
        from app.services.sheets_service import get_all_sheet_names
        import logging
        logger = logging.getLogger("sheets_direct")
        logger.debug(f"Direct sheet access for spreadsheet_id={spreadsheet_id}")

        result = await get_all_sheet_names(spreadsheet_id)

        if result["status"] == "success":
            return {
                "status": "success",
                "sheets": result["sheet_names"]
            }
        else:
            return result
    except Exception as e:
        logger.error(f"Error in direct sheet access: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

async def _get_available_tabs(
    spreadsheet_id: Optional[str] = None,
    event_key: Optional[str] = None,
    year: Optional[int] = None
):
    """
    Get all available tabs in the spreadsheet.

    Args:
        spreadsheet_id: Optional spreadsheet ID (will use active config if not provided)

    Returns:
        Dict with sheet names
    """
    try:
        from app.services.sheets_service import get_all_sheet_names
        import logging
        logger = logging.getLogger("sheets_headers")
        
        logger.info(f"Available tabs requested with parameters: spreadsheet_id={spreadsheet_id}, event_key={event_key}, year={year}")

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
                        logger.info(f"Found spreadsheet ID using event_key and year: {spreadsheet_id}")
                    else:
                        logger.warning(f"No active configuration found for event {event_key} and year {year}")

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
                "message": "No spreadsheet ID provided and no active configuration found"
            }

        logger.info(f"Getting all sheet names for spreadsheet_id: {spreadsheet_id}")
        # Get sheet names without db parameter
        result = await get_all_sheet_names(spreadsheet_id)

        if result["status"] == "error":
            logger.warning(f"Error getting sheet names: {result['message']}")
            return {
                "status": "error",
                "message": result["message"]
            }

        # Rename to "sheets" for this API endpoint for backward compatibility
        if "sheet_names" in result:
            logger.info(f"Successfully retrieved sheet names: {result['sheet_names']}")
            return {
                "status": "success",
                "sheets": result["sheet_names"]
            }
        else:
            return {
                "status": "error",
                "message": "No sheet names returned from service"
            }

    except Exception as e:
        import traceback
        logger = logging.getLogger("sheets_headers")
        logger.error(f"Error fetching available tabs: {str(e)}\n{traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"Error fetching available tabs: {str(e)}"
        }