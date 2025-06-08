"""
Token analysis and optimization for GPT operations.

This module provides comprehensive token counting, limit checking,
and optimization functionality for picklist generation.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import tiktoken

from .exceptions import PicklistTokenLimitError

logger = logging.getLogger(__name__)


class TokenAnalyzer:
    """
    Unified token analysis and optimization for GPT operations.
    
    Handles token counting, limit checking, response estimation,
    and similarity analysis for optimizing GPT usage.
    """
    
    # Token overhead estimates
    MESSAGE_OVERHEAD = 4  # Tokens for message formatting
    ROLE_TOKENS = {"system": 3, "user": 3, "assistant": 3}
    
    # Response estimation parameters
    TOKENS_PER_TEAM = 25  # Average tokens per team in response
    BASE_RESPONSE_TOKENS = 50  # Overhead for response structure
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """
        Initialize token analyzer.
        
        Args:
            model: OpenAI model name for encoding
        """
        self.model = model
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Unknown model {model}, using cl100k_base encoding")
            self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in plain text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        return len(self.encoder.encode(text))
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in chat message format.
        
        Accounts for role/content structure and message formatting overhead.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Total token count
        """
        if not messages:
            return 0
        
        total_tokens = 0
        
        for message in messages:
            # Add message formatting overhead
            total_tokens += self.MESSAGE_OVERHEAD
            
            # Add role tokens
            role = message.get("role", "user")
            total_tokens += self.ROLE_TOKENS.get(role, 3)
            
            # Add content tokens
            content = message.get("content", "")
            total_tokens += self.count_tokens(content)
        
        # Add conversation overhead
        total_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
        
        return total_tokens
    
    def check_within_limit(self, text: str, limit: int) -> bool:
        """
        Check if text is within token limit.
        
        Args:
            text: Text to check
            limit: Maximum allowed tokens
            
        Returns:
            True if within limit
        """
        return self.count_tokens(text) <= limit
    
    def check_prompt_limit(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        max_tokens: int = 128000,
        response_buffer: int = 4096
    ) -> None:
        """
        Check if prompts are within token limits.
        
        Args:
            system_prompt: System message
            user_prompt: User message
            max_tokens: Model's maximum context window
            response_buffer: Reserved tokens for response
            
        Raises:
            PicklistTokenLimitError: If prompts exceed limit
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        prompt_tokens = self.count_messages_tokens(messages)
        available_tokens = max_tokens - response_buffer
        
        if prompt_tokens > available_tokens:
            raise PicklistTokenLimitError(
                f"Prompt tokens ({prompt_tokens}) exceed limit "
                f"({available_tokens} available, {max_tokens} total, "
                f"{response_buffer} reserved for response)"
            )
        
        logger.debug(
            f"Token check passed: {prompt_tokens} tokens used, "
            f"{available_tokens - prompt_tokens} remaining"
        )
    
    def get_safe_limit(
        self, model_limit: int, response_tokens: int = 4096
    ) -> int:
        """
        Calculate safe input token limit.
        
        Args:
            model_limit: Model's maximum context window
            response_tokens: Expected response size
            
        Returns:
            Safe limit for input tokens
        """
        # Reserve 10% buffer for safety
        buffer = int(model_limit * 0.1)
        return model_limit - response_tokens - buffer
    
    def estimate_response_tokens(self, team_count: int) -> int:
        """
        Estimate response tokens based on team count.
        
        Args:
            team_count: Number of teams to rank
            
        Returns:
            Estimated token count
        """
        # Base tokens + (tokens per team * team count)
        estimated = self.BASE_RESPONSE_TOKENS + (self.TOKENS_PER_TEAM * team_count)
        
        # Add 20% buffer for safety
        return int(estimated * 1.2)
    
    def estimate_prompt_tokens(
        self, system_prompt: str, user_prompt: str
    ) -> int:
        """
        Estimate total prompt tokens.
        
        Args:
            system_prompt: System message
            user_prompt: User message
            
        Returns:
            Estimated token count
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.count_messages_tokens(messages)
    
    def calculate_response_similarity(
        self, response1: str, response2: str
    ) -> float:
        """
        Calculate similarity between two responses.
        
        Uses token-based overlap to determine similarity.
        
        Args:
            response1: First response
            response2: Second response
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not response1 or not response2:
            return 0.0
        
        # Tokenize both responses
        tokens1 = set(self.encoder.encode(response1))
        tokens2 = set(self.encoder.encode(response2))
        
        # Calculate Jaccard similarity
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def detect_repetition(self, text: str, min_length: int = 10) -> List[str]:
        """
        Detect repeated patterns in text.
        
        Args:
            text: Text to analyze
            min_length: Minimum pattern length to detect
            
        Returns:
            List of repeated patterns
        """
        patterns = []
        text_lower = text.lower()
        
        # Look for repeated substrings
        for length in range(min_length, len(text) // 2):
            for start in range(len(text) - length):
                pattern = text_lower[start:start + length]
                
                # Count occurrences
                count = text_lower.count(pattern)
                if count > 2:  # Pattern appears more than twice
                    # Avoid overlapping patterns
                    if not any(pattern in p or p in pattern for p in patterns):
                        patterns.append(text[start:start + length])
        
        return patterns
    
    def analyze_token_usage(
        self, prompts: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze token usage across multiple prompts.
        
        Args:
            prompts: List of prompts to analyze
            
        Returns:
            Dictionary with usage statistics
        """
        if not prompts:
            return {"error": "No prompts provided"}
        
        token_counts = [self.count_tokens(p) for p in prompts]
        
        return {
            "total_prompts": len(prompts),
            "total_tokens": sum(token_counts),
            "average_tokens": sum(token_counts) / len(token_counts),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "token_distribution": token_counts,
        }
    
    def suggest_optimizations(self, prompt: str) -> List[str]:
        """
        Suggest prompt optimizations to reduce token usage.
        
        Args:
            prompt: Prompt to optimize
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Check for verbose patterns
        verbose_patterns = [
            (r"\b(please|kindly|could you)\b", "Remove polite phrases"),
            (r"\b(in order to|for the purpose of)\b", "Simplify wordy phrases"),
            (r"\b(it is|there are|there is)\b", "Remove expletives"),
            (r"\s+", "Remove extra whitespace"),
        ]
        
        for pattern, suggestion in verbose_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                suggestions.append(suggestion)
        
        # Check for repetition
        repeated = self.detect_repetition(prompt)
        if repeated:
            suggestions.append(f"Remove repeated phrases: {', '.join(repeated[:3])}")
        
        # Check prompt length
        token_count = self.count_tokens(prompt)
        if token_count > 1000:
            suggestions.append(f"Consider splitting prompt (currently {token_count} tokens)")
        
        # Check for JSON formatting opportunities
        if prompt.count("\n") > 10:
            suggestions.append("Consider using compact JSON format for data")
        
        return suggestions
    
    def get_token_breakdown(
        self, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Get detailed token breakdown for messages.
        
        Args:
            messages: List of chat messages
            
        Returns:
            Detailed breakdown of token usage
        """
        breakdown = {
            "total_tokens": 0,
            "messages": [],
            "overhead": 0,
        }
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            content_tokens = self.count_tokens(content)
            
            message_info = {
                "role": role,
                "content_tokens": content_tokens,
                "role_tokens": self.ROLE_TOKENS.get(role, 3),
                "overhead": self.MESSAGE_OVERHEAD,
                "total": content_tokens + self.ROLE_TOKENS.get(role, 3) + self.MESSAGE_OVERHEAD,
            }
            
            breakdown["messages"].append(message_info)
            breakdown["total_tokens"] += message_info["total"]
            breakdown["overhead"] += message_info["role_tokens"] + message_info["overhead"]
        
        # Add conversation overhead
        breakdown["overhead"] += 3
        breakdown["total_tokens"] += 3
        
        return breakdown