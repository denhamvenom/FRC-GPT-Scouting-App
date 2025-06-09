# backend/app/api/alliance_selection.py
"""
Alliance Selection API Module

This module contains the FastAPI endpoints for managing the alliance selection process.
Refactored to use standardized schemas, thin controllers, and service delegation.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.alliance import (
    AdvanceRoundResponse,
    AllianceSelectionRequest,
    AllianceSelectionResponse,
    LockedPicklistResponse,
    LockPicklistRequest,
    PicklistDetailResponse,
    PicklistListResponse,
    ResetSelectionRequest,
    TeamActionRequest,
    TeamActionResponse,
)
from app.api.utils import format_success_response, handle_service_error
from app.database.db import get_db
from app.database.models import AllianceSelection, LockedPicklist
from app.services.alliance import AllianceSelectionError, AllianceSelectionService

# Configure logging
logger = logging.getLogger("alliance_selection")

router = APIRouter(prefix="/api/alliance", tags=["Alliance Selection"])


def get_alliance_service(db: Session = Depends(get_db)) -> AllianceSelectionService:
    """Dependency injection for alliance service"""
    return AllianceSelectionService(db)


@router.post("/lock-picklist", response_model=LockedPicklistResponse)
async def lock_picklist(
    request: LockPicklistRequest,
    db: Session = Depends(get_db)
):
    """Lock a picklist and save it to the database"""
    try:
        # Check for existing picklist
        existing = db.query(LockedPicklist).filter(
            LockedPicklist.team_number == request.team_number,
            LockedPicklist.event_key == request.event_key,
            LockedPicklist.year == request.year,
        ).first()

        if existing:
            # Update existing
            existing.first_pick_data = request.first_pick_data.dict()
            existing.second_pick_data = request.second_pick_data.dict()
            if request.third_pick_data:
                existing.third_pick_data = request.third_pick_data.dict()
            if request.excluded_teams is not None:
                existing.excluded_teams = request.excluded_teams
            if request.strategy_prompts is not None:
                existing.strategy_prompts = request.strategy_prompts

            db.commit()
            db.refresh(existing)
            return LockedPicklistResponse(
                id=existing.id,
                team_number=existing.team_number,
                event_key=existing.event_key,
                year=existing.year,
                created_at=existing.created_at.isoformat()
            )

        # Create new
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
        return LockedPicklistResponse(
            id=new_picklist.id,
            team_number=new_picklist.team_number,
            event_key=new_picklist.event_key,
            year=new_picklist.year,
            created_at=new_picklist.created_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Error locking picklist: {str(e)}")
        raise handle_service_error(e, "lock_picklist")


@router.get("/picklists", response_model=PicklistListResponse)
async def get_picklists(
    team_number: Optional[int] = None,
    event_key: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all locked picklists with optional filtering"""
    try:
        query = db.query(LockedPicklist)

        if team_number:
            query = query.filter(LockedPicklist.team_number == team_number)
        if event_key:
            query = query.filter(LockedPicklist.event_key == event_key)

        picklists = query.all()

        picklist_data = [
            {
                "id": p.id,
                "team_number": p.team_number,
                "event_key": p.event_key,
                "year": p.year,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in picklists
        ]

        return PicklistListResponse(
            picklists=picklist_data,
            total=len(picklist_data)
        )

    except Exception as e:
        logger.error(f"Error retrieving picklists: {str(e)}")
        raise handle_service_error(e, "get_picklists")


@router.get("/picklist/{picklist_id}", response_model=PicklistDetailResponse)
async def get_picklist(picklist_id: int, db: Session = Depends(get_db)):
    """Get a specific locked picklist by ID"""
    try:
        picklist = db.query(LockedPicklist).filter(LockedPicklist.id == picklist_id).first()

        if not picklist:
            raise HTTPException(status_code=404, detail="Picklist not found")

        picklist_data = {
            "id": picklist.id,
            "team_number": picklist.team_number,
            "event_key": picklist.event_key,
            "year": picklist.year,
            "first_pick_data": picklist.first_pick_data,
            "second_pick_data": picklist.second_pick_data,
            "third_pick_data": picklist.third_pick_data,
            "created_at": picklist.created_at.isoformat(),
            "updated_at": picklist.updated_at.isoformat() if picklist.updated_at else None,
        }

        return PicklistDetailResponse(picklist=picklist_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving picklist: {str(e)}")
        raise handle_service_error(e, "get_picklist")


@router.delete("/picklist/{picklist_id}")
async def unlock_picklist(picklist_id: int, db: Session = Depends(get_db)):
    """Unlock a picklist by deleting it"""
    try:
        picklist = db.query(LockedPicklist).filter(LockedPicklist.id == picklist_id).first()
        if not picklist:
            raise HTTPException(status_code=404, detail="Picklist not found")

        # Detach from alliance selections
        selections = db.query(AllianceSelection).filter(AllianceSelection.picklist_id == picklist_id).all()
        for selection in selections:
            selection.picklist_id = None

        db.delete(picklist)
        db.commit()

        return format_success_response(message="Picklist successfully unlocked and deleted")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlocking picklist: {str(e)}")
        raise handle_service_error(e, "unlock_picklist")


@router.post("/selection/create", response_model=AllianceSelectionResponse)
async def create_alliance_selection(
    request: AllianceSelectionRequest,
    service: AllianceSelectionService = Depends(get_alliance_service)
):
    """Create a new alliance selection process"""
    try:
        response = service.create_alliance_selection(request)
        return response

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error creating alliance selection: {str(e)}")
        raise handle_service_error(e, "create_alliance_selection")


@router.get("/selection/{selection_id}")
async def get_alliance_selection(
    selection_id: int,
    service: AllianceSelectionService = Depends(get_alliance_service)
):
    """Get the current state of an alliance selection"""
    try:
        response = service.get_alliance_selection(selection_id)
        return format_success_response(data={"selection": response.dict()})

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving alliance selection: {str(e)}")
        raise handle_service_error(e, "get_alliance_selection")


@router.post("/selection/team-action", response_model=TeamActionResponse)
async def team_action(
    request: TeamActionRequest,
    service: AllianceSelectionService = Depends(get_alliance_service)
):
    """Perform an action on a team during alliance selection"""
    try:
        response = service.execute_team_action(request)
        return response

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error performing team action: {str(e)}")
        raise handle_service_error(e, "team_action")


@router.post("/selection/{selection_id}/next-round", response_model=AdvanceRoundResponse)
async def advance_to_next_round(
    selection_id: int,
    service: AllianceSelectionService = Depends(get_alliance_service)
):
    """Advance the alliance selection to the next round"""
    try:
        response = service.advance_to_next_round(selection_id)
        return response

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error advancing to next round: {str(e)}")
        raise handle_service_error(e, "advance_to_next_round")


@router.post("/selection/{selection_id}/reset")
async def reset_alliance_selection(
    selection_id: int,
    request: ResetSelectionRequest,
    service: AllianceSelectionService = Depends(get_alliance_service)
):
    """Reset an alliance selection back to the beginning"""
    try:
        if not request.confirm:
            raise HTTPException(status_code=400, detail="Must confirm reset with 'confirm: true'")

        response = service.reset_alliance_selection(selection_id)
        return response

    except AllianceSelectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error resetting alliance selection: {str(e)}")
        raise handle_service_error(e, "reset_alliance_selection")
