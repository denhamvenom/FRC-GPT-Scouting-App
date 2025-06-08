"""
Batch processing logic for picklist generation.

This module handles the batching of large team datasets to optimize
token usage and improve generation performance.
"""

import logging
from typing import Any, Dict, List, Optional, Protocol

from .models import PicklistGenerationRequest, PriorityMetric

logger = logging.getLogger(__name__)


class PicklistStrategyProtocol(Protocol):
    """Protocol for picklist generation strategies."""
    
    async def generate_ranking(
        self,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        game_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate ranking for teams."""
        ...


class ProgressReporterProtocol(Protocol):
    """Protocol for progress reporting."""
    
    def update(self, percentage: int, message: str, status: str) -> None:
        """Update progress."""
        ...
    
    def update_batch_progress(
        self, current_batch: int, total_batches: int, message: str
    ) -> None:
        """Update batch processing progress."""
        ...


class BatchProcessor:
    """
    Handles batch processing of large team datasets.
    
    This processor divides large datasets into manageable batches,
    processes them sequentially with reference teams for continuity,
    and optionally performs a final re-ranking.
    """
    
    def __init__(self, strategy: PicklistStrategyProtocol):
        """
        Initialize batch processor.
        
        Args:
            strategy: Picklist generation strategy to use
        """
        self.strategy = strategy
    
    async def process_in_batches(
        self,
        teams_data: List[Dict[str, Any]],
        request: PicklistGenerationRequest,
        priorities_dict: List[Dict[str, Any]],
        game_context: Optional[str],
        progress_reporter: ProgressReporterProtocol,
    ) -> List[Dict[str, Any]]:
        """
        Process teams in batches to optimize token usage.
        
        Args:
            teams_data: List of team data dictionaries
            request: Picklist generation request
            priorities_dict: Priority metrics in dict format
            game_context: Game-specific context
            progress_reporter: Progress reporting callback
            
        Returns:
            List of ranked teams
        """
        logger.info(
            f"Starting batch processing for {len(teams_data)} teams "
            f"with batch size {request.batch_size}"
        )
        
        # Create batches
        batches = self._create_batches(teams_data, request.batch_size)
        total_batches = len(batches)
        
        logger.info(f"Created {total_batches} batches")
        
        all_ranked_teams = []
        reference_teams = []
        
        # Process each batch
        for batch_idx, batch_teams in enumerate(batches):
            # Calculate progress (30-80% range for batch processing)
            progress = 30 + int((batch_idx / total_batches) * 50)
            progress_reporter.update(
                progress, 
                f"Processing batch {batch_idx + 1} of {total_batches}", 
                "batch_processing"
            )
            progress_reporter.update_batch_progress(
                batch_idx + 1, 
                total_batches, 
                f"Ranking {len(batch_teams)} teams"
            )
            
            # Include reference teams from previous batches
            batch_with_references = reference_teams + batch_teams
            
            logger.debug(
                f"Batch {batch_idx + 1}: {len(batch_teams)} new teams, "
                f"{len(reference_teams)} reference teams"
            )
            
            # Generate ranking for this batch
            try:
                batch_ranking = await self.strategy.generate_ranking(
                    teams_data=batch_with_references,
                    your_team_number=request.your_team_number,
                    pick_position=request.pick_position.value,
                    priorities=priorities_dict,
                    game_context=game_context,
                )
            except Exception as e:
                logger.error(f"Failed to process batch {batch_idx + 1}: {e}")
                raise
            
            # Extract new teams (not references) from ranking
            new_ranked_teams = self._extract_new_teams(
                batch_ranking, reference_teams
            )
            
            all_ranked_teams.extend(new_ranked_teams)
            
            logger.debug(
                f"Batch {batch_idx + 1} complete: {len(new_ranked_teams)} teams ranked"
            )
            
            # Select reference teams for next batch
            if batch_idx < total_batches - 1:
                reference_teams = self._select_reference_teams(
                    new_ranked_teams, request.reference_teams_count
                )
        
        # Perform final re-ranking if requested
        if request.final_rerank and len(all_ranked_teams) > request.batch_size:
            logger.info("Performing final re-ranking of all teams")
            progress_reporter.update(
                85, "Performing final re-ranking...", "reranking"
            )
            
            all_ranked_teams = await self._final_rerank(
                all_ranked_teams,
                request,
                priorities_dict,
                game_context,
            )
        
        logger.info(f"Batch processing complete: {len(all_ranked_teams)} teams ranked")
        return all_ranked_teams
    
    def _create_batches(
        self, teams_data: List[Dict[str, Any]], batch_size: int
    ) -> List[List[Dict[str, Any]]]:
        """
        Divide teams into batches.
        
        Args:
            teams_data: List of all teams
            batch_size: Maximum teams per batch
            
        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(teams_data), batch_size):
            batches.append(teams_data[i : i + batch_size])
        return batches
    
    def _extract_new_teams(
        self,
        batch_ranking: List[Dict[str, Any]],
        reference_teams: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extract only new teams from batch ranking.
        
        Args:
            batch_ranking: Complete ranking including references
            reference_teams: Reference teams included in batch
            
        Returns:
            List of newly ranked teams
        """
        reference_numbers = {t["team_number"] for t in reference_teams}
        return [
            team for team in batch_ranking 
            if team["team_number"] not in reference_numbers
        ]
    
    def _select_reference_teams(
        self, ranked_teams: List[Dict[str, Any]], count: int
    ) -> List[Dict[str, Any]]:
        """
        Select reference teams for continuity between batches.
        
        Uses a strategy of selecting top, middle, and bottom teams
        to provide ranking context for the next batch.
        
        Args:
            ranked_teams: Teams ranked in current batch
            count: Number of reference teams to select
            
        Returns:
            List of reference teams
        """
        if not ranked_teams or count <= 0:
            return []
        
        if len(ranked_teams) <= count:
            return ranked_teams
        
        reference_teams = []
        
        # Always include top team
        reference_teams.append(ranked_teams[0])
        
        if count >= 2:
            # Include bottom team
            reference_teams.append(ranked_teams[-1])
        
        if count >= 3:
            # Include middle team(s)
            middle_count = count - 2
            step = len(ranked_teams) // (middle_count + 1)
            
            for i in range(1, middle_count + 1):
                idx = i * step
                if idx < len(ranked_teams) - 1:  # Avoid duplicating bottom team
                    reference_teams.append(ranked_teams[idx])
        
        # Ensure we don't exceed requested count
        return reference_teams[:count]
    
    async def _final_rerank(
        self,
        all_ranked_teams: List[Dict[str, Any]],
        request: PicklistGenerationRequest,
        priorities_dict: List[Dict[str, Any]],
        game_context: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Perform final re-ranking of all teams.
        
        Args:
            all_ranked_teams: All teams ranked in batches
            request: Original request parameters
            priorities_dict: Priority metrics
            game_context: Game context
            
        Returns:
            Final ranked list of all teams
        """
        try:
            return await self.strategy.generate_ranking(
                teams_data=all_ranked_teams,
                your_team_number=request.your_team_number,
                pick_position=request.pick_position.value,
                priorities=priorities_dict,
                game_context=game_context,
            )
        except Exception as e:
            logger.error(f"Final re-ranking failed: {e}")
            # Return original order if re-ranking fails
            return all_ranked_teams
    
    def validate_batch_parameters(
        self, batch_size: int, reference_count: int, total_teams: int
    ) -> None:
        """
        Validate batch processing parameters.
        
        Args:
            batch_size: Teams per batch
            reference_count: Reference teams per batch
            total_teams: Total number of teams
            
        Raises:
            ValueError: If parameters are invalid
        """
        if batch_size < 5:
            raise ValueError("Batch size must be at least 5")
        
        if reference_count < 0:
            raise ValueError("Reference teams count cannot be negative")
        
        if reference_count > batch_size // 2:
            raise ValueError(
                "Reference teams count cannot exceed half of batch size"
            )
        
        if batch_size > total_teams:
            logger.warning(
                f"Batch size ({batch_size}) exceeds total teams ({total_teams}). "
                "Will process in single batch."
            )