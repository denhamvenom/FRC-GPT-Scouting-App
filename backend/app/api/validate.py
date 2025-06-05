# backend/app/api/validate.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from app.services.data_validation_service import (
    validate_event_completeness,
    validate_event_with_outliers,
    suggest_corrections,
    apply_correction,
    ignore_match,
    create_virtual_scout,
    add_to_todo_list,
    get_todo_list,
    update_todo_status,
    preview_virtual_scout,
)

router = APIRouter()


class CorrectionRequest(BaseModel):
    team_number: int
    match_number: int
    corrections: Dict[str, Any]
    reason: Optional[str] = ""


class IgnoreMatchRequest(BaseModel):
    team_number: int
    match_number: int
    reason_category: str  # not_operational, not_present, other
    reason_text: Optional[str] = ""


class TodoStatusUpdateRequest(BaseModel):
    team_number: int
    match_number: int
    status: str  # pending, completed, cancelled


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
            request.reason,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/ignore-match")
async def ignore_match_endpoint(unified_dataset_path: str, request: IgnoreMatchRequest):
    """
    Mark a match as intentionally ignored with a reason.

    Accepted reason categories:
    - not_operational: Robot was not operational in the match
    - not_present: Robot was not present in the match
    - other: User-specified reason (requires reason_text)
    """
    try:
        result = ignore_match(
            unified_dataset_path,
            request.team_number,
            request.match_number,
            request.reason_category,
            request.reason_text,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/create-virtual-scout")
async def create_virtual_scout_endpoint(
    unified_dataset_path: str, team_number: int, match_number: int
):
    """
    Create a virtual scout entry for a team's missing match based on team averages
    and Blue Alliance match data.
    """
    try:
        result = create_virtual_scout(unified_dataset_path, team_number, match_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate/preview-virtual-scout")
async def preview_virtual_scout_endpoint(
    unified_dataset_path: str, team_number: int, match_number: int
):
    """
    Preview what a virtual scout entry would look like without saving it.
    """
    try:
        result = preview_virtual_scout(unified_dataset_path, team_number, match_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/add-to-todo")
async def add_to_todo_endpoint(unified_dataset_path: str, team_number: int, match_number: int):
    """
    Add a team-match combination to the to-do list for manual scouting.
    """
    try:
        result = add_to_todo_list(unified_dataset_path, team_number, match_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate/todo-list")
async def get_todo_list_endpoint(unified_dataset_path: str):
    """
    Get the current to-do list from the unified dataset.
    """
    try:
        result = get_todo_list(unified_dataset_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/update-todo-status")
async def update_todo_status_endpoint(unified_dataset_path: str, request: TodoStatusUpdateRequest):
    """
    Update the status of a to-do list entry.
    """
    try:
        result = update_todo_status(
            unified_dataset_path, request.team_number, request.match_number, request.status
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
