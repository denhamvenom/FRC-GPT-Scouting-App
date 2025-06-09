"""
Custom Pydantic Validators

This module contains reusable validators for Pydantic schemas.
These validators ensure data integrity and business rule compliance.
"""

import re
from pathlib import Path
from typing import Any, List, Optional


def validate_team_number(v: int) -> int:
    """Validate FRC team number"""
    if v <= 0:
        raise ValueError("Team number must be positive")
    if v > 99999:  # Reasonable upper limit for FRC teams
        raise ValueError("Team number is too large")
    return v


def validate_event_key(v: str) -> str:
    """Validate FRC event key format (e.g., '2025arc', '2025iri')"""
    pattern = r'^\d{4}[a-z0-9]+$'
    if not re.match(pattern, v.lower()):
        raise ValueError(
            "Event key must be in format: YYYY followed by event code (e.g., '2025arc')"
        )
    return v.lower()


def validate_year(v: int) -> int:
    """Validate competition year"""
    if v < 1992:  # FRC started in 1992
        raise ValueError("Year must be 1992 or later")
    if v > 2050:  # Reasonable upper limit
        raise ValueError("Year is too far in the future")
    return v


def validate_file_path(v: str) -> str:
    """Validate file path exists and is readable"""
    path = Path(v)
    if not path.exists():
        raise ValueError(f"File not found: {v}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {v}")
    if not path.suffix.lower() == '.json':
        raise ValueError(f"File must be a JSON file: {v}")
    return str(path.absolute())


def validate_metric_ids(metric_ids: List[str]) -> List[str]:
    """Validate metric IDs are unique and non-empty"""
    if not metric_ids:
        raise ValueError("At least one metric ID required")

    # Check for empty strings
    if any(not m.strip() for m in metric_ids):
        raise ValueError("Metric IDs cannot be empty")

    # Check for duplicates
    if len(metric_ids) != len(set(metric_ids)):
        raise ValueError("Duplicate metric IDs found")

    return metric_ids


def validate_weight(v: float) -> float:
    """Validate metric weight is within reasonable bounds"""
    if v < 0.1:
        raise ValueError("Weight must be at least 0.1")
    if v > 10.0:
        raise ValueError("Weight cannot exceed 10.0")
    return v


def validate_batch_size(v: int) -> int:
    """Validate batch size for processing"""
    if v < 1:
        raise ValueError("Batch size must be at least 1")
    if v > 200:
        raise ValueError("Batch size cannot exceed 200 for performance reasons")
    return v


def validate_alliance_number(v: Optional[int]) -> Optional[int]:
    """Validate alliance number (1-8 for standard FRC events)"""
    if v is None:
        return v
    if v < 1 or v > 16:  # Allow up to 16 for special events
        raise ValueError("Alliance number must be between 1 and 16")
    return v


def validate_round_number(v: int) -> int:
    """Validate round number in alliance selection"""
    if v < 0:
        raise ValueError("Round number cannot be negative")
    if v > 10:  # Reasonable upper limit
        raise ValueError("Round number is too high")
    return v


def validate_pick_position(v: str) -> str:
    """Validate pick position strategy"""
    valid_positions = ["first", "second", "third"]
    if v.lower() not in valid_positions:
        raise ValueError(
            f"Pick position must be one of: {', '.join(valid_positions)}"
        )
    return v.lower()


def validate_cache_key(v: Optional[str]) -> Optional[str]:
    """Validate cache key format"""
    if v is None:
        return v

    # Basic validation - alphanumeric with underscores/hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, v):
        raise ValueError(
            "Cache key must contain only alphanumeric characters, underscores, and hyphens"
        )

    # Length validation
    if len(v) < 3:
        raise ValueError("Cache key must be at least 3 characters")
    if len(v) > 128:
        raise ValueError("Cache key cannot exceed 128 characters")

    return v


def validate_percentage(v: float) -> float:
    """Validate percentage value (0-100)"""
    if v < 0:
        raise ValueError("Percentage cannot be negative")
    if v > 100:
        raise ValueError("Percentage cannot exceed 100")
    return v


def validate_positive_float(v: float) -> float:
    """Validate positive float value"""
    if v < 0:
        raise ValueError("Value must be positive")
    return v


def validate_non_empty_list(v: List[Any]) -> List[Any]:
    """Validate list is not empty"""
    if not v:
        raise ValueError("List cannot be empty")
    return v


def validate_action(v: str) -> str:
    """Validate team action in alliance selection"""
    valid_actions = ["captain", "accept", "decline", "remove"]
    if v.lower() not in valid_actions:
        raise ValueError(
            f"Action must be one of: {', '.join(valid_actions)}"
        )
    return v.lower()
