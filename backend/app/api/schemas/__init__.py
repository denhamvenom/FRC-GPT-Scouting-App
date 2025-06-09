"""
API Schemas Package

This package contains Pydantic schemas for API request/response validation.
The schemas provide strong typing, validation, and documentation for the API layer.
"""

from .alliance import (
    AllianceSelectionRequest,
    AllianceSelectionResponse,
    AllianceState,
    LockedPicklistResponse,
    LockPicklistRequest,
    TeamActionRequest,
    TeamActionResponse,
    TeamStatus,
)
from .common import (
    ErrorResponse,
    HealthCheckResponse,
    PaginatedResponse,
    StatusResponse,
    SuccessResponse,
)
from .picklist import (
    BatchProcessingStatus,
    MetricPriority,
    PicklistGenerateRequest,
    PicklistGenerateResponse,
    PicklistUpdateRequest,
    PicklistUpdateResponse,
    RankMissingTeamsRequest,
    RankMissingTeamsResponse,
    TeamRanking,
    UserRanking,
)

__all__ = [
    # Common schemas
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "StatusResponse",
    "HealthCheckResponse",
    # Picklist schemas
    "MetricPriority",
    "PicklistGenerateRequest",
    "PicklistGenerateResponse",
    "PicklistUpdateRequest",
    "PicklistUpdateResponse",
    "RankMissingTeamsRequest",
    "RankMissingTeamsResponse",
    "UserRanking",
    "TeamRanking",
    "BatchProcessingStatus",
    # Alliance schemas
    "LockPicklistRequest",
    "LockedPicklistResponse",
    "AllianceSelectionRequest",
    "AllianceSelectionResponse",
    "TeamActionRequest",
    "TeamActionResponse",
    "AllianceState",
    "TeamStatus",
]
