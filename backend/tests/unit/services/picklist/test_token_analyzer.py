"""
Unit tests for TokenAnalyzer.
"""

import pytest

from app.services.picklist.token_analyzer import TokenAnalyzer
from app.services.picklist.exceptions import PicklistTokenLimitError


class TestTokenAnalyzer:
    """Test TokenAnalyzer functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create TokenAnalyzer instance for testing."""
        return TokenAnalyzer(model="gpt-4-turbo")
    
    def test_token_analyzer_initialization(self):
        """Test TokenAnalyzer initialization."""
        analyzer = TokenAnalyzer()
        assert analyzer.model == "gpt-4-turbo"
        assert analyzer.encoder is not None
    
    def test_token_analyzer_unknown_model(self):
        """Test TokenAnalyzer with unknown model."""
        analyzer = TokenAnalyzer(model="unknown-model")
        assert analyzer.model == "unknown-model"
        assert analyzer.encoder is not None  # Should fallback to cl100k_base
    
    def test_count_tokens_basic(self, analyzer):
        """Test basic token counting."""
        # Empty string
        assert analyzer.count_tokens("") == 0
        
        # Simple text
        count = analyzer.count_tokens("Hello world")
        assert count > 0
        assert isinstance(count, int)
        
        # Longer text should have more tokens
        longer_count = analyzer.count_tokens("Hello world, this is a longer sentence with more words.")
        assert longer_count > count
    
    def test_count_tokens_special_characters(self, analyzer):
        """Test token counting with special characters."""
        # JSON-like text
        json_text = '{"team": 1001, "score": 95.5, "reason": "Strong autonomous"}'
        count = analyzer.count_tokens(json_text)
        assert count > 0
        
        # Unicode characters
        unicode_text = "Hello 世界 🚀"
        unicode_count = analyzer.count_tokens(unicode_text)
        assert unicode_count > 0
    
    def test_count_messages_tokens_basic(self, analyzer):
        """Test message token counting."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
        ]
        
        count = analyzer.count_messages_tokens(messages)
        assert count > 0
        
        # Should be more than just content tokens due to overhead
        content_only = sum(analyzer.count_tokens(msg["content"]) for msg in messages)
        assert count > content_only
    
    def test_count_messages_tokens_empty(self, analyzer):
        """Test message token counting with empty input."""
        assert analyzer.count_messages_tokens([]) == 0
        
        # Empty content
        messages = [{"role": "user", "content": ""}]
        count = analyzer.count_messages_tokens(messages)
        assert count > 0  # Should still have role and formatting overhead
    
    def test_check_within_limit(self, analyzer):
        """Test token limit checking."""
        short_text = "Hello"
        long_text = "This is a much longer text that will have many more tokens " * 100
        
        assert analyzer.check_within_limit(short_text, limit=100) is True
        assert analyzer.check_within_limit(long_text, limit=10) is False
    
    def test_check_prompt_limit_valid(self, analyzer):
        """Test prompt limit checking with valid prompts."""
        system_prompt = "You are a helpful assistant for FRC scouting."
        user_prompt = "Please rank these teams: Team 1001, Team 1002, Team 1003"
        
        # Should not raise exception
        analyzer.check_prompt_limit(system_prompt, user_prompt, max_tokens=10000)
    
    def test_check_prompt_limit_exceeded(self, analyzer):
        """Test prompt limit checking with exceeded limits."""
        system_prompt = "You are a helpful assistant for FRC scouting." * 100
        user_prompt = "Please rank these teams." * 100
        
        with pytest.raises(PicklistTokenLimitError, match="Prompt tokens .* exceed limit"):
            analyzer.check_prompt_limit(system_prompt, user_prompt, max_tokens=100)
    
    def test_get_safe_limit(self, analyzer):
        """Test safe limit calculation."""
        safe_limit = analyzer.get_safe_limit(model_limit=10000, response_tokens=1000)
        
        # Should be less than model limit
        assert safe_limit < 10000
        
        # Should account for response tokens and buffer
        expected_max = 10000 - 1000 - int(10000 * 0.1)  # 10% buffer
        assert safe_limit <= expected_max
    
    def test_estimate_response_tokens(self, analyzer):
        """Test response token estimation."""
        # Small team count
        small_estimate = analyzer.estimate_response_tokens(5)
        assert small_estimate > 0
        
        # Large team count should have more tokens
        large_estimate = analyzer.estimate_response_tokens(50)
        assert large_estimate > small_estimate
        
        # Should include safety buffer
        base_estimate = analyzer.BASE_RESPONSE_TOKENS + (analyzer.TOKENS_PER_TEAM * 10)
        actual_estimate = analyzer.estimate_response_tokens(10)
        assert actual_estimate > base_estimate  # Due to 20% buffer
    
    def test_estimate_prompt_tokens(self, analyzer):
        """Test prompt token estimation."""
        system_prompt = "You are a helpful assistant."
        user_prompt = "Hello, how are you?"
        
        estimate = analyzer.estimate_prompt_tokens(system_prompt, user_prompt)
        assert estimate > 0
        
        # Should match count_messages_tokens
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        actual_count = analyzer.count_messages_tokens(messages)
        assert estimate == actual_count
    
    def test_calculate_response_similarity(self, analyzer):
        """Test response similarity calculation."""
        response1 = "Team 1001 is the best choice for alliance captain."
        response2 = "Team 1001 would be excellent as an alliance captain."
        response3 = "Team 2002 should be avoided in alliance selection."
        
        # Similar responses
        similarity_high = analyzer.calculate_response_similarity(response1, response2)
        assert 0.0 <= similarity_high <= 1.0
        assert similarity_high > 0.3  # Should have some similarity
        
        # Different responses
        similarity_low = analyzer.calculate_response_similarity(response1, response3)
        assert 0.0 <= similarity_low <= 1.0
        assert similarity_low < similarity_high
        
        # Empty responses
        assert analyzer.calculate_response_similarity("", "") == 0.0
        assert analyzer.calculate_response_similarity("hello", "") == 0.0
    
    def test_detect_repetition(self, analyzer):
        """Test repetition detection."""
        # Text with repetition
        text_with_repetition = "Team 1001 is great. Team 1001 is great. Team 1001 is great."
        patterns = analyzer.detect_repetition(text_with_repetition, min_length=10)
        assert len(patterns) > 0
        assert "Team 1001 is great" in patterns[0]
        
        # Text without repetition
        text_without_repetition = "Team 1001 is excellent. Team 1002 is good. Team 1003 is okay."
        patterns = analyzer.detect_repetition(text_without_repetition, min_length=10)
        assert len(patterns) == 0
    
    def test_analyze_token_usage(self, analyzer):
        """Test token usage analysis."""
        prompts = [
            "Short prompt",
            "This is a medium length prompt with some more words",
            "This is a very long prompt with many words and tokens that should result in a higher token count than the others",
        ]
        
        analysis = analyzer.analyze_token_usage(prompts)
        
        assert analysis["total_prompts"] == 3
        assert analysis["total_tokens"] > 0
        assert analysis["average_tokens"] > 0
        assert analysis["min_tokens"] > 0
        assert analysis["max_tokens"] >= analysis["min_tokens"]
        assert len(analysis["token_distribution"]) == 3
        
        # Empty prompts
        empty_analysis = analyzer.analyze_token_usage([])
        assert "error" in empty_analysis
    
    def test_suggest_optimizations(self, analyzer):
        """Test optimization suggestions."""
        # Verbose prompt
        verbose_prompt = """
        Please kindly help me to rank these teams in order to create
        the best possible alliance for our team. It is important that
        we consider all factors carefully.
        """
        
        suggestions = analyzer.suggest_optimizations(verbose_prompt)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check for specific suggestions
        suggestion_text = " ".join(suggestions)
        assert any(word in suggestion_text.lower() for word in ["polite", "wordy", "expletive"])
        
        # Clean prompt should have fewer suggestions
        clean_prompt = "Rank these teams by score."
        clean_suggestions = analyzer.suggest_optimizations(clean_prompt)
        assert len(clean_suggestions) <= len(suggestions)
    
    def test_get_token_breakdown(self, analyzer):
        """Test detailed token breakdown."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello world."},
        ]
        
        breakdown = analyzer.get_token_breakdown(messages)
        
        assert "total_tokens" in breakdown
        assert "messages" in breakdown
        assert "overhead" in breakdown
        
        assert len(breakdown["messages"]) == 2
        
        # Check message breakdown structure
        msg_breakdown = breakdown["messages"][0]
        assert "role" in msg_breakdown
        assert "content_tokens" in msg_breakdown
        assert "role_tokens" in msg_breakdown
        assert "overhead" in msg_breakdown
        assert "total" in msg_breakdown
        
        # Total should be sum of individual messages plus conversation overhead
        expected_total = sum(msg["total"] for msg in breakdown["messages"]) + 3
        assert breakdown["total_tokens"] == expected_total
    
    def test_token_overhead_constants(self, analyzer):
        """Test that token overhead constants are reasonable."""
        assert analyzer.MESSAGE_OVERHEAD > 0
        assert analyzer.ROLE_TOKENS["system"] > 0
        assert analyzer.ROLE_TOKENS["user"] > 0
        assert analyzer.ROLE_TOKENS["assistant"] > 0
        assert analyzer.TOKENS_PER_TEAM > 0
        assert analyzer.BASE_RESPONSE_TOKENS > 0
    
    def test_edge_cases(self, analyzer):
        """Test edge cases and error conditions."""
        # None input
        assert analyzer.count_tokens(None) == 0
        
        # Very long text
        very_long_text = "word " * 10000
        count = analyzer.count_tokens(very_long_text)
        assert count > 1000
        
        # Special characters and formatting
        special_text = '{"key": "value", "array": [1, 2, 3], "null": null}'
        count = analyzer.count_tokens(special_text)
        assert count > 0