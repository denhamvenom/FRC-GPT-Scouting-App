"""
Legacy adapter for OpenAI client compatibility.

This adapter provides backward compatibility for existing services that use
direct OpenAI API calls, wrapping the new OpenAIClient with the old interface.
"""

import logging
from typing import Any, Dict, List, Optional

from ..openai_client import OpenAIClient
from ..factories import get_openai_client

logger = logging.getLogger(__name__)


class OpenAILegacyAdapter:
    """
    Legacy adapter for OpenAI API compatibility.
    
    This class provides the same interface as the original OpenAI usage patterns
    in the codebase while delegating to the new OpenAIClient implementation.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 100000,
        temperature: float = 0.1,
    ):
        """
        Initialize legacy adapter.
        
        Args:
            api_key: OpenAI API key
            model: Default model to use
            max_tokens: Maximum tokens per request
            temperature: Default temperature
        """
        self.default_model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Get the new client implementation
        self.client = get_openai_client(
            api_key=api_key,
            default_model=model,
            max_tokens=max_tokens,
        )
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text (legacy interface).
        
        Args:
            text: Text to count tokens for
            model: Model to use for counting
            
        Returns:
            Number of tokens
        """
        return self.client.count_tokens(text, model or self.default_model)
    
    def count_message_tokens(
        self, messages: List[Dict[str, str]], model: Optional[str] = None
    ) -> int:
        """
        Count tokens in messages (legacy interface).
        
        Args:
            messages: List of messages in OpenAI format
            model: Model to use for counting
            
        Returns:
            Total token count
        """
        return self.client.count_message_tokens(messages, model or self.default_model)
    
    def check_token_limit(
        self, system_prompt: str, user_prompt: str, model: Optional[str] = None
    ) -> None:
        """
        Check if prompts exceed token limit (legacy interface).
        
        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            model: Model to use for counting
            
        Raises:
            Exception: If token limit exceeded
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        total_tokens = self.count_message_tokens(messages, model)
        if total_tokens > self.max_tokens:
            raise Exception(
                f"Token limit exceeded: {total_tokens} > {self.max_tokens}"
            )
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate completion (legacy interface returning just content).
        
        Args:
            messages: Messages in OpenAI format
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text content
        """
        result = await self.client.generate_completion(
            messages=messages,
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
            **kwargs
        )
        
        return result["completion"]
    
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create chat completion (legacy interface with full response).
        
        Args:
            messages: Messages in OpenAI format
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Full API response in legacy format
        """
        result = await self.client.generate_completion(
            messages=messages,
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
            **kwargs
        )
        
        # Convert to legacy response format
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": result["completion"]
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": result["usage"],
            "model": result["model"],
            "id": result["metadata"]["completion_id"],
        }
    
    async def validate_api_key(self) -> bool:
        """
        Validate API key (legacy interface).
        
        Returns:
            True if API key is valid
        """
        return await self.client.validate_api_key()
    
    def create_system_prompt(self, pick_position: str, team_count: int) -> str:
        """
        Create system prompt for picklist generation (legacy interface).
        
        Args:
            pick_position: Pick position (first, second, third)
            team_count: Number of teams to rank
            
        Returns:
            System prompt text
        """
        role_descriptions = {
            "first": "a strong, versatile robot that excels in multiple game aspects",
            "second": "a reliable partner that complements existing alliance strengths", 
            "third": "a specialized robot that fills specific alliance needs",
        }
        
        return f"""You are an expert FRC (FIRST Robotics Competition) strategist analyzing teams for alliance selection.

PICK POSITION: You are picking the {pick_position} robot for your alliance.
This means you need {role_descriptions.get(pick_position, 'a strategic partner')}.

TASK: Rank exactly {team_count} teams based on:
1. Their overall performance metrics
2. Strategic fit for the {pick_position} pick position  
3. Reliability and consistency
4. How well they complement your team

OUTPUT FORMAT: You MUST respond with ONLY a valid JSON object in this exact format:
{{
  "p": [
    [team_number, score, "brief reason"],
    [team_number, score, "brief reason"],
    ...
  ],
  "s": "ok"
}}

Where:
- "p" contains exactly {team_count} teams ranked from best to worst
- Each team is [number, score_0_to_100, "one_sentence_reason"]
- "s" should be "ok" if successful
- Use compact reasoning (under 20 words per team)
- Include ALL {team_count} teams in your ranking

Remember: You are looking for the {pick_position} pick, so prioritize teams that would be effective in that role."""


# Singleton instance for backward compatibility
_legacy_adapter_instance: Optional[OpenAILegacyAdapter] = None


def get_legacy_openai_adapter(**kwargs) -> OpenAILegacyAdapter:
    """
    Get singleton instance of legacy OpenAI adapter.
    
    Args:
        **kwargs: Configuration parameters
        
    Returns:
        Legacy adapter instance
    """
    global _legacy_adapter_instance
    
    if _legacy_adapter_instance is None:
        _legacy_adapter_instance = OpenAILegacyAdapter(**kwargs)
        logger.info("Created legacy OpenAI adapter instance")
    
    return _legacy_adapter_instance


def reset_legacy_adapter() -> None:
    """Reset the legacy adapter instance (useful for testing)."""
    global _legacy_adapter_instance
    _legacy_adapter_instance = None