# backend/app/repositories/unit_of_work.py
"""
Unit of Work Pattern Implementation

Provides transaction management and coordinates work across multiple repositories.
Ensures that all repository operations within a unit of work are committed or rolled back together.
"""

from typing import Any, Dict, List, Optional, Type
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.database.db import SessionLocal, get_db_session
from .base_repository import BaseRepository
from .picklist_repository import PicklistRepository
from .alliance_repository import AllianceRepository
from .event_repository import EventRepository
from .team_repository import TeamRepository

logger = logging.getLogger(__name__)


class UnitOfWork:
    """
    Unit of Work implementation for managing database transactions.
    
    Provides a central point for coordinating operations across multiple repositories
    and ensuring transaction integrity.
    """

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize Unit of Work with optional database session.
        
        Args:
            db: Optional existing database session
        """
        self._db = db
        self._external_session = db is not None
        self._repositories: Dict[str, BaseRepository] = {}
        self._committed = False

    @property
    def db(self) -> Session:
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    @property
    def picklist_repository(self) -> PicklistRepository:
        """Get picklist repository."""
        if 'picklist' not in self._repositories:
            self._repositories['picklist'] = PicklistRepository(self.db)
        return self._repositories['picklist']

    @property
    def alliance_repository(self) -> AllianceRepository:
        """Get alliance repository."""
        if 'alliance' not in self._repositories:
            self._repositories['alliance'] = AllianceRepository(self.db)
        return self._repositories['alliance']

    @property
    def event_repository(self) -> EventRepository:
        """Get event repository."""
        if 'event' not in self._repositories:
            self._repositories['event'] = EventRepository(self.db)
        return self._repositories['event']

    @property
    def team_repository(self) -> TeamRepository:
        """Get team repository."""
        if 'team' not in self._repositories:
            self._repositories['team'] = TeamRepository(self.db)
        return self._repositories['team']

    def get_repository(self, repository_class: Type[BaseRepository]) -> BaseRepository:
        """
        Get a repository instance of the specified class.
        
        Args:
            repository_class: Repository class to instantiate
            
        Returns:
            Repository instance
        """
        class_name = repository_class.__name__.lower()
        if class_name not in self._repositories:
            self._repositories[class_name] = repository_class(self.db)
        return self._repositories[class_name]

    def commit(self) -> None:
        """
        Commit the current transaction.
        
        Raises:
            SQLAlchemyError: If commit fails
        """
        try:
            self.db.commit()
            self._committed = True
            logger.debug("Unit of work committed successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error committing unit of work: {e}")
            self.rollback()
            raise

    def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            self.db.rollback()
            logger.debug("Unit of work rolled back")
        except SQLAlchemyError as e:
            logger.error(f"Error rolling back unit of work: {e}")
            raise

    def flush(self) -> None:
        """
        Flush changes to the database without committing.
        
        Raises:
            SQLAlchemyError: If flush fails
        """
        try:
            self.db.flush()
            logger.debug("Unit of work flushed")
        except SQLAlchemyError as e:
            logger.error(f"Error flushing unit of work: {e}")
            raise

    def close(self) -> None:
        """Close the database session if we own it."""
        if not self._external_session and self._db is not None:
            try:
                self._db.close()
                logger.debug("Unit of work database session closed")
            except Exception as e:
                logger.error(f"Error closing unit of work session: {e}")
            finally:
                self._db = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        
        Automatically commits if no exception occurred, otherwise rolls back.
        """
        try:
            if exc_type is None and not self._committed:
                self.commit()
            elif exc_type is not None:
                self.rollback()
        finally:
            self.close()

    def execute_in_transaction(self, operation_func, *args, **kwargs) -> Any:
        """
        Execute an operation within a transaction.
        
        Args:
            operation_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If operation fails
        """
        try:
            result = operation_func(self, *args, **kwargs)
            if not self._committed:
                self.commit()
            return result
        except Exception as e:
            logger.error(f"Error executing operation in transaction: {e}")
            self.rollback()
            raise

    def bulk_operations(self) -> 'BulkOperations':
        """
        Get bulk operations handler.
        
        Returns:
            BulkOperations instance for batch processing
        """
        return BulkOperations(self)

    def get_transaction_info(self) -> Dict[str, Any]:
        """
        Get information about the current transaction state.
        
        Returns:
            Dictionary with transaction information
        """
        return {
            'has_session': self._db is not None,
            'external_session': self._external_session,
            'committed': self._committed,
            'repositories_loaded': list(self._repositories.keys()),
            'in_transaction': self._db.in_transaction() if self._db else False,
        }


class BulkOperations:
    """Helper class for bulk operations within a Unit of Work."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.uow = unit_of_work

    def create_picklists(self, picklist_data_list: List[Dict[str, Any]]) -> List[Any]:
        """
        Create multiple picklists in a single transaction.
        
        Args:
            picklist_data_list: List of picklist data dictionaries
            
        Returns:
            List of created picklist instances
        """
        try:
            return self.uow.picklist_repository.bulk_create(picklist_data_list)
        except Exception as e:
            logger.error(f"Error in bulk picklist creation: {e}")
            raise

    def update_team_statuses(self, status_updates: List[Dict[str, Any]]) -> bool:
        """
        Update multiple team statuses in a single transaction.
        
        Args:
            status_updates: List of status update dictionaries
            
        Returns:
            True if operation succeeded
        """
        try:
            return self.uow.team_repository.bulk_update(status_updates)
        except Exception as e:
            logger.error(f"Error in bulk team status updates: {e}")
            raise

    def create_alliance_selection_with_teams(
        self,
        selection_data: Dict[str, Any],
        team_statuses: List[Dict[str, Any]],
        alliances: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create complete alliance selection with teams and alliances.
        
        Args:
            selection_data: Alliance selection data
            team_statuses: Team status data list
            alliances: Alliance data list
            
        Returns:
            Dictionary with created objects
        """
        try:
            # Create alliance selection
            selection = self.uow.alliance_repository.create(selection_data)
            
            # Add selection_id to related objects
            for status in team_statuses:
                status['selection_id'] = selection.id
            
            for alliance in alliances:
                alliance['selection_id'] = selection.id
            
            # Create team statuses
            created_statuses = []
            for status_data in team_statuses:
                status = self.uow.alliance_repository.update_team_status(
                    selection.id,
                    status_data['team_number'],
                    status_data.get('is_captain', False),
                    status_data.get('is_picked', False),
                    status_data.get('has_declined', False),
                    status_data.get('round_eliminated')
                )
                created_statuses.append(status)
            
            # Create alliances
            created_alliances = []
            for alliance_data in alliances:
                alliance = self.uow.alliance_repository.update_alliance(
                    selection.id,
                    alliance_data['alliance_number'],
                    alliance_data.get('captain_team_number'),
                    alliance_data.get('first_pick_team_number'),
                    alliance_data.get('second_pick_team_number'),
                    alliance_data.get('backup_team_number')
                )
                created_alliances.append(alliance)
            
            return {
                'selection': selection,
                'team_statuses': created_statuses,
                'alliances': created_alliances,
            }
        except Exception as e:
            logger.error(f"Error creating alliance selection with teams: {e}")
            raise

    def archive_event_data(
        self,
        archive_data: Dict[str, Any],
        cleanup_configs: bool = True
    ) -> Dict[str, Any]:
        """
        Archive event data and optionally clean up configurations.
        
        Args:
            archive_data: Archive data
            cleanup_configs: Whether to deactivate old configurations
            
        Returns:
            Dictionary with archive results
        """
        try:
            # Create archive
            archive = self.uow.event_repository.create(archive_data)
            
            # Set as active if specified
            if archive_data.get('is_active', False):
                self.uow.event_repository.set_active_archive(archive.id)
            
            # Cleanup old configurations if requested
            if cleanup_configs:
                event_key = archive_data.get('event_key')
                year = archive_data.get('year')
                
                if event_key and year:
                    # Deactivate old sheet configurations
                    configs = self.uow.event_repository.get_sheet_configs_by_event(event_key, year)
                    for config in configs:
                        if config.is_active:
                            config.is_active = False
            
            return {
                'archive': archive,
                'cleanup_performed': cleanup_configs,
            }
        except Exception as e:
            logger.error(f"Error archiving event data: {e}")
            raise


@contextmanager
def get_unit_of_work(db: Optional[Session] = None):
    """
    Context manager for creating a Unit of Work.
    
    Args:
        db: Optional existing database session
        
    Yields:
        UnitOfWork instance
        
    Example:
        with get_unit_of_work() as uow:
            picklist = uow.picklist_repository.create(picklist_data)
            alliance = uow.alliance_repository.create(alliance_data)
            # Automatically commits if no exceptions
    """
    uow = UnitOfWork(db)
    try:
        yield uow
    except Exception:
        # Exception handling is done in UnitOfWork.__exit__
        raise
    finally:
        # Cleanup is done in UnitOfWork.__exit__
        pass


def create_unit_of_work_factory():
    """
    Create a factory function for Unit of Work instances.
    
    Returns:
        Function that creates UnitOfWork instances
    """
    def factory(db: Optional[Session] = None) -> UnitOfWork:
        return UnitOfWork(db)
    
    return factory


# Factory instance for dependency injection
unit_of_work_factory = create_unit_of_work_factory()