# backend/app/services/alliance/__init__.py
"""
Alliance Selection Service Package

This package provides a refactored, service-oriented architecture for FRC alliance selection.
It follows the same patterns established in the picklist service refactoring.

Key Components:
- AllianceSelectionService: Main orchestrator for alliance selection operations
- TeamActionService: Handles team actions (captain, accept, decline, remove)
- StateManager: Manages alliance selection state and transitions
- RulesEngine: Implements FRC alliance selection rules validation
- Models: Pydantic data models for type safety
- Exceptions: Custom exceptions for alliance-specific errors

The refactored architecture reduces the original 773-line API controller to focused,
single-responsibility services that are easier to test and maintain.
"""

from .selection_service import AllianceSelectionService
from .team_action_service import TeamActionService
from .state_manager import AllianceStateManager
from .rules_engine import AllianceRulesEngine
from .models import (
    AllianceSelectionRequest,
    TeamActionRequest,
    AllianceSelectionResponse,
    TeamStatusResponse,
    AllianceResponse,
)
from .exceptions import (
    AllianceSelectionError,
    InvalidActionError,
    InvalidRoundError,
    AllianceNotFoundError,
    TeamNotFoundError,
    SelectionCompletedError,
)

__all__ = [
    "AllianceSelectionService",
    "TeamActionService", 
    "AllianceStateManager",
    "AllianceRulesEngine",
    "AllianceSelectionRequest",
    "TeamActionRequest",
    "AllianceSelectionResponse",
    "TeamStatusResponse",
    "AllianceResponse",
    "AllianceSelectionError",
    "InvalidActionError",
    "InvalidRoundError",
    "AllianceNotFoundError", 
    "TeamNotFoundError",
    "SelectionCompletedError",
]