"""
Unit tests for GPTStrategy.
"""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.picklist.strategies.gpt_strategy import GPTStrategy
from app.services.picklist.models import GPTPrompt, RankedTeam
from app.services.picklist.exceptions import (
    GPTResponseError,
    TokenLimitExceededError,
    PicklistGenerationError
)


class TestGPTStrategy:
    """Test GPTStrategy functionality."""
    
    @pytest.fixture
    def sample_teams_data(self):
        """Sample teams data for testing."""
        return [
            {
                "team_number": 1001,
                "nickname": "Team Alpha", 
                "metrics": {"auto_points": 15.0, "teleop_points": 25.0}
            },
            {
                "team_number": 1002,
                "nickname": "Team Beta",
                "metrics": {"auto_points": 12.0, "teleop_points": 30.0}
            },
            {
                "team_number": 1003,
                "nickname": "Team Gamma",
                "metrics": {"auto_points": 18.0, "teleop_points": 20.0}
            }
        ]
    
    @pytest.fixture
    def sample_priorities(self):
        """Sample priority metrics."""
        return [
            {"id": "auto_points", "name": "Auto Points", "weight": 2.0},
            {"id": "teleop_points", "name": "Teleop Points", "weight": 1.5}
        ]
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        client = Mock()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "p": [
                [1003, 95.0, "Excellent autonomous performance"],
                [1002, 88.0, "Strong teleop capabilities"],
                [1001, 82.0, "Well-rounded team"]
            ]
        })
        mock_response.usage.total_tokens = 1500
        
        client.chat.completions.create.return_value = mock_response
        return client
    
    @pytest.fixture
    def gpt_strategy(self, mock_openai_client):
        """Create GPTStrategy with mocked client."""
        with patch('app.services.picklist.strategies.gpt_strategy.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            strategy = GPTStrategy(api_key="test_key")
            strategy.client = mock_openai_client
            return strategy
    
    def test_strategy_initialization(self):
        """Test GPTStrategy initialization."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            strategy = GPTStrategy()
            assert strategy.model == "gpt-4o"
            assert strategy.max_tokens == 100000
            assert strategy.temperature == 0.1
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('app.services.picklist.strategies.gpt_strategy.OpenAI') as mock_openai:
                strategy = GPTStrategy()
                assert strategy.client is None
                mock_openai.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_ranking_success(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test successful ranking generation."""
        result = await gpt_strategy.generate_ranking(
            teams_data=sample_teams_data,
            priorities=sample_priorities,
            your_team_number=1001,
            game_context="Test game context"
        )
        
        assert len(result) == 3
        assert result[0]["team_number"] == 1003
        assert result[0]["score"] == 95.0
        assert result[1]["team_number"] == 1002
        assert result[2]["team_number"] == 1001
        
        # Verify OpenAI was called correctly
        gpt_strategy.client.chat.completions.create.assert_called_once()
        call_args = gpt_strategy.client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4o"
        assert call_args[1]["temperature"] == 0.1
    
    @pytest.mark.asyncio
    async def test_generate_ranking_no_client(self, sample_teams_data, sample_priorities):
        """Test ranking generation without OpenAI client."""
        strategy = GPTStrategy()
        strategy.client = None
        
        with pytest.raises(PicklistGenerationError) as exc_info:
            await strategy.generate_ranking(
                teams_data=sample_teams_data,
                priorities=sample_priorities,
                your_team_number=1001
            )
        
        assert "OpenAI client not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_token_limit_exceeded(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test handling of token limit exceeded."""
        # Mock token counting to exceed limit
        with patch('tiktoken.encoding_for_model') as mock_encoding:
            mock_enc = Mock()
            mock_enc.encode.return_value = ['token'] * 120000  # Exceed 100k limit
            mock_encoding.return_value = mock_enc
            
            with pytest.raises(TokenLimitExceededError) as exc_info:
                await gpt_strategy.generate_ranking(
                    teams_data=sample_teams_data,
                    priorities=sample_priorities,
                    your_team_number=1001
                )
            
            assert "Token limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_gpt_api_error(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test handling of GPT API errors."""
        # Mock API error
        gpt_strategy.client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(PicklistGenerationError) as exc_info:
            await gpt_strategy.generate_ranking(
                teams_data=sample_teams_data,
                priorities=sample_priorities,
                your_team_number=1001
            )
        
        assert "GPT API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_gpt_response(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test handling of invalid GPT responses."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_response.usage.total_tokens = 1000
        
        gpt_strategy.client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(GPTResponseError) as exc_info:
            await gpt_strategy.generate_ranking(
                teams_data=sample_teams_data,
                priorities=sample_priorities,
                your_team_number=1001
            )
        
        assert "Failed to parse GPT response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_markdown_wrapped_response(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test handling of markdown-wrapped GPT responses."""
        # Mock response wrapped in markdown
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''```json
{
    "p": [
        [1003, 95.0, "Great team"],
        [1002, 88.0, "Good team"]
    ]
}
```'''
        mock_response.usage.total_tokens = 1000
        
        gpt_strategy.client.chat.completions.create.return_value = mock_response
        
        result = await gpt_strategy.generate_ranking(
            teams_data=sample_teams_data,
            priorities=sample_priorities,
            your_team_number=1001
        )
        
        assert len(result) == 2
        assert result[0]["team_number"] == 1003
    
    def test_build_prompt(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test prompt building."""
        prompt = gpt_strategy._build_prompt(
            teams_data=sample_teams_data,
            priorities=sample_priorities,
            your_team_number=1001,
            game_context="Test context",
            reference_teams=[]
        )
        
        assert isinstance(prompt, GPTPrompt)
        assert "Team Alpha" in prompt.content
        assert "auto_points" in prompt.content
        assert "Test context" in prompt.content
        assert prompt.token_count > 0
    
    def test_count_tokens(self, gpt_strategy):
        """Test token counting."""
        text = "This is a test message for token counting."
        
        with patch('tiktoken.encoding_for_model') as mock_encoding:
            mock_enc = Mock()
            mock_enc.encode.return_value = ['token'] * 10
            mock_encoding.return_value = mock_enc
            
            count = gpt_strategy._count_tokens(text)
            assert count == 10
    
    def test_parse_gpt_response_ultra_compact(self, gpt_strategy):
        """Test parsing ultra-compact GPT response format."""
        response_text = json.dumps({
            "p": [
                [1001, 95.0, "Great team"],
                [1002, 88.0, "Good team"],
                [1003, 82.0, "Average team"]
            ]
        })
        
        result = gpt_strategy._parse_gpt_response(response_text)
        
        assert len(result) == 3
        assert result[0]["team_number"] == 1001
        assert result[0]["score"] == 95.0
        assert result[0]["reasoning"] == "Great team"
    
    def test_parse_gpt_response_standard_format(self, gpt_strategy):
        """Test parsing standard GPT response format."""
        response_text = json.dumps({
            "picklist": [
                {
                    "team_number": 1001,
                    "score": 95.0,
                    "reasoning": "Great team"
                },
                {
                    "team_number": 1002,
                    "score": 88.0,
                    "reasoning": "Good team"
                }
            ]
        })
        
        result = gpt_strategy._parse_gpt_response(response_text)
        
        assert len(result) == 2
        assert result[0]["team_number"] == 1001
        assert result[0]["score"] == 95.0
    
    def test_parse_gpt_response_invalid_format(self, gpt_strategy):
        """Test parsing invalid GPT response format."""
        response_text = json.dumps({
            "unexpected_format": "data"
        })
        
        with pytest.raises(GPTResponseError) as exc_info:
            gpt_strategy._parse_gpt_response(response_text)
        
        assert "Unknown response format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test retry mechanism on failures."""
        # Mock first call to fail, second to succeed
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "p": [[1001, 95.0, "Success on retry"]]
        })
        mock_response.usage.total_tokens = 1000
        
        gpt_strategy.client.chat.completions.create.side_effect = [
            Exception("Temporary error"),
            mock_response
        ]
        
        result = await gpt_strategy.generate_ranking(
            teams_data=sample_teams_data,
            priorities=sample_priorities,
            your_team_number=1001
        )
        
        assert len(result) == 1
        assert result[0]["team_number"] == 1001
        assert gpt_strategy.client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, gpt_strategy, sample_teams_data, sample_priorities):
        """Test behavior when max retries are exceeded."""
        # Mock all calls to fail
        gpt_strategy.client.chat.completions.create.side_effect = Exception("Persistent error")
        
        with pytest.raises(PicklistGenerationError):
            await gpt_strategy.generate_ranking(
                teams_data=sample_teams_data,
                priorities=sample_priorities,
                your_team_number=1001
            )
        
        # Should have tried maximum number of times
        assert gpt_strategy.client.chat.completions.create.call_count == 3
    
    def test_clean_response_text(self, gpt_strategy):
        """Test response text cleaning."""
        # Test clean text (no change)
        clean_text = '{"p": [[1001, 95.0, "test"]]}'
        result = gpt_strategy._clean_response_text(clean_text)
        assert result == clean_text
        
        # Test markdown-wrapped text
        markdown_text = '```json\n{"p": [[1001, 95.0, "test"]]}\n```'
        result = gpt_strategy._clean_response_text(markdown_text)
        assert result == '{"p": [[1001, 95.0, "test"]]}'
        
        # Test simple code block
        simple_block = '```\n{"p": [[1001, 95.0, "test"]]}\n```'
        result = gpt_strategy._clean_response_text(simple_block)
        assert result == '{"p": [[1001, 95.0, "test"]]}'
    
    @pytest.mark.asyncio
    async def test_custom_model_parameters(self, mock_openai_client):
        """Test custom model parameters."""
        with patch('app.services.picklist.strategies.gpt_strategy.OpenAI') as mock_openai:
            mock_openai.return_value = mock_openai_client
            
            strategy = GPTStrategy(
                model="gpt-4-turbo",
                max_tokens=50000,
                temperature=0.3
            )
            strategy.client = mock_openai_client
            
            await strategy.generate_ranking(
                teams_data=[{"team_number": 1001, "metrics": {}}],
                priorities=[{"id": "test", "weight": 1.0}],
                your_team_number=1001
            )
            
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-4-turbo"
            assert call_args[1]["temperature"] == 0.3
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, gpt_strategy):
        """Test handling of large datasets."""
        # Create large dataset
        large_teams_data = [
            {
                "team_number": i,
                "nickname": f"Team {i}",
                "metrics": {"auto": i % 20, "teleop": (i * 2) % 30}
            }
            for i in range(1000, 1100)  # 100 teams
        ]
        
        # Mock response for large dataset
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "p": [[i, 50.0, f"Team {i}"] for i in range(1000, 1010)]
        })
        mock_response.usage.total_tokens = 5000
        
        gpt_strategy.client.chat.completions.create.return_value = mock_response
        
        result = await gpt_strategy.generate_ranking(
            teams_data=large_teams_data,
            priorities=[{"id": "auto", "weight": 1.0}],
            your_team_number=1050
        )
        
        assert len(result) == 10  # Returned subset
    
    def test_prompt_optimization(self, gpt_strategy):
        """Test prompt optimization features."""
        teams_data = [
            {"team_number": 1001, "nickname": "A" * 100, "metrics": {"auto": 10}}  # Long nickname
        ]
        
        prompt = gpt_strategy._build_prompt(
            teams_data=teams_data,
            priorities=[{"id": "auto", "weight": 1.0}],
            your_team_number=1001
        )
        
        # Should optimize long nicknames
        assert "A" * 100 not in prompt.content
        assert "A" * 20 in prompt.content  # Truncated version