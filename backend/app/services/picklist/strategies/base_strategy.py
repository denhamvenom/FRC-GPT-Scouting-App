"""
Base strategy class for picklist generation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..interfaces import PicklistStrategy
from ..models import RankedTeam, TeamMetrics

logger = logging.getLogger(__name__)


class BaseStrategy(PicklistStrategy, ABC):
    """Base class for picklist generation strategies."""

    def __init__(self):
        """Initialize the base strategy."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_weighted_score(
        self, team_metrics: Dict[str, float], priorities: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate a weighted score for a team based on priorities.

        Args:
            team_metrics: Dictionary of metric values
            priorities: List of priority metrics with weights

        Returns:
            Weighted score
        """
        total_score = 0.0
        total_weight = 0.0

        for priority in priorities:
            metric_id = priority.get("id", priority.get("metric_id"))
            weight = float(priority.get("weight", 1.0))

            if metric_id in team_metrics:
                metric_value = float(team_metrics[metric_id])
                total_score += metric_value * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def filter_teams(
        self, teams_data: List[Dict[str, Any]], exclude_teams: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter teams based on exclusion list.

        Args:
            teams_data: List of team data
            exclude_teams: Optional list of team numbers to exclude

        Returns:
            Filtered list of teams
        """
        if not exclude_teams:
            return teams_data

        return [team for team in teams_data if team.get("team_number") not in exclude_teams]

    def validate_inputs(
        self,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
    ) -> None:
        """
        Validate inputs for picklist generation.

        Args:
            teams_data: List of team data
            your_team_number: Your team's number
            pick_position: Pick position
            priorities: Priority metrics

        Raises:
            ValueError: If inputs are invalid
        """
        if not teams_data:
            raise ValueError("No teams data provided")

        if not priorities:
            raise ValueError("No priority metrics provided")

        valid_positions = ["first", "second", "third"]
        if pick_position not in valid_positions:
            raise ValueError(f"Invalid pick position: {pick_position}")

        # Check if your team exists in the data
        team_numbers = [team.get("team_number") for team in teams_data]
        if your_team_number not in team_numbers:
            self.logger.warning(f"Your team {your_team_number} not found in teams data")

    def sort_by_score(self, ranked_teams: List[RankedTeam]) -> List[RankedTeam]:
        """
        Sort teams by their score in descending order.

        Args:
            ranked_teams: List of ranked teams

        Returns:
            Sorted list of teams
        """
        return sorted(ranked_teams, key=lambda x: x.score, reverse=True)

    @abstractmethod
    async def generate_ranking(
        self,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        game_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate team ranking - must be implemented by subclasses."""
        pass