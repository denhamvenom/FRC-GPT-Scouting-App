"""
Token counter for GPT operations.
"""

import logging
from typing import Optional

import tiktoken

from ..interfaces import TokenCounter

logger = logging.getLogger(__name__)


class GPTTokenCounter(TokenCounter):
    """Token counter for GPT models."""

    def __init__(self, model: str = "gpt-4-turbo"):
        """
        Initialize token counter.

        Args:
            model: GPT model name for token encoding
        """
        self.model = model
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Rough estimate as fallback
            return len(text) // 4

    def check_within_limit(self, text: str, limit: int) -> bool:
        """Check if text is within token limit."""
        token_count = self.count_tokens(text)
        return token_count <= limit

    def count_messages_tokens(self, messages: list) -> int:
        """
        Count tokens in a list of messages (for chat models).

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Total token count
        """
        total_tokens = 0
        
        # Account for message formatting overhead
        # Each message has ~4 tokens of overhead
        total_tokens += len(messages) * 4
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            # Role tokens
            total_tokens += self.count_tokens(role)
            
            # Content tokens
            total_tokens += self.count_tokens(content)
        
        # Add some buffer for response formatting
        total_tokens += 3
        
        return total_tokens

    def estimate_response_tokens(self, team_count: int) -> int:
        """
        Estimate tokens needed for response based on team count.

        Args:
            team_count: Number of teams to rank

        Returns:
            Estimated token count
        """
        # Each team entry in compact format: [number, score, "reason"]
        # Roughly 20-30 tokens per team
        tokens_per_team = 25
        
        # JSON structure overhead
        overhead = 50
        
        return (team_count * tokens_per_team) + overhead

    def get_safe_limit(self, model_limit: int, response_tokens: int) -> int:
        """
        Get safe token limit for input, leaving room for response.

        Args:
            model_limit: Model's total token limit
            response_tokens: Estimated response tokens

        Returns:
            Safe limit for input tokens
        """
        # Leave 10% buffer for safety
        buffer = int(model_limit * 0.1)
        
        return model_limit - response_tokens - buffer