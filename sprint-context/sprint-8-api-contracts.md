# Sprint 8 API Contracts and Preservation Guarantees

**Service**: PicklistGeneratorService  
**Baseline**: 3,113 lines → Target: ~200 line orchestrator + 6-8 services  
**Contract Status**: IMMUTABLE - Zero tolerance for changes  

---

## Public API Contract (MUST PRESERVE EXACTLY)

### Class Constructor
```python
def __init__(self, unified_dataset_path: str):
    """
    PRESERVATION GUARANTEE: Exact signature and behavior maintained
    
    Required behaviors:
    - Loads dataset from provided path
    - Initializes teams_data, year, event_key from dataset
    - Loads game context if available
    - Initializes token encoder for gpt-4-turbo
    - Sets up class-level cache
    """
```

### Primary Public Methods

#### 1. generate_picklist (Main API)
```python
async def generate_picklist(
    self, 
    pick_position: str,
    priorities: Dict[str, float],
    team_count: Optional[int] = None,
    cache_key: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    PRESERVATION GUARANTEE: Core business logic - exact behavior required
    
    Input Contract:
    - pick_position: str (e.g., "first", "second", "third")
    - priorities: Dict[str, float] (priority weights for scoring)
    - team_count: Optional[int] (number of teams to rank)
    - cache_key: Optional[str] (for result caching)
    - **kwargs: Additional parameters for future extensibility
    
    Output Contract:
    {
        "status": "success|processing|error",
        "picklist": [
            {
                "team_number": int,
                "nickname": str,
                "score": float,
                "reasoning": str
            }
        ],
        "cache_key": str,
        "processing_time": float,
        "total_teams": int,
        "error": str (only if status == "error"),
        "batch_info": dict (only if batch processing used)
    }
    
    Behavioral Requirements:
    - Async operation with proper await patterns
    - Caching based on cache_key parameter
    - Progress tracking for long operations
    - Batch processing for large datasets
    - GPT integration for intelligent analysis
    - Error handling with structured responses
    """
```

#### 2. rank_missing_teams (Secondary API)
```python
async def rank_missing_teams(
    self,
    existing_picklist: List[Dict[str, Any]],
    pick_position: str,
    priorities: Dict[str, float],
    **kwargs
) -> Dict[str, Any]:
    """
    PRESERVATION GUARANTEE: Complementary ranking functionality
    
    Input Contract:
    - existing_picklist: List[Dict] (current ranked teams)
    - pick_position: str (same as generate_picklist)
    - priorities: Dict[str, float] (priority weights)
    - **kwargs: Additional parameters
    
    Output Contract: Same as generate_picklist
    
    Behavioral Requirements:
    - Identifies teams not in existing_picklist
    - Ranks only missing teams using same algorithm
    - Maintains consistency with main picklist generation
    """
```

#### 3. get_batch_processing_status (Status API)
```python
def get_batch_processing_status(self, cache_key: str) -> Dict[str, Any]:
    """
    PRESERVATION GUARANTEE: Progress tracking interface
    
    Input Contract:
    - cache_key: str (identifies the batch operation)
    
    Output Contract:
    {
        "status": "not_found|processing|completed|error",
        "progress": float (0.0 to 1.0),
        "current_batch": int,
        "total_batches": int,
        "estimated_time_remaining": float,
        "teams_processed": int,
        "total_teams": int,
        "error": str (only if status == "error")
    }
    
    Behavioral Requirements:
    - Synchronous operation (not async)
    - Real-time progress information
    - Cache-based status lookup
    """
```

#### 4. merge_and_update_picklist (Utility API)
```python
def merge_and_update_picklist(
    self,
    existing_picklist: List[Dict[str, Any]],
    new_rankings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    PRESERVATION GUARANTEE: Picklist merging logic
    
    Input Contract:
    - existing_picklist: List[Dict] (current picklist)
    - new_rankings: List[Dict] (new team rankings)
    
    Output Contract:
    List[Dict[str, Any]] (merged and sorted picklist)
    
    Behavioral Requirements:
    - Merges two picklists maintaining rank order
    - Handles duplicate teams appropriately
    - Preserves all team metadata
    - Returns sorted by score (highest first)
    """
```

---

## Class-Level Contracts

### Static Cache Management
```python
# Class-level cache to share across instances
_picklist_cache = {}

"""
PRESERVATION GUARANTEE: Caching behavior exactly maintained

Required behaviors:
- Shared across all service instances
- Cache keys based on parameters + dataset state
- Cache invalidation on data changes
- Thread-safe access patterns
"""
```

### Module-Level Configuration
```python
GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

"""
PRESERVATION GUARANTEE: Environment configuration exactly preserved

Required behaviors:
- Model selection via OPENAI_MODEL environment variable
- Default to "gpt-4o" if not specified
- OpenAI client initialization with API key
- Global client sharing across operations
"""
```

---

## Error Handling Contracts

### Expected Error Response Format
```python
{
    "status": "error",
    "error": str,  # Human-readable error message
    "error_type": str,  # Categorized error type
    "details": dict,  # Additional error context
    "cache_key": str,  # If applicable
    "processing_time": float
}
```

### Required Error Categories
1. **Dataset Errors**: Missing or invalid dataset files
2. **GPT API Errors**: OpenAI API failures, rate limits, token limits
3. **Validation Errors**: Invalid input parameters or data
4. **Processing Errors**: Batch processing failures
5. **Cache Errors**: Cache access or corruption issues

### Error Propagation Requirements
- Async errors must be properly awaited and handled
- Batch processing errors must not fail entire operation
- API errors must trigger appropriate retry logic
- All errors must maintain structured response format

---

## Performance Contracts

### Response Time Requirements
- **generate_picklist**: Baseline performance ±5%
- **rank_missing_teams**: Baseline performance ±5%
- **get_batch_processing_status**: <100ms (fast cache lookup)
- **merge_and_update_picklist**: <1s for typical datasets

### Resource Usage Contracts
- **Memory**: Maintain baseline memory footprint
- **CPU**: Efficient batch processing with threading
- **API Calls**: Minimize GPT API usage via caching
- **Disk I/O**: Efficient dataset loading and caching

### Scalability Requirements
- Support datasets with 100+ teams
- Handle multiple concurrent picklist generations
- Maintain performance with large priority weight sets
- Scale batch processing based on dataset size

---

## Integration Contracts

### Frontend Dependencies
```typescript
// Expected by React components - CANNOT CHANGE
interface PicklistGeneratorService {
  generate_picklist(
    pick_position: string,
    priorities: Record<string, number>,
    team_count?: number,
    cache_key?: string
  ): Promise<PicklistResponse>
  
  get_batch_processing_status(cache_key: string): BatchStatus
  
  // ... other methods
}
```

### Backend Service Dependencies
```python
# Must integrate with existing services
from app.services.progress_tracker import ProgressTracker
from app.services.metrics_extraction_service import MetricsExtractionService
from app.services.retry_service import RetryService
```

### External API Dependencies
```python
# OpenAI integration requirements
- Maintain existing prompt formats and response parsing
- Preserve token optimization strategies
- Keep error handling and retry patterns
- Maintain rate limiting compliance
```

---

## Data Format Contracts

### Input Data Requirements
```python
# Unified dataset format (CANNOT CHANGE)
{
    "teams": {
        "team_number": {
            "team_number": int,
            "nickname": str,
            "metrics": dict,
            # ... other team data
        }
    },
    "year": int,
    "event_key": str,
    # ... other dataset metadata
}
```

### Priority Weights Format
```python
# Priority input format (CANNOT CHANGE)
{
    "autonomous": float,
    "teleop": float,
    "endgame": float,
    "defense": float,
    # ... other priority categories
}
```

### Output Data Format
```python
# Picklist response format (CANNOT CHANGE)
{
    "team_number": int,
    "nickname": str,
    "score": float,  # 0.0 to 100.0
    "reasoning": str  # GPT-generated explanation
}
```

---

## Validation Requirements

### Contract Validation Checklist
- [ ] All public method signatures exactly preserved
- [ ] Input parameter types and validation identical
- [ ] Output response formats exactly matched
- [ ] Error handling produces identical error responses
- [ ] Caching behavior maintains same patterns
- [ ] Performance characteristics within 5% tolerance
- [ ] Integration points remain functional
- [ ] Thread safety patterns preserved

### Testing Requirements
- **Unit Tests**: Each decomposed service tested independently
- **Integration Tests**: Service composition tested against baseline
- **Contract Tests**: API contract compliance validation
- **Performance Tests**: Benchmark against baseline metrics
- **Error Tests**: Error handling scenarios validated
- **Concurrent Tests**: Thread safety and cache consistency

---

## Decomposition Implementation Strategy

### Service Boundary Preservation
Each new service MUST:
1. **Maintain Interface Contracts**: Public APIs unchanged
2. **Preserve Behavior**: Identical outputs for identical inputs
3. **Honor Dependencies**: Existing service integrations maintained
4. **Respect Performance**: Meet baseline performance requirements
5. **Handle Errors**: Maintain error handling patterns

### Orchestrator Responsibilities
The main PicklistGeneratorService becomes an orchestrator that:
- Maintains all public method signatures exactly
- Coordinates sub-services to produce identical results
- Preserves caching and performance characteristics
- Handles error aggregation and reporting
- Manages backwards compatibility

---

## Success Definition

**Sprint 8 API contract preservation succeeds when:**
1. ✅ All public methods work identically to baseline
2. ✅ All response formats exactly match baseline
3. ✅ All error scenarios produce identical error responses
4. ✅ Performance remains within 5% of baseline
5. ✅ Frontend integration requires zero changes
6. ✅ Backend service dependencies remain functional
7. ✅ All edge cases and error conditions preserved

This contract document ensures zero breaking changes while enabling dramatic architectural improvements through service decomposition.