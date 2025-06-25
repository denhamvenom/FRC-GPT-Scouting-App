# backend/app/services/sheet_metadata_service.py

from typing import List, Dict, Any, Optional
import logging
from .google_auth_service import GoogleAuthService

logger = logging.getLogger("sheet_metadata_service")

class SheetMetadataService:
    """Handles sheet metadata operations like sheet discovery and tab validation."""
    
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service
    
    async def get_all_sheets_metadata(self, spreadsheet_id: str) -> List[dict]:
        """
        Get metadata for all sheets in a spreadsheet, including their exact names.

        Args:
            spreadsheet_id: The ID of the spreadsheet

        Returns:
            List of sheet metadata dictionaries
        """
        try:
            sheet = self.auth_service.get_sheets_service().spreadsheets()
            response = sheet.get(spreadsheetId=spreadsheet_id).execute()
            return response.get("sheets", [])
        except Exception as e:
            logger.exception(f"Error getting spreadsheet metadata: {str(e)}")
            return []
    
    async def get_all_sheet_names(self, spreadsheet_id: str) -> Dict[str, Any]:
        """
        Get all sheet names in a spreadsheet.

        Args:
            spreadsheet_id: The spreadsheet ID

        Returns:
            Dictionary with sheet names
        """
        try:
            # Get spreadsheet metadata
            try:
                # Use our helper function that gets sheets metadata
                sheets_metadata = await self.get_all_sheets_metadata(spreadsheet_id)
                sheet_names = [s.get("properties", {}).get("title", "") for s in sheets_metadata]

                logger.debug(
                    f"Successfully retrieved {len(sheet_names)} sheet names from spreadsheet {spreadsheet_id}"
                )

                return {"status": "success", "sheet_names": sheet_names}
            except Exception as metadata_error:
                logger.error(f"Error getting sheet metadata: {str(metadata_error)}")
                # Try direct API call as fallback
                sheet = self.auth_service.get_sheets_service().spreadsheets()
                metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
                sheets = metadata.get("sheets", [])
                sheet_names = [s.get("properties", {}).get("title", "") for s in sheets]

                logger.debug(
                    f"Fallback: Retrieved {len(sheet_names)} sheet names from spreadsheet {spreadsheet_id}"
                )

                return {"status": "success", "sheet_names": sheet_names}

        except ValueError as ve:
            logger.warning(f"Value error getting sheet names: {str(ve)}")
            return {"status": "error", "message": str(ve)}
        except Exception as e:
            logger.exception(f"Error getting sheet names for spreadsheet {spreadsheet_id}: {str(e)}")
            return {"status": "error", "message": f"Error getting sheet names: {str(e)}"}
    
    def find_matching_sheet_name(self, sheet_titles: List[str], target_tab: str) -> Optional[str]:
        """
        Find a matching sheet name using case-insensitive and partial matching.
        
        Args:
            sheet_titles: List of available sheet titles
            target_tab: The tab name to find
            
        Returns:
            The actual sheet name if found, None otherwise
        """
        logger.debug(f"Available sheets in spreadsheet: {sheet_titles}")

        # Try to find a case-insensitive match for the tab name
        for title in sheet_titles:
            if title.lower() == target_tab.lower():
                logger.debug(f"Found matching sheet: '{title}'")
                return title

        # Try to find a partial match
        for title in sheet_titles:
            if target_tab.lower() in title.lower() or title.lower() in target_tab.lower():
                logger.debug(f"Found partial match sheet: '{title}'")
                return title

        # If no match found and we have sheets, use first sheet
        if sheet_titles:
            first_sheet = sheet_titles[0]
            logger.warning(
                f"No matching sheet found for '{target_tab}', using first sheet: '{first_sheet}'"
            )
            return first_sheet
        else:
            logger.error(f"No sheets found in spreadsheet")
            return None
    
    async def test_spreadsheet_connection(self, spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
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
            sheet = self.auth_service.get_sheets_service().spreadsheets()
            result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

            # Get the spreadsheet title
            metadata = sheet.get(spreadsheetId=spreadsheet_id, fields="properties.title").execute()
            sheet_title = metadata.get("properties", {}).get("title", "Unknown")

            # Get all sheet names
            sheet_metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_metadata.get("sheets", [])
            sheet_names = [s.get("properties", {}).get("title", "") for s in sheets]

            return {
                "status": "success",
                "message": f"Successfully connected to spreadsheet '{sheet_title}'",
                "spreadsheet_title": sheet_title,
                "available_sheets": sheet_names,
                "found_requested_sheet": sheet_name in sheet_names,
            }
        except Exception as e:
            from googleapiclient.errors import HttpError
            logger.exception(f"Error testing connection to spreadsheet {spreadsheet_id}: {str(e)}")
            
            if isinstance(e, HttpError):
                if e.status_code == 404:
                    return {
                        "status": "error",
                        "message": "Spreadsheet not found. Please check the ID and make sure the service account has access.",
                    }
                elif e.status_code == 403:
                    return {
                        "status": "error",
                        "message": "Access denied. Please share the spreadsheet with the service account email.",
                    }
                else:
                    return {"status": "error", "message": f"HTTP error {e.status_code}: {str(e)}"}
            else:
                return {"status": "error", "message": f"Error testing connection: {str(e)}"}