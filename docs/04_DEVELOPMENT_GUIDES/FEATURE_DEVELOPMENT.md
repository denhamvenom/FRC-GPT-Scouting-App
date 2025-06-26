# Feature Development Guide

**Purpose**: Comprehensive guide for developing new features in the FRC GPT Scouting App  
**Audience**: Developers and AI assistants  
**Scope**: Full feature development lifecycle from planning to deployment  

---

## Feature Development Philosophy

The FRC GPT Scouting App follows a **structured feature development process** that ensures consistency, quality, and maintainability while supporting both human and AI-assisted development.

### Core Development Principles
- **Service-Oriented Design**: Features are built around service boundaries
- **AI-First Architecture**: All features consider AI integration from the start
- **Test-Driven Development**: Tests guide feature implementation
- **Documentation-Driven**: Clear specifications before implementation
- **Performance-Aware**: Every feature considers performance implications
- **User-Centric**: Features solve real user problems effectively

---

## Feature Development Lifecycle

### Development Process Overview

```
1. Feature Planning
   ├── Requirements analysis
   ├── Technical specification
   ├── Architecture review
   └── Implementation planning

2. Design Phase
   ├── Service design
   ├── API contract definition
   ├── Database schema (if needed)
   └── UI/UX mockups (frontend features)

3. Implementation Phase
   ├── Test-driven development
   ├── Service implementation
   ├── API endpoint creation
   ├── Frontend component development
   └── Integration testing

4. Quality Assurance
   ├── Code review
   ├── Performance testing
   ├── Security review
   └── Documentation completion

5. Deployment & Monitoring
   ├── Feature flag implementation
   ├── Gradual rollout
   ├── Performance monitoring
   └── User feedback collection
```

---

## Feature Planning Phase

### Requirements Analysis

**Feature Requirements Template**:
```markdown
# Feature: [Feature Name]

## Problem Statement
Clear description of the problem this feature solves.

## User Stories
- As a [user type], I want [capability] so that [benefit]
- As a [user type], I want [capability] so that [benefit]

## Success Criteria
- [ ] Specific, measurable outcomes
- [ ] Performance requirements
- [ ] User adoption targets

## Technical Requirements
- [ ] Backend services needed
- [ ] Frontend components required
- [ ] External integrations
- [ ] Database changes
- [ ] AI/ML components

## Non-Functional Requirements
- [ ] Performance: Response times, throughput
- [ ] Security: Authentication, authorization, data protection
- [ ] Scalability: Expected load, growth projections
- [ ] Reliability: Uptime, error rates, recovery

## Constraints
- Timeline limitations
- Technical constraints
- Resource limitations
- Dependencies on other features

## Out of Scope
Explicitly list what this feature will NOT include.
```

### Technical Specification

**Architecture Decision Record (ADR) Template**:
```markdown
# ADR-XXX: [Feature Name] Implementation Approach

## Status
Proposed / Accepted / Superseded

## Context
Background information and problem description.

## Decision
The solution we've chosen and why.

## Alternatives Considered
- Option 1: Description, pros/cons
- Option 2: Description, pros/cons
- Option 3: Description, pros/cons

## Consequences
- Positive outcomes
- Negative outcomes
- Trade-offs accepted

## Implementation Plan
1. Phase 1: Foundation
2. Phase 2: Core functionality
3. Phase 3: Integration and optimization

## Success Metrics
How we'll measure if this decision was correct.
```

---

## Service-Oriented Feature Development

### Creating New Services

**Service Development Checklist**:
- [ ] Service follows established patterns (see [Service Contracts](../05_AI_FRAMEWORK/SERVICE_CONTRACTS.md))
- [ ] Comprehensive type hints and documentation
- [ ] Proper error handling and logging
- [ ] Input validation and sanitization
- [ ] Performance considerations (caching, optimization)
- [ ] Thread safety considerations
- [ ] Integration with orchestrator service

**New Service Template**:
```python
# app/services/example_feature_service.py
import logging
from typing import Any, Dict, List, Optional
from app.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)


class ExampleFeatureService:
    """
    Service for [feature description].
    
    This service handles [specific responsibilities] and integrates
    with [other services] to provide [functionality].
    
    Thread Safety: [Thread-safe/Not thread-safe - explain]
    Dependencies: [List dependencies]
    """
    
    def __init__(self, dependencies: Any) -> None:
        """
        Initialize service with required dependencies.
        
        Args:
            dependencies: Required dependencies for service operation
            
        Raises:
            ValueError: If dependencies are invalid
        """
        self._validate_dependencies(dependencies)
        self.dependencies = dependencies
        self._internal_cache: Dict[str, Any] = {}
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def primary_operation(self, 
                         input_data: Dict[str, Any],
                         options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Primary service operation following established patterns.
        
        Args:
            input_data: Input data for processing
            options: Optional configuration parameters
            
        Returns:
            Result dictionary with standardized format:
            {
                "status": "success" | "error",
                "data": Any,
                "metadata": {
                    "processing_time": float,
                    "cached": bool
                }
            }
            
        Raises:
            ValidationError: Input validation failed
            ServiceError: Service operation failed
            
        Example:
            >>> service = ExampleFeatureService(deps)
            >>> result = service.primary_operation({"key": "value"})
            >>> print(result["status"])
            success
        """
        try:
            # 1. Input validation
            self._validate_input(input_data, options)
            
            # 2. Processing with error handling
            start_time = time.time()
            result = self._process_data(input_data, options)
            processing_time = time.time() - start_time
            
            # 3. Success logging
            logger.info(f"Successfully processed operation: {input_data.get('id', 'unknown')}")
            
            return {
                "status": "success",
                "data": result,
                "metadata": {
                    "processing_time": processing_time,
                    "cached": False
                }
            }
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Service operation failed: {str(e)}", exc_info=True)
            raise ServiceError(f"Failed to process operation: {str(e)}")
    
    def _validate_input(self, input_data: Dict[str, Any], options: Optional[Dict[str, Any]]) -> None:
        """Private method for input validation."""
        if not input_data:
            raise ValidationError("Input data cannot be empty")
        
        required_fields = ['required_field_1', 'required_field_2']
        missing_fields = [field for field in required_fields if field not in input_data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
    
    def _process_data(self, input_data: Dict[str, Any], options: Optional[Dict[str, Any]]) -> Any:
        """Private method for core processing logic."""
        # Implementation details
        pass
    
    def _validate_dependencies(self, dependencies: Any) -> None:
        """Validate service dependencies during initialization."""
        if not dependencies:
            raise ValueError("Dependencies cannot be None")
```

### Extending Existing Services

**Service Extension Guidelines**:
```python
# Adding new methods to existing services
class ExistingService:
    """Existing service with new functionality."""
    
    def new_feature_method(self, 
                          params: Dict[str, Any]) -> Dict[str, Any]:
        """
        New method added for feature development.
        
        IMPORTANT: Maintain backward compatibility with existing methods.
        Follow established patterns and error handling.
        """
        try:
            # Follow same patterns as existing methods
            self._validate_new_input(params)
            result = self._implement_new_feature(params)
            
            logger.info(f"Successfully executed new feature: {params.get('id')}")
            return self._format_standard_response(result)
            
        except ValidationError as e:
            logger.error(f"Validation error in new feature: {e}")
            raise
        except Exception as e:
            logger.error(f"New feature operation failed: {e}")
            raise ServiceError(f"Feature operation failed: {e}")
```

---

## API Development

### FastAPI Endpoint Development

**API Endpoint Template**:
```python
# app/api/v1/endpoints/example_feature.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.example_feature_service import ExampleFeatureService
from app.api.deps import get_current_user, get_example_service
from app.schemas.requests import ExampleFeatureRequest
from app.schemas.responses import ExampleFeatureResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/example-feature", 
             response_model=ExampleFeatureResponse,
             responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
             summary="Execute example feature operation",
             description="Detailed description of what this endpoint does")
async def execute_example_feature(
    request: ExampleFeatureRequest,
    background_tasks: BackgroundTasks,
    service: ExampleFeatureService = Depends(get_example_service),
    current_user: Optional[User] = Depends(get_current_user)
) -> ExampleFeatureResponse:
    """
    Execute example feature with comprehensive validation and error handling.
    
    This endpoint demonstrates the standard pattern for new feature endpoints:
    - Input validation via Pydantic models
    - Service integration with proper error handling
    - Background task integration for analytics
    - Comprehensive logging and monitoring
    
    Args:
        request: Feature request with validated input data
        background_tasks: For async operations (analytics, caching)
        service: Injected service dependency
        current_user: Authenticated user context (if required)
        
    Returns:
        ExampleFeatureResponse with operation results
        
    Raises:
        HTTPException: For validation errors (422) or service failures (500)
    """
    try:
        # Log request for monitoring
        logger.info(f"Example feature requested by user {current_user.id if current_user else 'anonymous'}")
        
        # Execute service operation
        result = await service.primary_operation(
            input_data=request.dict(),
            options={"user_id": current_user.id if current_user else None}
        )
        
        # Background task for analytics/cleanup
        background_tasks.add_task(
            track_feature_usage, 
            feature_name="example_feature",
            user_id=current_user.id if current_user else None,
            request_data=request.dict()
        )
        
        # Return standardized response
        return ExampleFeatureResponse(
            status="success",
            data=result["data"],
            metadata={
                "request_id": generate_request_id(),
                "processing_time": result["metadata"]["processing_time"],
                "cached": result["metadata"]["cached"]
            }
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error in example feature: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Validation failed",
                "message": str(e),
                "type": "validation_error"
            }
        )
    except ServiceError as e:
        logger.error(f"Service error in example feature: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal service error",
                "message": "Feature operation failed",
                "type": "service_error"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in example feature: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "type": "internal_error"
            }
        )


@router.get("/example-feature/{feature_id}",
            response_model=ExampleFeatureResponse,
            summary="Get example feature by ID")
async def get_example_feature(
    feature_id: str,
    service: ExampleFeatureService = Depends(get_example_service)
) -> ExampleFeatureResponse:
    """Get specific feature data by ID."""
    try:
        result = await service.get_by_id(feature_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not found",
                    "message": f"Feature {feature_id} not found",
                    "type": "not_found_error"
                }
            )
        
        return ExampleFeatureResponse(
            status="success",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feature {feature_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Request/Response Schema Development

**Pydantic Schema Templates**:
```python
# app/schemas/example_feature.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


class FeatureType(str, Enum):
    """Enumeration of supported feature types."""
    TYPE_A = "type_a"
    TYPE_B = "type_b"
    TYPE_C = "type_c"


class ExampleFeatureRequest(BaseModel):
    """Request schema for example feature operation."""
    
    feature_type: FeatureType = Field(
        ..., 
        description="Type of feature operation to perform"
    )
    
    input_data: Dict[str, Any] = Field(
        ..., 
        description="Feature-specific input data",
        example={"key1": "value1", "key2": 42}
    )
    
    options: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional configuration parameters"
    )
    
    priority: int = Field(
        1,
        ge=1,
        le=5,
        description="Processing priority (1=low, 5=high)"
    )
    
    timeout_seconds: Optional[int] = Field(
        None,
        ge=1,
        le=300,
        description="Custom timeout for operation"
    )
    
    @validator('input_data')
    def validate_input_data(cls, v, values):
        """Validate input data based on feature type."""
        feature_type = values.get('feature_type')
        
        if feature_type == FeatureType.TYPE_A:
            required_fields = ['field_a', 'field_b']
        elif feature_type == FeatureType.TYPE_B:
            required_fields = ['field_x', 'field_y']
        else:
            required_fields = []
        
        missing_fields = [field for field in required_fields if field not in v]
        if missing_fields:
            raise ValueError(f"Missing required fields for {feature_type}: {missing_fields}")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "feature_type": "type_a",
                "input_data": {
                    "field_a": "example_value",
                    "field_b": 123
                },
                "options": {
                    "optimization_level": 2
                },
                "priority": 3,
                "timeout_seconds": 60
            }
        }


class ExampleFeatureData(BaseModel):
    """Feature result data schema."""
    
    feature_id: str = Field(..., description="Unique feature identifier")
    results: Dict[str, Any] = Field(..., description="Feature processing results")
    insights: List[str] = Field(default_factory=list, description="AI-generated insights")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Result confidence")
    
    class Config:
        schema_extra = {
            "example": {
                "feature_id": "feat_abc123",
                "results": {"score": 95.5, "category": "excellent"},
                "insights": ["Strong performance in area X", "Improvement needed in area Y"],
                "confidence_score": 0.92
            }
        }


class ExampleFeatureResponse(BaseModel):
    """Response schema for example feature operation."""
    
    status: str = Field(..., description="Operation status")
    data: ExampleFeatureData = Field(..., description="Feature results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "feature_id": "feat_abc123",
                    "results": {"score": 95.5, "category": "excellent"},
                    "insights": ["Strong performance detected"],
                    "confidence_score": 0.92
                },
                "metadata": {
                    "request_id": "req_xyz789",
                    "processing_time": 1.23,
                    "cached": False
                }
            }
        }
```

---

## Frontend Feature Development

### React Component Development

**Component Development Template**:
```tsx
// src/components/ExampleFeature/ExampleFeatureComponent.tsx
import React, { useState, useCallback, useMemo } from 'react';
import { ExampleFeatureRequest, ExampleFeatureData } from '../../types/exampleFeature';
import { useExampleFeature } from '../../hooks/useExampleFeature';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorBanner } from '../common/ErrorBanner';
import { FeatureResults } from './FeatureResults';
import { FeatureConfiguration } from './FeatureConfiguration';

interface ExampleFeatureComponentProps {
  /** Initial configuration for the feature */
  initialConfig?: Partial<ExampleFeatureRequest>;
  /** Callback when feature execution completes */
  onComplete?: (results: ExampleFeatureData) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * ExampleFeatureComponent provides a complete interface for feature interaction.
 * 
 * This component demonstrates the standard pattern for new feature components:
 * - Comprehensive state management
 * - Custom hook integration for API calls
 * - Error handling and loading states
 * - Accessibility considerations
 * - Performance optimization with useMemo and useCallback
 */
export const ExampleFeatureComponent: React.FC<ExampleFeatureComponentProps> = ({
  initialConfig = {},
  onComplete,
  className = ''
}) => {
  // State management
  const [config, setConfig] = useState<ExampleFeatureRequest>({
    feature_type: 'type_a',
    input_data: {},
    priority: 1,
    ...initialConfig
  });

  // Custom hook for API integration
  const {
    executeFeature,
    data: results,
    isLoading,
    error,
    clearError
  } = useExampleFeature();

  // Memoized validation
  const isConfigValid = useMemo(() => {
    return config.feature_type &&
           Object.keys(config.input_data).length > 0 &&
           config.priority >= 1 && config.priority <= 5;
  }, [config]);

  // Event handlers
  const handleConfigChange = useCallback((newConfig: Partial<ExampleFeatureRequest>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
    clearError();
  }, [clearError]);

  const handleExecute = useCallback(async () => {
    if (!isConfigValid) {
      return;
    }

    try {
      const results = await executeFeature(config);
      if (onComplete) {
        onComplete(results);
      }
    } catch (error) {
      // Error handling done by hook
      console.error('Feature execution failed:', error);
    }
  }, [config, isConfigValid, executeFeature, onComplete]);

  const handleReset = useCallback(() => {
    setConfig({
      feature_type: 'type_a',
      input_data: {},
      priority: 1
    });
    clearError();
  }, [clearError]);

  // Render
  return (
    <div className={`example-feature-component ${className}`}>
      <div className="feature-header">
        <h2>Example Feature</h2>
        <p>Configure and execute the example feature operation.</p>
      </div>

      {error && (
        <ErrorBanner 
          error={error} 
          onDismiss={clearError}
          className="mb-4"
        />
      )}

      <div className="feature-content">
        <div className="feature-configuration">
          <FeatureConfiguration
            config={config}
            onChange={handleConfigChange}
            disabled={isLoading}
          />
        </div>

        <div className="feature-actions">
          <button
            type="button"
            onClick={handleExecute}
            disabled={!isConfigValid || isLoading}
            className="btn btn-primary"
            aria-describedby="execute-help"
          >
            {isLoading ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Executing...
              </>
            ) : (
              'Execute Feature'
            )}
          </button>

          <button
            type="button"
            onClick={handleReset}
            disabled={isLoading}
            className="btn btn-secondary ml-2"
          >
            Reset
          </button>

          <div id="execute-help" className="help-text">
            {!isConfigValid && 'Please configure all required fields to execute.'}
          </div>
        </div>

        {results && (
          <div className="feature-results">
            <FeatureResults
              data={results}
              onExport={() => {/* Export functionality */}}
            />
          </div>
        )}
      </div>
    </div>
  );
};

// Export with display name for better debugging
ExampleFeatureComponent.displayName = 'ExampleFeatureComponent';
```

### Custom Hook Development

**Custom Hook Template**:
```tsx
// src/hooks/useExampleFeature.ts
import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/apiService';
import { ExampleFeatureRequest, ExampleFeatureData } from '../types/exampleFeature';

interface UseExampleFeatureOptions {
  /** Enable automatic result caching */
  enableCaching?: boolean;
  /** Custom error handler */
  onError?: (error: Error) => void;
  /** Custom success handler */
  onSuccess?: (data: ExampleFeatureData) => void;
}

/**
 * Custom hook for example feature operations.
 * 
 * Provides a clean interface for feature execution with:
 * - Automatic error handling and state management
 * - Query caching for performance
 * - Loading and error states
 * - Optimistic updates where appropriate
 */
export const useExampleFeature = (options: UseExampleFeatureOptions = {}) => {
  const {
    enableCaching = true,
    onError,
    onSuccess
  } = options;

  const queryClient = useQueryClient();
  const [error, setError] = useState<Error | null>(null);

  // Feature execution mutation
  const executeFeatureMutation = useMutation({
    mutationFn: (request: ExampleFeatureRequest) => apiService.executeExampleFeature(request),
    onSuccess: (data) => {
      setError(null);
      
      // Update cache if enabled
      if (enableCaching) {
        queryClient.setQueryData(['example-feature', data.feature_id], data);
      }
      
      // Custom success handler
      if (onSuccess) {
        onSuccess(data);
      }
    },
    onError: (error: Error) => {
      setError(error);
      
      // Custom error handler
      if (onError) {
        onError(error);
      }
    }
  });

  // Feature data query (for retrieving existing results)
  const getFeatureData = useCallback((featureId: string) => {
    return useQuery({
      queryKey: ['example-feature', featureId],
      queryFn: () => apiService.getExampleFeature(featureId),
      enabled: !!featureId && enableCaching,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
    });
  }, [enableCaching]);

  // Feature list query
  const {
    data: featureList,
    isLoading: isLoadingList,
    refetch: refetchList
  } = useQuery({
    queryKey: ['example-features'],
    queryFn: () => apiService.listExampleFeatures(),
    enabled: enableCaching,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Main execution function
  const executeFeature = useCallback(async (request: ExampleFeatureRequest): Promise<ExampleFeatureData> => {
    setError(null);
    
    try {
      const result = await executeFeatureMutation.mutateAsync(request);
      return result;
    } catch (error) {
      throw error; // Re-throw for component handling
    }
  }, [executeFeatureMutation]);

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
    executeFeatureMutation.reset();
  }, [executeFeatureMutation]);

  // Invalidate cache
  const invalidateCache = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['example-feature'] });
  }, [queryClient]);

  return {
    // Main functions
    executeFeature,
    getFeatureData,
    clearError,
    invalidateCache,
    
    // State
    data: executeFeatureMutation.data,
    isLoading: executeFeatureMutation.isPending,
    error: error || executeFeatureMutation.error,
    
    // Feature list
    featureList,
    isLoadingList,
    refetchList,
    
    // Mutation helpers
    reset: executeFeatureMutation.reset,
    isSuccess: executeFeatureMutation.isSuccess,
    isError: executeFeatureMutation.isError,
  };
};

// Type exports for consumers
export type { UseExampleFeatureOptions };
```

---

## Testing Strategy for Features

### Test-Driven Development Approach

**Feature Test Structure**:
```
tests/
├── test_services/
│   └── test_example_feature_service.py    # Service unit tests
├── test_integration/
│   └── test_example_feature_api.py        # API integration tests
└── test_e2e/
    └── test_example_feature_workflow.py   # End-to-end tests
```

**Service Test Template**:
```python
# tests/test_services/test_example_feature_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.example_feature_service import ExampleFeatureService
from app.exceptions import ValidationError, ServiceError


class TestExampleFeatureService:
    """Comprehensive test suite for ExampleFeatureService."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        mock_dependencies = Mock()
        return ExampleFeatureService(mock_dependencies)
    
    @pytest.fixture
    def valid_input_data(self):
        """Provide valid input data for testing."""
        return {
            "feature_type": "type_a",
            "field_a": "test_value",
            "field_b": 123,
            "priority": 2
        }
    
    def test_primary_operation_success(self, service, valid_input_data):
        """Test successful primary operation."""
        # Act
        result = service.primary_operation(valid_input_data)
        
        # Assert
        assert result["status"] == "success"
        assert "data" in result
        assert "metadata" in result
        assert result["metadata"]["processing_time"] > 0
        assert isinstance(result["metadata"]["cached"], bool)
    
    def test_primary_operation_validation_error(self, service):
        """Test validation error handling."""
        # Arrange
        invalid_input = {}  # Empty input
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Input data cannot be empty"):
            service.primary_operation(invalid_input)
    
    def test_primary_operation_missing_fields(self, service):
        """Test missing required fields validation."""
        # Arrange
        incomplete_input = {"feature_type": "type_a"}  # Missing required fields
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Missing required fields"):
            service.primary_operation(incomplete_input)
    
    @patch('app.services.example_feature_service.external_dependency')
    def test_primary_operation_external_failure(self, mock_external, service, valid_input_data):
        """Test handling of external service failures."""
        # Arrange
        mock_external.side_effect = Exception("External service error")
        
        # Act & Assert
        with pytest.raises(ServiceError, match="Failed to process operation"):
            service.primary_operation(valid_input_data)
    
    def test_performance_requirements(self, service, valid_input_data):
        """Test performance requirements are met."""
        import time
        
        # Act
        start_time = time.time()
        result = service.primary_operation(valid_input_data)
        execution_time = time.time() - start_time
        
        # Assert
        assert execution_time < 5.0  # Service should complete in <5 seconds
        assert result["metadata"]["processing_time"] < 5.0
    
    def test_concurrent_operations(self, service, valid_input_data):
        """Test handling of concurrent operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def execute_operation():
            try:
                result = service.primary_operation(valid_input_data)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Launch multiple threads
        threads = [threading.Thread(target=execute_operation) for _ in range(5)]
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 5
        assert all(r["status"] == "success" for r in results)
```

### Integration Testing

**API Integration Test Template**:
```python
# tests/test_integration/test_example_feature_api.py
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestExampleFeatureAPI:
    """Integration tests for example feature API endpoints."""
    
    async def test_execute_feature_success(self):
        """Test successful feature execution via API."""
        # Arrange
        request_data = {
            "feature_type": "type_a",
            "input_data": {
                "field_a": "test_value",
                "field_b": 123
            },
            "priority": 2
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.post("/api/v1/example-feature", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "metadata" in data
        assert data["metadata"]["request_id"]
    
    async def test_execute_feature_validation_error(self):
        """Test API validation error handling."""
        # Arrange
        invalid_request = {
            "feature_type": "invalid_type",  # Invalid enum value
            "input_data": {}
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.post("/api/v1/example-feature", json=invalid_request)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    async def test_get_feature_by_id(self):
        """Test retrieving feature by ID."""
        # First create a feature
        create_request = {
            "feature_type": "type_a",
            "input_data": {"field_a": "test", "field_b": 1},
            "priority": 1
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create feature
            create_response = await client.post("/api/v1/example-feature", json=create_request)
            feature_id = create_response.json()["data"]["feature_id"]
            
            # Retrieve feature
            get_response = await client.get(f"/api/v1/example-feature/{feature_id}")
        
        # Assert
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["data"]["feature_id"] == feature_id
    
    async def test_feature_not_found(self):
        """Test 404 handling for non-existent features."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Act
            response = await client.get("/api/v1/example-feature/nonexistent")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["type"] == "not_found_error"
```

---

## Performance Optimization

### Performance Guidelines

**Performance Requirements**:
- API endpoints: <200ms response time (90th percentile)
- Service methods: <5s processing time
- Database queries: <100ms execution time
- Memory usage: <100MB per service instance
- Cache hit rate: >80% for repeated requests

**Optimization Strategies**:

```python
# Example: Caching implementation
from functools import lru_cache
import time
from typing import Dict, Any

class OptimizedFeatureService:
    """Feature service with performance optimizations."""
    
    def __init__(self, dependencies):
        self.dependencies = dependencies
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 3600  # 1 hour
    
    def primary_operation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Primary operation with caching."""
        # Generate cache key
        cache_key = self._generate_cache_key(input_data)
        
        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return {
                **cached_result,
                "metadata": {
                    **cached_result["metadata"],
                    "cached": True
                }
            }
        
        # Process operation
        start_time = time.time()
        result = self._process_operation(input_data)
        processing_time = time.time() - start_time
        
        # Format response
        response = {
            "status": "success",
            "data": result,
            "metadata": {
                "processing_time": processing_time,
                "cached": False
            }
        }
        
        # Cache result
        self._cache_result(cache_key, response)
        
        return response
    
    @lru_cache(maxsize=1000)
    def _expensive_calculation(self, key: str) -> Any:
        """Expensive calculation with LRU cache."""
        # Expensive operation here
        return complex_calculation(key)
    
    def _generate_cache_key(self, input_data: Dict[str, Any]) -> str:
        """Generate deterministic cache key."""
        import hashlib
        import json
        
        # Sort keys for deterministic hashing
        sorted_data = json.dumps(input_data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache if valid."""
        if cache_key not in self._cache:
            return None
        
        # Check TTL
        cache_time = self._cache_timestamps.get(cache_key, 0)
        if time.time() - cache_time > self._cache_ttl:
            # Expired
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            return None
        
        return self._cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Store result in cache."""
        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
        
        # Implement cache size limit (LRU eviction)
        if len(self._cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self._cache_timestamps.keys(),
                key=lambda k: self._cache_timestamps[k]
            )[:100]  # Remove 100 oldest
            
            for key in oldest_keys:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
```

---

## Feature Rollout and Monitoring

### Feature Flags

**Feature Flag Implementation**:
```python
# app/utils/feature_flags.py
from typing import Dict, Any
import os
from functools import wraps

class FeatureFlags:
    """Feature flag management system."""
    
    def __init__(self):
        self.flags = {
            "example_feature_enabled": os.getenv("FEATURE_EXAMPLE_ENABLED", "false").lower() == "true",
            "example_feature_beta": os.getenv("FEATURE_EXAMPLE_BETA", "false").lower() == "true",
            "example_feature_rollout_percentage": int(os.getenv("FEATURE_EXAMPLE_ROLLOUT", "0"))
        }
    
    def is_enabled(self, flag_name: str, user_id: str = None) -> bool:
        """Check if feature flag is enabled for user."""
        if flag_name not in self.flags:
            return False
        
        # Simple percentage rollout
        if flag_name.endswith("_rollout_percentage"):
            base_flag = flag_name.replace("_rollout_percentage", "_enabled")
            if not self.flags.get(base_flag, False):
                return False
            
            percentage = self.flags[flag_name]
            if user_id:
                # Deterministic rollout based on user ID
                import hashlib
                hash_value = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
                return (hash_value % 100) < percentage
            
            return percentage >= 100
        
        return self.flags.get(flag_name, False)

# Global instance
feature_flags = FeatureFlags()

def feature_flag_required(flag_name: str):
    """Decorator to require feature flag for endpoint."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user ID from request context
            user_id = getattr(g, 'user_id', None) if 'g' in globals() else None
            
            if not feature_flags.is_enabled(flag_name, user_id):
                raise HTTPException(
                    status_code=404,
                    detail="Feature not available"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Usage in API Endpoints**:
```python
@router.post("/example-feature")
@feature_flag_required("example_feature_enabled")
async def execute_example_feature(request: ExampleFeatureRequest):
    """Execute example feature (behind feature flag)."""
    # Feature implementation
    pass
```

### Monitoring and Analytics

**Feature Monitoring Setup**:
```python
# app/utils/feature_monitoring.py
import logging
import time
from typing import Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class FeatureMonitor:
    """Monitor feature usage and performance."""
    
    def __init__(self):
        self.metrics = {}
    
    def track_feature_usage(self, 
                           feature_name: str,
                           user_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None):
        """Track feature usage for analytics."""
        logger.info(
            "Feature usage tracked",
            extra={
                "feature_name": feature_name,
                "user_id": user_id,
                "metadata": metadata,
                "timestamp": time.time()
            }
        )
    
    def track_feature_performance(self,
                                 feature_name: str,
                                 execution_time: float,
                                 success: bool,
                                 error_type: Optional[str] = None):
        """Track feature performance metrics."""
        logger.info(
            "Feature performance tracked",
            extra={
                "feature_name": feature_name,
                "execution_time": execution_time,
                "success": success,
                "error_type": error_type,
                "timestamp": time.time()
            }
        )

# Global monitor instance
feature_monitor = FeatureMonitor()

def monitor_feature_performance(feature_name: str):
    """Decorator to monitor feature performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_type = None
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                execution_time = time.time() - start_time
                feature_monitor.track_feature_performance(
                    feature_name=feature_name,
                    execution_time=execution_time,
                    success=success,
                    error_type=error_type
                )
        
        return wrapper
    return decorator
```

---

## Feature Documentation

### Documentation Requirements

**Feature Documentation Checklist**:
- [ ] User-facing documentation in appropriate guides
- [ ] API documentation with OpenAPI schemas
- [ ] Architecture documentation updates
- [ ] Code comments and docstrings
- [ ] Migration guides (if applicable)
- [ ] Troubleshooting guides

**Feature Documentation Template**:
```markdown
# Feature: [Feature Name]

## Overview
Brief description of what the feature does and its benefits.

## Use Cases
- Primary use case with example
- Secondary use cases
- Integration scenarios

## API Reference
Link to auto-generated API documentation or inline examples.

## Configuration
Environment variables, feature flags, and configuration options.

## Performance
Expected performance characteristics and optimization tips.

## Troubleshooting
Common issues and their solutions.

## Migration
If this feature replaces existing functionality, migration instructions.

## Related Features
Links to related features and documentation.
```

---

**Next Steps**: [Testing Guide](TESTING_GUIDE.md) | [Code Review](CODE_REVIEW.md) | [AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)

---

**Last Updated**: June 25, 2025  
**Maintainer**: Development Team  
**Related Documents**: [Coding Standards](CODING_STANDARDS.md), [Service Architecture](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md), [API Contracts](../03_ARCHITECTURE/API_CONTRACTS.md)