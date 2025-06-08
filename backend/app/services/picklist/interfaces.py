"""
Interfaces for the picklist service components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol


class PicklistStrategy(ABC):
    """Abstract base class for picklist generation strategies."""

    @abstractmethod
    async def generate_ranking(
        self,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        game_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate a ranking of teams based on the strategy.

        Args:
            teams_data: List of team data dictionaries
            your_team_number: Your team's number for alliance compatibility
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric priorities with weights
            game_context: Optional game manual context

        Returns:
            List of ranked teams with scores and reasoning
        """
        pass


class CacheManager(Protocol):
    """Protocol for cache management."""

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from cache."""
        ...

    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        ...

    def delete(self, key: str) -> None:
        """Delete a value from cache."""
        ...

    def is_processing(self, key: str) -> bool:
        """Check if a key is currently being processed."""
        ...

    def mark_processing(self, key: str) -> None:
        """Mark a key as being processed."""
        ...


class ProgressReporter(Protocol):
    """Protocol for progress reporting."""

    def update(
        self,
        progress: int,
        message: str,
        current_step: Optional[str] = None,
        status: str = "active",
    ) -> None:
        """Update progress."""
        ...

    def complete(self, message: str) -> None:
        """Mark operation as complete."""
        ...

    def error(self, message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark operation as failed."""
        ...


class TeamDataProvider(Protocol):
    """Protocol for providing team data."""

    def get_all_teams(self) -> Dict[str, Any]:
        """Get all team data."""
        ...

    def get_team_by_number(self, team_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific team's data."""
        ...

    def prepare_for_gpt(self, exclude_teams: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Prepare team data for GPT consumption."""
        ...


class TokenCounter(Protocol):
    """Protocol for token counting."""

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        ...

    def check_within_limit(self, text: str, limit: int) -> bool:
        """Check if text is within token limit."""
        ...