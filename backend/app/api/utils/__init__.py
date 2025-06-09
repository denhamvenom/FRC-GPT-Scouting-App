"""
API Utilities Package

This package contains shared utilities for API endpoints including
error handling, response formatting, and common functionality.
"""

from .error_handlers import (
    api_error_handler,
    create_error_response,
    handle_not_found_error,
    handle_permission_error,
    handle_service_error,
    handle_validation_error,
)
from .response_formatters import (
    format_error_response,
    format_paginated_response,
    format_status_response,
    format_success_response,
    standardize_response,
)

__all__ = [
    # Error handlers
    "handle_service_error",
    "handle_validation_error",
    "handle_not_found_error",
    "handle_permission_error",
    "api_error_handler",
    "create_error_response",
    # Response formatters
    "format_success_response",
    "format_error_response",
    "format_paginated_response",
    "format_status_response",
    "standardize_response",
]
