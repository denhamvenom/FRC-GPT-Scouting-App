"""
Setup API Schemas

This module contains schemas specific to the setup API endpoints.
Includes models for event management, learning setup, and configuration.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

from .common import SuccessResponse


class EventInfo(BaseModel):
    """Basic event information"""
    key: str = Field(..., description="Event key (e.g., '2025arc')")
    name: str = Field(..., description="Event name")
    event_code: str = Field(..., description="Event code")
    event_type: int = Field(..., description="Event type number")
    event_type_string: Optional[str] = Field(None, description="Human-readable event type")
    district: Optional[Dict[str, Any]] = Field(None, description="District information")
    city: Optional[str] = Field(None, description="Event city")
    state_prov: Optional[str] = Field(None, description="State or province")
    country: Optional[str] = Field(None, description="Country")
    start_date: str = Field(..., description="Event start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Event end date (YYYY-MM-DD)")
    year: int = Field(..., description="Event year")
    week: Optional[int] = Field(None, description="Competition week")
    timezone: Optional[str] = Field(None, description="Event timezone")
    website: Optional[str] = Field(None, description="Event website")
    first_event_code: Optional[str] = Field(None, description="FIRST event code")

    class Config:
        schema_extra = {
            "example": {
                "key": "2025arc",
                "name": "Archimedes Division",
                "event_code": "arc",
                "event_type": 3,
                "event_type_string": "Championship Division",
                "city": "Houston",
                "state_prov": "TX",
                "country": "USA",
                "start_date": "2025-04-17",
                "end_date": "2025-04-20",
                "year": 2025,
                "week": 7
            }
        }


class EventTeam(BaseModel):
    """Team participating in an event"""
    team_number: int = Field(..., description="Team number")
    nickname: str = Field(..., description="Team nickname")
    name: str = Field(..., description="Full team name")
    city: Optional[str] = Field(None, description="Team city")
    state_prov: Optional[str] = Field(None, description="Team state/province")
    country: Optional[str] = Field(None, description="Team country")
    rookie_year: Optional[int] = Field(None, description="Team's rookie year")

    class Config:
        schema_extra = {
            "example": {
                "team_number": 254,
                "nickname": "The Cheesy Poofs",
                "name": "NASA Ames Research Center/Google",
                "city": "San Jose",
                "state_prov": "CA",
                "country": "USA",
                "rookie_year": 1999
            }
        }


class SetupConfiguration(BaseModel):
    """Setup configuration for the application"""
    event_key: str = Field(..., description="Current event key")
    event_name: str = Field(..., description="Event name")
    year: int = Field(..., description="Competition year")
    sheet_id: Optional[str] = Field(None, description="Google Sheet ID")
    sheet_configured: bool = Field(False, description="Whether sheet is configured")
    schema_learned: bool = Field(False, description="Whether schema is learned")
    teams_loaded: bool = Field(False, description="Whether teams are loaded")
    dataset_built: bool = Field(False, description="Whether dataset is built")
    setup_complete: bool = Field(False, description="Whether setup is complete")
    last_updated: Optional[datetime] = Field(None, description="Last configuration update")

    @validator('setup_complete', always=True)
    def check_setup_complete(cls, v, values):
        """Setup is complete when all components are configured"""
        return all([
            values.get('sheet_configured', False),
            values.get('schema_learned', False),
            values.get('teams_loaded', False),
            values.get('dataset_built', False)
        ])

    class Config:
        schema_extra = {
            "example": {
                "event_key": "2025arc",
                "event_name": "Archimedes Division",
                "year": 2025,
                "sheet_id": "1234567890abcdef",
                "sheet_configured": True,
                "schema_learned": True,
                "teams_loaded": True,
                "dataset_built": False,
                "setup_complete": False,
                "last_updated": "2025-01-01T12:00:00Z"
            }
        }


class SetupStep(BaseModel):
    """Represents a step in the setup process"""
    id: str = Field(..., description="Step identifier")
    name: str = Field(..., description="Step name")
    description: str = Field(..., description="Step description")
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"] = Field(
        ...,
        description="Step status"
    )
    required: bool = Field(True, description="Whether step is required")
    order: int = Field(..., description="Step order")
    error: Optional[str] = Field(None, description="Error message if failed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "configure_sheet",
                "name": "Configure Google Sheet",
                "description": "Set up Google Sheet connection and permissions",
                "status": "completed",
                "required": True,
                "order": 1,
                "completed_at": "2025-01-01T12:00:00Z"
            }
        }


# Request Models

class EventsRequest(BaseModel):
    """Request for fetching events"""
    year: int = Field(..., ge=1992, le=2030, description="Competition year")
    event_type: Optional[int] = Field(
        None,
        description="Filter by event type (0=Regional, 1=District, 2=District Championship, etc.)"
    )
    district_key: Optional[str] = Field(None, description="Filter by district")
    week: Optional[int] = Field(None, ge=0, le=8, description="Filter by competition week")

    class Config:
        schema_extra = {
            "example": {
                "year": 2025,
                "event_type": 0,
                "week": 1
            }
        }


class StartSetupRequest(BaseModel):
    """Request to start the setup process"""
    event_key: str = Field(..., description="Event key to set up")
    sheet_id: Optional[str] = Field(None, description="Google Sheet ID")
    skip_sheet: bool = Field(False, description="Skip sheet configuration")
    auto_learn_schema: bool = Field(True, description="Automatically learn schema")
    
    @validator('event_key')
    def validate_event_key(cls, v):
        """Validate event key format"""
        if not v or len(v) < 4:
            raise ValueError("Invalid event key format")
        return v

    class Config:
        schema_extra = {
            "example": {
                "event_key": "2025arc",
                "sheet_id": "1234567890abcdef",
                "skip_sheet": False,
                "auto_learn_schema": True
            }
        }


class UpdateSetupRequest(BaseModel):
    """Request to update setup configuration"""
    sheet_id: Optional[str] = Field(None, description="Update Google Sheet ID")
    sheet_configured: Optional[bool] = Field(None, description="Update sheet status")
    schema_learned: Optional[bool] = Field(None, description="Update schema status")
    teams_loaded: Optional[bool] = Field(None, description="Update teams status")
    dataset_built: Optional[bool] = Field(None, description="Update dataset status")

    class Config:
        schema_extra = {
            "example": {
                "sheet_configured": True,
                "schema_learned": True
            }
        }


# Response Models

class EventsResponse(SuccessResponse):
    """Response containing list of events"""
    year: int = Field(..., description="Year of events")
    events: List[EventInfo] = Field(..., description="List of events")
    total: int = Field(..., description="Total number of events")
    filtered: int = Field(..., description="Number of events after filtering")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "year": 2025,
                "events": [],
                "total": 150,
                "filtered": 10
            }
        }


class EventDetailResponse(SuccessResponse):
    """Response with detailed event information"""
    event: EventInfo = Field(..., description="Event information")
    teams: List[EventTeam] = Field(..., description="Teams attending event")
    team_count: int = Field(..., description="Number of teams")
    matches_scheduled: int = Field(..., description="Number of matches scheduled")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event": {
                    "key": "2025arc",
                    "name": "Archimedes Division",
                    "event_code": "arc",
                    "event_type": 3,
                    "event_type_string": "Championship Division",
                    "start_date": "2025-04-17",
                    "end_date": "2025-04-20",
                    "year": 2025
                },
                "teams": [],
                "team_count": 68,
                "matches_scheduled": 120
            }
        }


class SetupInfoResponse(SuccessResponse):
    """Response with current setup information"""
    setup: SetupConfiguration = Field(..., description="Setup configuration")
    steps: List[SetupStep] = Field(..., description="Setup steps and status")
    progress: float = Field(..., ge=0, le=100, description="Overall progress percentage")
    next_step: Optional[str] = Field(None, description="Next recommended step")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "setup": {
                    "event_key": "2025arc",
                    "event_name": "Archimedes Division",
                    "year": 2025,
                    "sheet_configured": True,
                    "schema_learned": False,
                    "teams_loaded": True,
                    "dataset_built": False,
                    "setup_complete": False
                },
                "steps": [],
                "progress": 50.0,
                "next_step": "learn_schema"
            }
        }


class StartSetupResponse(SuccessResponse):
    """Response for starting setup process"""
    event_key: str = Field(..., description="Event being set up")
    setup_id: str = Field(..., description="Setup process ID")
    setup_status: str = Field(..., description="Setup status")
    next_steps: List[str] = Field(..., description="Next steps to complete")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event_key": "2025arc",
                "setup_id": "setup_2025arc_123456",
                "status": "in_progress",
                "message": "Setup started successfully",
                "next_steps": [
                    "Configure Google Sheet",
                    "Learn schema from headers",
                    "Load team data",
                    "Build unified dataset"
                ]
            }
        }