"""
Picklist service test fixtures and configuration.
"""

import json
import pytest
import tempfile
import os
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock

from app.services.picklist.models import (
    PicklistGenerationRequest,
    PickPosition,
    PriorityMetric,
    RankedTeam,
)


@pytest.fixture
def sample_unified_dataset():
    """Complete sample unified dataset for testing."""
    return {
        "event_info": {
            "key": "2025testcomp",
            "name": "Test Competition 2025",
            "year": 2025,
            "start_date": "2025-03-15",
            "end_date": "2025-03-17",
            "location": "Test Venue, Test City, TS"
        },
        "teams": {
            "1001": {
                "team_number": 1001,
                "nickname": "Alpha Robotics",
                "city": "Test City",
                "state_prov": "TS",
                "country": "USA",
                "rookie_year": 2010,
                "scouting_data": {
                    "auto_points": [15, 12, 18, 14, 16, 13, 17],
                    "teleop_points": [25, 30, 22, 28, 24, 26, 29],
                    "endgame_points": [10, 8, 12, 9, 11, 10, 12],
                    "defense_rating": [3, 4, 3, 5, 4, 3, 4],
                    "reliability": [5, 4, 5, 5, 4, 5, 5]
                },
                "statbotics_data": {
                    "epa": 18.5,
                    "auto_epa": 6.2,
                    "teleop_epa": 12.3,
                    "endgame_epa": 4.1,
                    "rp1_epa": 0.65,
                    "rp2_epa": 0.78
                },
                "tba_data": {
                    "wins": 8,
                    "losses": 4,
                    "ties": 0,
                    "rank": 3,
                    "ranking_score": 2.25,
                    "played": 12
                }
            },
            "1002": {
                "team_number": 1002,
                "nickname": "Beta Bots",
                "city": "Another City",
                "state_prov": "AC",
                "country": "USA",
                "rookie_year": 2015,
                "scouting_data": {
                    "auto_points": [10, 8, 12, 9, 11, 10, 13],
                    "teleop_points": [30, 32, 28, 35, 31, 33, 29],
                    "endgame_points": [5, 7, 6, 8, 6, 7, 8],
                    "defense_rating": [4, 5, 4, 4, 5, 4, 5],
                    "reliability": [4, 3, 4, 4, 3, 4, 4]
                },
                "statbotics_data": {
                    "epa": 20.1,
                    "auto_epa": 4.8,
                    "teleop_epa": 15.3,
                    "endgame_epa": 3.2,
                    "rp1_epa": 0.72,
                    "rp2_epa": 0.58
                },
                "tba_data": {
                    "wins": 10,
                    "losses": 2,
                    "ties": 0,
                    "rank": 1,
                    "ranking_score": 2.83,
                    "played": 12
                }
            },
            "1003": {
                "team_number": 1003,
                "nickname": "Gamma Force",
                "city": "Third City",
                "state_prov": "TC",
                "country": "USA",
                "rookie_year": 2012,
                "scouting_data": {
                    "auto_points": [18, 16, 20, 17, 19, 18, 21],
                    "teleop_points": [20, 18, 22, 19, 21, 20, 23],
                    "endgame_points": [12, 10, 15, 11, 13, 12, 14],
                    "defense_rating": [2, 3, 2, 3, 2, 3, 2],
                    "reliability": [5, 5, 4, 5, 5, 4, 5]
                },
                "statbotics_data": {
                    "epa": 19.2,
                    "auto_epa": 7.1,
                    "teleop_epa": 10.8,
                    "endgame_epa": 5.3,
                    "rp1_epa": 0.81,
                    "rp2_epa": 0.44
                },
                "tba_data": {
                    "wins": 7,
                    "losses": 5,
                    "ties": 0,
                    "rank": 5,
                    "ranking_score": 1.92,
                    "played": 12
                }
            }
        },
        "metadata": {
            "generated_at": "2025-06-10T10:00:00Z",
            "total_teams": 3,
            "data_sources": ["scouting", "statbotics", "tba"],
            "scouting_matches": 7,
            "last_updated": "2025-06-10T09:30:00Z"
        }
    }


@pytest.fixture
def temp_dataset_file(sample_unified_dataset):
    """Create temporary dataset file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_unified_dataset, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_priority_metrics():
    """Sample priority metrics for testing."""
    return [
        PriorityMetric(
            id="auto_points",
            name="Autonomous Points",
            weight=2.0,
            description="Points scored during autonomous period"
        ),
        PriorityMetric(
            id="teleop_points",
            name="Teleoperated Points",
            weight=1.5,
            description="Points scored during teleoperated period"
        ),
        PriorityMetric(
            id="endgame_points",
            name="Endgame Points",
            weight=1.2,
            description="Points scored during endgame"
        ),
        PriorityMetric(
            id="epa",
            name="Expected Points Added",
            weight=1.8,
            description="Statbotics EPA metric"
        )
    ]


@pytest.fixture
def sample_picklist_request(sample_priority_metrics):
    """Sample picklist generation request."""
    return PicklistGenerationRequest(
        your_team_number=1001,
        pick_position=PickPosition.FIRST,
        priorities=sample_priority_metrics,
        exclude_teams=[],
        use_batching=False,
        batch_size=10,
        cache_key=None,
        custom_strategy=""
    )


@pytest.fixture
def sample_batch_request(sample_priority_metrics):
    """Sample batch picklist generation request."""
    return PicklistGenerationRequest(
        your_team_number=1001,
        pick_position=PickPosition.SECOND,
        priorities=sample_priority_metrics,
        exclude_teams=[1999],
        use_batching=True,
        batch_size=5,
        cache_key="batch_test_key",
        custom_strategy="Focus on defensive capabilities"
    )


@pytest.fixture
def sample_ranked_teams():
    """Sample ranked teams result."""
    return [
        RankedTeam(
            team_number=1002,
            nickname="Beta Bots",
            score=92.5,
            reasoning="Excellent teleop performance with consistent scoring",
            rank=1,
            tier="S",
            strengths=["Teleop", "Consistency"],
            weaknesses=["Auto"],
            pick_probability=0.95
        ),
        RankedTeam(
            team_number=1003,
            nickname="Gamma Force",
            score=88.3,
            reasoning="Strong autonomous capabilities and reliable endgame",
            rank=2,
            tier="A",
            strengths=["Auto", "Endgame"],
            weaknesses=["Defense"],
            pick_probability=0.87
        ),
        RankedTeam(
            team_number=1001,
            nickname="Alpha Robotics",
            score=85.1,
            reasoning="Well-rounded team with solid all-around performance",
            rank=3,
            tier="A",
            strengths=["Reliability", "Defense"],
            weaknesses=["Peak Performance"],
            pick_probability=0.79
        )
    ]


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    
    # Mock successful response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "p": [
            [1002, 92.5, "Excellent teleop performance"],
            [1003, 88.3, "Strong autonomous capabilities"],
            [1001, 85.1, "Well-rounded team"]
        ]
    })
    mock_response.usage.total_tokens = 1500
    
    client.chat.completions.create.return_value = mock_response
    return client


@pytest.fixture
def mock_data_provider(sample_unified_dataset):
    """Mock unified dataset provider."""
    provider = Mock()
    
    # Mock team retrieval
    def get_team_by_number(team_num):
        return sample_unified_dataset["teams"].get(str(team_num))
    
    provider.get_team_by_number.side_effect = get_team_by_number
    
    # Mock GPT data preparation
    provider.prepare_for_gpt.return_value = [
        {
            "team_number": 1001,
            "nickname": "Alpha Robotics",
            "metrics": {
                "auto_points_avg": 15.0,
                "teleop_points_avg": 26.3,
                "endgame_points_avg": 10.3,
                "epa": 18.5
            }
        },
        {
            "team_number": 1002,
            "nickname": "Beta Bots",
            "metrics": {
                "auto_points_avg": 10.4,
                "teleop_points_avg": 31.1,
                "endgame_points_avg": 6.7,
                "epa": 20.1
            }
        },
        {
            "team_number": 1003,
            "nickname": "Gamma Force",
            "metrics": {
                "auto_points_avg": 18.4,
                "teleop_points_avg": 20.4,
                "endgame_points_avg": 12.4,
                "epa": 19.2
            }
        }
    ]
    
    # Mock game context
    provider.get_game_context.return_value = """
FRC 2025 Game Manual
Rules and Scoring Guide

GAME OVERVIEW:
Teams compete in matches to score points through various game elements.

SCORING:
- Autonomous Period (15 seconds): Higher multiplier for early actions
- Teleoperated Period (135 seconds): Main scoring period
- Endgame (30 seconds): Special scoring opportunities

STRATEGY NOTES:
- Balanced approach between auto and teleop is optimal
- Endgame provides significant point opportunities
- Defense can be valuable but should not compromise own scoring
    """.strip()
    
    return provider


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing."""
    manager = Mock()
    manager.get.return_value = None
    manager.is_processing.return_value = False
    manager.mark_processing.return_value = None
    manager.set.return_value = None
    manager.delete.return_value = None
    manager.clear.return_value = None
    manager.get_stats.return_value = {
        "total_entries": 0,
        "cached_results": 0,
        "processing_operations": 0,
        "hit_rate": 0.0
    }
    return manager


@pytest.fixture
def mock_progress_reporter():
    """Mock progress reporter for testing."""
    reporter = Mock()
    reporter.operation_id = "test_operation_123"
    reporter.update.return_value = None
    reporter.update_batch_progress.return_value = None
    reporter.complete.return_value = None
    reporter.fail.return_value = None
    return reporter


@pytest.fixture
def mock_gpt_strategy():
    """Mock GPT strategy for testing."""
    strategy = AsyncMock()
    strategy.generate_ranking.return_value = [
        {
            "team_number": 1002,
            "nickname": "Beta Bots",
            "score": 92.5,
            "reasoning": "Excellent teleop performance"
        },
        {
            "team_number": 1003,
            "nickname": "Gamma Force",
            "score": 88.3,
            "reasoning": "Strong autonomous capabilities"
        },
        {
            "team_number": 1001,
            "nickname": "Alpha Robotics",
            "score": 85.1,
            "reasoning": "Well-rounded team"
        }
    ]
    return strategy


@pytest.fixture
def mock_token_counter():
    """Mock token counter for testing."""
    counter = Mock()
    counter.count_tokens.return_value = 1500
    counter.estimate_response_tokens.return_value = 500
    counter.check_limits.return_value = True
    return counter


# Factory functions for test data generation

def create_team_data(team_number: int, nickname: str = None, **kwargs) -> Dict[str, Any]:
    """Factory function to create team data."""
    if nickname is None:
        nickname = f"Team {team_number}"
    
    default_data = {
        "team_number": team_number,
        "nickname": nickname,
        "city": "Test City",
        "state_prov": "TS",
        "country": "USA",
        "scouting_data": {
            "auto_points": [10, 12, 8, 15, 11],
            "teleop_points": [25, 30, 22, 28, 26],
            "endgame_points": [8, 10, 6, 12, 9]
        },
        "statbotics_data": {
            "epa": 15.0 + (team_number % 10),
            "auto_epa": 5.0 + (team_number % 5),
            "teleop_epa": 10.0 + (team_number % 8)
        },
        "tba_data": {
            "wins": team_number % 15,
            "losses": (team_number % 10),
            "ties": 0,
            "rank": team_number % 20 + 1
        }
    }
    
    # Update with any provided overrides
    default_data.update(kwargs)
    return default_data


def create_priority_metric(
    id: str,
    name: str = None,
    weight: float = 1.0,
    **kwargs
) -> PriorityMetric:
    """Factory function to create priority metrics."""
    if name is None:
        name = id.replace("_", " ").title()
    
    return PriorityMetric(
        id=id,
        name=name,
        weight=weight,
        **kwargs
    )


def create_picklist_request(
    your_team_number: int = 1001,
    pick_position: PickPosition = PickPosition.FIRST,
    **kwargs
) -> PicklistGenerationRequest:
    """Factory function to create picklist requests."""
    default_priorities = [
        create_priority_metric("auto_points", weight=2.0),
        create_priority_metric("teleop_points", weight=1.5)
    ]
    
    defaults = {
        "priorities": default_priorities,
        "exclude_teams": [],
        "use_batching": False,
        "batch_size": 10
    }
    defaults.update(kwargs)
    
    return PicklistGenerationRequest(
        your_team_number=your_team_number,
        pick_position=pick_position,
        **defaults
    )


def create_large_dataset(team_count: int = 100) -> Dict[str, Any]:
    """Factory function to create large test datasets."""
    teams = {}
    
    for i in range(1000, 1000 + team_count):
        teams[str(i)] = create_team_data(i)
    
    return {
        "event_info": {
            "key": f"2025large{team_count}",
            "name": f"Large Test Event ({team_count} teams)",
            "year": 2025
        },
        "teams": teams,
        "metadata": {
            "generated_at": "2025-06-10T10:00:00Z",
            "total_teams": team_count,
            "data_sources": ["scouting", "statbotics", "tba"]
        }
    }


# Performance test helpers

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


@pytest.fixture
def memory_tracker():
    """Memory usage tracker for testing."""
    import psutil
    import os
    
    class MemoryTracker:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.start_memory = None
            self.end_memory = None
        
        def start(self):
            self.start_memory = self.process.memory_info().rss
        
        def stop(self):
            self.end_memory = self.process.memory_info().rss
        
        @property
        def memory_delta_mb(self):
            if self.start_memory and self.end_memory:
                return (self.end_memory - self.start_memory) / 1024 / 1024
            return None
    
    return MemoryTracker()