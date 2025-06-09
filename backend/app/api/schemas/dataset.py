"""
Dataset API Schemas

This module contains schemas specific to the unified dataset API endpoints.
Includes models for dataset building, status tracking, and data retrieval.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .common import StatusResponse, SuccessResponse


class DatasetSource(BaseModel):
    """Represents a data source for the unified dataset"""
    name: str = Field(..., description="Source name (e.g., 'sheets', 'tba', 'statbotics')")
    enabled: bool = Field(True, description="Whether this source is enabled")
    status: Literal["pending", "fetching", "completed", "failed"] = Field(
        "pending",
        description="Current status of this source"
    )
    records_count: Optional[int] = Field(None, description="Number of records from this source")
    error: Optional[str] = Field(None, description="Error message if failed")
    last_updated: Optional[datetime] = Field(None, description="Last successful update")

    class Config:
        schema_extra = {
            "example": {
                "name": "sheets",
                "enabled": True,
                "status": "completed",
                "records_count": 500,
                "last_updated": "2025-01-01T12:00:00Z"
            }
        }


class DatasetField(BaseModel):
    """Represents a field in the unified dataset"""
    name: str = Field(..., description="Field name")
    display_name: str = Field(..., description="Human-readable name")
    type: str = Field(..., description="Data type (string, number, boolean, etc.)")
    source: str = Field(..., description="Source of this field")
    description: Optional[str] = Field(None, description="Field description")
    nullable: bool = Field(True, description="Whether field can be null")
    unique: bool = Field(False, description="Whether field values are unique")

    class Config:
        schema_extra = {
            "example": {
                "name": "team_number",
                "display_name": "Team Number",
                "type": "integer",
                "source": "tba",
                "description": "FRC team number",
                "nullable": False,
                "unique": False
            }
        }


class DatasetStats(BaseModel):
    """Statistics about the unified dataset"""
    total_records: int = Field(..., description="Total number of records")
    total_fields: int = Field(..., description="Total number of fields")
    sources: Dict[str, int] = Field(..., description="Record count by source")
    completeness: float = Field(..., ge=0, le=1, description="Data completeness percentage")
    last_built: datetime = Field(..., description="When dataset was last built")
    build_duration_seconds: float = Field(..., description="Time taken to build dataset")

    class Config:
        schema_extra = {
            "example": {
                "total_records": 1500,
                "total_fields": 45,
                "sources": {
                    "sheets": 500,
                    "tba": 500,
                    "statbotics": 500
                },
                "completeness": 0.92,
                "last_built": "2025-01-01T12:00:00Z",
                "build_duration_seconds": 45.3
            }
        }


# Request Models

class BuildDatasetRequest(BaseModel):
    """Request to build unified dataset"""
    event_key: str = Field(..., description="Event key to build dataset for")
    sources: Optional[List[str]] = Field(
        None,
        description="Specific sources to include (None = all enabled sources)"
    )
    force_rebuild: bool = Field(
        False,
        description="Force rebuild even if cached version exists"
    )
    include_practice: bool = Field(
        False,
        description="Include practice match data"
    )
    include_playoffs: bool = Field(
        True,
        description="Include playoff match data"
    )
    field_mappings: Optional[Dict[str, str]] = Field(
        None,
        description="Custom field mappings"
    )

    class Config:
        schema_extra = {
            "example": {
                "event_key": "2025arc",
                "sources": ["sheets", "tba", "statbotics"],
                "force_rebuild": False,
                "include_practice": False,
                "include_playoffs": True
            }
        }


class DatasetFilterRequest(BaseModel):
    """Request to filter dataset records"""
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Field filters (field_name: value or condition)"
    )
    fields: Optional[List[str]] = Field(
        None,
        description="Specific fields to include in response"
    )
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Literal["asc", "desc"] = Field("asc", description="Sort order")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")
    offset: int = Field(0, ge=0, description="Number of records to skip")

    class Config:
        schema_extra = {
            "example": {
                "filters": {
                    "team_number": 254,
                    "match_type": "qualification"
                },
                "fields": ["team_number", "match_key", "total_points"],
                "sort_by": "match_number",
                "sort_order": "asc",
                "limit": 50,
                "offset": 0
            }
        }


# Response Models

class BuildDatasetResponse(StatusResponse):
    """Response for dataset build operation"""
    event_key: str = Field(..., description="Event being processed")
    sources: List[DatasetSource] = Field(..., description="Status of each data source")
    cache_key: Optional[str] = Field(None, description="Cache key for the built dataset")

    class Config:
        schema_extra = {
            "example": {
                "status": "in_progress",
                "operation_id": "build_2025arc_123456",
                "progress": 33.3,
                "message": "Fetching data from TBA",
                "event_key": "2025arc",
                "sources": [
                    {
                        "name": "sheets",
                        "enabled": True,
                        "status": "completed",
                        "records_count": 500
                    }
                ],
                "created_at": "2025-01-01T12:00:00Z"
            }
        }


class DatasetStatusResponse(SuccessResponse):
    """Response for dataset status check"""
    event_key: str = Field(..., description="Event key")
    exists: bool = Field(..., description="Whether dataset exists")
    stats: Optional[DatasetStats] = Field(None, description="Dataset statistics")
    sources: List[DatasetSource] = Field(..., description="Data source information")
    cache_expires_at: Optional[datetime] = Field(None, description="When cache expires")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event_key": "2025arc",
                "exists": True,
                "stats": {
                    "total_records": 1500,
                    "total_fields": 45,
                    "sources": {"sheets": 500, "tba": 500, "statbotics": 500},
                    "completeness": 0.92,
                    "last_built": "2025-01-01T12:00:00Z",
                    "build_duration_seconds": 45.3
                },
                "sources": [],
                "cache_expires_at": "2025-01-02T12:00:00Z"
            }
        }


class DatasetResponse(SuccessResponse):
    """Response containing dataset records"""
    event_key: str = Field(..., description="Event key")
    data: List[Dict[str, Any]] = Field(..., description="Dataset records")
    fields: List[DatasetField] = Field(..., description="Field definitions")
    total_records: int = Field(..., description="Total records (before filtering)")
    returned_records: int = Field(..., description="Number of records returned")
    has_more: bool = Field(..., description="Whether more records exist")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event_key": "2025arc",
                "data": [
                    {
                        "team_number": 254,
                        "match_key": "2025arc_qm1",
                        "alliance": "red",
                        "total_points": 150
                    }
                ],
                "fields": [
                    {
                        "name": "team_number",
                        "display_name": "Team Number",
                        "type": "integer",
                        "source": "tba"
                    }
                ],
                "total_records": 1500,
                "returned_records": 1,
                "has_more": True
            }
        }


class DatasetExportResponse(SuccessResponse):
    """Response for dataset export operations"""
    event_key: str = Field(..., description="Event key")
    export_format: str = Field(..., description="Export format (csv, json, excel)")
    file_url: str = Field(..., description="URL to download exported file")
    file_size_bytes: int = Field(..., description="File size in bytes")
    expires_at: datetime = Field(..., description="When download link expires")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event_key": "2025arc",
                "export_format": "csv",
                "file_url": "/api/dataset/download/2025arc_export_123456.csv",
                "file_size_bytes": 524288,
                "expires_at": "2025-01-01T13:00:00Z"
            }
        }


class DatasetFieldsResponse(SuccessResponse):
    """Response containing available dataset fields"""
    event_key: str = Field(..., description="Event key")
    fields: List[DatasetField] = Field(..., description="Available fields")
    field_groups: Dict[str, List[str]] = Field(
        ...,
        description="Fields grouped by category"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event_key": "2025arc",
                "fields": [],
                "field_groups": {
                    "team_info": ["team_number", "team_name", "team_city"],
                    "match_info": ["match_key", "match_number", "match_type"],
                    "performance": ["total_points", "auto_points", "teleop_points"]
                }
            }
        }