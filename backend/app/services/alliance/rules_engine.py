# backend/app/services/alliance/rules_engine.py
"""
FRC Alliance Selection Rules Engine

This module implements the official FRC alliance selection rules validation.
It ensures all team actions and selection state transitions comply with
official FIRST Robotics Competition rules.

Key Rules Implemented:
1. Alliance captains are selected first (top 8 seeded teams)
2. Teams can only be on one alliance
3. Teams that decline can still become captains later
4. Captains cannot be removed once selected
5. Selection proceeds through rounds (Round 1: First picks, Round 2: Second picks, etc.)
6. Teams are eliminated from future selection after being picked or declining
"""

from typing import List, Optional, Tuple
import logging

from app.database.models import AllianceSelection, Alliance, TeamSelectionStatus
from .models import TeamAvailabilityResult, AllianceValidationResult
from .exceptions import (
    InvalidActionError,
    InvalidRoundError,
    AllianceAlreadyCompleteError,
    TeamAlreadySelectedError,
    CaptainRemovalError,
    InvalidAllianceNumberError,
)

logger = logging.getLogger(__name__)


class AllianceRulesEngine:
    """Implements FRC alliance selection rules validation."""

    @staticmethod
    def validate_alliance_number(alliance_number: Optional[int]) -> None:
        """
        Validate alliance number is within valid range (1-8).
        
        Args:
            alliance_number: Alliance number to validate
            
        Raises:
            InvalidAllianceNumberError: If alliance number is invalid
        """
        if alliance_number is None:
            raise InvalidAllianceNumberError(0)
        
        if alliance_number < 1 or alliance_number > 8:
            raise InvalidAllianceNumberError(alliance_number)

    @staticmethod
    def validate_team_availability(
        team_status: TeamSelectionStatus,
        action: str,
        current_round: int
    ) -> TeamAvailabilityResult:
        """
        Check if a team is available for the requested action.
        
        Args:
            team_status: Current team status from database
            action: Requested action ('captain', 'accept', 'decline', 'remove')
            current_round: Current selection round
            
        Returns:
            TeamAvailabilityResult with availability status and reason
        """
        team_number = team_status.team_number
        
        # For captain action - teams that declined can still become captains
        if action == "captain":
            if team_status.is_captain:
                return TeamAvailabilityResult(
                    team_number=team_number,
                    is_available=False,
                    reason="Team is already a captain",
                    current_status="captain"
                )
            if team_status.is_picked:
                return TeamAvailabilityResult(
                    team_number=team_number,
                    is_available=False,
                    reason="Team has already been picked",
                    current_status="picked"
                )
            # Teams that declined can become captains - this is allowed by FRC rules
            return TeamAvailabilityResult(team_number=team_number, is_available=True)
        
        # For accept/decline actions
        if action in ["accept", "decline"]:
            if team_status.is_captain:
                return TeamAvailabilityResult(
                    team_number=team_number,
                    is_available=False,
                    reason="Team is already a captain",
                    current_status="captain"
                )
            if team_status.is_picked:
                return TeamAvailabilityResult(
                    team_number=team_number,
                    is_available=False,
                    reason="Team has already been picked",
                    current_status="picked"
                )
            if team_status.has_declined:
                return TeamAvailabilityResult(
                    team_number=team_number,
                    is_available=False,
                    reason="Team has already declined",
                    current_status="declined"
                )
            return TeamAvailabilityResult(team_number=team_number, is_available=True)
        
        # For remove action - team must be currently selected
        if action == "remove":
            if not team_status.is_picked and not team_status.is_captain:
                return TeamAvailabilityResult(
                    team_number=team_number,
                    is_available=False,
                    reason="Team is not currently selected",
                    current_status="available"
                )
            return TeamAvailabilityResult(team_number=team_number, is_available=True)
        
        return TeamAvailabilityResult(
            team_number=team_number,
            is_available=False,
            reason=f"Unknown action: {action}"
        )

    @staticmethod
    def validate_captain_assignment(
        alliance: Alliance,
        team_number: int
    ) -> AllianceValidationResult:
        """
        Validate that a team can be assigned as captain to an alliance.
        
        Args:
            alliance: Target alliance
            team_number: Team to assign as captain
            
        Returns:
            AllianceValidationResult with validation status and any errors
        """
        errors = []
        
        if alliance.captain_team_number != 0:
            errors.append(f"Alliance {alliance.alliance_number} already has a captain")
        
        if errors:
            return AllianceValidationResult(is_valid=False, errors=errors)
        
        return AllianceValidationResult(is_valid=True)

    @staticmethod
    def validate_team_pick(
        alliance: Alliance,
        team_number: int,
        current_round: int
    ) -> Tuple[AllianceValidationResult, Optional[str]]:
        """
        Validate that a team can be picked by an alliance and determine position.
        
        Args:
            alliance: Target alliance
            team_number: Team to pick
            current_round: Current selection round
            
        Returns:
            Tuple of (validation_result, position) where position is the team's role
        """
        errors = []
        position = None
        
        # Check if alliance has a captain
        if alliance.captain_team_number == 0:
            errors.append(f"Alliance {alliance.alliance_number} doesn't have a captain yet")
        
        # Determine position based on current round and alliance state
        if current_round == 1 and alliance.first_pick_team_number == 0:
            position = "first_pick"
        elif (
            current_round == 2 or (current_round == 1 and alliance.first_pick_team_number != 0)
        ) and alliance.second_pick_team_number == 0:
            position = "second_pick"
        elif current_round == 3 and (
            alliance.backup_team_number == 0 or alliance.backup_team_number is None
        ):
            position = "backup"
        else:
            errors.append(f"Alliance {alliance.alliance_number} already has all picks for current round")
        
        if errors:
            return AllianceValidationResult(is_valid=False, errors=errors), None
        
        return AllianceValidationResult(is_valid=True), position

    @staticmethod
    def validate_team_removal(
        alliance: Alliance,
        team_number: int
    ) -> Tuple[AllianceValidationResult, Optional[str]]:
        """
        Validate that a team can be removed from an alliance and determine position.
        
        Args:
            alliance: Target alliance
            team_number: Team to remove
            
        Returns:
            Tuple of (validation_result, position) where position is the team's current role
        """
        errors = []
        position = None
        
        # Check if team is captain (cannot be removed)
        if alliance.captain_team_number == team_number:
            errors.append("Cannot remove alliance captain. Please start a new alliance selection if needed.")
        elif alliance.first_pick_team_number == team_number:
            position = "first_pick"
        elif alliance.second_pick_team_number == team_number:
            position = "second_pick"
        elif alliance.backup_team_number == team_number:
            position = "backup"
        else:
            errors.append(f"Team {team_number} is not part of alliance {alliance.alliance_number}")
        
        if errors:
            return AllianceValidationResult(is_valid=False, errors=errors), None
        
        return AllianceValidationResult(is_valid=True), position

    @staticmethod
    def validate_round_advancement(
        selection: AllianceSelection,
        alliances: List[Alliance]
    ) -> AllianceValidationResult:
        """
        Validate that the selection can advance to the next round.
        
        Args:
            selection: Current alliance selection
            alliances: List of all alliances in the selection
            
        Returns:
            AllianceValidationResult with validation status and any warnings
        """
        warnings = []
        current_round = selection.current_round
        
        # Check if all alliances have the required picks for current round
        incomplete_alliances = []
        
        for alliance in alliances:
            if alliance.captain_team_number == 0:
                incomplete_alliances.append(f"Alliance {alliance.alliance_number} has no captain")
            elif current_round == 1 and alliance.first_pick_team_number == 0:
                incomplete_alliances.append(f"Alliance {alliance.alliance_number} has no first pick")
            elif current_round == 2 and alliance.second_pick_team_number == 0:
                incomplete_alliances.append(f"Alliance {alliance.alliance_number} has no second pick")
        
        if incomplete_alliances:
            warnings.extend(incomplete_alliances)
            warnings.append("Some alliances are incomplete. You can still advance if this is intentional.")
        
        return AllianceValidationResult(is_valid=True, warnings=warnings)

    @staticmethod
    def get_selection_completion_status(
        selection: AllianceSelection,
        alliances: List[Alliance]
    ) -> Tuple[bool, List[str]]:
        """
        Determine if the alliance selection is complete.
        
        Args:
            selection: Current alliance selection
            alliances: List of all alliances in the selection
            
        Returns:
            Tuple of (is_complete, reasons) explaining completion status
        """
        reasons = []
        
        # Check if we're past round 3 (backup selection)
        if selection.current_round > 3:
            reasons.append(f"Selection has advanced past round 3 (current round: {selection.current_round})")
            return True, reasons
        
        # Check if all alliances have captains and at least first picks
        incomplete_count = 0
        for alliance in alliances:
            if alliance.captain_team_number == 0 or alliance.first_pick_team_number == 0:
                incomplete_count += 1
        
        if incomplete_count == 0:
            reasons.append("All alliances have captains and first picks")
            # Could be considered complete, but typically continues to second picks
        
        return False, reasons