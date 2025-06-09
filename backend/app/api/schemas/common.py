"""
Common API Schemas

This module contains shared schemas used across multiple API endpoints.
These schemas provide consistent response formats and common data structures.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, Field

# Generic type for paginated responses
T = TypeVar('T')


class SuccessResponse(BaseModel):
    """Standard success response format"""
    status: Literal["success"] = Field(default="success", description="Always 'success' for successful responses")
    message: Optional[str] = Field(None, description="Optional success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {"id": 123, "created": True}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format"""
    status: Literal["error"] = Field(default="error", description="Always 'error' for error responses")
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for client handling")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed error information")

    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "detail": "Validation error",
                "code": "VALIDATION_ERROR",
                "errors": [
                    {"field": "team_number", "message": "Team number must be positive"}
                ]
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response format"""
    status: Literal["success"] = Field(default="success", description="Always 'success' for successful responses")
    data: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "total": 50,
                "page": 1,
                "per_page": 20,
                "pages": 3,
                "has_next": True,
                "has_prev": False
            }
        }


class StatusResponse(BaseModel):
    """Generic status response for async operations"""
    status: str = Field(..., description="Operation status", enum=["pending", "in_progress", "completed", "failed"])
    operation_id: str = Field(..., description="Unique operation identifier")
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result (when completed)")
    error: Optional[str] = Field(None, description="Error message (when failed)")
    created_at: datetime = Field(..., description="Operation start time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

    class Config:
        schema_extra = {
            "example": {
                "status": "in_progress",
                "operation_id": "op_123456",
                "progress": 45.5,
                "message": "Processing batch 3 of 10",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:05:00Z",
                "estimated_completion": "2025-01-01T12:15:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response format"""
    status: str = Field(default="healthy", enum=["healthy", "degraded", "unhealthy"])
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Uptime in seconds")
    timestamp: datetime = Field(..., description="Current timestamp")
    services: Dict[str, Dict[str, Union[str, bool]]] = Field(
        ...,
        description="Status of dependent services"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5,
                "timestamp": "2025-01-01T12:00:00Z",
                "services": {
                    "database": {"status": "connected", "healthy": True},
                    "openai": {"status": "connected", "healthy": True},
                    "tba": {"status": "connected", "healthy": True}
                }
            }
        }


class CacheKeyRequest(BaseModel):
    """Request for operations requiring a cache key"""
    cache_key: str = Field(..., description="Cache key for the operation")

    class Config:
        schema_extra = {
            "example": {
                "cache_key": "op_abc123def456"
            }
        }


class BatchRequest(BaseModel):
    """Base request for batch operations"""
    batch_size: int = Field(20, ge=5, le=100, description="Number of items per batch")
    parallel: bool = Field(False, description="Whether to process batches in parallel")

    class Config:
        schema_extra = {
            "example": {
                "batch_size": 20,
                "parallel": False
            }
        }
