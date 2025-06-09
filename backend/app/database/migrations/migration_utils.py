# backend/app/database/migrations/migration_utils.py
"""
Database Migration Utilities

Provides utilities for managing database schema migrations, including
creating, running, and rolling back migrations.
"""

import os
import json
import logging
import importlib.util
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import engine, SessionLocal, Base

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations and schema changes."""

    def __init__(self, migrations_dir: Optional[str] = None):
        """
        Initialize migration manager.
        
        Args:
            migrations_dir: Directory containing migration scripts
        """
        if migrations_dir is None:
            migrations_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.migrations_dir = Path(migrations_dir)
        self.metadata_file = self.migrations_dir / "migration_metadata.json"
        self._ensure_migrations_table()

    def _ensure_migrations_table(self) -> None:
        """Ensure migrations tracking table exists."""
        try:
            with engine.connect() as conn:
                # Create migrations table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        migration_name TEXT NOT NULL UNIQUE,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        checksum TEXT,
                        rollback_sql TEXT
                    )
                """))
                conn.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error creating migrations table: {e}")
            raise

    def get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migrations.
        
        Returns:
            List of migration names that have been applied
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT migration_name FROM schema_migrations ORDER BY applied_at"
                ))
                return [row[0] for row in result.fetchall()]
        except SQLAlchemyError as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []

    def get_pending_migrations(self) -> List[str]:
        """
        Get list of pending migrations.
        
        Returns:
            List of migration files that haven't been applied
        """
        try:
            applied = set(self.get_applied_migrations())
            
            # Find all migration files
            migration_files = []
            for file_path in self.migrations_dir.glob("*.py"):
                if file_path.name.startswith("migration_") and file_path.name != "__init__.py":
                    migration_name = file_path.stem
                    if migration_name not in applied:
                        migration_files.append(migration_name)
            
            # Sort by timestamp/name
            return sorted(migration_files)
        except Exception as e:
            logger.error(f"Error getting pending migrations: {e}")
            return []

    def create_migration(
        self,
        name: str,
        upgrade_sql: str,
        downgrade_sql: str = "",
        description: str = ""
    ) -> str:
        """
        Create a new migration file.
        
        Args:
            name: Migration name
            upgrade_sql: SQL for applying the migration
            downgrade_sql: SQL for rolling back the migration
            description: Migration description
            
        Returns:
            Created migration filename
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            migration_name = f"migration_{timestamp}_{name}"
            filename = f"{migration_name}.py"
            filepath = self.migrations_dir / filename
            
            migration_template = f'''# {filepath.name}
"""
{description or f"Migration: {name}"}

Created: {datetime.now().isoformat()}
"""

from sqlalchemy import text
from app.database.db import engine

# Migration metadata
MIGRATION_NAME = "{migration_name}"
DESCRIPTION = "{description}"
DEPENDS_ON = []  # List of migration names this depends on

def upgrade():
    """Apply the migration."""
    upgrade_sql = """{upgrade_sql}"""
    
    if upgrade_sql.strip():
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in upgrade_sql.split(';') if stmt.strip()]
            for statement in statements:
                conn.execute(text(statement))
            conn.commit()

def downgrade():
    """Rollback the migration."""
    downgrade_sql = """{downgrade_sql}"""
    
    if downgrade_sql.strip():
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in downgrade_sql.split(';') if stmt.strip()]
            for statement in statements:
                conn.execute(text(statement))
            conn.commit()

def validate():
    """Validate that the migration can be applied."""
    # Add any pre-migration validation logic here
    return True

def get_checksum():
    """Get checksum for migration integrity check."""
    import hashlib
    content = upgrade_sql + downgrade_sql
    return hashlib.md5(content.encode()).hexdigest()
'''
            
            # Write migration file
            with open(filepath, 'w') as f:
                f.write(migration_template)
            
            logger.info(f"Created migration: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error creating migration {name}: {e}")
            raise

    def apply_migration(self, migration_name: str) -> bool:
        """
        Apply a specific migration.
        
        Args:
            migration_name: Name of migration to apply
            
        Returns:
            True if migration was applied successfully
        """
        try:
            # Check if already applied
            applied = self.get_applied_migrations()
            if migration_name in applied:
                logger.info(f"Migration {migration_name} already applied")
                return True
            
            # Load migration module
            migration_file = self.migrations_dir / f"{migration_name}.py"
            if not migration_file.exists():
                logger.error(f"Migration file not found: {migration_file}")
                return False
            
            spec = importlib.util.spec_from_file_location(migration_name, migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Validate migration
            if hasattr(migration_module, 'validate') and not migration_module.validate():
                logger.error(f"Migration validation failed: {migration_name}")
                return False
            
            # Apply migration
            if hasattr(migration_module, 'upgrade'):
                migration_module.upgrade()
                
                # Record in migrations table
                checksum = migration_module.get_checksum() if hasattr(migration_module, 'get_checksum') else ""
                
                # Get downgrade SQL for rollback
                downgrade_sql = ""
                if hasattr(migration_module, 'downgrade'):
                    import inspect
                    downgrade_sql = inspect.getsource(migration_module.downgrade)
                
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO schema_migrations (migration_name, checksum, rollback_sql)
                        VALUES (:name, :checksum, :rollback_sql)
                    """), {
                        'name': migration_name,
                        'checksum': checksum,
                        'rollback_sql': downgrade_sql
                    })
                    conn.commit()
                
                logger.info(f"Successfully applied migration: {migration_name}")
                return True
            else:
                logger.error(f"Migration {migration_name} has no upgrade function")
                return False
                
        except Exception as e:
            logger.error(f"Error applying migration {migration_name}: {e}")
            return False

    def rollback_migration(self, migration_name: str) -> bool:
        """
        Rollback a specific migration.
        
        Args:
            migration_name: Name of migration to rollback
            
        Returns:
            True if migration was rolled back successfully
        """
        try:
            # Check if migration was applied
            applied = self.get_applied_migrations()
            if migration_name not in applied:
                logger.info(f"Migration {migration_name} not applied, nothing to rollback")
                return True
            
            # Load migration module
            migration_file = self.migrations_dir / f"{migration_name}.py"
            if not migration_file.exists():
                logger.error(f"Migration file not found: {migration_file}")
                return False
            
            spec = importlib.util.spec_from_file_location(migration_name, migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Rollback migration
            if hasattr(migration_module, 'downgrade'):
                migration_module.downgrade()
                
                # Remove from migrations table
                with engine.connect() as conn:
                    conn.execute(text("""
                        DELETE FROM schema_migrations WHERE migration_name = :name
                    """), {'name': migration_name})
                    conn.commit()
                
                logger.info(f"Successfully rolled back migration: {migration_name}")
                return True
            else:
                logger.warning(f"Migration {migration_name} has no downgrade function")
                return False
                
        except Exception as e:
            logger.error(f"Error rolling back migration {migration_name}: {e}")
            return False

    def apply_all_pending(self) -> Tuple[int, int]:
        """
        Apply all pending migrations.
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        pending = self.get_pending_migrations()
        successful = 0
        failed = 0
        
        for migration_name in pending:
            if self.apply_migration(migration_name):
                successful += 1
            else:
                failed += 1
                logger.error(f"Stopping migration process due to failure in {migration_name}")
                break
        
        logger.info(f"Migration complete: {successful} successful, {failed} failed")
        return successful, failed

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get current schema information.
        
        Returns:
            Dictionary with schema details
        """
        try:
            inspector = inspect(engine)
            
            # Get table information
            tables = {}
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                tables[table_name] = {
                    'columns': [
                        {
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable'],
                            'default': col.get('default'),
                            'primary_key': col.get('primary_key', False),
                        }
                        for col in columns
                    ],
                    'indexes': [
                        {
                            'name': idx['name'],
                            'columns': idx['column_names'],
                            'unique': idx['unique'],
                        }
                        for idx in indexes
                    ],
                    'foreign_keys': [
                        {
                            'name': fk['name'],
                            'constrained_columns': fk['constrained_columns'],
                            'referred_table': fk['referred_table'],
                            'referred_columns': fk['referred_columns'],
                        }
                        for fk in foreign_keys
                    ]
                }
            
            return {
                'database_url': str(engine.url),
                'tables': tables,
                'applied_migrations': self.get_applied_migrations(),
                'pending_migrations': self.get_pending_migrations(),
            }
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return {}

    def backup_schema(self, backup_file: str) -> bool:
        """
        Create a backup of the current schema.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            True if backup was created successfully
        """
        try:
            schema_info = self.get_schema_info()
            
            with open(backup_file, 'w') as f:
                json.dump(schema_info, f, indent=2, default=str)
            
            logger.info(f"Schema backup created: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Error creating schema backup: {e}")
            return False

    def generate_schema_sql(self) -> str:
        """
        Generate SQL to recreate the current schema.
        
        Returns:
            SQL string for schema recreation
        """
        try:
            # Use SQLAlchemy metadata to generate schema
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            # Generate CREATE TABLE statements
            from sqlalchemy.schema import CreateTable
            sql_statements = []
            
            for table in metadata.tables.values():
                create_sql = str(CreateTable(table).compile(engine))
                sql_statements.append(create_sql)
            
            return ";\n\n".join(sql_statements) + ";"
        except Exception as e:
            logger.error(f"Error generating schema SQL: {e}")
            return ""


# Global migration manager instance
migration_manager = MigrationManager()


def run_migration(migration_name: str) -> bool:
    """
    Run a specific migration.
    
    Args:
        migration_name: Name of migration to run
        
    Returns:
        True if successful
    """
    return migration_manager.apply_migration(migration_name)


def rollback_migration(migration_name: str) -> bool:
    """
    Rollback a specific migration.
    
    Args:
        migration_name: Name of migration to rollback
        
    Returns:
        True if successful
    """
    return migration_manager.rollback_migration(migration_name)


def get_migration_status() -> Dict[str, Any]:
    """
    Get current migration status.
    
    Returns:
        Dictionary with migration status information
    """
    return {
        'applied_migrations': migration_manager.get_applied_migrations(),
        'pending_migrations': migration_manager.get_pending_migrations(),
        'schema_info': migration_manager.get_schema_info(),
    }


def create_migration_script(
    name: str,
    upgrade_sql: str,
    downgrade_sql: str = "",
    description: str = ""
) -> str:
    """
    Create a new migration script.
    
    Args:
        name: Migration name
        upgrade_sql: SQL for applying migration
        downgrade_sql: SQL for rolling back migration
        description: Migration description
        
    Returns:
        Created migration filename
    """
    return migration_manager.create_migration(name, upgrade_sql, downgrade_sql, description)