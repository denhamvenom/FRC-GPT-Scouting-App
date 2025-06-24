# Testing Standards and Guidelines

## Document Version
- **Version**: 1.0
- **Date**: 2025-06-22
- **Purpose**: Define comprehensive testing standards for refactored code

## Overview

This document establishes testing standards to ensure code quality, prevent regressions, and enable safe refactoring. All refactored code must meet these standards before merging.

## Testing Philosophy

1. **Test Behavior, Not Implementation**: Tests should verify what code does, not how
2. **Fast and Reliable**: Tests must run quickly and consistently
3. **Isolated**: Each test should be independent
4. **Readable**: Tests serve as documentation
5. **Comprehensive**: Cover happy paths, edge cases, and error conditions

## Test Structure

### Directory Organization
```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── unit/                    # Unit tests (isolated components)
│   │   ├── domain/             
│   │   │   ├── models/
│   │   │   └── services/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/             # Integration tests (multiple components)
│   │   ├── api/                # API endpoint tests
│   │   ├── database/           # Database integration tests
│   │   └── external/           # External service tests
│   ├── e2e/                    # End-to-end tests (full workflows)
│   └── performance/            # Performance benchmarks
```

### File Naming Convention
- Unit tests: `test_[module_name].py`
- Integration tests: `test_[feature]_integration.py`
- E2E tests: `test_[workflow]_e2e.py`
- Performance tests: `bench_[component].py`

## Test Categories

### Unit Tests
Test individual functions, methods, and classes in isolation.

```python
# tests/unit/domain/models/test_team.py
import pytest
from src.domain.models.team import Team
from pydantic import ValidationError

class TestTeamModel:
    """Test Team domain model."""
    
    def test_team_creation_with_valid_data(self):
        """Team can be created with valid data."""
        team = Team(
            team_number=254,
            nickname="The Cheesy Poofs",
            stats={"auto_points": 15.5, "teleop_points": 32.0}
        )
        assert team.team_number == 254
        assert team.nickname == "The Cheesy Poofs"
        assert team.stats["auto_points"] == 15.5
    
    def test_team_validation_rejects_invalid_number(self):
        """Team number must be positive integer."""
        with pytest.raises(ValidationError) as exc_info:
            Team(
                team_number=-1,
                nickname="Invalid Team",
                stats={}
            )
        assert "team_number" in str(exc_info.value)
    
    @pytest.mark.parametrize("team_number,expected", [
        (1, True),
        (9999, True),
        (0, False),
        (10000, False),
    ])
    def test_team_number_bounds(self, team_number, expected):
        """Team number must be between 1 and 9999."""
        if expected:
            team = Team(team_number=team_number, nickname="Test", stats={})
            assert team.team_number == team_number
        else:
            with pytest.raises(ValidationError):
                Team(team_number=team_number, nickname="Test", stats={})
```

### Integration Tests
Test interactions between multiple components.

```python
# tests/integration/api/test_picklist_integration.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

class TestPicklistAPIIntegration:
    """Test picklist API with service integration."""
    
    @pytest.fixture
    def mock_unified_dataset(self):
        """Mock unified dataset for testing."""
        return {
            "teams": {
                "254": {"team_number": 254, "stats": {...}},
                "1114": {"team_number": 1114, "stats": {...}}
            },
            "year": 2025,
            "event_key": "2025test"
        }
    
    def test_generate_picklist_full_flow(self, client: TestClient, mock_unified_dataset):
        """Test complete picklist generation flow."""
        with patch("app.services.unified_dataset_service.load_dataset") as mock_load:
            mock_load.return_value = mock_unified_dataset
            
            response = client.post(
                "/api/v1/picklist/generate",
                json={
                    "strategy": "balanced scoring and defense",
                    "excluded_teams": [180, 971]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "picklist" in data
            assert isinstance(data["picklist"], list)
            assert all(isinstance(t, int) for t in data["picklist"])
            assert 180 not in data["picklist"]  # Excluded team
    
    @pytest.mark.slow
    def test_picklist_performance_with_large_dataset(self, client: TestClient):
        """Picklist generation completes within SLA for large events."""
        # Generate large mock dataset (100+ teams)
        large_dataset = self._generate_large_dataset(team_count=120)
        
        with patch("app.services.unified_dataset_service.load_dataset") as mock_load:
            mock_load.return_value = large_dataset
            
            import time
            start = time.time()
            
            response = client.post(
                "/api/v1/picklist/generate",
                json={"strategy": "high scoring"}
            )
            
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration < 5.0  # Must complete within 5 seconds
```

### End-to-End Tests
Test complete user workflows.

```python
# tests/e2e/test_scouting_workflow_e2e.py
import pytest
from playwright.sync_api import Page, expect

class TestScoutingWorkflowE2E:
    """Test complete scouting workflow from data entry to picklist."""
    
    @pytest.mark.e2e
    def test_full_scouting_flow(self, page: Page, test_server_url: str):
        """User can complete full scouting workflow."""
        # Navigate to app
        page.goto(test_server_url)
        
        # Step 1: Configure event
        page.click("text=Setup")
        page.fill("#event-key", "2025test")
        page.click("button:has-text('Save Configuration')")
        expect(page.locator(".success-message")).to_be_visible()
        
        # Step 2: Enter scouting data
        page.click("text=Data Entry")
        page.fill("#team-number", "254")
        page.fill("#auto-points", "15")
        page.fill("#teleop-points", "35")
        page.click("button:has-text('Submit')")
        
        # Step 3: Validate data
        page.click("text=Validation")
        expect(page.locator("text=No outliers detected")).to_be_visible()
        
        # Step 4: Generate picklist
        page.click("text=Picklist")
        page.fill("#strategy", "High scoring autonomous")
        page.click("button:has-text('Generate')")
        
        # Verify picklist generated
        expect(page.locator(".picklist-results")).to_be_visible()
        expect(page.locator(".team-rank").first).to_contain_text("254")
```

### Performance Tests
Benchmark critical operations.

```python
# tests/performance/bench_picklist_generation.py
import pytest
import time
from statistics import mean, stdev

class BenchmarkPicklistGeneration:
    """Benchmark picklist generation performance."""
    
    @pytest.mark.benchmark
    def test_picklist_generation_speed(self, benchmark, picklist_service, large_dataset):
        """Picklist generation performance with 100 teams."""
        def generate():
            return picklist_service.generate_picklist(
                teams=large_dataset["teams"],
                strategy="balanced"
            )
        
        # Run benchmark
        result = benchmark(generate)
        
        # Assert performance requirements
        assert result.stats.mean < 2.0  # Average under 2 seconds
        assert result.stats.max < 3.0   # Max under 3 seconds
    
    @pytest.mark.benchmark
    def test_memory_usage(self, picklist_service, large_dataset):
        """Memory usage stays reasonable during generation."""
        import tracemalloc
        
        tracemalloc.start()
        
        # Generate picklist multiple times
        for _ in range(10):
            picklist_service.generate_picklist(
                teams=large_dataset["teams"],
                strategy="different strategy each time"
            )
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Assert memory usage under 100MB
        assert peak / 1024 / 1024 < 100
```

## Test Fixtures

### Common Fixtures (conftest.py)
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_db):
    """Create clean database session for each test."""
    connection = test_db.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API responses."""
    def _mock_response(content):
        return Mock(
            choices=[Mock(message=Mock(content=content))],
            usage=Mock(total_tokens=100)
        )
    return _mock_response

@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "254": {
            "team_number": 254,
            "nickname": "The Cheesy Poofs",
            "stats": {
                "auto_points_avg": 15.5,
                "teleop_points_avg": 32.0,
                "endgame_points_avg": 8.5,
                "total_points_avg": 56.0,
                "win_rate": 0.85
            }
        },
        "1114": {
            "team_number": 1114,
            "nickname": "Simbotics",
            "stats": {
                "auto_points_avg": 14.0,
                "teleop_points_avg": 35.5,
                "endgame_points_avg": 10.0,
                "total_points_avg": 59.5,
                "win_rate": 0.90
            }
        }
    }
```

### Factory Functions
```python
# tests/factories.py
from datetime import datetime
import factory
from factory import fuzzy

class TeamFactory(factory.Factory):
    """Factory for creating test teams."""
    class Meta:
        model = Team
    
    team_number = factory.Sequence(lambda n: n + 1)
    nickname = factory.Faker("company")
    stats = factory.Dict({
        "auto_points_avg": fuzzy.FuzzyFloat(0, 20),
        "teleop_points_avg": fuzzy.FuzzyFloat(0, 40),
        "endgame_points_avg": fuzzy.FuzzyFloat(0, 15),
    })

class MatchFactory(factory.Factory):
    """Factory for creating test matches."""
    class Meta:
        model = Match
    
    match_key = factory.LazyAttribute(
        lambda obj: f"2025test_qm{obj.match_number}"
    )
    match_number = factory.Sequence(lambda n: n + 1)
    red_alliance = factory.List([
        factory.SubFactory(TeamFactory) for _ in range(3)
    ])
    blue_alliance = factory.List([
        factory.SubFactory(TeamFactory) for _ in range(3)
    ])
```

## Test Patterns

### Arrange-Act-Assert (AAA)
```python
def test_calculate_team_score():
    # Arrange
    team = Team(team_number=254, stats={"total_avg": 55.5})
    weights = {"total_avg": 1.0}
    
    # Act
    score = calculate_team_score(team, weights)
    
    # Assert
    assert score == 55.5
```

### Given-When-Then (BDD Style)
```python
def test_picklist_excludes_unavailable_teams():
    # Given a list of teams and some are unavailable
    all_teams = [team1, team2, team3]
    unavailable = {team2.team_number}
    
    # When generating picklist
    picklist = generate_picklist(all_teams, excluded=unavailable)
    
    # Then unavailable teams are not included
    assert team2.team_number not in picklist
    assert len(picklist) == 2
```

### Table-Driven Tests
```python
@pytest.mark.parametrize("input_value,expected_output,should_raise", [
    # Valid inputs
    ("2025arc", "2025arc", False),
    ("2025LAKE", "2025lake", False),
    ("2025_test", "2025test", False),
    
    # Invalid inputs
    ("", None, True),
    ("invalid", None, True),
    ("12345", None, True),
])
def test_normalize_event_key(input_value, expected_output, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            normalize_event_key(input_value)
    else:
        assert normalize_event_key(input_value) == expected_output
```

## Mocking Guidelines

### Mock External Services
```python
@patch("app.services.tba_client.TBAClient")
def test_fetch_teams_handles_api_error(mock_tba):
    # Arrange
    mock_tba.get_teams.side_effect = APIError("TBA is down")
    
    # Act & Assert
    with pytest.raises(ServiceUnavailable):
        fetch_teams_for_event("2025test")
```

### Don't Mock What You Own
```python
# Bad - mocking internal service
@patch("app.services.team_service.TeamService.get_team")
def test_bad_example(mock_get_team):
    mock_get_team.return_value = Team(...)
    
# Good - use real service with test data
def test_good_example(db_session):
    # Insert test data
    team = TeamFactory.create()
    db_session.add(team)
    db_session.commit()
    
    # Use real service
    service = TeamService(db_session)
    result = service.get_team(team.team_number)
    assert result.team_number == team.team_number
```

## Coverage Requirements

### Minimum Coverage by Type
- Unit tests: 90% coverage
- Integration tests: 80% coverage  
- Critical paths: 100% coverage
- Overall project: 80% coverage

### Coverage Configuration
```ini
# .coveragerc
[run]
source = backend/src
omit = 
    */tests/*
    */migrations/*
    */__init__.py
    */config.py

[report]
precision = 2
show_missing = True
skip_covered = True

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

### Enforcement
```yaml
# .github/workflows/tests.yml
- name: Run tests with coverage
  run: |
    pytest --cov=backend/src --cov-report=xml --cov-fail-under=80
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
```

## Test Execution

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend/src --cov-report=html

# Run specific test file
pytest tests/unit/domain/models/test_team.py

# Run specific test
pytest tests/unit/domain/models/test_team.py::TestTeamModel::test_team_creation_with_valid_data

# Run by marker
pytest -m "not slow"  # Skip slow tests
pytest -m e2e         # Only E2E tests

# Run with verbose output
pytest -v

# Run with debugging
pytest -vv --tb=short --pdb  # Drop to debugger on failure

# Run in parallel
pytest -n auto  # Use all CPU cores
```

### Test Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_large_dataset_processing():
    pass

# Mark flaky tests (temporary)
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_external_api_integration():
    pass

# Mark tests requiring specific conditions
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires API key")
def test_gpt_integration():
    pass

# Custom markers in pytest.ini
[tool:pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    e2e: marks tests as end-to-end
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    benchmark: marks performance benchmark tests
```

## Test Documentation

### Test Docstrings
```python
def test_complex_business_logic():
    """
    Test that complex picklist ranking handles edge cases.
    
    This test verifies:
    1. Teams with no data are ranked last
    2. Tied scores are broken by team number
    3. Excluded teams are filtered out
    4. Ranking is stable (same input = same output)
    
    See: https://github.com/team/repo/issues/123
    """
    pass
```

### Test Comments
```python
def test_performance_critical_operation():
    # This operation must complete in <100ms to meet UX requirements
    # Previous implementation took 500ms due to N+1 queries
    # Current implementation uses single query with joins
    
    start = time.time()
    result = perform_operation()
    duration = time.time() - start
    
    assert duration < 0.1  # 100ms
```

## Continuous Integration

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: ["-x", "--tb=short"]
```

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
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
          
      - name: Run tests
        run: |
          pytest \
            --cov=backend/src \
            --cov-report=xml \
            --cov-report=term-missing \
            --junit-xml=test-results.xml
            
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```python
   # Add to conftest.py
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   ```

2. **Async Test Issues**
   ```python
   # Use pytest-asyncio
   @pytest.mark.asyncio
   async def test_async_operation():
       result = await async_function()
       assert result is not None
   ```

3. **Database Test Isolation**
   ```python
   # Use transactions that rollback
   @pytest.fixture
   def isolated_db(db_session):
       yield db_session
       db_session.rollback()
   ```

---

**Remember**: Good tests enable confident refactoring. Invest time in test quality and it will pay dividends throughout the project.