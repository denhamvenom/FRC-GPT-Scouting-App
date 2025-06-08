# backend/app/services/alliance/selection_service.py
"""
Alliance Selection Service

Main orchestrator for alliance selection operations. This service provides
a clean interface for all alliance selection functionality, coordinating
between the state manager, team action service, and rules engine.

This represents the refactored core logic from the original 773-line
alliance_selection.py API controller.
"""

from typing import List, Optional
import logging
from sqlalchemy.orm import Session

from .models import (
    AllianceSelectionRequest,
    AllianceSelectionResponse,
    AllianceSelectionStateResponse,
    TeamActionRequest,
    TeamActionResponse,
    RoundAdvanceResponse,
    SelectionResetResponse,
)
from .state_manager import AllianceStateManager
from .team_action_service import TeamActionService
from .rules_engine import AllianceRulesEngine
from .exceptions import AllianceSelectionError

logger = logging.getLogger(__name__)


class AllianceSelectionService:
    """Main service for alliance selection operations."""

    def __init__(self, db: Session):
        self.db = db
        self.state_manager = AllianceStateManager(db)
        self.team_action_service = TeamActionService(db)
        self.rules_engine = AllianceRulesEngine()

    def create_alliance_selection(
        self, request: AllianceSelectionRequest
    ) -> AllianceSelectionResponse:
        """
        Create a new alliance selection process.
        
        Args:
            request: AllianceSelectionRequest with selection details
            
        Returns:
            AllianceSelectionResponse with created selection info
            
        Raises:
            PicklistNotFoundError: If picklist_id provided but not found
            DuplicateSelectionError: If selection already exists for picklist
        """
        try:
            selection = self.state_manager.create_selection(
                picklist_id=request.picklist_id,
                event_key=request.event_key,
                year=request.year,
                team_list=request.team_list
            )

            logger.info(f"Created alliance selection {selection.id} for event {request.event_key}")
            
            return AllianceSelectionResponse(
                id=selection.id,
                event_key=selection.event_key,
                year=selection.year,
                is_completed=selection.is_completed,
                current_round=selection.current_round
            )

        except Exception as e:
            logger.error(f"Error creating alliance selection: {str(e)}")
            raise

    def get_alliance_selection(self, selection_id: int) -> AllianceSelectionStateResponse:
        """
        Get the current state of an alliance selection.
        
        Args:
            selection_id: ID of the alliance selection
            
        Returns:
            AllianceSelectionStateResponse with complete state
            
        Raises:
            SelectionNotFoundError: If selection not found
        """
        try:
            return self.state_manager.get_selection_state(selection_id)

        except Exception as e:
            logger.error(f"Error retrieving alliance selection {selection_id}: {str(e)}")
            raise

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
        try:
            return self.team_action_service.execute_team_action(request)

        except AllianceSelectionError:
            # Re-raise alliance selection errors as-is
            raise
        except Exception as e:
            logger.error(f"Error executing team action: {str(e)}")
            raise AllianceSelectionError(f"Error performing team action: {str(e)}")

    def advance_to_next_round(self, selection_id: int) -> RoundAdvanceResponse:
        """
        Advance the alliance selection to the next round.
        
        Args:
            selection_id: ID of the alliance selection
            
        Returns:
            RoundAdvanceResponse with result
            
        Raises:
            SelectionNotFoundError: If selection not found
            SelectionCompletedError: If selection already completed
        """
        try:
            # Get current state for validation
            selection = self.state_manager.get_selection(selection_id)
            alliances = self.state_manager.get_alliances(selection_id)
            
            # Validate round advancement
            validation = self.rules_engine.validate_round_advancement(selection, alliances)
            if validation.warnings:
                logger.warning(f"Round advancement warnings for selection {selection_id}: {validation.warnings}")

            # Advance the round
            response = self.state_manager.advance_round(selection_id)
            
            logger.info(f"Advanced alliance selection {selection_id} to next round")
            return response

        except Exception as e:
            logger.error(f"Error advancing to next round for selection {selection_id}: {str(e)}")
            raise

    def reset_alliance_selection(self, selection_id: int) -> SelectionResetResponse:
        """
        Reset an alliance selection back to the beginning.
        
        Args:
            selection_id: ID of the alliance selection
            
        Returns:
            SelectionResetResponse with result
            
        Raises:
            SelectionNotFoundError: If selection not found
        """
        try:
            response = self.state_manager.reset_selection(selection_id)
            
            logger.info(f"Reset alliance selection {selection_id}")
            return response

        except Exception as e:
            logger.error(f"Error resetting alliance selection {selection_id}: {str(e)}")
            raise

    def get_selection_status(self, selection_id: int) -> dict:
        """
        Get basic status information for an alliance selection.
        
        Args:
            selection_id: ID of the alliance selection
            
        Returns:
            Dictionary with basic selection status
        """
        try:
            selection = self.state_manager.get_selection(selection_id)
            alliances = self.state_manager.get_alliances(selection_id)
            
            # Get completion status
            is_complete, reasons = self.rules_engine.get_selection_completion_status(selection, alliances)
            
            return {
                "id": selection.id,
                "event_key": selection.event_key,
                "year": selection.year,
                "is_completed": selection.is_completed,
                "current_round": selection.current_round,
                "picklist_id": selection.picklist_id,
                "completion_analysis": {
                    "is_complete": is_complete,
                    "reasons": reasons
                }
            }

        except Exception as e:
            logger.error(f"Error getting selection status for {selection_id}: {str(e)}")
            raise

    def validate_selection_state(self, selection_id: int) -> dict:
        """
        Validate the current state of an alliance selection.
        
        Args:
            selection_id: ID of the alliance selection
            
        Returns:
            Dictionary with validation results
        """
        try:
            selection = self.state_manager.get_selection(selection_id)
            alliances = self.state_manager.get_alliances(selection_id)
            team_statuses = self.state_manager.get_team_statuses(selection_id)
            
            # Basic state validation
            validation_results = {
                "selection_id": selection_id,
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Check alliance integrity
            for alliance in alliances:
                if alliance.captain_team_number == 0:
                    validation_results["warnings"].append(
                        f"Alliance {alliance.alliance_number} has no captain"
                    )
                
                # Check for duplicate team assignments
                team_numbers = [
                    alliance.captain_team_number,
                    alliance.first_pick_team_number,
                    alliance.second_pick_team_number,
                    alliance.backup_team_number
                ]
                team_numbers = [t for t in team_numbers if t != 0]
                
                if len(team_numbers) != len(set(team_numbers)):
                    validation_results["errors"].append(
                        f"Alliance {alliance.alliance_number} has duplicate team assignments"
                    )
                    validation_results["is_valid"] = False
            
            # Check team status consistency
            captain_count = sum(1 for ts in team_statuses if ts.is_captain)
            picked_count = sum(1 for ts in team_statuses if ts.is_picked)
            
            if captain_count > 8:
                validation_results["errors"].append(f"Too many captains: {captain_count} (max 8)")
                validation_results["is_valid"] = False
            
            return validation_results

        except Exception as e:
            logger.error(f"Error validating selection state for {selection_id}: {str(e)}")
            raise