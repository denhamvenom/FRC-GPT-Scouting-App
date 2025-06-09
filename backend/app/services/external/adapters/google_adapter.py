"""
Legacy adapter for Google Sheets service compatibility.

This adapter provides backward compatibility for existing services that use
the legacy sheets_service module, wrapping the new SheetsClient with the old interface.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from ..sheets_client import SheetsClient
from ..factories import get_sheets_client

logger = logging.getLogger(__name__)


class GoogleSheetsLegacyAdapter:
    """
    Legacy adapter for Google Sheets service compatibility.
    
    This class provides the same interface as the original sheets_service module
    while delegating to the new SheetsClient implementation.
    """
    
    def __init__(
        self,
        service_account_file: Optional[str] = None,
        service_account_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize legacy adapter.
        
        Args:
            service_account_file: Path to service account file
            service_account_info: Service account info dict
        """
        # Get the new client implementation
        self.client = get_sheets_client(
            service_account_file=service_account_file,
            service_account_info=service_account_info,
        )
    
    async def get_active_spreadsheet_id(self, db: Optional[Session] = None) -> Optional[str]:
        """
        Get active spreadsheet ID from database configuration (legacy interface).
        
        Args:
            db: Database session
            
        Returns:
            Active spreadsheet ID or None
        """
        if db:
            # Import here to avoid circular imports
            try:
                from ...sheet_config_service import get_active_configuration
                from ...global_cache import cache
                
                # Try to get the active event key and year from cache
                event_key = cache.get("active_event_key")
                year = cache.get("active_event_year", 2025)
                
                # First, try to get configuration for the current event
                if event_key:
                    result = await get_active_configuration(db, event_key, year)
                    if result["status"] == "success":
                        return result["configuration"]["spreadsheet_id"]
                
                # If no event-specific configuration, try to get any active configuration
                result = await get_active_configuration(db)
                if result["status"] == "success":
                    return result["configuration"]["spreadsheet_id"]
                    
            except Exception as e:
                logger.error(f"Error getting active spreadsheet ID: {e}")
        
        logger.warning("No active configuration found")
        return None
    
    async def get_all_sheets_metadata(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """
        Get metadata for all sheets in a spreadsheet (legacy interface).
        
        Args:
            spreadsheet_id: Spreadsheet ID
            
        Returns:
            List of sheet metadata
        """
        try:
            metadata = await self.client.get_spreadsheet_metadata(spreadsheet_id)
            return metadata.get("sheets", [])
        except Exception as e:
            logger.error(f"Error getting sheets metadata: {e}")
            return []
    
    async def get_sheet_values(
        self,
        range_name: str,
        spreadsheet_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[List[Any]]:
        """
        Read data from a Google Sheet (legacy interface).
        
        Args:
            range_name: Range to read (e.g., "Sheet1!A1:D10")
            spreadsheet_id: Optional spreadsheet ID
            db: Optional database session
            
        Returns:
            List of rows containing values
        """
        # Get spreadsheet ID if not provided
        if not spreadsheet_id:
            spreadsheet_id = await self.get_active_spreadsheet_id(db)
            if not spreadsheet_id:
                logger.error("No spreadsheet ID available")
                return []
        
        return await self.client.get_sheet_values(spreadsheet_id, range_name)
    
    async def update_sheet_values(
        self,
        range_name: str,
        values: List[List[Any]],
        spreadsheet_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Write data to a Google Sheet (legacy interface).
        
        Args:
            range_name: Range to write to
            values: Data to write
            spreadsheet_id: Optional spreadsheet ID
            db: Optional database session
            
        Returns:
            API response
        """
        # Get spreadsheet ID if not provided
        if not spreadsheet_id:
            spreadsheet_id = await self.get_active_spreadsheet_id(db)
            if not spreadsheet_id:
                raise ValueError("No spreadsheet ID available")
        
        return await self.client.update_sheet_values(spreadsheet_id, range_name, values)
    
    async def test_spreadsheet_connection(
        self, spreadsheet_id: str, sheet_name: str
    ) -> Dict[str, Any]:
        """
        Test connection to a spreadsheet (legacy interface).
        
        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_name: Sheet name to test
            
        Returns:
            Test result
        """
        return await self.client.test_connection(spreadsheet_id, sheet_name)
    
    async def get_all_sheet_names(
        self, spreadsheet_id: Optional[str] = None, db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get all sheet names in a spreadsheet (legacy interface).
        
        Args:
            spreadsheet_id: Optional spreadsheet ID
            db: Optional database session
            
        Returns:
            Dictionary with sheet names and status
        """
        try:
            # Get spreadsheet ID if not provided
            if not spreadsheet_id:
                spreadsheet_id = await self.get_active_spreadsheet_id(db)
                if not spreadsheet_id:
                    return {
                        "status": "error",
                        "message": "No spreadsheet ID provided and no active configuration found",
                    }
            
            metadata = await self.client.get_spreadsheet_metadata(spreadsheet_id)
            sheet_names = [sheet["title"] for sheet in metadata["sheets"]]
            
            return {
                "status": "success",
                "sheet_names": sheet_names,
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }
    
    async def get_sheet_headers_async(
        self,
        tab: str,
        spreadsheet_id: Optional[str] = None,
        db: Optional[Session] = None,
        log_errors: bool = True,
    ) -> List[str]:
        """
        Get headers from a specific sheet tab (legacy async interface).
        
        Args:
            tab: Sheet tab name
            spreadsheet_id: Optional spreadsheet ID
            db: Optional database session
            log_errors: Whether to log errors
            
        Returns:
            List of header strings
        """
        try:
            # Get spreadsheet ID if not provided
            if not spreadsheet_id:
                spreadsheet_id = await self.get_active_spreadsheet_id(db)
                if not spreadsheet_id:
                    if log_errors:
                        logger.warning("No active spreadsheet ID found")
                    return []
            
            # Handle tab name mapping if we have a database session
            actual_tab = tab
            if db:
                try:
                    from ...sheet_config_service import get_active_configuration
                    from ...global_cache import cache
                    
                    event_key = cache.get("active_event_key")
                    year = cache.get("active_event_year", 2025)
                    
                    # Get active configuration to check for tab mapping
                    result = await get_active_configuration(db, event_key, year)
                    if result["status"] == "success":
                        config = result["configuration"]
                        
                        # Map standard tab names to configured names
                        if tab == "Scouting" and config.get("match_scouting_sheet"):
                            actual_tab = config["match_scouting_sheet"]
                        elif tab == "PitScouting" and config.get("pit_scouting_sheet"):
                            actual_tab = config["pit_scouting_sheet"]
                        elif tab == "SuperScouting" and config.get("super_scouting_sheet"):
                            actual_tab = config["super_scouting_sheet"]
                            
                except Exception as e:
                    if log_errors:
                        logger.warning(f"Error mapping tab name: {e}")
            
            # Get headers from the sheet
            headers = await self.client.get_sheet_headers(spreadsheet_id, actual_tab)
            
            if log_errors and headers:
                logger.info(f"Found {len(headers)} headers in tab '{actual_tab}'")
            
            return headers
            
        except Exception as e:
            if log_errors:
                logger.error(f"Error getting headers from {tab}: {e}")
            return []
    
    def get_sheet_headers(
        self,
        tab: str,
        spreadsheet_id: Optional[str] = None,
        log_errors: bool = True,
    ) -> List[str]:
        """
        Get headers from a specific sheet tab (legacy sync interface).
        
        Args:
            tab: Sheet tab name
            spreadsheet_id: Optional spreadsheet ID
            log_errors: Whether to log errors
            
        Returns:
            List of header strings
        """
        try:
            import asyncio
            from ...database.db import get_db_session
            
            # Get database session
            db = None
            try:
                db_generator = get_db_session()
                db = next(db_generator)
            except Exception as db_error:
                if log_errors:
                    logger.warning(f"Could not get database session: {db_error}")
            
            # Run async function
            try:
                # Handle event loop issues
                import os
                if os.name == "nt":
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                headers = loop.run_until_complete(
                    self.get_sheet_headers_async(tab, spreadsheet_id, db, log_errors)
                )
                
                loop.close()
                return headers
                
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    # Already in async context, use direct API
                    if log_errors:
                        logger.warning("Already in async context, using direct API call")
                    
                    # Fallback to direct service call
                    if not spreadsheet_id:
                        if log_errors:
                            logger.error("No spreadsheet ID provided for direct call")
                        return []
                    
                    try:
                        # Use the underlying service directly
                        metadata = self.client.service.spreadsheets().get(
                            spreadsheetId=spreadsheet_id
                        ).execute()
                        
                        sheets = metadata.get("sheets", [])
                        sheet_titles = [s.get("properties", {}).get("title", "") for s in sheets]
                        
                        # Find matching sheet
                        actual_tab = None
                        for title in sheet_titles:
                            if title.lower() == tab.lower():
                                actual_tab = title
                                break
                        
                        if not actual_tab and sheet_titles:
                            actual_tab = sheet_titles[0]
                        
                        if actual_tab:
                            result = self.client.service.spreadsheets().values().get(
                                spreadsheetId=spreadsheet_id,
                                range=f"{actual_tab}!A1:ZZ1"
                            ).execute()
                            
                            values = result.get("values", [])
                            return values[0] if values else []
                        
                    except Exception as direct_error:
                        if log_errors:
                            logger.error(f"Direct API call failed: {direct_error}")
                    
                    return []
                else:
                    raise
            
        except Exception as e:
            if log_errors:
                logger.error(f"Error getting headers: {e}")
            return []


# Singleton instance for backward compatibility
_legacy_sheets_adapter: Optional[GoogleSheetsLegacyAdapter] = None


def get_legacy_sheets_adapter(**kwargs) -> GoogleSheetsLegacyAdapter:
    """
    Get singleton instance of legacy Google Sheets adapter.
    
    Args:
        **kwargs: Configuration parameters
        
    Returns:
        Legacy adapter instance
    """
    global _legacy_sheets_adapter
    
    if _legacy_sheets_adapter is None:
        _legacy_sheets_adapter = GoogleSheetsLegacyAdapter(**kwargs)
        logger.info("Created legacy Google Sheets adapter instance")
    
    return _legacy_sheets_adapter


def reset_legacy_sheets_adapter() -> None:
    """Reset the legacy adapter instance (useful for testing)."""
    global _legacy_sheets_adapter
    _legacy_sheets_adapter = None


# Legacy function compatibility
async def get_sheet_values(
    range_name: str,
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> List[List[Any]]:
    """Legacy function for getting sheet values."""
    adapter = get_legacy_sheets_adapter()
    return await adapter.get_sheet_values(range_name, spreadsheet_id, db)


async def update_sheet_values(
    range_name: str,
    values: List[List[Any]],
    spreadsheet_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Legacy function for updating sheet values."""
    adapter = get_legacy_sheets_adapter()
    return await adapter.update_sheet_values(range_name, values, spreadsheet_id, db)


def get_sheet_headers(
    tab: str,
    spreadsheet_id: Optional[str] = None,
    log_errors: bool = True,
) -> List[str]:
    """Legacy function for getting sheet headers."""
    adapter = get_legacy_sheets_adapter()
    return adapter.get_sheet_headers(tab, spreadsheet_id, log_errors)