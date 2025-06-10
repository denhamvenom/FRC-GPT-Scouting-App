"""
Integration tests for external API interactions.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, Mock

from app.services.picklist.strategies.gpt_strategy import GPTStrategy
from app.services.picklist.exceptions import (
    GPTResponseError,
    TokenLimitExceededError,
    PicklistGenerationError
)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not available"
)
class TestOpenAIIntegration:
    """Integration tests for OpenAI API (requires real API key)."""
    
    @pytest.fixture
    def gpt_strategy(self):
        """Create GPT strategy with real API key for integration testing."""
        return GPTStrategy(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",  # Use cheaper model for testing
            max_tokens=10000,
            temperature=0.1
        )
    
    @pytest.fixture
    def sample_teams_data(self):
        """Small sample of teams data for real API testing."""
        return [
            {
                "team_number": 254,
                "nickname": "The Cheesy Poofs",
                "metrics": {
                    "auto_points_avg": 20.5,
                    "teleop_points_avg": 35.2,
                    "endgame_points_avg": 12.8,
                    "epa": 28.5
                }
            },
            {
                "team_number": 1323,
                "nickname": "MadTown Robotics",
                "metrics": {
                    "auto_points_avg": 18.3,
                    "teleop_points_avg": 32.1,
                    "endgame_points_avg": 11.5,
                    "epa": 25.2
                }
            },
            {
                "team_number": 2056,
                "nickname": "OP Robotics",
                "metrics": {
                    "auto_points_avg": 16.8,
                    "teleop_points_avg": 28.7,
                    "endgame_points_avg": 10.2,
                    "epa": 22.8
                }
            }
        ]
    
    @pytest.fixture
    def sample_priorities(self):
        """Sample priority metrics for testing."""
        return [
            {"id": "auto_points_avg", "name": "Autonomous Points", "weight": 2.0},
            {"id": "teleop_points_avg", "name": "Teleoperated Points", "weight": 1.5},
            {"id": "epa", "name": "Expected Points Added", "weight": 1.8}
        ]
    
    @pytest.mark.asyncio
    async def test_real_gpt_ranking_generation(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test actual GPT ranking generation with real API."""
        result = await gpt_strategy.generate_ranking(
            teams_data=sample_teams_data,
            priorities=sample_priorities,
            your_team_number=1234,
            game_context="FRC 2025 game involves scoring game pieces in autonomous and teleoperated periods."
        )
        
        # Verify response structure
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check each ranked team
        for team in result:
            assert "team_number" in team
            assert "score" in team
            assert "reasoning" in team
            assert isinstance(team["team_number"], int)
            assert isinstance(team["score"], (int, float))
            assert isinstance(team["reasoning"], str)
            
        # Verify teams are present
        team_numbers = [team["team_number"] for team in result]
        assert 254 in team_numbers
        assert 1323 in team_numbers
        assert 2056 in team_numbers
    
    @pytest.mark.asyncio
    async def test_gpt_response_format_handling(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test handling of different GPT response formats."""
        result = await gpt_strategy.generate_ranking(
            teams_data=sample_teams_data,
            priorities=sample_priorities,
            your_team_number=1234
        )
        
        # GPT should return teams in some order
        assert len(result) == len(sample_teams_data)
        
        # Scores should be reasonable (0-100 range typically)
        for team in result:
            assert 0 <= team["score"] <= 100
            assert len(team["reasoning"]) > 10  # Should have meaningful reasoning
    
    @pytest.mark.asyncio
    async def test_token_counting_accuracy(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test token counting accuracy with real data."""
        # Build prompt
        prompt = gpt_strategy._build_prompt(
            teams_data=sample_teams_data,
            priorities=sample_priorities,
            your_team_number=1234,
            game_context="Test context",
            reference_teams=[]
        )
        
        # Token count should be reasonable
        assert prompt.token_count > 0
        assert prompt.token_count < gpt_strategy.max_tokens
        
        # Manual count should match
        manual_count = gpt_strategy._count_tokens(prompt.content)
        assert abs(prompt.token_count - manual_count) <= 10  # Allow small variance
    
    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test handling of API rate limits."""
        # Make multiple rapid requests to test rate limiting
        tasks = []
        for i in range(3):  # Reduced for cost control
            task = gpt_strategy.generate_ranking(
                teams_data=sample_teams_data,
                priorities=sample_priorities,
                your_team_number=1234 + i
            )
            tasks.append(task)
        
        # All should complete (with retries if needed)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that most succeeded (some might fail due to rate limits)
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 1  # At least one should succeed


@pytest.mark.integration
class TestMockedExternalAPIs:
    """Integration tests with mocked external APIs for deterministic testing."""
    
    @pytest.fixture
    def mock_openai_responses(self):
        """Mock OpenAI responses for different scenarios."""
        return {
            "success": {
                "choices": [Mock()],
                "usage": Mock(total_tokens=1500)
            },
            "rate_limit": Exception("Rate limit exceeded"),
            "invalid_json": {
                "choices": [Mock()],
                "usage": Mock(total_tokens=1000)
            },
            "token_limit": {
                "choices": [Mock()],
                "usage": Mock(total_tokens=150000)
            }
        }
    
    @pytest.fixture
    def gpt_strategy_mock(self, mock_openai_responses):
        """GPT strategy with mocked client."""
        strategy = GPTStrategy(api_key="test_key")
        
        # Set up successful response by default
        mock_openai_responses["success"].choices[0].message.content = '''```json
{
    "p": [
        [254, 95.0, "Elite team with consistent high performance"],
        [1323, 88.5, "Strong autonomous with good teleop"],
        [2056, 82.3, "Reliable team with solid fundamentals"]
    ]
}
```'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_responses["success"]
        strategy.client = mock_client
        
        return strategy, mock_client, mock_openai_responses
    
    @pytest.mark.asyncio
    async def test_api_retry_mechanism(self, gpt_strategy_mock):
        """Test API retry mechanism with failures."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        # First call fails, second succeeds
        mock_client.chat.completions.create.side_effect = [
            Exception("Temporary failure"),
            responses["success"]
        ]
        
        teams_data = [
            {"team_number": 254, "nickname": "Test Team", "metrics": {"epa": 25}}
        ]
        
        result = await strategy.generate_ranking(
            teams_data=teams_data,
            priorities=[{"id": "epa", "weight": 1.0}],
            your_team_number=1234
        )
        
        # Should succeed after retry
        assert len(result) == 1
        assert result[0]["team_number"] == 254
        assert mock_client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, gpt_strategy_mock):
        """Test behavior when max retries are exceeded."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        # All calls fail
        mock_client.chat.completions.create.side_effect = Exception("Persistent failure")
        
        teams_data = [
            {"team_number": 254, "nickname": "Test Team", "metrics": {"epa": 25}}
        ]
        
        with pytest.raises(PicklistGenerationError):
            await strategy.generate_ranking(
                teams_data=teams_data,
                priorities=[{"id": "epa", "weight": 1.0}],
                your_team_number=1234
            )
        
        # Should have tried maximum number of times
        assert mock_client.chat.completions.create.call_count == 3
    
    @pytest.mark.asyncio
    async def test_response_parsing_edge_cases(self, gpt_strategy_mock):
        """Test parsing of various response formats."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        test_cases = [
            # Standard format
            {
                "response": '{"picklist": [{"team_number": 254, "score": 95.0, "reasoning": "Great team"}]}',
                "expected_teams": 1
            },
            # Ultra-compact format
            {
                "response": '{"p": [[254, 95.0, "Great team"]]}',
                "expected_teams": 1
            },
            # Markdown wrapped
            {
                "response": '```json\n{"p": [[254, 95.0, "Great team"]]}\n```',
                "expected_teams": 1
            },
            # Multiple teams
            {
                "response": '{"p": [[254, 95.0, "Great"], [1323, 90.0, "Good"], [2056, 85.0, "Decent"]]}',
                "expected_teams": 3
            }
        ]
        
        teams_data = [
            {"team_number": 254, "nickname": "Team 1", "metrics": {"epa": 25}},
            {"team_number": 1323, "nickname": "Team 2", "metrics": {"epa": 23}},
            {"team_number": 2056, "nickname": "Team 3", "metrics": {"epa": 21}}
        ]
        
        for i, test_case in enumerate(test_cases):
            # Set up response
            responses["success"].choices[0].message.content = test_case["response"]
            
            result = await strategy.generate_ranking(
                teams_data=teams_data,
                priorities=[{"id": "epa", "weight": 1.0}],
                your_team_number=1234
            )
            
            assert len(result) == test_case["expected_teams"], f"Test case {i} failed"
            assert result[0]["team_number"] == 254
    
    @pytest.mark.asyncio
    async def test_invalid_response_handling(self, gpt_strategy_mock):
        """Test handling of invalid API responses."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        invalid_responses = [
            "Invalid JSON",
            '{"wrong_format": "data"}',
            '{"p": "not_an_array"}',
            '{"p": [["invalid", "data"]]}',  # Missing required fields
            "",  # Empty response
            '{"p": []}'  # Empty picklist
        ]
        
        teams_data = [
            {"team_number": 254, "nickname": "Test Team", "metrics": {"epa": 25}}
        ]
        
        for invalid_response in invalid_responses:
            responses["invalid_json"].choices[0].message.content = invalid_response
            mock_client.chat.completions.create.return_value = responses["invalid_json"]
            
            with pytest.raises(GPTResponseError):
                await strategy.generate_ranking(
                    teams_data=teams_data,
                    priorities=[{"id": "epa", "weight": 1.0}],
                    your_team_number=1234
                )
    
    @pytest.mark.asyncio
    async def test_large_prompt_handling(self, gpt_strategy_mock):
        """Test handling of large prompts approaching token limits."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        # Create large dataset
        teams_data = []
        for i in range(100):  # Large number of teams
            teams_data.append({
                "team_number": 1000 + i,
                "nickname": f"Team {1000 + i} with a very long nickname that takes up many tokens",
                "metrics": {
                    "auto_points_avg": 15.0 + i % 10,
                    "teleop_points_avg": 25.0 + i % 15,
                    "epa": 20.0 + i % 8
                }
            })
        
        # Mock token counting to be near limit
        with patch.object(strategy, '_count_tokens') as mock_count:
            mock_count.return_value = strategy.max_tokens - 1000  # Near limit
            
            with pytest.raises(TokenLimitExceededError):
                await strategy.generate_ranking(
                    teams_data=teams_data,
                    priorities=[{"id": "epa", "weight": 1.0}],
                    your_team_number=1234
                )
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, gpt_strategy_mock):
        """Test concurrent API calls behavior."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        teams_data = [
            {"team_number": 254, "nickname": "Test Team", "metrics": {"epa": 25}}
        ]
        
        # Create multiple concurrent calls
        tasks = []
        for i in range(5):
            task = strategy.generate_ranking(
                teams_data=teams_data,
                priorities=[{"id": "epa", "weight": 1.0}],
                your_team_number=1234 + i
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        for result in results:
            assert len(result) == 1
            assert result[0]["team_number"] == 254
        
        # Should have made 5 API calls
        assert mock_client.chat.completions.create.call_count == 5
    
    def test_token_estimation_accuracy(self, gpt_strategy_mock):
        """Test accuracy of token estimation."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        test_texts = [
            "Short text",
            "This is a longer text with more words to test token counting accuracy",
            "Very long text " * 100,  # Repeated text
            "Mixed content with numbers 123 and symbols !@#$%",
            "",  # Empty text
        ]
        
        for text in test_texts:
            count = strategy._count_tokens(text)
            
            # Token count should be reasonable
            assert count >= 0
            if text:
                assert count > 0
            else:
                assert count == 0
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, gpt_strategy_mock):
        """Test API timeout handling."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        # Mock timeout
        import asyncio
        mock_client.chat.completions.create.side_effect = asyncio.TimeoutError("Request timeout")
        
        teams_data = [
            {"team_number": 254, "nickname": "Test Team", "metrics": {"epa": 25}}
        ]
        
        with pytest.raises(PicklistGenerationError):
            await strategy.generate_ranking(
                teams_data=teams_data,
                priorities=[{"id": "epa", "weight": 1.0}],
                your_team_number=1234
            )
    
    @pytest.mark.asyncio
    async def test_response_content_validation(self, gpt_strategy_mock):
        """Test validation of response content."""
        strategy, mock_client, responses = gpt_strategy_mock
        
        # Test malicious or problematic content
        problematic_responses = [
            '{"p": [[254, 95.0, "Team with \\"malicious\\" content"]]}',
            '{"p": [[254, 95.0, "Team with unicode 🤖 characters"]]}',
            '{"p": [[254, 95.0, "Team with very long reasoning text ' + 'x' * 1000 + '"]]}',
            '{"p": [[254, 95.0, "Team with\\nnewlines\\tand\\ttabs"]]}',
        ]
        
        teams_data = [
            {"team_number": 254, "nickname": "Test Team", "metrics": {"epa": 25}}
        ]
        
        for response_content in problematic_responses:
            responses["success"].choices[0].message.content = response_content
            
            # Should handle gracefully
            result = await strategy.generate_ranking(
                teams_data=teams_data,
                priorities=[{"id": "epa", "weight": 1.0}],
                your_team_number=1234
            )
            
            assert len(result) == 1
            assert result[0]["team_number"] == 254
            assert isinstance(result[0]["reasoning"], str)