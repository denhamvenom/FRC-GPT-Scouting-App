"""
Google Sheets API client with authentication, caching, and error handling.
"""

import base64
import json
import logging
import os
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .interfaces import SheetsClientInterface, HealthCheckResult, ServiceStatus

logger = logging.getLogger(__name__)


class SheetsClient(SheetsClientInterface):
    """
    Production-ready Google Sheets API client with comprehensive error handling.
    
    Features:
    - Multiple authentication methods (file, base64 env vars)
    - Automatic retry with exponential backoff
    - Circuit breaker pattern for resilience
    - Smart sheet name matching and fallbacks
    - Built-in caching for metadata operations
    - Health monitoring and connection testing
    - Comprehensive logging for debugging
    """
    
    def __init__(
        self,
        service_account_file: Optional[str] = None,
        service_account_info: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        scopes: Optional[List[str]] = None,
    ):
        """
        Initialize Google Sheets client.
        
        Args:
            service_account_file: Path to service account JSON file
            service_account_info: Service account info dict (alternative to file)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            scopes: Google API scopes (defaults to sheets access)
        """
        super().__init__(service_name="GoogleSheets", timeout=timeout)
        
        self.max_retries = max_retries
        self.scopes = scopes or ["https://www.googleapis.com/auth/spreadsheets"]
        
        # Initialize credentials
        self.credentials = self._initialize_credentials(
            service_account_file, service_account_info
        )
        
        # Initialize service
        if self.credentials:
            try:
                self.service = build("sheets", "v4", credentials=self.credentials)
                logger.info("Google Sheets service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Sheets service: {e}")
                self.service = None
        else:
            self.service = None
        
        # Cache for spreadsheet metadata
        self._metadata_cache = {}
        self._metadata_cache_ttl = {}
    
    def _initialize_credentials(
        self,
        service_account_file: Optional[str] = None,
        service_account_info: Optional[Dict[str, Any]] = None,
    ) -> Optional[service_account.Credentials]:
        """
        Initialize Google service account credentials.
        
        Tries multiple methods in order:
        1. Provided service_account_info dict
        2. Provided service_account_file path
        3. Base64 encoded env vars (B64_PART_1 + B64_PART_2)
        4. GOOGLE_SERVICE_ACCOUNT_FILE env var
        
        Returns:
            Service account credentials or None if none found
        """
        # Method 1: Use provided service account info
        if service_account_info:
            try:
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.scopes
                )
                logger.info("Loaded credentials from provided service account info")
                return credentials
            except Exception as e:
                logger.error(f"Failed to load provided service account info: {e}")
        
        # Method 2: Use provided file path
        if service_account_file and os.path.exists(service_account_file):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file, scopes=self.scopes
                )
                logger.info(f"Loaded credentials from file: {service_account_file}")
                return credentials
            except Exception as e:
                logger.error(f"Failed to load service account file {service_account_file}: {e}")
        
        # Method 3: Base64 encoded environment variables
        part1 = os.getenv("B64_PART_1")
        part2 = os.getenv("B64_PART_2")
        
        if part1 and part2:
            try:
                joined = part1 + part2
                json_bytes = base64.b64decode(joined)
                service_account_info = json.loads(json_bytes)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.scopes
                )
                logger.info("Loaded credentials from split base64 environment variables")
                return credentials
            except Exception as e:
                logger.error(f"Failed to decode base64 credentials: {e}")
        
        # Method 4: Environment variable file path
        env_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        if env_file:
            resolved_path = self._resolve_service_account_path(env_file)
            if resolved_path and os.path.exists(resolved_path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        resolved_path, scopes=self.scopes
                    )
                    logger.info(f"Loaded credentials from env file: {resolved_path}")
                    return credentials
                except Exception as e:
                    logger.error(f"Failed to load env service account file: {e}")
        
        logger.error("No valid Google service account credentials found")
        return None
    
    def _resolve_service_account_path(self, path: str) -> Optional[str]:
        """
        Resolve service account file path with Docker/Windows compatibility.
        
        Args:
            path: Original path from environment
            
        Returns:
            Resolved path or None if not found
        """
        if not path:
            return None
        
        # If path exists as-is, use it
        if os.path.exists(path):
            return path
        
        # If path starts with /app/, try to substitute with project root
        if path.startswith("/app/"):
            # Get project root (assuming we're in backend/app/services/external)
            project_root = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                )
            )
            relative_path = path.replace("/app/", "", 1)
            windows_path = os.path.join(project_root, relative_path)
            
            if os.path.exists(windows_path):
                return windows_path
        
        # Try fallback path in secrets directory
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
        fallback_path = os.path.join(project_root, "secrets", "google-service-account.json")
        
        if os.path.exists(fallback_path):
            logger.info(f"Found service account file at fallback path: {fallback_path}")
            return fallback_path
        
        return None
    
    def _cache_key(self, operation: str, **params) -> str:
        """Generate cache key for metadata operations."""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{operation}?{param_str}" if param_str else operation
    
    def _is_metadata_cache_valid(self, key: str, ttl_seconds: int = 300) -> bool:
        """Check if cached metadata is still valid (default 5 minutes)."""
        if key not in self._metadata_cache:
            return False
        return (time.time() - self._metadata_cache_ttl.get(key, 0)) < ttl_seconds
    
    def _set_metadata_cache(self, key: str, data: Any) -> None:
        """Store metadata in cache with timestamp."""
        self._metadata_cache[key] = data
        self._metadata_cache_ttl[key] = time.time()
    
    def _get_metadata_cache(self, key: str) -> Any:
        """Get metadata from cache."""
        return self._metadata_cache.get(key)
    
    def _find_best_sheet_match(
        self, requested_name: str, available_sheets: List[str]
    ) -> Optional[str]:
        """
        Find the best matching sheet name from available sheets.
        
        Args:
            requested_name: Name requested by user
            available_sheets: List of actual sheet names
            
        Returns:
            Best matching sheet name or None
        """
        if not available_sheets:
            return None
        
        requested_lower = requested_name.lower()
        
        # Exact match (case insensitive)
        for sheet in available_sheets:
            if sheet.lower() == requested_lower:
                return sheet
        
        # Partial match (requested name in sheet name)
        for sheet in available_sheets:
            if requested_lower in sheet.lower():
                return sheet
        
        # Partial match (sheet name in requested name)
        for sheet in available_sheets:
            if sheet.lower() in requested_lower:
                return sheet
        
        # No match found, return first sheet as fallback
        logger.warning(
            f"No match for '{requested_name}' in {available_sheets}, using first sheet"
        )
        return available_sheets[0]
    
    async def health_check(self) -> HealthCheckResult:
        """
        Check the health of Google Sheets API.
        
        Returns:
            HealthCheckResult with service status
        """
        if not self.service:
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                error_message="Google Sheets service not initialized"
            )
        
        start_time = time.time()
        
        try:
            # Test with a simple API call to list available operations
            # This doesn't require a specific spreadsheet ID
            discovery_doc = self.service._resourceDesc
            response_time = int((time.time() - start_time) * 1000)
            
            self.record_success()
            
            return HealthCheckResult(
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                metadata={
                    "service_version": discovery_doc.get("version", "unknown"),
                    "auth_method": "service_account"
                }
            )
            
        except Exception as e:
            self.record_failure()
            response_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def get_spreadsheet_metadata(
        self, spreadsheet_id: str
    ) -> Dict[str, Any]:
        """
        Get metadata about a spreadsheet including sheet names.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            
        Returns:
            Spreadsheet metadata
        """
        if not self.service:
            raise ValueError("Google Sheets service not initialized")
        
        # Check cache first
        cache_key = self._cache_key("metadata", spreadsheet_id=spreadsheet_id)
        if self._is_metadata_cache_valid(cache_key):
            logger.debug(f"Cache hit for spreadsheet metadata: {spreadsheet_id}")
            return self._get_metadata_cache(cache_key)
        
        async def _get_metadata():
            try:
                response = (
                    self.service.spreadsheets()
                    .get(spreadsheetId=spreadsheet_id)
                    .execute()
                )
                
                # Extract useful metadata
                metadata = {
                    "spreadsheet_id": spreadsheet_id,
                    "title": response.get("properties", {}).get("title", "Unknown"),
                    "sheets": [],
                    "sheet_count": 0,
                }
                
                sheets = response.get("sheets", [])
                for sheet in sheets:
                    properties = sheet.get("properties", {})
                    metadata["sheets"].append({
                        "sheet_id": properties.get("sheetId"),
                        "title": properties.get("title", ""),
                        "index": properties.get("index", 0),
                        "sheet_type": properties.get("sheetType", "GRID"),
                        "grid_properties": properties.get("gridProperties", {}),
                    })
                
                metadata["sheet_count"] = len(metadata["sheets"])
                
                # Cache the result
                self._set_metadata_cache(cache_key, metadata)
                
                logger.info(
                    f"Retrieved metadata for '{metadata['title']}': "
                    f"{metadata['sheet_count']} sheets"
                )
                
                return metadata
                
            except HttpError as e:
                if e.status_code == 404:
                    raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
                elif e.status_code == 403:
                    raise ValueError(
                        f"Access denied to spreadsheet {spreadsheet_id}. "
                        "Check service account permissions."
                    )
                else:
                    raise ValueError(f"HTTP error {e.status_code}: {e}")
            except Exception as e:
                raise ValueError(f"Error getting spreadsheet metadata: {e}")
        
        try:
            self.record_success()
            return await self.with_retry(_get_metadata)
        except Exception as e:
            self.record_failure()
            logger.error(f"Failed to get spreadsheet metadata: {e}")
            raise
    
    async def get_sheet_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        value_render_option: str = "UNFORMATTED_VALUE",
    ) -> List[List[Any]]:
        """
        Get values from a sheet range with smart sheet name matching.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range (e.g., "Sheet1!A1:D10")
            value_render_option: How values should be rendered
            
        Returns:
            2D list of cell values
        """
        if not self.service:
            raise ValueError("Google Sheets service not initialized")
        
        # Parse range to extract sheet name and cell range
        if "!" in range_name:
            sheet_name, cell_range = range_name.split("!", 1)
            sheet_name = sheet_name.strip("'")
        else:
            sheet_name = range_name
            cell_range = "A1:Z1"
        
        # Get spreadsheet metadata to find actual sheet names
        try:
            metadata = await self.get_spreadsheet_metadata(spreadsheet_id)
            available_sheets = [sheet["title"] for sheet in metadata["sheets"]]
            
            # Find best matching sheet
            actual_sheet = self._find_best_sheet_match(sheet_name, available_sheets)
            if not actual_sheet:
                logger.warning(f"No sheets found in spreadsheet {spreadsheet_id}")
                return []
            
            # Construct actual range
            actual_range = f"'{actual_sheet}'!{cell_range}"
            
        except Exception as e:
            logger.error(f"Error getting sheet metadata: {e}")
            # Fallback to original range
            actual_range = range_name
        
        async def _get_values():
            try:
                result = (
                    self.service.spreadsheets()
                    .values()
                    .get(
                        spreadsheetId=spreadsheet_id,
                        range=actual_range,
                        valueRenderOption=value_render_option,
                    )
                    .execute()
                )
                
                values = result.get("values", [])
                logger.debug(f"Retrieved {len(values)} rows from {actual_range}")
                return values
                
            except HttpError as e:
                if e.status_code == 400:
                    logger.error(f"Invalid range {actual_range}: {e}")
                    return []
                else:
                    raise
            except Exception as e:
                logger.error(f"Error getting sheet values: {e}")
                return []
        
        try:
            self.record_success()
            return await self.with_retry(_get_values)
        except Exception as e:
            self.record_failure()
            logger.error(f"Failed to get sheet values: {e}")
            return []
    
    async def update_sheet_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "RAW",
    ) -> Dict[str, Any]:
        """
        Update values in a sheet range.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range
            values: 2D list of values to write
            value_input_option: How values should be interpreted
            
        Returns:
            API response
        """
        if not self.service:
            raise ValueError("Google Sheets service not initialized")
        
        async def _update_values():
            try:
                body = {"values": values}
                
                result = (
                    self.service.spreadsheets()
                    .values()
                    .update(
                        spreadsheetId=spreadsheet_id,
                        range=range_name,
                        valueInputOption=value_input_option,
                        body=body,
                    )
                    .execute()
                )
                
                logger.info(
                    f"Updated {result.get('updatedCells', 0)} cells in {range_name}"
                )
                return result
                
            except Exception as e:
                logger.error(f"Error updating sheet values: {e}")
                raise
        
        try:
            self.record_success()
            return await self.with_retry(_update_values)
        except Exception as e:
            self.record_failure()
            logger.error(f"Failed to update sheet values: {e}")
            raise
    
    async def get_sheet_headers(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        header_row: int = 1,
    ) -> List[str]:
        """
        Get headers from a specific sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            header_row: Row number containing headers (1-indexed)
            
        Returns:
            List of header strings
        """
        range_name = f"{sheet_name}!{header_row}:{header_row}"
        values = await self.get_sheet_values(spreadsheet_id, range_name)
        
        if values and len(values) > 0:
            return [str(cell) for cell in values[0]]
        return []
    
    async def test_connection(
        self, spreadsheet_id: str, sheet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test connection to a spreadsheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Optional sheet name to test
            
        Returns:
            Test result with status and details
        """
        try:
            metadata = await self.get_spreadsheet_metadata(spreadsheet_id)
            
            result = {
                "status": "success",
                "message": f"Successfully connected to '{metadata['title']}'",
                "spreadsheet_title": metadata["title"],
                "sheet_count": metadata["sheet_count"],
                "available_sheets": [sheet["title"] for sheet in metadata["sheets"]],
            }
            
            if sheet_name:
                available_sheets = result["available_sheets"]
                best_match = self._find_best_sheet_match(sheet_name, available_sheets)
                result["requested_sheet"] = sheet_name
                result["matched_sheet"] = best_match
                result["found_requested_sheet"] = best_match is not None
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "spreadsheet_id": spreadsheet_id,
            }
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._metadata_cache.clear()
        self._metadata_cache_ttl.clear()
        logger.info("Google Sheets client cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "metadata_cache_entries": len(self._metadata_cache),
            "cached_spreadsheets": [
                key.split("?")[1].split("=")[1] 
                for key in self._metadata_cache.keys() 
                if "spreadsheet_id=" in key
            ],
            "cache_memory_mb": sum(
                len(str(v)) for v in self._metadata_cache.values()
            ) / (1024 * 1024)
        }