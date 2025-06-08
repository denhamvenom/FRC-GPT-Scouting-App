# backend/app/services/alliance/state_manager.py
"""
Alliance Selection State Manager

This module manages the state of alliance selections, including state transitions,
persistence, and validation of state changes.
"""

from typing import List, Optional
import logging
from sqlalchemy.orm import Session

from app.database.models import AllianceSelection, Alliance, TeamSelectionStatus, LockedPicklist
from .models import (
    AllianceSelectionStateResponse,
    AllianceResponse,
    TeamStatusResponse,
    RoundAdvanceResponse,
    SelectionResetResponse,
)
from .exceptions import (
    SelectionNotFoundError,
    PicklistNotFoundError,
    DuplicateSelectionError,
    SelectionCompletedError,
)
from .rules_engine import AllianceRulesEngine

logger = logging.getLogger(__name__)


class AllianceStateManager:
    """Manages alliance selection state and transitions."""

    def __init__(self, db: Session):
        self.db = db
        self.rules_engine = AllianceRulesEngine()

    def create_selection(
        self,
        picklist_id: Optional[int],
        event_key: str,
        year: int,
        team_list: List[int]
    ) -> AllianceSelection:
        """
        Create a new alliance selection.
        
        Args:
            picklist_id: Optional ID of locked picklist to use
            event_key: Event key for the selection
            year: Competition year
            team_list: List of team numbers participating
            
        Returns:
            Created AllianceSelection instance
            
        Raises:
            PicklistNotFoundError: If picklist_id provided but not found
            DuplicateSelectionError: If selection already exists for picklist
        """
        # Validate picklist if provided
        if picklist_id is not None:
            picklist = self.db.query(LockedPicklist).filter(LockedPicklist.id == picklist_id).first()
            if not picklist:
                raise PicklistNotFoundError(picklist_id)
            
            # Check for existing selection with this picklist
            existing = (
                self.db.query(AllianceSelection)
                .filter(AllianceSelection.picklist_id == picklist_id)
                .first()
            )
            if existing:
                raise DuplicateSelectionError("Alliance selection already exists for this picklist")

        # Create the selection
        selection = AllianceSelection(
            picklist_id=picklist_id,
            event_key=event_key,
            year=year,
            is_completed=False,
            current_round=1,
        )
        
        self.db.add(selection)
        self.db.commit()
        self.db.refresh(selection)

        # Create alliances (1-8)
        for i in range(1, 9):
            alliance = Alliance(selection_id=selection.id, alliance_number=i)
            self.db.add(alliance)

        # Initialize team statuses
        for team_number in team_list:
            team_status = TeamSelectionStatus(
                selection_id=selection.id,
                team_number=team_number,
                is_captain=False,
                is_picked=False,
                has_declined=False,
            )
            self.db.add(team_status)

        self.db.commit()
        
        logger.info(f"Created alliance selection {selection.id} for event {event_key}")
        return selection

    def get_selection(self, selection_id: int) -> AllianceSelection:
        """
        Get alliance selection by ID.
        
        Args:
            selection_id: ID of the selection
            
        Returns:
            AllianceSelection instance
            
        Raises:
            SelectionNotFoundError: If selection not found
        """
        selection = self.db.query(AllianceSelection).filter(AllianceSelection.id == selection_id).first()
        if not selection:
            raise SelectionNotFoundError(selection_id)
        return selection

    def get_alliances(self, selection_id: int) -> List[Alliance]:
        """Get all alliances for a selection."""
        return self.db.query(Alliance).filter(Alliance.selection_id == selection_id).all()

    def get_team_statuses(self, selection_id: int) -> List[TeamSelectionStatus]:
        """Get all team statuses for a selection."""
        return (
            self.db.query(TeamSelectionStatus)
            .filter(TeamSelectionStatus.selection_id == selection_id)
            .all()
        )

    def get_alliance_by_number(self, selection_id: int, alliance_number: int) -> Optional[Alliance]:
        """Get specific alliance by number."""
        return (
            self.db.query(Alliance)
            .filter(
                Alliance.selection_id == selection_id,
                Alliance.alliance_number == alliance_number,
            )
            .first()
        )

    def get_team_status(self, selection_id: int, team_number: int) -> Optional[TeamSelectionStatus]:
        """Get specific team status."""
        return (
            self.db.query(TeamSelectionStatus)
            .filter(
                TeamSelectionStatus.selection_id == selection_id,
                TeamSelectionStatus.team_number == team_number,
            )
            .first()
        )

    def get_selection_state(self, selection_id: int) -> AllianceSelectionStateResponse:
        """
        Get complete alliance selection state.
        
        Args:
            selection_id: ID of the selection
            
        Returns:
            AllianceSelectionStateResponse with complete state
        """
        selection = self.get_selection(selection_id)
        alliances = self.get_alliances(selection_id)
        team_statuses = self.get_team_statuses(selection_id)

        return AllianceSelectionStateResponse(
            id=selection.id,
            event_key=selection.event_key,
            year=selection.year,
            is_completed=selection.is_completed,
            current_round=selection.current_round,
            picklist_id=selection.picklist_id,
            alliances=[
                AllianceResponse(
                    alliance_number=a.alliance_number,
                    captain_team_number=a.captain_team_number,
                    first_pick_team_number=a.first_pick_team_number,
                    second_pick_team_number=a.second_pick_team_number,
                    backup_team_number=a.backup_team_number,
                )
                for a in sorted(alliances, key=lambda x: x.alliance_number)
            ],
            team_statuses=[
                TeamStatusResponse(
                    team_number=ts.team_number,
                    is_captain=ts.is_captain,
                    is_picked=ts.is_picked,
                    has_declined=ts.has_declined,
                    round_eliminated=ts.round_eliminated,
                )
                for ts in sorted(team_statuses, key=lambda x: x.team_number)
            ],
        )

    def advance_round(self, selection_id: int) -> RoundAdvanceResponse:
        """
        Advance alliance selection to next round.
        
        Args:
            selection_id: ID of the selection
            
        Returns:
            RoundAdvanceResponse with result
            
        Raises:
            SelectionNotFoundError: If selection not found
            SelectionCompletedError: If selection already completed
        """
        selection = self.get_selection(selection_id)
        
        if selection.is_completed:
            raise SelectionCompletedError(selection_id)

        current_round = selection.current_round
        
        # Check if we should mark as completed
        if current_round >= 3:
            selection.is_completed = True
            self.db.commit()
            
            logger.info(f"Alliance selection {selection_id} marked as completed")
            return RoundAdvanceResponse(
                status="success",
                action="completed",
                selection_id=selection_id,
                message="Alliance selection completed successfully!"
            )

        # Mark all captains and picked teams as eliminated for current round
        self._mark_teams_eliminated(selection_id, current_round)

        # Advance to next round
        selection.current_round += 1
        self.db.commit()

        logger.info(f"Alliance selection {selection_id} advanced to round {selection.current_round}")
        return RoundAdvanceResponse(
            status="success",
            action="next_round",
            selection_id=selection_id,
            new_round=selection.current_round
        )

    def reset_selection(self, selection_id: int) -> SelectionResetResponse:
        """
        Reset alliance selection to beginning.
        
        Args:
            selection_id: ID of the selection
            
        Returns:
            SelectionResetResponse with result
            
        Raises:
            SelectionNotFoundError: If selection not found
        """
        selection = self.get_selection(selection_id)
        
        # Reset all alliances
        alliances = self.get_alliances(selection_id)
        for alliance in alliances:
            alliance.captain_team_number = 0
            alliance.first_pick_team_number = 0
            alliance.second_pick_team_number = 0
            alliance.backup_team_number = 0

        # Reset all team statuses
        team_statuses = self.get_team_statuses(selection_id)
        for ts in team_statuses:
            ts.is_captain = False
            ts.is_picked = False
            ts.has_declined = False
            ts.round_eliminated = None

        # Reset the selection itself
        selection.current_round = 1
        selection.is_completed = False

        self.db.commit()
        
        logger.info(f"Alliance selection {selection_id} reset to beginning")
        return SelectionResetResponse(
            status="success",
            action="reset",
            selection_id=selection_id,
            message="Alliance selection has been reset to the beginning"
        )

    def _mark_teams_eliminated(self, selection_id: int, current_round: int) -> None:
        """Mark captains and picked teams as eliminated for the current round."""
        # Mark all captains as eliminated
        captain_statuses = (
            self.db.query(TeamSelectionStatus)
            .filter(
                TeamSelectionStatus.selection_id == selection_id,
                TeamSelectionStatus.is_captain == True,
                TeamSelectionStatus.round_eliminated.is_(None)
            )
            .all()
        )
        
        for ts in captain_statuses:
            ts.round_eliminated = current_round

        # Mark all picked teams as eliminated
        picked_statuses = (
            self.db.query(TeamSelectionStatus)
            .filter(
                TeamSelectionStatus.selection_id == selection_id,
                TeamSelectionStatus.is_picked == True,
                TeamSelectionStatus.round_eliminated.is_(None)
            )
            .all()
        )
        
        for ts in picked_statuses:
            ts.round_eliminated = current_round

    def update_alliance_captain(self, alliance: Alliance, team_number: int) -> None:
        """Update alliance captain."""
        alliance.captain_team_number = team_number
        self.db.commit()

    def update_alliance_pick(self, alliance: Alliance, team_number: int, position: str) -> None:
        """Update alliance pick for specified position."""
        if position == "first_pick":
            alliance.first_pick_team_number = team_number
        elif position == "second_pick":
            alliance.second_pick_team_number = team_number
        elif position == "backup":
            alliance.backup_team_number = team_number
        
        self.db.commit()

    def remove_alliance_pick(self, alliance: Alliance, position: str) -> None:
        """Remove team from specified alliance position."""
        if position == "first_pick":
            alliance.first_pick_team_number = 0
        elif position == "second_pick":
            alliance.second_pick_team_number = 0
        elif position == "backup":
            alliance.backup_team_number = 0
        
        self.db.commit()

    def update_team_status(self, team_status: TeamSelectionStatus, **kwargs) -> None:
        """Update team status with provided fields."""
        for field, value in kwargs.items():
            if hasattr(team_status, field):
                setattr(team_status, field, value)
        
        self.db.commit()