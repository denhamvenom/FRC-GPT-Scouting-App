# AI Prompt Templates

**Purpose**: Standardized AI prompts for common development tasks  
**Audience**: AI assistants, developers using AI tools  
**Scope**: Complete collection of tested prompt templates for autonomous development  

---

## Prompt Template Framework

This document provides **battle-tested prompt templates** specifically designed for AI assistants working with the FRC GPT Scouting App. Each template includes context, constraints, and validation criteria to ensure consistent, high-quality results.

### Template Categories
- **Analysis Prompts**: Understanding code and requirements
- **Implementation Prompts**: Generating new code and features
- **Testing Prompts**: Creating comprehensive test suites
- **Documentation Prompts**: Generating and maintaining documentation
- **Debugging Prompts**: Identifying and fixing issues
- **Review Prompts**: Code review and quality assessment

---

## Analysis Prompt Templates

### System Analysis Template
```markdown
# System Analysis: [SPECIFIC_ANALYSIS_TARGET]

You are analyzing the FRC GPT Scouting App to understand [SPECIFIC_ASPECT].

## System Context
- **Architecture**: Service-oriented with 6 specialized services coordinated by PicklistGeneratorService
- **Tech Stack**: React TypeScript frontend, Python FastAPI backend, SQLite database
- **AI Integration**: OpenAI GPT-4 for strategic analysis, designed for Claude Code development
- **Current State**: Well-established patterns in existing services

## Analysis Focus
**Target**: [Specific component/feature/issue to analyze]
**Scope**: [Breadth of analysis required]
**Depth**: [Level of detail needed]

## Analysis Requirements
1. **Current Implementation Patterns**
   - Identify existing patterns used for similar functionality
   - Document current service boundaries and responsibilities
   - Map data flow and integration points

2. **Integration Impact Assessment**
   - Determine which services would be affected
   - Identify API changes required (if any)
   - Assess database schema impacts

3. **Compliance Validation**
   - Verify alignment with service-oriented architecture
   - Check adherence to established coding standards
   - Validate consistency with existing error handling patterns

4. **Risk and Complexity Assessment**
   - Identify potential technical risks
   - Estimate implementation complexity
   - Highlight dependencies and constraints

## Reference Materials
- **Service Architecture**: `docs/03_ARCHITECTURE/SERVICE_ARCHITECTURE.md`
- **API Contracts**: `docs/03_ARCHITECTURE/API_CONTRACTS.md`
- **Coding Standards**: `docs/04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md`
- **Service Contracts**: `docs/05_AI_FRAMEWORK/SERVICE_CONTRACTS.md`

## Required Output Format
```yaml
analysis_summary:
  component_affected: [list]
  integration_points: [list]
  complexity_level: [low|medium|high]
  
current_patterns:
  similar_implementations: [file_paths_and_descriptions]
  established_patterns: [pattern_descriptions]
  
impact_assessment:
  services_modified: [service_list]
  api_changes: [endpoint_changes]
  database_changes: [schema_changes]
  
recommendations:
  approach: [recommended_implementation_approach]
  considerations: [important_considerations]
  potential_issues: [risks_and_mitigations]
```

## Validation Criteria
- [ ] Analysis covers all affected components
- [ ] Integration points clearly identified
- [ ] Recommendations follow established patterns
- [ ] Risk assessment is comprehensive
- [ ] Output follows required format
```

### Requirement Analysis Template
```markdown
# Requirement Analysis: [FEATURE_NAME]

You are analyzing requirements for a new feature in the FRC GPT Scouting App.

## Feature Requirements
**Feature Name**: [Feature name]
**Business Purpose**: [Why this feature is needed]
**User Stories**: 
- [User story 1]
- [User story 2]
- [User story 3]

**Acceptance Criteria**:
- [ ] [Criteria 1]
- [ ] [Criteria 2]
- [ ] [Criteria 3]

## Technical Analysis Required
1. **Service Architecture Impact**
   - Which existing services need modification?
   - Are new services required?
   - How does this fit the current 6-service architecture?

2. **API Design Requirements**
   - What new endpoints are needed?
   - What request/response formats are required?
   - How does this integrate with existing API patterns?

3. **Data Model Impact**
   - What new data structures are needed?
   - Are database schema changes required?
   - How does data flow through the system?

4. **Frontend Integration**
   - What UI components are needed?
   - How does this integrate with existing React components?
   - What state management is required?

## Implementation Strategy
Analyze and recommend:
- **Development Approach**: Service-first, API-first, or UI-first
- **Service Design**: Which services to create/modify and why
- **Integration Pattern**: How components work together
- **Testing Strategy**: Unit, integration, and end-to-end testing approach

## Output Required
```yaml
feature_analysis:
  complexity: [low|medium|high]
  estimated_effort: [hours]
  dependencies: [list_of_dependencies]

technical_design:
  new_services: [service_names_and_purposes]
  modified_services: [services_and_modifications]
  api_endpoints: [endpoint_definitions]
  data_changes: [data_model_changes]

implementation_plan:
  phases: [development_phases]
  testing_approach: [testing_strategy]
  integration_points: [integration_considerations]
```
```

---

## Implementation Prompt Templates

### Service Creation Template
```markdown
# Service Implementation: [SERVICE_NAME]

You are implementing a new service for the FRC GPT Scouting App following established architectural patterns.

## Service Specification
**Service Name**: [ServiceName]
**Purpose**: [Clear, specific purpose statement]
**Layer**: [Data Layer | Analysis Layer | AI Layer]
**Responsibilities**: 
- [Responsibility 1]
- [Responsibility 2] 
- [Responsibility 3]

**Dependencies**:
- Internal: [internal_dependencies]
- External: [external_libraries]
- Services: [other_service_dependencies]

## Implementation Requirements

### 1. Service Structure
Follow the established service pattern from existing services:
- Class-based design with clear constructor
- Public methods with comprehensive docstrings and type hints
- Private methods for internal implementation
- Consistent error handling with logging
- Input validation for all public methods

### 2. Code Quality Standards
- **Type Hints**: All method parameters and return values
- **Documentation**: Docstrings with examples for all public methods
- **Error Handling**: Try/catch blocks with specific exceptions
- **Logging**: Appropriate levels (INFO for operations, ERROR for failures)
- **Validation**: Input validation with clear error messages

### 3. Integration Pattern
- **Orchestrator Integration**: How to integrate with PicklistGeneratorService
- **Service Isolation**: No direct calls to other services
- **State Management**: How the service manages its internal state
- **Resource Management**: Proper initialization and cleanup

## Reference Implementation
Study similar services for patterns:
- **Similar Service**: [path/to/similar/service.py]
- **Integration Example**: [path/to/orchestrator/integration.py]
- **Test Pattern**: [path/to/test/example.py]

## Implementation Template
```python
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("services.[service_name]")

class [ServiceName]:
    """
    [Service purpose and responsibility].
    
    This service [detailed description of functionality].
    Follows established service patterns with comprehensive error handling.
    """

    def __init__(self, dependencies):
        """
        Initialize [ServiceName] with required dependencies.
        
        Args:
            dependencies: [Description of required dependencies]
        """
        self.dependency = dependencies
        logger.info(f"Initialized {self.__class__.__name__}")

    def public_method(self, param: ParamType) -> ReturnType:
        """
        [Method description and purpose].
        
        Args:
            param: [Parameter description with constraints]
            
        Returns:
            [Return value description and format]
            
        Raises:
            ValueError: [When this exception is raised]
            ServiceError: [When service errors occur]
            
        Example:
            >>> service = [ServiceName](dependencies)
            >>> result = service.public_method(value)
            >>> print(result)
            [Expected output]
        """
        try:
            # Input validation
            if not self._validate_input(param):
                raise ValueError(f"Invalid parameter: {param}")
            
            # Process following established patterns
            result = self._process_data(param)
            
            logger.info(f"Successfully processed {param}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ServiceError(f"Operation failed: {str(e)}")

    def _private_method(self, param: ParamType) -> ReturnType:
        """Private implementation method."""
        pass
        
    def _validate_input(self, param: ParamType) -> bool:
        """Validate input parameters."""
        pass
```

## Testing Requirements
Create comprehensive test suite:
```python
import unittest
from unittest.mock import Mock, patch
from app.services.[service_name] import [ServiceName]

class Test[ServiceName](unittest.TestCase):
    def setUp(self):
        self.mock_dependency = Mock()
        self.service = [ServiceName](self.mock_dependency)

    def test_public_method_success(self):
        # Test successful execution
        pass

    def test_public_method_validation_error(self):
        # Test input validation
        pass

    def test_integration_with_dependencies(self):
        # Test dependency integration
        pass
```

## Deliverables Required
1. **Complete Service Implementation**
   - Full service class with all required methods
   - Comprehensive error handling and logging
   - Type hints and documentation

2. **Test Suite**
   - Unit tests with >90% coverage
   - Integration tests for dependency interaction
   - Error scenario testing

3. **Integration Updates**
   - Orchestrator integration (if needed)
   - API endpoint updates (if needed)
   - Database changes (if needed)

4. **Documentation**
   - Service documentation following template
   - Usage examples
   - Integration instructions

## Validation Checklist
- [ ] Service follows established architectural patterns
- [ ] All public methods have type hints and docstrings
- [ ] Comprehensive error handling with logging
- [ ] Input validation for all public methods
- [ ] Test coverage >90%
- [ ] Integration with orchestrator (if applicable)
- [ ] Documentation complete and accurate
```

### API Endpoint Template
```markdown
# API Endpoint Implementation: [ENDPOINT_NAME]

You are implementing a new API endpoint for the FRC GPT Scouting App following FastAPI patterns.

## Endpoint Specification
**URL**: `[HTTP_METHOD] /api/v1/[path]`
**Purpose**: [Clear description of endpoint functionality]
**Authentication**: [Required | Not Required]
**Rate Limiting**: [If applicable]

## Request/Response Contract
**Request Format**:
```json
{
  "parameter1": "type and description",
  "parameter2": "type and description"
}
```

**Response Format**:
```json
{
  "status": "success",
  "data": {
    "result_field": "description"
  },
  "metadata": {
    "processing_time": 1.23
  }
}
```

## Implementation Requirements

### 1. FastAPI Patterns
Follow established API patterns:
- Pydantic models for request/response validation
- Consistent error handling and status codes
- Proper HTTP status codes and headers
- Comprehensive OpenAPI documentation

### 2. Service Integration
- Use orchestrator service for business logic
- No direct service calls from API layer
- Proper error propagation from services
- Consistent response formatting

### 3. Validation and Security
- Input validation with Pydantic
- Error handling with proper status codes
- Rate limiting (if applicable)
- Security best practices

## Implementation Template
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import logging

from app.services.picklist_generator_service import PicklistGeneratorService
from app.models.api_models import StandardResponse, ErrorResponse

logger = logging.getLogger("api.[endpoint_name]")
router = APIRouter()

class [RequestName]Request(BaseModel):
    """Request model for [endpoint_name] endpoint."""
    parameter1: str = Field(..., description="Parameter description")
    parameter2: int = Field(..., gt=0, description="Parameter description")

class [ResponseName]Response(BaseModel):
    """Response model for [endpoint_name] endpoint."""
    result_field: str = Field(..., description="Result description")

@router.post("/[path]", response_model=StandardResponse[[ResponseName]Response])
async def [endpoint_function_name](
    request: [RequestName]Request,
    generator_service: PicklistGeneratorService = Depends(get_generator_service)
) -> StandardResponse[[ResponseName]Response]:
    """
    [Endpoint description].
    
    - **parameter1**: [Parameter description]
    - **parameter2**: [Parameter description]
    
    Returns standardized response with [result description].
    """
    try:
        logger.info(f"Processing [endpoint_name] request for {request.parameter1}")
        
        # Call service through orchestrator
        result = await generator_service.[service_method](
            parameter1=request.parameter1,
            parameter2=request.parameter2
        )
        
        # Format response
        response_data = [ResponseName]Response(
            result_field=result["field"]
        )
        
        return StandardResponse(
            status="success",
            data=response_data,
            metadata={
                "processing_time": result.get("processing_time", 0),
                "cached": result.get("cached", False)
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

## Testing Requirements
```python
from fastapi.testclient import TestClient
import pytest

def test_endpoint_success(client: TestClient):
    response = client.post("/api/v1/[path]", json={
        "parameter1": "test_value",
        "parameter2": 123
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_endpoint_validation_error(client: TestClient):
    response = client.post("/api/v1/[path]", json={
        "parameter1": "",  # Invalid
        "parameter2": -1   # Invalid
    })
    assert response.status_code == 400
```

## Deliverables Required
1. **Complete Endpoint Implementation**
2. **Pydantic Models** for request/response
3. **Comprehensive Error Handling**
4. **Test Suite** with positive and negative cases
5. **OpenAPI Documentation** updates

## Validation Checklist
- [ ] Follows FastAPI and project patterns
- [ ] Pydantic models for validation
- [ ] Proper error handling and status codes
- [ ] Service integration through orchestrator
- [ ] Comprehensive test coverage
- [ ] OpenAPI documentation updated
```

---

## Testing Prompt Templates

### Comprehensive Test Suite Template
```markdown
# Test Implementation: [COMPONENT_NAME]

You are creating comprehensive tests for [component_type] in the FRC GPT Scouting App.

## Testing Requirements

### 1. Test Coverage Goals
- **Unit Tests**: >90% line coverage for new code
- **Integration Tests**: All service interactions
- **Error Scenarios**: All exception paths
- **Edge Cases**: Boundary conditions and unusual inputs

### 2. Testing Patterns
- **AAA Pattern**: Arrange, Act, Assert structure
- **Mock Strategy**: Mock external dependencies appropriately
- **Test Data**: Use consistent, realistic test data
- **Isolation**: Tests must be independent and repeatable

### 3. Test Categories Required

#### Unit Tests
- Test all public methods with valid inputs
- Test input validation and error handling
- Test edge cases and boundary conditions
- Test internal logic with mocked dependencies

#### Integration Tests
- Test service integration with orchestrator
- Test API endpoint integration
- Test database operations (if applicable)
- Test external service calls (mocked)

#### Error Scenario Tests
- Test all exception handling paths
- Test timeout and retry scenarios
- Test invalid input handling
- Test resource unavailability scenarios

## Implementation Template
```python
import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
from app.services.[component_name] import [ComponentName]
from app.exceptions import ServiceError, ValidationError

class Test[ComponentName](unittest.TestCase):
    """Comprehensive test suite for [ComponentName]."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_dependency = Mock()
        
        # Initialize component
        self.component = [ComponentName](self.mock_dependency)
        
        # Test data
        self.valid_input = [valid_test_data]
        self.invalid_input = [invalid_test_data]
        self.expected_output = [expected_result]

    def test_[method_name]_success(self):
        """Test successful execution of [method_name]."""
        # Arrange
        input_data = self.valid_input
        expected_result = self.expected_output
        
        # Act
        result = self.component.[method_name](input_data)
        
        # Assert
        self.assertEqual(result, expected_result)
        self.mock_dependency.assert_called_once()

    def test_[method_name]_validation_error(self):
        """Test input validation error handling."""
        # Arrange
        invalid_input = self.invalid_input
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.component.[method_name](invalid_input)
        
        self.assertIn("Invalid", str(context.exception))

    def test_[method_name]_service_error(self):
        """Test service error handling."""
        # Arrange
        self.mock_dependency.side_effect = Exception("Dependency failure")
        
        # Act & Assert
        with self.assertRaises(ServiceError):
            self.component.[method_name](self.valid_input)

    def test_[method_name]_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test empty input
        result = self.component.[method_name]([])
        self.assertEqual(result, [])
        
        # Test single item
        result = self.component.[method_name]([single_item])
        self.assertIsNotNone(result)
        
        # Test large input
        large_input = [create_large_test_data()]
        result = self.component.[method_name](large_input)
        self.assertIsNotNone(result)

    @patch('app.services.[component_name].external_dependency')
    def test_external_integration(self, mock_external):
        """Test integration with external dependencies."""
        # Configure mock
        mock_external.return_value = "mocked_response"
        
        # Test
        result = self.component.[method_name](self.valid_input)
        
        # Verify
        mock_external.assert_called_once()
        self.assertIsNotNone(result)

    def test_performance_requirements(self):
        """Test performance requirements are met."""
        import time
        
        start_time = time.time()
        result = self.component.[method_name](self.valid_input)
        execution_time = time.time() - start_time
        
        # Verify performance requirement
        self.assertLess(execution_time, 0.1)  # 100ms requirement
        self.assertIsNotNone(result)

class Test[ComponentName]Integration(unittest.TestCase):
    """Integration tests for [ComponentName]."""

    def setUp(self):
        """Set up integration test environment."""
        # Set up real dependencies for integration testing
        pass

    def test_integration_with_orchestrator(self):
        """Test integration with main orchestrator."""
        # Test real integration scenario
        pass

    def test_end_to_end_workflow(self):
        """Test complete workflow integration."""
        # Test full workflow that uses this component
        pass

if __name__ == '__main__':
    # Run unit tests
    unittest.main()
```

## Test Data Patterns
```python
# Standard test data patterns
def create_test_team_data():
    """Create realistic test team data."""
    return {
        "team_number": 1234,
        "nickname": "Test Team",
        "autonomous_score": 15.5,
        "teleop_avg_points": 48.2,
        "endgame_points": 12.0,
        "defense_rating": 3.8,
        "reliability_score": 0.87
    }

def create_test_priorities():
    """Create realistic test priorities."""
    return [
        {"metric": "autonomous_score", "weight": 0.3},
        {"metric": "teleop_avg_points", "weight": 0.4},
        {"metric": "endgame_points", "weight": 0.2},
        {"metric": "defense_rating", "weight": 0.1}
    ]
```

## Validation Requirements
- [ ] All public methods tested
- [ ] Error scenarios covered
- [ ] Edge cases tested
- [ ] Integration points validated
- [ ] Performance requirements verified
- [ ] Test data is realistic and consistent
- [ ] Mocks used appropriately
- [ ] Tests are independent and repeatable
```

---

## Documentation Prompt Templates

### Service Documentation Template
```markdown
# Service Documentation: [SERVICE_NAME]

You are generating comprehensive documentation for [SERVICE_NAME] in the FRC GPT Scouting App.

## Documentation Requirements

### 1. Service Overview
- Clear purpose and responsibility statement
- Integration context within the system
- Dependencies and relationships
- Key features and capabilities

### 2. Technical Specifications
- Complete API documentation with examples
- Data contracts and formats
- Error handling patterns
- Performance characteristics

### 3. Usage Guidance
- Practical examples that work
- Integration instructions
- Common patterns and best practices
- Troubleshooting information

## Documentation Template
```markdown
# [ServiceName] Documentation

## Overview
**Purpose**: [Clear statement of service responsibility]  
**Layer**: [Data Layer | Analysis Layer | AI Layer]  
**File**: `backend/app/services/[service_name].py`  
**Created**: [Date] as part of [context]  

### Responsibilities
- [Primary responsibility 1]
- [Primary responsibility 2]
- [Primary responsibility 3]

### Integration Context
This service integrates with the FRC GPT Scouting App architecture by:
- [Integration point 1]
- [Integration point 2]
- [Integration point 3]

## Service Contract

### Constructor
```python
def __init__(self, dependencies):
    """
    Initialize [ServiceName] with required dependencies.
    
    Args:
        dependencies: [Description of required dependencies]
        
    Raises:
        ValueError: [When initialization fails]
    """
```

### Public Methods
[For each public method, include:]

```python
def method_name(self, param: Type) -> ReturnType:
    """
    [Method description and purpose].
    
    Args:
        param: [Parameter description with type and constraints]
        
    Returns:
        [Return value description with type and format]
        
    Raises:
        ValueError: [When this exception is raised]
        ServiceError: [When service errors occur]
        
    Example:
        >>> service = [ServiceName](dependencies)
        >>> result = service.method_name(value)
        >>> print(result)
        [Expected output]
    """
```

## Implementation Details

### Key Algorithms
- **[Algorithm 1]**: [Description and purpose]
- **[Algorithm 2]**: [Description and purpose]

### Data Structures
- **[Structure 1]**: [Description and usage]
- **[Structure 2]**: [Description and usage]

### Error Handling
- **[Error Type 1]**: [How it's handled]
- **[Error Type 2]**: [How it's handled]

## Integration Points

### Dependencies
- **Internal**: [List internal dependencies]
- **External**: [List external libraries]
- **Services**: [List service dependencies]

### Data Sources
- **[Source 1]**: [Description and format]
- **[Source 2]**: [Description and format]

### Output Consumers
- **[Consumer 1]**: [What they expect]
- **[Consumer 2]**: [What they expect]

## Usage Examples

### Basic Usage
```python
# Initialize service
service = [ServiceName](dependencies)

# Basic operation
result = service.basic_operation(data)
print(f"Result: {result}")
```

### Advanced Usage
```python
# Complex workflow example
try:
    # Set up complex parameters
    complex_params = {
        "parameter1": value1,
        "parameter2": value2
    }
    
    # Execute complex operation
    result = service.complex_operation(**complex_params)
    
    # Process results
    if result.get("status") == "success":
        data = result["data"]
        process_data(data)
    else:
        handle_error(result.get("error"))
        
except ServiceError as e:
    logger.error(f"Service error: {str(e)}")
    handle_service_error(e)
except ValueError as e:
    logger.error(f"Validation error: {str(e)}")
    handle_validation_error(e)
```

### Integration with Orchestrator
```python
# How this service integrates with PicklistGeneratorService
class PicklistGeneratorService:
    def __init__(self, dataset_path: str):
        # Initialize this service
        self.[service_instance] = [ServiceName](dependencies)
    
    def workflow_method(self):
        # Use service in workflow
        result = self.[service_instance].method_name(parameters)
        return self.process_result(result)
```

## Testing

### Unit Tests
- **Location**: `tests/test_[service_name].py`
- **Coverage**: [X]% of code lines
- **Key Test Cases**:
  - [Test case 1 description]
  - [Test case 2 description]
  - [Test case 3 description]

### Integration Tests
- **Location**: `tests/test_services_integration.py`
- **Integration Points Tested**:
  - [Integration point 1]
  - [Integration point 2]

### Running Tests
```bash
# Run unit tests
pytest tests/test_[service_name].py -v

# Run integration tests
pytest tests/test_services_integration.py -k [service_name] -v

# Run with coverage
pytest tests/test_[service_name].py --cov=app.services.[service_name] --cov-report=html
```

## Performance Characteristics

### Benchmarks
- **[Operation 1]**: [Performance metrics and targets]
- **[Operation 2]**: [Performance metrics and targets]

### Optimization Notes
- **[Optimization 1]**: [Description and impact]
- **[Optimization 2]**: [Description and impact]

### Resource Usage
- **Memory**: [Typical memory usage patterns]
- **CPU**: [CPU usage characteristics]
- **I/O**: [File system or network usage]

## Troubleshooting

### Common Issues
- **[Issue 1]**: [Description and solution]
- **[Issue 2]**: [Description and solution]

### Debugging
- **Log Levels**: [What to look for in logs]
- **Common Error Messages**: [Error message meanings]
- **Debug Mode**: [How to enable detailed debugging]

### Monitoring
- **Health Indicators**: [What to monitor for health]
- **Performance Metrics**: [Key performance indicators]
- **Alert Conditions**: [When to alert]

## Maintenance Notes

### Update Procedures
- **[Procedure 1]**: [When and how to update]
- **[Procedure 2]**: [Update process]

### Configuration Management
- **[Config 1]**: [Configuration parameter and usage]
- **[Config 2]**: [Configuration parameter and usage]

### Version History
- **[Date]**: [Change description] - [Author]
- **[Date]**: [Change description] - [Author]

---
**Last Updated**: [Date]  
**Maintainer**: [Name/Role]  
**Related Documents**: [Links to related documentation]
```

## Validation Requirements
- [ ] All public methods documented with examples
- [ ] Integration instructions are clear and complete
- [ ] Examples can be executed successfully
- [ ] Error scenarios are documented
- [ ] Performance characteristics are specified
- [ ] Troubleshooting information is practical
- [ ] Cross-references to related docs are accurate
```

---

## Debugging Prompt Templates

### Bug Investigation Template
```markdown
# Bug Investigation: [BUG_DESCRIPTION]

You are investigating and fixing a bug in the FRC GPT Scouting App.

## Bug Information
**Description**: [Brief description of the bug]
**Symptoms**: [What the user observes]
**Expected Behavior**: [What should happen]
**Actual Behavior**: [What actually happens]

**Error Information**:
```
[Stack trace, error messages, or failure logs]
```

**Reproduction Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Observe error]

## Investigation Approach

### 1. Error Analysis
- Analyze stack trace and error messages
- Identify the failing component/service
- Determine the root cause category
- Check for related issues in logs

### 2. Code Analysis
- Review relevant service code
- Check integration points
- Examine error handling patterns
- Look for recent changes that might be related

### 3. Data Analysis
- Validate input data format
- Check for edge cases or boundary conditions
- Verify data consistency
- Test with different data sets

### 4. Environment Analysis
- Check configuration settings
- Verify dependencies and versions
- Test in different environments
- Check resource availability

## Investigation Template
```python
# Bug investigation checklist
investigation_steps = {
    "error_analysis": {
        "stack_trace_review": "[Analysis of stack trace]",
        "error_message_meaning": "[What the error indicates]", 
        "failure_location": "[Exact location of failure]",
        "error_category": "[Type of error - validation, service, integration, etc.]"
    },
    
    "code_review": {
        "failing_method": "[Method/function where error occurs]",
        "input_validation": "[How inputs are validated]",
        "error_handling": "[Current error handling approach]",
        "recent_changes": "[Any recent modifications]"
    },
    
    "data_analysis": {
        "input_format": "[Format of input data when error occurs]",
        "edge_cases": "[Any unusual data conditions]",
        "data_validation": "[Data validation results]",
        "test_scenarios": "[Different data scenarios tested]"
    },
    
    "environment_check": {
        "configuration": "[Relevant configuration settings]",
        "dependencies": "[Dependency versions and status]",
        "resources": "[Memory, disk, network status]",
        "logs": "[Relevant log entries]"
    }
}
```

## Root Cause Analysis
Based on investigation, determine:
- **Primary Cause**: [Main reason for the bug]
- **Contributing Factors**: [Secondary factors]
- **Scope**: [How widespread the issue is]
- **Impact**: [Who/what is affected]

## Fix Implementation

### 1. Fix Strategy
- **Approach**: [How to fix the root cause]
- **Scope**: [What code needs to change]
- **Risk Assessment**: [Potential impact of the fix]
- **Testing Strategy**: [How to verify the fix]

### 2. Implementation Requirements
- Follow existing error handling patterns
- Add appropriate logging for debugging
- Include input validation if missing
- Maintain backward compatibility
- Add regression tests

### 3. Fix Template
```python
# Before (problematic code)
def problematic_method(self, param):
    # Original implementation with bug
    result = process_data(param)  # Bug: no validation or error handling
    return result

# After (fixed code)
def fixed_method(self, param):
    """
    Fixed method with proper validation and error handling.
    
    Args:
        param: [Parameter description with validation requirements]
        
    Returns:
        [Return description]
        
    Raises:
        ValueError: [When validation fails]
        ServiceError: [When processing fails]
    """
    try:
        # Add input validation
        if not self._validate_input(param):
            raise ValueError(f"Invalid parameter: {param}")
        
        # Process with error handling
        result = process_data(param)
        
        # Add success logging
        logger.info(f"Successfully processed parameter: {param}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in {self.__class__.__name__}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Processing error in {self.__class__.__name__}: {str(e)}")
        raise ServiceError(f"Failed to process data: {str(e)}")

def _validate_input(self, param):
    """Validate input parameter."""
    # Add specific validation logic
    return param is not None and isinstance(param, expected_type)
```

## Testing Requirements

### 1. Regression Test
Create specific test for this bug:
```python
def test_bug_fix_[bug_id](self):
    """Test that specific bug [bug_id] is fixed."""
    # Arrange - set up conditions that caused the bug
    problematic_input = [input_that_caused_bug]
    
    # Act - execute the fixed code
    result = self.service.fixed_method(problematic_input)
    
    # Assert - verify bug is fixed
    self.assertIsNotNone(result)
    self.assertEqual(result.status, "success")
```

### 2. Edge Case Tests
Add tests for related edge cases:
```python
def test_edge_cases_related_to_bug(self):
    """Test edge cases related to the bug fix."""
    # Test boundary conditions
    # Test unusual input formats  
    # Test error scenarios
    pass
```

### 3. Integration Testing
Verify fix doesn't break other functionality:
```python
def test_integration_after_bug_fix(self):
    """Ensure bug fix doesn't break integration."""
    # Test full workflow
    # Test service interactions
    # Test API endpoints (if affected)
    pass
```

## Deliverables Required
1. **Root Cause Analysis**: Detailed explanation of why the bug occurred
2. **Fix Implementation**: Complete code fix following established patterns
3. **Regression Tests**: Tests that prevent this bug from recurring
4. **Validation**: Proof that fix works and doesn't break other functionality
5. **Documentation**: Update relevant documentation if behavior changes

## Validation Checklist
- [ ] Root cause clearly identified and documented
- [ ] Fix addresses the actual cause (not just symptoms)
- [ ] Fix follows established coding patterns
- [ ] Comprehensive error handling added
- [ ] Regression test prevents future occurrences
- [ ] Integration testing confirms no breaking changes
- [ ] Documentation updated if necessary
- [ ] All existing tests still pass
```

---

## Review Prompt Templates

### Code Review Template
```markdown
# Code Review: [COMPONENT_NAME]

You are performing a comprehensive code review for [COMPONENT_NAME] in the FRC GPT Scouting App.

## Code Under Review
```[language]
[Code to be reviewed]
```

## Review Criteria

### 1. Architecture Compliance
- **Service Patterns**: Does code follow established service architecture?
- **Integration**: Proper integration with orchestrator and other services?
- **Boundaries**: Clear service boundaries maintained?
- **Dependencies**: Appropriate dependency management?

### 2. Code Quality
- **Standards Compliance**: Follows coding standards in CODING_STANDARDS.md?
- **Type Safety**: Comprehensive type hints used?
- **Documentation**: Clear docstrings with examples?
- **Naming**: Consistent and descriptive naming conventions?

### 3. Error Handling
- **Exception Handling**: Comprehensive try/catch blocks?
- **Error Types**: Appropriate exception types used?
- **Logging**: Proper logging levels and messages?
- **Recovery**: Graceful error recovery where possible?

### 4. Testing
- **Test Coverage**: Adequate test coverage (>90%)?
- **Test Quality**: Tests follow AAA pattern and best practices?
- **Edge Cases**: Boundary conditions and edge cases tested?
- **Integration**: Integration points properly tested?

### 5. Performance
- **Efficiency**: Algorithms and data structures efficient?
- **Resource Usage**: Appropriate memory and CPU usage?
- **Caching**: Caching used where beneficial?
- **Scalability**: Code scales with increased load?

### 6. Security
- **Input Validation**: All inputs properly validated?
- **Data Protection**: Sensitive data handled securely?
- **Dependencies**: No security vulnerabilities in dependencies?
- **Best Practices**: Security best practices followed?

## Review Template
```yaml
review_summary:
  overall_assessment: [excellent|good|needs_improvement|poor]
  approval_status: [approved|approved_with_changes|requires_changes|rejected]
  
architecture_review:
  service_pattern_compliance: [compliant|minor_issues|major_issues]
  integration_quality: [excellent|good|needs_improvement]
  dependency_management: [appropriate|issues_found]
  
code_quality:
  standards_compliance: [full|partial|non_compliant]
  type_safety: [comprehensive|adequate|insufficient]
  documentation_quality: [excellent|good|needs_improvement]
  naming_conventions: [consistent|mostly_consistent|inconsistent]
  
error_handling:
  exception_handling: [comprehensive|adequate|insufficient]
  logging_quality: [excellent|good|needs_improvement]
  error_recovery: [robust|adequate|insufficient]
  
testing_assessment:
  coverage_level: [>90%|70-90%|<70%]
  test_quality: [excellent|good|needs_improvement]
  edge_case_coverage: [comprehensive|adequate|insufficient]
  
performance_review:
  algorithm_efficiency: [optimal|good|needs_improvement]
  resource_usage: [efficient|acceptable|concerning]
  scalability: [excellent|good|limited]
  
security_assessment:
  input_validation: [comprehensive|adequate|insufficient]
  data_protection: [secure|mostly_secure|vulnerabilities_found]
  best_practices: [followed|mostly_followed|not_followed]
```

## Detailed Feedback

### Issues Found
For each issue:
- **Severity**: [Critical|High|Medium|Low]
- **Category**: [Architecture|Quality|Security|Performance|Testing]
- **Description**: [Clear description of the issue]
- **Location**: [File and line number if applicable]
- **Recommendation**: [Specific action to address the issue]

### Positive Observations
- [Good practice 1]
- [Good practice 2]
- [Good practice 3]

### Improvement Suggestions
- [Suggestion 1]: [How to improve]
- [Suggestion 2]: [How to improve]
- [Suggestion 3]: [How to improve]

## Action Items
- [ ] [Required change 1]
- [ ] [Required change 2]
- [ ] [Recommended improvement 1]
- [ ] [Recommended improvement 2]

## Approval Decision
**Status**: [Approved|Approved with Changes|Requires Changes|Rejected]
**Rationale**: [Explanation of decision]
**Next Steps**: [What needs to happen next]
```

---

## Validation and Testing

### Template Validation
Each prompt template has been validated for:
- **Clarity**: Clear instructions and expectations
- **Completeness**: All necessary information included
- **Consistency**: Follows established patterns
- **Effectiveness**: Produces high-quality results

### Usage Guidelines
1. **Customize Templates**: Adapt templates to specific use cases
2. **Provide Context**: Include relevant project context
3. **Set Clear Expectations**: Define success criteria
4. **Validate Results**: Review AI output against requirements

---

**Next Steps**: [AI Development Guide](AI_DEVELOPMENT_GUIDE.md) | [Service Contracts](SERVICE_CONTRACTS.md) | [Service Architecture](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)

---

**Last Updated**: June 25, 2025  
**Maintainer**: AI Framework Team  
**Related Documents**: [AI Development Guide](AI_DEVELOPMENT_GUIDE.md), [Service Contracts](SERVICE_CONTRACTS.md), [Coding Standards](../04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md)