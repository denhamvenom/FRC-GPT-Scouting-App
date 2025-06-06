"""
Global test configuration and fixtures for FRC GPT Scouting App backend tests.
"""

import os
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

# Try to import optional dependencies
try:
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# Try to import app modules if available
try:
    from app.database.db import Base, get_db
    from app.main import app
    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine using SQLite in memory."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Mock common OpenAI responses
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"rankings": [{"team": 1234, "rank": 1}]}'
                    )
                )
            ]
        )
        
        yield mock_instance


@pytest.fixture(scope="function")
def mock_tba_client():
    """Mock The Blue Alliance client for testing."""
    with patch("app.services.tba_client.TBAClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Mock common TBA responses
        mock_instance.get_event_teams.return_value = [
            {"team_number": 1234, "nickname": "Test Team 1"},
            {"team_number": 5678, "nickname": "Test Team 2"}
        ]
        
        mock_instance.get_event_matches.return_value = [
            {
                "match_number": 1,
                "alliances": {
                    "red": {"team_keys": ["frc1234", "frc5678", "frc9012"]},
                    "blue": {"team_keys": ["frc3456", "frc7890", "frc1357"]}
                }
            }
        ]
        
        yield mock_instance


@pytest.fixture(scope="function")
def mock_statbotics_client():
    """Mock Statbotics client for testing."""
    with patch("app.services.statbotics_client.StatboticsClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Mock common Statbotics responses
        mock_instance.get_team_stats.return_value = {
            "team": 1234,
            "epa": {"total_points": {"mean": 150.5}},
            "auto_points": {"mean": 25.0},
            "teleop_points": {"mean": 100.0}
        }
        
        yield mock_instance


@pytest.fixture(scope="function")
def mock_google_sheets():
    """Mock Google Sheets service for testing."""
    with patch("app.services.sheets_service.SheetsService") as mock_service:
        mock_instance = MagicMock()
        mock_service.return_value = mock_instance
        
        # Mock common Google Sheets responses
        mock_instance.get_sheet_data.return_value = [
            ["Team", "Match", "Auto Points", "Teleop Points"],
            ["1234", "1", "25", "100"],
            ["5678", "1", "30", "95"]
        ]
        
        yield mock_instance


@pytest.fixture(scope="function")
def sample_team_data():
    """Sample team data for testing."""
    return [
        {
            "team_number": 1234,
            "nickname": "Test Team 1",
            "auto_points": 25.0,
            "teleop_points": 100.0,
            "total_points": 150.0,
            "epa": 150.5
        },
        {
            "team_number": 5678,
            "nickname": "Test Team 2",
            "auto_points": 30.0,
            "teleop_points": 95.0,
            "total_points": 140.0,
            "epa": 145.2
        }
    ]


@pytest.fixture(scope="function")
def sample_picklist_data():
    """Sample picklist data for testing."""
    return {
        "rankings": [
            {"team": 1234, "rank": 1, "strengths": ["Auto", "Defense"]},
            {"team": 5678, "rank": 2, "strengths": ["Teleop", "Climbing"]}
        ],
        "metadata": {
            "total_teams": 2,
            "strategy": "Balanced approach focusing on auto and teleop",
            "excluded_teams": []
        }
    }


@pytest.fixture(scope="function")
def sample_alliance_data():
    """Sample alliance selection data for testing."""
    return {
        "alliances": [
            {
                "captain": 1234,
                "picks": [5678, 9012],
                "declined": []
            },
            {
                "captain": 3456,
                "picks": [7890],
                "declined": [1357]
            }
        ],
        "available_teams": [2468, 1357],
        "current_pick": 1,
        "round": 2
    }


@pytest.fixture(scope="function")
def env_vars():
    """Set up environment variables for testing."""
    test_env = {
        "OPENAI_API_KEY": "test-openai-key",
        "TBA_API_KEY": "test-tba-key",
        "GOOGLE_SHEET_ID": "test-sheet-id",
        "GOOGLE_SERVICE_ACCOUNT_FILE": "test-service-account.json"
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_env
    
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(autouse=True)
def reset_global_cache():
    """Reset global cache before each test."""
    try:
        from app.services.global_cache import cache as global_cache
        original_cache = global_cache.copy()
        global_cache.clear()
        yield
        global_cache.clear()
        global_cache.update(original_cache)
    except ImportError:
        # If cache module doesn't exist or has different structure, skip
        yield


# Custom markers for different test types
pytest_plugins = ["pytest_asyncio"]