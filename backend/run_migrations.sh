#!/bin/bash
# Run all database migrations in sequence

echo "Starting database migrations..."

# Run Locked Picklist migration
echo "Running LockedPicklist migration..."
python migrate_locked_picklist.py

echo "All migrations completed."
echo "Check the log files for details."