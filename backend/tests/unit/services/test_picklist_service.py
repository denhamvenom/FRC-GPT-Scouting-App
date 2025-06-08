"""
Unit tests for the refactored picklist service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.picklist import PicklistService
from app.services.picklist.models import (
    PicklistGenerationRequest,
    PickPosition,
    PriorityMetric,
)
from app.services.picklist.exceptions import (
    PicklistValidationError,
    TeamNotFoundException,
)


@pytest.fixture
def mock_data_provider():
    """Mock team data provider."""
    provider = Mock()
    provider.get_team_by_number.return_value = {
        "team_number": 1234,
        "nickname": "Test Team",
        "metrics": {"auto_points": 15.5, "teleop_points": 25.0},
    }
    provider.prepare_for_gpt.return_value = [
        {
            "team_number": 1234,
            "nickname": "Test Team",
            "metrics": {"auto_points": 15.5, "teleop_points": 25.0},
        },
        {
            "team_number": 5678,
            "nickname": "Another Team",
            "metrics": {"auto_points": 12.0, "teleop_points": 30.0},
        },
    ]
    provider.get_game_context.return_value = "Test game context"
    return provider


@pytest.fixture
def mock_strategy():
    """Mock picklist strategy."""
    strategy = AsyncMock()
    strategy.generate_ranking.return_value = [
        {
            "team_number": 5678,
            "nickname": "Another Team",
            "score": 85.0,
            "reasoning": "High scoring potential",
        },
        {
            "team_number": 1234,
            "nickname": "Test Team",
            "score": 75.0,
            "reasoning": "Consistent performance",
        },
    ]
    return strategy


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager."""
    manager = Mock()
    manager.get.return_value = None
    manager.is_processing.return_value = False
    return manager


@pytest.fixture
def picklist_service(mock_data_provider, mock_strategy, mock_cache_manager):
    """Create picklist service with mocked dependencies."""
    service = PicklistService("/fake/path.json")
    service.data_provider = mock_data_provider
    service.strategy = mock_strategy
    service.cache_manager = mock_cache_manager
    return service


@pytest.fixture
def sample_request():
    """Sample picklist generation request."""
    return PicklistGenerationRequest(
        your_team_number=1234,
        pick_position=PickPosition.FIRST,
        priorities=[
            PriorityMetric(id="auto_points", name="Auto Points", weight=2.0),
            PriorityMetric(id="teleop_points", name="Teleop Points", weight=1.5),
        ],
    )


@pytest.mark.asyncio
async def test_generate_picklist_success(picklist_service, sample_request):
    """Test successful picklist generation."""
    result = await picklist_service.generate_picklist(sample_request)

    assert result.status == "success"
    assert len(result.picklist) == 2
    assert result.picklist[0].team_number == 5678
    assert result.picklist[0].score == 85.0
    assert result.picklist[1].team_number == 1234
    assert result.picklist[1].score == 75.0


@pytest.mark.asyncio
async def test_generate_picklist_with_cache_hit(picklist_service, sample_request):
    """Test picklist generation with cache hit."""
    from app.services.picklist.models import RankedTeam
    
    cached_result = {
        "status": "success",
        "picklist": [
            RankedTeam(
                team_number=1111,
                nickname="Cached Team",
                score=90.0,
                reasoning="From cache",
                rank=1,
            )
        ],
        "analysis": {},
        "missing_team_numbers": [],
        "performance": {},
    }
    picklist_service.cache_manager.get.return_value = cached_result

    result = await picklist_service.generate_picklist(sample_request)

    assert result.status == "success"
    assert len(result.picklist) == 1
    assert result.picklist[0].team_number == 1111
    picklist_service.strategy.generate_ranking.assert_not_called()


@pytest.mark.asyncio
async def test_generate_picklist_team_not_found(picklist_service, sample_request):
    """Test picklist generation when your team is not found."""
    picklist_service.data_provider.get_team_by_number.return_value = None

    with pytest.raises(TeamNotFoundException) as exc_info:
        await picklist_service.generate_picklist(sample_request)

    assert exc_info.value.team_number == 1234


@pytest.mark.asyncio
async def test_generate_picklist_no_priorities(picklist_service):
    """Test picklist generation with no priorities."""
    request = PicklistGenerationRequest(
        your_team_number=1234,
        pick_position=PickPosition.FIRST,
        priorities=[],
    )

    with pytest.raises(PicklistValidationError) as exc_info:
        await picklist_service.generate_picklist(request)

    assert "No priority metrics provided" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_picklist_with_excluded_teams(picklist_service, sample_request):
    """Test picklist generation with excluded teams."""
    sample_request.exclude_teams = [9999]
    
    result = await picklist_service.generate_picklist(sample_request)

    assert result.status == "success"
    picklist_service.data_provider.prepare_for_gpt.assert_called_once_with([9999])


@pytest.mark.asyncio
async def test_generate_picklist_with_batching(picklist_service, sample_request):
    """Test picklist generation with batch processing."""
    sample_request.use_batching = True
    sample_request.batch_size = 1  # Force batching with small size
    
    # Mock more teams to trigger batching
    picklist_service.data_provider.prepare_for_gpt.return_value = [
        {"team_number": i, "nickname": f"Team {i}", "metrics": {}}
        for i in range(1000, 1010)
    ]

    result = await picklist_service.generate_picklist(sample_request)

    assert result.status == "success"
    # Strategy should be called multiple times for batches
    assert picklist_service.strategy.generate_ranking.call_count > 1


def test_validate_request_invalid_batch_size(picklist_service):
    """Test request validation with invalid batch size."""
    request = PicklistGenerationRequest(
        your_team_number=1234,
        pick_position=PickPosition.FIRST,
        priorities=[PriorityMetric(id="test", name="Test", weight=1.0)],
        batch_size=3,  # Too small
    )

    with pytest.raises(PicklistValidationError) as exc_info:
        picklist_service._validate_request(request)

    assert "Batch size must be at least 5" in str(exc_info.value)


def test_create_cache_key(picklist_service, sample_request):
    """Test cache key creation."""
    key = picklist_service._create_cache_key(sample_request)

    assert "1234" in key  # Team number
    assert "first" in key  # Pick position
    assert "auto_points:2.0" in key  # Priority
    assert "teleop_points:1.5" in key  # Priority


def test_select_reference_teams(picklist_service):
    """Test reference team selection."""
    teams = [
        {"team_number": i, "score": 100 - i}
        for i in range(1, 11)
    ]

    # Test with 3 reference teams
    refs = picklist_service._select_reference_teams(teams, 3)
    assert len(refs) == 3
    assert refs[0]["team_number"] == 1  # Top
    assert refs[1]["team_number"] == 10  # Bottom
    assert refs[2]["team_number"] == 6  # Middle (index 5 for 10 items)

    # Test with more teams requested than available
    refs = picklist_service._select_reference_teams(teams[:2], 5)
    assert len(refs) == 2