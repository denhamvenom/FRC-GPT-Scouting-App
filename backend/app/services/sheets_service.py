# backend/app/services/sheets_service.py

from typing import Any, List, Dict, Optional
import logging
from sqlalchemy.orm import Session
from .google_auth_service import GoogleAuthService
from .sheet_metadata_service import SheetMetadataService
from .sheet_reader_service import SheetReaderService
from .sheet_writer_service import SheetWriterService
from .retry_service import RetryService

# Configure logging
logger = logging.getLogger("sheets_service")


class SheetsService:
    """Orchestrator service for Google Sheets operations."""
    
    def __init__(self):
        self.auth_service = GoogleAuthService()
        self.metadata_service = SheetMetadataService(self.auth_service)
        self.reader_service = SheetReaderService(self.auth_service, self.metadata_service)
        self.writer_service = SheetWriterService(self.auth_service)
        self.retry_service = RetryService()


# Global instance for backward compatibility
_sheets_service_instance = None

def _get_sheets_service_instance() -> SheetsService:
    """Get the global SheetsService instance."""
    global _sheets_service_instance
    if _sheets_service_instance is None:
        _sheets_service_instance = SheetsService()
    return _sheets_service_instance


# Preserve original function for backward compatibility
def resolve_service_account_path(path: Optional[str]) -> Optional[str]:
    """Safely resolve a service account file path."""
    service = _get_sheets_service_instance()
    return service.auth_service.resolve_service_account_path(path)


def get_sheets_service():
    """Create and cache the Google Sheets service."""
    service = _get_sheets_service_instance()
    return service.auth_service.get_sheets_service()


async def get_active_spreadsheet_id(db: Optional[Session] = None) -> str:
    """
    Get the active spreadsheet ID from the database configuration.
    Falls back to the environment variable if no active configuration is found.
    """
    service = _get_sheets_service_instance()
    return await service.reader_service.get_active_spreadsheet_id(db)


async def get_all_sheets_metadata(spreadsheet_id: str) -> List[dict]:
    """
    Get metadata for all sheets in a spreadsheet, including their exact names.

    Args:
        spreadsheet_id: The ID of the spreadsheet

    Returns:
        List of sheet metadata dictionaries
    """
    service = _get_sheets_service_instance()
    return await service.metadata_service.get_all_sheets_metadata(spreadsheet_id)


async def get_sheet_values(
    range_name: str, spreadsheet_id: Optional[str] = None, db: Optional[Session] = None
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
    service = _get_sheets_service_instance()
    return await service.reader_service.get_sheet_values(range_name, spreadsheet_id, db)


async def update_sheet_values(
    range_name: str,
    values: List[List[Any]],
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None,
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
    service = _get_sheets_service_instance()
    return await service.writer_service.update_sheet_values(range_name, values, spreadsheet_id, db)


async def test_spreadsheet_connection(spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
    """
    Test the connection to a Google Sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet_name: The name of the sheet to test

    Returns:
        Dictionary with test results
    """
    service = _get_sheets_service_instance()
    return await service.metadata_service.test_spreadsheet_connection(spreadsheet_id, sheet_name)


async def get_all_sheet_names(
    spreadsheet_id: Optional[str] = None, db: Optional[Session] = None
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
        service = _get_sheets_service_instance()
        sheet_id = spreadsheet_id or await service.reader_service.get_active_spreadsheet_id(db)
        if not sheet_id:
            return {
                "status": "error",
                "message": "No spreadsheet ID provided and no active configuration found",
            }

        return await service.metadata_service.get_all_sheet_names(sheet_id)
    except ValueError as ve:
        logger.warning(f"Value error getting sheet names: {str(ve)}")
        return {"status": "error", "message": str(ve)}
    except Exception as e:
        logger.exception(f"Error getting sheet names for spreadsheet {spreadsheet_id}: {str(e)}")
        return {"status": "error", "message": f"Error getting sheet names: {str(e)}"}


async def get_sheet_headers_async(
    tab: str,
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None,
    log_errors: bool = True,
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
    service = _get_sheets_service_instance()
    return await service.reader_service.get_sheet_headers_async(tab, spreadsheet_id, db, log_errors)


def get_sheet_headers(
    tab: str, spreadsheet_id: Optional[str] = None, log_errors: bool = True
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
    service = _get_sheets_service_instance()
    return service.reader_service.get_sheet_headers(tab, spreadsheet_id, log_errors)
