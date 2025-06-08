"""
Adapter service to maintain backward compatibility with existing API.

This adapter bridges the gap between the old PicklistGeneratorService interface
and the new refactored service architecture.
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.picklist import PicklistService
from app.services.picklist.models import (
    PicklistGenerationRequest,
    PickPosition,
    PriorityMetric,
    ReferenceSelectionStrategy,
)

logger = logging.getLogger(__name__)


class PicklistServiceAdapter:
    """
    Adapter to maintain compatibility with the original PicklistGeneratorService API.
    
    This class wraps the new PicklistService and provides the same interface
    as the original service, allowing existing code to work without changes.
    """

    # Class-level cache for backward compatibility
    _picklist_cache = {}

    def __init__(self, unified_dataset_path: str):
        """
        Initialize the adapter with the unified dataset path.

        Args:
            unified_dataset_path: Path to the unified dataset JSON file
        """
        self.dataset_path = unified_dataset_path
        self.service = PicklistService(unified_dataset_path)

        # Copy some attributes for backward compatibility
        self.dataset = self.service.data_provider.dataset
        self.teams_data = self.service.data_provider.teams_data
        self.year = self.service.data_provider.year
        self.event_key = self.service.data_provider.event_key

    async def generate_picklist(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        exclude_teams: Optional[List[int]] = None,
        request_id: Optional[int] = None,
        cache_key: Optional[str] = None,
        batch_size: int = 20,
        reference_teams_count: int = 3,
        reference_selection: str = "top_middle_bottom",
        use_batching: bool = False,
        final_rerank: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate picklist using the new service architecture.

        This method maintains the exact same interface as the original
        PicklistGeneratorService.generate_picklist method.
        """
        try:
            # Convert old format to new request model
            priority_metrics = []
            for priority in priorities:
                priority_metrics.append(
                    PriorityMetric(
                        id=priority.get("id", priority.get("metric_id", "")),
                        name=priority.get("name", priority.get("id", "")),
                        weight=float(priority.get("weight", 1.0)),
                        description=priority.get("reason"),
                    )
                )

            # Map pick position
            pick_pos_map = {
                "first": PickPosition.FIRST,
                "second": PickPosition.SECOND,
                "third": PickPosition.THIRD,
            }
            pick_pos = pick_pos_map.get(pick_position, PickPosition.FIRST)

            # Map reference selection strategy
            ref_strategy_map = {
                "even_distribution": ReferenceSelectionStrategy.EVEN_DISTRIBUTION,
                "percentile": ReferenceSelectionStrategy.PERCENTILE,
                "top_middle_bottom": ReferenceSelectionStrategy.TOP_MIDDLE_BOTTOM,
            }
            ref_strategy = ref_strategy_map.get(
                reference_selection, ReferenceSelectionStrategy.TOP_MIDDLE_BOTTOM
            )

            # Create new request
            request = PicklistGenerationRequest(
                your_team_number=your_team_number,
                pick_position=pick_pos,
                priorities=priority_metrics,
                exclude_teams=exclude_teams or [],
                request_id=request_id,
                cache_key=cache_key,
                batch_size=batch_size,
                reference_teams_count=reference_teams_count,
                reference_selection=ref_strategy,
                use_batching=use_batching,
                final_rerank=final_rerank,
            )

            # Generate using new service
            result = await self.service.generate_picklist(request)

            # Convert result back to old format
            return self._convert_result_to_old_format(result)

        except Exception as e:
            logger.error(f"Picklist generation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "picklist": [],
                "analysis": {},
                "missing_team_numbers": [],
                "performance": {},
            }

    def _convert_result_to_old_format(self, result) -> Dict[str, Any]:
        """Convert new result format to old format."""
        # Convert RankedTeam objects to dictionaries
        picklist = []
        for team in result.picklist:
            picklist.append(
                {
                    "team_number": team.team_number,
                    "nickname": team.nickname,
                    "score": team.score,
                    "reasoning": team.reasoning,
                }
            )

        return {
            "status": result.status,
            "picklist": picklist,
            "analysis": result.analysis,
            "missing_team_numbers": result.missing_team_numbers,
            "performance": result.performance,
            "error_message": result.error_message,
        }

    def get_batch_processing_status(self, cache_key: str) -> Dict[str, Any]:
        """Get batch processing status - delegate to new service."""
        status = self.service.get_batch_processing_status(cache_key)
        return status or {}

    def _get_team_by_number(self, team_number: int) -> Optional[Dict[str, Any]]:
        """Get team by number - delegate to data provider."""
        return self.service.data_provider.get_team_by_number(team_number)

    def _prepare_team_data_for_gpt(self) -> List[Dict[str, Any]]:
        """Prepare team data for GPT - delegate to data provider."""
        return self.service.data_provider.prepare_for_gpt()

    # Additional methods for backward compatibility
    async def rank_missing_teams(
        self,
        existing_picklist: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        all_teams_data: List[Dict[str, Any]],
        exclude_teams: Optional[List[int]] = None,
        game_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Rank missing teams (simplified implementation).
        
        For now, this delegates to the main generate_picklist method
        with the missing teams.
        """
        # Extract team numbers from existing picklist
        existing_numbers = {team["team_number"] for team in existing_picklist}
        
        # Find missing teams
        all_numbers = {team["team_number"] for team in all_teams_data}
        missing_numbers = list(all_numbers - existing_numbers)
        
        # If no missing teams, return empty result
        if not missing_numbers:
            return {
                "status": "success",
                "picklist": [],
                "missing_team_numbers": [],
            }
        
        # Generate picklist for missing teams only
        # We'll exclude the existing teams and only rank the missing ones
        exclude_existing = list(existing_numbers)
        if exclude_teams:
            exclude_existing.extend(exclude_teams)
        
        result = await self.generate_picklist(
            your_team_number=your_team_number,
            pick_position=pick_position,
            priorities=priorities,
            exclude_teams=exclude_existing,
            use_batching=False,  # Use simple approach for missing teams
        )
        
        return result

    def merge_and_update_picklist(
        self,
        existing_picklist: List[Dict[str, Any]],
        user_rankings: List[Dict[str, Any]],
        missing_teams: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge and update picklist with user rankings.
        
        This is a simplified implementation that maintains the original behavior.
        """
        # Create a lookup for user rankings by team number
        user_rank_map = {ranking["team_number"]: ranking for ranking in user_rankings}
        
        # Start with existing picklist
        updated_picklist = []
        
        # Apply user rankings first
        for ranking in sorted(user_rankings, key=lambda x: x["position"]):
            team_number = ranking["team_number"]
            
            # Find the team in existing picklist or missing teams
            team_data = None
            for team in existing_picklist + missing_teams:
                if team["team_number"] == team_number:
                    team_data = team.copy()
                    break
            
            if team_data:
                team_data["user_rank"] = ranking["position"]
                updated_picklist.append(team_data)
        
        # Add remaining teams that weren't user-ranked
        user_ranked_numbers = {r["team_number"] for r in user_rankings}
        
        for team in existing_picklist:
            if team["team_number"] not in user_ranked_numbers:
                updated_picklist.append(team)
        
        # Add missing teams that weren't user-ranked
        for team in missing_teams:
            if team["team_number"] not in user_ranked_numbers:
                updated_picklist.append(team)
        
        return updated_picklist