# backend/app/services/alliance/team_action_service.py
"""
Team Action Service

This service handles all team actions during alliance selection:
- Making teams captains
- Teams accepting/declining picks
- Removing teams from alliances

This represents the refactored 225-line team_action() method from the original
alliance_selection.py file, broken down into focused, testable methods.
"""

from typing import Optional
import logging
from sqlalchemy.orm import Session

from .models import TeamActionRequest, TeamActionResponse
from .exceptions import (
    SelectionNotFoundError,
    TeamNotFoundError,
    SelectionCompletedError,
    InvalidActionError,
    AllianceNotFoundError,
    InvalidAllianceNumberError,
    TeamAlreadySelectedError,
    AllianceAlreadyCompleteError,
    CaptainRemovalError,
)
from .state_manager import AllianceStateManager
from .rules_engine import AllianceRulesEngine

logger = logging.getLogger(__name__)


class TeamActionService:
    """Handles team actions during alliance selection."""

    def __init__(self, db: Session):
        self.db = db
        self.state_manager = AllianceStateManager(db)
        self.rules_engine = AllianceRulesEngine()

    def execute_team_action(self, request: TeamActionRequest) -> TeamActionResponse:
        """
        Execute a team action during alliance selection.
        
        Args:
            request: TeamActionRequest with action details
            
        Returns:
            TeamActionResponse with result
            
        Raises:
            Various AllianceSelectionError subclasses for validation failures
        """
        # Validate selection exists and is not completed
        selection = self.state_manager.get_selection(request.selection_id)
        if selection.is_completed:
            raise SelectionCompletedError(request.selection_id)

        # Get team status
        team_status = self.state_manager.get_team_status(request.selection_id, request.team_number)
        if not team_status:
            raise TeamNotFoundError(request.team_number)

        # Route to specific action handler
        if request.action == "captain":
            return self._handle_captain_action(request, selection, team_status)
        elif request.action == "accept":
            return self._handle_accept_action(request, selection, team_status)
        elif request.action == "decline":
            return self._handle_decline_action(request, selection, team_status)
        elif request.action == "remove":
            return self._handle_remove_action(request, selection, team_status)
        else:
            raise InvalidActionError(f"Invalid action: {request.action}")

    def _handle_captain_action(self, request, selection, team_status) -> TeamActionResponse:
        """Handle making a team the captain of an alliance."""
        # Validate alliance number is provided
        if not request.alliance_number:
            raise InvalidAllianceNumberError(0)
        
        self.rules_engine.validate_alliance_number(request.alliance_number)

        # Check team availability
        availability = self.rules_engine.validate_team_availability(
            team_status, "captain", selection.current_round
        )
        if not availability.is_available:
            raise TeamAlreadySelectedError(request.team_number, availability.reason)

        # Get alliance and validate captain assignment
        alliance = self.state_manager.get_alliance_by_number(
            request.selection_id, request.alliance_number
        )
        if not alliance:
            raise AllianceNotFoundError(request.alliance_number)

        validation = self.rules_engine.validate_captain_assignment(alliance, request.team_number)
        if not validation.is_valid:
            raise AllianceAlreadyCompleteError(request.alliance_number, "captain")

        # Update alliance and team status
        self.state_manager.update_alliance_captain(alliance, request.team_number)
        self.state_manager.update_team_status(team_status, is_captain=True)

        logger.info(f"Team {request.team_number} set as captain of alliance {request.alliance_number}")
        
        return TeamActionResponse(
            status="success",
            action="captain",
            team_number=request.team_number,
            alliance_number=request.alliance_number
        )

    def _handle_accept_action(self, request, selection, team_status) -> TeamActionResponse:
        """Handle a team accepting to be picked by an alliance."""
        # Validate alliance number is provided
        if not request.alliance_number:
            raise InvalidAllianceNumberError(0)
        
        self.rules_engine.validate_alliance_number(request.alliance_number)

        # Check team availability
        availability = self.rules_engine.validate_team_availability(
            team_status, "accept", selection.current_round
        )
        if not availability.is_available:
            raise TeamAlreadySelectedError(request.team_number, availability.reason)

        # Get alliance and validate pick
        alliance = self.state_manager.get_alliance_by_number(
            request.selection_id, request.alliance_number
        )
        if not alliance:
            raise AllianceNotFoundError(request.alliance_number)

        validation, position = self.rules_engine.validate_team_pick(
            alliance, request.team_number, selection.current_round
        )
        if not validation.is_valid:
            raise AllianceAlreadyCompleteError(request.alliance_number, "position")

        # Update alliance and team status
        self.state_manager.update_alliance_pick(alliance, request.team_number, position)
        self.state_manager.update_team_status(team_status, is_picked=True)

        logger.info(f"Team {request.team_number} accepted as {position} for alliance {request.alliance_number}")
        
        return TeamActionResponse(
            status="success",
            action="accept",
            team_number=request.team_number,
            alliance_number=request.alliance_number,
            position=position
        )

    def _handle_decline_action(self, request, selection, team_status) -> TeamActionResponse:
        """Handle a team declining to be picked."""
        # Check team availability
        availability = self.rules_engine.validate_team_availability(
            team_status, "decline", selection.current_round
        )
        if not availability.is_available:
            raise TeamAlreadySelectedError(request.team_number, availability.reason)

        # Update team status
        self.state_manager.update_team_status(team_status, has_declined=True)

        logger.info(f"Team {request.team_number} declined selection")
        
        return TeamActionResponse(
            status="success",
            action="decline",
            team_number=request.team_number
        )

    def _handle_remove_action(self, request, selection, team_status) -> TeamActionResponse:
        """Handle removing a team from an alliance."""
        # Validate alliance number is provided
        if not request.alliance_number:
            raise InvalidAllianceNumberError(0)
        
        self.rules_engine.validate_alliance_number(request.alliance_number)

        # Get alliance and validate removal
        alliance = self.state_manager.get_alliance_by_number(
            request.selection_id, request.alliance_number
        )
        if not alliance:
            raise AllianceNotFoundError(request.alliance_number)

        validation, position = self.rules_engine.validate_team_removal(alliance, request.team_number)
        if not validation.is_valid:
            # Check for captain removal specifically
            if alliance.captain_team_number == request.team_number:
                raise CaptainRemovalError(request.team_number)
            raise InvalidActionError(validation.errors[0])

        # Update alliance and team status
        self.state_manager.remove_alliance_pick(alliance, position)
        self.state_manager.update_team_status(
            team_status, 
            is_picked=False, 
            round_eliminated=None  # Clear elimination to make team available
        )

        logger.info(f"Removed team {request.team_number} as {position} from alliance {request.alliance_number}")
        
        return TeamActionResponse(
            status="success",
            action="remove",
            team_number=request.team_number,
            alliance_number=request.alliance_number,
            position=position
        )