"""
Basic test to validate that the testing infrastructure is working correctly.
"""

import pytest
from unittest.mock import MagicMock

from tests.fixtures.test_data import TestDataFactory, SAMPLE_TEAMS
from tests.utils.test_helpers import TestHelpers, assert_valid_picklist


class TestInfrastructureValidation:
    """Test that the testing infrastructure is properly configured."""
    
    def test_pytest_configuration(self):
        """Test that pytest is configured correctly."""
        assert True  # Basic assertion
    
    def test_fixtures_available(self, sample_team_data, sample_picklist_data):
        """Test that fixtures are available and working."""
        assert len(sample_team_data) == 2
        assert sample_team_data[0]["team_number"] == 1234
        
        assert "rankings" in sample_picklist_data
        assert "metadata" in sample_picklist_data
    
    def test_mock_external_apis(self, mock_openai_client, mock_tba_client, mock_statbotics_client):
        """Test that external API mocks are working."""
        assert isinstance(mock_openai_client, MagicMock)
        assert isinstance(mock_tba_client, MagicMock)
        assert isinstance(mock_statbotics_client, MagicMock)
    
    def test_test_data_factory(self):
        """Test that the test data factory works correctly."""
        team_data = TestDataFactory.create_team_data(9999, nickname="Test Factory Team")
        assert team_data["team_number"] == 9999
        assert team_data["nickname"] == "Test Factory Team"
        
        picklist_data = TestDataFactory.create_picklist_data()
        assert_valid_picklist(picklist_data)
    
    def test_test_helpers(self):
        """Test that test helper functions work correctly."""
        team1 = {"team_number": 1234, "nickname": "Test Team"}
        team2 = {"team_number": 1234, "nickname": "Test Team"}
        
        TestHelpers.assert_teams_equal(team1, team2)
        
        # Test dictionary subset assertion
        subset = {"team_number": 1234}
        full_dict = {"team_number": 1234, "nickname": "Test Team", "location": "Test City"}
        TestHelpers.assert_dict_subset(subset, full_dict)
    
    def test_sample_data_constants(self):
        """Test that sample data constants are properly defined."""
        assert len(SAMPLE_TEAMS) == 5
        assert all("team_number" in team for team in SAMPLE_TEAMS)
        assert all("nickname" in team for team in SAMPLE_TEAMS)
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit test marker works."""
        assert True
    
    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration test marker works."""
        assert True
    
    def test_environment_variables(self, env_vars):
        """Test that environment variables fixture works."""
        assert "OPENAI_API_KEY" in env_vars
        assert "TBA_API_KEY" in env_vars
        assert env_vars["OPENAI_API_KEY"] == "test-openai-key"
    
    def test_temp_directory(self, temp_dir):
        """Test that temporary directory fixture works."""
        import os
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)