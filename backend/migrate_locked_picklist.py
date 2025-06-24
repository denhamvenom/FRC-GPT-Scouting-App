#!/usr/bin/env python3
# backend/migrate_locked_picklist.py
#
# Migration script to add new columns to LockedPicklist table
# This script adds 'excluded_teams' and 'strategy_prompts' columns to support
# archiving additional picklist data.

import os
import sqlite3
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f"migrate_locked_picklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger("migration")

# Get database path
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "scouting_app.db")


def run_migration():
    """Adds new columns to LockedPicklist table"""
    logger.info(f"Starting migration for database: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found: {DB_PATH}")
        return False

    # Connect to database
    try:
        logger.info("Connecting to database")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the LockedPicklist table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='locked_picklists'"
        )
        if not cursor.fetchone():
            logger.error("Table 'locked_picklists' does not exist")
            conn.close()
            return False

        # Check if excluded_teams column already exists
        cursor.execute("PRAGMA table_info(locked_picklists)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add excluded_teams column if it doesn't exist
        if "excluded_teams" not in columns:
            logger.info("Adding 'excluded_teams' column to locked_picklists table")
            cursor.execute("ALTER TABLE locked_picklists ADD COLUMN excluded_teams TEXT")
        else:
            logger.info("Column 'excluded_teams' already exists")

        # Add strategy_prompts column if it doesn't exist
        if "strategy_prompts" not in columns:
            logger.info("Adding 'strategy_prompts' column to locked_picklists table")
            cursor.execute("ALTER TABLE locked_picklists ADD COLUMN strategy_prompts TEXT")
        else:
            logger.info("Column 'strategy_prompts' already exists")

        # Update any existing records with default values (empty JSON arrays/objects)
        logger.info("Updating existing records with default values")
        cursor.execute(
            "UPDATE locked_picklists SET excluded_teams = ?, strategy_prompts = ? WHERE excluded_teams IS NULL",
            (json.dumps([]), json.dumps({})),
        )

        # Commit changes and close connection
        conn.commit()
        affected_rows = cursor.rowcount
        logger.info(f"Updated {affected_rows} existing records with default values")
        conn.close()

        logger.info("Migration completed successfully")
        return True

    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        if conn:
            conn.close()
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if conn:
            conn.close()
        return False


if __name__ == "__main__":
    if run_migration():
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed, see log for details")
