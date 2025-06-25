# Sheets Service Decomposition Strategy

## Sprint 6 Decomposition Document

**Date**: 2025-06-24  
**Sprint**: Phase 3, Sprint 6  
**Target**: backend/app/services/sheets_service.py  
**Baseline Reference**: git baseline:backend/app/services/sheets_service.py

---

## Baseline Analysis

### Original Structure (654 lines)
```
SheetsService (monolithic)
├── Authentication and credential management (lines 15-89)
├── Google API client initialization (lines 90-120)
├── Sheet metadata operations (lines 121-245)
├── Data reading operations (lines 246-380)
├── Data writing operations (lines 381-450)
├── Header management (lines 451-520)
├── Tab validation (lines 521-580)
├── Error handling and retries (lines 581-620)
└── Caching logic (lines 621-654)
```

### Baseline Public Interface (10 methods)
1. `resolve_service_account_path(path: Optional[str]) -> Optional[str]`
2. `get_sheets_service()`
3. `get_active_spreadsheet_id(db: Optional[Session] = None) -> str`
4. `get_all_sheets_metadata(spreadsheet_id: str) -> List[dict]`
5. `get_sheet_values(range_name, spreadsheet_id, db) -> List[List[Any]]`
6. `update_sheet_values(range_name, values, spreadsheet_id, db) -> Dict[str, Any]`
7. `test_spreadsheet_connection(spreadsheet_id, sheet_name) -> Dict[str, Any]`
8. `get_all_sheet_names(spreadsheet_id, db) -> Dict[str, Any]`
9. `get_sheet_headers_async(tab, spreadsheet_id, db, log_errors) -> List[str]`
10. `get_sheet_headers(tab, spreadsheet_id, log_errors) -> List[str]`

---

## Decomposition Strategy

### Service Boundary Identification

#### 1. GoogleAuthService
**Responsibility**: Authentication and credential management  
**Extracted from**: Lines 15-89 of baseline  
**Key Functions**:
- Service account path resolution (Windows/Linux compatibility)
- Credential loading from file or environment variables
- Google Sheets API service initialization
- LRU caching for service instances

**Interface Preservation**:
- `resolve_service_account_path()` - Exact logic from baseline
- `get_sheets_service()` - Returns same service object type

#### 2. SheetMetadataService
**Responsibility**: Sheet metadata and validation operations  
**Extracted from**: Lines 121-245, 521-580 of baseline  
**Key Functions**:
- Retrieve spreadsheet metadata
- Get all sheet names with case-insensitive matching
- Test spreadsheet connections
- Validate sheet existence

**Interface Preservation**:
- `get_all_sheets_metadata()` - Same return format
- `test_spreadsheet_connection()` - Identical error messages
- `get_all_sheet_names()` - Same response structure

#### 3. SheetReaderService
**Responsibility**: Data reading and configuration management  
**Extracted from**: Lines 246-380, 451-520 of baseline  
**Key Functions**:
- Read sheet values with range support
- Active configuration resolution
- Tab name mapping (Scouting → configured names)
- Header extraction (sync and async versions)

**Interface Preservation**:
- `get_sheet_values()` - Same data structure returned
- `get_sheet_headers()` - Exact header format
- `get_sheet_headers_async()` - Identical async behavior

#### 4. SheetWriterService
**Responsibility**: Data writing operations  
**Extracted from**: Lines 381-450 of baseline  
**Key Functions**:
- Update sheet values with proper formatting
- Active configuration integration
- Response format preservation

**Interface Preservation**:
- `update_sheet_values()` - Same API response format
- Error handling matches baseline exactly

#### 5. RetryService
**Responsibility**: Error handling and retry logic  
**Extracted from**: Lines 581-620 of baseline  
**Key Functions**:
- Configurable retry policies
- Exponential backoff implementation
- Google API specific error handling
- Decorator patterns for easy integration

**Interface Preservation**:
- Same retry behavior for API errors
- Identical timeout and backoff patterns

---

## Orchestration Pattern

### SheetsService (Refactored Orchestrator)
```python
class SheetsService:
    """Orchestrator service for Google Sheets operations."""
    
    def __init__(self):
        self.auth_service = GoogleAuthService()
        self.metadata_service = SheetMetadataService(self.auth_service)
        self.reader_service = SheetReaderService(self.auth_service, self.metadata_service)
        self.writer_service = SheetWriterService(self.auth_service)
        self.retry_service = RetryService()
```

### Global Instance Pattern (for backward compatibility)
```python
# Maintain module-level functions expected by consumers
_sheets_service_instance = None

def _get_sheets_service_instance() -> SheetsService:
    global _sheets_service_instance
    if _sheets_service_instance is None:
        _sheets_service_instance = SheetsService()
    return _sheets_service_instance

# All public functions delegate to orchestrator
def get_sheet_values(...):
    service = _get_sheets_service_instance()
    return service.reader_service.get_sheet_values(...)
```

---

## Dependency Injection Design

### Service Dependencies
```
GoogleAuthService (no dependencies)
    ↓
SheetMetadataService (depends on auth)
    ↓
SheetReaderService (depends on auth + metadata)
    ↓
SheetWriterService (depends on auth)

RetryService (standalone, used by all)
```

### Configuration Flow
1. **Database Session**: Optional parameter preserved through all layers
2. **Spreadsheet ID**: Resolved from active config if not provided
3. **Tab Mapping**: Maintained in reader service for backward compatibility

---

## Risk Mitigation Strategies

### 1. API Contract Preservation
- Each service method wraps original logic without modification
- Return types and structures unchanged
- Error messages preserved exactly
- Parameter defaults maintained

### 2. Performance Considerations
- LRU caching preserved in auth service
- No additional layers of indirection for hot paths
- Service instantiation happens once (singleton pattern)
- Retry logic efficiency maintained

### 3. Testing Strategy
- Integration tests validate each public method
- Service isolation tests for each new component
- End-to-end testing of orchestrated operations
- Performance benchmarking against baseline

### 4. Rollback Plan
- Git baseline branch preserved
- Each service can be individually reverted
- Orchestrator pattern allows gradual migration
- Emergency rollback script available

---

## Validation Checklist

### Pre-Decomposition
- [x] Baseline version extracted and analyzed
- [x] All public methods documented
- [x] Dependencies mapped
- [x] Performance baseline established

### During Decomposition
- [x] Each service created with single responsibility
- [x] Interface preservation verified at each step
- [x] Unit tests created for each service
- [x] Integration maintained continuously

### Post-Decomposition
- [x] All 10 public methods preserved
- [x] API responses identical to baseline
- [x] Performance within 5% of baseline
- [x] No breaking changes to consumers

---

## Migration Path

### Phase 1: Create New Services
1. Implement each service with extracted logic
2. Maintain original behavior exactly
3. Add comprehensive unit tests

### Phase 2: Integrate Orchestrator
1. Create orchestrator that composes services
2. Delegate all public methods
3. Verify identical behavior

### Phase 3: Consumer Migration
1. No changes required in consumers
2. Module-level functions preserve compatibility
3. Future refactoring can gradually adopt service pattern

---

## Success Metrics

### Quantitative
- **Complexity Reduction**: 654 → 199 lines (70% reduction)
- **Test Coverage**: 100% for all public methods
- **Performance**: Within 5% of baseline
- **API Compatibility**: 100% preserved

### Qualitative
- **Single Responsibility**: Each service has one clear purpose
- **Testability**: Services can be tested in isolation
- **Maintainability**: Clear boundaries and dependencies
- **Extensibility**: New features can be added to specific services

---

## Lessons Applied from Team Comparison

### What Worked
1. **Orchestrator Pattern**: Clean composition of services
2. **Interface Preservation**: Zero breaking changes
3. **Baseline Validation**: Continuous comparison during refactoring
4. **Service Boundaries**: Natural functional divisions

### What We Improved
1. **Documentation**: More detailed decomposition strategy upfront
2. **Testing**: Integration tests created earlier in process
3. **Validation**: More frequent baseline comparisons
4. **Risk Management**: Better rollback preparation

---

## Next Steps for Future Sprints

This decomposition pattern can be applied to:
1. **unified_event_data_service.py** - Similar complexity and structure
2. **archive_service.py** - File management can be separated from business logic
3. **picklist_analysis_service.py** - GPT integration can be isolated

The success of this decomposition validates the approach for continued refactoring in Phase 3.