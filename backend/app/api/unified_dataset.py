# backend/app/api/unified_dataset.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

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
    """
    try:
        output_path = await build_unified_dataset(
            event_key=request.event_key,
            year=request.year,
            force_rebuild=request.force_rebuild
        )
        
        return {
            "status": "success",
            "message": "Unified dataset built successfully",
            "path": output_path
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
        
        return {
            "status": "exists",
            "path": dataset_path,
            "last_modified": modified_time
        }
    else:
        return {
            "status": "not_found",
            "event_key": event_key
        }