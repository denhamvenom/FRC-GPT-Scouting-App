# Testing Guide

**Purpose**: Complete testing strategy and implementation guidelines  
**Audience**: Developers and AI assistants  
**Scope**: Unit, integration, and end-to-end testing for all application components  

---

## Testing Philosophy

The FRC GPT Scouting App follows a **comprehensive testing strategy** that ensures reliability, maintainability, and confidence in AI-driven functionality.

### Core Testing Principles
- **Test-Driven Development (TDD)**: Write tests before implementation
- **Comprehensive Coverage**: >90% test coverage for critical paths
- **AI-Aware Testing**: Special consideration for AI service testing
- **Fast Feedback**: Tests run quickly for rapid development cycles
- **Realistic Testing**: Use realistic data and scenarios
- **Isolated Testing**: Tests are independent and can run in any order

---

## Testing Strategy Overview

### Testing Pyramid

```
              E2E Tests (5%)
         ┌─────────────────────┐
         │   Integration       │
         │   Tests (25%)       │
    ┌─────────────────────────────┐
    │        Unit Tests           │
    │        (70%)                │
    └─────────────────────────────┘
```

**Unit Tests (70%)**:
- Individual service methods
- Data transformation functions
- Utility functions and helpers
- Error handling scenarios

**Integration Tests (25%)**:
- Service-to-service interactions
- API endpoint testing
- Database operations
- External service mocking

**End-to-End Tests (5%)**:
- Complete user workflows
- Frontend-backend integration
- Real scenario validation

---

## Backend Testing Framework

### Testing Stack
- **pytest 7.0+**: Primary testing framework
- **pytest-asyncio**: Async function testing
- **pytest-cov**: Coverage measurement
- **pytest-mock**: Mocking and patching
- **httpx**: API client testing
- **factory_boy**: Test data generation

### Test Organization

```
backend/tests/
├── conftest.py              # Shared fixtures and configuration
├── test_services/           # Service unit tests
│   ├── test_data_aggregation_service.py
│   ├── test_team_analysis_service.py
│   ├── test_priority_calculation_service.py
│   ├── test_performance_optimization_service.py
│   ├── test_batch_processing_service.py
│   └── test_picklist_gpt_service.py
├── test_integration/        # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_service_orchestration.py
│   └── test_database_operations.py
├── test_utils/             # Utility function tests
│   ├── test_validators.py
│   └── test_helpers.py
├── fixtures/               # Test data files
│   ├── sample_dataset.json
│   ├── test_teams.json
│   └── mock_responses/
└── factories/              # Test data factories
    ├── team_factory.py
    └── priority_factory.py
```

### Basic Test Configuration

**conftest.py**:
```python
import pytest
import asyncio
from pathlib import Path
from typing import Generator, Dict, Any, List
from unittest.mock import Mock

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "fixtures"
SAMPLE_DATASET = TEST_DATA_DIR / "sample_dataset.json"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_teams_data() -> List[Dict[str, Any]]:
    """Provide consistent test team data."""
    return [
        {
            "team_number": 1001,
            "nickname": "Test Alpha",
            "autonomous_score": 20.5,
            "teleop_avg_points": 45.2,
            "endgame_points": 15.0,
            "defense_rating": 4.0,
            "reliability_score": 0.85
        },
        {
            "team_number": 1002,
            "nickname": "Test Beta",
            "autonomous_score": 18.0,
            "teleop_avg_points": 42.1,
            "endgame_points": 12.5,
            "defense_rating": 3.5,
            "reliability_score": 0.90
        },
        {
            "team_number": 1003,
            "nickname": "Test Gamma",
            "autonomous_score": 22.0,
            "teleop_avg_points": 48.7,
            "endgame_points": 18.0,
            "defense_rating": 4.5,
            "reliability_score": 0.75
        }
    ]

@pytest.fixture
def sample_priorities() -> List[Dict[str, Any]]:
    """Provide consistent test priority data."""
    return [
        {"metric": "autonomous_score", "weight": 3.0},
        {"metric": "teleop_avg_points", "weight": 5.0},
        {"metric": "endgame_points", "weight": 2.0}
    ]

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content='{"ranked_teams": [], "summary": "Test response"}'))
    ]
    mock_response.usage = Mock(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def temp_dataset_file(tmp_path: Path, sample_teams_data: List[Dict[str, Any]]) -> Path:
    """Create temporary dataset file for testing."""
    dataset = {
        "teams": sample_teams_data,
        "context": "Test competition data",
        "game_info": "Test game with sample scoring"
    }
    
    dataset_file = tmp_path / "test_dataset.json"
    dataset_file.write_text(json.dumps(dataset, indent=2))
    return dataset_file
```

---

## Unit Testing Patterns

### Service Testing Template

**test_data_aggregation_service.py**:
```python
import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from app.services.data_aggregation_service import DataAggregationService
from app.exceptions import ValidationError


class TestDataAggregationService:
    """Test suite for DataAggregationService."""
    
    def test_initialization_success(self, temp_dataset_file: Path):
        """Test successful service initialization."""
        # Act
        service = DataAggregationService(str(temp_dataset_file))
        
        # Assert
        assert service is not None
        assert service.dataset_path == temp_dataset_file
        assert len(service.teams_data) > 0

    def test_initialization_file_not_found(self):
        """Test initialization with non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Dataset file not found"):
            DataAggregationService("/nonexistent/path.json")

    def test_initialization_invalid_json(self, tmp_path: Path):
        """Test initialization with invalid JSON."""
        # Arrange
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid JSON"):
            DataAggregationService(str(invalid_file))

    def test_get_teams_for_analysis_no_filters(self, temp_dataset_file: Path, sample_teams_data):
        """Test getting teams without any filters."""
        # Arrange
        service = DataAggregationService(str(temp_dataset_file))
        
        # Act
        teams = service.get_teams_for_analysis()
        
        # Assert
        assert len(teams) == len(sample_teams_data)
        assert teams[0]["team_number"] == 1001
        
    def test_get_teams_for_analysis_with_exclusions(self, temp_dataset_file: Path):
        """Test getting teams with exclusion filter."""
        # Arrange
        service = DataAggregationService(str(temp_dataset_file))
        exclude_teams = [1001, 1003]
        
        # Act
        teams = service.get_teams_for_analysis(exclude_teams=exclude_teams)
        
        # Assert
        assert len(teams) == 1
        assert teams[0]["team_number"] == 1002
        assert all(team["team_number"] not in exclude_teams for team in teams)

    def test_get_teams_for_analysis_specific_teams(self, temp_dataset_file: Path):
        """Test getting specific teams."""
        # Arrange
        service = DataAggregationService(str(temp_dataset_file))
        specific_teams = [1001, 1003]
        
        # Act
        teams = service.get_teams_for_analysis(team_numbers=specific_teams)
        
        # Assert
        assert len(teams) == 2
        team_numbers = [team["team_number"] for team in teams]
        assert all(num in team_numbers for num in specific_teams)

    def test_load_game_context_success(self, temp_dataset_file: Path):
        """Test loading game context."""
        # Arrange
        service = DataAggregationService(str(temp_dataset_file))
        
        # Act
        context = service.load_game_context()
        
        # Assert
        assert context is not None
        assert "Test competition data" in context

    def test_validate_dataset_success(self, temp_dataset_file: Path):
        """Test dataset validation with valid data."""
        # Arrange
        service = DataAggregationService(str(temp_dataset_file))
        
        # Act
        validation_result = service.validate_dataset()
        
        # Assert
        assert validation_result["status"] == "valid"
        assert validation_result["team_count"] == 3
        assert validation_result["required_fields_present"] is True
        assert validation_result["data_quality_score"] > 0.8

    def test_validate_dataset_missing_fields(self, tmp_path: Path):
        """Test dataset validation with missing required fields."""
        # Arrange
        incomplete_data = {
            "teams": [
                {"team_number": 1001},  # Missing nickname
                {"nickname": "Test Team"}  # Missing team_number
            ]
        }
        
        dataset_file = tmp_path / "incomplete.json"
        dataset_file.write_text(json.dumps(incomplete_data))
        
        service = DataAggregationService(str(dataset_file))
        
        # Act
        validation_result = service.validate_dataset()
        
        # Assert
        assert validation_result["status"] in ["invalid", "warning"]
        assert len(validation_result["missing_fields"]) > 0
        assert validation_result["data_quality_score"] < 0.8

    @pytest.mark.asyncio
    async def test_performance_requirements(self, temp_dataset_file: Path):
        """Test performance requirements are met."""
        import time
        
        # Arrange
        service = DataAggregationService(str(temp_dataset_file))
        
        # Act - Test get_teams_for_analysis performance
        start_time = time.time()
        teams = service.get_teams_for_analysis(exclude_teams=[1001])
        end_time = time.time()
        
        # Assert
        assert (end_time - start_time) < 0.1  # <100ms requirement
        assert len(teams) > 0

    def test_thread_safety_warning(self, temp_dataset_file: Path):
        """Document that service is not thread-safe."""
        # This test documents the thread safety contract
        service = DataAggregationService(str(temp_dataset_file))
        
        # Service should be used with separate instances for threads
        # This is documented behavior, not a test failure
        assert hasattr(service, 'teams_data')  # Maintains state
```

### AI Service Testing Patterns

**test_picklist_gpt_service.py**:
```python
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from app.services.picklist_gpt_service import PicklistGPTService
from app.exceptions import OpenAIError, ValidationError


class TestPicklistGPTService:
    """Test suite for PicklistGPTService with OpenAI mocking."""
    
    def test_create_system_prompt(self):
        """Test system prompt generation."""
        # Arrange
        service = PicklistGPTService()
        pick_position = "first"
        context = "2024 Crescendo competition"
        
        # Act
        prompt = service.create_system_prompt(pick_position, context)
        
        # Assert
        assert pick_position in prompt
        assert context in prompt
        assert "FRC" in prompt
        assert "strategist" in prompt.lower()
        assert len(prompt) < 5000  # Reasonable length

    def test_create_user_prompt(self, sample_teams_data, sample_priorities):
        """Test user prompt generation."""
        # Arrange
        service = PicklistGPTService()
        
        # Act
        prompt = service.create_user_prompt(sample_teams_data, sample_priorities)
        
        # Assert
        assert "1001" in prompt  # Team numbers present
        assert "autonomous_score" in prompt  # Metrics present
        assert len(prompt) > 100  # Has content

    @pytest.mark.asyncio
    async def test_execute_analysis_success(self, mock_openai_client):
        """Test successful AI analysis execution."""
        # Arrange
        service = PicklistGPTService()
        messages = [
            {"role": "system", "content": "You are an expert"},
            {"role": "user", "content": "Analyze these teams"}
        ]
        
        with patch('app.services.picklist_gpt_service.openai_client', mock_openai_client):
            # Act
            result = await service.execute_analysis(messages)
            
            # Assert
            assert result["response"] is not None
            assert result["token_usage"]["total_tokens"] == 150
            assert result["model_used"] == "gpt-4"
            assert result["processing_time"] >= 0

    @pytest.mark.asyncio
    async def test_execute_analysis_rate_limit_retry(self):
        """Test rate limit handling with retry."""
        # Arrange
        service = PicklistGPTService()
        messages = [{"role": "user", "content": "test"}]
        
        mock_client = Mock()
        # First call raises rate limit, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"test": "success"}'))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client.chat.completions.create.side_effect = [
            Exception("Rate limit exceeded"),
            mock_response
        ]
        
        with patch('app.services.picklist_gpt_service.openai_client', mock_client):
            with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up test
                # Act
                result = await service.execute_analysis(messages)
                
                # Assert
                assert result["response"] is not None
                assert mock_client.chat.completions.create.call_count == 2

    def test_parse_response_with_index_mapping(self, sample_teams_data):
        """Test response parsing with team index mapping."""
        # Arrange
        service = PicklistGPTService()
        
        gpt_response = json.dumps({
            "ranked_teams": [
                {"team_index": 0, "rank": 1, "score": 95.5, "reasoning": "Strong all-around"},
                {"team_index": 2, "rank": 2, "score": 88.2, "reasoning": "Good autonomous"},
                {"team_index": 1, "rank": 3, "score": 82.1, "reasoning": "Reliable but slower"}
            ],
            "summary": "Analysis complete"
        })
        
        team_index_map = {0: 1001, 1: 1002, 2: 1003}
        
        # Act
        result = service.parse_response_with_index_mapping(
            gpt_response, sample_teams_data, team_index_map
        )
        
        # Assert
        assert len(result) == 3
        assert result[0]["team_number"] == 1001  # Mapped correctly
        assert result[0]["rank"] == 1
        assert result[0]["score"] == 95.5
        assert "Strong all-around" in result[0]["reasoning"]

    def test_parse_response_invalid_json(self, sample_teams_data):
        """Test parsing of invalid JSON response."""
        # Arrange
        service = PicklistGPTService()
        invalid_response = "{ invalid json response"
        team_index_map = {0: 1001}
        
        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            service.parse_response_with_index_mapping(
                invalid_response, sample_teams_data, team_index_map
            )

    def test_parse_response_missing_required_fields(self, sample_teams_data):
        """Test parsing response missing required fields."""
        # Arrange
        service = PicklistGPTService()
        incomplete_response = json.dumps({
            "summary": "Missing ranked_teams field"
        })
        team_index_map = {0: 1001}
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Missing required field"):
            service.parse_response_with_index_mapping(
                incomplete_response, sample_teams_data, team_index_map
            )

    def test_token_count_estimation(self):
        """Test token counting functionality."""
        # Arrange
        service = PicklistGPTService()
        test_text = "This is a test prompt for token counting."
        
        # Act
        token_info = service.check_token_count(test_text)
        
        # Assert
        assert "input_tokens" in token_info
        assert "estimated_cost" in token_info
        assert token_info["input_tokens"] > 0
        assert token_info["estimated_cost"] >= 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling for long-running requests."""
        # Arrange
        service = PicklistGPTService()
        messages = [{"role": "user", "content": "test"}]
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = TimeoutError("Request timeout")
        
        with patch('app.services.picklist_gpt_service.openai_client', mock_client):
            # Act & Assert
            with pytest.raises(OpenAIError, match="timeout"):
                await service.execute_analysis(messages)
```

---

## Integration Testing

### API Endpoint Testing

**test_api_endpoints.py**:
```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_database


@pytest.fixture
def test_client():
    """Create test client for API testing."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestPicklistAPI:
    """Integration tests for picklist API endpoints."""
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        # Act
        response = test_client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_generate_picklist_success(self, async_client, mock_openai_client):
        """Test successful picklist generation."""
        # Arrange
        request_data = {
            "your_team_number": 1234,
            "pick_position": "first",
            "priorities": [
                {"metric": "autonomous_score", "weight": 3.0},
                {"metric": "teleop_avg_points", "weight": 5.0}
            ],
            "exclude_teams": [9999]
        }
        
        with patch('app.services.picklist_gpt_service.openai_client', mock_openai_client):
            # Act
            response = await async_client.post("/api/v1/picklist/generate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "ranked_teams" in data["data"]
        assert len(data["data"]["ranked_teams"]) > 0

    @pytest.mark.asyncio
    async def test_generate_picklist_validation_error(self, async_client):
        """Test picklist generation with validation errors."""
        # Arrange
        invalid_request = {
            "your_team_number": "invalid",  # Should be integer
            "pick_position": "invalid_position",  # Invalid position
            "priorities": []  # Empty priorities
        }
        
        # Act
        response = await async_client.post("/api/v1/picklist/generate", json=invalid_request)
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_team_comparison_endpoint(self, async_client, mock_openai_client):
        """Test team comparison endpoint."""
        # Arrange
        request_data = {
            "team_numbers": [1001, 1002, 1003],
            "comparison_criteria": ["autonomous_score", "teleop_avg_points"]
        }
        
        with patch('app.services.picklist_gpt_service.openai_client', mock_openai_client):
            # Act
            response = await async_client.post("/api/v1/teams/compare", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "comparison_results" in data["data"]

    def test_api_documentation_accessible(self, test_client):
        """Test that API documentation is accessible."""
        # Act
        response = test_client.get("/docs")
        
        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema_accessible(self, test_client):
        """Test that OpenAPI schema is accessible."""
        # Act
        response = test_client.get("/openapi.json")
        
        # Assert
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
```

### Service Orchestration Testing

**test_service_orchestration.py**:
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.picklist_generator_service import PicklistGeneratorService


class TestServiceOrchestration:
    """Integration tests for service orchestration."""
    
    @pytest.fixture
    def orchestrator(self, temp_dataset_file):
        """Create orchestrator service for testing."""
        return PicklistGeneratorService(str(temp_dataset_file))

    @pytest.mark.asyncio
    async def test_full_picklist_generation_workflow(self, orchestrator, mock_openai_client):
        """Test complete picklist generation workflow."""
        # Arrange
        request_params = {
            "your_team_number": 1234,
            "pick_position": "first",
            "priorities": [
                {"metric": "autonomous_score", "weight": 3.0},
                {"metric": "teleop_avg_points", "weight": 5.0}
            ],
            "exclude_teams": [9999]
        }
        
        with patch('app.services.picklist_gpt_service.openai_client', mock_openai_client):
            # Act
            result = await orchestrator.generate_picklist(**request_params)
        
        # Assert
        assert result["status"] == "success"
        assert "ranked_teams" in result["data"]
        assert "summary" in result["data"]
        assert "metadata" in result
        assert result["metadata"]["processing_time"] > 0

    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self, orchestrator, mock_openai_client):
        """Test batch processing for large datasets."""
        # Arrange - Create large team dataset
        with patch.object(orchestrator.data_service, 'get_teams_for_analysis') as mock_get_teams:
            # Mock 60 teams to trigger batch processing
            mock_teams = [
                {"team_number": i, "nickname": f"Team {i}", "autonomous_score": 20.0}
                for i in range(1000, 1060)
            ]
            mock_get_teams.return_value = mock_teams
            
            request_params = {
                "your_team_number": 1234,
                "pick_position": "first",
                "priorities": [{"metric": "autonomous_score", "weight": 1.0}]
            }
            
            with patch('app.services.picklist_gpt_service.openai_client', mock_openai_client):
                # Act
                result = await orchestrator.generate_picklist(**request_params)
            
            # Assert
            assert result["status"] == "success"
            assert "batch_processing_used" in result["metadata"]
            assert result["metadata"]["batch_processing_used"] is True

    @pytest.mark.asyncio
    async def test_caching_integration(self, orchestrator, mock_openai_client):
        """Test caching integration across services."""
        # Arrange
        request_params = {
            "your_team_number": 1234,
            "pick_position": "first",
            "priorities": [{"metric": "autonomous_score", "weight": 1.0}]
        }
        
        with patch('app.services.picklist_gpt_service.openai_client', mock_openai_client):
            # Act - First request
            result1 = await orchestrator.generate_picklist(**request_params)
            
            # Act - Second identical request (should use cache)
            result2 = await orchestrator.generate_picklist(**request_params)
        
        # Assert
        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result2["metadata"]["cached"] is True
        # OpenAI should only be called once due to caching
        assert mock_openai_client.chat.completions.create.call_count == 1

    @pytest.mark.asyncio
    async def test_error_propagation_and_handling(self, orchestrator):
        """Test error propagation through service layers."""
        # Arrange - Mock data service to raise error
        with patch.object(orchestrator.data_service, 'get_teams_for_analysis') as mock_get_teams:
            mock_get_teams.side_effect = ValueError("Data processing error")
            
            request_params = {
                "your_team_number": 1234,
                "pick_position": "first",
                "priorities": [{"metric": "autonomous_score", "weight": 1.0}]
            }
            
            # Act & Assert
            with pytest.raises(ValueError, match="Data processing error"):
                await orchestrator.generate_picklist(**request_params)

    @pytest.mark.asyncio
    async def test_service_initialization_validation(self, temp_dataset_file):
        """Test service initialization and validation."""
        # Act
        orchestrator = PicklistGeneratorService(str(temp_dataset_file))
        
        # Assert - All services should be initialized
        assert orchestrator.data_service is not None
        assert orchestrator.analysis_service is not None
        assert orchestrator.priority_service is not None
        assert orchestrator.batch_service is not None
        assert orchestrator.performance_service is not None
        assert orchestrator.gpt_service is not None
```

---

## Frontend Testing

### Component Testing with React Testing Library

**Component Test Setup**:
```typescript
// src/test-utils.tsx
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create wrapper with providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

**Component Test Example**:
```typescript
// src/components/__tests__/TeamCard.test.tsx
import { render, screen, fireEvent } from '../test-utils';
import { TeamCard } from '../TeamCard';
import { TeamData } from '../../types';

const mockTeam: TeamData = {
  team_number: 1234,
  nickname: 'Test Team',
  autonomous_score: 20.5,
  teleop_avg_points: 45.2,
  endgame_points: 15.0,
  defense_rating: 4.0,
  reliability_score: 0.85,
};

describe('TeamCard Component', () => {
  it('renders team information correctly', () => {
    // Arrange
    const mockOnSelect = jest.fn();

    // Act
    render(
      <TeamCard
        team={mockTeam}
        onSelect={mockOnSelect}
        isSelected={false}
      />
    );

    // Assert
    expect(screen.getByText('Test Team')).toBeInTheDocument();
    expect(screen.getByText('Team #1234')).toBeInTheDocument();
    expect(screen.getByText(/Autonomous: 20.5/)).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    // Arrange
    const mockOnSelect = jest.fn();

    // Act
    render(
      <TeamCard
        team={mockTeam}
        onSelect={mockOnSelect}
        isSelected={false}
      />
    );

    fireEvent.click(screen.getByRole('button'));

    // Assert
    expect(mockOnSelect).toHaveBeenCalledWith(1234);
  });

  it('applies selected styling when isSelected is true', () => {
    // Arrange
    const mockOnSelect = jest.fn();

    // Act
    render(
      <TeamCard
        team={mockTeam}
        onSelect={mockOnSelect}
        isSelected={true}
      />
    );

    // Assert
    const card = screen.getByRole('button');
    expect(card).toHaveClass('selected');
  });

  it('shows detailed information when showDetails is true', () => {
    // Arrange
    const mockOnSelect = jest.fn();

    // Act
    render(
      <TeamCard
        team={mockTeam}
        onSelect={mockOnSelect}
        isSelected={false}
        showDetails={true}
      />
    );

    // Assert
    expect(screen.getByText(/Teleop: 45.2/)).toBeInTheDocument();
    expect(screen.getByText(/Defense: 4.0/)).toBeInTheDocument();
  });
});
```

### API Integration Testing

**API Service Tests**:
```typescript
// src/services/__tests__/apiService.test.ts
import { apiService } from '../apiService';
import { PicklistRequest, PicklistResponse } from '../../types';

// Mock fetch globally
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('API Service', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('generatePicklist', () => {
    it('makes correct API call and returns data', async () => {
      // Arrange
      const mockRequest: PicklistRequest = {
        your_team_number: 1234,
        pick_position: 'first',
        priorities: [
          { metric: 'autonomous_score', weight: 3.0 },
        ],
      };

      const mockResponse: PicklistResponse = {
        status: 'success',
        data: {
          ranked_teams: [
            {
              team_number: 1001,
              rank: 1,
              score: 95.5,
              reasoning: 'Strong performance',
            },
          ],
          summary: 'Analysis complete',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      // Act
      const result = await apiService.generatePicklist(mockRequest);

      // Assert
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/picklist/generate',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(mockRequest),
        })
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('throws error on HTTP error response', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as Response);

      const mockRequest: PicklistRequest = {
        your_team_number: 1234,
        pick_position: 'first',
        priorities: [],
      };

      // Act & Assert
      await expect(apiService.generatePicklist(mockRequest)).rejects.toThrow(
        'HTTP error! status: 500'
      );
    });

    it('throws error on API error response', async () => {
      // Arrange
      const errorResponse = {
        status: 'error',
        error: 'Invalid request data',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => errorResponse,
      } as Response);

      const mockRequest: PicklistRequest = {
        your_team_number: 1234,
        pick_position: 'first',
        priorities: [],
      };

      // Act & Assert
      await expect(apiService.generatePicklist(mockRequest)).rejects.toThrow(
        'Invalid request data'
      );
    });
  });
});
```

---

## End-to-End Testing

### E2E Testing Setup

**Playwright Configuration**:
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

**E2E Test Example**:
```typescript
// e2e/picklist-generation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Picklist Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('complete picklist generation workflow', async ({ page }) => {
    // Navigate to picklist generator
    await page.click('text=Generate Picklist');
    await expect(page).toHaveURL('/picklist');

    // Fill in team number
    await page.fill('input[name="teamNumber"]', '1234');

    // Select pick position
    await page.selectOption('select[name="pickPosition"]', 'first');

    // Add priorities
    await page.click('button:has-text("Add Priority")');
    await page.selectOption('select[name="metric"]', 'autonomous_score');
    await page.fill('input[name="weight"]', '3');

    await page.click('button:has-text("Add Priority")');
    await page.selectOption('select[name="metric"]', 'teleop_avg_points');
    await page.fill('input[name="weight"]', '5');

    // Submit form
    await page.click('button:has-text("Generate Picklist")');

    // Wait for results
    await expect(page.locator('.loading-spinner')).toBeVisible();
    await expect(page.locator('.loading-spinner')).toBeHidden({ timeout: 30000 });

    // Verify results displayed
    await expect(page.locator('.ranked-teams')).toBeVisible();
    await expect(page.locator('.team-card')).toHaveCount.greaterThan(0);

    // Verify team rankings
    const firstTeam = page.locator('.team-card').first();
    await expect(firstTeam.locator('.rank')).toContainText('1');
    await expect(firstTeam.locator('.team-number')).toBeVisible();
    await expect(firstTeam.locator('.reasoning')).toBeVisible();
  });

  test('team comparison workflow', async ({ page }) => {
    // Navigate to team comparison
    await page.goto('/compare');

    // Select multiple teams
    await page.fill('input[name="teamNumbers"]', '1001,1002,1003');

    // Select comparison criteria
    await page.check('input[value="autonomous_score"]');
    await page.check('input[value="teleop_avg_points"]');

    // Submit comparison
    await page.click('button:has-text("Compare Teams")');

    // Wait for comparison results
    await expect(page.locator('.comparison-results')).toBeVisible({ timeout: 30000 });

    // Verify comparison table
    await expect(page.locator('.comparison-table')).toBeVisible();
    await expect(page.locator('.team-row')).toHaveCount(3);

    // Verify AI insights
    await expect(page.locator('.ai-insights')).toBeVisible();
    await expect(page.locator('.recommendation')).toBeVisible();
  });

  test('error handling for invalid inputs', async ({ page }) => {
    await page.goto('/picklist');

    // Try to submit without required fields
    await page.click('button:has-text("Generate Picklist")');

    // Should show validation errors
    await expect(page.locator('.error-message')).toBeVisible();
    await expect(page.locator('text=Team number is required')).toBeVisible();

    // Fill invalid team number
    await page.fill('input[name="teamNumber"]', 'invalid');
    await page.click('button:has-text("Generate Picklist")');

    // Should show validation error
    await expect(page.locator('text=Please enter a valid team number')).toBeVisible();
  });
});
```

---

## Testing Utilities and Helpers

### Test Data Factories

**team_factory.py**:
```python
import factory
from typing import Dict, Any


class TeamDataFactory(factory.DictFactory):
    """Factory for generating test team data."""
    
    team_number = factory.Sequence(lambda n: 1000 + n)
    nickname = factory.Faker('company')
    autonomous_score = factory.Faker('pyfloat', min_value=0, max_value=50)
    teleop_avg_points = factory.Faker('pyfloat', min_value=0, max_value=150)
    endgame_points = factory.Faker('pyfloat', min_value=0, max_value=30)
    defense_rating = factory.Faker('pyfloat', min_value=1, max_value=5)
    reliability_score = factory.Faker('pyfloat', min_value=0.5, max_value=1.0)

    @classmethod
    def create_strong_team(cls, **kwargs) -> Dict[str, Any]:
        """Create a strong-performing team."""
        defaults = {
            'autonomous_score': 45.0,
            'teleop_avg_points': 120.0,
            'endgame_points': 25.0,
            'defense_rating': 4.5,
            'reliability_score': 0.95
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def create_weak_team(cls, **kwargs) -> Dict[str, Any]:
        """Create a weak-performing team."""
        defaults = {
            'autonomous_score': 10.0,
            'teleop_avg_points': 30.0,
            'endgame_points': 5.0,
            'defense_rating': 2.0,
            'reliability_score': 0.6
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def create_batch(cls, size: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Create a batch of teams for testing."""
        return [cls(**kwargs) for _ in range(size)]
```

### Performance Testing Utilities

**performance_helpers.py**:
```python
import time
import psutil
import functools
from typing import Callable, Dict, Any


def measure_performance(func: Callable) -> Callable:
    """Decorator to measure function performance."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Measure memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        # Measure execution time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Measure memory after
        memory_after = process.memory_info().rss
        
        # Store performance metrics
        performance_data = {
            'execution_time': end_time - start_time,
            'memory_used': memory_after - memory_before,
            'function_name': func.__name__
        }
        
        # Add performance data to result if it's a dict
        if isinstance(result, dict):
            result['_performance'] = performance_data
        
        return result
    
    return wrapper


class PerformanceAssertions:
    """Helper class for performance-related assertions."""
    
    @staticmethod
    def assert_response_time(actual_time: float, max_time: float, operation: str = ""):
        """Assert that response time is within acceptable limits."""
        if actual_time > max_time:
            raise AssertionError(
                f"{operation} took {actual_time:.3f}s, "
                f"which exceeds maximum of {max_time:.3f}s"
            )
    
    @staticmethod
    def assert_memory_usage(memory_used: int, max_memory: int, operation: str = ""):
        """Assert that memory usage is within acceptable limits."""
        memory_mb = memory_used / (1024 * 1024)
        max_mb = max_memory / (1024 * 1024)
        
        if memory_used > max_memory:
            raise AssertionError(
                f"{operation} used {memory_mb:.1f}MB, "
                f"which exceeds maximum of {max_mb:.1f}MB"
            )
```

---

## Test Execution and CI/CD

### Running Tests

**Local Development**:
```bash
# Backend tests
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_services/test_data_aggregation_service.py

# Run tests with specific markers
pytest -m "unit"
pytest -m "integration"
pytest -m "slow"

# Run tests in parallel
pytest -n auto  # Requires pytest-xdist

# Frontend tests
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

### Continuous Integration

**GitHub Actions Workflow**:
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml --cov-fail-under=90
        
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Run tests
      run: |
        cd frontend
        npm run test:ci
        
    - name: Run E2E tests
      run: |
        cd frontend
        npm run build
        npm run test:e2e

  integration-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    services:
      database:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up environment
      run: |
        docker-compose -f docker-compose.test.yml up -d
        
    - name: Wait for services
      run: |
        docker-compose -f docker-compose.test.yml exec backend python -c "import time; time.sleep(10)"
        
    - name: Run integration tests
      run: |
        docker-compose -f docker-compose.test.yml exec backend pytest tests/test_integration/
```

---

## Test Quality and Best Practices

### Test Quality Standards

**Test Coverage Requirements**:
- Unit tests: >90% coverage
- Integration tests: >80% coverage  
- Critical paths: 100% coverage
- AI services: Comprehensive mocking with real scenarios

**Test Organization**:
- One test class per service
- Clear test method naming: `test_method_condition_expected`
- AAA pattern: Arrange, Act, Assert
- Independent tests (no shared state)

**Performance Testing**:
- All tests complete in <30 seconds total
- Individual test methods complete in <5 seconds
- Database tests use transactions (rollback after each test)
- Mock external services for speed and reliability

### AI Service Testing Best Practices

**OpenAI API Testing**:
1. Always mock OpenAI client in tests
2. Test different response formats and edge cases
3. Test error handling for API failures
4. Verify token counting and cost calculations
5. Test timeout scenarios

**Prompt Testing**:
1. Test prompt generation with various inputs
2. Verify prompt token counts stay within limits
3. Test context handling and formatting
4. Validate output format specifications

**Response Parsing Testing**:
1. Test valid JSON responses
2. Test malformed JSON handling
3. Test missing required fields
4. Test unexpected response formats
5. Test index mapping accuracy

---

**Next Steps**: [Code Review Guide](CODE_REVIEW.md) | [Feature Development](FEATURE_DEVELOPMENT.md) | [Service Architecture](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)

---

**Last Updated**: June 25, 2025  
**Maintainer**: Development Team  
**Related Documents**: [Coding Standards](CODING_STANDARDS.md), [Development Environment](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md), [AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)