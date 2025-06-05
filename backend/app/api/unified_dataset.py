# backend/app/api/unified_dataset.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from app.services.unified_event_data_service import build_unified_dataset, get_unified_dataset_path

# Initialize the router correctly
router = APIRouter()  # Make sure this line is here


class UnifiedDatasetRequest(BaseModel):
    event_key: str
    year: int
    force_rebuild: Optional[bool] = False


@router.post("/build")
async def build_dataset(request: UnifiedDatasetRequest):
    """
    Build or update the unified dataset for an event.

    This is a long-running operation that will return immediately with an operation ID.
    Progress can be tracked using the /progress/{operation_id} endpoint.
    """
    try:
        # Generate a unique operation ID
        operation_id = f"build_dataset_{request.event_key}_{uuid.uuid4().hex[:8]}"

        # Start the dataset build process in the background
        import asyncio

        # Create a task that will run in the background
        asyncio.create_task(
            build_unified_dataset(
                event_key=request.event_key,
                year=request.year,
                force_rebuild=request.force_rebuild,
                operation_id=operation_id,
            )
        )

        return {
            "status": "processing",
            "message": "Unified dataset build started",
            "operation_id": operation_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def check_dataset_status(event_key: str, year: int):
    """
    Check if a unified dataset exists for the given event.
    """
    import os
    from datetime import datetime
    import time

    dataset_path = get_unified_dataset_path(event_key)

    if os.path.exists(dataset_path):
        # Get file stats
        stats = os.stat(dataset_path)
        last_modified = stats.st_mtime

        modified_time = time.ctime(last_modified)

        return {"status": "exists", "path": dataset_path, "last_modified": modified_time}
    else:
        return {"status": "not_found", "event_key": event_key}


@router.get("/dataset")
async def get_dataset(path: str = None, event_key: str = None):
    """
    Get the unified dataset content.

    This endpoint supports two methods of retrieving a dataset:
    1. By providing the full path (for backward compatibility)
    2. By providing the event_key (preferred method)

    At least one of the parameters must be provided.
    """
    import os
    import json

    try:
        # Determine which path to use
        dataset_path = None

        if event_key:
            # Use event key to get the standard path
            dataset_path = get_unified_dataset_path(event_key)
        elif path:
            # Use the provided path directly
            dataset_path = path
        else:
            raise HTTPException(
                status_code=400, detail="Either 'path' or 'event_key' must be provided"
            )

        # Check if the file exists
        if not os.path.exists(dataset_path):
            raise HTTPException(
                status_code=404, detail=f"Dataset not found at path: {dataset_path}"
            )

        # Read and return the dataset
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        return dataset
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=500, detail=f"Error reading dataset: {str(e)}")
