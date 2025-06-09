"""
Alliance Selection API Schemas

This module contains schemas specific to alliance selection endpoints.
It re-exports and extends the models from the service layer for API use.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

# Re-export service models that are already well-defined
from app.services.alliance.models import (
    AllianceResponse,
    AllianceSelectionRequest,
    AllianceSelectionResponse,
    AllianceSelectionStateResponse,
    LockedPicklistResponse,
    LockPicklistRequest,
    PicklistData,
    TeamActionRequest,
    TeamStatusResponse,
)

# Additional API-specific models


class AllianceState(BaseModel):
    """Current state of alliance selection process"""
    selection_id: int = Field(..., description="Selection ID")
    event_key: str = Field(..., description="Event key")
    year: int = Field(..., description="Competition year")
    is_completed: bool = Field(..., description="Whether selection is complete")
    current_round: int = Field(..., description="Current round number")
    current_alliance: Optional[int] = Field(None, description="Alliance currently picking")
    picklist_id: Optional[int] = Field(None, description="Associated picklist ID")

    # Timing information
    started_at: datetime = Field(..., description="When selection started")
    completed_at: Optional[datetime] = Field(None, description="When selection completed")
    last_action_at: Optional[datetime] = Field(None, description="Time of last action")

    # Statistics
    total_teams: int = Field(..., description="Total teams in event")
    picked_teams: int = Field(..., description="Number of picked teams")
    declined_teams: int = Field(..., description="Number of teams that declined")

    class Config:
        schema_extra = {
            "example": {
                "selection_id": 1,
                "event_key": "2025arc",
                "year": 2025,
                "is_completed": False,
                "current_round": 2,
                "current_alliance": 3,
                "picklist_id": 42,
                "started_at": "2025-01-01T10:00:00Z",
                "last_action_at": "2025-01-01T10:30:00Z",
                "total_teams": 60,
                "picked_teams": 16,
                "declined_teams": 2
            }
        }


class TeamStatus(BaseModel):
    """Detailed team status in alliance selection"""
    team_number: int = Field(..., description="Team number")
    team_name: Optional[str] = Field(None, description="Team name")
    status: Literal["available", "captain", "picked", "declined", "eliminated"] = Field(
        ...,
        description="Current status"
    )
    alliance_number: Optional[int] = Field(None, description="Alliance number if picked")
    pick_order: Optional[int] = Field(None, description="Order in which team was picked")
    round_picked: Optional[int] = Field(None, description="Round when picked")
    declined_count: int = Field(0, description="Number of times declined")

    class Config:
        schema_extra = {
            "example": {
                "team_number": 254,
                "team_name": "The Cheesy Poofs",
                "status": "captain",
                "alliance_number": 1,
                "pick_order": 1,
                "round_picked": 0,
                "declined_count": 0
            }
        }


class TeamActionResponse(BaseModel):
    """Response from a team action"""
    status: Literal["success"] = Field(default="success", description="Always 'success' for successful responses")
    message: str = Field(..., description="Action result message")
    action: str = Field(..., description="Action performed")
    team_number: int = Field(..., description="Team affected")
    alliance_number: Optional[int] = Field(None, description="Alliance affected")
    selection_state: AllianceSelectionStateResponse = Field(
        ...,
        description="Updated selection state"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Team 254 selected as captain of Alliance 1",
                "action": "captain",
                "team_number": 254,
                "alliance_number": 1,
                "selection_state": {
                    "id": 1,
                    "event_key": "2025arc",
                    "year": 2025,
                    "is_completed": False,
                    "current_round": 1,
                    "alliances": [],
                    "team_statuses": []
                }
            }
        }


class ResetSelectionRequest(BaseModel):
    """Request to reset alliance selection"""
    confirm: bool = Field(..., description="Must be true to confirm reset")
    reason: Optional[str] = Field(None, description="Reason for reset")

    class Config:
        schema_extra = {
            "example": {
                "confirm": True,
                "reason": "Need to restart due to error in captain selection"
            }
        }


class AdvanceRoundResponse(BaseModel):
    """Response from advancing to next round"""
    status: Literal["success"] = Field(default="success", description="Always 'success' for successful responses")
    message: str = Field(..., description="Round advancement message")
    previous_round: int = Field(..., description="Previous round number")
    current_round: int = Field(..., description="New round number")
    is_completed: bool = Field(..., description="Whether selection is now complete")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Advanced to round 2",
                "previous_round": 1,
                "current_round": 2,
                "is_completed": False
            }
        }


class PicklistListResponse(BaseModel):
    """Response for listing picklists"""
    status: Literal["success"] = Field(default="success", description="Always 'success' for successful responses")
    picklists: List[Dict[str, Any]] = Field(..., description="List of picklists")
    total: int = Field(..., description="Total number of picklists")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "picklists": [
                    {
                        "id": 1,
                        "team_number": 1234,
                        "event_key": "2025arc",
                        "year": 2025,
                        "created_at": "2025-01-01T10:00:00Z"
                    }
                ],
                "total": 1
            }
        }


class PicklistDetailResponse(BaseModel):
    """Response for picklist details"""
    status: Literal["success"] = Field(default="success", description="Always 'success' for successful responses")
    picklist: Dict[str, Any] = Field(..., description="Picklist details")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "picklist": {
                    "id": 1,
                    "team_number": 1234,
                    "event_key": "2025arc",
                    "year": 2025,
                    "first_pick_data": {"teams": []},
                    "second_pick_data": {"teams": []},
                    "created_at": "2025-01-01T10:00:00Z"
                }
            }
        }
