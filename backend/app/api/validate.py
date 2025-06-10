"""
Validation API Router

This module handles all validation-related endpoints including outlier detection,
corrections, virtual scouting, and todo list management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas import (
    CorrectionRequest,
    CorrectionSuggestionsResponse,
    IgnoreMatchRequest,
    SuccessResponse,
    TodoListResponse,
    TodoUpdateRequest,
    ValidationRequest,
    ValidationResponse,
    VirtualScoutRequest,
    VirtualScoutResponse,
)
from app.api.utils.response_formatters import format_error_response, format_success_response
from app.services.validation import (
    add_to_todo_list,
    apply_correction,
    create_virtual_scout,
    get_todo_list,
    ignore_match,
    preview_virtual_scout,
    suggest_corrections,
    update_todo_status,
    validate_event_completeness,
    validate_event_with_outliers,
)

router = APIRouter(prefix="/api/validate", tags=["validation"])


# Legacy endpoints removed - frontend now uses modern API endpoints with proper schemas


@router.get("/event", response_model=ValidationResponse, deprecated=True)
async def validate_event(
    event_key: str = Query(..., description="Event key to validate"),
    unified_dataset_path: Optional[str] = Query(None, description="Path to unified dataset"),
) -> ValidationResponse:
    """
    Legacy endpoint for completeness validation only.
    
    This endpoint is deprecated. Use /api/validate/enhanced instead.
    """
    try:
        # Use event key to determine dataset path if not provided
        if not unified_dataset_path:
            unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
            
        result = validate_event_completeness(unified_dataset_path)
        
        return ValidationResponse(
            status="success",
            event_key=event_key,
            validation_type="legacy",
            total_issues=result.get("total_issues", 0),
            issues_by_type=result.get("issues_by_type", {}),
            issues_by_severity={"info": result.get("total_issues", 0)},
            issues=[],  # Legacy endpoint doesn't return detailed issues
            summary=result.get("summary", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhanced", response_model=ValidationResponse)
async def validate_enhanced(
    request: ValidationRequest,
) -> ValidationResponse:
    """
    Enhanced validation with comprehensive outlier detection.
    
    Performs multiple validation checks including:
    - Statistical outlier detection using Z-score
    - Missing data identification
    - Duplicate detection
    - Business rule validation
    """
    try:
        # Determine dataset path from event key
        unified_dataset_path = f"app/cache/{request.event_key}_unified_dataset.json"
        
        # Perform validation with specified threshold
        result = validate_event_with_outliers(
            unified_dataset_path,
            z_score_threshold=1 / request.confidence_threshold if request.confidence_threshold > 0 else 3.0
        )
        
        # Transform result to match schema
        issues = []
        for issue in result.get("outliers", []):
            issues.append({
                "id": f"issue_{issue['team_number']}_{issue['match_number']}_{issue['field']}",
                "match_key": f"{request.event_key}_qm{issue['match_number']}",
                "team_number": issue["team_number"],
                "issue_type": issue.get("type", "statistical"),
                "severity": issue.get("severity", "warning"),
                "field": issue["field"],
                "current_value": issue.get("value"),
                "suggested_value": issue.get("suggested_value"),
                "details": {
                    "field": issue["field"],
                    "value": issue.get("value"),
                    "expected_range": issue.get("expected_range"),
                    "deviation": issue.get("z_score"),
                    "confidence": request.confidence_threshold,
                    "reason": issue.get("reason", "Statistical outlier detected"),
                },
                "created_at": "2025-01-01T00:00:00Z",  # Placeholder
            })
        
        return ValidationResponse(
            status="success",
            event_key=request.event_key,
            validation_type="enhanced",
            total_issues=len(issues),
            issues_by_type=result.get("issues_by_type", {}),
            issues_by_severity=result.get("issues_by_severity", {}),
            issues=issues,
            summary=result.get("summary", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest-corrections", response_model=CorrectionSuggestionsResponse)
async def get_suggested_corrections(
    event_key: str = Query(..., description="Event key"),
    team_number: int = Query(..., description="Team number"),
    match_number: int = Query(..., description="Match number"),
) -> CorrectionSuggestionsResponse:
    """
    Get AI-powered correction suggestions for detected outliers.
    
    Analyzes the outlier in context and suggests appropriate corrections
    based on team performance patterns and game rules.
    """
    try:
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        result = suggest_corrections(unified_dataset_path, team_number, match_number)
        
        suggestions = []
        for suggestion in result.get("suggestions", []):
            suggestions.append({
                "issue_id": f"issue_{team_number}_{match_number}_{suggestion.get('field', 'unknown')}",
                "field": suggestion.get("field"),
                "current_value": suggestion.get("current_value"),
                "suggested_value": suggestion.get("suggested_value"),
                "confidence": suggestion.get("confidence", 0.8),
                "reason": suggestion.get("reason", "Statistical analysis"),
            })
        
        return CorrectionSuggestionsResponse(
            status="success",
            suggestions=suggestions,
            total_suggestions=len(suggestions),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-correction", response_model=SuccessResponse)
async def apply_corrections(
    event_key: str,
    request: CorrectionRequest,
) -> SuccessResponse:
    """
    Apply corrections to the dataset with full audit trail.
    
    Corrections are tracked with timestamp, user, and reason for
    future reference and rollback capability.
    """
    try:
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        # Extract team and match from issue_id if needed
        result = apply_correction(
            unified_dataset_path,
            request.issue_id,  # Assuming service can parse this
            request.corrected_value,
            request.reason,
        )
        
        return format_success_response(
            message="Correction applied successfully",
            data={"issue_id": request.issue_id, "applied": True},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ignore-match", response_model=SuccessResponse)
async def ignore_match_endpoint(
    event_key: str,
    request: IgnoreMatchRequest,
) -> SuccessResponse:
    """
    Mark a match as ignored with categorized reason.
    
    Valid reasons include robot issues, absence, or custom reasons.
    Ignored matches are excluded from analysis but preserved in dataset.
    """
    try:
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        result = ignore_match(
            unified_dataset_path,
            request.team_number,
            request.match_key,
            request.reason,
            request.ignore_all_teams,
        )
        
        return format_success_response(
            message=f"Match {request.match_key} marked as ignored",
            data={
                "match_key": request.match_key,
                "team_number": request.team_number,
                "ignored": True,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/virtual-scout", response_model=VirtualScoutResponse)
async def create_virtual_scout_endpoint(
    event_key: str,
    request: VirtualScoutRequest,
) -> VirtualScoutResponse:
    """
    Create virtual scout data using multiple data sources.
    
    Combines Statbotics predictions, historical team performance,
    and match context to generate realistic scout data.
    """
    try:
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        result = create_virtual_scout(
            unified_dataset_path,
            request.team_number,
            request.match_key,
            use_statbotics=request.use_statbotics,
            use_historical=request.use_historical,
            confidence_weight=request.confidence_weight,
        )
        
        return VirtualScoutResponse(
            status="success",
            virtual_scout=result["virtual_scout"],
            match_key=request.match_key,
            team_number=request.team_number,
            created=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview-virtual-scout", response_model=VirtualScoutResponse)
async def preview_virtual_scout_endpoint(
    event_key: str = Query(..., description="Event key"),
    match_key: str = Query(..., description="Match key"),
    team_number: int = Query(..., description="Team number"),
) -> VirtualScoutResponse:
    """
    Preview virtual scout data without saving.
    
    Useful for reviewing what data would be generated before
    committing to the dataset.
    """
    try:
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        result = preview_virtual_scout(unified_dataset_path, team_number, match_key)
        
        return VirtualScoutResponse(
            status="success",
            virtual_scout=result["virtual_scout"],
            match_key=match_key,
            team_number=team_number,
            created=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/todo", response_model=SuccessResponse)
async def add_to_todo_endpoint(
    event_key: str,
    team_number: int,
    match_key: str,
    priority: int = 3,
    description: Optional[str] = None,
) -> SuccessResponse:
    """
    Add item to validation todo list.
    
    Creates a todo item for manual verification or data collection.
    """
    try:
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        result = add_to_todo_list(
            unified_dataset_path,
            team_number,
            match_key,
            priority=priority,
            description=description,
        )
        
        return format_success_response(
            message="Added to todo list",
            data={"team_number": team_number, "match_key": match_key},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/todo", response_model=TodoListResponse)
async def get_todo_list_endpoint(
    event_key: str = Query(..., description="Event key"),
) -> TodoListResponse:
    """
    Get current validation todo list.
    
    Returns all pending validation tasks sorted by priority.
    """
    try:
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        result = get_todo_list(unified_dataset_path)
        
        todos = result.get("todos", [])
        
        return TodoListResponse(
            status="success",
            todos=todos,
            total=len(todos),
            pending=sum(1 for t in todos if t.get("status") == "pending"),
            in_progress=sum(1 for t in todos if t.get("status") == "in_progress"),
            completed=sum(1 for t in todos if t.get("status") == "completed"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/todo/{todo_id}", response_model=SuccessResponse)
async def update_todo_status_endpoint(
    todo_id: str,
    request: TodoUpdateRequest,
) -> SuccessResponse:
    """
    Update todo item status and assignment.
    
    Tracks progress on validation tasks with assignment and notes.
    """
    try:
        # Parse todo_id to get event_key
        parts = todo_id.split("_")
        event_key = parts[0] if parts else ""
        
        unified_dataset_path = f"app/cache/{event_key}_unified_dataset.json"
        
        result = update_todo_status(
            unified_dataset_path,
            todo_id,
            request.status,
            assigned_to=request.assigned_to,
            notes=request.notes,
        )
        
        return format_success_response(
            message=f"Todo {todo_id} updated to {request.status}",
            data={"todo_id": todo_id, "status": request.status},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))