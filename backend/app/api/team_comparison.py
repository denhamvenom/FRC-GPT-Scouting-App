"""API endpoint for comparing teams and re-ranking them."""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.team_comparison_service import TeamComparisonService

router = APIRouter(prefix="/api/picklist", tags=["Picklist"])


class MetricPriority(BaseModel):
    id: str
    weight: float = Field(1.0, ge=0.5, le=3.0)
    reason: Optional[str] = None


class CompareTeamsRequest(BaseModel):
    unified_dataset_path: str
    team_numbers: List[int]
    your_team_number: int
    pick_position: str = Field(..., pattern="^(first|second|third)$")
    priorities: List[MetricPriority]
    question: Optional[str] = None


@router.post("/compare-teams")
async def compare_teams(request: CompareTeamsRequest) -> Dict[str, Any]:
    try:
        service = TeamComparisonService(request.unified_dataset_path)
        priorities = [p.model_dump() for p in request.priorities]
        result = await service.compare_teams(
            team_numbers=request.team_numbers,
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=priorities,
            question=request.question,
        )
        return {"status": "success", **result}
    except Exception as e:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=500, detail=f"Error comparing teams: {e}")
