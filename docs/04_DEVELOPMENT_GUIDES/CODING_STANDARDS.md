# Coding Standards

**Purpose**: Code quality and consistency standards for all development  
**Audience**: Developers and AI assistants  
**Scope**: Python backend, TypeScript frontend, and documentation standards  

---

## Overview

The FRC GPT Scouting App follows strict coding standards to ensure maintainable, readable, and consistent code across all components. These standards are designed for both human developers and AI assistants like Claude Code.

### Guiding Principles
- **Consistency**: Code should look like it was written by a single person
- **Readability**: Code should be self-documenting and easy to understand
- **Maintainability**: Code should be easy to modify and extend
- **Quality**: Code should be robust, tested, and error-free
- **AI-Friendly**: Patterns should be clear for AI assistants to follow

---

## Python Backend Standards

### Code Style and Formatting

**PEP 8 Compliance with Modifications**:
- **Line Length**: 100 characters maximum (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Encoding**: UTF-8
- **Imports**: One import per line, grouped and sorted

**Formatting Tools**:
```bash
# Format code with Black
black app/ tests/ --line-length 100

# Sort imports with isort
isort app/ tests/ --profile black

# Check formatting
flake8 app/ tests/ --max-line-length=100
```

### Naming Conventions

**Variables and Functions**:
```python
# Use snake_case for variables and functions
team_analysis_result = analyze_teams(team_data)
user_input_validation = validate_user_input(request_data)

# Use descriptive names
def calculate_weighted_team_score(team_data: Dict[str, Any], priorities: List[Dict[str, Any]]) -> float:
    """Calculate weighted score for a team based on priorities."""
    pass

# Avoid abbreviations and single letters (except for loops)
for team in teams_list:  # Good
for t in teams_list:     # Avoid
```

**Classes**:
```python
# Use PascalCase for class names
class DataAggregationService:
    """Service for data aggregation and preparation."""
    pass

class TeamAnalysisService:
    """Service for team evaluation and ranking."""
    pass
```

**Constants**:
```python
# Use UPPER_SNAKE_CASE for constants
DEFAULT_BATCH_SIZE = 20
MAX_TEAMS_PER_ANALYSIS = 500
API_TIMEOUT_SECONDS = 30

# Group related constants
class CacheConfig:
    DEFAULT_TTL = 3600
    MAX_CACHE_SIZE = 1000
    CLEANUP_INTERVAL = 300
```

**Private Methods**:
```python
class ServiceExample:
    def public_method(self):
        """Public method accessible to other services."""
        return self._private_helper()
    
    def _private_helper(self):
        """Private method for internal use only."""
        pass
```

### Type Hints

**Comprehensive Type Hints Required**:
```python
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path

# All function parameters and return values must have type hints
def process_team_data(
    teams: List[Dict[str, Any]], 
    priorities: List[Dict[str, float]], 
    exclude_teams: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Process team data with given priorities."""
    pass

# Class attributes should have type hints
class DataService:
    dataset_path: Path
    teams_cache: Dict[int, Dict[str, Any]]
    last_updated: Optional[datetime]
    
    def __init__(self, dataset_path: str) -> None:
        self.dataset_path = Path(dataset_path)
        self.teams_cache = {}
        self.last_updated = None
```

**Complex Types**:
```python
from typing import TypedDict, Protocol

# Use TypedDict for structured dictionaries
class TeamData(TypedDict):
    team_number: int
    nickname: str
    autonomous_score: float
    teleop_avg_points: float
    endgame_points: float

# Use Protocol for interface definitions
class AnalysisService(Protocol):
    def analyze_teams(self, teams: List[TeamData]) -> List[Dict[str, Any]]:
        ...
```

### Documentation Standards

**Docstring Format**:
```python
def normalize_priorities(self, priorities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize priority weights to sum to 1.0.
    
    Takes a list of priority dictionaries and ensures the weights
    sum to 1.0 while preserving relative ratios. Adds metadata
    for tracking original weights and descriptions.
    
    Args:
        priorities: List of priority dictionaries with 'metric' and 'weight' keys.
                   Each priority must have a positive weight value.
    
    Returns:
        List of normalized priority dictionaries with structure:
        {
            "metric": str,
            "weight": float,  # normalized to sum to 1.0
            "original_weight": float,
            "description": str
        }
    
    Raises:
        ValueError: If all weights are zero or negative, or if priorities is empty.
        TypeError: If priorities is not a list or contains invalid types.
    
    Example:
        >>> service = PriorityCalculationService()
        >>> priorities = [
        ...     {"metric": "autonomous_score", "weight": 3},
        ...     {"metric": "teleop_avg_points", "weight": 7}
        ... ]
        >>> result = service.normalize_priorities(priorities)
        >>> print(result[0]["weight"])
        0.3
        >>> print(result[1]["weight"])
        0.7
    
    Note:
        The normalization preserves relative weight ratios while ensuring
        the sum equals 1.0 within floating-point precision (±0.001).
    """
    pass
```

**Class Documentation**:
```python
class DataAggregationService:
    """
    Service for unified data loading and preparation.
    
    This service handles loading team data from various sources,
    validating data integrity, and preparing clean datasets for
    analysis by other services in the system.
    
    The service maintains an internal cache of loaded data and
    provides filtered views based on analysis requirements.
    
    Thread Safety:
        This service is not thread-safe. Use separate instances
        for concurrent operations.
    
    Performance:
        Data is loaded once during initialization and cached
        for subsequent operations. Filtering operations are
        optimized for O(n) performance.
    
    Example:
        >>> service = DataAggregationService("path/to/dataset.json")
        >>> teams = service.get_teams_for_analysis(exclude_teams=[1234])
        >>> context = service.load_game_context()
    """
    pass
```

### Error Handling Patterns

**Consistent Error Handling**:
```python
import logging

logger = logging.getLogger(__name__)

def service_method(self, param: str) -> Dict[str, Any]:
    """Example of proper error handling pattern."""
    try:
        # Input validation first
        if not param or not isinstance(param, str):
            raise ValueError(f"Invalid parameter: {param}")
        
        # Main processing logic
        result = self._process_parameter(param)
        
        # Success logging
        logger.info(f"Successfully processed parameter: {param}")
        return result
        
    except ValueError as e:
        # Log validation errors at ERROR level
        logger.error(f"Validation error in {self.__class__.__name__}.service_method: {str(e)}")
        raise  # Re-raise validation errors
        
    except FileNotFoundError as e:
        # Log file access errors
        logger.error(f"File access error: {str(e)}")
        raise ServiceError(f"Required file not found: {str(e)}")
        
    except Exception as e:
        # Log unexpected errors with full context
        logger.error(
            f"Unexpected error in {self.__class__.__name__}.service_method: {str(e)}",
            exc_info=True
        )
        raise ServiceError(f"Service operation failed: {str(e)}")
```

**Custom Exception Classes**:
```python
class ServiceError(Exception):
    """Base exception for service-specific errors."""
    pass

class ValidationError(ServiceError):
    """Raised when input validation fails."""
    pass

class DataProcessingError(ServiceError):
    """Raised when data processing operations fail."""
    pass

class IntegrationError(ServiceError):
    """Raised when service integration fails."""
    pass
```

### Logging Standards

**Logger Configuration**:
```python
import logging

# Use module-level logger
logger = logging.getLogger(__name__)

# For services, use descriptive logger names
logger = logging.getLogger("services.data_aggregation")
logger = logging.getLogger("services.team_analysis")
```

**Logging Levels**:
```python
# INFO: Normal operations, successful processing
logger.info("Initialized DataAggregationService with 45 teams")
logger.info("Successfully processed picklist generation for team 1234")

# WARNING: Degraded performance, missing optional data
logger.warning("Team 5678 missing defense_rating field, using default")
logger.warning("Cache hit rate below 80%: 65%")

# ERROR: Operation failures, exceptions
logger.error("Failed to load dataset: file not found")
logger.error("OpenAI API call failed after 3 retries")

# DEBUG: Detailed debugging information (development only)
logger.debug(f"Processing batch {batch_idx} with {len(teams)} teams")
logger.debug(f"Cache key generated: {cache_key}")
```

### Service Architecture Patterns

**Service Class Structure**:
```python
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("services.example")

class ExampleService:
    """
    Service following established architectural patterns.
    
    This template shows the standard structure for all services
    in the FRC GPT Scouting App architecture.
    """
    
    def __init__(self, dependencies: Any) -> None:
        """
        Initialize service with required dependencies.
        
        Args:
            dependencies: Required dependencies for service operation
        """
        self.dependencies = dependencies
        self._internal_cache: Dict[str, Any] = {}
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def public_method(self, param: str) -> Dict[str, Any]:
        """
        Public method following established patterns.
        
        All public methods must:
        - Have comprehensive type hints
        - Include detailed docstrings with examples
        - Implement proper error handling
        - Include appropriate logging
        - Validate all inputs
        
        Args:
            param: Parameter description
            
        Returns:
            Result dictionary with standardized format
            
        Raises:
            ValueError: Input validation failed
            ServiceError: Service operation failed
        """
        try:
            # Always validate inputs first
            self._validate_input(param)
            
            # Process using private methods
            result = self._process_data(param)
            
            # Log successful operations
            logger.info(f"Successfully processed {param}")
            
            return {
                "status": "success",
                "data": result,
                "metadata": {
                    "processing_time": 0.0,
                    "cached": False
                }
            }
            
        except ValueError as e:
            logger.error(f"Input validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Service operation failed: {str(e)}")
            raise ServiceError(f"Failed to process {param}: {str(e)}")
    
    def _validate_input(self, param: str) -> None:
        """Private method for input validation."""
        if not param:
            raise ValueError("Parameter cannot be empty")
        if not isinstance(param, str):
            raise ValueError(f"Parameter must be string, got {type(param)}")
    
    def _process_data(self, param: str) -> Any:
        """Private method for data processing."""
        # Implementation details
        pass
```

### Testing Integration

**Test File Organization**:
```python
# tests/test_services/test_data_aggregation_service.py
import unittest
from unittest.mock import Mock, patch
from app.services.data_aggregation_service import DataAggregationService
from app.exceptions import ServiceError, ValidationError

class TestDataAggregationService(unittest.TestCase):
    """Test suite following established testing patterns."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_dataset_path = "tests/fixtures/test_dataset.json"
        self.service = DataAggregationService(self.test_dataset_path)
        
        # Standard test data
        self.valid_team_data = {
            "team_number": 1234,
            "nickname": "Test Team",
            "autonomous_score": 15.5
        }
    
    def test_method_success(self) -> None:
        """Test successful method execution."""
        # Arrange
        input_data = "valid_input"
        
        # Act
        result = self.service.public_method(input_data)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
    
    def test_method_validation_error(self) -> None:
        """Test input validation error handling."""
        # Arrange
        invalid_input = ""
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.service.public_method(invalid_input)
```

---

## TypeScript Frontend Standards

### Code Style and Formatting

**Prettier Configuration**:
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

**ESLint Configuration**:
```json
{
  "extends": [
    "react-app",
    "react-app/jest",
    "@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "prefer-const": "error"
  }
}
```

### TypeScript Patterns

**Component Structure**:
```typescript
import React from 'react';

// Define props interface
interface TeamCardProps {
  team: TeamData;
  onSelect: (teamNumber: number) => void;
  isSelected: boolean;
  showDetails?: boolean;
}

// Define component with explicit return type
export const TeamCard: React.FC<TeamCardProps> = ({
  team,
  onSelect,
  isSelected,
  showDetails = false,
}) => {
  // Event handlers with proper typing
  const handleClick = (): void => {
    onSelect(team.team_number);
  };

  // Render with consistent structure
  return (
    <div 
      className={`team-card ${isSelected ? 'selected' : ''}`}
      onClick={handleClick}
    >
      <h3>{team.nickname}</h3>
      <p>Team #{team.team_number}</p>
      {showDetails && (
        <div className="team-details">
          <p>Autonomous: {team.autonomous_score}</p>
          <p>Teleop: {team.teleop_avg_points}</p>
        </div>
      )}
    </div>
  );
};
```

**Type Definitions**:
```typescript
// Define data interfaces
export interface TeamData {
  team_number: number;
  nickname: string;
  autonomous_score: number;
  teleop_avg_points: number;
  endgame_points: number;
  defense_rating: number;
  reliability_score: number;
}

export interface Priority {
  metric: string;
  weight: number;
  description?: string;
}

export interface PicklistRequest {
  your_team_number: number;
  pick_position: 'first' | 'second' | 'third';
  priorities: Priority[];
  exclude_teams?: number[];
}

// API response types
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  metadata?: {
    processing_time: number;
    cached: boolean;
  };
}
```

**API Service Pattern**:
```typescript
class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  async generatePicklist(request: PicklistRequest): Promise<PicklistResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/picklist/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<PicklistResponse> = await response.json();
      
      if (data.status === 'error') {
        throw new Error(data.error || 'API request failed');
      }

      return data.data!;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();
```

### React Patterns

**Hooks Usage**:
```typescript
import React, { useState, useEffect, useCallback, useMemo } from 'react';

export const PicklistGenerator: React.FC = () => {
  // State with proper typing
  const [teams, setTeams] = useState<TeamData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Memoized calculations
  const filteredTeams = useMemo(() => {
    return teams.filter(team => team.autonomous_score > 10);
  }, [teams]);

  // Callback functions
  const handleTeamSelect = useCallback((teamNumber: number) => {
    console.log(`Selected team: ${teamNumber}`);
  }, []);

  // Effects
  useEffect(() => {
    const loadTeams = async (): Promise<void> => {
      try {
        setLoading(true);
        const data = await apiService.getTeams();
        setTeams(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load teams');
      } finally {
        setLoading(false);
      }
    };

    loadTeams();
  }, []);

  return (
    <div className="picklist-generator">
      {/* Component JSX */}
    </div>
  );
};
```

---

## Documentation Standards

### Markdown Formatting

**Document Structure**:
```markdown
# Document Title

**Purpose**: Brief description of document purpose  
**Audience**: Who should read this document  
**Scope**: What is and isn't covered  

---

## Section Headings

Use hierarchical headings with clear structure:
- # H1 for document title only
- ## H2 for major sections
- ### H3 for subsections
- #### H4 for detailed subsections (rarely needed)

### Code Examples

All code examples must be:
- Properly formatted with syntax highlighting
- Executable without modification
- Include necessary imports and context
- Follow the coding standards defined here

```python
# Good example - complete and executable
from typing import List, Dict, Any

def example_function(teams: List[Dict[str, Any]]) -> bool:
    """Example function with proper documentation."""
    return len(teams) > 0
```

### Cross-References

Link to related documents using relative paths:
- [Service Architecture](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)
- [API Contracts](../03_ARCHITECTURE/API_CONTRACTS.md)
- [Development Environment](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md)
```

**Document Metadata**:
```markdown
---
**Last Updated**: June 25, 2025  
**Maintainer**: Development Team  
**Related Documents**: [Link1](path1.md), [Link2](path2.md)
```

---

## Quality Assurance

### Automated Quality Checks

**Python Quality Pipeline**:
```bash
# Code formatting
black app/ tests/ --line-length 100 --check

# Import sorting
isort app/ tests/ --profile black --check-only

# Linting
flake8 app/ tests/ --max-line-length=100

# Type checking
mypy app/ --strict

# Security scanning
bandit -r app/

# Test coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=90
```

**TypeScript Quality Pipeline**:
```bash
# Type checking
tsc --noEmit

# Linting
eslint src/ --ext .ts,.tsx

# Formatting check
prettier --check src/

# Testing
npm test -- --coverage --watchAll=false
```

### Code Review Checklist

**For All Code**:
- [ ] Follows naming conventions
- [ ] Has comprehensive type hints/types
- [ ] Includes proper error handling
- [ ] Has appropriate logging
- [ ] Includes unit tests with >90% coverage
- [ ] Documentation is complete and accurate

**For Python Code**:
- [ ] Follows PEP 8 with 100-character line limit
- [ ] Has docstrings for all public methods
- [ ] Uses appropriate exception types
- [ ] Implements proper input validation
- [ ] Follows service architecture patterns

**For TypeScript Code**:
- [ ] Uses strict TypeScript configuration
- [ ] Has proper interface definitions
- [ ] Implements error boundaries where appropriate
- [ ] Follows React best practices
- [ ] Uses appropriate state management

**For Documentation**:
- [ ] Follows markdown formatting standards
- [ ] Includes working code examples
- [ ] Has accurate cross-references
- [ ] Is up-to-date with current implementation

---

## AI Assistant Integration

### Claude Code Standards

**Service Creation Pattern for AI**:
```python
# Template for AI assistants creating new services
class NewServiceTemplate:
    """
    Template service following all established patterns.
    
    AI assistants must use this exact structure when creating services.
    """
    
    def __init__(self, dependencies) -> None:
        """Initialize with comprehensive logging and validation."""
        # Validate dependencies
        # Set up internal state
        # Log initialization
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def public_method(self, param: TypeHint) -> ReturnType:
        """
        Public method template with all required elements.
        
        Must include:
        - Comprehensive docstring with examples
        - Type hints for all parameters and return
        - Input validation
        - Error handling with logging
        - Success logging
        
        Args:
            param: Description with type and constraints
            
        Returns:
            Description of return value and format
            
        Raises:
            ValueError: When validation fails
            ServiceError: When processing fails
            
        Example:
            >>> service = NewServiceTemplate(deps)
            >>> result = service.public_method("test")
            >>> print(result["status"])
            success
        """
        try:
            # 1. Input validation
            self._validate_input(param)
            
            # 2. Processing with error handling
            result = self._process_input(param)
            
            # 3. Success logging
            logger.info(f"Successfully processed: {param}")
            
            return result
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            raise ServiceError(f"Operation failed: {str(e)}")
    
    def _validate_input(self, param: TypeHint) -> None:
        """Private validation method."""
        pass
    
    def _process_input(self, param: TypeHint) -> ReturnType:
        """Private processing method."""
        pass
```

**Quality Validation for AI-Generated Code**:
```python
def validate_ai_generated_service(service_class) -> Dict[str, bool]:
    """
    Validation checklist for AI-generated services.
    
    AI assistants must ensure all these checks pass.
    """
    return {
        "has_proper_docstring": check_class_docstring(service_class),
        "follows_naming_conventions": check_naming(service_class),
        "has_type_hints": check_type_hints(service_class),
        "has_error_handling": check_error_handling(service_class),
        "has_logging": check_logging_usage(service_class),
        "has_input_validation": check_input_validation(service_class),
        "follows_service_pattern": check_service_pattern(service_class),
        "has_comprehensive_tests": check_test_coverage(service_class)
    }
```

---

## Enforcement and Monitoring

### Continuous Integration

**Pre-commit Hooks**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        args: [--line-length=100]
        
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
```

**GitHub Actions Workflow**:
```yaml
name: Code Quality
on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
          
      - name: Run quality checks
        run: |
          black --check app/ tests/
          isort --check app/ tests/
          flake8 app/ tests/
          mypy app/
          pytest tests/ --cov=app --cov-fail-under=90
```

### Metrics and Monitoring

**Code Quality Metrics**:
- Test coverage: >90%
- Type hint coverage: >95%
- Documentation coverage: 100% of public methods
- Linting violations: 0
- Security issues: 0

**Performance Standards**:
- Service method response time: <100ms (90th percentile)
- API endpoint response time: <200ms (90th percentile)
- Memory usage per service: <100MB
- CPU utilization: <80% sustained

---

**Next Steps**: [Testing Guide](TESTING_GUIDE.md) | [Feature Development](FEATURE_DEVELOPMENT.md) | [Code Review](CODE_REVIEW.md)

---

**Last Updated**: June 25, 2025  
**Maintainer**: Development Team  
**Related Documents**: [Service Architecture](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md), [AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)