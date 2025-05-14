# Database Migration Guide

This guide explains how to run database migrations for schema changes.

## Current Migrations

### 1. LockedPicklist Table Migration (May 2025)

This migration adds two new columns to the `locked_picklists` table:
- `excluded_teams`: Stores teams that were excluded from picklist consideration
- `strategy_prompts`: Stores the original strategy prompts used to generate priorities

These additions ensure that when events are archived, they include all relevant data from the picklist generation process.

## Running the Migration

To run the migration:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Run the migration script:
   ```bash
   python migrate_locked_picklist.py
   ```

3. Verify the migration completed successfully:
   - Check for the "✅ Migration completed successfully" message
   - Review the generated log file in the same directory

## How Migrations Work

The migration scripts use SQLite's ALTER TABLE command to add new columns to existing tables. The process is designed to be:

1. **Non-destructive**: Existing data is preserved
2. **Idempotent**: Safe to run multiple times (will not add columns that already exist)
3. **Backward compatible**: Default values are provided for new columns

## Notes for Developers

When adding new columns to database models:

1. Update the model in `app/database/models.py`
2. Create a migration script if the table already exists in production
3. Test the migration in a development environment before applying to production
4. Document the migration in this file

## Troubleshooting

If you encounter issues during migration:

1. Check the generated log file for detailed error messages
2. Ensure the database is not locked by another process
3. Verify you have write permissions to the database file

For assistance, please contact the development team.