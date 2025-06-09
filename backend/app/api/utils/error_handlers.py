"""
Standardized Error Handlers

This module provides consistent error handling across all API endpoints.
It converts various exception types to appropriate HTTP responses.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.schemas.common import ErrorResponse

# Configure logger
logger = logging.getLogger("api.error_handlers")


def create_error_response(
    detail: str,
    status_code: int = 500,
    code: Optional[str] = None,
    errors: Optional[List[Dict[str, Any]]] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    return ErrorResponse(
        detail=detail,
        code=code or f"ERROR_{status_code}",
        errors=errors
    )


def handle_validation_error(error: ValidationError) -> HTTPException:
    """Convert Pydantic validation errors to HTTP exceptions"""
    errors = []
    for err in error.errors():
        errors.append({
            "field": ".".join(str(x) for x in err["loc"]),
            "message": err["msg"],
            "type": err["type"]
        })

    return HTTPException(
        status_code=422,
        detail=create_error_response(
            detail="Validation failed",
            status_code=422,
            code="VALIDATION_ERROR",
            errors=errors
        ).dict()
    )


def handle_not_found_error(
    resource: str,
    identifier: Union[str, int]
) -> HTTPException:
    """Create a not found error"""
    return HTTPException(
        status_code=404,
        detail=create_error_response(
            detail=f"{resource} with ID '{identifier}' not found",
            status_code=404,
            code="NOT_FOUND"
        ).dict()
    )


def handle_permission_error(
    action: str,
    resource: Optional[str] = None
) -> HTTPException:
    """Create a permission denied error"""
    detail = f"Permission denied for action: {action}"
    if resource:
        detail += f" on resource: {resource}"

    return HTTPException(
        status_code=403,
        detail=create_error_response(
            detail=detail,
            status_code=403,
            code="PERMISSION_DENIED"
        ).dict()
    )


def handle_service_error(
    error: Exception,
    context: Optional[str] = None
) -> HTTPException:
    """Handle service layer errors"""
    # Log the full error for debugging
    logger.error(
        f"Service error in {context or 'unknown context'}: {str(error)}",
        exc_info=True
    )

    # Map known error types
    error_message = str(error)
    status_code = 500
    error_code = "SERVICE_ERROR"

    # Check for specific error patterns
    if "not found" in error_message.lower():
        status_code = 404
        error_code = "NOT_FOUND"
    elif "already exists" in error_message.lower():
        status_code = 409
        error_code = "CONFLICT"
    elif "invalid" in error_message.lower() or "validation" in error_message.lower():
        status_code = 400
        error_code = "VALIDATION_ERROR"
    elif "unauthorized" in error_message.lower():
        status_code = 401
        error_code = "UNAUTHORIZED"
    elif "forbidden" in error_message.lower() or "permission" in error_message.lower():
        status_code = 403
        error_code = "PERMISSION_DENIED"

    # For known business logic errors from services
    if hasattr(error, 'status_code'):
        status_code = error.status_code
    if hasattr(error, 'error_code'):
        error_code = error.error_code

    return HTTPException(
        status_code=status_code,
        detail=create_error_response(
            detail=error_message,
            status_code=status_code,
            code=error_code
        ).dict()
    )


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global error handler for unhandled exceptions.
    
    This should be registered with the FastAPI app:
    app.add_exception_handler(Exception, api_error_handler)
    """
    # Log the full error
    logger.error(
        f"Unhandled error for {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )

    # Don't expose internal errors in production
    if isinstance(exc, HTTPException):
        # Re-raise HTTP exceptions as-is
        raise exc

    # For all other exceptions, return a generic error
    error_response = create_error_response(
        detail="An unexpected error occurred",
        status_code=500,
        code="INTERNAL_ERROR"
    )

    # In development, include more details
    import os
    if os.getenv("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]:
        error_response.errors = [{
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc().split("\n")
        }]

    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


def log_api_error(
    endpoint: str,
    error: Exception,
    request_data: Optional[Dict[str, Any]] = None
) -> None:
    """Log API errors with context"""
    logger.error(
        f"API Error in {endpoint}",
        extra={
            "endpoint": endpoint,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "request_data": request_data,
            "traceback": traceback.format_exc()
        }
    )
