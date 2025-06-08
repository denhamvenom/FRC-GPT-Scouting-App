# backend/app/api/alliance_selection.py
"""
Alliance Selection API Module

This module contains the FastAPI endpoints for managing the alliance selection process.
The alliance selection process follows the official FRC alliance selection rules.

This module has been refactored to use the new service-oriented architecture,
reducing complexity from 773 lines to a focused API layer that delegates
business logic to dedicated services.

Key Services Used:
- AllianceSelectionService: Main orchestrator for alliance operations
- TeamActionService: Handles team actions (captain, accept, decline, remove)
- AllianceStateManager: Manages selection state and persistence
- AllianceRulesEngine: Validates FRC rules compliance

The refactored architecture provides better separation of concerns, improved
testability, and cleaner error handling.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.database.db import get_db
from app.database.models import LockedPicklist
from app.services.alliance import (
    AllianceSelectionService,
    AllianceSelectionRequest,
    TeamActionRequest,
    AllianceSelectionError,
)
from app.services.alliance.models import (
    LockPicklistRequest,
    LockedPicklistResponse,
)

# Configure logging
logger = logging.getLogger("alliance_selection")

router = APIRouter(prefix="/api/alliance", tags=["Alliance Selection"])


def _get_alliance_service(db: Session) -> AllianceSelectionService:
    """Get alliance selection service instance."""
    return AllianceSelectionService(db)


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


@router.post("/selection/create")
async def create_alliance_selection(
    request: AllianceSelectionRequest, 
    db: Session = Depends(get_db)
):
    """
    Create a new alliance selection process.
    Refactored to use the new service-oriented architecture.
    """
    try:
        service = _get_alliance_service(db)
        response = service.create_alliance_selection(request)
        return response.dict()

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in create_alliance_selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating alliance selection: {str(e)}")


@router.get("/selection/{selection_id}")
async def get_alliance_selection(
    selection_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get the current state of an alliance selection.
    Refactored to use the new service-oriented architecture.
    """
    try:
        service = _get_alliance_service(db)
        response = service.get_alliance_selection(selection_id)
        return {
            "status": "success",
            "selection": response.dict()
        }

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in get_alliance_selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alliance selection: {str(e)}")


@router.post("/selection/team-action")
async def team_action(
    request: TeamActionRequest, 
    db: Session = Depends(get_db)
):
    """
    Perform an action on a team during alliance selection.
    Refactored to use the new service-oriented architecture.
    """
    try:
        service = _get_alliance_service(db)
        response = service.execute_team_action(request)
        return response.dict()

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in team_action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing team action: {str(e)}")


@router.post("/selection/{selection_id}/next-round")
async def advance_to_next_round(
    selection_id: int, 
    db: Session = Depends(get_db)
):
    """
    Advance the alliance selection to the next round.
    Refactored to use the new service-oriented architecture.
    """
    try:
        service = _get_alliance_service(db)
        response = service.advance_to_next_round(selection_id)
        return response.dict()

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in advance_to_next_round: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error advancing to next round: {str(e)}")


@router.post("/selection/{selection_id}/reset")
async def reset_alliance_selection(
    selection_id: int, 
    db: Session = Depends(get_db)
):
    """
    Reset an alliance selection back to the beginning.
    Refactored to use the new service-oriented architecture.
    """
    try:
        service = _get_alliance_service(db)
        response = service.reset_alliance_selection(selection_id)
        return response.dict()

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in reset_alliance_selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting alliance selection: {str(e)}")
