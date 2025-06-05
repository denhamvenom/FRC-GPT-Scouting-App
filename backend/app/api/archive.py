# backend/app/api/archive.py

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.database.db import get_db

# Set up logger
logger = logging.getLogger("archive_api")
from app.services.archive_service import (
    archive_current_event,
    clear_event_data,
    get_archived_events,
    get_archived_event,
    restore_archived_event,
    delete_archived_event,
)

router = APIRouter(prefix="/api/archive", tags=["Archive"])


# Pydantic models for request/response
class ArchiveEventRequest(BaseModel):
    name: str
    event_key: str
    year: int
    notes: Optional[str] = None
    created_by: Optional[str] = None


class ClearEventRequest(BaseModel):
    event_key: str
    year: int


class RestoreArchiveRequest(BaseModel):
    archive_id: int


class DeleteArchiveRequest(BaseModel):
    archive_id: int


@router.post("/create")
async def create_archive(request: ArchiveEventRequest, req: Request, db: Session = Depends(get_db)):
    """
    Archive the current event data for later restoration.
    """
    logger.info(f"Archive request received: {request.dict()}")
    logger.info(f"Client IP: {req.client.host}, Headers: {dict(req.headers)}")

    try:
        result = await archive_current_event(
            db=db,
            name=request.name,
            event_key=request.event_key,
            year=request.year,
            notes=request.notes,
            created_by=request.created_by,
        )

        logger.info(f"Archive result: {result}")

        if result["status"] == "error":
            logger.error(f"Archive error: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])

        return result
    except Exception as e:
        logger.exception(f"Unexpected error in create_archive endpoint: {str(e)}")
        raise


@router.post("/clear")
async def clear_archive(request: ClearEventRequest, db: Session = Depends(get_db)):
    """
    Clear all data for a specific event.
    """
    result = await clear_event_data(db=db, event_key=request.event_key, year=request.year)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/list")
async def list_archives(db: Session = Depends(get_db)):
    """
    Get a list of all archived events.
    """
    archives = await get_archived_events(db)

    return {"status": "success", "archives": archives}


@router.get("/{archive_id}")
async def get_archive(archive_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific archived event.
    """
    archive = await get_archived_event(db, archive_id)

    if not archive:
        raise HTTPException(status_code=404, detail=f"Archive with ID {archive_id} not found")

    return {"status": "success", "archive": archive}


@router.post("/restore")
async def restore_archive(request: RestoreArchiveRequest, db: Session = Depends(get_db)):
    """
    Restore an archived event to the active database.
    """
    result = await restore_archived_event(db, request.archive_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/delete")
async def delete_archive(request: DeleteArchiveRequest, db: Session = Depends(get_db)):
    """
    Delete an archived event.
    """
    result = await delete_archived_event(db, request.archive_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/archive-and-clear")
async def archive_and_clear(
    request: ArchiveEventRequest, req: Request, db: Session = Depends(get_db)
):
    """
    Archive the current event and then clear the data.
    This is a convenience endpoint that combines both operations.
    """
    logger.info(f"Archive and clear request received: {request.dict()}")
    logger.info(f"Client IP: {req.client.host}, Headers: {dict(req.headers)}")

    try:
        # First archive the event
        logger.info(f"Starting archive for event {request.event_key} ({request.year})")
        archive_result = await archive_current_event(
            db=db,
            name=request.name,
            event_key=request.event_key,
            year=request.year,
            notes=request.notes,
            created_by=request.created_by,
        )

        logger.info(f"Archive result: {archive_result}")

        if archive_result["status"] == "error":
            logger.error(f"Archive error: {archive_result['message']}")
            raise HTTPException(status_code=400, detail=archive_result["message"])

        # Then clear the event data
        logger.info(f"Starting clear for event {request.event_key} ({request.year})")
        clear_result = await clear_event_data(db=db, event_key=request.event_key, year=request.year)

        logger.info(f"Clear result: {clear_result}")

        if clear_result["status"] == "error":
            logger.warning(f"Event was archived but couldn't be cleared: {clear_result['message']}")
            return {
                "status": "partial",
                "message": f"Event was archived successfully, but could not be cleared: {clear_result['message']}",
                "archive_result": archive_result,
                "clear_result": clear_result,
            }

        logger.info(f"Archive and clear successful for event {request.event_key} ({request.year})")
        return {
            "status": "success",
            "message": f"Successfully archived and cleared event {request.event_key} ({request.year})",
            "archive_result": archive_result,
            "clear_result": clear_result,
        }
    except Exception as e:
        logger.exception(f"Unexpected error in archive_and_clear endpoint: {str(e)}")
        raise
