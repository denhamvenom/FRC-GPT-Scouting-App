# backend/app/services/sheet_reader_service.py

from typing import Any, List, Dict, Optional
import logging
import os
import asyncio
from sqlalchemy.orm import Session
from .google_auth_service import GoogleAuthService
from .sheet_metadata_service import SheetMetadataService

logger = logging.getLogger("sheet_reader_service")

class SheetReaderService:
    """Handles Google Sheets read operations with caching and error handling."""
    
    def __init__(self, auth_service: GoogleAuthService, metadata_service: SheetMetadataService):
        self.auth_service = auth_service
        self.metadata_service = metadata_service
    
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
    
    async def get_sheet_values(
        self, range_name: str, spreadsheet_id: Optional[str] = None, db: Optional[Session] = None
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
            logger.debug("No spreadsheet_id provided for get_sheet_values, using active configuration")
            sheet_id = await self.get_active_spreadsheet_id(db)
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
            sheets_metadata = await self.metadata_service.get_all_sheets_metadata(sheet_id)
            sheet_titles = [s.get("properties", {}).get("title", "") for s in sheets_metadata]
            
            # Find matching sheet name
            actual_tab_name = self.metadata_service.find_matching_sheet_name(sheet_titles, tab_name)
            
            if not actual_tab_name:
                logger.error(f"No sheets found in spreadsheet {sheet_id}")
                return []

            # Use the actual sheet name from the spreadsheet
            actual_range = f"{actual_tab_name}!{cell_range}"
            logger.debug(f"Using range: {actual_range}")

            sheet = self.auth_service.get_sheets_service().spreadsheets()
            result = sheet.values().get(spreadsheetId=sheet_id, range=actual_range).execute()
            values = result.get("values", [])
            return values

        except Exception as e:
            logger.exception(f"Error getting sheet values for {range_name}: {str(e)}")
            # Return empty result on error instead of raising
            logger.warning(f"Returning empty result for {range_name} due to error")
            return []
    
    async def get_sheet_headers_async(
        self,
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
        try:
            # First, get active sheet configuration if spreadsheet_id not provided
            sheet_id = spreadsheet_id
            if not sheet_id:
                if log_errors:
                    logger.info(
                        f"No spreadsheet_id provided for tab '{tab}', getting active configuration"
                    )

                sheet_id = await self.get_active_spreadsheet_id(db)
                if not sheet_id:
                    if log_errors:
                        logger.warning("No active spreadsheet ID found")
                    return []

                if log_errors:
                    logger.info(f"Using active spreadsheet ID: {sheet_id}")

                # When using active configuration, also check if we have configured tab names
                if db:
                    tab = await self._map_tab_name(db, tab, log_errors)

            # Use our get_sheet_values function which has better error handling
            range_name = f"{tab}!A1:ZZ1"
            if log_errors:
                logger.info(f"Getting headers from {range_name} in spreadsheet {sheet_id}")

            values = await self.get_sheet_values(range_name, sheet_id, db)

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
    
    async def _map_tab_name(self, db: Session, tab: str, log_errors: bool = True) -> str:
        """Map standard tab names to configured sheet names."""
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
                    return mapped_tab
                elif tab == "PitScouting" and config.get("pit_scouting_sheet"):
                    mapped_tab = config["pit_scouting_sheet"]
                    if log_errors:
                        logger.info(f"Mapping 'PitScouting' to configured tab: {mapped_tab}")
                    return mapped_tab
                elif tab == "SuperScouting" and config.get("super_scouting_sheet"):
                    mapped_tab = config["super_scouting_sheet"]
                    if log_errors:
                        logger.info(f"Mapping 'SuperScouting' to configured tab: {mapped_tab}")
                    return mapped_tab
        except Exception as e:
            if log_errors:
                logger.warning(f"Error mapping tab name: {str(e)}")
        
        return tab
    
    def get_sheet_headers(
        self, tab: str, spreadsheet_id: Optional[str] = None, log_errors: bool = True
    ) -> List[str]:
        """
        Synchronous wrapper for get_sheet_headers_async.
        Get headers from a specific sheet tab with optional error suppression.

        Args:
            tab: The name of the sheet tab (e.g., "Scouting", "PitScouting")
            spreadsheet_id: Optional spreadsheet ID
            log_errors: Whether to log exceptions

        Returns:
            List of header strings or empty list if tab doesn't exist
        """
        try:
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
                    config = (
                        db.query(SheetConfiguration)
                        .filter_by(event_key=event_key, year=year, is_active=True)
                        .first()
                    )

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
                                logger.info(
                                    f"Using spreadsheet ID from active config: {spreadsheet_id}"
                                )
                except Exception as e:
                    if log_errors:
                        logger.warning(f"Error mapping tab name: {str(e)}")

            # If still no spreadsheet ID, return an error
            if not spreadsheet_id:
                if log_errors:
                    logger.error(
                        "No active sheet configuration found. Please set up a sheet configuration first."
                    )
                return []

            # Try to run the async function
            try:
                # For Windows, we need to use WindowsSelectorEventLoopPolicy
                if os.name == "nt":
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

                # Create a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Run the async function
                headers = loop.run_until_complete(
                    self.get_sheet_headers_async(tab, spreadsheet_id, db, log_errors)
                )

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
                    sheet = self.auth_service.get_sheets_service().spreadsheets()

                    # Get available sheets first
                    try:
                        metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
                        sheets = metadata.get("sheets", [])
                        sheet_titles = [s.get("properties", {}).get("title", "") for s in sheets]

                        # Find the right sheet
                        actual_tab = self.metadata_service.find_matching_sheet_name(sheet_titles, tab)

                        if not actual_tab:
                            return []

                        # Get headers from the sheet
                        range_name = f"{actual_tab}!A1:ZZ1"
                        result = (
                            sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
                        )

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