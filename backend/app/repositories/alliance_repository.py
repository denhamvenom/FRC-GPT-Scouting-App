# backend/app/repositories/alliance_repository.py
"""
Alliance Repository

Specialized repository for alliance selection models (AllianceSelection, Alliance, TeamSelectionStatus)
with domain-specific queries for alliance management operations.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, or_
import logging

from app.database.models import AllianceSelection, Alliance, TeamSelectionStatus
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AllianceRepository(BaseRepository[AllianceSelection]):
    """Repository for alliance selection operations with specialized queries."""

    def __init__(self, db: Session):
        super().__init__(AllianceSelection, db)

    def get_domain_specific_methods(self) -> Dict[str, Any]:
        """Return domain-specific methods for alliance operations."""
        return {
            'get_by_event': self.get_by_event,
            'get_active_selection': self.get_active_selection,
            'get_with_details': self.get_with_details,
            'get_team_status': self.get_team_status,
            'update_team_status': self.update_team_status,
            'get_alliance_by_number': self.get_alliance_by_number,
            'update_alliance': self.update_alliance,
            'get_available_teams': self.get_available_teams,
            'get_captains': self.get_captains,
            'get_picked_teams': self.get_picked_teams,
            'get_declined_teams': self.get_declined_teams,
            'is_team_available': self.is_team_available,
            'complete_selection': self.complete_selection,
            'reset_selection': self.reset_selection,
            'get_selection_summary': self.get_selection_summary,
        }

    def get_by_event(self, event_key: str, year: Optional[int] = None) -> List[AllianceSelection]:
        """
        Get all alliance selections for a specific event.
        
        Args:
            event_key: Event key
            year: Optional year filter
            
        Returns:
            List of AllianceSelection instances
        """
        try:
            query = self.db.query(AllianceSelection).filter(
                AllianceSelection.event_key == event_key
            )
            
            if year:
                query = query.filter(AllianceSelection.year == year)
            
            return query.options(
                joinedload(AllianceSelection.alliances),
                joinedload(AllianceSelection.team_statuses)
            ).order_by(desc(AllianceSelection.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting alliance selections for event {event_key}: {e}")
            raise

    def get_active_selection(self, event_key: str, year: Optional[int] = None) -> Optional[AllianceSelection]:
        """
        Get the active (incomplete) alliance selection for an event.
        
        Args:
            event_key: Event key
            year: Optional year filter
            
        Returns:
            Active AllianceSelection instance or None
        """
        try:
            query = self.db.query(AllianceSelection).filter(
                and_(
                    AllianceSelection.event_key == event_key,
                    AllianceSelection.is_completed == False
                )
            )
            
            if year:
                query = query.filter(AllianceSelection.year == year)
            
            return query.options(
                joinedload(AllianceSelection.alliances),
                joinedload(AllianceSelection.team_statuses)
            ).first()
        except Exception as e:
            logger.error(f"Error getting active alliance selection for event {event_key}: {e}")
            raise

    def get_with_details(self, selection_id: int) -> Optional[AllianceSelection]:
        """
        Get alliance selection with all related data.
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            AllianceSelection with loaded relationships or None
        """
        try:
            return self.db.query(AllianceSelection).filter(
                AllianceSelection.id == selection_id
            ).options(
                joinedload(AllianceSelection.alliances),
                joinedload(AllianceSelection.team_statuses),
                joinedload(AllianceSelection.picklist)
            ).first()
        except Exception as e:
            logger.error(f"Error getting alliance selection details for ID {selection_id}: {e}")
            raise

    def get_team_status(self, selection_id: int, team_number: int) -> Optional[TeamSelectionStatus]:
        """
        Get team status for a specific selection.
        
        Args:
            selection_id: Alliance selection ID
            team_number: Team number
            
        Returns:
            TeamSelectionStatus instance or None
        """
        try:
            return self.db.query(TeamSelectionStatus).filter(
                and_(
                    TeamSelectionStatus.selection_id == selection_id,
                    TeamSelectionStatus.team_number == team_number
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting team status for team {team_number} in selection {selection_id}: {e}")
            raise

    def update_team_status(
        self,
        selection_id: int,
        team_number: int,
        is_captain: Optional[bool] = None,
        is_picked: Optional[bool] = None,
        has_declined: Optional[bool] = None,
        round_eliminated: Optional[int] = None
    ) -> TeamSelectionStatus:
        """
        Update or create team status.
        
        Args:
            selection_id: Alliance selection ID
            team_number: Team number
            is_captain: Whether team is a captain
            is_picked: Whether team is picked
            has_declined: Whether team has declined
            round_eliminated: Round team was eliminated
            
        Returns:
            Updated TeamSelectionStatus instance
        """
        try:
            status = self.get_team_status(selection_id, team_number)
            
            if not status:
                # Create new status
                status = TeamSelectionStatus(
                    selection_id=selection_id,
                    team_number=team_number,
                    is_captain=is_captain or False,
                    is_picked=is_picked or False,
                    has_declined=has_declined or False,
                    round_eliminated=round_eliminated
                )
                self.db.add(status)
            else:
                # Update existing status
                if is_captain is not None:
                    status.is_captain = is_captain
                if is_picked is not None:
                    status.is_picked = is_picked
                if has_declined is not None:
                    status.has_declined = has_declined
                if round_eliminated is not None:
                    status.round_eliminated = round_eliminated
            
            self.db.flush()
            self.db.refresh(status)
            return status
        except Exception as e:
            logger.error(f"Error updating team status for team {team_number}: {e}")
            self.db.rollback()
            raise

    def get_alliance_by_number(self, selection_id: int, alliance_number: int) -> Optional[Alliance]:
        """
        Get alliance by its number in a selection.
        
        Args:
            selection_id: Alliance selection ID
            alliance_number: Alliance number (1-8)
            
        Returns:
            Alliance instance or None
        """
        try:
            return self.db.query(Alliance).filter(
                and_(
                    Alliance.selection_id == selection_id,
                    Alliance.alliance_number == alliance_number
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting alliance {alliance_number} from selection {selection_id}: {e}")
            raise

    def update_alliance(
        self,
        selection_id: int,
        alliance_number: int,
        captain_team_number: Optional[int] = None,
        first_pick_team_number: Optional[int] = None,
        second_pick_team_number: Optional[int] = None,
        backup_team_number: Optional[int] = None
    ) -> Alliance:
        """
        Update or create alliance.
        
        Args:
            selection_id: Alliance selection ID
            alliance_number: Alliance number (1-8)
            captain_team_number: Captain team number
            first_pick_team_number: First pick team number
            second_pick_team_number: Second pick team number
            backup_team_number: Backup team number
            
        Returns:
            Updated Alliance instance
        """
        try:
            alliance = self.get_alliance_by_number(selection_id, alliance_number)
            
            if not alliance:
                # Create new alliance
                alliance = Alliance(
                    selection_id=selection_id,
                    alliance_number=alliance_number,
                    captain_team_number=captain_team_number or 0,
                    first_pick_team_number=first_pick_team_number or 0,
                    second_pick_team_number=second_pick_team_number or 0,
                    backup_team_number=backup_team_number or 0
                )
                self.db.add(alliance)
            else:
                # Update existing alliance
                if captain_team_number is not None:
                    alliance.captain_team_number = captain_team_number
                if first_pick_team_number is not None:
                    alliance.first_pick_team_number = first_pick_team_number
                if second_pick_team_number is not None:
                    alliance.second_pick_team_number = second_pick_team_number
                if backup_team_number is not None:
                    alliance.backup_team_number = backup_team_number
            
            self.db.flush()
            self.db.refresh(alliance)
            return alliance
        except Exception as e:
            logger.error(f"Error updating alliance {alliance_number}: {e}")
            self.db.rollback()
            raise

    def get_available_teams(self, selection_id: int) -> List[int]:
        """
        Get list of available teams (not captains, picked, or declined).
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            List of available team numbers
        """
        try:
            unavailable_teams = self.db.query(TeamSelectionStatus.team_number).filter(
                and_(
                    TeamSelectionStatus.selection_id == selection_id,
                    or_(
                        TeamSelectionStatus.is_captain == True,
                        TeamSelectionStatus.is_picked == True,
                        TeamSelectionStatus.has_declined == True
                    )
                )
            ).all()
            
            unavailable_team_numbers = [team[0] for team in unavailable_teams]
            
            # Return all teams that have status records but are available
            all_teams = self.db.query(TeamSelectionStatus.team_number).filter(
                TeamSelectionStatus.selection_id == selection_id
            ).all()
            
            all_team_numbers = [team[0] for team in all_teams]
            available_teams = [team for team in all_team_numbers if team not in unavailable_team_numbers]
            
            return available_teams
        except Exception as e:
            logger.error(f"Error getting available teams for selection {selection_id}: {e}")
            raise

    def get_captains(self, selection_id: int) -> List[int]:
        """
        Get list of captain team numbers.
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            List of captain team numbers
        """
        try:
            captains = self.db.query(TeamSelectionStatus.team_number).filter(
                and_(
                    TeamSelectionStatus.selection_id == selection_id,
                    TeamSelectionStatus.is_captain == True
                )
            ).all()
            
            return [captain[0] for captain in captains]
        except Exception as e:
            logger.error(f"Error getting captains for selection {selection_id}: {e}")
            raise

    def get_picked_teams(self, selection_id: int) -> List[int]:
        """
        Get list of picked team numbers.
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            List of picked team numbers
        """
        try:
            picked = self.db.query(TeamSelectionStatus.team_number).filter(
                and_(
                    TeamSelectionStatus.selection_id == selection_id,
                    TeamSelectionStatus.is_picked == True
                )
            ).all()
            
            return [team[0] for team in picked]
        except Exception as e:
            logger.error(f"Error getting picked teams for selection {selection_id}: {e}")
            raise

    def get_declined_teams(self, selection_id: int) -> List[int]:
        """
        Get list of declined team numbers.
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            List of declined team numbers
        """
        try:
            declined = self.db.query(TeamSelectionStatus.team_number).filter(
                and_(
                    TeamSelectionStatus.selection_id == selection_id,
                    TeamSelectionStatus.has_declined == True
                )
            ).all()
            
            return [team[0] for team in declined]
        except Exception as e:
            logger.error(f"Error getting declined teams for selection {selection_id}: {e}")
            raise

    def is_team_available(self, selection_id: int, team_number: int) -> bool:
        """
        Check if a team is available for selection.
        
        Args:
            selection_id: Alliance selection ID
            team_number: Team number
            
        Returns:
            True if team is available, False otherwise
        """
        try:
            status = self.get_team_status(selection_id, team_number)
            
            if not status:
                return True  # No status record means available
            
            return not (status.is_captain or status.is_picked or status.has_declined)
        except Exception as e:
            logger.error(f"Error checking availability for team {team_number}: {e}")
            raise

    def complete_selection(self, selection_id: int) -> AllianceSelection:
        """
        Mark an alliance selection as completed.
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            Updated AllianceSelection instance
        """
        try:
            selection = self.get(selection_id)
            if selection:
                selection.is_completed = True
                self.db.flush()
                self.db.refresh(selection)
            return selection
        except Exception as e:
            logger.error(f"Error completing selection {selection_id}: {e}")
            self.db.rollback()
            raise

    def reset_selection(self, selection_id: int) -> bool:
        """
        Reset an alliance selection by clearing all team statuses and alliances.
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            True if reset successful
        """
        try:
            # Clear team statuses
            self.db.query(TeamSelectionStatus).filter(
                TeamSelectionStatus.selection_id == selection_id
            ).delete()
            
            # Clear alliances
            self.db.query(Alliance).filter(
                Alliance.selection_id == selection_id
            ).delete()
            
            # Reset selection status
            selection = self.get(selection_id)
            if selection:
                selection.is_completed = False
                selection.current_round = 1
            
            self.db.flush()
            return True
        except Exception as e:
            logger.error(f"Error resetting selection {selection_id}: {e}")
            self.db.rollback()
            raise

    def get_selection_summary(self, selection_id: int) -> Dict[str, Any]:
        """
        Get comprehensive summary of alliance selection state.
        
        Args:
            selection_id: Alliance selection ID
            
        Returns:
            Dictionary with selection summary
        """
        try:
            selection = self.get_with_details(selection_id)
            if not selection:
                return {}
            
            # Count teams by status
            captains = len(self.get_captains(selection_id))
            picked = len(self.get_picked_teams(selection_id))
            declined = len(self.get_declined_teams(selection_id))
            available = len(self.get_available_teams(selection_id))
            
            # Get alliance details
            alliances = self.db.query(Alliance).filter(
                Alliance.selection_id == selection_id
            ).order_by(Alliance.alliance_number).all()
            
            alliance_summary = []
            for alliance in alliances:
                alliance_summary.append({
                    'number': alliance.alliance_number,
                    'captain': alliance.captain_team_number if alliance.captain_team_number != 0 else None,
                    'first_pick': alliance.first_pick_team_number if alliance.first_pick_team_number != 0 else None,
                    'second_pick': alliance.second_pick_team_number if alliance.second_pick_team_number != 0 else None,
                    'backup': alliance.backup_team_number if alliance.backup_team_number != 0 else None,
                })
            
            return {
                'selection_id': selection_id,
                'event_key': selection.event_key,
                'year': selection.year,
                'is_completed': selection.is_completed,
                'current_round': selection.current_round,
                'team_counts': {
                    'captains': captains,
                    'picked': picked,
                    'declined': declined,
                    'available': available,
                },
                'alliances': alliance_summary,
                'created_at': selection.created_at,
                'updated_at': selection.updated_at,
            }
        except Exception as e:
            logger.error(f"Error getting selection summary for {selection_id}: {e}")
            raise