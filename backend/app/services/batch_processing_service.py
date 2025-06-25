# backend/app/services/batch_processing_service.py

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from app.services.progress_tracker import ProgressTracker

logger = logging.getLogger("batch_processing_service")


class BatchProcessingService:
    """
    Service for handling batch processing workflows and progress tracking.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    """

    def __init__(self, cache: Dict[str, Any]):
        """
        Initialize the batch processing service.
        
        Args:
            cache: Shared cache for storing batch processing status
        """
        self.cache = cache

    def should_use_batching(self, teams_count: int, batch_size: int, use_batching: bool) -> bool:
        """
        Determine if batch processing should be used based on team count and settings.
        
        Args:
            teams_count: Number of teams to process
            batch_size: Size of each batch
            use_batching: Whether batching is enabled
            
        Returns:
            True if batch processing should be used
        """
        return use_batching and teams_count > batch_size

    def calculate_batch_info(self, teams_count: int, batch_size: int) -> Dict[str, int]:
        """
        Calculate batch processing information.
        
        Args:
            teams_count: Total number of teams
            batch_size: Size of each batch
            
        Returns:
            Dictionary with batch calculation results
        """
        total_batches = (teams_count + batch_size - 1) // batch_size  # Ceiling division
        
        return {
            "total_batches": total_batches,
            "batch_size": batch_size,
            "teams_count": teams_count,
            "last_batch_size": teams_count % batch_size or batch_size
        }

    def initialize_batch_processing(self, cache_key: str, total_batches: int) -> None:
        """
        Initialize batch processing in cache with initial status.
        
        Args:
            cache_key: Cache key for this operation
            total_batches: Total number of batches to process
        """
        self.cache[cache_key] = {
            "status": "in_progress",
            "batch_processing": {
                "total_batches": total_batches,
                "current_batch": 0,
                "progress_percentage": 0,
                "processing_complete": False,
                "start_time": time.time(),
                "batch_results": [],
                "errors": []
            },
        }

    def update_batch_progress(self, cache_key: str, current_batch: int, batch_result: Optional[Dict[str, Any]] = None) -> None:
        """
        Update batch processing progress in cache.
        
        Args:
            cache_key: Cache key for this operation
            current_batch: Current batch number (0-indexed)
            batch_result: Result of completed batch (optional)
        """
        if cache_key not in self.cache:
            logger.warning(f"Cache key {cache_key} not found for progress update")
            return

        cache_data = self.cache[cache_key]
        if "batch_processing" not in cache_data:
            logger.warning(f"Batch processing data not found for {cache_key}")
            return

        batch_info = cache_data["batch_processing"]
        total_batches = batch_info["total_batches"]
        
        # Update current batch and progress
        batch_info["current_batch"] = current_batch + 1  # 1-indexed for display
        batch_info["progress_percentage"] = ((current_batch + 1) / total_batches) * 100
        
        # Store batch result if provided
        if batch_result is not None:
            if batch_result.get("status") == "success":
                batch_info["batch_results"].append(batch_result)
            else:
                batch_info["errors"].append({
                    "batch": current_batch,
                    "error": batch_result.get("error", "Unknown error"),
                    "timestamp": time.time()
                })

        # Mark as complete if all batches done
        if current_batch + 1 >= total_batches:
            batch_info["processing_complete"] = True
            batch_info["end_time"] = time.time()

    def get_batch_processing_status(self, cache_key: str) -> Dict[str, Any]:
        """
        Get the current status of batch processing operation.
        
        Args:
            cache_key: Cache key to check status for
            
        Returns:
            Dictionary with current batch processing status
        """
        if cache_key not in self.cache:
            return {"status": "not_found"}

        cached_data = self.cache[cache_key]

        # Handle timestamp (initial processing state)
        if isinstance(cached_data, float):
            return {
                "status": "in_progress",
                "batch_processing": {
                    "total_batches": 0,
                    "current_batch": 0,
                    "progress_percentage": 0,
                    "processing_complete": False,
                    "start_time": cached_data,
                },
            }

        # Handle active batch processing
        elif isinstance(cached_data, dict) and "batch_processing" in cached_data:
            batch_info = cached_data["batch_processing"]
            
            # Calculate estimated time remaining
            estimated_time_remaining = None
            if batch_info["current_batch"] > 0 and not batch_info["processing_complete"]:
                elapsed_time = time.time() - batch_info["start_time"]
                time_per_batch = elapsed_time / batch_info["current_batch"]
                remaining_batches = batch_info["total_batches"] - batch_info["current_batch"]
                estimated_time_remaining = time_per_batch * remaining_batches

            status = "in_progress"
            if batch_info["processing_complete"]:
                status = "error" if batch_info["errors"] else "success"

            return {
                "status": status,
                "batch_processing": {
                    "total_batches": batch_info["total_batches"],
                    "current_batch": batch_info["current_batch"],
                    "progress_percentage": batch_info["progress_percentage"],
                    "processing_complete": batch_info["processing_complete"],
                    "start_time": batch_info["start_time"],
                    "estimated_time_remaining": estimated_time_remaining,
                    "batches_completed": len(batch_info["batch_results"]),
                    "error_count": len(batch_info["errors"]),
                    "errors": batch_info["errors"][-3:] if batch_info["errors"] else []  # Last 3 errors
                },
            }

        # Handle completed non-batch processing
        else:
            return {
                "status": "success",
                "batch_processing": {
                    "total_batches": 1,
                    "current_batch": 1,
                    "progress_percentage": 100,
                    "processing_complete": True,
                },
            }

    def combine_batch_results(
        self, 
        batch_results: List[Dict[str, Any]], 
        reference_teams_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Combine results from multiple batches with score normalization.
        
        Args:
            batch_results: List of batch processing results
            reference_teams_count: Number of reference teams for normalization
            
        Returns:
            Combined and normalized picklist
        """
        if not batch_results:
            return []

        # Extract picklists from batch results
        all_picklists = []
        for result in batch_results:
            if result.get("status") == "success" and "picklist" in result:
                all_picklists.extend(result["picklist"])

        if not all_picklists:
            logger.warning("No successful picklists found in batch results")
            return []

        # Two-pass algorithm for score normalization
        
        # First pass: Collect reference team scores for normalization
        reference_team_scores = {}
        batch_adjustments = {}
        
        for batch_idx, result in enumerate(batch_results):
            if result.get("status") != "success" or "picklist" not in result:
                continue
                
            picklist = result["picklist"]
            reference_teams = result.get("reference_teams", [])
            
            # Collect scores for reference teams
            for ref_team in reference_teams[:reference_teams_count]:
                team_num = ref_team.get("team_number")
                if team_num:
                    if team_num not in reference_team_scores:
                        reference_team_scores[team_num] = []
                    
                    # Find this team's score in current batch
                    for team in picklist:
                        if team.get("team_number") == team_num:
                            reference_team_scores[team_num].append({
                                "batch": batch_idx,
                                "score": team.get("score", 0.0)
                            })
                            break

        # Calculate normalization factors
        for team_num, scores in reference_team_scores.items():
            if len(scores) > 1:
                scores.sort(key=lambda x: x["score"], reverse=True)
                base_score = scores[0]["score"]  # Highest score as baseline
                
                for score_data in scores:
                    batch_idx = score_data["batch"]
                    if batch_idx not in batch_adjustments:
                        batch_adjustments[batch_idx] = []
                    
                    if score_data["score"] > 0:
                        adjustment = base_score / score_data["score"]
                        batch_adjustments[batch_idx].append(adjustment)

        # Calculate average adjustment per batch
        for batch_idx in batch_adjustments:
            adjustments = batch_adjustments[batch_idx]
            if adjustments:
                batch_adjustments[batch_idx] = sum(adjustments) / len(adjustments)
            else:
                batch_adjustments[batch_idx] = 1.0

        # Second pass: Apply normalization and combine
        final_picklist = []
        seen_teams = set()
        
        for batch_idx, result in enumerate(batch_results):
            if result.get("status") != "success" or "picklist" not in result:
                continue
                
            adjustment_factor = batch_adjustments.get(batch_idx, 1.0)
            
            for team in result["picklist"]:
                team_num = team.get("team_number")
                
                # Skip duplicates (keep first occurrence)
                if team_num in seen_teams:
                    continue
                    
                seen_teams.add(team_num)
                
                # Apply normalization
                normalized_team = team.copy()
                original_score = team.get("score", 0.0)
                normalized_score = original_score * adjustment_factor
                normalized_team["score"] = round(normalized_score, 2)
                
                # Add batch information for debugging
                normalized_team["batch_info"] = {
                    "batch": batch_idx,
                    "original_score": original_score,
                    "adjustment_factor": round(adjustment_factor, 3)
                }
                
                final_picklist.append(normalized_team)

        # Sort by normalized score (highest first)
        final_picklist.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        logger.info(f"Combined {len(batch_results)} batches into {len(final_picklist)} teams")
        
        return final_picklist

    def select_reference_teams(
        self,
        ranked_teams: List[Dict[str, Any]],
        reference_teams_count: int,
        reference_selection: str = "top_middle_bottom"
    ) -> List[Dict[str, Any]]:
        """
        Select reference teams for batch processing score normalization.
        
        Args:
            ranked_teams: List of teams ranked by score
            reference_teams_count: Number of reference teams to select
            reference_selection: Selection strategy
            
        Returns:
            List of selected reference teams
        """
        if not ranked_teams or reference_teams_count <= 0:
            return []

        teams_count = len(ranked_teams)
        reference_teams = []

        if reference_selection == "top_middle_bottom":
            # Distribute reference teams across performance tiers
            if reference_teams_count >= 3 and teams_count >= 3:
                # Top tier
                reference_teams.append(ranked_teams[0])
                
                # Middle tier
                middle_idx = teams_count // 2
                reference_teams.append(ranked_teams[middle_idx])
                
                # Bottom tier (but not last to avoid outliers)
                bottom_idx = min(teams_count - 2, int(teams_count * 0.8))
                reference_teams.append(ranked_teams[bottom_idx])
                
                # Additional teams from top if needed
                for i in range(3, reference_teams_count):
                    if i < teams_count:
                        reference_teams.append(ranked_teams[i])
            else:
                # Fallback to top teams
                for i in range(min(reference_teams_count, teams_count)):
                    reference_teams.append(ranked_teams[i])

        elif reference_selection == "percentile":
            # Select teams at specific percentiles
            percentiles = [0.1, 0.3, 0.5, 0.7, 0.9]
            for i in range(min(reference_teams_count, len(percentiles))):
                idx = int(teams_count * percentiles[i])
                idx = min(idx, teams_count - 1)
                reference_teams.append(ranked_teams[idx])

        elif reference_selection == "even_distribution":
            # Evenly distribute across the entire list
            if reference_teams_count > 1:
                step = teams_count / (reference_teams_count - 1)
                for i in range(reference_teams_count):
                    idx = min(int(i * step), teams_count - 1)
                    reference_teams.append(ranked_teams[idx])
            else:
                reference_teams.append(ranked_teams[0])

        else:
            # Default: top teams
            for i in range(min(reference_teams_count, teams_count)):
                reference_teams.append(ranked_teams[i])

        return reference_teams

    def create_team_batches(
        self, 
        teams_data: List[Dict[str, Any]], 
        batch_size: int
    ) -> List[List[Dict[str, Any]]]:
        """
        Split team data into batches for processing.
        
        Args:
            teams_data: List of team data to batch
            batch_size: Size of each batch
            
        Returns:
            List of team data batches
        """
        batches = []
        for i in range(0, len(teams_data), batch_size):
            batch = teams_data[i:i + batch_size]
            batches.append(batch)
        
        return batches

    async def process_batches_with_progress(
        self,
        cache_key: str,
        batch_processor_func,
        batches: List[List[Dict[str, Any]]],
        reference_teams: List[Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process batches with progress tracking and error handling.
        
        Args:
            cache_key: Cache key for progress tracking
            batch_processor_func: Function to process each batch
            batches: List of team data batches
            reference_teams: Reference teams for normalization
            **kwargs: Additional arguments for batch processor
            
        Returns:
            List of batch processing results
        """
        batch_results = []
        total_batches = len(batches)
        
        # Initialize batch processing
        self.initialize_batch_processing(cache_key, total_batches)
        
        # Create progress tracker
        progress_tracker = ProgressTracker.create_tracker(cache_key)
        progress_tracker.update_progress(0, f"Starting batch processing ({total_batches} batches)")

        for batch_idx, batch_teams in enumerate(batches):
            try:
                # Update progress
                progress_msg = f"Processing batch {batch_idx + 1} of {total_batches}"
                progress_tracker.update_progress(
                    (batch_idx / total_batches) * 100, 
                    progress_msg
                )

                # Process the batch
                batch_result = await batch_processor_func(
                    teams_data=batch_teams,
                    reference_teams=reference_teams,
                    batch_index=batch_idx,
                    cache_key=cache_key,
                    **kwargs
                )

                # Update batch progress
                self.update_batch_progress(cache_key, batch_idx, batch_result)
                
                if batch_result.get("status") == "success":
                    batch_results.append(batch_result)
                    logger.info(f"Batch {batch_idx + 1} completed successfully")
                else:
                    error_msg = f"Batch {batch_idx + 1} failed: {batch_result.get('error', 'Unknown error')}"
                    logger.error(error_msg)
                    
                    # Continue processing other batches rather than fail completely
                    batch_results.append({
                        "status": "error",
                        "error": batch_result.get("error", "Unknown error"),
                        "batch_index": batch_idx
                    })

            except Exception as e:
                error_msg = f"Exception in batch {batch_idx + 1}: {str(e)}"
                logger.error(error_msg)
                
                # Record the error and continue
                batch_result = {
                    "status": "error",
                    "error": error_msg,
                    "batch_index": batch_idx
                }
                self.update_batch_progress(cache_key, batch_idx, batch_result)
                batch_results.append(batch_result)

            # Small delay between batches to prevent rate limiting
            if batch_idx < total_batches - 1:
                await asyncio.sleep(0.5)

        # Complete progress tracking
        successful_batches = sum(1 for r in batch_results if r.get("status") == "success")
        if successful_batches > 0:
            progress_tracker.complete(f"Batch processing completed: {successful_batches}/{total_batches} successful")
        else:
            progress_tracker.fail("All batches failed")

        return batch_results

    def finalize_batch_processing(self, cache_key: str, final_result: Dict[str, Any]) -> None:
        """
        Finalize batch processing by storing the final result in cache.
        
        Args:
            cache_key: Cache key for this operation
            final_result: Final processed result to store
        """
        if cache_key in self.cache:
            # Store final result, replacing batch processing status
            self.cache[cache_key] = final_result
            logger.info(f"Batch processing finalized for {cache_key}")
        else:
            logger.warning(f"Cache key {cache_key} not found for finalization")