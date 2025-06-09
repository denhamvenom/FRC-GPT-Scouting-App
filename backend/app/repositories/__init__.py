# backend/app/repositories/__init__.py
"""
Repository Package

This package provides the repository pattern implementation for data access.
Repositories abstract the data layer and provide a clean interface for CRUD operations.
"""

from .base_repository import BaseRepository
from .picklist_repository import PicklistRepository
from .alliance_repository import AllianceRepository
from .event_repository import EventRepository
from .team_repository import TeamRepository
from .unit_of_work import UnitOfWork, get_unit_of_work

__all__ = [
    "BaseRepository",
    "PicklistRepository",
    "AllianceRepository",
    "EventRepository",
    "TeamRepository",
    "UnitOfWork",
    "get_unit_of_work",
]