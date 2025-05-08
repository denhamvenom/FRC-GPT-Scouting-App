# backend/app/api/picklist_generator.py

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set

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
        
        # Convert priorities to plain dictionaries to avoid serialization issues
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
            "exclude": sorted(request.exclude_teams) if request.exclude_teams else []
        }
        
        # Convert to a hash for quick comparison
        cache_key = hashlib.md5(json.dumps(cache_key_dict, sort_keys=True).encode()).hexdigest()
        logger.info(f"Request {request_id} cache key: {cache_key}")
        
        # Use the cache on the service to prevent duplicate work
        # The generator_service has internal caching that should prevent duplicate work
        result = await generator_service.generate_picklist(
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=priorities,  # Use the plain dict version
            exclude_teams=request.exclude_teams,
            request_id=request_id,  # Pass the request ID for logging
            cache_key=cache_key     # Pass the cache key for deduplication
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Error generating picklist"))
        
        logger.info(f"Successfully generated picklist for request {request_id}")
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