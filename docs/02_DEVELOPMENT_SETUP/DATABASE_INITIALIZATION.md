# Database Initialization and Management

**Purpose**: Database setup, schema management, and data operations  
**Audience**: Developers, data managers, and AI assistants  
**Scope**: Development, testing, and production database configurations  

---

## Database Overview

The FRC GPT Scouting App uses a **hybrid data storage approach** combining structured database storage with flexible JSON datasets. This provides both relational data integrity and the flexibility needed for varying scouting data formats.

### Storage Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    DATA STORAGE LAYER                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  SQLite/    │  │    JSON     │  │  In-Memory  │        │
│  │ PostgreSQL  │  │   Files     │  │   Cache     │        │
│  │             │  │             │  │             │        │
│  │ • Teams     │  │ • Datasets  │  │ • Sessions  │        │
│  │ • Events    │  │ • Config    │  │ • Results   │        │
│  │ • Users     │  │ • Context   │  │ • Temp Data │        │
│  │ • Sessions  │  │ • Static    │  │ • Analytics │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

#### Teams Table
```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_number INTEGER UNIQUE NOT NULL,
    nickname VARCHAR(255),
    city VARCHAR(255),
    state_prov VARCHAR(100),
    country VARCHAR(100),
    website VARCHAR(500),
    rookie_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teams_number ON teams(team_number);
CREATE INDEX idx_teams_rookie_year ON teams(rookie_year);
```

#### Events Table
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    event_code VARCHAR(50),
    event_type INTEGER,
    district_key VARCHAR(50),
    city VARCHAR(255),
    state_prov VARCHAR(100),
    country VARCHAR(100),
    start_date DATE,
    end_date DATE,
    year INTEGER,
    week INTEGER,
    address VARCHAR(500),
    postal_code VARCHAR(20),
    lat DECIMAL(10, 8),
    lng DECIMAL(11, 8),
    location_name VARCHAR(255),
    timezone VARCHAR(100),
    website VARCHAR(500),
    webcasts TEXT,  -- JSON array
    division_keys TEXT,  -- JSON array
    playoff_type INTEGER,
    playoff_type_string VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_key ON events(event_key);
CREATE INDEX idx_events_year ON events(year);
CREATE INDEX idx_events_dates ON events(start_date, end_date);
```

#### Analysis Sessions Table
```sql
CREATE TABLE analysis_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    event_key VARCHAR(50),
    dataset_path VARCHAR(500),
    configuration TEXT,  -- JSON configuration
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_sessions_id ON analysis_sessions(session_id);
CREATE INDEX idx_sessions_user ON analysis_sessions(user_id);
CREATE INDEX idx_sessions_status ON analysis_sessions(status);
```

#### Analysis Results Table
```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,
    team_numbers TEXT,  -- JSON array
    parameters TEXT,  -- JSON parameters
    results TEXT,  -- JSON results
    cache_key VARCHAR(200),
    processing_time DECIMAL(10, 3),
    token_usage INTEGER,
    cost_estimate DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_results_session ON analysis_results(session_id);
CREATE INDEX idx_results_cache_key ON analysis_results(cache_key);
CREATE INDEX idx_results_type ON analysis_results(analysis_type);
```

#### Performance Metrics Table
```sql
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(200),
    method VARCHAR(10),
    response_time DECIMAL(10, 3),
    status_code INTEGER,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    error_message TEXT,
    request_size INTEGER,
    response_size INTEGER
);

CREATE INDEX idx_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_metrics_endpoint ON performance_metrics(endpoint);
CREATE INDEX idx_metrics_response_time ON performance_metrics(response_time);
```

---

## Database Models (SQLAlchemy)

### Team Model
```python
# app/models/team.py
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_number = Column(Integer, unique=True, nullable=False, index=True)
    nickname = Column(String(255))
    city = Column(String(255))
    state_prov = Column(String(100))
    country = Column(String(100))
    website = Column(String(500))
    rookie_year = Column(Integer, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Team(team_number={self.team_number}, nickname='{self.nickname}')>"
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "team_number": self.team_number,
            "nickname": self.nickname,
            "city": self.city,
            "state_prov": self.state_prov,
            "country": self.country,
            "website": self.website,
            "rookie_year": self.rookie_year,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
```

### Event Model
```python
# app/models/event.py
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    event_code = Column(String(50))
    event_type = Column(Integer)
    city = Column(String(255))
    state_prov = Column(String(100))
    country = Column(String(100))
    start_date = Column(Date, index=True)
    end_date = Column(Date, index=True)
    year = Column(Integer, index=True)
    week = Column(Integer)
    website = Column(String(500))
    webcasts = Column(Text)  # JSON array
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def get_webcasts(self):
        """Get webcasts as Python list."""
        if self.webcasts:
            return json.loads(self.webcasts)
        return []
    
    def set_webcasts(self, webcasts_list):
        """Set webcasts from Python list."""
        self.webcasts = json.dumps(webcasts_list) if webcasts_list else None
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_key": self.event_key,
            "name": self.name,
            "event_code": self.event_code,
            "event_type": self.event_type,
            "city": self.city,
            "state_prov": self.state_prov,
            "country": self.country,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "year": self.year,
            "week": self.week,
            "website": self.website,
            "webcasts": self.get_webcasts(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
```

### Analysis Session Model
```python
# app/models/analysis_session.py
from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
import json
import uuid

Base = declarative_base()

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), index=True)
    event_key = Column(String(50))
    dataset_path = Column(String(500))
    configuration = Column(Text)  # JSON configuration
    status = Column(String(50), default='active', index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
    
    def get_configuration(self):
        """Get configuration as Python dict."""
        if self.configuration:
            return json.loads(self.configuration)
        return {}
    
    def set_configuration(self, config_dict):
        """Set configuration from Python dict."""
        self.configuration = json.dumps(config_dict) if config_dict else None
    
    def is_expired(self):
        """Check if session is expired."""
        if self.expires_at:
            from datetime import datetime
            return datetime.now() > self.expires_at
        return False
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "event_key": self.event_key,
            "dataset_path": self.dataset_path,
            "configuration": self.get_configuration(),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired()
        }
```

---

## Database Initialization

### Development Database Setup

**Database Initialization Script** (`app/database/init_db.py`):
```python
#!/usr/bin/env python3
"""Database initialization script for development."""

import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models.base import Base
from app.models.team import Team
from app.models.event import Event
from app.models.analysis_session import AnalysisSession
from app.models.analysis_result import AnalysisResult
from app.models.performance_metric import PerformanceMetric

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_directory():
    """Create database directory if it doesn't exist."""
    settings = get_settings()
    if settings.database_url.startswith('sqlite'):
        db_path = settings.database_url.replace('sqlite:///', '')
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created database directory: {db_dir}")

def initialize_database():
    """Initialize database with all tables."""
    try:
        settings = get_settings()
        engine = create_engine(settings.database_url)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create database session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Add any initial data
        add_initial_data(session)
        
        session.close()
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def add_initial_data(session):
    """Add initial data to database."""
    try:
        # Check if we already have data
        existing_teams = session.query(Team).count()
        if existing_teams > 0:
            logger.info("Database already contains data, skipping initial data")
            return
        
        # Add sample teams for development
        sample_teams = [
            Team(team_number=254, nickname="The Cheesy Poofs", city="San Jose", state_prov="CA", country="USA", rookie_year=1999),
            Team(team_number=1678, nickname="Citrus Circuits", city="Davis", state_prov="CA", country="USA", rookie_year=2005),
            Team(team_number=148, nickname="Robowranglers", city="Greenville", state_prov="TX", country="USA", rookie_year=1992),
            Team(team_number=1323, nickname="MadTown Robotics", city="Madison", state_prov="WI", country="USA", rookie_year=2004),
            Team(team_number=2056, nickname="OP Robotics", city="Overland Park", state_prov="KS", country="USA", rookie_year=2007)
        ]
        
        for team in sample_teams:
            session.add(team)
        
        # Add sample event
        from datetime import date
        sample_event = Event(
            event_key="2024week1",
            name="Week 1 Test Event",
            event_code="week1",
            city="Test City",
            state_prov="TS",
            country="USA",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 3),
            year=2024,
            week=1
        )
        session.add(sample_event)
        
        session.commit()
        logger.info("Initial sample data added successfully")
        
    except Exception as e:
        logger.error(f"Failed to add initial data: {e}")
        session.rollback()
        raise

if __name__ == "__main__":
    create_database_directory()
    initialize_database()
```

**Run Database Initialization**:
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Run initialization
python -m app.database.init_db

# Verify database creation
ls -la app/data/
# Should show scouting_app.db file
```

### Production Database Setup

**PostgreSQL Setup Script** (`scripts/setup_postgres.py`):
```python
#!/usr/bin/env python3
"""Production PostgreSQL database setup."""

import logging
import os
from sqlalchemy import create_engine, text
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_postgres_database():
    """Set up PostgreSQL database for production."""
    settings = get_settings()
    
    # Connect to postgres database to create app database
    postgres_url = settings.database_url.replace('/scouting_app', '/postgres')
    engine = create_engine(postgres_url)
    
    with engine.connect() as conn:
        # Enable autocommit for database creation
        conn.execute(text("COMMIT"))
        
        # Create database if it doesn't exist
        result = conn.execute(text(
            "SELECT 1 FROM pg_database WHERE datname = 'scouting_app'"
        ))
        
        if not result.fetchone():
            conn.execute(text("CREATE DATABASE scouting_app"))
            logger.info("Created scouting_app database")
        else:
            logger.info("Database scouting_app already exists")
    
    # Connect to app database and create tables
    app_engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=app_engine)
    logger.info("Created all tables in scouting_app database")

if __name__ == "__main__":
    setup_postgres_database()
```

---

## Sample Data Loading

### Development Sample Data

**Sample Dataset** (`app/data/sample_dataset.json`):
```json
{
  "teams": [
    {
      "team_number": 254,
      "nickname": "The Cheesy Poofs",
      "autonomous_score": 18.5,
      "teleop_avg_points": 55.2,
      "endgame_points": 20.0,
      "defense_rating": 4.8,
      "reliability_score": 0.92,
      "matches_played": 12,
      "wins": 10,
      "losses": 2,
      "ties": 0,
      "opr": 65.3,
      "dpr": 8.2,
      "ccwm": 57.1
    },
    {
      "team_number": 1678,
      "nickname": "Citrus Circuits", 
      "autonomous_score": 16.8,
      "teleop_avg_points": 52.1,
      "endgame_points": 18.5,
      "defense_rating": 3.9,
      "reliability_score": 0.88,
      "matches_played": 11,
      "wins": 9,
      "losses": 2,
      "ties": 0,
      "opr": 62.1,
      "dpr": 7.8,
      "ccwm": 54.3
    },
    {
      "team_number": 148,
      "nickname": "Robowranglers",
      "autonomous_score": 15.2,
      "teleop_avg_points": 48.7,
      "endgame_points": 22.0,
      "defense_rating": 4.2,
      "reliability_score": 0.85,
      "matches_played": 10,
      "wins": 7,
      "losses": 3,
      "ties": 0,
      "opr": 58.9,
      "dpr": 9.1,
      "ccwm": 49.8
    }
  ],
  "context": "2024 FIRST Robotics Competition - Crescendo",
  "game_info": "Teams score by placing notes in the Speaker and Amp, with bonus points for harmony and trap scoring in the endgame.",
  "event_info": {
    "name": "2024 Week 1 Sample Event",
    "location": "Test Venue",
    "date": "2024-03-01"
  },
  "metadata": {
    "created_by": "FRC GPT Scouting App",
    "version": "1.0",
    "last_updated": "2024-03-01T10:00:00Z"
  }
}
```

**Load Sample Data Script** (`app/database/load_sample_data.py`):
```python
#!/usr/bin/env python3
"""Load sample data for development and testing."""

import json
import logging
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from app.database import get_engine, get_db
from app.models.team import Team
from app.models.event import Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sample_teams(session, dataset_path: str):
    """Load sample teams from JSON dataset."""
    try:
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        teams_data = data.get('teams', [])
        loaded_count = 0
        
        for team_data in teams_data:
            # Check if team already exists
            existing_team = session.query(Team).filter_by(
                team_number=team_data['team_number']
            ).first()
            
            if existing_team:
                logger.info(f"Team {team_data['team_number']} already exists, skipping")
                continue
            
            # Create new team
            team = Team(
                team_number=team_data['team_number'],
                nickname=team_data.get('nickname', ''),
                # Add other fields as needed
            )
            
            session.add(team)
            loaded_count += 1
        
        session.commit()
        logger.info(f"Loaded {loaded_count} teams from {dataset_path}")
        
    except Exception as e:
        logger.error(f"Failed to load sample teams: {e}")
        session.rollback()
        raise

def load_sample_event(session, dataset_path: str):
    """Load sample event from JSON dataset."""
    try:
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        event_info = data.get('event_info', {})
        if not event_info:
            logger.info("No event info in dataset, skipping event creation")
            return
        
        # Create event key from name
        event_key = event_info.get('name', '').lower().replace(' ', '_').replace('-', '_')
        
        # Check if event already exists
        existing_event = session.query(Event).filter_by(event_key=event_key).first()
        if existing_event:
            logger.info(f"Event {event_key} already exists, skipping")
            return
        
        # Create new event
        from datetime import datetime
        event_date = datetime.fromisoformat(event_info.get('date', '2024-01-01'))
        
        event = Event(
            event_key=event_key,
            name=event_info.get('name', 'Sample Event'),
            city=event_info.get('location', 'Test City'),
            start_date=event_date.date(),
            end_date=event_date.date(),
            year=event_date.year
        )
        
        session.add(event)
        session.commit()
        logger.info(f"Created event: {event.name}")
        
    except Exception as e:
        logger.error(f"Failed to load sample event: {e}")
        session.rollback()
        raise

def load_all_sample_data():
    """Load all sample data for development."""
    # Get database session
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Load sample dataset
        sample_path = Path(__file__).parent.parent / "data" / "sample_dataset.json"
        if sample_path.exists():
            load_sample_teams(session, str(sample_path))
            load_sample_event(session, str(sample_path))
        else:
            logger.warning(f"Sample dataset not found at {sample_path}")
        
        logger.info("Sample data loading completed")
        
    finally:
        session.close()

if __name__ == "__main__":
    load_all_sample_data()
```

---

## Database Migrations

### Migration System

**Migration Base** (`app/database/migrations/base.py`):
```python
"""Database migration base classes."""

import logging
from abc import ABC, abstractmethod
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class Migration(ABC):
    """Base class for database migrations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Migration version identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Migration description."""
        pass
    
    @abstractmethod
    def upgrade(self):
        """Apply migration."""
        pass
    
    @abstractmethod
    def downgrade(self):
        """Rollback migration."""
        pass
    
    def execute_sql(self, sql: str):
        """Execute raw SQL."""
        self.session.execute(text(sql))
        self.session.commit()
        logger.info(f"Executed SQL: {sql[:100]}...")

class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, session: Session):
        self.session = session
        self.migrations = []
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.session.execute(text(sql))
        self.session.commit()
    
    def register_migration(self, migration_class):
        """Register a migration."""
        self.migrations.append(migration_class)
    
    def get_applied_migrations(self):
        """Get list of applied migrations."""
        result = self.session.execute(
            text("SELECT version FROM schema_migrations ORDER BY applied_at")
        )
        return [row[0] for row in result.fetchall()]
    
    def apply_migration(self, migration: Migration):
        """Apply a single migration."""
        try:
            migration.upgrade()
            
            # Record migration as applied
            self.session.execute(
                text("INSERT INTO schema_migrations (version, description) VALUES (:version, :description)"),
                {"version": migration.version, "description": migration.description}
            )
            self.session.commit()
            
            logger.info(f"Applied migration {migration.version}: {migration.description}")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Migration {migration.version} failed: {e}")
            raise
    
    def run_migrations(self):
        """Run all pending migrations."""
        applied = set(self.get_applied_migrations())
        
        for migration_class in sorted(self.migrations, key=lambda m: m.version):
            migration = migration_class(self.session)
            
            if migration.version not in applied:
                self.apply_migration(migration)
            else:
                logger.info(f"Migration {migration.version} already applied, skipping")
```

**Example Migration** (`app/database/migrations/001_add_performance_indexes.py`):
```python
"""Add performance indexes to improve query speed."""

from .base import Migration

class AddPerformanceIndexes(Migration):
    version = "001"
    description = "Add performance indexes for common queries"
    
    def upgrade(self):
        """Add indexes for better performance."""
        # Index for team lookups by number
        self.execute_sql("CREATE INDEX IF NOT EXISTS idx_teams_number_perf ON teams(team_number)")
        
        # Index for analysis results by session and type
        self.execute_sql("CREATE INDEX IF NOT EXISTS idx_results_session_type ON analysis_results(session_id, analysis_type)")
        
        # Index for performance metrics by timestamp
        self.execute_sql("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp_perf ON performance_metrics(timestamp DESC)")
        
        # Composite index for common event queries
        self.execute_sql("CREATE INDEX IF NOT EXISTS idx_events_year_week ON events(year, week)")
    
    def downgrade(self):
        """Remove performance indexes."""
        self.execute_sql("DROP INDEX IF EXISTS idx_teams_number_perf")
        self.execute_sql("DROP INDEX IF EXISTS idx_results_session_type")
        self.execute_sql("DROP INDEX IF EXISTS idx_metrics_timestamp_perf")
        self.execute_sql("DROP INDEX IF EXISTS idx_events_year_week")
```

**Run Migrations** (`app/database/migrate.py`):
```python
#!/usr/bin/env python3
"""Run database migrations."""

import logging
from sqlalchemy.orm import sessionmaker
from app.database import get_engine
from app.database.migrations.base import MigrationManager
from app.database.migrations.001_add_performance_indexes import AddPerformanceIndexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run all database migrations."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        manager = MigrationManager(session)
        
        # Register all migrations
        manager.register_migration(AddPerformanceIndexes)
        
        # Run migrations
        manager.run_migrations()
        
        logger.info("All migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migrations()
```

---

## Database Operations

### Backup and Restore

**SQLite Backup Script** (`scripts/backup_sqlite.py`):
```python
#!/usr/bin/env python3
"""Backup SQLite database."""

import shutil
import logging
from datetime import datetime
from pathlib import Path
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_sqlite_database():
    """Create backup of SQLite database."""
    settings = get_settings()
    
    if not settings.database_url.startswith('sqlite'):
        logger.error("This script is only for SQLite databases")
        return
    
    # Get database path
    db_path = Path(settings.database_url.replace('sqlite:///', ''))
    
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return
    
    # Create backup directory
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"scouting_app_backup_{timestamp}.db"
    
    # Copy database file
    shutil.copy2(db_path, backup_path)
    
    logger.info(f"Database backed up to: {backup_path}")
    logger.info(f"Backup size: {backup_path.stat().st_size / 1024:.1f} KB")
    
    return backup_path

if __name__ == "__main__":
    backup_sqlite_database()
```

**PostgreSQL Backup Script** (`scripts/backup_postgres.py`):
```python
#!/usr/bin/env python3
"""Backup PostgreSQL database."""

import subprocess
import logging
from datetime import datetime
from pathlib import Path
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_postgres_database():
    """Create backup of PostgreSQL database using pg_dump."""
    settings = get_settings()
    
    # Parse database URL
    # Format: postgresql://user:password@host:port/database
    url_parts = settings.database_url.replace('postgresql://', '').split('/')
    db_name = url_parts[-1]
    connection_parts = url_parts[0].split('@')
    auth_parts = connection_parts[0].split(':')
    host_parts = connection_parts[1].split(':')
    
    username = auth_parts[0]
    password = auth_parts[1] if len(auth_parts) > 1 else None
    host = host_parts[0]
    port = host_parts[1] if len(host_parts) > 1 else '5432'
    
    # Create backup directory
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"scouting_app_backup_{timestamp}.sql"
    
    # Build pg_dump command
    cmd = [
        'pg_dump',
        '--host', host,
        '--port', port,
        '--username', username,
        '--dbname', db_name,
        '--file', str(backup_path),
        '--verbose'
    ]
    
    # Set password environment variable if provided
    env = None
    if password:
        import os
        env = os.environ.copy()
        env['PGPASSWORD'] = password
    
    try:
        # Run pg_dump
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Database backed up to: {backup_path}")
            logger.info(f"Backup size: {backup_path.stat().st_size / 1024:.1f} KB")
            return backup_path
        else:
            logger.error(f"Backup failed: {result.stderr}")
            return None
            
    except FileNotFoundError:
        logger.error("pg_dump not found. Please install PostgreSQL client tools.")
        return None

if __name__ == "__main__":
    backup_postgres_database()
```

### Data Maintenance

**Database Cleanup Script** (`scripts/cleanup_database.py`):
```python
#!/usr/bin/env python3
"""Clean up old data from database."""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from app.database import get_engine
from app.models.analysis_session import AnalysisSession
from app.models.analysis_result import AnalysisResult
from app.models.performance_metric import PerformanceMetric

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_expired_sessions(session, days_old=30):
    """Remove expired analysis sessions and their results."""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # Find expired sessions
    expired_sessions = session.query(AnalysisSession).filter(
        AnalysisSession.expires_at < datetime.now()
    ).all()
    
    # Find old inactive sessions
    old_sessions = session.query(AnalysisSession).filter(
        AnalysisSession.updated_at < cutoff_date,
        AnalysisSession.status == 'inactive'
    ).all()
    
    all_expired = expired_sessions + old_sessions
    
    if all_expired:
        session_ids = [s.session_id for s in all_expired]
        
        # Delete related results first (foreign key constraint)
        deleted_results = session.query(AnalysisResult).filter(
            AnalysisResult.session_id.in_(session_ids)
        ).delete(synchronize_session=False)
        
        # Delete sessions
        deleted_sessions = session.query(AnalysisSession).filter(
            AnalysisSession.session_id.in_(session_ids)
        ).delete(synchronize_session=False)
        
        session.commit()
        
        logger.info(f"Cleaned up {deleted_sessions} expired sessions and {deleted_results} results")
    else:
        logger.info("No expired sessions to clean up")

def cleanup_old_metrics(session, days_old=90):
    """Remove old performance metrics."""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    deleted_count = session.query(PerformanceMetric).filter(
        PerformanceMetric.timestamp < cutoff_date
    ).delete(synchronize_session=False)
    
    session.commit()
    logger.info(f"Cleaned up {deleted_count} old performance metrics")

def optimize_database(session):
    """Optimize database performance."""
    try:
        # SQLite-specific optimization
        from app.config import get_settings
        settings = get_settings()
        
        if settings.database_url.startswith('sqlite'):
            session.execute(text("VACUUM"))
            session.execute(text("ANALYZE"))
            session.commit()
            logger.info("SQLite database optimized (VACUUM and ANALYZE)")
        else:
            # PostgreSQL optimization
            session.execute(text("VACUUM ANALYZE"))
            session.commit()
            logger.info("PostgreSQL database optimized (VACUUM ANALYZE)")
            
    except Exception as e:
        logger.warning(f"Database optimization failed: {e}")

def run_maintenance():
    """Run all database maintenance tasks."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        logger.info("Starting database maintenance...")
        
        cleanup_expired_sessions(session)
        cleanup_old_metrics(session)
        optimize_database(session)
        
        logger.info("Database maintenance completed successfully")
        
    except Exception as e:
        logger.error(f"Database maintenance failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_maintenance()
```

---

## Testing Database

### Test Database Configuration

**Test Database Setup** (`tests/conftest.py`):
```python
"""Pytest configuration and fixtures."""

import pytest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.database import get_db

@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database."""
    # Create temporary database file
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{temp_db.name}")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    import os
    os.unlink(temp_db.name)

@pytest.fixture(scope="function")
def sample_teams(test_db):
    """Create sample teams for testing."""
    from app.models.team import Team
    
    teams = [
        Team(team_number=254, nickname="The Cheesy Poofs"),
        Team(team_number=1678, nickname="Citrus Circuits"),
        Team(team_number=148, nickname="Robowranglers")
    ]
    
    for team in teams:
        test_db.add(team)
    test_db.commit()
    
    return teams

@pytest.fixture(scope="function")
def sample_event(test_db):
    """Create sample event for testing."""
    from app.models.event import Event
    from datetime import date
    
    event = Event(
        event_key="2024test",
        name="Test Event",
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 3),
        year=2024
    )
    
    test_db.add(event)
    test_db.commit()
    
    return event
```

**Database Tests** (`tests/test_database.py`):
```python
"""Test database operations."""

import pytest
from app.models.team import Team
from app.models.event import Event
from app.models.analysis_session import AnalysisSession

def test_create_team(test_db):
    """Test creating a team."""
    team = Team(team_number=1234, nickname="Test Team")
    test_db.add(team)
    test_db.commit()
    
    # Verify team was created
    retrieved_team = test_db.query(Team).filter_by(team_number=1234).first()
    assert retrieved_team is not None
    assert retrieved_team.nickname == "Test Team"

def test_team_to_dict(sample_teams):
    """Test team dictionary conversion."""
    team = sample_teams[0]
    team_dict = team.to_dict()
    
    assert team_dict['team_number'] == 254
    assert team_dict['nickname'] == "The Cheesy Poofs"
    assert 'created_at' in team_dict

def test_analysis_session_configuration(test_db):
    """Test analysis session configuration handling."""
    config = {"priorities": [{"metric": "auto", "weight": 0.3}]}
    
    session = AnalysisSession(user_id="test_user")
    session.set_configuration(config)
    test_db.add(session)
    test_db.commit()
    
    # Retrieve and verify
    retrieved_session = test_db.query(AnalysisSession).filter_by(
        session_id=session.session_id
    ).first()
    
    assert retrieved_session.get_configuration() == config

def test_event_webcasts(test_db):
    """Test event webcasts JSON handling."""
    webcasts = [
        {"type": "youtube", "channel": "firstinspires"},
        {"type": "twitch", "channel": "firstinspires"}
    ]
    
    event = Event(
        event_key="2024webcasts",
        name="Webcasts Test Event",
        year=2024
    )
    event.set_webcasts(webcasts)
    test_db.add(event)
    test_db.commit()
    
    # Retrieve and verify
    retrieved_event = test_db.query(Event).filter_by(
        event_key="2024webcasts"
    ).first()
    
    assert retrieved_event.get_webcasts() == webcasts
```

---

## Production Database Configuration

### PostgreSQL Production Setup

**Production Environment Variables**:
```env
# Production database configuration
DATABASE_URL=postgresql://scouting_user:secure_password@localhost:5432/scouting_app
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

**Connection Pool Configuration** (`app/database/connection.py`):
```python
"""Database connection management for production."""

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from app.config import get_settings

def create_production_engine():
    """Create production database engine with connection pooling."""
    settings = get_settings()
    
    return create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_recycle=settings.database_pool_recycle,
        echo=False,  # Set to True for SQL debugging
        future=True
    )
```

---

## Next Steps

### For Development
1. **[Development Environment](DEVELOPMENT_ENVIRONMENT.md)** - Complete development setup
2. **[Testing Guide](../04_DEVELOPMENT_GUIDES/TESTING_GUIDE.md)** - Database testing strategies
3. **[API Development](../04_DEVELOPMENT_GUIDES/API_DEVELOPMENT.md)** - Database integration patterns

### For Production
1. **[Deployment Guide](../06_OPERATIONS/DEPLOYMENT_GUIDE.md)** - Production database deployment
2. **[Monitoring](../06_OPERATIONS/MONITORING.md)** - Database monitoring
3. **[Backup Strategy](../06_OPERATIONS/BACKUP_RECOVERY.md)** - Production backup procedures

### For AI Development
1. **[Service Contracts](../05_AI_FRAMEWORK/SERVICE_CONTRACTS.md)** - Database service patterns
2. **[AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)** - AI-assisted database development
3. **[Development Patterns](../05_AI_FRAMEWORK/PROMPT_TEMPLATES.md)** - Database operation templates

---

**Last Updated**: June 25, 2025  
**Maintainer**: Database Team  
**Related Documents**: [Development Environment](DEVELOPMENT_ENVIRONMENT.md), [Service Architecture](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)