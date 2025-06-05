# backend/app/api/alliance_selection.py
"""
Alliance Selection API Module

This module contains the FastAPI endpoints for managing the alliance selection process.
The alliance selection process follows the official FRC alliance selection rules:

1. Teams go through multiple rounds of selection:
   - Round 1: Alliance captains and first picks
   - Round 2: Second picks
   - Round 3: Backup robots (for World Championship events)

2. Database Models (defined in app.database.models):
   - LockedPicklist: Stores the finalized picklist data with rankings
   - AllianceSelection: Represents a full alliance selection process
   - Alliance: Represents one of the 8 alliances with their team members
   - TeamSelectionStatus: Tracks the status of each team during selection

3. Key Features:
   - Lock/unlock picklists to prevent further editing
   - Track team status (captain, picked, declined)
   - Allow teams that declined to become captains later (per FRC rules)
   - Support multiple rounds of selection
   - Print alliance selections

Endpoints include locking/unlocking picklists, creating alliance selections,
recording team actions, and advancing through selection rounds.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import logging

from app.database.db import get_db
from app.database.models import LockedPicklist, AllianceSelection, Alliance, TeamSelectionStatus

# Configure logging
logger = logging.getLogger("alliance_selection")

router = APIRouter(prefix="/api/alliance", tags=["Alliance Selection"])


# Pydantic models for request/response
class PicklistData(BaseModel):
    teams: List[Dict[str, Any]]
    analysis: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class LockPicklistRequest(BaseModel):
    team_number: int
    event_key: str
    year: int
    first_pick_data: PicklistData
    second_pick_data: PicklistData
    third_pick_data: Optional[PicklistData] = None
    excluded_teams: Optional[List[int]] = None
    strategy_prompts: Optional[Dict[str, str]] = None


class LockedPicklistResponse(BaseModel):
    id: int
    team_number: int
    event_key: str
    year: int
    created_at: str


@router.post("/lock-picklist", response_model=LockedPicklistResponse)
async def lock_picklist(request: LockPicklistRequest, db: Session = Depends(get_db)):
    """
    Lock a picklist and save it to the database
    """
    try:
        # Check if a locked picklist already exists for this team/event
        existing_picklist = (
            db.query(LockedPicklist)
            .filter(
                LockedPicklist.team_number == request.team_number,
                LockedPicklist.event_key == request.event_key,
                LockedPicklist.year == request.year,
            )
            .first()
        )

        if existing_picklist:
            # Update existing picklist
            existing_picklist.first_pick_data = request.first_pick_data.dict()
            existing_picklist.second_pick_data = request.second_pick_data.dict()
            if request.third_pick_data:
                existing_picklist.third_pick_data = request.third_pick_data.dict()

            # Update additional metadata
            if request.excluded_teams is not None:
                existing_picklist.excluded_teams = request.excluded_teams
            if request.strategy_prompts is not None:
                existing_picklist.strategy_prompts = request.strategy_prompts

            db.commit()
            db.refresh(existing_picklist)

            return {
                "id": existing_picklist.id,
                "team_number": existing_picklist.team_number,
                "event_key": existing_picklist.event_key,
                "year": existing_picklist.year,
                "created_at": existing_picklist.created_at.isoformat(),
            }
        else:
            # Create new picklist
            new_picklist = LockedPicklist(
                team_number=request.team_number,
                event_key=request.event_key,
                year=request.year,
                first_pick_data=request.first_pick_data.dict(),
                second_pick_data=request.second_pick_data.dict(),
                third_pick_data=request.third_pick_data.dict() if request.third_pick_data else None,
                excluded_teams=request.excluded_teams,
                strategy_prompts=request.strategy_prompts,
            )

            db.add(new_picklist)
            db.commit()
            db.refresh(new_picklist)

            return {
                "id": new_picklist.id,
                "team_number": new_picklist.team_number,
                "event_key": new_picklist.event_key,
                "year": new_picklist.year,
                "created_at": new_picklist.created_at.isoformat(),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error locking picklist: {str(e)}")


@router.get("/picklists")
async def get_picklists(
    team_number: Optional[int] = None,
    event_key: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get all locked picklists, optionally filtered by team number or event key
    """
    try:
        query = db.query(LockedPicklist)

        if team_number:
            query = query.filter(LockedPicklist.team_number == team_number)

        if event_key:
            query = query.filter(LockedPicklist.event_key == event_key)

        picklists = query.all()

        return {
            "status": "success",
            "picklists": [
                {
                    "id": p.id,
                    "team_number": p.team_number,
                    "event_key": p.event_key,
                    "year": p.year,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
                for p in picklists
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving picklists: {str(e)}")


@router.get("/picklist/{picklist_id}")
async def get_picklist(picklist_id: int, db: Session = Depends(get_db)):
    """
    Get a specific locked picklist by ID
    """
    try:
        picklist = db.query(LockedPicklist).filter(LockedPicklist.id == picklist_id).first()

        if not picklist:
            raise HTTPException(status_code=404, detail="Picklist not found")

        return {
            "status": "success",
            "picklist": {
                "id": picklist.id,
                "team_number": picklist.team_number,
                "event_key": picklist.event_key,
                "year": picklist.year,
                "first_pick_data": picklist.first_pick_data,
                "second_pick_data": picklist.second_pick_data,
                "third_pick_data": picklist.third_pick_data,
                "created_at": picklist.created_at.isoformat(),
                "updated_at": picklist.updated_at.isoformat() if picklist.updated_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving picklist: {str(e)}")


@router.delete("/picklist/{picklist_id}")
async def unlock_picklist(picklist_id: int, db: Session = Depends(get_db)):
    """
    Unlock a picklist by deleting it
    """
    try:
        # Check if picklist exists
        picklist = db.query(LockedPicklist).filter(LockedPicklist.id == picklist_id).first()
        if not picklist:
            raise HTTPException(status_code=404, detail="Picklist not found")

        # Check if this picklist is being used in any alliance selections
        selections = (
            db.query(AllianceSelection).filter(AllianceSelection.picklist_id == picklist_id).all()
        )

        # If there are alliance selections using this picklist, detach them
        for selection in selections:
            selection.picklist_id = None

        # Delete the picklist
        db.delete(picklist)
        db.commit()

        return {"status": "success", "message": "Picklist successfully unlocked and deleted"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlocking picklist: {str(e)}")


# Alliance Selection Models
class CreateAllianceSelectionRequest(BaseModel):
    picklist_id: Optional[int] = None
    event_key: str
    year: int
    team_list: List[int]  # List of all team numbers at the event


class AllianceSelectionResponse(BaseModel):
    id: int
    event_key: str
    year: int
    is_completed: bool
    current_round: int


class TeamStatus(BaseModel):
    team_number: int
    is_captain: bool
    is_picked: bool
    has_declined: bool
    round_eliminated: Optional[int] = None


class AllianceData(BaseModel):
    alliance_number: int
    captain_team_number: int = 0
    first_pick_team_number: int = 0
    second_pick_team_number: int = 0
    backup_team_number: Optional[int] = 0


class TeamActionRequest(BaseModel):
    selection_id: int
    team_number: int
    action: str = Field(..., description="Action: 'captain', 'accept', 'decline', 'remove'")
    alliance_number: Optional[int] = None  # Required for 'captain', 'accept', and 'remove' actions


@router.post("/selection/create", response_model=AllianceSelectionResponse)
async def create_alliance_selection(
    request: CreateAllianceSelectionRequest, db: Session = Depends(get_db)
):
    """
    Create a new alliance selection process
    """
    try:
        # If a picklist ID is provided, verify it exists
        if request.picklist_id is not None:
            picklist = (
                db.query(LockedPicklist).filter(LockedPicklist.id == request.picklist_id).first()
            )
            if not picklist:
                raise HTTPException(status_code=404, detail="Picklist not found")

            # Check if a selection process already exists for this picklist
            existing = (
                db.query(AllianceSelection)
                .filter(AllianceSelection.picklist_id == request.picklist_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=400, detail="Alliance selection already exists for this picklist"
                )

        # Create new alliance selection
        selection = AllianceSelection(
            picklist_id=request.picklist_id,  # This can be None
            event_key=request.event_key,
            year=request.year,
            is_completed=False,
            current_round=1,
        )

        db.add(selection)
        db.commit()
        db.refresh(selection)

        # Create alliances (1-8)
        for i in range(1, 9):
            alliance = Alliance(selection_id=selection.id, alliance_number=i)
            db.add(alliance)

        # Initialize team statuses
        for team_number in request.team_list:
            team_status = TeamSelectionStatus(
                selection_id=selection.id,
                team_number=team_number,
                is_captain=False,
                is_picked=False,
                has_declined=False,
            )
            db.add(team_status)

        db.commit()

        return {
            "id": selection.id,
            "event_key": selection.event_key,
            "year": selection.year,
            "is_completed": selection.is_completed,
            "current_round": selection.current_round,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating alliance selection: {str(e)}")


@router.get("/selection/{selection_id}")
async def get_alliance_selection(selection_id: int, db: Session = Depends(get_db)):
    """
    Get the current state of an alliance selection
    """
    try:
        # Get the selection
        selection = db.query(AllianceSelection).filter(AllianceSelection.id == selection_id).first()
        if not selection:
            raise HTTPException(status_code=404, detail="Alliance selection not found")

        # Get alliances
        alliances = db.query(Alliance).filter(Alliance.selection_id == selection_id).all()

        # Get team statuses
        team_statuses = (
            db.query(TeamSelectionStatus)
            .filter(TeamSelectionStatus.selection_id == selection_id)
            .all()
        )

        # Format the response
        return {
            "status": "success",
            "selection": {
                "id": selection.id,
                "event_key": selection.event_key,
                "year": selection.year,
                "is_completed": selection.is_completed,
                "current_round": selection.current_round,
                "picklist_id": selection.picklist_id,  # Include picklist_id in the response
                "alliances": [
                    {
                        "alliance_number": a.alliance_number,
                        "captain_team_number": a.captain_team_number,
                        "first_pick_team_number": a.first_pick_team_number,
                        "second_pick_team_number": a.second_pick_team_number,
                        "backup_team_number": a.backup_team_number,
                    }
                    for a in sorted(alliances, key=lambda x: x.alliance_number)
                ],
                "team_statuses": [
                    {
                        "team_number": ts.team_number,
                        "is_captain": ts.is_captain,
                        "is_picked": ts.is_picked,
                        "has_declined": ts.has_declined,
                        "round_eliminated": ts.round_eliminated,
                    }
                    for ts in sorted(team_statuses, key=lambda x: x.team_number)
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving alliance selection: {str(e)}"
        )


@router.post("/selection/team-action")
async def team_action(request: TeamActionRequest, db: Session = Depends(get_db)):
    """
    Perform an action on a team during alliance selection
    """
    try:
        # Get the selection
        selection = (
            db.query(AllianceSelection).filter(AllianceSelection.id == request.selection_id).first()
        )
        if not selection:
            raise HTTPException(status_code=404, detail="Alliance selection not found")

        # Check if selection is completed
        if selection.is_completed:
            raise HTTPException(status_code=400, detail="Alliance selection is already completed")

        # Get the team status
        team_status = (
            db.query(TeamSelectionStatus)
            .filter(
                TeamSelectionStatus.selection_id == request.selection_id,
                TeamSelectionStatus.team_number == request.team_number,
            )
            .first()
        )

        if not team_status:
            raise HTTPException(status_code=404, detail="Team not found in this selection")

        # Process the action
        if request.action == "captain":
            # Make team the captain of alliance
            if team_status.is_captain or team_status.is_picked:
                raise HTTPException(
                    status_code=400, detail="Team is already a captain or has been picked"
                )

            # Note: We specifically allow a team that has declined to become a captain later
            # This is per FRC alliance selection rules

            if (
                not request.alliance_number
                or request.alliance_number < 1
                or request.alliance_number > 8
            ):
                raise HTTPException(status_code=400, detail="Invalid alliance number")

            # Get the alliance
            alliance = (
                db.query(Alliance)
                .filter(
                    Alliance.selection_id == request.selection_id,
                    Alliance.alliance_number == request.alliance_number,
                )
                .first()
            )

            if not alliance:
                raise HTTPException(status_code=404, detail="Alliance not found")

            if alliance.captain_team_number != 0:
                raise HTTPException(status_code=400, detail="Alliance already has a captain")

            # Update the alliance
            alliance.captain_team_number = request.team_number

            # Update the team status
            team_status.is_captain = True

            db.commit()

            return {"status": "success", "action": "captain", "team_number": request.team_number}

        elif request.action == "accept":
            # Team accepts being picked by an alliance
            if team_status.is_captain or team_status.is_picked or team_status.has_declined:
                raise HTTPException(
                    status_code=400,
                    detail="Team is already a captain, has been picked, or has declined",
                )

            if (
                not request.alliance_number
                or request.alliance_number < 1
                or request.alliance_number > 8
            ):
                raise HTTPException(status_code=400, detail="Invalid alliance number")

            # Get the alliance
            alliance = (
                db.query(Alliance)
                .filter(
                    Alliance.selection_id == request.selection_id,
                    Alliance.alliance_number == request.alliance_number,
                )
                .first()
            )

            if not alliance:
                raise HTTPException(status_code=404, detail="Alliance not found")

            # Check captain exists
            if alliance.captain_team_number == 0:
                raise HTTPException(status_code=400, detail="Alliance doesn't have a captain yet")

            # Determine whether this is first pick, second pick, or backup
            current_round = selection.current_round

            if current_round == 1 and alliance.first_pick_team_number == 0:
                alliance.first_pick_team_number = request.team_number
            elif (
                current_round == 2 or (current_round == 1 and alliance.first_pick_team_number != 0)
            ) and alliance.second_pick_team_number == 0:
                alliance.second_pick_team_number = request.team_number
            elif current_round == 3 and (
                alliance.backup_team_number == 0 or alliance.backup_team_number is None
            ):
                alliance.backup_team_number = request.team_number
            else:
                raise HTTPException(
                    status_code=400, detail="Alliance already has all picks for current round"
                )

            # Update the team status
            team_status.is_picked = True

            db.commit()

            return {"status": "success", "action": "accept", "team_number": request.team_number}

        elif request.action == "decline":
            # Team declines being picked
            if team_status.is_captain or team_status.is_picked or team_status.has_declined:
                raise HTTPException(
                    status_code=400,
                    detail="Team is already a captain, has been picked, or has declined",
                )

            # Update the team status
            team_status.has_declined = True

            db.commit()

            return {"status": "success", "action": "decline", "team_number": request.team_number}

        elif request.action == "remove":
            # Remove a team from an alliance
            if (
                not request.alliance_number
                or request.alliance_number < 1
                or request.alliance_number > 8
            ):
                raise HTTPException(status_code=400, detail="Invalid alliance number")

            # Get the alliance
            alliance = (
                db.query(Alliance)
                .filter(
                    Alliance.selection_id == request.selection_id,
                    Alliance.alliance_number == request.alliance_number,
                )
                .first()
            )

            if not alliance:
                raise HTTPException(status_code=404, detail="Alliance not found")

            # Check if the team is part of this alliance
            removed = False
            position = ""

            if alliance.captain_team_number == request.team_number:
                # Can't remove a captain - that would break the alliance
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove alliance captain. Please start a new alliance selection if needed.",
                )

            elif alliance.first_pick_team_number == request.team_number:
                alliance.first_pick_team_number = 0
                removed = True
                position = "first pick"

            elif alliance.second_pick_team_number == request.team_number:
                alliance.second_pick_team_number = 0
                removed = True
                position = "second pick"

            elif alliance.backup_team_number == request.team_number:
                alliance.backup_team_number = 0
                removed = True
                position = "backup"

            if not removed:
                raise HTTPException(
                    status_code=404,
                    detail=f"Team {request.team_number} is not part of alliance {request.alliance_number}",
                )

            # Update the team status to make it selectable again
            team_status.is_picked = False
            team_status.round_eliminated = None  # Clear elimination round to make team available

            db.commit()

            logger.info(
                f"Removed team {request.team_number} as {position} from alliance {request.alliance_number}"
            )

            return {
                "status": "success",
                "action": "remove",
                "team_number": request.team_number,
                "alliance_number": request.alliance_number,
                "position": position,
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error performing team action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing team action: {str(e)}")


@router.post("/selection/{selection_id}/next-round")
async def advance_to_next_round(selection_id: int, db: Session = Depends(get_db)):
    """
    Advance the alliance selection to the next round
    """
    try:
        # Get the selection
        selection = db.query(AllianceSelection).filter(AllianceSelection.id == selection_id).first()
        if not selection:
            raise HTTPException(status_code=404, detail="Alliance selection not found")

        # Check if selection is completed
        if selection.is_completed:
            raise HTTPException(status_code=400, detail="Alliance selection is already completed")

        # Check current round
        current_round = selection.current_round

        if current_round >= 3:
            # If we're in round 3 or higher (sometimes might go to 4 for extra backups)
            # and advancing, mark as completed
            selection.is_completed = True
            db.commit()
            return {
                "status": "success",
                "action": "completed",
                "selection_id": selection_id,
                "message": "Alliance selection completed successfully!",
            }

        # Mark all captains and picked teams as eliminated for this round
        # This prevents them from being selected in future rounds
        team_statuses = (
            db.query(TeamSelectionStatus)
            .filter(
                TeamSelectionStatus.selection_id == selection_id,
                TeamSelectionStatus.is_captain == True,  # All captains
            )
            .all()
        )

        for ts in team_statuses:
            if not ts.round_eliminated:  # Only update if not already eliminated
                ts.round_eliminated = current_round

        team_statuses = (
            db.query(TeamSelectionStatus)
            .filter(
                TeamSelectionStatus.selection_id == selection_id,
                TeamSelectionStatus.is_picked == True,  # All picked teams
            )
            .all()
        )

        for ts in team_statuses:
            if not ts.round_eliminated:  # Only update if not already eliminated
                ts.round_eliminated = current_round

        # Advance to next round
        selection.current_round += 1

        db.commit()

        return {
            "status": "success",
            "action": "next_round",
            "selection_id": selection_id,
            "new_round": selection.current_round,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error advancing to next round: {str(e)}")


@router.post("/selection/{selection_id}/reset")
async def reset_alliance_selection(selection_id: int, db: Session = Depends(get_db)):
    """
    Reset an alliance selection back to the beginning.
    This will:
    1. Reset all alliances (clear captain and picks)
    2. Reset all team statuses (clear captain, picked, declined status)
    3. Reset the selection itself (current_round to 1, is_completed to False)
    """
    try:
        # Get the selection
        selection = db.query(AllianceSelection).filter(AllianceSelection.id == selection_id).first()

        if not selection:
            raise HTTPException(status_code=404, detail="Alliance selection not found")

        # Reset all alliances
        alliances = db.query(Alliance).filter(Alliance.selection_id == selection_id).all()
        for alliance in alliances:
            alliance.captain_team_number = 0
            alliance.first_pick_team_number = 0
            alliance.second_pick_team_number = 0
            alliance.backup_team_number = 0

        # Reset all team statuses
        team_statuses = (
            db.query(TeamSelectionStatus)
            .filter(TeamSelectionStatus.selection_id == selection_id)
            .all()
        )
        for ts in team_statuses:
            ts.is_captain = False
            ts.is_picked = False
            ts.has_declined = False
            ts.round_eliminated = None

        # Reset the selection itself
        selection.current_round = 1
        selection.is_completed = False

        db.commit()

        return {
            "status": "success",
            "action": "reset",
            "selection_id": selection_id,
            "message": "Alliance selection has been reset to the beginning",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting alliance selection: {str(e)}")
