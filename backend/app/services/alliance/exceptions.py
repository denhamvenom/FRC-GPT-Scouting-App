# backend/app/services/alliance/exceptions.py
"""
Alliance Selection Service Exceptions

Custom exceptions for alliance selection operations, providing clear error messages
and appropriate HTTP status codes for API responses.
"""


class AllianceSelectionError(Exception):
    """Base exception for alliance selection operations."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InvalidActionError(AllianceSelectionError):
    """Raised when an invalid team action is attempted."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class InvalidRoundError(AllianceSelectionError):
    """Raised when an operation is attempted in an invalid round."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AllianceNotFoundError(AllianceSelectionError):
    """Raised when a requested alliance is not found."""

    def __init__(self, alliance_number: int):
        super().__init__(f"Alliance {alliance_number} not found", status_code=404)


class TeamNotFoundError(AllianceSelectionError):
    """Raised when a requested team is not found in the selection."""

    def __init__(self, team_number: int):
        super().__init__(f"Team {team_number} not found in this selection", status_code=404)


class SelectionNotFoundError(AllianceSelectionError):
    """Raised when a requested alliance selection is not found."""

    def __init__(self, selection_id: int):
        super().__init__(f"Alliance selection {selection_id} not found", status_code=404)


class PicklistNotFoundError(AllianceSelectionError):
    """Raised when a requested picklist is not found."""

    def __init__(self, picklist_id: int):
        super().__init__(f"Picklist {picklist_id} not found", status_code=404)


class SelectionCompletedError(AllianceSelectionError):
    """Raised when attempting to modify a completed alliance selection."""

    def __init__(self, selection_id: int):
        super().__init__(f"Alliance selection {selection_id} is already completed", status_code=400)


class DuplicateSelectionError(AllianceSelectionError):
    """Raised when attempting to create a duplicate alliance selection."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class InvalidAllianceNumberError(AllianceSelectionError):
    """Raised when an invalid alliance number is provided."""

    def __init__(self, alliance_number: int):
        super().__init__(f"Invalid alliance number: {alliance_number}. Must be 1-8.", status_code=400)


class TeamAlreadySelectedError(AllianceSelectionError):
    """Raised when attempting to select a team that is already selected."""

    def __init__(self, team_number: int, reason: str):
        super().__init__(
            f"Team {team_number} cannot be selected: {reason}",
            status_code=400
        )


class AllianceAlreadyCompleteError(AllianceSelectionError):
    """Raised when attempting to add a team to a complete alliance."""

    def __init__(self, alliance_number: int, position: str):
        super().__init__(
            f"Alliance {alliance_number} already has a {position}",
            status_code=400
        )


class CaptainRemovalError(AllianceSelectionError):
    """Raised when attempting to remove an alliance captain."""

    def __init__(self, team_number: int):
        super().__init__(
            f"Cannot remove alliance captain (Team {team_number}). Please start a new alliance selection if needed.",
            status_code=400
        )