"""
Unified Dataset API Router

This module handles all unified dataset operations including building,
status checking, and data retrieval.
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import (
    BuildDatasetRequest,
    BuildDatasetResponse,
    DatasetResponse,
    DatasetStatusResponse,
)
from app.api.utils.response_formatters import format_error_response
from app.services.unified_event_data_service import (
    build_unified_dataset,
    get_unified_dataset_path,
)

router = APIRouter(prefix="/api/dataset", tags=["dataset"])



@router.post("/build", response_model=BuildDatasetResponse)
async def build_dataset(request: BuildDatasetRequest) -> BuildDatasetResponse:
    """
    Build or rebuild the unified dataset for an event.
    
    This is an asynchronous operation that combines data from multiple sources:
    - Google Sheets scouting data
    - The Blue Alliance match and team data
    - Statbotics EPA ratings
    
    Progress can be tracked using the returned operation_id with the /api/progress/{operation_id} endpoint.
    """
    try:
        # Generate a unique operation ID
        operation_id = f"build_{request.event_key}_{uuid.uuid4().hex[:8]}"
        
        # Start the dataset build process in the background
        import asyncio
        
        asyncio.create_task(
            build_unified_dataset(
                event_key=request.event_key,
                year=2025,  # TODO: Extract year from event_key or pass separately
                force_rebuild=request.force_rebuild,
                operation_id=operation_id,
                include_practice=request.include_practice,
                include_playoffs=request.include_playoffs,
                field_mappings=request.field_mappings,
            )
        )
        
        # Return initial status
        return BuildDatasetResponse(
            status="pending",
            operation_id=operation_id,
            progress=0.0,
            message="Dataset build initiated",
            event_key=request.event_key,
            sources=[
                {"name": "sheets", "enabled": True, "status": "pending"},
                {"name": "tba", "enabled": True, "status": "pending"},
                {"name": "statbotics", "enabled": True, "status": "pending"},
            ],
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{event_key}", response_model=DatasetStatusResponse)
async def check_dataset_status(event_key: str) -> DatasetStatusResponse:
    """
    Check if a unified dataset exists for the given event.
    
    Returns dataset statistics and source information if the dataset exists.
    """
    dataset_path = get_unified_dataset_path(event_key)
    
    if os.path.exists(dataset_path):
        # Get file stats
        stats = os.stat(dataset_path)
        last_modified = datetime.fromtimestamp(stats.st_mtime)
        
        # Read dataset to get statistics
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
            
            # Extract metadata if available
            metadata = dataset.get("metadata", {})
            records = dataset.get("data", [])
            
            # Count records by source
            sources_count = {}
            if records:
                # Assume there's a source field or derive from data
                sources_count = {
                    "sheets": len([r for r in records if r.get("source") == "sheets"]),
                    "tba": len([r for r in records if r.get("source") == "tba"]),
                    "statbotics": len([r for r in records if r.get("source") == "statbotics"]),
                }
            
            dataset_stats = {
                "total_records": len(records),
                "total_fields": len(records[0].keys()) if records else 0,
                "sources": sources_count,
                "completeness": metadata.get("completeness", 0.0),
                "last_built": last_modified,
                "build_duration_seconds": metadata.get("build_duration", 0.0),
            }
            
            # Build source information
            sources = [
                {
                    "name": "sheets",
                    "enabled": True,
                    "status": "completed",
                    "records_count": sources_count.get("sheets", 0),
                    "last_updated": last_modified,
                },
                {
                    "name": "tba",
                    "enabled": True,
                    "status": "completed",
                    "records_count": sources_count.get("tba", 0),
                    "last_updated": last_modified,
                },
                {
                    "name": "statbotics",
                    "enabled": True,
                    "status": "completed",
                    "records_count": sources_count.get("statbotics", 0),
                    "last_updated": last_modified,
                },
            ]
            
            return DatasetStatusResponse(
                status="success",
                event_key=event_key,
                exists=True,
                stats=dataset_stats,
                sources=sources,
                cache_expires_at=None,  # Could add cache expiry logic
            )
        except Exception as e:
            # Dataset exists but couldn't read it
            return DatasetStatusResponse(
                status="success",
                event_key=event_key,
                exists=True,
                stats=None,
                sources=[],
                cache_expires_at=None,
            )
    else:
        return DatasetStatusResponse(
            status="success",
            event_key=event_key,
            exists=False,
            stats=None,
            sources=[
                {"name": "sheets", "enabled": True, "status": "pending"},
                {"name": "tba", "enabled": True, "status": "pending"},
                {"name": "statbotics", "enabled": True, "status": "pending"},
            ],
            cache_expires_at=None,
        )


@router.get("/{event_key}", response_model=DatasetResponse)
async def get_dataset(
    event_key: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> DatasetResponse:
    """
    Get the unified dataset content for an event.
    
    Returns the combined dataset with all fields from sheets, TBA, and Statbotics.
    Supports pagination through limit and offset parameters.
    """
    dataset_path = get_unified_dataset_path(event_key)
    
    # Check if the file exists
    if not os.path.exists(dataset_path):
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found for event {event_key}. Please build it first."
        )
    
    try:
        # Read the dataset
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        # Extract data and metadata
        all_records = dataset.get("data", [])
        metadata = dataset.get("metadata", {})
        
        # Apply pagination
        paginated_records = all_records[offset : offset + limit]
        
        # Build field definitions from first record
        fields = []
        if paginated_records:
            sample_record = paginated_records[0]
            for field_name, value in sample_record.items():
                # Determine field type from value
                field_type = "unknown"
                if isinstance(value, bool):
                    field_type = "boolean"
                elif isinstance(value, int):
                    field_type = "integer"
                elif isinstance(value, float):
                    field_type = "float"
                elif isinstance(value, str):
                    field_type = "string"
                elif isinstance(value, list):
                    field_type = "array"
                elif isinstance(value, dict):
                    field_type = "json"
                
                fields.append({
                    "name": field_name,
                    "display_name": field_name.replace("_", " ").title(),
                    "type": field_type,
                    "source": metadata.get("field_sources", {}).get(field_name, "unknown"),
                    "nullable": True,
                    "unique": False,
                })
        
        return DatasetResponse(
            status="success",
            event_key=event_key,
            data=paginated_records,
            fields=fields,
            total_records=len(all_records),
            returned_records=len(paginated_records),
            has_more=(offset + limit) < len(all_records),
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing dataset: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading dataset: {str(e)}"
        )