# backend/app/services/sheet_writer_service.py

from typing import Any, List, Dict, Optional
import logging
from sqlalchemy.orm import Session
from .google_auth_service import GoogleAuthService

logger = logging.getLogger("sheet_writer_service")

class SheetWriterService:
    """Handles Google Sheets write operations."""
    
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
    
    async def get_active_spreadsheet_id(self, db: Optional[Session] = None) -> str:
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
                    print(
                        f"Using active configuration for event {event_key}: {result['configuration']['name']}"
                    )
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
    
    async def update_sheet_values(
        self,
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
        # Get spreadsheet ID if not provided
        sheet_id = spreadsheet_id or await self.get_active_spreadsheet_id(db)
        if not sheet_id:
            raise ValueError("No spreadsheet ID provided and no active configuration found")

        try:
            body = {"values": values}
            sheet = self.auth_service.get_sheets_service().spreadsheets()
            result = (
                sheet.values()
                .update(
                    spreadsheetId=sheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body=body,
                )
                .execute()
            )
            return result
        except Exception as e:
            logger.exception(f"Error updating sheet values for {range_name}: {str(e)}")
            raise