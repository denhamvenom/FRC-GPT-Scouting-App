#!/usr/bin/env python3
"""
Database migration script to add custom events and teams tables.

This script creates the new tables for custom event functionality:
- custom_events: Store user-created events for offseason competitions
- custom_teams: Store teams associated with custom events

Run this script after updating the models.py file to add custom event support.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.db import engine, Base
from app.database.models import CustomEvent, CustomTeam
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(table_name: str) -> bool:
    """Check if a table already exists in the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking table existence: {e}")
        return False

def migrate_database():
    """Run the database migration to add custom events tables."""
    try:
        logger.info("Starting database migration for custom events...")
        
        # Check if tables already exist
        custom_events_exists = check_table_exists('custom_events')
        custom_teams_exists = check_table_exists('custom_teams')
        
        if custom_events_exists and custom_teams_exists:
            logger.info("Custom events tables already exist. No migration needed.")
            return True
        
        # Create all tables (this will only create missing ones)
        logger.info("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        custom_events_created = check_table_exists('custom_events')
        custom_teams_created = check_table_exists('custom_teams')
        
        if custom_events_created and custom_teams_created:
            logger.info("✅ Migration completed successfully!")
            logger.info("   - custom_events table created")
            logger.info("   - custom_teams table created")
            return True
        else:
            logger.error("❌ Migration failed - tables were not created properly")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}")
        return False

def verify_migration():
    """Verify the migration was successful by checking table schemas."""
    try:
        logger.info("Verifying migration...")
        
        with engine.connect() as conn:
            # Check custom_events table structure
            result = conn.execute(text("PRAGMA table_info(custom_events);"))
            custom_events_columns = [row[1] for row in result.fetchall()]
            
            # Check custom_teams table structure
            result = conn.execute(text("PRAGMA table_info(custom_teams);"))
            custom_teams_columns = [row[1] for row in result.fetchall()]
            
            # Expected columns
            expected_custom_events = ['id', 'name', 'event_key', 'year', 'is_custom', 'description', 'location', 'created_at', 'updated_at']
            expected_custom_teams = ['id', 'team_number', 'event_key', 'team_name', 'is_secondary_robot', 'has_tba_data', 'created_at', 'updated_at']
            
            # Verify columns exist
            missing_event_cols = [col for col in expected_custom_events if col not in custom_events_columns]
            missing_team_cols = [col for col in expected_custom_teams if col not in custom_teams_columns]
            
            if not missing_event_cols and not missing_team_cols:
                logger.info("✅ Migration verification successful!")
                logger.info(f"   - custom_events columns: {custom_events_columns}")
                logger.info(f"   - custom_teams columns: {custom_teams_columns}")
                return True
            else:
                logger.error("❌ Migration verification failed!")
                if missing_event_cols:
                    logger.error(f"   - Missing custom_events columns: {missing_event_cols}")
                if missing_team_cols:
                    logger.error(f"   - Missing custom_teams columns: {missing_team_cols}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Migration verification failed with error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Custom Events Database Migration")
    logger.info("=" * 50)
    
    # Run migration
    success = migrate_database()
    
    if success:
        # Verify migration
        verification_success = verify_migration()
        
        if verification_success:
            logger.info("=" * 50)
            logger.info("🎉 Migration completed successfully!")
            logger.info("You can now use custom event functionality.")
            sys.exit(0)
        else:
            logger.error("Migration completed but verification failed.")
            sys.exit(1)
    else:
        logger.error("Migration failed.")
        sys.exit(1)