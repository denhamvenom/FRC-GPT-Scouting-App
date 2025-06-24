#!/usr/bin/env python3
# backend/app/api/progress.py

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from app.services.progress_tracker import ProgressTracker

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    responses={404: {"description": "Operation not found"}},
)


@router.get("/{operation_id}")
async def get_operation_progress(operation_id: str) -> Dict[str, Any]:
    """
    Get the progress of a specific operation.

    Args:
        operation_id: The unique identifier for the operation

    Returns:
        Dictionary with progress information

    Raises:
        HTTPException: If the operation is not found
    """
    progress = ProgressTracker.get_progress(operation_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Operation {operation_id} not found")
    return progress


@router.get("/")
async def list_active_operations() -> Dict[str, Dict[str, Any]]:
    """
    List all active operations and their progress.

    Returns:
        Dictionary of operation IDs to progress information
    """
    return ProgressTracker.list_operations()
