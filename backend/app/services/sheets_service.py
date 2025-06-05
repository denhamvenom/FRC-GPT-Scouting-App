# backend/app/services/sheets_service.py

from typing import Any, List, Dict, Optional
import os
import logging
import base64
import json
from sqlalchemy.orm import Session
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from functools import lru_cache

# Configure logging
logger = logging.getLogger("sheets_service")

load_dotenv()

# ENV Vars
SERVICE_ACCOUNT_FILE_ENV = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
DEFAULT_SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")  # Fallback if no config in DB

# Path resolution logic to handle both Windows and Linux/Docker paths
def resolve_service_account_path(path: str) -> str:
    # If the path exists as-is, use it
    if os.path.exists(path):
        return path

    # If path starts with /app/, try to substitute with the project root
    if path.startswith("/app/"):
        # Get the project root (assuming we're in backend/app/services)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # Replace /app/ with the project root
        relative_path = path.replace("/app/", "", 1)
        windows_path = os.path.join(project_root, relative_path)

        if os.path.exists(windows_path):
            return windows_path

    # Try a direct relative path from project root as a fallback
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fallback_path = os.path.join(project_root, "secrets", "google-service-account.json")

    if os.path.exists(fallback_path):
        logger.info(f"Found service account file at fallback path: {fallback_path}")
        return fallback_path

    # If we get here, we couldn't find the file
    available_dirs = os.listdir(project_root)
    logger.warning(f"Available directories at project root: {available_dirs}")

    # Check if secrets dir exists
    secrets_dir = os.path.join(project_root, "secrets")
    if os.path.exists(secrets_dir):
        logger.warning(f"Secrets directory exists. Contents: {os.listdir(secrets_dir)}")

    # Let the original error happen
    return path

# Resolve the service account file path
SERVICE_ACCOUNT_FILE = resolve_service_account_path(SERVICE_ACCOUNT_FILE_ENV)
logger.info(f"Using service account file: {SERVICE_ACCOUNT_FILE}")

# Setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@lru_cache(maxsize=1)
def get_sheets_service():
    """Create and cache the Google Sheets service."""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    part1 = os.getenv("B64_PART_1")
    part2 = os.getenv("B64_PART_2")

    if part1 and part2:
        try:
            joined = part1 + part2
            json_bytes = base64.b64decode(joined)
            service_account_info = json.loads(json_bytes)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
            logger.info("Loaded service account credentials from split base64 env variables.")
        except Exception as e:
            logger.exception("Failed to decode or parse split base64 credentials.")
            raise
    elif SERVICE_ACCOUNT_FILE:
        SERVICE_ACCOUNT_FILE = resolve_service_account_path(SERVICE_ACCOUNT_FILE_ENV)
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        logger.info(f"Loaded service account credentials from file: {SERVICE_ACCOUNT_FILE}")
    else:
        raise RuntimeError("No valid Google service account credentials found.")

    return build("sheets", "v4", credentials=credentials)


async def get_active_spreadsheet_id(db: Optional[Session] = None) -> str:
    """
    Get the active spreadsheet ID from the database configuration.
    Falls back to the environment variable if no active configuration is found.
    """
    if db:
        # Import here to avoid circular imports
        from app.services.sheet_config_service import get_active_configuration
        from app.services.global_cache import cache
        
        # Try to get the active event key and year from the cache
        event_key = cache.get("active_event_key")
        year = cache.get("active_event_year", 2025)
        
        # First, try to get configuration for the current event
        if event_key:
            result = await get_active_configuration(db, event_key, year)
            if result["status"] == "success":
                print(f"Using active configuration for event {event_key}: {result['configuration']['name']}")
                return result["configuration"]["spreadsheet_id"]
        
        # If no event-specific configuration, try to get any active configuration
        result = await get_active_configuration(db)
        if result["status"] == "success":
            print(f"Using generic active configuration: {result['configuration']['name']}")
            return result["configuration"]["spreadsheet_id"]

    # Instead of falling back to environment variable, require an explicit configuration
    logger.warning("No active configuration found. Please set up a sheet configuration first.")
    # Return None which will cause the calling code to raise a more specific error
    return None

async def get_all_sheets_metadata(spreadsheet_id: str) -> List[dict]:
    """
    Get metadata for all sheets in a spreadsheet, including their exact names.

    Args:
        spreadsheet_id: The ID of the spreadsheet

    Returns:
        List of sheet metadata dictionaries
    """
    try:
        sheet = get_sheets_service().spreadsheets()
        response = sheet.get(spreadsheetId=spreadsheet_id).execute()
        return response.get('sheets', [])
    except Exception as e:
        logger.exception(f"Error getting spreadsheet metadata: {str(e)}")
        return []

async def get_sheet_values(
    range_name: str,
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None
) -> List[List[Any]]:
    """
    Read data from a Google Sheet.

    Args:
        range_name: The range to read (e.g., "Sheet1!A1:D10")
        spreadsheet_id: Optional spreadsheet ID (will use active config if not provided)
        db: Optional database session for getting active configuration

    Returns:
        List of rows containing values
    """
    # Get spreadsheet ID if not provided
    if not spreadsheet_id:
        logger.debug(f"No spreadsheet_id provided for get_sheet_values, using active configuration")
        sheet_id = await get_active_spreadsheet_id(db)
        if sheet_id:
            logger.debug(f"Found active spreadsheet ID: {sheet_id}")
        else:
            logger.error("No active spreadsheet ID found")
            raise ValueError("No spreadsheet ID provided and no active configuration found")
    else:
        sheet_id = spreadsheet_id
        logger.debug(f"Using provided spreadsheet ID: {sheet_id} for range {range_name}")

    # Process the range to extract tab name and range part
    tab_name = range_name
    cell_range = "A1:Z1"
    if "!" in range_name:
        parts = range_name.split("!", 1)
        tab_name = parts[0].strip("'")  # Remove any quotes
        cell_range = parts[1]
    
    try:
        # Get actual sheet names from the spreadsheet to find the right one
        sheets_metadata = await get_all_sheets_metadata(sheet_id)
        sheet_titles = [s.get("properties", {}).get("title", "") for s in sheets_metadata]
        logger.debug(f"Available sheets in spreadsheet: {sheet_titles}")

        # Try to find a case-insensitive match for the tab name
        actual_tab_name = None
        for title in sheet_titles:
            if title.lower() == tab_name.lower():
                actual_tab_name = title
                logger.debug(f"Found matching sheet: '{actual_tab_name}'")
                break
        
        if not actual_tab_name:
            # Try to find a partial match
            for title in sheet_titles:
                if tab_name.lower() in title.lower() or title.lower() in tab_name.lower():
                    actual_tab_name = title
                    logger.debug(f"Found partial match sheet: '{actual_tab_name}'")
                    break

        if not actual_tab_name:
            if sheet_titles:
                # Default to first sheet if no match found
                actual_tab_name = sheet_titles[0]
                logger.warning(f"No matching sheet found for '{tab_name}', using first sheet: '{actual_tab_name}'")
            else:
                logger.error(f"No sheets found in spreadsheet {sheet_id}")
                return []

        # Use the actual sheet name from the spreadsheet
        actual_range = f"{actual_tab_name}!{cell_range}"
        logger.debug(f"Using range: {actual_range}")
        
        sheet = get_sheets_service().spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id, range=actual_range).execute()
        values = result.get("values", [])
        return values
        
    except Exception as e:
        logger.exception(f"Error getting sheet values for {range_name}: {str(e)}")
        # Return empty result on error instead of raising
        logger.warning(f"Returning empty result for {range_name} due to error")
        return []

async def update_sheet_values(
    range_name: str,
    values: List[List[Any]],
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Write data to a Google Sheet.

    Args:
        range_name: The range to write to (e.g., "Sheet1!A1:D10")
        values: The data to write
        spreadsheet_id: Optional spreadsheet ID (will use active config if not provided)
        db: Optional database session for getting active configuration

    Returns:
        Response from the Google Sheets API
    """
    # Get spreadsheet ID if not provided
    sheet_id = spreadsheet_id or await get_active_spreadsheet_id(db)
    if not sheet_id:
        raise ValueError("No spreadsheet ID provided and no active configuration found")

    try:
        body = {"values": values}
        sheet = get_sheets_service().spreadsheets()
        result = sheet.values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()
        return result
    except Exception as e:
        logger.exception(f"Error updating sheet values for {range_name}: {str(e)}")
        raise

async def test_spreadsheet_connection(
    spreadsheet_id: str,
    sheet_name: str
) -> Dict[str, Any]:
    """
    Test the connection to a Google Sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet_name: The name of the sheet to test

    Returns:
        Dictionary with test results
    """
    try:
        # Try to get the first row of the sheet
        range_name = f"{sheet_name}!A1:A1"
        sheet = get_sheets_service().spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

        # Get the spreadsheet title
        metadata = sheet.get(spreadsheetId=spreadsheet_id, fields="properties.title").execute()
        sheet_title = metadata.get("properties", {}).get("title", "Unknown")

        # Get all sheet names
        sheet_metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        sheet_names = [s.get("properties", {}).get("title", "") for s in sheets]

        return {
            "status": "success",
            "message": f"Successfully connected to spreadsheet '{sheet_title}'",
            "spreadsheet_title": sheet_title,
            "available_sheets": sheet_names,
            "found_requested_sheet": sheet_name in sheet_names
        }
    except HttpError as e:
        logger.exception(f"HTTP error testing connection to spreadsheet {spreadsheet_id}: {str(e)}")

        if e.status_code == 404:
            return {
                "status": "error",
                "message": "Spreadsheet not found. Please check the ID and make sure the service account has access."
            }
        elif e.status_code == 403:
            return {
                "status": "error",
                "message": "Access denied. Please share the spreadsheet with the service account email."
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP error {e.status_code}: {str(e)}"
            }
    except Exception as e:
        logger.exception(f"Error testing connection to spreadsheet {spreadsheet_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error testing connection: {str(e)}"
        }

async def get_all_sheet_names(
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Get all sheet names in a spreadsheet.

    Args:
        spreadsheet_id: Optional spreadsheet ID (will use active config if not provided)
        db: Optional database session for getting active configuration

    Returns:
        Dictionary with sheet names
    """
    try:
        # Get spreadsheet ID if not provided
        sheet_id = spreadsheet_id or await get_active_spreadsheet_id(db)
        if not sheet_id:
            return {
                "status": "error",
                "message": "No spreadsheet ID provided and no active configuration found"
            }

        # Get spreadsheet metadata
        try:
            # Use our helper function that gets sheets metadata
            sheets_metadata = await get_all_sheets_metadata(sheet_id)
            sheet_names = [s.get("properties", {}).get("title", "") for s in sheets_metadata]
            
            logger.debug(f"Successfully retrieved {len(sheet_names)} sheet names from spreadsheet {sheet_id}")

            return {
                "status": "success",
                "sheet_names": sheet_names
            }
        except Exception as metadata_error:
            logger.error(f"Error getting sheet metadata: {str(metadata_error)}")
            # Try direct API call as fallback
            sheet = get_sheets_service().spreadsheets()
            metadata = sheet.get(spreadsheetId=sheet_id).execute()
            sheets = metadata.get('sheets', [])
            sheet_names = [s.get("properties", {}).get("title", "") for s in sheets]
            
            logger.debug(f"Fallback: Retrieved {len(sheet_names)} sheet names from spreadsheet {sheet_id}")
            
            return {
                "status": "success",
                "sheet_names": sheet_names
            }
        
    except ValueError as ve:
        logger.warning(f"Value error getting sheet names: {str(ve)}")
        return {
            "status": "error",
            "message": str(ve)
        }
    except Exception as e:
        logger.exception(f"Error getting sheet names for spreadsheet {spreadsheet_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting sheet names: {str(e)}"
        }

async def get_sheet_headers_async(
    tab: str,
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None,
    log_errors: bool = True
) -> List[str]:
    """
    Async version of get_sheet_headers.
    Get headers from a specific sheet tab with optional error suppression.

    Args:
        tab: The name of the sheet tab (e.g., "Scouting", "PitScouting")
        spreadsheet_id: Optional spreadsheet ID
        db: Optional database session
        log_errors: Whether to log exceptions

    Returns:
        List of header strings or empty list if tab doesn't exist
    """
    try:
        # First, get active sheet configuration if spreadsheet_id not provided
        sheet_id = spreadsheet_id
        if not sheet_id:
            if log_errors:
                logger.info(f"No spreadsheet_id provided for tab '{tab}', getting active configuration")
            
            sheet_id = await get_active_spreadsheet_id(db)
            if not sheet_id:
                if log_errors:
                    logger.warning("No active spreadsheet ID found")
                return []
            
            if log_errors:
                logger.info(f"Using active spreadsheet ID: {sheet_id}")
                
            # When using active configuration, also check if we have configured tab names
            if db:
                try:
                    from app.services.sheet_config_service import get_active_configuration
                    from app.services.global_cache import cache
                    
                    event_key = cache.get("active_event_key")
                    year = cache.get("active_event_year", 2025)
                    
                    # Get the active configuration to check if we need to map tab names
                    result = await get_active_configuration(db, event_key, year)
                    if result["status"] == "success":
                        config = result["configuration"]
                        
                        # Map tab name if it's standard
                        if tab == "Scouting" and config.get("match_scouting_sheet"):
                            mapped_tab = config["match_scouting_sheet"]
                            if log_errors:
                                logger.info(f"Mapping 'Scouting' to configured tab: {mapped_tab}")
                            tab = mapped_tab
                        elif tab == "PitScouting" and config.get("pit_scouting_sheet"):
                            mapped_tab = config["pit_scouting_sheet"]
                            if log_errors:
                                logger.info(f"Mapping 'PitScouting' to configured tab: {mapped_tab}")
                            tab = mapped_tab
                        elif tab == "SuperScouting" and config.get("super_scouting_sheet"):
                            mapped_tab = config["super_scouting_sheet"]
                            if log_errors:
                                logger.info(f"Mapping 'SuperScouting' to configured tab: {mapped_tab}")
                            tab = mapped_tab
                except Exception as e:
                    if log_errors:
                        logger.warning(f"Error mapping tab name: {str(e)}")
        
        # Use our get_sheet_values function which has better error handling
        range_name = f"{tab}!A1:ZZ1"
        if log_errors:
            logger.info(f"Getting headers from {range_name} in spreadsheet {sheet_id}")
            
        values = await get_sheet_values(range_name, sheet_id, db)
        
        if not values or len(values) == 0:
            if log_errors:
                logger.warning(f"No headers found in tab '{tab}'")
            return []
            
        if log_errors:
            logger.info(f"Found {len(values[0])} headers in tab '{tab}'")
            
        return values[0]
    except Exception as e:
        if log_errors:
            logger.exception(f"Error getting headers from {tab}: {str(e)}")
        return []

def get_sheet_headers(
    tab: str,
    spreadsheet_id: Optional[str] = None,
    log_errors: bool = True
) -> List[str]:
    """
    Get headers from a specific sheet tab with optional error suppression.

    Args:
        tab: The name of the sheet tab (e.g., "Scouting", "PitScouting")
        spreadsheet_id: Optional spreadsheet ID
        log_errors: Whether to log exceptions

    Returns:
        List of header strings or empty list if tab doesn't exist
    """
    try:
        import asyncio
        from app.database.db import get_db_session
        
        # Get database session for retrieving active configuration
        db = None
        try:
            db_generator = get_db_session()
            db = next(db_generator)
            if log_errors:
                logger.info("Successfully obtained database session in sync headers")
        except Exception as db_error:
            if log_errors:
                logger.warning(f"Could not get database session: {str(db_error)}")
        
        # Check if tab needs to be mapped from configuration
        if not spreadsheet_id and db:
            try:
                from app.database.models import SheetConfiguration
                from app.services.global_cache import cache
                
                event_key = cache.get("active_event_key")
                year = cache.get("active_event_year", 2025)
                
                if log_errors:
                    logger.info(f"Checking for tab mapping for event {event_key}, year {year}")
                
                # Get active configuration
                config = db.query(SheetConfiguration).filter_by(
                    event_key=event_key,
                    year=year,
                    is_active=True
                ).first()
                
                if config:
                    if log_errors:
                        logger.info(f"Found active config: {config.name}")
                    
                    # Map tab name
                    if tab == "Scouting" and config.match_scouting_sheet:
                        original_tab = tab
                        tab = config.match_scouting_sheet
                        if log_errors:
                            logger.info(f"Mapped tab name from '{original_tab}' to '{tab}'")
                    elif tab == "PitScouting" and config.pit_scouting_sheet:
                        original_tab = tab
                        tab = config.pit_scouting_sheet
                        if log_errors:
                            logger.info(f"Mapped tab name from '{original_tab}' to '{tab}'")
                    elif tab == "SuperScouting" and config.super_scouting_sheet:
                        original_tab = tab
                        tab = config.super_scouting_sheet
                        if log_errors:
                            logger.info(f"Mapped tab name from '{original_tab}' to '{tab}'")
                    
                    # Use spreadsheet ID from configuration if none provided
                    if not spreadsheet_id:
                        spreadsheet_id = config.spreadsheet_id
                        if log_errors:
                            logger.info(f"Using spreadsheet ID from active config: {spreadsheet_id}")
            except Exception as e:
                if log_errors:
                    logger.warning(f"Error mapping tab name: {str(e)}")
        
        # If still no spreadsheet ID, return an error
        if not spreadsheet_id:
            if log_errors:
                logger.error("No active sheet configuration found. Please set up a sheet configuration first.")
            return []

        # Try to run the async function
        try:
            # For Windows, we need to use WindowsSelectorEventLoopPolicy
            if os.name == 'nt':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            # Create a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async function
            headers = loop.run_until_complete(get_sheet_headers_async(tab, spreadsheet_id, db, log_errors))
            
            # Close the loop
            loop.close()
            
            return headers
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                # We're already in an async context, can't create a new loop
                # Fall back to direct API call using our get_sheet_values function
                if log_errors:
                    logger.warning(f"Already in async context, using direct API call for {tab}")
                
                # Create a synchronous request to get headers
                sheet = get_sheets_service().spreadsheets()
                
                # Get available sheets first
                try:
                    metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
                    sheets = metadata.get('sheets', [])
                    sheet_titles = [s.get("properties", {}).get("title", "") for s in sheets]
                    
                    # Find the right sheet
                    actual_tab = None
                    for title in sheet_titles:
                        if title.lower() == tab.lower():
                            actual_tab = title
                            break
                    
                    # If not found, try partial match
                    if not actual_tab:
                        for title in sheet_titles:
                            if tab.lower() in title.lower() or title.lower() in tab.lower():
                                actual_tab = title
                                break
                    
                    # If still not found, use first sheet
                    if not actual_tab and sheet_titles:
                        actual_tab = sheet_titles[0]
                    
                    if not actual_tab:
                        return []
                    
                    # Get headers from the sheet
                    range_name = f"{actual_tab}!A1:ZZ1"
                    result = sheet.values().get(
                        spreadsheetId=spreadsheet_id,
                        range=range_name
                    ).execute()
                    
                    values = result.get("values", [])
                    if values:
                        return values[0]
                except Exception as direct_error:
                    if log_errors:
                        logger.exception(f"Error in direct API call: {str(direct_error)}")
                
                return []
            else:
                raise
        
    except Exception as e:
        if log_errors:
            logger.exception(f"Error in sync get_sheet_headers for {tab}: {str(e)}")
        return []