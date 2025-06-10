"""
Unit tests for UnifiedDatasetProvider.
"""

import json
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open

from app.services.picklist.core.team_data_provider import UnifiedDatasetProvider
from app.services.picklist.exceptions import DatasetLoadError, TeamNotFoundException


class TestUnifiedDatasetProvider:
    """Test UnifiedDatasetProvider functionality."""
    
    @pytest.fixture
    def sample_dataset(self):
        """Sample unified dataset for testing."""
        return {
            "event_info": {
                "key": "2025test",
                "name": "Test Event",
                "year": 2025
            },
            "teams": {
                "1001": {
                    "team_number": 1001,
                    "nickname": "Team Alpha",
                    "city": "Test City",
                    "state_prov": "TS",
                    "country": "USA",
                    "scouting_data": {
                        "auto_points": [15, 12, 18, 14, 16],
                        "teleop_points": [25, 30, 22, 28, 24],
                        "endgame_points": [10, 8, 12, 9, 11]
                    },
                    "statbotics_data": {
                        "epa": 18.5,
                        "auto_epa": 6.2,
                        "teleop_epa": 12.3
                    },
                    "tba_data": {
                        "wins": 8,
                        "losses": 4,
                        "ties": 0,
                        "rank": 3
                    }
                },
                "1002": {
                    "team_number": 1002,
                    "nickname": "Team Beta",
                    "city": "Another City",
                    "state_prov": "AC",
                    "country": "USA",
                    "scouting_data": {
                        "auto_points": [10, 8, 12, 9, 11],
                        "teleop_points": [30, 32, 28, 35, 31],
                        "endgame_points": [5, 7, 6, 8, 6]
                    },
                    "statbotics_data": {
                        "epa": 20.1,
                        "auto_epa": 4.8,
                        "teleop_epa": 15.3
                    },
                    "tba_data": {
                        "wins": 10,
                        "losses": 2,
                        "ties": 0,
                        "rank": 1
                    }
                }
            },
            "metadata": {
                "generated_at": "2025-06-10T10:00:00Z",
                "total_teams": 2,
                "data_sources": ["scouting", "statbotics", "tba"]
            }
        }
    
    @pytest.fixture
    def temp_dataset_file(self, sample_dataset):
        """Create temporary dataset file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_dataset, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def provider(self, temp_dataset_file):
        """Create provider instance with test data."""
        return UnifiedDatasetProvider(temp_dataset_file)
    
    def test_provider_initialization(self, temp_dataset_file):
        """Test provider initialization."""
        provider = UnifiedDatasetProvider(temp_dataset_file)
        assert provider.dataset_path == temp_dataset_file
        assert provider.dataset is not None
        assert provider.dataset["metadata"]["total_teams"] == 2
    
    def test_initialization_with_missing_file(self):
        """Test initialization with missing file."""
        with pytest.raises(DatasetLoadError) as exc_info:
            UnifiedDatasetProvider("/nonexistent/file.json")
        
        assert "Dataset file not found" in str(exc_info.value)
    
    def test_initialization_with_invalid_json(self):
        """Test initialization with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            with pytest.raises(DatasetLoadError) as exc_info:
                UnifiedDatasetProvider(temp_path)
            
            assert "Failed to parse dataset JSON" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    def test_get_team_by_number_success(self, provider):
        """Test successful team retrieval."""
        team = provider.get_team_by_number(1001)
        
        assert team is not None
        assert team["team_number"] == 1001
        assert team["nickname"] == "Team Alpha"
        assert "scouting_data" in team
        assert "statbotics_data" in team
        assert "tba_data" in team
    
    def test_get_team_by_number_not_found(self, provider):
        """Test team retrieval for non-existent team."""
        team = provider.get_team_by_number(9999)
        assert team is None
    
    def test_get_all_teams(self, provider):
        """Test getting all teams."""
        teams = provider.get_all_teams()
        
        assert len(teams) == 2
        assert any(team["team_number"] == 1001 for team in teams)
        assert any(team["team_number"] == 1002 for team in teams)
    
    def test_prepare_for_gpt_basic(self, provider):
        """Test basic GPT data preparation."""
        teams_data = provider.prepare_for_gpt()
        
        assert len(teams_data) == 2
        
        # Check first team
        team1 = next(team for team in teams_data if team["team_number"] == 1001)
        assert team1["nickname"] == "Team Alpha"
        assert "metrics" in team1
        assert "auto_points_avg" in team1["metrics"]
        assert "teleop_points_avg" in team1["metrics"]
        assert "epa" in team1["metrics"]
    
    def test_prepare_for_gpt_with_exclusions(self, provider):
        """Test GPT data preparation with team exclusions."""
        teams_data = provider.prepare_for_gpt(exclude_teams=[1002])
        
        assert len(teams_data) == 1
        assert teams_data[0]["team_number"] == 1001
    
    def test_calculate_averages(self, provider):
        """Test metric average calculations."""
        team = provider.get_team_by_number(1001)
        metrics = provider._calculate_averages(team["scouting_data"])
        
        # Check calculated averages
        assert metrics["auto_points_avg"] == 15.0  # (15+12+18+14+16)/5
        assert metrics["teleop_points_avg"] == 25.8  # (25+30+22+28+24)/5
        assert metrics["endgame_points_avg"] == 10.0  # (10+8+12+9+11)/5
    
    def test_calculate_averages_empty_data(self, provider):
        """Test average calculation with empty data."""
        metrics = provider._calculate_averages({})
        assert metrics == {}
        
        # Test with empty lists
        metrics = provider._calculate_averages({"auto_points": []})
        assert "auto_points_avg" not in metrics
    
    def test_get_game_context(self, provider):
        """Test game context retrieval."""
        # Mock game manual file
        mock_content = "Game Manual Content\nSection 1: Rules\nSection 2: Scoring"
        
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch("os.path.exists", return_value=True):
                context = provider.get_game_context()
                
                assert context == mock_content
                assert "Game Manual" in context
                assert "Rules" in context
    
    def test_get_game_context_file_not_found(self, provider):
        """Test game context with missing file."""
        with patch("os.path.exists", return_value=False):
            context = provider.get_game_context()
            assert context == ""
    
    def test_filter_teams_by_criteria(self, provider):
        """Test team filtering by criteria."""
        # Filter teams with EPA > 19
        filtered = provider.filter_teams_by_criteria(
            lambda team: team.get("statbotics_data", {}).get("epa", 0) > 19
        )
        
        assert len(filtered) == 1
        assert filtered[0]["team_number"] == 1002
    
    def test_get_team_statistics(self, provider):
        """Test team statistics calculation."""
        stats = provider.get_team_statistics(1001)
        
        assert stats is not None
        assert "scouting_stats" in stats
        assert "statbotics_stats" in stats
        assert "tba_stats" in stats
        
        # Check scouting statistics
        scouting_stats = stats["scouting_stats"]
        assert "auto_points_avg" in scouting_stats
        assert "auto_points_std" in scouting_stats
        assert "auto_points_min" in scouting_stats
        assert "auto_points_max" in scouting_stats
    
    def test_get_event_info(self, provider):
        """Test event information retrieval."""
        event_info = provider.get_event_info()
        
        assert event_info["key"] == "2025test"
        assert event_info["name"] == "Test Event"
        assert event_info["year"] == 2025
    
    def test_get_teams_by_rank_range(self, provider):
        """Test team retrieval by rank range."""
        teams = provider.get_teams_by_rank_range(1, 2)
        
        # Should return teams with ranks 1-2
        assert len(teams) == 2
        ranks = [team["tba_data"]["rank"] for team in teams]
        assert 1 in ranks
        assert 3 in ranks  # Team 1001 has rank 3, but within range
    
    def test_get_top_performers(self, provider):
        """Test top performer identification."""
        top_teams = provider.get_top_performers("epa", count=1)
        
        assert len(top_teams) == 1
        assert top_teams[0]["team_number"] == 1002  # Higher EPA
    
    def test_prepare_compact_data(self, provider):
        """Test compact data preparation for token efficiency."""
        compact_data = provider.prepare_compact_data()
        
        assert len(compact_data) == 2
        
        # Check that data is more compact
        team_data = compact_data[0]
        assert "t" in team_data  # team_number shortened
        assert "n" in team_data  # nickname shortened
        assert "m" in team_data  # metrics shortened
    
    def test_data_validation(self, provider):
        """Test dataset validation."""
        is_valid, errors = provider.validate_dataset()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_data_validation_with_errors(self, temp_dataset_file):
        """Test dataset validation with errors."""
        # Create invalid dataset
        invalid_dataset = {
            "teams": {
                "1001": {
                    # Missing required fields
                    "team_number": 1001
                }
            }
        }
        
        with open(temp_dataset_file, 'w') as f:
            json.dump(invalid_dataset, f)
        
        provider = UnifiedDatasetProvider(temp_dataset_file)
        is_valid, errors = provider.validate_dataset()
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_get_team_match_history(self, provider):
        """Test team match history retrieval."""
        # Mock match history data
        with patch.object(provider, '_load_match_history') as mock_load:
            mock_load.return_value = [
                {"match": "qm1", "score": 45, "rp": 2},
                {"match": "qm2", "score": 52, "rp": 3}
            ]
            
            history = provider.get_team_match_history(1001)
            
            assert len(history) == 2
            assert history[0]["match"] == "qm1"
    
    def test_calculate_team_trends(self, provider):
        """Test team performance trend calculation."""
        trends = provider.calculate_team_trends(1001)
        
        assert "auto_trend" in trends
        assert "teleop_trend" in trends
        assert "overall_trend" in trends
    
    def test_memory_usage_optimization(self, provider):
        """Test memory usage optimization."""
        # Should not load full dataset into memory multiple times
        original_dataset = provider.dataset
        
        # Multiple operations should reuse same dataset
        provider.get_all_teams()
        provider.prepare_for_gpt()
        provider.get_event_info()
        
        assert provider.dataset is original_dataset  # Same object reference
    
    def test_concurrent_access(self, provider):
        """Test concurrent access to provider."""
        import threading
        import time
        
        results = []
        
        def access_data(team_num):
            team = provider.get_team_by_number(team_num)
            results.append(team)
            time.sleep(0.01)  # Simulate processing time
        
        # Start multiple threads
        threads = []
        for team_num in [1001, 1002, 1001, 1002]:
            thread = threading.Thread(target=access_data, args=(team_num,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert len(results) == 4
        assert all(result is not None for result in results)
    
    def test_large_dataset_handling(self, sample_dataset):
        """Test handling of large datasets."""
        # Create large dataset
        large_dataset = sample_dataset.copy()
        large_dataset["teams"] = {}
        
        for i in range(1000, 1100):  # 100 teams
            large_dataset["teams"][str(i)] = {
                "team_number": i,
                "nickname": f"Team {i}",
                "scouting_data": {"auto_points": [10, 12, 8]},
                "statbotics_data": {"epa": 15.0},
                "tba_data": {"rank": i - 999}
            }
        
        large_dataset["metadata"]["total_teams"] = 100
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_dataset, f)
            temp_path = f.name
        
        try:
            provider = UnifiedDatasetProvider(temp_path)
            
            # Should handle large dataset efficiently
            all_teams = provider.get_all_teams()
            assert len(all_teams) == 100
            
            # Prepare for GPT should work
            gpt_data = provider.prepare_for_gpt()
            assert len(gpt_data) == 100
            
        finally:
            os.unlink(temp_path)