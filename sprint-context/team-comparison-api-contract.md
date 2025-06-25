# Team Comparison API Contract - Sprint 3 Baseline

## API Endpoint: POST /api/picklist/compare-teams

### Request Structure
```json
{
  "unified_dataset_path": "string",
  "team_numbers": [1234, 5678],
  "your_team_number": 9999,
  "pick_position": "first|second|third",
  "priorities": [
    {
      "id": "string", 
      "weight": 1.0,
      "reason": "optional string"
    }
  ],
  "question": "optional string",
  "chat_history": [
    {
      "type": "question|answer",
      "content": "string",
      "timestamp": "string"
    }
  ]
}
```

### Response Structure
```json
{
  "status": "success",
  "ordered_teams": [
    {
      "team_number": 1234,
      "nickname": "Team Name",
      "score": 85.5,
      "reasoning": "Brief explanation",
      // ... all original team data fields
    }
  ],
  "summary": "Detailed narrative analysis from GPT",
  "comparison_data": {
    "teams": [
      {
        "team_number": 1234,
        "nickname": "Team Name", 
        "stats": {
          "metric_name": numeric_value
        }
      }
    ],
    "metrics": ["metric_name_1", "metric_name_2"]
  }
}
```

### Critical Preservation Requirements

#### Request Processing
1. **Input Validation**: All Pydantic models must remain identical
2. **Parameter Handling**: Same validation rules and constraints
3. **Error Messages**: Exact same HTTP status codes and error messages

#### Service Interface
```python
async def compare_teams(
    self,
    team_numbers: List[int],
    your_team_number: int, 
    pick_position: str,
    priorities: List[Dict[str, Any]],
    question: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
```

#### Response Behavior
1. **Follow-up Questions**: When `chat_history` and `question` are provided:
   - `ordered_teams` must be `None` 
   - `summary` contains GPT response
   - `comparison_data` uses metric discovery (not GPT suggested)

2. **Initial Analysis**: When no chat history:
   - `ordered_teams` contains ranked team data with scores/reasoning
   - `summary` contains detailed narrative analysis
   - `comparison_data` uses GPT-suggested metrics when available

3. **Error Handling**: Same exceptions and error messages:
   - ValueError for <2 teams or missing teams
   - HTTPException with status 500 for service errors

#### Internal Processing Flow
1. **Data Preparation**: `self.generator._prepare_team_data_for_gpt()`
2. **Team Filtering**: Filter by `team_numbers`, preserve order
3. **Prompt Building**: System prompt + user prompt with priorities
4. **GPT Integration**: OpenAI API call with specific model and parameters
5. **Response Parsing**: JSON parsing with fallback handling
6. **Statistics Extraction**: Metric discovery and comparison table building

#### OpenAI Integration Constraints
- **Model**: GPT_MODEL from environment (default "gpt-4o")
- **Temperature**: 0.2 (must remain identical)
- **Max Tokens**: 2000 for initial, 1500 for follow-up
- **Response Format**: {"type": "json_object"} for initial analysis only

#### Performance Requirements
- **Response Time**: <30 seconds for GPT analysis (95th percentile)
- **Token Management**: Same token counting and limits
- **Memory Usage**: No degradation in memory efficiency

## Refactoring Constraints

### What CAN Be Changed
- Internal service structure and organization
- Private method implementations
- Code organization and separation of concerns
- Documentation and logging improvements
- Performance optimizations that don't affect response timing

### What CANNOT Be Changed
- Public method signatures
- Response structure and field names
- Error handling behavior and messages
- OpenAI API parameters
- Validation rules and constraints
- Processing order that affects results

## Validation Checklist

### API Contract Validation
- [ ] Request parsing identical
- [ ] Response structure unchanged
- [ ] Error handling preserved
- [ ] HTTP status codes same

### Functional Validation  
- [ ] Same teams ranked in same order
- [ ] Identical GPT prompts generated
- [ ] Same metric discovery logic
- [ ] Chat history handling unchanged

### Performance Validation
- [ ] Response times within 5% tolerance
- [ ] Memory usage unchanged
- [ ] Token counting identical
- [ ] No additional API calls

### Integration Validation
- [ ] PicklistGeneratorService integration unchanged
- [ ] Database/file system access patterns same
- [ ] Environment variable usage identical
- [ ] Error propagation preserved