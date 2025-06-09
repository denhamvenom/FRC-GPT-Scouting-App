# backend/app/repositories/event_repository.py
"""
Event Repository

Specialized repository for event-related models (ArchivedEvent, SheetConfiguration)
with domain-specific queries for event management operations.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, or_
import logging

from app.database.models import ArchivedEvent, SheetConfiguration
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class EventRepository(BaseRepository[ArchivedEvent]):
    """Repository for event operations with specialized queries."""

    def __init__(self, db: Session):
        super().__init__(ArchivedEvent, db)
        self.sheet_config_model = SheetConfiguration

    def get_domain_specific_methods(self) -> Dict[str, Any]:
        """Return domain-specific methods for event operations."""
        return {
            'get_archived_events_by_year': self.get_archived_events_by_year,
            'get_active_archive': self.get_active_archive,
            'set_active_archive': self.set_active_archive,
            'get_archive_by_name': self.get_archive_by_name,
            'search_archives': self.search_archives,
            'get_sheet_configuration': self.get_sheet_configuration,
            'create_sheet_configuration': self.create_sheet_configuration,
            'update_sheet_configuration': self.update_sheet_configuration,
            'get_active_sheet_config': self.get_active_sheet_config,
            'set_active_sheet_config': self.set_active_sheet_config,
            'get_sheet_configs_by_event': self.get_sheet_configs_by_event,
            'delete_archive_and_cleanup': self.delete_archive_and_cleanup,
            'get_event_summary': self.get_event_summary,
        }

    # Archived Event Methods
    def get_archived_events_by_year(self, year: int) -> List[ArchivedEvent]:
        """
        Get all archived events for a specific year.
        
        Args:
            year: Competition year
            
        Returns:
            List of ArchivedEvent instances
        """
        try:
            return self.db.query(ArchivedEvent).filter(
                ArchivedEvent.year == year
            ).order_by(desc(ArchivedEvent.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting archived events for year {year}: {e}")
            raise

    def get_active_archive(self) -> Optional[ArchivedEvent]:
        """
        Get the currently active archived event.
        
        Returns:
            Active ArchivedEvent instance or None
        """
        try:
            return self.db.query(ArchivedEvent).filter(
                ArchivedEvent.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Error getting active archive: {e}")
            raise

    def set_active_archive(self, archive_id: int) -> ArchivedEvent:
        """
        Set an archive as active and deactivate all others.
        
        Args:
            archive_id: Archive ID to activate
            
        Returns:
            Activated ArchivedEvent instance
        """
        try:
            # Deactivate all archives
            self.db.query(ArchivedEvent).update({'is_active': False})
            
            # Activate the specified archive
            archive = self.get(archive_id)
            if archive:
                archive.is_active = True
                self.db.flush()
                self.db.refresh(archive)
            
            return archive
        except Exception as e:
            logger.error(f"Error setting active archive {archive_id}: {e}")
            self.db.rollback()
            raise

    def get_archive_by_name(self, name: str, year: Optional[int] = None) -> Optional[ArchivedEvent]:
        """
        Get archived event by name.
        
        Args:
            name: Archive name
            year: Optional year filter
            
        Returns:
            ArchivedEvent instance or None
        """
        try:
            query = self.db.query(ArchivedEvent).filter(
                ArchivedEvent.name == name
            )
            
            if year:
                query = query.filter(ArchivedEvent.year == year)
            
            return query.first()
        except Exception as e:
            logger.error(f"Error getting archive by name {name}: {e}")
            raise

    def search_archives(self, search_term: str, year: Optional[int] = None) -> List[ArchivedEvent]:
        """
        Search archived events by name, event key, or notes.
        
        Args:
            search_term: Search term
            year: Optional year filter
            
        Returns:
            List of matching ArchivedEvent instances
        """
        try:
            query = self.db.query(ArchivedEvent).filter(
                or_(
                    ArchivedEvent.name.like(f'%{search_term}%'),
                    ArchivedEvent.event_key.like(f'%{search_term}%'),
                    ArchivedEvent.notes.like(f'%{search_term}%')
                )
            )
            
            if year:
                query = query.filter(ArchivedEvent.year == year)
            
            return query.order_by(desc(ArchivedEvent.created_at)).all()
        except Exception as e:
            logger.error(f"Error searching archives with term {search_term}: {e}")
            raise

    # Sheet Configuration Methods
    def get_sheet_configuration(self, config_id: int) -> Optional[SheetConfiguration]:
        """
        Get sheet configuration by ID.
        
        Args:
            config_id: Sheet configuration ID
            
        Returns:
            SheetConfiguration instance or None
        """
        try:
            return self.db.query(SheetConfiguration).filter(
                SheetConfiguration.id == config_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting sheet configuration {config_id}: {e}")
            raise

    def create_sheet_configuration(self, config_data: Dict[str, Any]) -> SheetConfiguration:
        """
        Create a new sheet configuration.
        
        Args:
            config_data: Configuration data
            
        Returns:
            Created SheetConfiguration instance
        """
        try:
            config = SheetConfiguration(**config_data)
            self.db.add(config)
            self.db.flush()
            self.db.refresh(config)
            return config
        except Exception as e:
            logger.error(f"Error creating sheet configuration: {e}")
            self.db.rollback()
            raise

    def update_sheet_configuration(self, config_id: int, updates: Dict[str, Any]) -> Optional[SheetConfiguration]:
        """
        Update sheet configuration.
        
        Args:
            config_id: Configuration ID
            updates: Update data
            
        Returns:
            Updated SheetConfiguration instance or None
        """
        try:
            config = self.get_sheet_configuration(config_id)
            if config:
                for field, value in updates.items():
                    if hasattr(config, field):
                        setattr(config, field, value)
                
                self.db.flush()
                self.db.refresh(config)
            
            return config
        except Exception as e:
            logger.error(f"Error updating sheet configuration {config_id}: {e}")
            self.db.rollback()
            raise

    def get_active_sheet_config(self, event_key: str, year: int) -> Optional[SheetConfiguration]:
        """
        Get active sheet configuration for an event.
        
        Args:
            event_key: Event key
            year: Competition year
            
        Returns:
            Active SheetConfiguration instance or None
        """
        try:
            return self.db.query(SheetConfiguration).filter(
                and_(
                    SheetConfiguration.event_key == event_key,
                    SheetConfiguration.year == year,
                    SheetConfiguration.is_active == True
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting active sheet config for event {event_key}: {e}")
            raise

    def set_active_sheet_config(self, config_id: int, event_key: str, year: int) -> SheetConfiguration:
        """
        Set a sheet configuration as active for an event.
        
        Args:
            config_id: Configuration ID to activate
            event_key: Event key
            year: Competition year
            
        Returns:
            Activated SheetConfiguration instance
        """
        try:
            # Deactivate all configs for this event
            self.db.query(SheetConfiguration).filter(
                and_(
                    SheetConfiguration.event_key == event_key,
                    SheetConfiguration.year == year
                )
            ).update({'is_active': False})
            
            # Activate the specified config
            config = self.get_sheet_configuration(config_id)
            if config and config.event_key == event_key and config.year == year:
                config.is_active = True
                self.db.flush()
                self.db.refresh(config)
            
            return config
        except Exception as e:
            logger.error(f"Error setting active sheet config {config_id}: {e}")
            self.db.rollback()
            raise

    def get_sheet_configs_by_event(self, event_key: str, year: int) -> List[SheetConfiguration]:
        """
        Get all sheet configurations for an event.
        
        Args:
            event_key: Event key
            year: Competition year
            
        Returns:
            List of SheetConfiguration instances
        """
        try:
            return self.db.query(SheetConfiguration).filter(
                and_(
                    SheetConfiguration.event_key == event_key,
                    SheetConfiguration.year == year
                )
            ).order_by(desc(SheetConfiguration.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting sheet configs for event {event_key}: {e}")
            raise

    def delete_archive_and_cleanup(self, archive_id: int) -> bool:
        """
        Delete an archived event and perform cleanup.
        
        Args:
            archive_id: Archive ID to delete
            
        Returns:
            True if deletion successful
        """
        try:
            archive = self.get(archive_id)
            if archive:
                # If this was the active archive, clear the active flag
                if archive.is_active:
                    # Don't set another archive as active automatically
                    pass
                
                self.db.delete(archive)
                self.db.flush()
                logger.info(f"Deleted archive {archive_id}: {archive.name}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting archive {archive_id}: {e}")
            self.db.rollback()
            raise

    def get_event_summary(self, event_key: str, year: int) -> Dict[str, Any]:
        """
        Get comprehensive summary for an event.
        
        Args:
            event_key: Event key
            year: Competition year
            
        Returns:
            Dictionary with event summary
        """
        try:
            # Get archived events
            archives = self.db.query(ArchivedEvent).filter(
                and_(
                    ArchivedEvent.event_key == event_key,
                    ArchivedEvent.year == year
                )
            ).order_by(desc(ArchivedEvent.created_at)).all()
            
            active_archive = None
            for archive in archives:
                if archive.is_active:
                    active_archive = archive
                    break
            
            # Get sheet configurations
            sheet_configs = self.get_sheet_configs_by_event(event_key, year)
            active_sheet_config = self.get_active_sheet_config(event_key, year)
            
            # Count related data from other repositories (if available)
            # This would typically be done through the UnitOfWork pattern
            
            return {
                'event_key': event_key,
                'year': year,
                'archives': {
                    'total_count': len(archives),
                    'active_archive': {
                        'id': active_archive.id,
                        'name': active_archive.name,
                        'created_at': active_archive.created_at,
                    } if active_archive else None,
                    'all_archives': [
                        {
                            'id': archive.id,
                            'name': archive.name,
                            'is_active': archive.is_active,
                            'created_at': archive.created_at,
                        } for archive in archives
                    ]
                },
                'sheet_configs': {
                    'total_count': len(sheet_configs),
                    'active_config': {
                        'id': active_sheet_config.id,
                        'name': active_sheet_config.name,
                        'spreadsheet_id': active_sheet_config.spreadsheet_id,
                    } if active_sheet_config else None,
                    'all_configs': [
                        {
                            'id': config.id,
                            'name': config.name,
                            'is_active': config.is_active,
                            'created_at': config.created_at,
                        } for config in sheet_configs
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error getting event summary for {event_key}: {e}")
            raise