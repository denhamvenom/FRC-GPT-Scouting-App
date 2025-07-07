# Sheets Service API Contracts

## Sprint 6 Service Interface Documentation

**Date**: 2025-06-24  
**Sprint**: Phase 3, Sprint 6  
**Services**: GoogleAuthService, SheetMetadataService, SheetReaderService, SheetWriterService, RetryService

---

## GoogleAuthService

### Purpose
Handles Google authentication and service account management with credential caching.

### Public Interface
```python
class GoogleAuthService:
    def resolve_service_account_path(self, path: Optional[str]) -> Optional[str]:
        """
        Safely resolve a service account file path.
        
        Args:
            path: Optional path to service account file
            
        Returns:
            Resolved path or None if not found/valid
            
        Behavior (preserved from baseline):
        - Returns None if path is None
        - Checks if path exists as absolute path
        - Checks relative to backend directory
        - Preserves exact path resolution order from baseline
        """
        
    @lru_cache(maxsize=1)
    def get_sheets_service(self):
        """
        Create and cache the Google Sheets service.
        
        Returns:
            Google Sheets API service object
            
        Raises:
            ValueError: If no valid credentials found
            
        Behavior (preserved from baseline):
        - Tries service account file first
        - Falls back to base64 encoded credentials
        - Caches service instance for performance
        - Same error messages as baseline
        """
```

### Baseline Compatibility
- Path resolution logic identical to baseline
- Credential loading sequence unchanged
- Error messages preserved exactly
- LRU caching behavior maintained

---

## SheetMetadataService

### Purpose
Manages sheet metadata operations including tab discovery and validation.

### Public Interface
```python
class SheetMetadataService:
    def __init__(self, auth_service: GoogleAuthService):
        """Initialize with auth service dependency."""
        
    async def get_all_sheets_metadata(self, spreadsheet_id: str) -> List[dict]:
        """
        Get metadata for all sheets in a spreadsheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            
        Returns:
            List of sheet metadata dictionaries with properties:
            - sheetId: int
            - title: str
            - index: int
            - gridProperties: dict
            
        Behavior (preserved from baseline):
        - Returns empty list on error
        - Same retry logic for API calls
        - Identical metadata format
        """
        
    async def test_spreadsheet_connection(self, spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
        """
        Test the connection to a Google Sheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_name: The name of the sheet to test
            
        Returns:
            Dictionary with:
            - success: bool
            - message: str
            - sheet_found: bool (if applicable)
            - error: str (if applicable)
            
        Behavior (preserved from baseline):
        - Case-insensitive sheet name matching
        - Same error message formats
        - Identical response structure
        """
        
    async def get_all_sheet_names(self, spreadsheet_id: str) -> Dict[str, Any]:
        """
        Get all sheet names in a spreadsheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            
        Returns:
            Dictionary with:
            - status: "success" or "error"
            - sheets: List[str] (if success)
            - message: str (if error)
            
        Behavior (preserved from baseline):
        - Same error handling
        - Identical response format
        """
```

### Baseline Compatibility
- Case-insensitive matching preserved
- Error message formats unchanged
- Response structures identical
- Retry behavior maintained

---

## SheetReaderService

### Purpose
Handles all sheet reading operations with configuration management and caching.

### Public Interface
```python
class SheetReaderService:
    def __init__(self, auth_service: GoogleAuthService, metadata_service: SheetMetadataService):
        """Initialize with service dependencies."""
        
    async def get_active_spreadsheet_id(self, db: Optional[Session] = None) -> str:
        """
        Get the active spreadsheet ID from configuration.
        
        Args:
            db: Optional database session
            
        Returns:
            Spreadsheet ID or None if not configured
            
        Behavior (preserved from baseline):
        - Checks database for active config first
        - Falls back to environment variable
        - Returns None if no config found
        """
        
    async def get_sheet_values(
        self, range_name: str, spreadsheet_id: Optional[str] = None, db: Optional[Session] = None
    ) -> List[List[Any]]:
        """
        Read data from a Google Sheet.
        
        Args:
            range_name: The range to read (e.g., "Sheet1!A1:D10")
            spreadsheet_id: Optional spreadsheet ID
            db: Optional database session
            
        Returns:
            List of rows containing values
            
        Behavior (preserved from baseline):
        - Uses active config if spreadsheet_id not provided
        - Same error handling for invalid ranges
        - Identical data format returned
        """
        
    async def get_sheet_headers_async(
        self, tab: str, spreadsheet_id: Optional[str] = None, 
        db: Optional[Session] = None, log_errors: bool = True
    ) -> List[str]:
        """
        Async version of get_sheet_headers.
        
        Args:
            tab: Sheet tab name (e.g., "Scouting")
            spreadsheet_id: Optional spreadsheet ID
            db: Optional database session
            log_errors: Whether to log exceptions
            
        Returns:
            List of header strings or empty list
            
        Behavior (preserved from baseline):
        - Maps "Scouting" to configured tab name
        - Same error suppression logic
        - Identical header extraction
        """
        
    def get_sheet_headers(
        self, tab: str, spreadsheet_id: Optional[str] = None, log_errors: bool = True
    ) -> List[str]:
        """
        Sync version of get_sheet_headers.
        
        Behavior: Identical to async version but synchronous
        """
```

### Tab Name Mapping
Preserves exact baseline logic:
- "Scouting" → active_config.match_scouting_sheet
- "SuperScouting" → active_config.super_scouting_sheet
- Other names → passed through unchanged

### Baseline Compatibility
- Configuration resolution unchanged
- Tab mapping logic preserved
- Error handling identical
- Header format maintained

---

## SheetWriterService

### Purpose
Manages all sheet writing operations with proper formatting and error handling.

### Public Interface
```python
class SheetWriterService:
    def __init__(self, auth_service: GoogleAuthService):
        """Initialize with auth service dependency."""
        
    async def update_sheet_values(
        self, range_name: str, values: List[List[Any]], 
        spreadsheet_id: Optional[str] = None, db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Write data to a Google Sheet.
        
        Args:
            range_name: The range to write to
            values: The data to write
            spreadsheet_id: Optional spreadsheet ID
            db: Optional database session
            
        Returns:
            Response from Google Sheets API with:
            - spreadsheetId: str
            - updatedRange: str
            - updatedRows: int
            - updatedColumns: int
            - updatedCells: int
            
        Behavior (preserved from baseline):
        - Same value input option (USER_ENTERED)
        - Identical error handling
        - Response format unchanged
        """
```

### Baseline Compatibility
- Update behavior identical
- Response format preserved
- Error handling unchanged
- Configuration integration maintained

---

## RetryService

### Purpose
Provides reusable retry logic with exponential backoff for Google API operations.

### Public Interface
```python
class RetryService:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """Initialize with retry configuration."""
        
    def with_retry(
        self, retryable_exceptions: tuple = (Exception,),
        max_retries: Optional[int] = None, base_delay: Optional[float] = None
    ):
        """
        Decorator to add retry logic to functions.
        
        Returns:
            Decorated function with retry behavior
            
        Behavior:
        - Exponential backoff between retries
        - Configurable retry count
        - Logs retry attempts
        """
        
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Behavior (preserved from baseline):
        - Same retry count defaults
        - Identical backoff calculation
        - Error logging format maintained
        """
        
    @staticmethod
    def is_retryable_http_error(error: HttpError) -> bool:
        """
        Determine if an HTTP error is retryable.
        
        Returns:
            True for 429, 500, 502, 503, 504 errors
            
        Behavior: Exact same error codes as baseline
        """
        
    def with_google_api_retry(self, max_retries: Optional[int] = None):
        """
        Decorator specifically for Google API calls.
        
        Behavior:
        - Retries on specific HTTP errors
        - Handles connection errors
        - Same backoff pattern as baseline
        """
```

### Baseline Compatibility
- Retry counts unchanged
- Backoff calculation identical
- Error code handling preserved
- Logging format maintained

---

## Integration Patterns

### Service Composition
```python
# All services work together through the orchestrator
sheets_service = SheetsService()

# Internal composition
sheets_service.auth_service        # Authentication
sheets_service.metadata_service    # Metadata operations
sheets_service.reader_service      # Reading data
sheets_service.writer_service      # Writing data
sheets_service.retry_service       # Error handling
```

### Error Propagation
All services maintain baseline error behavior:
- Same exception types raised
- Identical error messages
- Consistent logging patterns
- Preserved retry semantics

### Performance Characteristics
- LRU caching for auth service
- No additional overhead from composition
- Same number of API calls
- Identical timeout behavior

---

## Testing Contracts

### Integration Test Coverage
Each service contract is validated by integration tests:
1. Service instantiation
2. Method signature compatibility
3. Return type validation
4. Error behavior verification
5. Performance benchmarking

### Contract Validation
```python
# Example test pattern
def test_service_contract_preserved():
    # Verify method exists
    assert hasattr(service, 'expected_method')
    
    # Verify signature
    sig = inspect.signature(service.expected_method)
    assert 'expected_param' in sig.parameters
    
    # Verify behavior
    result = service.expected_method(test_input)
    assert result == expected_baseline_output
```

---

## Migration Guide

### For Service Consumers
No changes required - all public APIs preserved:
```python
# Before (works with baseline)
from app.services.sheets_service import get_sheet_values
data = await get_sheet_values("Sheet1!A1:D10")

# After (works identically)
from app.services.sheets_service import get_sheet_values
data = await get_sheet_values("Sheet1!A1:D10")
```

### For Future Development
New features should be added to appropriate services:
- Authentication features → GoogleAuthService
- New metadata operations → SheetMetadataService
- Reading enhancements → SheetReaderService
- Writing improvements → SheetWriterService
- Retry strategies → RetryService

---

## Baseline Preservation Guarantee

All service contracts guarantee:
1. **Identical public interfaces** - Same methods with same signatures
2. **Preserved behavior** - Same outputs for same inputs
3. **Error compatibility** - Same exceptions and messages
4. **Performance parity** - Within 5% of baseline timing
5. **Zero breaking changes** - No consumer modifications needed

This contract documentation ensures future maintainers understand the preservation requirements and can safely extend functionality without breaking existing consumers.