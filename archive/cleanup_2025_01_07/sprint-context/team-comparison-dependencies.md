# Team Comparison Workflow - Complete Dependency Analysis

## Executive Summary
The Team Comparison feature represents an ideal canary for refactoring due to its moderate complexity, clear boundaries, and comprehensive integration of both frontend and backend systems while maintaining independence from other workflows.

## Complete File Inventory

### Frontend Components
- **Primary Component**: `frontend/src/components/TeamComparisonModal.tsx` (589 lines)
  - Complex React component with three-panel layout
  - Manages team selection, GPT chat, and statistical comparison
  - State management for chat history, loading states, and user interactions

- **Integration Point**: `frontend/src/components/PicklistGenerator.tsx`
  - Team selection checkboxes (max 3 teams)
  - "Compare & Re-Rank" button visibility
  - Modal trigger and state management

### Backend Services
- **API Layer**: `backend/app/api/team_comparison.py`
  - Single endpoint: `POST /api/picklist/compare-teams`
  - Request validation using Pydantic models
  - Thin wrapper around service layer

- **Service Layer**: `backend/app/services/team_comparison_service.py` (415 lines)
  - Core GPT integration and response parsing
  - Statistical data processing
  - Team ranking algorithm

## External Dependencies

### Critical Dependencies
1. **OpenAI API**
   - Model: GPT-4o (configurable via OPENAI_MODEL env var)
   - API Key: Required via OPENAI_API_KEY env var
   - Purpose: Team analysis and ranking generation
   - Token counting and rate limiting handled

2. **Unified Dataset**
   - File-based data source (JSON)
   - No database dependencies
   - Shared with PicklistGeneratorService

### Internal Dependencies
- **PicklistGeneratorService**: Reused for team data preparation
- **Frontend State**: Integration with PicklistGenerator component state
- **API Communication**: Single REST endpoint with comprehensive payload

## Data Flow Architecture

### Request Flow
1. User selects 2-3 teams via PicklistGenerator checkboxes
2. "Compare & Re-Rank" button opens TeamComparisonModal
3. Modal constructs request with:
   - `unified_dataset_path`
   - `team_numbers` (array)
   - `your_team_number`
   - `pick_position` (first/second/third)
   - `priorities` (metric weights)
   - `question` (optional follow-up)
   - `chat_history` (optional conversation context)

### Response Structure
```json
{
  "ordered_teams": [
    {
      "team_number": 1234,
      "nickname": "Team Name", 
      "score": 85.5,
      "reasoning": "Detailed analysis"
    }
  ],
  "summary": "GPT narrative analysis",
  "comparison_data": {
    "teams": [/* Statistical team data */],
    "metrics": [/* Field names for comparison table */]
  }
}
```

## Integration Points

### Frontend Integration
- **State Management**: 
  - `selectedTeams` array in PicklistGenerator
  - `showComparison` boolean for modal visibility
  - Modal manages own chat history and loading states

- **User Interface**:
  - Three-panel modal layout (selection, chat, comparison)
  - Real-time team selection updates
  - Chat interface for follow-up questions
  - Statistical comparison table

### Backend Integration
- **Service Isolation**: Self-contained service with clear interface
- **Shared Utilities**: Leverages PicklistGeneratorService for data access
- **Error Handling**: Comprehensive error responses and logging

## Refactoring Opportunities

### Backend Service (team_comparison_service.py)
**Current Issues**:
- 415-line monolithic class
- GPT prompt construction mixed with data processing
- Response parsing logic embedded in service
- No clear separation of concerns

**Refactoring Targets**:
1. **Prompt Management**: Extract prompt building to separate module
2. **Response Parser**: Isolate GPT response parsing logic
3. **Data Processor**: Separate statistical analysis logic
4. **Service Orchestration**: Clean interface between components

### Frontend Component (TeamComparisonModal.tsx)
**Current Issues**:
- 589-line component handling multiple responsibilities
- Chat logic mixed with comparison display
- State management complexity

**Refactoring Targets**:
1. **Component Decomposition**: Split into smaller focused components
2. **State Management**: Clarify state responsibilities
3. **Hook Extraction**: Extract custom hooks for chat and comparison logic

## Testing Strategy

### Critical Validation Points
1. **API Contract**: Exact request/response structure preservation
2. **Visual Preservation**: Three-panel modal layout unchanged
3. **User Interactions**: Team selection, chat, comparison table
4. **Performance**: GPT response times within tolerance
5. **Error Handling**: Network failures, API errors, invalid responses

### Test Scenarios
1. **Basic Comparison**: 2 teams, standard analysis
2. **Three-Team Comparison**: Maximum team count
3. **Follow-up Questions**: Chat history preservation
4. **Error Conditions**: Network failures, API timeouts
5. **Edge Cases**: Invalid team numbers, missing data

## Rollback Considerations

### Isolated Impact
- **Database**: No database schema dependencies
- **API Contracts**: Single endpoint affects only this feature
- **Frontend Routes**: No routing changes required
- **External Services**: Only OpenAI API dependency

### Safe Rollback Points
1. **Backend Service Only**: API contract preserved
2. **Frontend Component Only**: Service unchanged
3. **Full Feature**: Complete rollback to baseline
4. **Partial Rollback**: Individual component restoration

## Risk Assessment

### Low Risk Factors
- **Isolated Feature**: No dependencies on other workflows
- **Clear Boundaries**: Well-defined API and component interfaces
- **Single External Dependency**: Only OpenAI API integration
- **No Data Migration**: File-based data source unchanged

### Medium Risk Factors
- **GPT Integration**: External service dependency
- **Complex UI**: Three-panel modal with multiple states
- **State Management**: Integration with parent component

### Mitigation Strategies
- **API Mocking**: Test without OpenAI dependency
- **Visual Regression**: Pixel-perfect comparison validation
- **Integration Testing**: End-to-end workflow validation
- **Performance Monitoring**: GPT response time tracking

## Success Criteria

### Functional Preservation
- [ ] Team selection behavior identical
- [ ] Modal opening/closing unchanged
- [ ] Chat functionality preserved
- [ ] Comparison table rendering identical
- [ ] API responses byte-identical

### Performance Preservation
- [ ] Modal load time within 5% of baseline
- [ ] GPT response times unchanged
- [ ] UI responsiveness maintained
- [ ] Memory usage comparable

### Visual Preservation
- [ ] Three-panel layout unchanged
- [ ] Button styles and positions identical
- [ ] Chat interface appearance preserved
- [ ] Comparison table styling unchanged
- [ ] Loading states visually identical

## Conclusion

The Team Comparison workflow is an excellent canary candidate because:
1. **Moderate Complexity**: Sufficient to validate refactoring approach
2. **Clear Boundaries**: Well-isolated from other system components
3. **Full Stack Coverage**: Tests both frontend and backend refactoring
4. **External Integration**: Validates API preservation patterns
5. **Low Risk**: Isolated impact with clear rollback paths

This analysis provides the foundation for safe, incremental refactoring with confidence in our ability to preserve exact behavior while improving code structure.