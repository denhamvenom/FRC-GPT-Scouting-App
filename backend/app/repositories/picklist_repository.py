# backend/app/repositories/picklist_repository.py
"""
Picklist Repository

Specialized repository for LockedPicklist model with domain-specific queries
for picklist management operations.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from app.database.models import LockedPicklist
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PicklistRepository(BaseRepository[LockedPicklist]):
    """Repository for LockedPicklist operations with specialized queries."""

    def __init__(self, db: Session):
        super().__init__(LockedPicklist, db)

    def get_domain_specific_methods(self) -> Dict[str, Any]:
        """Return domain-specific methods for picklist operations."""
        return {
            'get_by_team_and_event': self.get_by_team_and_event,
            'get_latest_for_team': self.get_latest_for_team,
            'get_by_event': self.get_by_event,
            'get_by_year': self.get_by_year,
            'search_by_strategy': self.search_by_strategy,
            'get_recent_picklists': self.get_recent_picklists,
            'has_picklist_for_event': self.has_picklist_for_event,
            'delete_old_picklists': self.delete_old_picklists,
        }

    def get_by_team_and_event(self, team_number: int, event_key: str) -> Optional[LockedPicklist]:
        """
        Get picklist for a specific team and event.
        
        Args:
            team_number: Team number
            event_key: Event key
            
        Returns:
            LockedPicklist instance or None
        """
        try:
            return self.db.query(LockedPicklist).filter(
                and_(
                    LockedPicklist.team_number == team_number,
                    LockedPicklist.event_key == event_key
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting picklist for team {team_number} at event {event_key}: {e}")
            raise

    def get_latest_for_team(self, team_number: int, year: Optional[int] = None) -> Optional[LockedPicklist]:
        """
        Get the most recent picklist for a team.
        
        Args:
            team_number: Team number
            year: Optional year filter
            
        Returns:
            Most recent LockedPicklist instance or None
        """
        try:
            query = self.db.query(LockedPicklist).filter(
                LockedPicklist.team_number == team_number
            )
            
            if year:
                query = query.filter(LockedPicklist.year == year)
            
            return query.order_by(desc(LockedPicklist.created_at)).first()
        except Exception as e:
            logger.error(f"Error getting latest picklist for team {team_number}: {e}")
            raise

    def get_by_event(self, event_key: str, year: Optional[int] = None) -> List[LockedPicklist]:
        """
        Get all picklists for a specific event.
        
        Args:
            event_key: Event key
            year: Optional year filter
            
        Returns:
            List of LockedPicklist instances
        """
        try:
            query = self.db.query(LockedPicklist).filter(
                LockedPicklist.event_key == event_key
            )
            
            if year:
                query = query.filter(LockedPicklist.year == year)
            
            return query.order_by(desc(LockedPicklist.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting picklists for event {event_key}: {e}")
            raise

    def get_by_year(self, year: int) -> List[LockedPicklist]:
        """
        Get all picklists for a specific year.
        
        Args:
            year: Competition year
            
        Returns:
            List of LockedPicklist instances
        """
        try:
            return self.db.query(LockedPicklist).filter(
                LockedPicklist.year == year
            ).order_by(desc(LockedPicklist.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting picklists for year {year}: {e}")
            raise

    def search_by_strategy(self, strategy_keywords: List[str], year: Optional[int] = None) -> List[LockedPicklist]:
        """
        Search picklists by strategy prompts containing keywords.
        
        Args:
            strategy_keywords: List of keywords to search for
            year: Optional year filter
            
        Returns:
            List of matching LockedPicklist instances
        """
        try:
            query = self.db.query(LockedPicklist)
            
            if year:
                query = query.filter(LockedPicklist.year == year)
            
            # Search in strategy_prompts JSON field
            for keyword in strategy_keywords:
                # SQLite JSON search - this may need adjustment based on SQLite version
                query = query.filter(
                    LockedPicklist.strategy_prompts.like(f'%{keyword}%')
                )
            
            return query.order_by(desc(LockedPicklist.created_at)).all()
        except Exception as e:
            logger.error(f"Error searching picklists by strategy keywords {strategy_keywords}: {e}")
            raise

    def get_recent_picklists(self, limit: int = 10, team_number: Optional[int] = None) -> List[LockedPicklist]:
        """
        Get recently created picklists.
        
        Args:
            limit: Maximum number of picklists to return
            team_number: Optional team filter
            
        Returns:
            List of recent LockedPicklist instances
        """
        try:
            query = self.db.query(LockedPicklist)
            
            if team_number:
                query = query.filter(LockedPicklist.team_number == team_number)
            
            return query.order_by(desc(LockedPicklist.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent picklists: {e}")
            raise

    def has_picklist_for_event(self, team_number: int, event_key: str) -> bool:
        """
        Check if a team has a picklist for a specific event.
        
        Args:
            team_number: Team number
            event_key: Event key
            
        Returns:
            True if picklist exists, False otherwise
        """
        try:
            return self.db.query(LockedPicklist).filter(
                and_(
                    LockedPicklist.team_number == team_number,
                    LockedPicklist.event_key == event_key
                )
            ).first() is not None
        except Exception as e:
            logger.error(f"Error checking picklist existence for team {team_number} at event {event_key}: {e}")
            raise

    def delete_old_picklists(self, days_old: int = 365) -> int:
        """
        Delete picklists older than specified number of days.
        
        Args:
            days_old: Number of days to keep picklists
            
        Returns:
            Number of deleted picklists
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            count = self.db.query(LockedPicklist).filter(
                LockedPicklist.created_at < cutoff_date
            ).count()
            
            self.db.query(LockedPicklist).filter(
                LockedPicklist.created_at < cutoff_date
            ).delete()
            
            self.db.flush()
            logger.info(f"Deleted {count} old picklists (older than {days_old} days)")
            return count
        except Exception as e:
            logger.error(f"Error deleting old picklists: {e}")
            self.db.rollback()
            raise

    def get_picklist_stats(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics about picklists.
        
        Args:
            year: Optional year filter
            
        Returns:
            Dictionary with picklist statistics
        """
        try:
            query = self.db.query(LockedPicklist)
            
            if year:
                query = query.filter(LockedPicklist.year == year)
            
            total_count = query.count()
            
            # Count unique teams
            unique_teams = len(set(
                p.team_number for p in query.with_entities(LockedPicklist.team_number).all()
            ))
            
            # Count unique events
            unique_events = len(set(
                p.event_key for p in query.with_entities(LockedPicklist.event_key).all()
            ))
            
            # Get most recent picklist
            latest_picklist = query.order_by(desc(LockedPicklist.created_at)).first()
            latest_date = latest_picklist.created_at if latest_picklist else None
            
            return {
                'total_picklists': total_count,
                'unique_teams': unique_teams,
                'unique_events': unique_events,
                'latest_picklist_date': latest_date,
                'year_filter': year,
            }
        except Exception as e:
            logger.error(f"Error getting picklist stats: {e}")
            raise