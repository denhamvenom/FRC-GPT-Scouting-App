"""
Unit tests for BatchProcessor.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from app.services.picklist.batch_processor import BatchProcessor
from app.services.picklist.models import PicklistGenerationRequest, PickPosition


class TestBatchProcessor:
    """Test BatchProcessor functionality."""
    
    @pytest.fixture
    def mock_strategy(self):
        """Mock strategy for testing."""
        strategy = AsyncMock()
        strategy.generate_ranking.return_value = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Top performer"},
            {"team_number": 1002, "score": 90.0, "reasoning": "Solid choice"},
            {"team_number": 1003, "score": 85.0, "reasoning": "Good backup"},
        ]
        return strategy
    
    @pytest.fixture
    def mock_progress_reporter(self):
        """Mock progress reporter for testing."""
        reporter = Mock()
        reporter.update = Mock()
        reporter.update_batch_progress = Mock()
        return reporter
    
    @pytest.fixture
    def sample_teams_data(self):
        """Sample teams data for testing."""
        return [
            {"team_number": 1001, "nickname": "Team Alpha", "metrics": {"auto": 10, "teleop": 20}},
            {"team_number": 1002, "nickname": "Team Beta", "metrics": {"auto": 8, "teleop": 22}},
            {"team_number": 1003, "nickname": "Team Gamma", "metrics": {"auto": 12, "teleop": 18}},
            {"team_number": 1004, "nickname": "Team Delta", "metrics": {"auto": 9, "teleop": 21}},
            {"team_number": 1005, "nickname": "Team Echo", "metrics": {"auto": 11, "teleop": 19}},
        ]
    
    @pytest.fixture
    def sample_request(self):
        """Sample picklist generation request."""
        return PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[],
            exclude_teams=[],
            use_batching=True,
            batch_size=3,
            reference_teams_count=2,
            final_rerank=True,
        )
    
    def test_batch_processor_initialization(self, mock_strategy):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor(mock_strategy)
        assert processor.strategy == mock_strategy
    
    def test_create_batches(self, mock_strategy, sample_teams_data):
        """Test batch creation logic."""
        processor = BatchProcessor(mock_strategy)
        
        batches = processor._create_batches(sample_teams_data, batch_size=2)
        
        assert len(batches) == 3  # 5 teams with batch size 2 = 3 batches
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2
        assert len(batches[2]) == 1
        
        # Check that all teams are included
        all_teams = [team for batch in batches for team in batch]
        assert len(all_teams) == 5
    
    def test_extract_new_teams(self, mock_strategy):
        """Test extraction of new teams from batch ranking."""
        processor = BatchProcessor(mock_strategy)
        
        batch_ranking = [
            {"team_number": 1001, "score": 95.0},  # Reference team
            {"team_number": 1002, "score": 90.0},  # New team
            {"team_number": 1003, "score": 85.0},  # Reference team
            {"team_number": 1004, "score": 80.0},  # New team
        ]
        
        reference_teams = [
            {"team_number": 1001, "score": 95.0},
            {"team_number": 1003, "score": 85.0},
        ]
        
        new_teams = processor._extract_new_teams(batch_ranking, reference_teams)
        
        assert len(new_teams) == 2
        assert new_teams[0]["team_number"] == 1002
        assert new_teams[1]["team_number"] == 1004
    
    def test_select_reference_teams_top_middle_bottom(self, mock_strategy):
        """Test reference team selection with top/middle/bottom strategy."""
        processor = BatchProcessor(mock_strategy)
        
        ranked_teams = [
            {"team_number": 1001, "score": 95.0},
            {"team_number": 1002, "score": 90.0},
            {"team_number": 1003, "score": 85.0},
            {"team_number": 1004, "score": 80.0},
            {"team_number": 1005, "score": 75.0},
        ]
        
        # Test with 3 reference teams
        references = processor._select_reference_teams(ranked_teams, count=3)
        
        assert len(references) == 3
        assert references[0]["team_number"] == 1001  # Top
        assert references[1]["team_number"] == 1005  # Bottom
        assert references[2]["team_number"] == 1003  # Middle
    
    def test_select_reference_teams_edge_cases(self, mock_strategy):
        """Test reference team selection edge cases."""
        processor = BatchProcessor(mock_strategy)
        
        # Empty list
        references = processor._select_reference_teams([], count=3)
        assert len(references) == 0
        
        # Count is 0
        ranked_teams = [{"team_number": 1001, "score": 95.0}]
        references = processor._select_reference_teams(ranked_teams, count=0)
        assert len(references) == 0
        
        # More reference teams requested than available
        references = processor._select_reference_teams(ranked_teams, count=5)
        assert len(references) == 1
        assert references[0]["team_number"] == 1001
    
    @pytest.mark.asyncio
    async def test_process_in_batches_small_dataset(
        self, mock_strategy, mock_progress_reporter, sample_teams_data, sample_request
    ):
        """Test batch processing with small dataset."""
        processor = BatchProcessor(mock_strategy)
        
        # Use small batch size to force batching
        sample_request.batch_size = 2
        sample_request.reference_teams_count = 1
        
        result = await processor.process_in_batches(
            sample_teams_data,
            sample_request,
            [],  # priorities_dict
            None,  # game_context
            mock_progress_reporter,
        )
        
        # Should have called strategy multiple times for batches
        assert mock_strategy.generate_ranking.call_count >= 2
        
        # Progress reporter should have been called
        mock_progress_reporter.update.assert_called()
        mock_progress_reporter.update_batch_progress.assert_called()
        
        # Should return ranked teams
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_process_with_final_rerank(
        self, mock_strategy, mock_progress_reporter, sample_teams_data, sample_request
    ):
        """Test batch processing with final re-ranking."""
        processor = BatchProcessor(mock_strategy)
        
        # Enable final re-ranking
        sample_request.final_rerank = True
        sample_request.batch_size = 2
        
        await processor.process_in_batches(
            sample_teams_data,
            sample_request,
            [],
            None,
            mock_progress_reporter,
        )
        
        # Should have extra call for final re-ranking
        assert mock_strategy.generate_ranking.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_batch_processing_error_handling(
        self, mock_strategy, mock_progress_reporter, sample_teams_data, sample_request
    ):
        """Test error handling during batch processing."""
        processor = BatchProcessor(mock_strategy)
        
        # Make strategy fail on second call
        mock_strategy.generate_ranking.side_effect = [
            [{"team_number": 1001, "score": 95.0}],  # First call succeeds
            Exception("GPT API error"),  # Second call fails
        ]
        
        with pytest.raises(Exception, match="GPT API error"):
            await processor.process_in_batches(
                sample_teams_data,
                sample_request,
                [],
                None,
                mock_progress_reporter,
            )
    
    @pytest.mark.asyncio
    async def test_final_rerank_failure_recovery(
        self, mock_strategy, mock_progress_reporter, sample_teams_data, sample_request
    ):
        """Test recovery when final re-ranking fails."""
        processor = BatchProcessor(mock_strategy)
        
        original_result = [{"team_number": 1001, "score": 95.0}]
        
        # Mock strategy to return original result for batches but fail on re-rank
        mock_strategy.generate_ranking.side_effect = [
            original_result,  # Batch processing succeeds
            Exception("Re-ranking failed"),  # Final re-rank fails
        ]
        
        sample_request.final_rerank = True
        sample_request.batch_size = 10  # Force single batch
        
        result = await processor._final_rerank(
            original_result,
            sample_request,
            [],
            None,
        )
        
        # Should return original result on failure
        assert result == original_result
    
    def test_validate_batch_parameters_valid(self, mock_strategy):
        """Test validation with valid parameters."""
        processor = BatchProcessor(mock_strategy)
        
        # Should not raise any exception
        processor.validate_batch_parameters(
            batch_size=10,
            reference_count=3,
            total_teams=50
        )
    
    def test_validate_batch_parameters_invalid(self, mock_strategy):
        """Test validation with invalid parameters."""
        processor = BatchProcessor(mock_strategy)
        
        # Batch size too small
        with pytest.raises(ValueError, match="Batch size must be at least 5"):
            processor.validate_batch_parameters(
                batch_size=3,
                reference_count=1,
                total_teams=50
            )
        
        # Negative reference count
        with pytest.raises(ValueError, match="Reference teams count cannot be negative"):
            processor.validate_batch_parameters(
                batch_size=10,
                reference_count=-1,
                total_teams=50
            )
        
        # Reference count too high
        with pytest.raises(ValueError, match="Reference teams count cannot exceed half"):
            processor.validate_batch_parameters(
                batch_size=10,
                reference_count=6,
                total_teams=50
            )
    
    def test_validate_batch_parameters_warnings(self, mock_strategy, caplog):
        """Test validation warnings for edge cases."""
        processor = BatchProcessor(mock_strategy)
        
        # Batch size exceeds total teams
        processor.validate_batch_parameters(
            batch_size=100,
            reference_count=3,
            total_teams=50
        )
        
        assert "Batch size (100) exceeds total teams (50)" in caplog.text