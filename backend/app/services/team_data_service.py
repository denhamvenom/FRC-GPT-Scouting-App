"""Service for handling team data preparation and validation."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.services.picklist_generator_service import PicklistGeneratorService


class TeamDataService:
    """Handles team data preparation and validation for comparison."""
    
    def __init__(self, unified_dataset_path: str) -> None:
        self.generator = PicklistGeneratorService(unified_dataset_path)
    
    def prepare_teams_data(self, team_numbers: List[int]) -> Tuple[List[Dict[str, Any]], Dict[int, int]]:
        """Prepare team data and create index mapping.
        
        Args:
            team_numbers: List of team numbers to prepare data for
            
        Returns:
            Tuple of (teams_data, team_index_map)
            
        Raises:
            ValueError: If any teams are not found in dataset
        """
        teams_data_all = self.generator._prepare_team_data_for_gpt()
        teams_data = [t for t in teams_data_all if t["team_number"] in team_numbers]
        
        # Validate all teams found
        if len(teams_data) != len(team_numbers):
            found = {t["team_number"] for t in teams_data}
            missing = [n for n in team_numbers if n not in found]
            raise ValueError(f"Teams not found in dataset: {missing}")
        
        # Sort to preserve order and create index mapping
        teams_data.sort(key=lambda t: team_numbers.index(t["team_number"]))
        team_index_map = {i + 1: t["team_number"] for i, t in enumerate(teams_data)}
        
        return teams_data, team_index_map