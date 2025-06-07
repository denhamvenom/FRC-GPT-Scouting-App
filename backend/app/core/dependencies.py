# Dependency Injection Setup and FastAPI Dependencies

from typing import Generator, Dict, Any
from functools import lru_cache
import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

# Configuration imports
from ..config.settings import get_settings, Settings
from ..config.database import get_db_session, get_database, DatabaseConfig
from ..config.external_apis import (
    get_api_config, 
    get_tba_config, 
    get_statbotics_config,
    get_openai_client,
    get_google_client,
    get_openai_config,
    ExternalAPIConfig
)
from ..config.logging import get_logging_config, get_service_logger, LoggingConfig
from ..config.validators import get_config_validator, ConfigurationValidator

# Service imports (will be updated as services are refactored)
from ..services.cache_service import CacheService
from ..services.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration Dependencies
# =============================================================================

@lru_cache()
def get_cached_settings() -> Settings:
    """Get cached application settings (singleton)"""
    return get_settings()


def get_app_settings() -> Settings:
    """FastAPI dependency for application settings"""
    return get_cached_settings()


def get_db_config() -> DatabaseConfig:
    """FastAPI dependency for database configuration"""
    return get_database()


def get_external_api_config() -> ExternalAPIConfig:
    """FastAPI dependency for external API configuration"""
    return get_api_config()


def get_logging_service() -> LoggingConfig:
    """FastAPI dependency for logging configuration"""
    return get_logging_config()


def get_validator() -> ConfigurationValidator:
    """FastAPI dependency for configuration validator"""
    return get_config_validator()


# =============================================================================
# Database Dependencies
# =============================================================================

def get_database_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions with proper cleanup"""
    session = None
    try:
        db_config = get_database()
        session = db_config.get_session()
        yield session
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Database session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
    finally:
        if session:
            session.close()


def get_database_session_factory():
    """Get database session factory for manual session management"""
    return get_database().SessionLocal


# =============================================================================
# External API Client Dependencies
# =============================================================================

def get_tba_api_config() -> Dict[str, Any]:
    """FastAPI dependency for TBA configuration"""
    try:
        return get_tba_config()
    except Exception as e:
        logger.error(f"Failed to get TBA config: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TBA API configuration unavailable"
        )


def get_statbotics_api_config() -> Dict[str, Any]:
    """FastAPI dependency for Statbotics configuration"""
    try:
        return get_statbotics_config()
    except Exception as e:
        logger.error(f"Failed to get Statbotics config: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Statbotics API configuration unavailable"
        )


def get_openai_api_client():
    """FastAPI dependency for OpenAI client"""
    try:
        return get_openai_client()
    except Exception as e:
        logger.error(f"Failed to get OpenAI client: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API client unavailable"
        )


def get_google_sheets_client():
    """FastAPI dependency for Google Sheets client"""
    try:
        return get_google_client()
    except Exception as e:
        logger.error(f"Failed to get Google Sheets client: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Sheets API client unavailable"
        )


def get_openai_configuration() -> Dict[str, Any]:
    """FastAPI dependency for OpenAI configuration"""
    try:
        return get_openai_config()
    except Exception as e:
        logger.error(f"Failed to get OpenAI configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI configuration unavailable"
        )


# =============================================================================
# Service Dependencies
# =============================================================================

@lru_cache()
def get_cache_service() -> CacheService:
    """Get cached CacheService instance (singleton)"""
    settings = get_cached_settings()
    return CacheService(
        cache_dir=settings.cache.cache_dir,
        default_ttl_hours=settings.cache.default_ttl_hours,
        max_cache_size_mb=settings.cache.max_cache_size_mb,
        cleanup_interval_hours=settings.cache.cleanup_interval_hours,
        enable_compression=settings.cache.enable_compression
    )


def get_cache_dependency() -> CacheService:
    """FastAPI dependency for cache service"""
    return get_cache_service()


@lru_cache()
def get_progress_tracker() -> ProgressTracker:
    """Get cached ProgressTracker instance (singleton)"""
    settings = get_cached_settings()
    return ProgressTracker(
        cleanup_hours=settings.app.progress_cleanup_hours,
        max_operations=settings.app.max_progress_operations
    )


def get_progress_dependency() -> ProgressTracker:
    """FastAPI dependency for progress tracker"""
    return get_progress_tracker()


# =============================================================================
# Logger Dependencies
# =============================================================================

def get_api_logger() -> logging.Logger:
    """Get logger for API endpoints"""
    return get_service_logger("api")


def get_service_logger_factory():
    """Factory function for creating service loggers"""
    def create_logger(service_name: str) -> logging.Logger:
        return get_service_logger(service_name)
    return create_logger


# =============================================================================
# Configuration Health Check Dependencies
# =============================================================================

def verify_configuration_health():
    """Dependency to verify configuration health before processing requests"""
    try:
        validator = get_config_validator()
        health_check = validator.quick_health_check()
        
        if health_check["status"] != "healthy":
            logger.warning(f"Configuration health check failed: {health_check}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="System configuration is unhealthy"
            )
        
        return health_check
    except Exception as e:
        logger.error(f"Configuration health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration health check failed"
        )


def verify_database_health():
    """Dependency to verify database health"""
    try:
        db_config = get_database()
        if not db_config.test_connection():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable"
            )
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database health check failed"
        )


def verify_external_apis_health():
    """Dependency to verify external APIs health (optional)"""
    try:
        api_config = get_external_api_config()
        connection_results = api_config.test_connections()
        
        # Log warnings for failed connections but don't block requests
        failed_apis = [api for api, success in connection_results.items() if not success]
        if failed_apis:
            logger.warning(f"Some external APIs are unavailable: {failed_apis}")
        
        return connection_results
    except Exception as e:
        logger.error(f"External API health check error: {e}")
        return {}


# =============================================================================
# Composite Dependencies
# =============================================================================

class AppDependencies:
    """Container for all application dependencies"""
    
    def __init__(
        self,
        settings: Settings = Depends(get_app_settings),
        db_session: Session = Depends(get_database_session),
        cache_service: CacheService = Depends(get_cache_dependency),
        progress_tracker: ProgressTracker = Depends(get_progress_dependency),
        logger: logging.Logger = Depends(get_api_logger),
    ):
        self.settings = settings
        self.db_session = db_session
        self.cache_service = cache_service
        self.progress_tracker = progress_tracker
        self.logger = logger


class ExternalAPIDependencies:
    """Container for external API dependencies"""
    
    def __init__(
        self,
        tba_config: Dict[str, Any] = Depends(get_tba_api_config),
        statbotics_config: Dict[str, Any] = Depends(get_statbotics_api_config),
        openai_client=Depends(get_openai_api_client),
        openai_config: Dict[str, Any] = Depends(get_openai_configuration),
    ):
        self.tba_config = tba_config
        self.statbotics_config = statbotics_config
        self.openai_client = openai_client
        self.openai_config = openai_config


# Optional Google Sheets dependency (may not always be available)
def get_optional_google_sheets_client():
    """Optional Google Sheets client dependency"""
    try:
        return get_google_sheets_client()
    except HTTPException:
        logger.info("Google Sheets client unavailable, continuing without it")
        return None


class ServiceDependencies:
    """Container for service-layer dependencies"""
    
    def __init__(
        self,
        app_deps: AppDependencies = Depends(AppDependencies),
        api_deps: ExternalAPIDependencies = Depends(ExternalAPIDependencies),
        google_client=Depends(get_optional_google_sheets_client),
    ):
        self.app = app_deps
        self.apis = api_deps
        self.google_client = google_client


# =============================================================================
# Initialization and Cleanup
# =============================================================================

def initialize_dependencies():
    """Initialize all dependency singletons"""
    logger.info("Initializing application dependencies...")
    
    try:
        # Initialize configuration
        settings = get_cached_settings()
        logger.info(f"Settings loaded for environment: {settings.app.environment}")
        
        # Initialize database
        db_config = get_database()
        if db_config.test_connection():
            logger.info("Database connection verified")
        else:
            logger.error("Database connection failed")
        
        # Initialize cache service
        cache_service = get_cache_service()
        logger.info("Cache service initialized")
        
        # Initialize progress tracker
        progress_tracker = get_progress_tracker()
        logger.info("Progress tracker initialized")
        
        # Initialize logging
        logging_config = get_logging_service()
        logging_config.configure_logging()
        logger.info("Logging configuration applied")
        
        # Test external APIs (non-blocking)
        try:
            api_config = get_external_api_config()
            connection_results = api_config.test_connections()
            working_apis = [api for api, success in connection_results.items() if success]
            logger.info(f"External APIs initialized: {working_apis}")
        except Exception as e:
            logger.warning(f"External API initialization warning: {e}")
        
        logger.info("All dependencies initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Dependency initialization failed: {e}")
        return False


def cleanup_dependencies():
    """Cleanup resources on application shutdown"""
    logger.info("Cleaning up application dependencies...")
    
    try:
        # Close database connections
        db_config = get_database()
        if db_config._engine:
            db_config._engine.dispose()
            logger.info("Database connections closed")
        
        # Cleanup cache if needed
        cache_service = get_cache_service()
        # Add any cache cleanup logic here
        
        # Cleanup progress tracker
        progress_tracker = get_progress_tracker()
        # Add any progress tracker cleanup logic here
        
        logger.info("Dependencies cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during dependency cleanup: {e}")


# =============================================================================
# Health Check Utilities
# =============================================================================

def get_dependency_health() -> Dict[str, Any]:
    """Get health status of all dependencies"""
    health_status = {
        "timestamp": "unknown",
        "overall_status": "unknown",
        "dependencies": {}
    }
    
    try:
        # Configuration validator
        validator = get_config_validator()
        health_check = validator.quick_health_check()
        health_status.update(health_check)
        
        # Additional dependency-specific checks
        health_status["dependencies"]["cache_service"] = "✓"  # Cache service is always available
        health_status["dependencies"]["progress_tracker"] = "✓"  # Progress tracker is always available
        
        # External API status
        try:
            api_config = get_external_api_config()
            api_health = api_config.test_connections()
            health_status["dependencies"]["external_apis"] = api_health
        except Exception:
            health_status["dependencies"]["external_apis"] = "error"
        
    except Exception as e:
        health_status["overall_status"] = "error"
        health_status["error"] = str(e)
    
    return health_status