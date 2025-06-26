# backend/app/services/picklist_generator_service.py

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import tiktoken
from app.services.progress_tracker import ProgressTracker
from dotenv import load_dotenv
from openai import OpenAI

# Import all decomposed services
from app.services.data_aggregation_service import DataAggregationService
from app.services.team_analysis_service import TeamAnalysisService
from app.services.priority_calculation_service import PriorityCalculationService
from app.services.batch_processing_service import BatchProcessingService
from app.services.performance_optimization_service import PerformanceOptimizationService
from app.services.picklist_gpt_service import PicklistGPTService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("picklist_generator.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("picklist_generator")

# Load environment variables
load_dotenv()

# Allow model selection via environment with a sensible default
GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class PicklistGeneratorService:
    """
    Orchestrator service that coordinates 6 decomposed services
    while maintaining exact API compatibility with baseline.
    
    This service transforms from a 3,113-line monolith to a lightweight
    orchestrator that delegates functionality to focused services.
    """

    # Class-level cache to share across instances (CRITICAL: Preserve for compatibility)
    _picklist_cache = {}

    def __init__(self, unified_dataset_path: str):
        """Initialize the picklist generator with the unified dataset."""
        # Initialize orchestrated services
        self.data_service = DataAggregationService(unified_dataset_path)
        self.team_analysis = TeamAnalysisService(self.data_service.get_teams_data())
        self.priority_service = PriorityCalculationService()
        self.performance_service = PerformanceOptimizationService(self._picklist_cache)
        self.batch_service = BatchProcessingService(self._picklist_cache)
        self.gpt_service = PicklistGPTService()
        
        # Preserve baseline attributes for API compatibility
        self.dataset_path = unified_dataset_path
        self.dataset = self.data_service.dataset
        self.teams_data = self.data_service.teams_data
        self.year = self.data_service.year
        self.event_key = self.data_service.event_key
        self.game_context = self.data_service.load_game_context()
        self.token_encoder = self.gpt_service.token_encoder

    async def generate_picklist(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        exclude_teams: Optional[List[int]] = None,
        request_id: Optional[int] = None,
        cache_key: Optional[str] = None,
        batch_size: int = 60,
        reference_teams_count: int = 3,
        reference_selection: str = "top_middle_bottom",
        use_batching: bool = False,
        final_rerank: bool = True,
    ) -> Dict[str, Any]:
        """Generate a ranked picklist for alliance selection."""
        start_time = time.time()
        
        # Cache management
        if not cache_key:
            cache_key = self.performance_service.generate_cache_key(
                your_team_number, pick_position, priorities, exclude_teams, len(self.teams_data)
            )
        
        cached_result = self.performance_service.get_cached_result(cache_key)
        if cached_result and cached_result.get("status") == "success":
            logger.info(f"Returning cached result for key: {cache_key}")
            return cached_result
        
        # Initialize progress tracking
        from app.services.progress_tracker import ProgressTracker
        progress_tracker = ProgressTracker.create_tracker(cache_key)
        progress_tracker.update(5, "Initializing picklist generation...", "initialization")
        
        self.performance_service.mark_cache_processing(cache_key)
        
        try:
            # Data preparation
            progress_tracker.update(15, "Preparing team data...", "data_preparation")
            teams_data = self.data_service.get_teams_for_analysis(exclude_teams)
            normalized_priorities = self.priority_service.normalize_priorities(priorities)
            
            # ORIGINAL AUTOMATIC BATCHING DECISION - EXACT RESTORATION
            progress_tracker.update(25, "Determining processing strategy...", "strategy_selection")
            should_batch, batching_reason = self._determine_processing_strategy(teams_data, use_batching)
            
            if should_batch:
                # Use batch_size from request parameters, or calculate optimal if not provided
                optimal_batch_size = batch_size if batch_size else self._calculate_optimal_batch_size(len(teams_data), len(normalized_priorities))
                logger.info(f"Using batch processing for {len(teams_data)} teams with batch size {optimal_batch_size}")
                progress_tracker.update(35, f"Starting batch processing ({len(teams_data)} teams)...", "batch_processing")
                result = await self._orchestrate_batch_processing(
                    teams_data, your_team_number, pick_position, normalized_priorities,
                    cache_key, optimal_batch_size, reference_teams_count, reference_selection, final_rerank,
                    progress_tracker
                )
            else:
                logger.info(f"Using single processing for {len(teams_data)} teams")
                progress_tracker.update(35, f"Starting single processing ({len(teams_data)} teams)...", "single_processing")
                result = await self._orchestrate_single_processing(
                    teams_data, your_team_number, pick_position, normalized_priorities, cache_key
                )
                progress_tracker.update(90, "Finalizing results...", "finalization")
            
            result["processing_time"] = time.time() - start_time
            self.performance_service.store_cached_result(cache_key, result)
            progress_tracker.complete("Picklist generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in generate_picklist: {str(e)}")
            progress_tracker.fail(f"Picklist generation failed: {str(e)}")
            error_result = {
                "status": "error", "error": str(e), "cache_key": cache_key,
                "processing_time": time.time() - start_time
            }
            self.performance_service.store_cached_result(cache_key, error_result)
            return error_result

    async def rank_missing_teams(
        self,
        existing_picklist: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        exclude_teams: Optional[List[int]] = None,
        request_id: Optional[int] = None,
        cache_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rank teams that are missing from the existing picklist."""
        start_time = time.time()
        
        try:
            # Identify missing teams
            existing_team_numbers = {team.get("team_number") for team in existing_picklist}
            all_teams = self.data_service.get_teams_for_analysis(exclude_teams)
            missing_team_numbers = [
                team["team_number"] for team in all_teams 
                if team["team_number"] not in existing_team_numbers
            ]
            
            if not missing_team_numbers:
                return {
                    "status": "success", "picklist": [], "total_teams": 0,
                    "processing_time": time.time() - start_time
                }
            
            logger.info(f"Ranking {len(missing_team_numbers)} missing teams")
            
            # Execute GPT analysis
            normalized_priorities = self.priority_service.normalize_priorities(priorities)
            analysis_result = await self.gpt_service.analyze_teams(
                system_prompt=self.gpt_service.create_missing_teams_system_prompt(
                    pick_position, len(missing_team_numbers)
                ),
                user_prompt=self.gpt_service.create_missing_teams_user_prompt(
                    missing_team_numbers, existing_picklist, your_team_number,
                    pick_position, normalized_priorities, all_teams
                ),
                teams_data=all_teams
            )
            
            if analysis_result.get("status") == "success":
                return {
                    "status": "success",
                    "picklist": analysis_result["picklist"],
                    "total_teams": len(analysis_result["picklist"]),
                    "processing_time": time.time() - start_time,
                    "cache_key": cache_key
                }
            else:
                return {
                    "status": "error",
                    "error": analysis_result.get("error", "Analysis failed"),
                    "cache_key": cache_key,
                    "processing_time": time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Error in rank_missing_teams: {str(e)}")
            return {
                "status": "error", "error": str(e), "cache_key": cache_key,
                "processing_time": time.time() - start_time
            }

    def get_batch_processing_status(self, cache_key: str) -> Dict[str, Any]:
        """Get the current status of a batch processing job."""
        return self.batch_service.get_batch_processing_status(cache_key)

    def merge_and_update_picklist(
        self, existing_picklist: List[Dict[str, Any]], new_rankings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge a new picklist with an existing one, handling duplicates.
        
        Args:
            existing_picklist: Current picklist with team rankings
            new_rankings: New team rankings to merge (higher scores take precedence)
            
        Returns:
            Merged and sorted picklist with updated team rankings
            
        Raises:
            ValueError: If input data is invalid
        """
        try:
            # Input validation
            if existing_picklist is None:
                existing_picklist = []
            if new_rankings is None:
                new_rankings = []
                
            if not isinstance(existing_picklist, list):
                raise ValueError("existing_picklist must be a list")
            if not isinstance(new_rankings, list):
                raise ValueError("new_rankings must be a list")
            
            # Merge teams, giving preference to higher scores
            combined_teams = existing_picklist + new_rankings
            seen_teams = {}
            
            for team in combined_teams:
                if not isinstance(team, dict):
                    logger.warning(f"Skipping invalid team data: {team}")
                    continue
                    
                team_number = team.get("team_number")
                if team_number is None:
                    logger.warning(f"Skipping team without team_number: {team}")
                    continue
                
                # Keep team with higher score, or first occurrence if scores are equal
                if (team_number not in seen_teams or 
                    team.get("score", 0) > seen_teams[team_number].get("score", 0)):
                    seen_teams[team_number] = team
            
            # Sort by score (highest first)
            merged_picklist = sorted(
                seen_teams.values(), 
                key=lambda x: x.get("score", 0), 
                reverse=True
            )
            
            logger.info(
                f"Merged picklist: {len(existing_picklist)} + {len(new_rankings)} = "
                f"{len(merged_picklist)} teams"
            )
            
            return merged_picklist
            
        except Exception as e:
            logger.error(f"Error merging picklists: {str(e)}")
            raise

    async def _orchestrate_batch_processing(
        self, teams_data, your_team_number, pick_position, normalized_priorities,
        cache_key, batch_size, reference_teams_count, reference_selection, final_rerank,
        progress_tracker=None
    ) -> Dict[str, Any]:
        """Coordinate batch processing following baseline logic"""
        # Create simple batches like baseline
        team_batches = []
        for i in range(0, len(teams_data), batch_size):
            team_batches.append(teams_data[i:i + batch_size])
        
        logger.info(f"Split teams into {len(team_batches)} batches")
        
        # Process each batch sequentially like baseline
        batch_results = []
        combined_picklist = []
        reference_teams = []
        total_batches = len(team_batches)
        
        for batch_index, batch in enumerate(team_batches):
            # Update progress for each batch
            batch_progress = 35 + (batch_index / total_batches) * 50  # 35-85% for batch processing
            if progress_tracker:
                progress_tracker.update(
                    batch_progress, 
                    f"Processing batch {batch_index + 1}/{total_batches} ({len(batch)} teams)...", 
                    f"batch_{batch_index + 1}"
                )
            
            logger.info(f"Processing batch {batch_index + 1}/{total_batches} with {len(batch)} teams")
            
            # Create batch-specific prompts using available methods
            # Use index mapping for batches to prevent duplicates
            team_index_map = {}
            for index, team in enumerate(batch, 1):
                team_index_map[index] = team["team_number"]
            
            system_prompt = self.gpt_service.create_system_prompt(
                pick_position, len(batch), self.game_context, use_ultra_compact=True
            )
            
            # Use reference teams prompt if we have reference teams
            if reference_teams:
                user_prompt = self.gpt_service.create_user_prompt_with_reference_teams(
                    your_team_number, pick_position, normalized_priorities, batch, reference_teams,
                    team_index_map=team_index_map
                )
            else:
                user_prompt, _ = self.gpt_service.create_user_prompt(
                    your_team_number, pick_position, normalized_priorities, batch,
                    team_numbers=[t["team_number"] for t in batch],
                    force_index_mapping=True
                )
            
            # Process batch with GPT
            batch_result = await self.gpt_service.analyze_teams(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                teams_data=batch,
                team_index_map=team_index_map
            )
            
            if batch_result.get("status") == "success":
                batch_results.append(batch_result)
                batch_picklist = batch_result.get("picklist", [])
                combined_picklist.extend(batch_picklist)
                
                # Select reference teams from this batch for next batch (like baseline)
                if batch_index < len(team_batches) - 1:  # Don't need reference teams after last batch
                    reference_teams = self.team_analysis.select_reference_teams(
                        batch_picklist, reference_teams_count, reference_selection
                    )
                    logger.info(f"Selected {len(reference_teams)} reference teams for next batch")
            else:
                logger.error(f"Batch {batch_index + 1} failed: {batch_result.get('error', 'Unknown error')}")
        
        # Optional final reranking
        if final_rerank and len(combined_picklist) > 10:
            if progress_tracker:
                progress_tracker.update(85, "Performing final reranking...", "final_reranking")
            logger.info("Performing final reranking of combined results")
            
            # Convert combined_picklist back to raw team data format for final reranking
            final_teams_data = []
            for result in combined_picklist:
                team_number = result.get("team_number")
                if team_number:
                    # Try both string and int keys since teams_data might use string keys
                    team_key = str(team_number)
                    if team_key in self.teams_data:
                        final_teams_data.append(self.teams_data[team_key])
                    elif team_number in self.teams_data:
                        final_teams_data.append(self.teams_data[team_number])
                    else:
                        logger.warning(f"Team {team_number} not found in teams_data")
            
            # Only proceed with final reranking if we have teams
            if len(final_teams_data) > 0:
                # Create index mapping for final reranking
                team_index_map = {}
                for index, team in enumerate(final_teams_data, 1):
                    team_index_map[index] = team["team_number"]
                
                user_prompt, _ = self.gpt_service.create_user_prompt(
                    your_team_number, pick_position, normalized_priorities, final_teams_data,
                    team_numbers=[t["team_number"] for t in final_teams_data],
                    force_index_mapping=True
                )
                
                final_result = await self.gpt_service.analyze_teams(
                    system_prompt=self.gpt_service.create_system_prompt(
                        pick_position, len(final_teams_data), self.game_context
                    ),
                    user_prompt=user_prompt,
                    teams_data=final_teams_data,
                    team_index_map=team_index_map
                )
                if final_result.get("status") == "success":
                    combined_picklist = final_result["picklist"]
            else:
                logger.warning("No teams found for final reranking, skipping")
        
        # Final progress update
        if progress_tracker:
            progress_tracker.update(95, "Finalizing batch processing results...", "finalization")
        
        return {
            "status": "success", "picklist": combined_picklist,
            "total_teams": len(combined_picklist), "cache_key": cache_key,
            "batch_processing": True, "batches_processed": len(batch_results)
        }

    def _determine_processing_strategy(self, teams_data: List[Dict[str, Any]], use_batching: Optional[bool] = None) -> Tuple[bool, str]:
        """ORIGINAL AUTOMATIC BATCHING DECISION - EXACT RESTORATION"""
        
        team_count = len(teams_data)
        
        # UPDATED LOGIC: Automatic batching for >80 teams (more reasonable threshold)
        if use_batching is None:
            # Auto-decide based on team count (UPDATED THRESHOLD FOR MODERN GPT)
            should_batch = team_count > 80
            reason = f"Auto-selected {'batching' if should_batch else 'single'} for {team_count} teams (threshold: 80)"
        else:
            # Respect explicit user choice - ALWAYS honor the user's decision
            should_batch = use_batching
            reason = f"User-specified {'batching' if should_batch else 'single'} for {team_count} teams"
            
            # Log information but don't override user choice
            if team_count > 80 and not use_batching:
                logger.info(f"Single processing requested for {team_count} teams")
            elif team_count <= 30 and use_batching:
                logger.info(f"Batching requested for {team_count} teams")
        
        logger.info(f"Processing strategy: {reason}")
        return should_batch, reason

    def _calculate_optimal_batch_size(self, team_count: int, priorities_count: int) -> int:
        """ORIGINAL BATCH SIZE CALCULATION - EXACT RESTORATION"""
        
        # ORIGINAL CONSTANTS
        base_batch_size = 20
        max_batch_size = 25
        min_batch_size = 15
        
        # Adjust based on priorities complexity (original had this logic)
        if priorities_count > 5:
            adjusted_size = base_batch_size - 2
        elif priorities_count > 3:
            adjusted_size = base_batch_size - 1
        else:
            adjusted_size = base_batch_size
        
        # Ensure within bounds
        final_size = max(min_batch_size, min(max_batch_size, adjusted_size))
        
        logger.debug(f"Calculated batch size: {final_size} for {team_count} teams with {priorities_count} priorities")
        return final_size

    async def _orchestrate_single_processing(
        self, teams_data, your_team_number, pick_position, normalized_priorities, cache_key
    ) -> Dict[str, Any]:
        """ORIGINAL SINGLE PROCESSING WITH INDEX MAPPING - EXACT RESTORATION"""
        
        # ALWAYS use index mapping for single processing (original did this)
        team_index_map = {}
        for index, team in enumerate(teams_data, 1):
            team_index_map[index] = team["team_number"]
        
        logger.info(f"Single processing {len(teams_data)} teams with index mapping to prevent duplicates")
        
        # Create prompts with index mapping
        system_prompt = self.gpt_service.create_system_prompt(
            pick_position, len(teams_data), self.game_context, use_ultra_compact=True
        )
        
        user_prompt, _ = self.gpt_service.create_user_prompt(
            your_team_number, pick_position, normalized_priorities, teams_data,
            team_numbers=[t["team_number"] for t in teams_data],
            force_index_mapping=True
        )
        
        # Execute analysis with full error recovery
        analysis_result = await self.gpt_service.analyze_teams(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            teams_data=teams_data,
            team_index_map=team_index_map
        )
        
        if analysis_result.get("status") == "success":
            picklist = analysis_result["picklist"]
            
            # ORIGINAL MISSING TEAM DETECTION AND HANDLING
            final_picklist = await self._handle_missing_teams(
                picklist, teams_data, your_team_number, pick_position, normalized_priorities
            )
            
            return {
                "status": "success", 
                "picklist": final_picklist,
                "total_teams": len(final_picklist), 
                "cache_key": cache_key,
                "processing_strategy": "single_with_index_mapping"
            }
        else:
            return {
                "status": "error", 
                "error": analysis_result.get("error", "Analysis failed"),
                "cache_key": cache_key
            }

    async def _handle_missing_teams(
        self,
        picklist: List[Dict[str, Any]],
        all_teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """ORIGINAL MISSING TEAM HANDLING - EXACT RESTORATION"""
        
        # ORIGINAL SET DIFFERENCE CALCULATION
        available_team_numbers = {team["team_number"] for team in all_teams_data}
        ranked_team_numbers = {team["team_number"] for team in picklist}
        missing_team_numbers = available_team_numbers - ranked_team_numbers
        
        if not missing_team_numbers:
            logger.info("No missing teams detected")
            return picklist
        
        logger.warning(f"Missing {len(missing_team_numbers)} teams: {sorted(missing_team_numbers)}")
        
        # ORIGINAL MISSING TEAM RANKING WITH SMALLER BATCH SIZE
        missing_teams_data = [t for t in all_teams_data if t["team_number"] in missing_team_numbers]
        
        try:
            missing_result = await self.gpt_service.analyze_teams(
                system_prompt=self.gpt_service.create_missing_teams_system_prompt(
                    pick_position, len(missing_teams_data)
                ),
                user_prompt=self.gpt_service.create_missing_teams_user_prompt(
                    list(missing_team_numbers), picklist, your_team_number,
                    pick_position, priorities, missing_teams_data
                ),
                teams_data=missing_teams_data
            )
            
            if missing_result.get("status") == "success":
                missing_picklist = missing_result.get("picklist", [])
                logger.info(f"Successfully ranked {len(missing_picklist)} missing teams")
                
                # MERGE WITH ORIGINAL PICKLIST
                combined_picklist = picklist + missing_picklist
                
                # ORIGINAL DEDUPLICATION AND SORTING
                seen_teams = {}
                for team in combined_picklist:
                    team_number = team.get("team_number")
                    if team_number not in seen_teams or team.get("score", 0) > seen_teams[team_number].get("score", 0):
                        seen_teams[team_number] = team
                
                final_list = sorted(seen_teams.values(), key=lambda x: x.get("score", 0), reverse=True)
                logger.info(f"Final picklist: {len(final_list)} teams after missing team integration")
                return final_list
            
        except Exception as e:
            logger.error(f"Failed to rank missing teams: {str(e)}")
        
        logger.warning("Using original picklist without missing teams")
        return picklist