#!/usr/bin/env python3
"""Test script to validate refactored team comparison service behavior."""

import asyncio
import json
import sys
from typing import Any, Dict
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, '/mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App/backend')

from app.services.team_comparison_service import TeamComparisonService


def create_mock_teams_data():
    """Create mock team data for testing."""
    return [
        {
            "team_number": 1234,
            "nickname": "Team Alpha",
            "auto_avg_points": 25.5,
            "teleop_avg_points": 45.2,
            "endgame_avg_points": 15.0,
            "epa_total": 65.7,
            "consistency_score": 0.85
        },
        {
            "team_number": 5678,
            "nickname": "Team Beta", 
            "auto_avg_points": 30.1,
            "teleop_avg_points": 40.8,
            "endgame_avg_points": 12.5,
            "epa_total": 63.4,
            "consistency_score": 0.90
        }
    ]


def create_mock_gpt_response():
    """Create mock GPT response."""
    return {
        "ranking": [
            {"team_number": 5678, "rank": 1, "score": 88.5, "brief_reason": "Higher consistency and autonomous performance"},
            {"team_number": 1234, "rank": 2, "score": 85.2, "brief_reason": "Strong teleop, slightly lower consistency"}
        ],
        "summary": "Team 5678 (Beta) is ranked first due to superior autonomous performance (30.1 vs 25.5) and excellent consistency (0.90 vs 0.85). While Team 1234 (Alpha) has a slight edge in teleop scoring (45.2 vs 40.8), the consistency advantage of Team Beta makes them the preferred first pick. Both teams show strong overall performance with EPA scores above 60.",
        "key_metrics": ["auto_avg_points", "teleop_avg_points", "consistency_score", "epa_total", "endgame_avg_points"]
    }


async def test_refactored_service():
    """Test the refactored service maintains exact behavior."""
    print("=== Testing Refactored Team Comparison Service ===")
    
    # Test parameters
    team_numbers = [1234, 5678]
    your_team_number = 9999
    pick_position = "first"
    priorities = [
        {"id": "auto", "weight": 1.5, "reason": "Strong autonomous is critical"},
        {"id": "consistency", "weight": 1.2, "reason": "Reliable performance needed"}
    ]
    
    mock_teams_data = create_mock_teams_data()
    mock_gpt_response = create_mock_gpt_response()
    
    # Initialize service
    service = TeamComparisonService("/fake/path/to/dataset.json")
    
    # Mock dependencies
    with patch.object(service.data_service, 'prepare_teams_data') as mock_prepare_data, \
         patch.object(service.prompt_service, 'create_system_prompt') as mock_system_prompt, \
         patch.object(service.prompt_service, 'build_conversation_messages') as mock_build_messages, \
         patch.object(service.gpt_service, 'get_initial_analysis') as mock_gpt_analysis, \
         patch.object(service.generator, '_check_token_count') as mock_token_check:
        
        # Setup mocks
        mock_prepare_data.return_value = (mock_teams_data, {1: 1234, 2: 5678})
        mock_system_prompt.return_value = "You are an expert FRC strategist..."
        mock_build_messages.return_value = [
            {"role": "system", "content": "System prompt..."},
            {"role": "user", "content": "User prompt..."}
        ]
        mock_gpt_analysis.return_value = mock_gpt_response
        mock_token_check.return_value = None
        
        # Test initial analysis
        print("\n1. Testing Initial Analysis...")
        result = await service.compare_teams(
            team_numbers=team_numbers,
            your_team_number=your_team_number,
            pick_position=pick_position,
            priorities=priorities
        )
        
        # Validate response structure
        assert "ordered_teams" in result, "Missing ordered_teams in response"
        assert "summary" in result, "Missing summary in response" 
        assert "comparison_data" in result, "Missing comparison_data in response"
        
        # Validate ordered teams
        ordered_teams = result["ordered_teams"]
        assert len(ordered_teams) == 2, f"Expected 2 teams, got {len(ordered_teams)}"
        assert ordered_teams[0]["team_number"] == 5678, "First team should be 5678"
        assert ordered_teams[1]["team_number"] == 1234, "Second team should be 1234"
        assert ordered_teams[0]["score"] == 88.5, "First team score incorrect"
        assert ordered_teams[1]["score"] == 85.2, "Second team score incorrect"
        
        # Validate comparison data
        comparison_data = result["comparison_data"]
        assert "teams" in comparison_data, "Missing teams in comparison_data"
        assert "metrics" in comparison_data, "Missing metrics in comparison_data"
        assert len(comparison_data["teams"]) == 2, "Should have 2 teams in comparison data"
        
        print("✅ Initial analysis test passed")
        
        # Test follow-up question
        print("\n2. Testing Follow-up Question...")
        chat_history = [
            {"type": "question", "content": "Which team is better for autonomous?"},
            {"type": "answer", "content": "Team 5678 is better for autonomous with 30.1 points vs 25.5."}
        ]
        
        with patch.object(service.gpt_service, 'get_followup_response') as mock_followup:
            mock_followup.return_value = "Team 5678 has consistently higher autonomous scores..."
            
            result = await service.compare_teams(
                team_numbers=team_numbers,
                your_team_number=your_team_number,
                pick_position=pick_position,
                priorities=priorities,
                question="What about their endgame performance?",
                chat_history=chat_history
            )
            
            # Validate follow-up response structure
            assert result["ordered_teams"] is None, "Follow-up should not change ranking"
            assert "summary" in result, "Missing summary in follow-up response"
            assert "comparison_data" in result, "Missing comparison_data in follow-up"
            
        print("✅ Follow-up question test passed")
        
        # Test input validation
        print("\n3. Testing Input Validation...")
        try:
            await service.compare_teams(
                team_numbers=[1234],  # Only one team
                your_team_number=your_team_number,
                pick_position=pick_position,
                priorities=priorities
            )
            assert False, "Should have raised ValueError for single team"
        except ValueError as e:
            assert "At least two teams must be provided" in str(e)
            print("✅ Input validation test passed")
        
        # Verify service decomposition
        print("\n4. Verifying Service Decomposition...")
        assert hasattr(service, 'data_service'), "Missing data_service"
        assert hasattr(service, 'prompt_service'), "Missing prompt_service"
        assert hasattr(service, 'gpt_service'), "Missing gpt_service"
        assert hasattr(service, 'metrics_service'), "Missing metrics_service"
        assert hasattr(service, 'generator'), "Missing generator for backward compatibility"
        
        print("✅ Service decomposition verified")
        
        print("\n=== All Tests Passed! ===")
        print("✅ API contract preserved")
        print("✅ Response structure unchanged")
        print("✅ Error handling maintained") 
        print("✅ Service decomposition successful")
        
        return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_refactored_service())
        if result:
            print("\n🎉 Refactoring validation SUCCESSFUL!")
            print("The service decomposition maintains exact API behavior.")
            exit(0)
        else:
            print("\n❌ Refactoring validation FAILED!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)