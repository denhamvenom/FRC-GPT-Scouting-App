"""
Validation Service Models

Pydantic models for validation service data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class IssueType(str, Enum):
    """Types of validation issues."""
    MISSING_SCOUTING = "missing_scouting"
    MISSING_SUPERSCOUTING = "missing_superscouting"
    STATISTICAL_OUTLIER = "statistical_outlier"
    TEAM_OUTLIER = "team_outlier"
    DATA_QUALITY = "data_quality"
    IGNORED_MATCH = "ignored_match"


class IssueSeverity(str, Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DetectionMethod(str, Enum):
    """Methods used to detect outliers."""
    Z_SCORE = "z_score"
    IQR = "iqr"
    TEAM_SPECIFIC = "team_specific"
    BUSINESS_RULE = "business_rule"


class CorrectionMethod(str, Enum):
    """Methods for suggesting corrections."""
    TEAM_AVERAGE = "team_average"
    MINIMUM_REASONABLE = "minimum_reasonable"
    MAXIMUM_REASONABLE = "maximum_reasonable"
    ZERO = "zero"
    STATISTICAL_MEDIAN = "statistical_median"
    INTERPOLATION = "interpolation"


class TodoStatus(str, Enum):
    """Status of todo items."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IgnoreReason(str, Enum):
    """Reasons for ignoring matches."""
    NOT_OPERATIONAL = "not_operational"
    NOT_PRESENT = "not_present"
    OTHER = "other"


class ValidationIssue(BaseModel):
    """Represents a single validation issue."""
    team_number: int
    match_number: int
    issue_type: IssueType
    severity: IssueSeverity
    metric: Optional[str] = None
    value: Optional[Union[int, float]] = None
    detection_method: Optional[DetectionMethod] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class OutlierDetails(BaseModel):
    """Detailed information about an outlier."""
    metric: str
    value: Union[int, float]
    z_score: Optional[float] = None
    team_z_score: Optional[float] = None
    bounds: Optional[List[float]] = None
    detection_method: DetectionMethod


class ValidationSummary(BaseModel):
    """Summary statistics for validation results."""
    total_missing_matches: int = 0
    total_missing_superscouting: int = 0
    total_outliers: int = 0
    total_ignored_matches: int = 0
    has_issues: bool = False
    scouting_records_count: int = 0
    expected_match_records_count: int = 0


class ValidationResult(BaseModel):
    """Complete validation results."""
    status: str
    missing_scouting: List[Dict[str, int]] = Field(default_factory=list)
    missing_superscouting: List[Dict[str, int]] = Field(default_factory=list)
    outliers: List[Dict[str, Any]] = Field(default_factory=list)
    ignored_matches: List[Dict[str, Any]] = Field(default_factory=list)
    summary: ValidationSummary
    issues: List[ValidationIssue] = Field(default_factory=list)


class CorrectionSuggestion(BaseModel):
    """Suggestion for correcting a data issue."""
    metric: str
    current_value: Union[int, float]
    suggested_value: Union[int, float]
    method: CorrectionMethod
    confidence: float = Field(ge=0.0, le=1.0)
    reason: Optional[str] = None


class AuditEntry(BaseModel):
    """Audit trail entry for data corrections."""
    metric: str
    original_value: Any
    corrected_value: Any
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)
    user: Optional[str] = None
    correction_method: Optional[CorrectionMethod] = None


class VirtualScoutData(BaseModel):
    """Virtual scout data for missing matches."""
    team_number: int
    match_number: int
    qual_number: int
    alliance_color: str
    is_virtual_scout: bool = True
    virtual_scout_timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Union[int, float]]
    adjustment_info: Optional[Dict[str, Any]] = None


class TodoItem(BaseModel):
    """Todo list item for manual validation tasks."""
    team_number: int
    match_number: int
    added_timestamp: datetime = Field(default_factory=datetime.now)
    status: TodoStatus = TodoStatus.PENDING
    priority: int = Field(ge=1, le=5, default=3)
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    updated_timestamp: Optional[datetime] = None
    notes: Optional[str] = None


class IgnoredMatch(BaseModel):
    """Ignored match record."""
    team_number: int
    match_number: int
    reason_category: IgnoreReason
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)