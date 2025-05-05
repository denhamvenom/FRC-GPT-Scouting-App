# backend/app/api/picklist_generator.py

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

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
        
        # Generate the picklist with plain dictionaries
        result = await generator_service.generate_picklist(
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=priorities,  # Use the plain dict version
            exclude_teams=request.exclude_teams
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Error generating picklist"))
            
        return result
        
    except Exception as e:
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