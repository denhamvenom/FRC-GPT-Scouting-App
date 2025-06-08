"""
Team data provider for picklist service.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ..exceptions import TeamNotFoundException
from ..interfaces import TeamDataProvider

logger = logging.getLogger(__name__)


class UnifiedDatasetProvider(TeamDataProvider):
    """Provider for team data from unified dataset."""

    def __init__(self, dataset_path: str):
        """
        Initialize provider with dataset path.

        Args:
            dataset_path: Path to unified dataset JSON file
        """
        self.dataset_path = dataset_path
        self.dataset = self._load_dataset()
        self.teams_data = self.dataset.get("teams", {})
        self.year = self.dataset.get("year", 2025)
        self.event_key = self.dataset.get("event_key", f"{self.year}arc")

    def _load_dataset(self) -> Dict[str, Any]:
        """Load unified dataset from file."""
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Dataset file not found: {self.dataset_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in dataset file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return {}

    def get_all_teams(self) -> Dict[str, Any]:
        """Get all team data."""
        return self.teams_data

    def get_team_by_number(self, team_number: int) -> Optional[Dict[str, Any]]:
        """Get specific team's data."""
        team_str = str(team_number)
        return self.teams_data.get(team_str)

    def prepare_for_gpt(self, exclude_teams: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Prepare condensed team data for GPT consumption.

        Args:
            exclude_teams: Optional list of team numbers to exclude

        Returns:
            List of team data dictionaries optimized for GPT
        """
        condensed_teams = []

        for team_number_str, team_data in self.teams_data.items():
            # Skip invalid team numbers
            try:
                team_number = int(team_number_str)
            except (ValueError, TypeError):
                continue

            # Skip excluded teams
            if exclude_teams and team_number in exclude_teams:
                continue

            # Create condensed team info
            team_info = {
                "team_number": team_number,
                "nickname": team_data.get("nickname", f"Team {team_number}"),
                "metrics": {},
                "match_count": len(team_data.get("scouting_data", [])),
            }

            # Calculate average metrics from scouting data
            scouting_metrics = self._calculate_scouting_averages(team_data.get("scouting_data", []))
            team_info["metrics"].update(scouting_metrics)

            # Add Statbotics metrics
            statbotics_info = team_data.get("statbotics_info", {})
            for key, value in statbotics_info.items():
                if isinstance(value, (int, float)):
                    team_info["metrics"][f"statbotics_{key}"] = value

            # Add ranking info
            ranking_info = team_data.get("ranking_info", {})
            if ranking_info.get("rank") is not None:
                team_info["rank"] = ranking_info["rank"]
            if ranking_info.get("record"):
                team_info["record"] = ranking_info["record"]

            # Add limited superscouting notes
            superscouting_notes = self._extract_superscouting_notes(
                team_data.get("superscouting_data", [])
            )
            if superscouting_notes:
                team_info["superscouting_notes"] = superscouting_notes[:1]  # Limit to save tokens

            condensed_teams.append(team_info)

        return condensed_teams

    def _calculate_scouting_averages(self, scouting_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average metrics from scouting data."""
        metrics = {}
        metric_values = {}

        # Collect all numeric values
        for match in scouting_data:
            for key, value in match.items():
                if isinstance(value, (int, float)) and key not in [
                    "team_number",
                    "match_number",
                    "qual_number",
                ]:
                    if key not in metric_values:
                        metric_values[key] = []
                    metric_values[key].append(value)

        # Calculate averages
        for metric, values in metric_values.items():
            if values:
                metrics[metric] = sum(values) / len(values)

        return metrics

    def _extract_superscouting_notes(self, superscouting_data: List[Dict[str, Any]]) -> List[str]:
        """Extract relevant notes from superscouting data."""
        notes = []
        
        # Only use the most recent entry to save tokens
        for entry in superscouting_data[:1]:
            if entry.get("strategy_notes"):
                notes.append(entry["strategy_notes"])
            elif entry.get("comments"):
                notes.append(entry["comments"])

        return notes

    def get_game_context(self) -> Optional[str]:
        """Load game manual text for context."""
        try:
            # Navigate from backend/app/services/picklist/core/ to backend/app/data/
            # __file__ is at: backend/app/services/picklist/core/team_data_provider.py
            # We need to go: ../../../../app/data/
            services_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend/app/services
            app_dir = os.path.dirname(services_dir)  # backend/app
            data_dir = os.path.join(app_dir, "data")  # backend/app/data
            manual_text_path = os.path.join(data_dir, f"manual_text_{self.year}.json")

            logger.debug(f"Looking for game manual at: {manual_text_path}")
            
            if os.path.exists(manual_text_path):
                logger.debug(f"Loading game manual for year {self.year}")
                with open(manual_text_path, "r", encoding="utf-8") as f:
                    manual_data = json.load(f)
                    game_name = manual_data.get("game_name", "")
                    relevant_sections = manual_data.get("relevant_sections", "")
                    game_context = f"Game: {game_name}\n\n{relevant_sections}"
                    logger.info(f"Loaded game context: {len(game_context)} characters")
                    return game_context
            else:
                logger.warning(f"Game manual file not found at: {manual_text_path}")
            
            return None
        except Exception as e:
            logger.error(f"Error loading game context: {e}")
            return None

    def get_team_count(self) -> int:
        """Get total number of teams."""
        return len(self.teams_data)

    def get_event_info(self) -> Dict[str, Any]:
        """Get event information from dataset."""
        return {
            "year": self.year,
            "event_key": self.event_key,
            "team_count": self.get_team_count(),
        }