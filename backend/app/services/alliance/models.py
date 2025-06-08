# backend/app/services/alliance/models.py
"""
Alliance Selection Service Data Models

Pydantic models for alliance selection operations, providing type safety
and validation for API requests and responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PicklistData(BaseModel):
    """Data model for picklist information."""
    teams: List[Dict[str, Any]]
    analysis: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class LockPicklistRequest(BaseModel):
    """Request model for locking a picklist."""
    team_number: int
    event_key: str
    year: int
    first_pick_data: PicklistData
    second_pick_data: PicklistData
    third_pick_data: Optional[PicklistData] = None
    excluded_teams: Optional[List[int]] = None
    strategy_prompts: Optional[Dict[str, str]] = None


class LockedPicklistResponse(BaseModel):
    """Response model for locked picklist operations."""
    id: int
    team_number: int
    event_key: str
    year: int
    created_at: str


class AllianceSelectionRequest(BaseModel):
    """Request model for creating an alliance selection."""
    picklist_id: Optional[int] = None
    event_key: str
    year: int
    team_list: List[int] = Field(..., description="List of all team numbers at the event")


class AllianceSelectionResponse(BaseModel):
    """Response model for alliance selection operations."""
    id: int
    event_key: str
    year: int
    is_completed: bool
    current_round: int


class TeamActionRequest(BaseModel):
    """Request model for team actions during alliance selection."""
    selection_id: int
    team_number: int
    action: str = Field(
        ..., 
        description="Action: 'captain', 'accept', 'decline', 'remove'"
    )
    alliance_number: Optional[int] = Field(
        None,
        description="Required for 'captain', 'accept', and 'remove' actions"
    )


class TeamStatusResponse(BaseModel):
    """Response model for team status information."""
    team_number: int
    is_captain: bool
    is_picked: bool
    has_declined: bool
    round_eliminated: Optional[int] = None


class AllianceResponse(BaseModel):
    """Response model for alliance information."""
    alliance_number: int
    captain_team_number: int = 0
    first_pick_team_number: int = 0
    second_pick_team_number: int = 0
    backup_team_number: Optional[int] = 0


class AllianceSelectionStateResponse(BaseModel):
    """Response model for complete alliance selection state."""
    id: int
    event_key: str
    year: int
    is_completed: bool
    current_round: int
    picklist_id: Optional[int] = None
    alliances: List[AllianceResponse]
    team_statuses: List[TeamStatusResponse]


class TeamActionResponse(BaseModel):
    """Response model for team action operations."""
    status: str
    action: str
    team_number: int
    alliance_number: Optional[int] = None
    position: Optional[str] = None
    message: Optional[str] = None


class RoundAdvanceResponse(BaseModel):
    """Response model for round advancement operations."""
    status: str
    action: str
    selection_id: int
    new_round: Optional[int] = None
    message: Optional[str] = None


class SelectionResetResponse(BaseModel):
    """Response model for selection reset operations."""
    status: str
    action: str
    selection_id: int
    message: str


class AllianceValidationResult(BaseModel):
    """Model for alliance validation results."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TeamAvailabilityResult(BaseModel):
    """Model for team availability check results."""
    team_number: int
    is_available: bool
    reason: Optional[str] = None
    current_status: Optional[str] = None