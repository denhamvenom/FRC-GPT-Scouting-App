"""
Validation API Schemas

This module contains schemas specific to the validation API endpoints.
Includes models for validation results, corrections, and todo items.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from .common import SuccessResponse


class OutlierType(str, Enum):
    """Types of outliers that can be detected"""
    STATISTICAL = "statistical"
    BUSINESS_RULE = "business_rule"
    MISSING_DATA = "missing_data"
    DUPLICATE = "duplicate"
    INCONSISTENT = "inconsistent"


class TodoStatus(str, Enum):
    """Status options for todo items"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class OutlierDetails(BaseModel):
    """Details about a detected outlier"""
    field: str = Field(..., description="Field containing the outlier")
    value: Any = Field(..., description="The outlier value")
    expected_range: Optional[Dict[str, float]] = Field(None, description="Expected min/max values")
    deviation: Optional[float] = Field(None, description="Standard deviations from mean")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in outlier detection")
    reason: str = Field(..., description="Human-readable explanation")


class ValidationIssue(BaseModel):
    """Represents a single validation issue"""
    id: str = Field(..., description="Unique issue identifier")
    match_key: str = Field(..., description="Match identifier")
    team_number: int = Field(..., description="Team number")
    issue_type: OutlierType = Field(..., description="Type of issue detected")
    severity: ValidationSeverity = Field(..., description="Severity level")
    field: str = Field(..., description="Field with the issue")
    current_value: Any = Field(..., description="Current value")
    suggested_value: Optional[Any] = Field(None, description="Suggested correction")
    details: OutlierDetails = Field(..., description="Detailed information about the issue")
    created_at: datetime = Field(..., description="When the issue was detected")

    class Config:
        schema_extra = {
            "example": {
                "id": "issue_123",
                "match_key": "2025arc_qm10",
                "team_number": 254,
                "issue_type": "statistical",
                "severity": "warning",
                "field": "teleop_amp_scores",
                "current_value": 50,
                "suggested_value": 5,
                "details": {
                    "field": "teleop_amp_scores",
                    "value": 50,
                    "expected_range": {"min": 0, "max": 10},
                    "deviation": 4.5,
                    "confidence": 0.95,
                    "reason": "Value is 4.5 standard deviations from mean"
                },
                "created_at": "2025-01-01T12:00:00Z"
            }
        }


class TodoItem(BaseModel):
    """Represents a todo item for validation"""
    id: str = Field(..., description="Unique todo identifier")
    match_key: str = Field(..., description="Match identifier")
    team_number: int = Field(..., description="Team number")
    issue_type: OutlierType = Field(..., description="Type of issue")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1=highest)")
    status: TodoStatus = Field(default=TodoStatus.PENDING, description="Current status")
    description: str = Field(..., description="Description of the issue")
    assigned_to: Optional[str] = Field(None, description="Assigned user")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        schema_extra = {
            "example": {
                "id": "todo_456",
                "match_key": "2025arc_qm10",
                "team_number": 254,
                "issue_type": "missing_data",
                "priority": 2,
                "status": "pending",
                "description": "Missing autonomous data for team 254 in match qm10",
                "created_at": "2025-01-01T12:00:00Z"
            }
        }


class VirtualScoutEntry(BaseModel):
    """Virtual scout data entry"""
    scout_name: str = Field(..., description="Name of the virtual scout")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in the data")
    source: str = Field(..., description="Data source (e.g., 'statbotics', 'tba', 'historical')")
    data: Dict[str, Any] = Field(..., description="Scout data fields and values")
    reasoning: Optional[str] = Field(None, description="Explanation of data generation")

    class Config:
        schema_extra = {
            "example": {
                "scout_name": "Virtual Scout - Statbotics",
                "confidence": 0.85,
                "source": "statbotics",
                "data": {
                    "auto_speaker_scores": 2,
                    "teleop_speaker_scores": 5,
                    "climb_success": True
                },
                "reasoning": "Based on team's average performance in similar matches"
            }
        }


# Request Models

class ValidationRequest(BaseModel):
    """Request for validation operations"""
    event_key: str = Field(..., description="Event key to validate")
    unified_dataset_path: Optional[str] = Field(None, description="Path to unified dataset file")
    validation_type: Literal["legacy", "enhanced"] = Field(
        "enhanced",
        description="Type of validation to perform"
    )
    include_missing: bool = Field(True, description="Include missing data detection")
    include_outliers: bool = Field(True, description="Include outlier detection")
    include_duplicates: bool = Field(True, description="Include duplicate detection")
    confidence_threshold: float = Field(0.8, ge=0, le=1, description="Minimum confidence for issues")

    class Config:
        schema_extra = {
            "example": {
                "event_key": "2025arc",
                "unified_dataset_path": "/app/data/unified_event_2025arc.json",
                "validation_type": "enhanced",
                "include_missing": True,
                "include_outliers": True,
                "include_duplicates": True,
                "confidence_threshold": 0.8
            }
        }


class CorrectionRequest(BaseModel):
    """Request to apply a correction"""
    issue_id: str = Field(..., description="Issue ID to correct")
    corrected_value: Any = Field(..., description="New value to apply")
    reason: Optional[str] = Field(None, description="Reason for correction")
    applied_by: Optional[str] = Field(None, description="User applying correction")

    class Config:
        schema_extra = {
            "example": {
                "issue_id": "issue_123",
                "corrected_value": 5,
                "reason": "Confirmed with scout that this was a data entry error"
            }
        }


class IgnoreMatchRequest(BaseModel):
    """Request to ignore a match"""
    match_key: str = Field(..., description="Match to ignore")
    team_number: int = Field(..., description="Team number")
    reason: str = Field(..., description="Reason for ignoring")
    ignore_all_teams: bool = Field(False, description="Ignore entire match for all teams")

    class Config:
        schema_extra = {
            "example": {
                "match_key": "2025arc_qm10",
                "team_number": 254,
                "reason": "Robot was disabled for entire match",
                "ignore_all_teams": False
            }
        }


class VirtualScoutRequest(BaseModel):
    """Request to create virtual scout data"""
    match_key: str = Field(..., description="Match identifier")
    team_number: int = Field(..., description="Team number")
    use_statbotics: bool = Field(True, description="Use Statbotics data")
    use_historical: bool = Field(True, description="Use team's historical data")
    confidence_weight: float = Field(0.7, ge=0, le=1, description="Weight for confidence calculation")

    class Config:
        schema_extra = {
            "example": {
                "match_key": "2025arc_qm10",
                "team_number": 254,
                "use_statbotics": True,
                "use_historical": True,
                "confidence_weight": 0.7
            }
        }


class TodoUpdateRequest(BaseModel):
    """Request to update a todo item"""
    status: TodoStatus = Field(..., description="New status")
    assigned_to: Optional[str] = Field(None, description="Assign to user")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "notes": "Verified with head scout"
            }
        }


# Response Models

class ValidationResponse(SuccessResponse):
    """Response containing validation results"""
    event_key: str = Field(..., description="Validated event")
    validation_type: str = Field(..., description="Type of validation performed")
    total_issues: int = Field(..., description="Total issues found")
    issues_by_type: Dict[str, int] = Field(..., description="Issue count by type")
    issues_by_severity: Dict[str, int] = Field(..., description="Issue count by severity")
    issues: List[ValidationIssue] = Field(..., description="List of validation issues")
    summary: Dict[str, Any] = Field(..., description="Validation summary statistics")
    # Add missing data arrays that frontend expects
    missing_scouting: List[Dict[str, Any]] = Field(default_factory=list, description="Missing scouting data")
    missing_superscouting: List[Dict[str, Any]] = Field(default_factory=list, description="Missing superscouting data")
    ignored_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Ignored matches")
    outliers: List[Dict[str, Any]] = Field(default_factory=list, description="Statistical outliers")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event_key": "2025arc",
                "validation_type": "enhanced",
                "total_issues": 15,
                "issues_by_type": {
                    "statistical": 8,
                    "missing_data": 5,
                    "duplicate": 2
                },
                "issues_by_severity": {
                    "error": 2,
                    "warning": 10,
                    "info": 3
                },
                "issues": [],
                "summary": {
                    "total_matches": 100,
                    "total_scouts": 50,
                    "completion_rate": 0.95
                }
            }
        }


class CorrectionSuggestionsResponse(SuccessResponse):
    """Response with suggested corrections"""
    suggestions: List[Dict[str, Any]] = Field(..., description="List of suggested corrections")
    total_suggestions: int = Field(..., description="Total number of suggestions")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "suggestions": [
                    {
                        "issue_id": "issue_123",
                        "field": "teleop_amp_scores",
                        "current_value": 50,
                        "suggested_value": 5,
                        "confidence": 0.95,
                        "reason": "Statistical outlier"
                    }
                ],
                "total_suggestions": 1
            }
        }


class TodoListResponse(SuccessResponse):
    """Response containing todo items"""
    todos: List[TodoItem] = Field(..., description="List of todo items")
    total: int = Field(..., description="Total todo items")
    pending: int = Field(..., description="Pending items count")
    in_progress: int = Field(..., description="In progress items count")
    completed: int = Field(..., description="Completed items count")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "todos": [],
                "total": 10,
                "pending": 6,
                "in_progress": 2,
                "completed": 2
            }
        }


class VirtualScoutResponse(SuccessResponse):
    """Response for virtual scout operations"""
    virtual_scout: VirtualScoutEntry = Field(..., description="Generated virtual scout data")
    match_key: str = Field(..., description="Match identifier")
    team_number: int = Field(..., description="Team number")
    created: bool = Field(..., description="Whether entry was created or previewed")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "virtual_scout": {
                    "scout_name": "Virtual Scout - Statbotics",
                    "confidence": 0.85,
                    "source": "statbotics",
                    "data": {},
                    "reasoning": "Based on historical performance"
                },
                "match_key": "2025arc_qm10",
                "team_number": 254,
                "created": False
            }
        }