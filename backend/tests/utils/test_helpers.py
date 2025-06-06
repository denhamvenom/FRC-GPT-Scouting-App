"""
Testing utilities and helper functions.
"""

import json
import os
import tempfile
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock, patch
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


class TestHelpers:
    """Collection of testing helper methods."""
    
    @staticmethod
    def assert_response_success(response, status_code: int = 200):
        """Assert that a response is successful."""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
        return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
    
    @staticmethod
    def assert_response_error(response, status_code: int = 400):
        """Assert that a response is an error."""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
        return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
    
    @staticmethod
    def create_temp_file(content: str, suffix: str = ".json") -> str:
        """Create a temporary file with given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def create_temp_dir() -> str:
        """Create a temporary directory."""
        return tempfile.mkdtemp()
    
    @staticmethod
    def load_json_file(file_path: str) -> Dict[str, Any]:
        """Load JSON data from a file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_json_file(data: Dict[str, Any], file_path: str) -> None:
        """Save data to a JSON file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def mock_api_response(response_data: Any, status_code: int = 200):
        """Create a mock API response."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = response_data
        mock_response.text = json.dumps(response_data) if isinstance(response_data, (dict, list)) else str(response_data)
        return mock_response
    
    @staticmethod
    def assert_dict_subset(subset: Dict[str, Any], full_dict: Dict[str, Any]):
        """Assert that subset is contained within full_dict."""
        for key, value in subset.items():
            assert key in full_dict, f"Key '{key}' not found in dictionary"
            if isinstance(value, dict) and isinstance(full_dict[key], dict):
                TestHelpers.assert_dict_subset(value, full_dict[key])
            else:
                assert full_dict[key] == value, f"Expected {value} for key '{key}', got {full_dict[key]}"
    
    @staticmethod
    def assert_list_contains(item: Any, target_list: List[Any]):
        """Assert that item is contained in target_list."""
        assert item in target_list, f"Item {item} not found in list"
    
    @staticmethod
    def assert_teams_equal(team1: Dict[str, Any], team2: Dict[str, Any]):
        """Assert that two team objects are equal."""
        assert team1["team_number"] == team2["team_number"]
        assert team1.get("nickname") == team2.get("nickname")
    
    @staticmethod
    def normalize_team_data(team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize team data for comparison."""
        normalized = team_data.copy()
        
        # Convert team_number to int if it's a string
        if "team_number" in normalized:
            normalized["team_number"] = int(normalized["team_number"])
        
        # Normalize performance data
        if "performance" in normalized:
            perf = normalized["performance"]
            for key, value in perf.items():
                if isinstance(value, str):
                    try:
                        perf[key] = float(value)
                    except ValueError:
                        pass
        
        return normalized


class APITestMixin:
    """Mixin class for API testing utilities."""
    
    def post_json(self, client: TestClient, url: str, data: Dict[str, Any], **kwargs):
        """Make a POST request with JSON data."""
        return client.post(url, json=data, **kwargs)
    
    def get_json(self, client: TestClient, url: str, **kwargs):
        """Make a GET request and return JSON response."""
        response = client.get(url, **kwargs)
        return TestHelpers.assert_response_success(response)
    
    def put_json(self, client: TestClient, url: str, data: Dict[str, Any], **kwargs):
        """Make a PUT request with JSON data."""
        return client.put(url, json=data, **kwargs)
    
    def delete_request(self, client: TestClient, url: str, **kwargs):
        """Make a DELETE request."""
        return client.delete(url, **kwargs)


@contextmanager
def mock_external_apis():
    """Context manager to mock all external APIs."""
    with patch("openai.OpenAI") as mock_openai, \
         patch("app.services.tba_client.TBAClient") as mock_tba, \
         patch("app.services.statbotics_client.StatboticsClient") as mock_statbotics, \
         patch("app.services.sheets_service.SheetsService") as mock_sheets:
        
        # Configure OpenAI mock
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"r": [], "m": {}}'))]
        )
        
        # Configure TBA mock
        mock_tba_instance = MagicMock()
        mock_tba.return_value = mock_tba_instance
        mock_tba_instance.get_event_teams.return_value = []
        mock_tba_instance.get_event_matches.return_value = []
        
        # Configure Statbotics mock
        mock_statbotics_instance = MagicMock()
        mock_statbotics.return_value = mock_statbotics_instance
        mock_statbotics_instance.get_team_stats.return_value = {}
        
        # Configure Sheets mock
        mock_sheets_instance = MagicMock()
        mock_sheets.return_value = mock_sheets_instance
        mock_sheets_instance.get_sheet_data.return_value = []
        
        yield {
            "openai": mock_openai_instance,
            "tba": mock_tba_instance,
            "statbotics": mock_statbotics_instance,
            "sheets": mock_sheets_instance
        }


@contextmanager
def temporary_environment(**env_vars):
    """Context manager to temporarily set environment variables."""
    original_env = {}
    
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = str(value)
    
    try:
        yield
    finally:
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def create_mock_database_session():
    """Create a mock database session for testing."""
    mock_session = MagicMock()
    mock_session.query.return_value = mock_session
    mock_session.filter.return_value = mock_session
    mock_session.first.return_value = None
    mock_session.all.return_value = []
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.close.return_value = None
    return mock_session


def assert_valid_picklist(picklist_data: Dict[str, Any]):
    """Assert that picklist data has valid structure."""
    assert "rankings" in picklist_data
    assert "metadata" in picklist_data
    
    rankings = picklist_data["rankings"]
    assert isinstance(rankings, list)
    
    for ranking in rankings:
        assert "team" in ranking
        assert "rank" in ranking
        assert isinstance(ranking["team"], int)
        assert isinstance(ranking["rank"], int)
    
    metadata = picklist_data["metadata"]
    assert "total_teams" in metadata
    assert isinstance(metadata["total_teams"], int)


def assert_valid_alliance_data(alliance_data: Dict[str, Any]):
    """Assert that alliance selection data has valid structure."""
    assert "alliances" in alliance_data
    assert "available_teams" in alliance_data
    
    alliances = alliance_data["alliances"]
    assert isinstance(alliances, list)
    
    for alliance in alliances:
        assert "captain" in alliance
        assert isinstance(alliance["captain"], int)
    
    available_teams = alliance_data["available_teams"]
    assert isinstance(available_teams, list)
    assert all(isinstance(team, int) for team in available_teams)


# Pytest fixtures using the helpers
@pytest.fixture
def api_test_helper():
    """Provide API testing helper."""
    return APITestMixin()


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    temp_files = []
    
    def _create_temp_file(content: str = "", suffix: str = ".json"):
        file_path = TestHelpers.create_temp_file(content, suffix)
        temp_files.append(file_path)
        return file_path
    
    yield _create_temp_file
    
    # Cleanup
    for file_path in temp_files:
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            pass