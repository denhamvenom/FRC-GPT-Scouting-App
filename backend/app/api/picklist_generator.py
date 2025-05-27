# backend/app/api/picklist_generator.py

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set, Union

from app.services.picklist_generator_service import PicklistGeneratorService

router = APIRouter(prefix="/api/picklist", tags=["Picklist"])

class MetricPriority(BaseModel):
    id: str
    weight: float = Field(1.0, ge=0.5, le=3.0)
    reason: Optional[str] = None

class PicklistRequest(BaseModel):
    unified_dataset_path: str
    your_team_number: int
    pick_position: str = Field(..., description="Options: 'first', 'second', or 'third'")
    priorities: List[MetricPriority]
    exclude_teams: Optional[List[int]] = None
    batch_size: int = Field(20, ge=5, le=100, description="Number of teams in each batch (default: 20)")
    reference_teams_count: int = Field(3, ge=1, le=10, description="Number of reference teams to include (default: 3)")
    reference_selection: str = Field("top_middle_bottom", description="Strategy for selecting reference teams", enum=["even_distribution", "percentile", "top_middle_bottom"])
    use_batching: bool = Field(..., description="Whether to use batch processing instead of one-shot generation")
    cache_key: Optional[str] = Field(None, description="Optional cache key to use for progress tracking")

class UserRanking(BaseModel):
    team_number: int
    position: int
    nickname: Optional[str] = None

class UpdatePicklistRequest(BaseModel):
    unified_dataset_path: str
    original_picklist: List[Dict[str, Any]]
    user_rankings: List[UserRanking]
    
class RankMissingTeamsRequest(BaseModel):
    unified_dataset_path: str
    missing_team_numbers: List[int]
    ranked_teams: List[Dict[str, Any]]
    your_team_number: int
    pick_position: str = Field(..., description="Options: 'first', 'second', or 'third'")
    priorities: List[MetricPriority]

@router.post("/generate/status")
async def get_picklist_generation_status(request: Dict[str, str] = Body(...)):
    """
    Get the status of a picklist generation job.
    
    Args:
        request: A dictionary containing the cache_key
        
    Returns:
        Status information for the job
    """
    try:
        cache_key = request.get("cache_key")
        if not cache_key:
            raise HTTPException(status_code=400, detail="cache_key is required")
            
        # For status checks, we don't need to initialize with a real dataset path
        # so just create a service instance without loading the dataset
        from app.services.picklist_generator_service import PicklistGeneratorService
        
        class StatusCheckService:
            def __init__(self):
                self._picklist_cache = {}
                
            def get_batch_processing_status(self, cache_key):
                # Use the same logic as the original service but without loading any dataset
                if cache_key in PicklistGeneratorService._picklist_cache:
                    cached_data = PicklistGeneratorService._picklist_cache[cache_key]
                    
                    # If it's a timestamp, it's in progress but no batches have completed yet
                    if isinstance(cached_data, float):
                        return {
                            "status": "in_progress",
                            "batch_processing": {
                                "total_batches": 0,
                                "current_batch": 0,
                                "progress_percentage": 0,
                                "processing_complete": False
                            }
                        }
                    # If it's a dictionary with batch_processing info, return the status
                    elif isinstance(cached_data, dict) and "batch_processing" in cached_data:
                        # If processing is complete, return the full result including the picklist
                        if cached_data["batch_processing"].get("processing_complete"):
                            return cached_data  # Return the entire result with picklist data
                        else:
                            # If still processing, just return status info
                            return {
                                "status": "in_progress",
                                "batch_processing": cached_data["batch_processing"]
                            }
                    # Otherwise, it's a completed non-batch job
                    else:
                        return {
                            "status": "success",
                            "batch_processing": {
                                "total_batches": 1,
                                "current_batch": 1,
                                "progress_percentage": 100,
                                "processing_complete": True
                            }
                        }
                
                # Not found in cache
                return {
                    "status": "not_found",
                    "batch_processing": {
                        "total_batches": 0,
                        "current_batch": 0,
                        "progress_percentage": 0,
                        "processing_complete": False
                    }
                }
        
        # Use the simplified status check service that doesn't try to load datasets
        status_service = StatusCheckService()
        
        # Get the status using our dedicated status service
        status = status_service.get_batch_processing_status(cache_key)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking picklist generation status: {str(e)}")

@router.post("/generate")
async def generate_picklist(request: PicklistRequest):
    """
    Generate a ranked picklist using GPT based on team data and priorities.
    
    Args:
        request: Picklist generation request with dataset path, team number, pick position, and priorities
        
    Returns:
        Generated picklist with team rankings and explanations
    """
    try:
        # Add request logging to track potential duplicate requests
        import logging
        logger = logging.getLogger('picklist_api')
        request_id = id(request)
        logger.info(f"Received picklist generation request {request_id}: {request.pick_position} pick for team {request.your_team_number}")
        
        # Validate inputs
        if request.pick_position not in ["first", "second", "third"]:
            raise HTTPException(status_code=400, detail="Pick position must be 'first', 'second', or 'third'")
            
        if not request.priorities:
            raise HTTPException(status_code=400, detail="At least one priority metric must be provided")
        
        # Initialize the service
        generator_service = PicklistGeneratorService(request.unified_dataset_path)
        
        # Debug logging - check exactly what we're passing
        logger.info(f"API Layer - About to call generate_picklist with use_batching={request.use_batching} (type: {type(request.use_batching)})")
        logger.info(f"API Layer - Full request values: batch_size={request.batch_size}, reference_teams_count={request.reference_teams_count}")
        
        # Convert priorities to plain dictionaries to avoid serialization issues
        priorities = [
            {
                "id": p.id,
                "weight": float(p.weight),
                "reason": p.reason
            } 
            for p in request.priorities
        ]
        
        # Use provided cache key or generate one for deduplication
        if request.cache_key:
            cache_key = request.cache_key
            logger.info(f"Using provided cache key: {cache_key}")
        else:
            import hashlib
            import json
            
            # Create a deterministic representation of the request
            cache_key_dict = {
                "path": request.unified_dataset_path,
                "team": request.your_team_number,
                "position": request.pick_position,
                "priorities": sorted([(p["id"], p["weight"]) for p in priorities]),
                "exclude": sorted(request.exclude_teams) if request.exclude_teams else [],
                "use_batching": request.use_batching
            }
            
            # Include batching parameters if batching is enabled
            if request.use_batching:
                cache_key_dict.update({
                    "batch_size": request.batch_size,
                    "reference_teams_count": request.reference_teams_count,
                    "reference_selection": request.reference_selection
                })
            
            # Convert to a hash for quick comparison
            cache_key = hashlib.md5(json.dumps(cache_key_dict, sort_keys=True).encode()).hexdigest()
            logger.info(f"Generated cache key: {cache_key}")
        
        # Add batch processing parameters to log
        logger.info(f"Received use_batching={request.use_batching} (type: {type(request.use_batching)})")
        logger.info(f"Raw request data: {request.dict()}")
        if request.use_batching:
            logger.info(f"Using batching with batch_size={request.batch_size}, reference_teams_count={request.reference_teams_count}")
            logger.info(f"Reference selection strategy: {request.reference_selection}")
        else:
            logger.info("Batching is disabled, will use one-shot processing")
        
        # Use the cache on the service to prevent duplicate work
        # The generator_service has internal caching that should prevent duplicate work
        
        # TEMPORARY: Force batching off to test one-shot processing
        logger.info(f"API Layer - Original use_batching={request.use_batching}")
        
        result = await generator_service.generate_picklist(
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=priorities,  # Use the plain dict version
            exclude_teams=request.exclude_teams,
            request_id=request_id,  # Pass the request ID for logging
            cache_key=cache_key,    # Pass the cache key for deduplication and progress tracking
            batch_size=request.batch_size,
            reference_teams_count=request.reference_teams_count,
            reference_selection=request.reference_selection,
            use_batching=request.use_batching
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Error generating picklist"))
        
        logger.info(f"Successfully generated picklist for request {request_id}")
        
        # Add the cache key to the response for status polling
        result["cache_key"] = cache_key
        return result
    
    except Exception as e:
        logger.error(f"Error generating picklist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating picklist: {str(e)}")

    
@router.post("/update")
async def update_picklist(request: UpdatePicklistRequest):
    """
    Update a picklist based on user-defined team rankings.
    
    Args:
        request: Update request with original picklist and user rankings
        
    Returns:
        Updated picklist with new team order
    """
    try:
        # Initialize the service
        generator_service = PicklistGeneratorService(request.unified_dataset_path)
        
        # Convert user rankings to the format expected by the service
        user_rankings = [
            {
                "team_number": ranking.team_number,
                "position": ranking.position,
                "nickname": ranking.nickname
            } for ranking in request.user_rankings
        ]
        
        # Sort by position
        user_rankings.sort(key=lambda x: x["position"])
        
        # Merge and update the picklist
        updated_picklist = generator_service.merge_and_update_picklist(
            picklist=request.original_picklist,
            user_rankings=user_rankings
        )
        
        return {
            "status": "success",
            "picklist": updated_picklist
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating picklist: {str(e)}")
        
@router.post("/rank-missing-teams")
async def rank_missing_teams(request: RankMissingTeamsRequest):
    """
    Generate rankings for teams that were missed in the initial picklist generation.
    
    Args:
        request: Missing teams ranking request with dataset path, missing team numbers, 
                already ranked teams, and other context
        
    Returns:
        Rankings for the previously missing teams
    """
    try:
        # Add request logging to track potential duplicate requests
        import logging
        logger = logging.getLogger('picklist_api')
        request_id = id(request)
        logger.info(f"Received missing teams ranking request {request_id}: {request.pick_position} pick for team {request.your_team_number} - missing teams count: {len(request.missing_team_numbers)}")
        
        # Validate inputs
        if request.pick_position not in ["first", "second", "third"]:
            raise HTTPException(status_code=400, detail="Pick position must be 'first', 'second', or 'third'")
            
        if not request.priorities:
            raise HTTPException(status_code=400, detail="At least one priority metric must be provided")
        
        if not request.missing_team_numbers:
            raise HTTPException(status_code=400, detail="No missing teams to rank")
        
        # Initialize the service
        generator_service = PicklistGeneratorService(request.unified_dataset_path)
        
        # Convert priorities to plain dictionaries
        priorities = [
            {
                "id": p.id,
                "weight": float(p.weight),
                "reason": p.reason
            } 
            for p in request.priorities
        ]
        
        # Generate a cache key for deduplication
        import hashlib
        import json
        
        # Create a deterministic representation of the request
        cache_key_dict = {
            "path": request.unified_dataset_path,
            "team": request.your_team_number,
            "position": request.pick_position,
            "priorities": sorted([(p["id"], p["weight"]) for p in priorities]),
            "missing_teams": sorted(request.missing_team_numbers)
        }
        
        # Convert to a hash for quick comparison
        cache_key = hashlib.md5(json.dumps(cache_key_dict, sort_keys=True).encode()).hexdigest()
        logger.info(f"Missing teams request {request_id} cache key: {cache_key}")
        
        # Rank the missing teams
        result = await generator_service.rank_missing_teams(
            missing_team_numbers=request.missing_team_numbers,
            ranked_teams=request.ranked_teams,
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=priorities,
            request_id=request_id,  # Pass the request ID for logging
            cache_key=cache_key     # Pass the cache key for deduplication
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Error ranking missing teams"))
        
        logger.info(f"Successfully generated missing teams rankings for request {request_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error ranking missing teams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ranking missing teams: {str(e)}")

@router.post("/clear-cache")
async def clear_picklist_cache(
    request: Optional[Dict[str, Any]] = Body(None)
):
    """
    Clear the picklist cache. Can optionally clear specific cache keys.
    
    Args:
        request: Optional dictionary with 'cache_keys' list or 'pick_position' to clear specific entries
        
    Returns:
        dict: Status message
    """
    import logging
    logger = logging.getLogger('picklist_api')
    
    try:
        from app.services.picklist_generator_service import PicklistGeneratorService
        
        if request and 'cache_keys' in request:
            # Clear specific cache keys
            cache_keys = request['cache_keys']
            cleared_count = 0
            for key in cache_keys:
                if key in PicklistGeneratorService._picklist_cache:
                    del PicklistGeneratorService._picklist_cache[key]
                    cleared_count += 1
            
            logger.info(f"Cleared {cleared_count} specific cache entries")
            return {
                "status": "success",
                "message": f"Cleared {cleared_count} cache entries"
            }
        else:
            # Clear entire cache
            old_size = len(PicklistGeneratorService._picklist_cache)
            PicklistGeneratorService._picklist_cache.clear()
            
            logger.info(f"Cleared entire picklist cache (had {old_size} entries)")
            return {
                "status": "success",
                "message": f"Cleared entire picklist cache ({old_size} entries removed)"
            }
    
    except Exception as e:
        logger.error(f"Error clearing picklist cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")