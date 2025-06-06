"""
Basic test to validate that pytest is working without external dependencies.
"""

import pytest
import json
from typing import Dict, Any


class TestBasicInfrastructure:
    """Test basic infrastructure without external dependencies."""
    
    def test_pytest_works(self):
        """Test that pytest is functioning."""
        assert True
    
    def test_python_basics(self):
        """Test basic Python functionality."""
        data = {"test": "value"}
        assert data["test"] == "value"
    
    def test_json_handling(self):
        """Test JSON serialization/deserialization."""
        data = {"team": 1234, "score": 150.5}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["team"] == 1234
        assert parsed["score"] == 150.5
    
    @pytest.mark.unit
    def test_unit_marker_basic(self):
        """Test unit marker without dependencies."""
        assert 1 + 1 == 2
    
    def test_list_operations(self):
        """Test list operations."""
        teams = [1234, 5678, 9012]
        assert len(teams) == 3
        assert 1234 in teams
        assert max(teams) == 9012
    
    def test_dict_operations(self):
        """Test dictionary operations."""
        team_data = {
            "team_number": 1234,
            "nickname": "Test Team",
            "performance": {
                "auto": 25.0,
                "teleop": 100.0
            }
        }
        
        assert team_data["team_number"] == 1234
        assert team_data["performance"]["auto"] == 25.0
        
    def test_string_operations(self):
        """Test string operations."""
        team_name = "Test Team 1234"
        assert "1234" in team_name
        assert team_name.startswith("Test")
        assert team_name.endswith("1234")
    
    def test_math_operations(self):
        """Test mathematical operations."""
        scores = [150, 140, 160, 155]
        average = sum(scores) / len(scores)
        assert average == 151.25
        
        max_score = max(scores)
        min_score = min(scores)
        assert max_score == 160
        assert min_score == 140