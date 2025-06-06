"""
Sample test data for use across tests.
"""

from typing import Dict, List, Any
from datetime import datetime


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_team_data(team_number: int = 1234, **kwargs) -> Dict[str, Any]:
        """Create a test team data object."""
        defaults = {
            "team_number": team_number,
            "nickname": f"Test Team {team_number}",
            "rookie_year": 2020,
            "location": "Test City, ST",
            "website": f"https://team{team_number}.com"
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_match_data(match_number: int = 1, **kwargs) -> Dict[str, Any]:
        """Create a test match data object."""
        defaults = {
            "match_number": match_number,
            "comp_level": "qm",
            "set_number": 1,
            "alliances": {
                "red": {
                    "team_keys": ["frc1234", "frc5678", "frc9012"],
                    "score": 150
                },
                "blue": {
                    "team_keys": ["frc3456", "frc7890", "frc1357"], 
                    "score": 140
                }
            },
            "winning_alliance": "red"
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_performance_data(team_number: int = 1234, **kwargs) -> Dict[str, Any]:
        """Create test performance data for a team."""
        defaults = {
            "team_number": team_number,
            "auto_points": 25.0,
            "teleop_points": 100.0,
            "endgame_points": 15.0,
            "foul_points": 0.0,
            "total_points": 140.0,
            "ranking_points": 2.0
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_picklist_data(**kwargs) -> Dict[str, Any]:
        """Create test picklist data."""
        defaults = {
            "rankings": [
                {
                    "team": 1234,
                    "rank": 1,
                    "strengths": ["Auto", "Defense"],
                    "notes": 4.8
                },
                {
                    "team": 5678,
                    "rank": 2,
                    "strengths": ["Teleop", "Climbing"],
                    "notes": 4.5
                }
            ],
            "metadata": {
                "total_teams": 2,
                "strategy": "Balanced approach focusing on versatility",
                "excluded_teams": [],
                "generated_at": datetime.now().isoformat()
            }
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_alliance_selection_data(**kwargs) -> Dict[str, Any]:
        """Create test alliance selection data."""
        defaults = {
            "alliances": [
                {
                    "captain": 1234,
                    "first_pick": 5678,
                    "second_pick": 9012,
                    "declined": []
                },
                {
                    "captain": 3456,
                    "first_pick": 7890,
                    "second_pick": None,
                    "declined": [1357]
                }
            ],
            "available_teams": [2468, 1357, 1111],
            "current_pick": "second",
            "current_alliance": 1,
            "round": 2
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_event_data(event_key: str = "2025lake", **kwargs) -> Dict[str, Any]:
        """Create test event data."""
        defaults = {
            "event_key": event_key,
            "name": "Lake Superior Regional",
            "year": 2025,
            "week": 1,
            "start_date": "2025-03-06",
            "end_date": "2025-03-09",
            "location": "Duluth, MN",
            "district": None
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_sheets_data() -> List[List[str]]:
        """Create sample Google Sheets data."""
        return [
            # Header row
            [
                "Team Number", "Match Number", "Auto Points", "Teleop Points",
                "Endgame Points", "Foul Points", "Defense Rating", "Notes"
            ],
            # Data rows
            ["1234", "1", "25", "100", "15", "0", "4", "Strong auto"],
            ["1234", "2", "30", "95", "20", "5", "3", "Good teleop"],
            ["5678", "1", "20", "110", "10", "0", "5", "Excellent defense"],
            ["5678", "2", "22", "105", "12", "2", "4", "Consistent performer"],
            ["9012", "1", "35", "80", "25", "0", "2", "Auto specialist"],
            ["9012", "2", "32", "85", "22", "3", "3", "Reliable climber"]
        ]
    
    @staticmethod
    def create_statbotics_data(team_number: int = 1234, **kwargs) -> Dict[str, Any]:
        """Create test Statbotics data."""
        defaults = {
            "team": team_number,
            "year": 2025,
            "epa": {
                "total_points": {"mean": 150.5, "sd": 25.2},
                "auto_points": {"mean": 27.5, "sd": 8.1},
                "teleop_points": {"mean": 98.0, "sd": 20.3},
                "endgame_points": {"mean": 15.0, "sd": 5.7}
            },
            "wins": 8,
            "losses": 4,
            "ties": 0,
            "total_matches": 12
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_tba_team_data(team_number: int = 1234, **kwargs) -> Dict[str, Any]:
        """Create TBA team data."""
        defaults = {
            "key": f"frc{team_number}",
            "team_number": team_number,
            "nickname": f"Test Team {team_number}",
            "name": f"Test Team {team_number} Long Name",
            "city": "Test City",
            "state_prov": "ST",
            "country": "USA",
            "rookie_year": 2020,
            "website": f"https://team{team_number}.com"
        }
        defaults.update(kwargs)
        return defaults


# Predefined test datasets
SAMPLE_TEAMS = [
    TestDataFactory.create_team_data(1234, nickname="Alpha Bots"),
    TestDataFactory.create_team_data(5678, nickname="Beta Builders"),
    TestDataFactory.create_team_data(9012, nickname="Gamma Gears"),
    TestDataFactory.create_team_data(3456, nickname="Delta Drivers"),
    TestDataFactory.create_team_data(7890, nickname="Epsilon Engineers")
]

SAMPLE_MATCHES = [
    TestDataFactory.create_match_data(1),
    TestDataFactory.create_match_data(2),
    TestDataFactory.create_match_data(3)
]

SAMPLE_PERFORMANCE_DATA = [
    TestDataFactory.create_performance_data(1234, auto_points=25, teleop_points=100),
    TestDataFactory.create_performance_data(5678, auto_points=30, teleop_points=95),
    TestDataFactory.create_performance_data(9012, auto_points=35, teleop_points=80)
]