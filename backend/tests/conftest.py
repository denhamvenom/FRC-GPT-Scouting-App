"""
Test configuration and fixtures specific to the tests directory.
"""

import pytest
from typing import Dict, Any, List


@pytest.fixture
def mock_event_data() -> Dict[str, Any]:
    """Mock event data for testing."""
    return {
        "event_key": "2025lake",
        "name": "Lake Superior Regional",
        "year": 2025,
        "week": 1,
        "start_date": "2025-03-06",
        "end_date": "2025-03-09"
    }


@pytest.fixture
def mock_team_performance_data() -> List[Dict[str, Any]]:
    """Mock team performance data for testing."""
    return [
        {
            "team_number": 1234,
            "match_number": 1,
            "auto_points": 25,
            "teleop_points": 100,
            "endgame_points": 15,
            "foul_points": 0,
            "total_points": 140
        },
        {
            "team_number": 1234,
            "match_number": 2,
            "auto_points": 30,
            "teleop_points": 95,
            "endgame_points": 20,
            "foul_points": 5,
            "total_points": 150
        },
        {
            "team_number": 5678,
            "match_number": 1,
            "auto_points": 20,
            "teleop_points": 110,
            "endgame_points": 10,
            "foul_points": 0,
            "total_points": 140
        }
    ]


@pytest.fixture
def mock_unified_dataset() -> Dict[str, Any]:
    """Mock unified dataset for testing."""
    return {
        "teams": [
            {
                "team_number": 1234,
                "nickname": "Test Team 1",
                "rookie_year": 2020,
                "location": "Test City, ST",
                "performance": {
                    "auto_avg": 27.5,
                    "teleop_avg": 97.5,
                    "endgame_avg": 17.5,
                    "total_avg": 145.0
                }
            },
            {
                "team_number": 5678,
                "nickname": "Test Team 2", 
                "rookie_year": 2018,
                "location": "Another City, ST",
                "performance": {
                    "auto_avg": 20.0,
                    "teleop_avg": 110.0,
                    "endgame_avg": 10.0,
                    "total_avg": 140.0
                }
            }
        ],
        "metadata": {
            "event_key": "2025lake",
            "total_teams": 2,
            "data_sources": ["sheets", "tba", "statbotics"],
            "generated_at": "2025-01-06T12:00:00Z"
        }
    }


@pytest.fixture
def mock_gpt_response() -> str:
    """Mock GPT response for picklist generation."""
    return '''
    {
        "r": [
            {"t": 1234, "rk": 1, "s": ["A", "D"], "n": 4.8},
            {"t": 5678, "rk": 2, "s": ["T", "C"], "n": 4.5}
        ],
        "m": {
            "tt": 2,
            "st": "Balanced approach",
            "ex": []
        }
    }
    '''


@pytest.fixture
def mock_sheets_data() -> List[List[str]]:
    """Mock Google Sheets data for testing."""
    return [
        ["Team", "Match", "Auto Points", "Teleop Points", "Endgame Points"],
        ["1234", "1", "25", "100", "15"],
        ["1234", "2", "30", "95", "20"],
        ["5678", "1", "20", "110", "10"]
    ]