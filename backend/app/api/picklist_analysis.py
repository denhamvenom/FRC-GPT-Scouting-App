# backend/app/api/picklist_analysis.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.picklist_analysis_service import PicklistAnalysisService

router = APIRouter()

class MetricPriority(BaseModel):
    id: str
    weight: float = 1.0
    reason: Optional[str] = None

class PicklistAnalysisRequest(BaseModel):
    unified_dataset_path: str
    priorities: Optional[List[MetricPriority]] = None
    strategy_prompt: Optional[str] = None

@router.post("/picklist/analyze")
async def analyze_picklist_data(request: PicklistAnalysisRequest):
    """
    Analyze the unified dataset to generate picklist suggestions and metrics.
    
    Either priorities or strategy_prompt should be provided:
    - priorities: List of metric IDs with weights for direct ranking
    - strategy_prompt: Natural language description of desired strategy
    """
    try:
        # Initialize the analysis service
        analysis_service = PicklistAnalysisService(request.unified_dataset_path)
        
        # Get game-specific metrics
        game_metrics = analysis_service.identify_game_specific_metrics()
        
        # Get superscouting metrics - new addition
        superscout_metrics = analysis_service.identify_superscout_metrics()
        
        # Get suggested metrics based on statistical analysis
        suggested_metrics = analysis_service.get_suggested_priorities()
        
        # If strategy prompt is provided, parse it into priorities using GPT
        parsed_priorities = None
        if request.strategy_prompt:
            parsed_priorities = analysis_service.parse_strategy_prompt(request.strategy_prompt)
        
        # Generate team rankings if priorities are provided
        team_rankings = None
        if request.priorities:
            team_rankings = analysis_service.rank_teams(request.priorities)
        
        # Generate statistics for all metrics
        metrics_stats = analysis_service.calculate_metrics_statistics()
        
        return {
            "status": "success",
            "game_metrics": game_metrics,
            "universal_metrics": analysis_service.universal_metrics,
            "superscout_metrics": superscout_metrics,  # Add superscouting metrics to response
            "suggested_metrics": suggested_metrics,
            "metrics_stats": metrics_stats,
            "parsed_priorities": parsed_priorities,
            "team_rankings": team_rankings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing picklist data: {str(e)}")