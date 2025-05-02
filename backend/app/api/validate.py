# backend/app/api/validate.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.data_validation_service import (
    validate_event_completeness,
    validate_event_with_outliers,
    suggest_corrections,
    apply_correction
)

router = APIRouter()

class CorrectionRequest(BaseModel):
    team_number: int
    match_number: int
    corrections: Dict[str, Any]
    reason: Optional[str] = ""

@router.get("/validate/event")
async def validate_event(unified_dataset_path: str):
    """
    Legacy endpoint for completeness validation only.
    """
    try:
        result = validate_event_completeness(unified_dataset_path)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/validate/enhanced")
async def validate_enhanced(unified_dataset_path: str, z_score_threshold: float = 3.0):
    """
    Enhanced validation with outlier detection.
    """
    try:
        result = validate_event_with_outliers(unified_dataset_path, z_score_threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/suggest-corrections")
async def get_suggested_corrections(unified_dataset_path: str, team_number: int, match_number: int):
    """
    Get suggested corrections for outliers.
    """
    try:
        result = suggest_corrections(unified_dataset_path, team_number, match_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate/apply-correction")
async def apply_corrections(unified_dataset_path: str, request: CorrectionRequest):
    """
    Apply corrections to the dataset.
    """
    try:
        result = apply_correction(
            unified_dataset_path,
            request.team_number,
            request.match_number,
            request.corrections,
            request.reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))