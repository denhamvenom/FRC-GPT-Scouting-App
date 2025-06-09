"""
Validation Service Package

This package provides comprehensive data validation functionality for the FRC scouting app.
It includes validators for completeness, statistical outliers, and data quality,
as well as correctors for handling issues and maintaining audit trails.
"""

from .validation_service import ValidationService
from .data_validation_adapter import (
    validate_event_completeness,
    validate_event_with_outliers,
    suggest_corrections,
    apply_correction,
    ignore_match,
    create_virtual_scout,
    preview_virtual_scout,
    add_to_todo_list,
    get_todo_list,
    update_todo_status,
    get_team_averages,
)
from .exceptions import (
    ValidationError,
    DataNotFoundError,
    InvalidCorrectionError,
    TodoItemExistsError,
    TodoItemNotFoundError,
)
from .models import (
    ValidationResult,
    ValidationIssue,
    CorrectionSuggestion,
    VirtualScoutData,
    TodoItem,
    AuditEntry,
)

__all__ = [
    # Main service
    "ValidationService",
    # Adapter functions for backward compatibility
    "validate_event_completeness",
    "validate_event_with_outliers",
    "suggest_corrections",
    "apply_correction",
    "ignore_match",
    "create_virtual_scout",
    "preview_virtual_scout",
    "add_to_todo_list",
    "get_todo_list",
    "update_todo_status",
    "get_team_averages",
    # Exceptions
    "ValidationError",
    "DataNotFoundError",
    "InvalidCorrectionError",
    "TodoItemExistsError",
    "TodoItemNotFoundError",
    # Models
    "ValidationResult",
    "ValidationIssue",
    "CorrectionSuggestion",
    "VirtualScoutData",
    "TodoItem",
    "AuditEntry",
]