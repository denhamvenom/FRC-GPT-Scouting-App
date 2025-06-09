# backend/app/database/seeds/default_data.py
"""
Default Data Seeding

Provides utilities for seeding the database with default configuration data
and test data for development and testing purposes.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import SessionLocal
from app.database.models import (
    LockedPicklist,
    AllianceSelection,
    Alliance,
    TeamSelectionStatus,
    ArchivedEvent,
    SheetConfiguration,
    GameManual,
)

logger = logging.getLogger(__name__)


class SeedManager:
    """Manages database seeding operations."""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize seed manager.
        
        Args:
            db: Optional database session
        """
        self.db = db or SessionLocal()
        self._external_session = db is not None

    def close(self):
        """Close database session if we own it."""
        if not self._external_session:
            self.db.close()

    def seed_default_sheet_configurations(self) -> int:
        """
        Seed default sheet configurations.
        
        Returns:
            Number of configurations created
        """
        try:
            default_configs = [
                {
                    'name': 'Default 2025 Configuration',
                    'spreadsheet_id': 'PLACEHOLDER_SPREADSHEET_ID',
                    'match_scouting_sheet': 'Match Scouting',
                    'pit_scouting_sheet': 'Pit Scouting',
                    'super_scouting_sheet': 'Super Scouting',
                    'event_key': '2025demo',
                    'year': 2025,
                    'is_active': False,
                    'match_scouting_headers': [
                        'Team Number', 'Match Number', 'Alliance Color',
                        'Auto Points', 'Teleop Points', 'Endgame Points'
                    ],
                    'pit_scouting_headers': [
                        'Team Number', 'Robot Weight', 'Drive Train',
                        'Programming Language', 'Special Features'
                    ],
                    'super_scouting_headers': [
                        'Team Number', 'Overall Rating', 'Strategy Notes',
                        'Reliability Score', 'Communication'
                    ]
                }
            ]
            
            created_count = 0
            for config_data in default_configs:
                # Check if config already exists
                existing = self.db.query(SheetConfiguration).filter_by(
                    name=config_data['name']
                ).first()
                
                if not existing:
                    config = SheetConfiguration(**config_data)
                    self.db.add(config)
                    created_count += 1
            
            self.db.commit()
            logger.info(f"Created {created_count} default sheet configurations")
            return created_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error seeding sheet configurations: {e}")
            self.db.rollback()
            return 0

    def seed_test_picklists(self) -> int:
        """
        Seed test picklist data for development.
        
        Returns:
            Number of picklists created
        """
        try:
            test_picklists = [
                {
                    'team_number': 1234,
                    'event_key': '2025demo',
                    'year': 2025,
                    'first_pick_data': [
                        {'team_number': 5678, 'nickname': 'Test Team A', 'score': 95.5, 'reasoning': 'Strong autonomous'},
                        {'team_number': 9012, 'nickname': 'Test Team B', 'score': 92.3, 'reasoning': 'Reliable scorer'},
                        {'team_number': 3456, 'nickname': 'Test Team C', 'score': 89.7, 'reasoning': 'Good defense'},
                    ],
                    'second_pick_data': [
                        {'team_number': 7890, 'nickname': 'Test Team D', 'score': 87.2, 'reasoning': 'Versatile robot'},
                        {'team_number': 2345, 'nickname': 'Test Team E', 'score': 85.1, 'reasoning': 'Strong endgame'},
                        {'team_number': 6789, 'nickname': 'Test Team F', 'score': 82.9, 'reasoning': 'Consistent performance'},
                    ],
                    'third_pick_data': [
                        {'team_number': 4567, 'nickname': 'Test Team G', 'score': 78.5, 'reasoning': 'Good backup option'},
                        {'team_number': 8901, 'nickname': 'Test Team H', 'score': 76.3, 'reasoning': 'Defensive specialist'},
                    ],
                    'excluded_teams': [1111, 2222],
                    'strategy_prompts': {
                        'first_pick': 'Focus on high-scoring autonomous robots',
                        'second_pick': 'Look for consistent teleop performance',
                        'third_pick': 'Prioritize defensive capabilities'
                    }
                },
                {
                    'team_number': 5678,
                    'event_key': '2025demo',
                    'year': 2025,
                    'first_pick_data': [
                        {'team_number': 1234, 'nickname': 'Test Team 1234', 'score': 94.2, 'reasoning': 'Excellent all-around'},
                        {'team_number': 9012, 'nickname': 'Test Team B', 'score': 91.8, 'reasoning': 'Strong scorer'},
                        {'team_number': 7890, 'nickname': 'Test Team D', 'score': 88.5, 'reasoning': 'Versatile'},
                    ],
                    'second_pick_data': [
                        {'team_number': 3456, 'nickname': 'Test Team C', 'score': 86.7, 'reasoning': 'Good strategy'},
                        {'team_number': 2345, 'nickname': 'Test Team E', 'score': 84.3, 'reasoning': 'Reliable'},
                        {'team_number': 6789, 'nickname': 'Test Team F', 'score': 81.9, 'reasoning': 'Consistent'},
                    ],
                    'excluded_teams': [3333],
                    'strategy_prompts': {
                        'first_pick': 'Prioritize versatile robots',
                        'second_pick': 'Look for strategic gameplay'
                    }
                }
            ]
            
            created_count = 0
            for picklist_data in test_picklists:
                # Check if picklist already exists
                existing = self.db.query(LockedPicklist).filter_by(
                    team_number=picklist_data['team_number'],
                    event_key=picklist_data['event_key']
                ).first()
                
                if not existing:
                    picklist = LockedPicklist(**picklist_data)
                    self.db.add(picklist)
                    created_count += 1
            
            self.db.commit()
            logger.info(f"Created {created_count} test picklists")
            return created_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error seeding test picklists: {e}")
            self.db.rollback()
            return 0

    def seed_test_alliance_selection(self) -> int:
        """
        Seed test alliance selection data.
        
        Returns:
            Number of selections created
        """
        try:
            # Create alliance selection
            selection_data = {
                'event_key': '2025demo',
                'year': 2025,
                'is_completed': False,
                'current_round': 1,
            }
            
            existing_selection = self.db.query(AllianceSelection).filter_by(
                event_key=selection_data['event_key'],
                year=selection_data['year']
            ).first()
            
            if existing_selection:
                logger.info("Test alliance selection already exists")
                return 0
            
            selection = AllianceSelection(**selection_data)
            self.db.add(selection)
            self.db.flush()  # Get the ID
            
            # Create test teams
            test_teams = [1234, 5678, 9012, 3456, 7890, 2345, 6789, 4567, 8901, 1111, 2222, 3333]
            
            for team_number in test_teams:
                team_status = TeamSelectionStatus(
                    selection_id=selection.id,
                    team_number=team_number,
                    is_captain=False,
                    is_picked=False,
                    has_declined=False
                )
                self.db.add(team_status)
            
            # Create 8 empty alliances
            for alliance_number in range(1, 9):
                alliance = Alliance(
                    selection_id=selection.id,
                    alliance_number=alliance_number,
                    captain_team_number=0,
                    first_pick_team_number=0,
                    second_pick_team_number=0,
                    backup_team_number=0
                )
                self.db.add(alliance)
            
            self.db.commit()
            logger.info("Created test alliance selection with teams and alliances")
            return 1
            
        except SQLAlchemyError as e:
            logger.error(f"Error seeding test alliance selection: {e}")
            self.db.rollback()
            return 0

    def seed_test_archived_events(self) -> int:
        """
        Seed test archived event data.
        
        Returns:
            Number of archives created
        """
        try:
            test_archives = [
                {
                    'name': 'Demo Event 2024 Archive',
                    'event_key': '2024demo',
                    'year': 2024,
                    'archive_data': b'{"sample": "archive data"}',
                    'archive_metadata': {
                        'tables_archived': ['LockedPicklist', 'AllianceSelection'],
                        'record_counts': {'LockedPicklist': 5, 'AllianceSelection': 1},
                        'archive_size_bytes': 1024
                    },
                    'is_active': False,
                    'notes': 'Test archive for development purposes'
                },
                {
                    'name': 'Current Demo Event',
                    'event_key': '2025demo',
                    'year': 2025,
                    'archive_data': b'{"current": "event data"}',
                    'archive_metadata': {
                        'tables_archived': ['LockedPicklist', 'AllianceSelection', 'SheetConfiguration'],
                        'record_counts': {'LockedPicklist': 2, 'AllianceSelection': 1, 'SheetConfiguration': 1},
                        'archive_size_bytes': 2048
                    },
                    'is_active': True,
                    'notes': 'Current active event archive'
                }
            ]
            
            created_count = 0
            for archive_data in test_archives:
                # Check if archive already exists
                existing = self.db.query(ArchivedEvent).filter_by(
                    name=archive_data['name']
                ).first()
                
                if not existing:
                    # If this is set as active, deactivate others first
                    if archive_data.get('is_active', False):
                        self.db.query(ArchivedEvent).update({'is_active': False})
                    
                    archive = ArchivedEvent(**archive_data)
                    self.db.add(archive)
                    created_count += 1
            
            self.db.commit()
            logger.info(f"Created {created_count} test archived events")
            return created_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error seeding test archived events: {e}")
            self.db.rollback()
            return 0

    def clear_all_test_data(self) -> Dict[str, int]:
        """
        Clear all test data from the database.
        
        Returns:
            Dictionary with counts of deleted records
        """
        try:
            deleted_counts = {}
            
            # Delete in reverse dependency order
            deleted_counts['team_statuses'] = self.db.query(TeamSelectionStatus).delete()
            deleted_counts['alliances'] = self.db.query(Alliance).delete()
            deleted_counts['alliance_selections'] = self.db.query(AllianceSelection).delete()
            deleted_counts['picklists'] = self.db.query(LockedPicklist).delete()
            deleted_counts['archived_events'] = self.db.query(ArchivedEvent).delete()
            deleted_counts['sheet_configurations'] = self.db.query(SheetConfiguration).delete()
            deleted_counts['game_manuals'] = self.db.query(GameManual).delete()
            
            self.db.commit()
            
            total_deleted = sum(deleted_counts.values())
            logger.info(f"Cleared {total_deleted} total records from database")
            
            return deleted_counts
            
        except SQLAlchemyError as e:
            logger.error(f"Error clearing test data: {e}")
            self.db.rollback()
            return {}

    def get_database_stats(self) -> Dict[str, int]:
        """
        Get current database statistics.
        
        Returns:
            Dictionary with record counts for each table
        """
        try:
            stats = {}
            
            stats['locked_picklists'] = self.db.query(LockedPicklist).count()
            stats['alliance_selections'] = self.db.query(AllianceSelection).count()
            stats['alliances'] = self.db.query(Alliance).count()
            stats['team_selection_statuses'] = self.db.query(TeamSelectionStatus).count()
            stats['archived_events'] = self.db.query(ArchivedEvent).count()
            stats['sheet_configurations'] = self.db.query(SheetConfiguration).count()
            stats['game_manuals'] = self.db.query(GameManual).count()
            
            return stats
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def seed_all_default_data(self) -> Dict[str, int]:
        """
        Seed all default data.
        
        Returns:
            Dictionary with counts of created records
        """
        try:
            results = {}
            
            results['sheet_configurations'] = self.seed_default_sheet_configurations()
            
            logger.info(f"Seeded all default data: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error seeding all default data: {e}")
            return {}

    def seed_all_test_data(self) -> Dict[str, int]:
        """
        Seed all test data for development.
        
        Returns:
            Dictionary with counts of created records
        """
        try:
            results = {}
            
            results['sheet_configurations'] = self.seed_default_sheet_configurations()
            results['picklists'] = self.seed_test_picklists()
            results['alliance_selections'] = self.seed_test_alliance_selection()
            results['archived_events'] = self.seed_test_archived_events()
            
            logger.info(f"Seeded all test data: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error seeding all test data: {e}")
            return {}


# Global functions for easy access
def seed_default_data() -> Dict[str, int]:
    """Seed default application data."""
    with SeedManager() as manager:
        return manager.seed_all_default_data()


def seed_test_data() -> Dict[str, int]:
    """Seed test data for development."""
    with SeedManager() as manager:
        return manager.seed_all_test_data()


def clear_all_data() -> Dict[str, int]:
    """Clear all data from the database."""
    with SeedManager() as manager:
        return manager.clear_all_test_data()


def get_seed_status() -> Dict[str, Any]:
    """Get current database seeding status."""
    with SeedManager() as manager:
        return {
            'database_stats': manager.get_database_stats(),
            'timestamp': datetime.now().isoformat(),
        }