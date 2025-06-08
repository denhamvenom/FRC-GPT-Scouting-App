"""
Custom exceptions for the picklist service.
"""

from typing import Any, Dict, Optional


class PicklistGenerationError(Exception):
    """Base exception for picklist generation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class PicklistValidationError(PicklistGenerationError):
    """Raised when input validation fails."""

    pass


class TokenLimitExceededError(PicklistGenerationError):
    """Raised when the token limit for GPT is exceeded."""

    def __init__(self, message: str, token_count: int, max_tokens: int):
        super().__init__(message)
        self.token_count = token_count
        self.max_tokens = max_tokens
        self.details = {
            "token_count": token_count,
            "max_tokens": max_tokens,
            "exceeded_by": token_count - max_tokens,
        }


class PicklistTokenLimitError(TokenLimitExceededError):
    """Raised when token limits are exceeded in picklist operations."""
    
    pass


class GPTResponseError(PicklistGenerationError):
    """Raised when GPT response parsing fails."""

    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message)
        self.raw_response = raw_response
        self.details = {"raw_response": raw_response}


class TeamNotFoundException(PicklistGenerationError):
    """Raised when a requested team is not found in the dataset."""

    def __init__(self, team_number: int):
        super().__init__(f"Team {team_number} not found in dataset")
        self.team_number = team_number
        self.details = {"team_number": team_number}


class CacheError(PicklistGenerationError):
    """Raised when cache operations fail."""

    pass


class BatchProcessingError(PicklistGenerationError):
    """Raised when batch processing encounters an error."""

    def __init__(self, message: str, batch_index: int, batch_count: int):
        super().__init__(message)
        self.batch_index = batch_index
        self.batch_count = batch_count
        self.details = {
            "batch_index": batch_index,
            "batch_count": batch_count,
        }