# Database Configuration and Setup

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from .settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.settings = get_settings().database
        self._engine = None
        self._SessionLocal = None
        
    @property
    def engine(self):
        """Get or create database engine"""
        if self._engine is None:
            self._create_engine()
        return self._engine
    
    @property
    def SessionLocal(self):
        """Get or create session factory"""
        if self._SessionLocal is None:
            self._create_session_factory()
        return self._SessionLocal
    
    def _create_engine(self):
        """Create SQLAlchemy engine with optimized settings"""
        connect_args = {}
        
        # SQLite-specific optimizations
        if self.settings.database_url.startswith("sqlite"):
            connect_args.update({
                "check_same_thread": False,  # Allow multiple threads
                "timeout": self.settings.pool_timeout,
            })
            
            # Use StaticPool for SQLite to maintain connections
            self._engine = create_engine(
                self.settings.database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
                pool_pre_ping=True,
                echo=self.settings.echo_sql,
            )
        else:
            # PostgreSQL/MySQL settings
            self._engine = create_engine(
                self.settings.database_url,
                pool_size=self.settings.pool_size,
                pool_timeout=self.settings.pool_timeout,
                pool_pre_ping=True,
                echo=self.settings.echo_sql,
            )
        
        # Set up SQLite optimizations
        if self.settings.database_url.startswith("sqlite"):
            self._setup_sqlite_optimizations()
            
        logger.info(f"Database engine created for: {self.settings.database_url}")
    
    def _create_session_factory(self):
        """Create session factory"""
        self._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _setup_sqlite_optimizations(self):
        """Set up SQLite-specific optimizations"""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance"""
            cursor = dbapi_connection.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Optimize synchronous mode
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Set cache size (negative value = KB)
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Set temp store to memory
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            # Optimize locking mode
            cursor.execute("PRAGMA locking_mode=NORMAL")
            
            cursor.close()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            from ..database.models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            from ..database.models import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            from sqlalchemy import text
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """Get database information and statistics"""
        try:
            from sqlalchemy import text
            with self.session_scope() as session:
                if self.settings.database_url.startswith("sqlite"):
                    # SQLite-specific queries
                    result = session.execute(text("PRAGMA database_list")).fetchall()
                    tables = session.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table'")
                    ).fetchall()
                    
                    return {
                        "type": "SQLite",
                        "path": self.settings.database_path,
                        "databases": [dict(row) for row in result],
                        "tables": [row[0] for row in tables],
                        "connection_url": self.settings.database_url,
                    }
                else:
                    # Generic database info
                    return {
                        "type": "SQL Database",
                        "connection_url": self.settings.database_url,
                    }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database (SQLite only)"""
        if not self.settings.database_url.startswith("sqlite"):
            logger.warning("Database backup only supported for SQLite")
            return False
        
        try:
            import shutil
            from pathlib import Path
            
            source_path = Path(self.settings.database_path)
            backup_path = Path(backup_path)
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy database file
            shutil.copy2(source_path, backup_path)
            
            logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup (SQLite only)"""
        if not self.settings.database_url.startswith("sqlite"):
            logger.warning("Database restore only supported for SQLite")
            return False
        
        try:
            import shutil
            from pathlib import Path
            
            backup_path = Path(backup_path)
            target_path = Path(self.settings.database_path)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Close all connections
            self._engine.dispose()
            
            # Copy backup to target location
            shutil.copy2(backup_path, target_path)
            
            # Recreate engine
            self._engine = None
            self._SessionLocal = None
            
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def get_table_sizes(self) -> dict:
        """Get size information for all tables"""
        try:
            from sqlalchemy import text
            with self.session_scope() as session:
                if self.settings.database_url.startswith("sqlite"):
                    # SQLite table sizes
                    tables = session.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table'")
                    ).fetchall()
                    
                    sizes = {}
                    for table in tables:
                        table_name = table[0]
                        count = session.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        ).scalar()
                        sizes[table_name] = {"row_count": count}
                    
                    return sizes
                else:
                    return {"error": "Table size info only available for SQLite"}
        except Exception as e:
            logger.error(f"Failed to get table sizes: {e}")
            return {"error": str(e)}


# Global database configuration instance
db_config = DatabaseConfig()


def get_database() -> DatabaseConfig:
    """Get the global database configuration instance"""
    return db_config


def get_db_session() -> Generator[Session, None, None]:
    """Dependency injection function for database sessions"""
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()


def init_database():
    """Initialize database with tables"""
    db_config.create_tables()


def close_database():
    """Close database connections"""
    if db_config._engine:
        db_config._engine.dispose()
    logger.info("Database connections closed")