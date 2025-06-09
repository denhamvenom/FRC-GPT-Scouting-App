"""
Validation Service Exceptions

Custom exceptions for the validation service providing specific error handling
for various validation and correction scenarios.
"""


class ValidationError(Exception):
    """Base exception for all validation-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DataNotFoundError(ValidationError):
    """Raised when requested data (team, match, etc.) is not found in the dataset."""
    
    def __init__(self, entity_type: str, identifier: str):
        message = f"{entity_type} '{identifier}' not found in dataset"
        super().__init__(message, {"entity_type": entity_type, "identifier": identifier})


class InvalidCorrectionError(ValidationError):
    """Raised when a correction cannot be applied due to invalid data or constraints."""
    
    def __init__(self, reason: str, field: str = None, value: any = None):
        message = f"Invalid correction: {reason}"
        details = {"reason": reason}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)


class TodoItemExistsError(ValidationError):
    """Raised when attempting to add a duplicate todo item."""
    
    def __init__(self, team_number: int, match_number: int):
        message = f"Todo item already exists for team {team_number}, match {match_number}"
        super().__init__(message, {"team_number": team_number, "match_number": match_number})


class TodoItemNotFoundError(ValidationError):
    """Raised when a todo item cannot be found for update/deletion."""
    
    def __init__(self, team_number: int, match_number: int):
        message = f"Todo item not found for team {team_number}, match {match_number}"
        super().__init__(message, {"team_number": team_number, "match_number": match_number})


class InsufficientDataError(ValidationError):
    """Raised when there's not enough data to perform statistical analysis."""
    
    def __init__(self, data_type: str, required: int, found: int):
        message = f"Insufficient {data_type} data: required {required}, found {found}"
        super().__init__(message, {"data_type": data_type, "required": required, "found": found})


class FileOperationError(ValidationError):
    """Raised when file read/write operations fail."""
    
    def __init__(self, operation: str, file_path: str, error: str):
        message = f"Failed to {operation} file '{file_path}': {error}"
        super().__init__(message, {"operation": operation, "file_path": file_path, "error": error})