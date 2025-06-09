# backend/app/api/picklist_generator.py
"""
Picklist Generator API Module

This module provides endpoints for generating, updating, and managing picklists.
Refactored to use standardized schemas and thin controller pattern.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.common import CacheKeyRequest, SuccessResponse
from app.api.schemas.picklist import (
    ClearCacheRequest,
    PicklistGenerateRequest,
    PicklistGenerateResponse,
    PicklistUpdateRequest,
    PicklistUpdateResponse,
    RankMissingTeamsRequest,
    RankMissingTeamsResponse,
)
from app.api.utils import (
    format_success_response,
    handle_service_error,
    standardize_response,
)
from app.services.picklist_service_adapter import PicklistServiceAdapter

# Configure logging
logger = logging.getLogger("picklist_api")

router = APIRouter(prefix="/api/picklist", tags=["Picklist"])


@router.post("/generate", response_model=PicklistGenerateResponse)
async def generate_picklist(request: PicklistGenerateRequest):
    """Generate a ranked picklist using GPT based on team data and priorities."""
    try:
        # Initialize service
        service = PicklistServiceAdapter(request.unified_dataset_path)

        # Convert priorities to dict format
        priorities = [p.dict() for p in request.priorities]

        # Generate cache key if not provided
        if request.cache_key:
            cache_key = request.cache_key
        else:
            import time
            # Create operation_id compatible with frontend expectations and progress tracker
            # Format: {team}_{position}_{timestamp}
            timestamp = int(time.time() * 1000)  # milliseconds like frontend expects
            cache_key = f"{request.your_team_number}_{request.pick_position}_{timestamp}"

        # Store operation_id in both cache systems for compatibility
        PicklistServiceAdapter._picklist_cache[cache_key] = "initializing"
        logger.info(f"Starting picklist generation with cache_key: {cache_key}, use_batching: {request.use_batching}")

        # Call service method
        result = await service.generate_picklist(
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=priorities,
            exclude_teams=request.exclude_teams,
            cache_key=cache_key,
            batch_size=request.batch_size,
            reference_teams_count=request.reference_teams_count,
            reference_selection=request.reference_selection,
            use_batching=request.use_batching,
        )

        # Store result in cache for status endpoint
        PicklistServiceAdapter._picklist_cache[cache_key] = result
        logger.info(f"Stored picklist result in cache with {len(result.get('picklist', []))} teams")

        # Add cache key to response
        result["cache_key"] = cache_key
        return PicklistGenerateResponse(**result)

    except Exception as e:
        logger.error(f"Error generating picklist: {str(e)}")
        raise handle_service_error(e, "generate_picklist")


@router.post("/generate/status")
async def get_picklist_status(request: CacheKeyRequest):
    """Get the status of a picklist generation job."""
    try:
        # Check both cache systems for compatibility
        
        # First check the main cache
        if request.cache_key in PicklistServiceAdapter._picklist_cache:
            cached_data = PicklistServiceAdapter._picklist_cache[request.cache_key]
            
            if isinstance(cached_data, str) and cached_data == "initializing":
                # Still initializing
                return {
                    "status": "in_progress",
                    "batch_processing": {
                        "total_batches": 0,
                        "current_batch": 0,
                        "completed_batches": 0,
                        "progress_percentage": 5,
                        "processing_complete": False,
                    }
                }
            elif isinstance(cached_data, dict):
                logger.info(f"Returning completed picklist with {len(cached_data.get('picklist', []))} teams")
                return standardize_response(cached_data, wrap_data=False)

        # Check progress tracker for additional status info
        from app.services.progress_tracker import ProgressTracker
        progress_data = ProgressTracker.get_progress(request.cache_key)
        if progress_data:
            return {
                "status": progress_data.get("status", "in_progress"),
                "message": progress_data.get("message", "Processing..."),
                "progress": progress_data.get("progress", 0),
                "batch_processing": {
                    "total_batches": 1,
                    "current_batch": 1 if progress_data.get("progress", 0) > 0 else 0,
                    "completed_batches": 1 if progress_data.get("status") == "completed" else 0,
                    "progress_percentage": progress_data.get("progress", 0),
                    "processing_complete": progress_data.get("status") == "completed",
                }
            }

        # Not found in either system
        return {
            "status": "not_found",
            "batch_processing": {
                "total_batches": 0,
                "current_batch": 0,
                "completed_batches": 0,
                "progress_percentage": 0,
                "processing_complete": False,
            }
        }

    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise handle_service_error(e, "get_picklist_status")


@router.post("/update", response_model=PicklistUpdateResponse)
async def update_picklist(request: PicklistUpdateRequest):
    """Update a picklist based on user-defined team rankings."""
    try:
        # Initialize service
        service = PicklistServiceAdapter(request.unified_dataset_path)

        # Convert user rankings to dict format
        user_rankings = sorted(
            [r.dict() for r in request.user_rankings],
            key=lambda x: x["position"]
        )

        # Update picklist
        updated_picklist = service.merge_and_update_picklist(
            picklist=request.original_picklist,
            user_rankings=user_rankings
        )

        # Calculate changes
        changes_made = sum(
            1 for i, team in enumerate(updated_picklist)
            if i >= len(request.original_picklist) or
            team.get("team_number") != request.original_picklist[i].get("team_number")
        )

        return PicklistUpdateResponse(
            picklist=updated_picklist,
            changes_made=changes_made
        )

    except Exception as e:
        logger.error(f"Error updating picklist: {str(e)}")
        raise handle_service_error(e, "update_picklist")


@router.post("/rank-missing-teams", response_model=RankMissingTeamsResponse)
async def rank_missing_teams(request: RankMissingTeamsRequest):
    """Generate rankings for teams that were missed in the initial picklist generation."""
    try:
        # Initialize service
        service = PicklistServiceAdapter(request.unified_dataset_path)

        # Convert priorities to dict format
        priorities = [p.dict() for p in request.priorities]

        # Generate cache key
        cache_key = f"missing_{request.your_team_number}_{request.pick_position}_{hash(tuple(request.missing_team_numbers))}"

        # Rank missing teams
        result = await service.rank_missing_teams(
            missing_team_numbers=request.missing_team_numbers,
            ranked_teams=request.ranked_teams,
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=priorities,
            cache_key=cache_key,
        )

        return RankMissingTeamsResponse(**result)

    except Exception as e:
        logger.error(f"Error ranking missing teams: {str(e)}")
        raise handle_service_error(e, "rank_missing_teams")


@router.post("/clear-cache", response_model=SuccessResponse)
async def clear_picklist_cache(request: ClearCacheRequest = ClearCacheRequest()):
    """Clear the picklist cache."""
    try:
        if request.cache_keys:
            # Clear specific keys
            cleared = 0
            for key in request.cache_keys:
                if key in PicklistServiceAdapter._picklist_cache:
                    del PicklistServiceAdapter._picklist_cache[key]
                    cleared += 1

            message = f"Cleared {cleared} cache entries"
        else:
            # Clear all
            old_size = len(PicklistServiceAdapter._picklist_cache)
            PicklistServiceAdapter._picklist_cache.clear()
            message = f"Cleared entire cache ({old_size} entries)"

        logger.info(message)
        return SuccessResponse(message=message)

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise handle_service_error(e, "clear_cache")
