"""
Main picklist service orchestrator.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .core import (
    GPTTokenCounter,
    PicklistCacheManager,
    PicklistProgressReporter,
    UnifiedDatasetProvider,
)
from .exceptions import (
    PicklistGenerationError,
    PicklistValidationError,
    TeamNotFoundException,
)
from .interfaces import PicklistStrategy
from .models import (
    PicklistGenerationRequest,
    PicklistGenerationResult,
    PickPosition,
    PriorityMetric,
    RankedTeam,
)
from .strategies import GPTStrategy

logger = logging.getLogger(__name__)


class PicklistService:
    """
    Main service for generating team picklists.
    
    This service orchestrates the picklist generation process using
    various strategies and manages caching, progress tracking, and
    error handling.
    """

    def __init__(
        self,
        dataset_path: str,
        strategy: Optional[PicklistStrategy] = None,
        cache_manager: Optional[PicklistCacheManager] = None,
    ):
        """
        Initialize picklist service.

        Args:
            dataset_path: Path to unified dataset JSON file
            strategy: Picklist generation strategy (defaults to GPT)
            cache_manager: Cache manager (defaults to in-memory)
        """
        self.data_provider = UnifiedDatasetProvider(dataset_path)
        self.strategy = strategy or GPTStrategy()
        self.cache_manager = cache_manager or PicklistCacheManager()
        self.token_counter = GPTTokenCounter()

    async def generate_picklist(
        self, request: PicklistGenerationRequest
    ) -> PicklistGenerationResult:
        """
        Generate a picklist based on the request parameters.

        Args:
            request: Picklist generation request

        Returns:
            Picklist generation result

        Raises:
            PicklistValidationError: If request validation fails
            TeamNotFoundException: If your team is not found
            PicklistGenerationError: If generation fails
        """
        # Validate request
        self._validate_request(request)

        # Create cache key if not provided
        cache_key = request.cache_key or self._create_cache_key(request)

        # Check cache first
        cached_result = await self._check_cache(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for key: {cache_key}")
            return cached_result

        # Mark as processing
        self.cache_manager.mark_processing(cache_key)

        # Create progress reporter
        progress_reporter = PicklistProgressReporter(cache_key)
        progress_reporter.update(5, "Starting picklist generation...", "initialization")

        try:
            # Get your team data
            your_team = self.data_provider.get_team_by_number(request.your_team_number)
            if not your_team:
                raise TeamNotFoundException(request.your_team_number)

            progress_reporter.update(10, "Preparing team data...", "data_preparation")

            # Prepare team data
            teams_data = self.data_provider.prepare_for_gpt(request.exclude_teams)
            game_context = self.data_provider.get_game_context()

            progress_reporter.update(20, "Generating rankings...", "ranking")

            # Convert request priorities to dict format for strategy
            priorities_dict = [
                {
                    "id": p.id,
                    "metric_id": p.id,
                    "name": p.name,
                    "weight": p.weight,
                }
                for p in request.priorities
            ]

            # Generate ranking using strategy
            if request.use_batching and len(teams_data) > request.batch_size:
                # Use batch processing for large datasets
                ranked_teams = await self._generate_with_batching(
                    teams_data, request, priorities_dict, game_context, progress_reporter
                )
            else:
                # Use single-shot generation
                progress_reporter.update(30, "Generating complete ranking...", "generation")
                
                ranked_teams = await self.strategy.generate_ranking(
                    teams_data=teams_data,
                    your_team_number=request.your_team_number,
                    pick_position=request.pick_position.value,
                    priorities=priorities_dict,
                    game_context=game_context,
                )

            progress_reporter.update(90, "Finalizing results...", "finalization")

            # Create result
            result = self._create_result(ranked_teams, teams_data)

            # Cache result
            self.cache_manager.set(cache_key, result.__dict__)

            progress_reporter.complete("Picklist generation completed successfully")

            return result

        except Exception as e:
            logger.error(f"Picklist generation failed: {e}")
            progress_reporter.error(str(e))
            
            # Clean up cache
            self.cache_manager.delete(cache_key)
            
            if isinstance(e, (PicklistValidationError, TeamNotFoundException)):
                raise
            raise PicklistGenerationError(f"Generation failed: {e}")

    async def _generate_with_batching(
        self,
        teams_data: List[Dict[str, Any]],
        request: PicklistGenerationRequest,
        priorities_dict: List[Dict[str, Any]],
        game_context: Optional[str],
        progress_reporter: PicklistProgressReporter,
    ) -> List[Dict[str, Any]]:
        """Generate picklist using batch processing."""
        logger.info(f"Using batch processing for {len(teams_data)} teams")
        
        # Create batches
        batches = []
        for i in range(0, len(teams_data), request.batch_size):
            batches.append(teams_data[i : i + request.batch_size])
        
        total_batches = len(batches)
        all_ranked_teams = []
        reference_teams = []
        
        for batch_idx, batch_teams in enumerate(batches):
            progress = 30 + int((batch_idx / total_batches) * 50)
            progress_reporter.update_batch_progress(
                batch_idx + 1, total_batches, f"Processing batch {batch_idx + 1}"
            )
            
            # Include reference teams with batch
            batch_with_references = reference_teams + batch_teams
            
            # Generate ranking for this batch
            batch_ranking = await self.strategy.generate_ranking(
                teams_data=batch_with_references,
                your_team_number=request.your_team_number,
                pick_position=request.pick_position.value,
                priorities=priorities_dict,
                game_context=game_context,
            )
            
            # Extract new teams (not references) from ranking
            reference_numbers = {t["team_number"] for t in reference_teams}
            new_ranked_teams = [
                t for t in batch_ranking if t["team_number"] not in reference_numbers
            ]
            
            all_ranked_teams.extend(new_ranked_teams)
            
            # Select reference teams for next batch
            if batch_idx < total_batches - 1:
                reference_teams = self._select_reference_teams(
                    new_ranked_teams, request.reference_teams_count
                )
        
        # Optionally re-rank all teams for final ordering
        if request.final_rerank and len(all_ranked_teams) > request.batch_size:
            progress_reporter.update(85, "Performing final re-ranking...", "reranking")
            
            # Store original count for validation
            original_count = len(all_ranked_teams)
            original_teams = all_ranked_teams.copy()
            
            logger.info(f"Starting final rerank with {original_count} teams")
            
            try:
                # Ensure unique teams before final rerank
                unique_teams_map = {team["team_number"]: team for team in all_ranked_teams}
                if len(unique_teams_map) != len(all_ranked_teams):
                    logger.warning(f"Found duplicates before final rerank: {len(all_ranked_teams)} -> {len(unique_teams_map)}")
                    all_ranked_teams = list(unique_teams_map.values())
                
                # Perform final rerank
                reranked_teams = await self.strategy.generate_ranking(
                    teams_data=all_ranked_teams,
                    your_team_number=request.your_team_number,
                    pick_position=request.pick_position.value,
                    priorities=priorities_dict,
                    game_context=game_context,
                )
                
                # Validate final rerank results
                if len(reranked_teams) < original_count * 0.8:  # Allow for some missing teams but not too many
                    logger.error(f"Final rerank returned too few teams: {len(reranked_teams)} vs expected {original_count}")
                    logger.info("Falling back to batch processing results")
                    all_ranked_teams = original_teams
                else:
                    logger.info(f"Final rerank successful: {len(reranked_teams)} teams")
                    all_ranked_teams = reranked_teams
                    
            except Exception as e:
                logger.error(f"Final rerank failed: {e}")
                logger.info("Falling back to batch processing results")
                all_ranked_teams = original_teams
        
        return all_ranked_teams

    def _select_reference_teams(
        self, ranked_teams: List[Dict[str, Any]], count: int
    ) -> List[Dict[str, Any]]:
        """Select reference teams for next batch."""
        if len(ranked_teams) <= count:
            return ranked_teams
        
        # Use top, middle, bottom strategy
        reference_teams = []
        
        # Always include top team
        reference_teams.append(ranked_teams[0])
        
        if count >= 2:
            # Include bottom team
            reference_teams.append(ranked_teams[-1])
        
        if count >= 3:
            # Include middle team
            middle_idx = len(ranked_teams) // 2
            reference_teams.append(ranked_teams[middle_idx])
        
        return reference_teams

    def _validate_request(self, request: PicklistGenerationRequest) -> None:
        """Validate picklist generation request."""
        if not request.priorities:
            raise PicklistValidationError("No priority metrics provided")
        
        if request.batch_size < 5:
            raise PicklistValidationError("Batch size must be at least 5")
        
        if request.reference_teams_count < 0:
            raise PicklistValidationError("Reference teams count cannot be negative")
        
        if request.reference_teams_count > request.batch_size // 2:
            raise PicklistValidationError(
                "Reference teams count cannot exceed half of batch size"
            )

    def _create_cache_key(self, request: PicklistGenerationRequest) -> str:
        """Create cache key from request parameters."""
        priorities_str = "|".join(
            f"{p.id}:{p.weight}" for p in sorted(request.priorities, key=lambda x: x.id)
        )
        exclude_str = "|".join(str(t) for t in sorted(request.exclude_teams))
        
        return f"picklist_{request.your_team_number}_{request.pick_position.value}_{priorities_str}_{exclude_str}"

    async def _check_cache(self, cache_key: str) -> Optional[PicklistGenerationResult]:
        """Check cache for existing result."""
        cached_data = self.cache_manager.get(cache_key)
        
        if cached_data:
            # Convert dict back to result object
            return PicklistGenerationResult(**cached_data)
        
        # Check if processing
        if self.cache_manager.is_processing(cache_key):
            logger.info(f"Found in-progress generation for key: {cache_key}")
            
            # Wait for processing to complete
            cached_data = self.cache_manager.wait_for_processing(cache_key)
            if cached_data:
                return PicklistGenerationResult(**cached_data)
        
        return None

    def _create_result(
        self, ranked_teams: List[Dict[str, Any]], all_teams: List[Dict[str, Any]]
    ) -> PicklistGenerationResult:
        """Create picklist generation result."""
        # Convert to RankedTeam objects
        ranked_team_objects = [
            RankedTeam(
                team_number=t["team_number"],
                nickname=t.get("nickname", f"Team {t['team_number']}"),
                score=t.get("score", 0.0),
                reasoning=t.get("reasoning", ""),
                rank=idx + 1,
            )
            for idx, t in enumerate(ranked_teams)
        ]
        
        # Find missing teams
        ranked_numbers = {t.team_number for t in ranked_team_objects}
        all_numbers = {t["team_number"] for t in all_teams}
        missing_numbers = list(all_numbers - ranked_numbers)
        
        # Create minimal analysis
        analysis = {
            "draft_reasoning": "Analysis optimized for token efficiency",
            "evaluation": f"Ranked {len(ranked_team_objects)} teams successfully",
            "final_recommendations": "Review rankings and adjust based on latest match data",
        }
        
        return PicklistGenerationResult(
            status="success",
            picklist=ranked_team_objects,
            analysis=analysis,
            missing_team_numbers=missing_numbers,
            performance={
                "team_count": len(all_teams),
                "ranked_count": len(ranked_team_objects),
                "missing_count": len(missing_numbers),
            },
        )

    def get_batch_processing_status(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get status of batch processing operation."""
        return self.cache_manager.get_processing_status(cache_key)