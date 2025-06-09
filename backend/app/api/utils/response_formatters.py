"""
Response Formatting Utilities

This module provides consistent response formatting across all API endpoints.
It ensures all responses follow the same structure and standards.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel

from app.api.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    StatusResponse,
    SuccessResponse,
)

T = TypeVar('T')


def format_success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Format a successful response"""
    response = SuccessResponse(
        message=message,
        data=data if isinstance(data, dict) else {"result": data} if data is not None else None
    )
    return response.dict(exclude_none=True)


def format_error_response(
    detail: str,
    code: Optional[str] = None,
    errors: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Format an error response"""
    response = ErrorResponse(
        detail=detail,
        code=code,
        errors=errors
    )
    return response.dict(exclude_none=True)


def format_paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """Format a paginated response"""
    pages = (total + per_page - 1) // per_page  # Ceiling division

    response = {
        "status": "success",
        "data": data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }

    return response


def format_status_response(
    status: str,
    operation_id: str,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
    estimated_completion: Optional[datetime] = None
) -> Dict[str, Any]:
    """Format a status response for async operations"""
    response = StatusResponse(
        status=status,
        operation_id=operation_id,
        progress=progress,
        message=message,
        result=result,
        error=error,
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at,
        estimated_completion=estimated_completion
    )
    return response.dict(exclude_none=True)


def standardize_response(
    data: Union[BaseModel, Dict[str, Any], List[Any], Any],
    wrap_data: bool = True
) -> Dict[str, Any]:
    """
    Standardize any response to ensure consistent structure.
    
    Args:
        data: The data to standardize
        wrap_data: Whether to wrap non-dict responses in a 'data' key
    
    Returns:
        Standardized response dictionary
    """
    # If it's already a Pydantic model, convert to dict
    if isinstance(data, BaseModel):
        response_data = data.dict(exclude_none=True)
    elif isinstance(data, dict):
        response_data = data
    # For lists and other types, wrap in a standard structure
    elif wrap_data:
        response_data = {"data": data}
    else:
        response_data = data

    # Ensure there's always a status field
    if isinstance(response_data, dict) and "status" not in response_data:
        # Don't add status to error responses
        if "detail" not in response_data:
            response_data["status"] = "success"

    return response_data


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string"""
    if dt is None:
        return None
    return dt.isoformat() + "Z"


def format_list_response(
    items: List[Any],
    total: Optional[int] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Format a list response (non-paginated)"""
    response = {
        "status": "success",
        "data": items,
        "count": len(items)
    }

    if total is not None:
        response["total"] = total

    if message:
        response["message"] = message

    return response


def format_item_response(
    item: Any,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format a single item response"""
    response = {
        "status": "success",
        "data": item
    }

    if message:
        response["message"] = message

    if metadata:
        response["metadata"] = metadata

    return response


def format_action_response(
    success: bool,
    message: str,
    data: Optional[Any] = None,
    changes: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format a response for an action (create, update, delete)"""
    response = {
        "status": "success" if success else "error",
        "message": message
    }

    if data is not None:
        response["data"] = data

    if changes:
        response["changes"] = changes

    return response


def format_batch_response(
    successful: List[Any],
    failed: List[Dict[str, Any]],
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Format a response for batch operations"""
    total = len(successful) + len(failed)

    response = {
        "status": "partial" if failed else "success",
        "message": message or f"Processed {total} items",
        "summary": {
            "total": total,
            "successful": len(successful),
            "failed": len(failed)
        },
        "successful": successful,
        "failed": failed
    }

    return response
