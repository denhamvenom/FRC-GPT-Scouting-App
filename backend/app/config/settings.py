# Centralized Configuration Management using Pydantic Settings

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    # SQLite settings
    database_url: str = Field(
        default="sqlite:///./data/scouting_app.db",
        description="Database connection URL"
    )
    database_path: str = Field(
        default="./data/scouting_app.db", 
        description="SQLite database file path"
    )
    echo_sql: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    pool_size: int = Field(
        default=20,
        description="Database connection pool size"
    )
    pool_timeout: int = Field(
        default=30,
        description="Database connection pool timeout in seconds"
    )
    
    @field_validator("database_path")
    @classmethod
    def validate_database_path(cls, v):
        # Ensure the directory exists if possible
        try:
            db_path = Path(v)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return str(db_path.resolve())
        except (PermissionError, OSError):
            # If we can't create the directory, just return the path
            return v

    model_config = {"env_prefix": "DB_"}


class OpenAISettings(BaseSettings):
    """OpenAI API configuration settings"""
    
    api_key: str = Field(
        ...,
        description="OpenAI API key (required)"
    )
    model: str = Field(
        default="gpt-4-1106-preview",
        description="Default OpenAI model to use"
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens per request"
    )
    temperature: float = Field(
        default=0.1,
        description="Temperature for AI responses"
    )
    timeout: int = Field(
        default=120,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Custom base URL for OpenAI API"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or v.strip() == "":
            raise ValueError("OpenAI API key is required")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    model_config = {"env_prefix": "OPENAI_"}


class TBASettings(BaseSettings):
    """The Blue Alliance API configuration settings"""
    
    api_key: str = Field(
        ...,
        description="TBA API key (required)"
    )
    base_url: str = Field(
        default="https://www.thebluealliance.com/api/v3",
        description="TBA API base URL"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    cache_duration_hours: int = Field(
        default=24,
        description="Default cache duration in hours"
    )
    user_agent: str = Field(
        default="FRC-GPT-Scouting-App/1.0",
        description="User agent for API requests"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or v.strip() == "":
            raise ValueError("TBA API key is required")
        return v

    model_config = {"env_prefix": "TBA_"}


class GoogleSheetsSettings(BaseSettings):
    """Google Sheets API configuration settings"""
    
    service_account_file: str = Field(
        default="./secrets/google-service-account.json",
        description="Path to Google service account JSON file"
    )
    sheet_id: Optional[str] = Field(
        default=None,
        description="Default Google Sheets ID"
    )
    scopes: List[str] = Field(
        default=["https://www.googleapis.com/auth/spreadsheets"],
        description="Google API scopes"
    )
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    batch_size: int = Field(
        default=1000,
        description="Batch size for bulk operations"
    )
    
    # Base64 encoded parts for service account (fallback)
    b64_part_1: Optional[str] = Field(
        default=None,
        description="Base64 encoded service account part 1"
    )
    b64_part_2: Optional[str] = Field(
        default=None,
        description="Base64 encoded service account part 2"
    )

    @field_validator("service_account_file")
    @classmethod
    def validate_service_account_file(cls, v):
        if v and not Path(v).exists():
            # Create directory if it doesn't exist and we have permission
            try:
                Path(v).parent.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                pass  # Ignore permission errors during validation
        return v

    model_config = {"env_prefix": "GOOGLE_"}


class StatboticsSettings(BaseSettings):
    """Statbotics API configuration settings"""
    
    base_url: str = Field(
        default="https://api.statbotics.io/v2",
        description="Statbotics API base URL"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    cache_duration_hours: int = Field(
        default=8,
        description="Cache duration in hours"
    )
    user_agent: str = Field(
        default="FRC-GPT-Scouting-App/1.0",
        description="User agent for API requests"
    )

    model_config = {"env_prefix": "STATBOTICS_"}


class CacheSettings(BaseSettings):
    """Cache configuration settings"""
    
    cache_dir: str = Field(
        default="./app/cache",
        description="Directory for file cache"
    )
    default_ttl_hours: int = Field(
        default=24,
        description="Default cache TTL in hours"
    )
    max_cache_size_mb: int = Field(
        default=500,
        description="Maximum cache size in MB"
    )
    cleanup_interval_hours: int = Field(
        default=24,
        description="Cache cleanup interval in hours"
    )
    enable_compression: bool = Field(
        default=True,
        description="Enable cache compression"
    )

    @field_validator("cache_dir")
    @classmethod
    def validate_cache_dir(cls, v):
        try:
            cache_path = Path(v)
            cache_path.mkdir(parents=True, exist_ok=True)
            return str(cache_path.resolve())
        except (PermissionError, OSError):
            # If we can't create the directory, just return the path
            return v

    model_config = {"env_prefix": "CACHE_"}


class LoggingSettings(BaseSettings):
    """Logging configuration settings"""
    
    log_level: str = Field(
        default="INFO",
        description="Default log level"
    )
    log_dir: str = Field(
        default="./logs",
        description="Directory for log files"
    )
    log_file_max_size_mb: int = Field(
        default=50,
        description="Maximum log file size in MB"
    )
    log_file_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    enable_console_logging: bool = Field(
        default=True,
        description="Enable console logging"
    )
    enable_file_logging: bool = Field(
        default=True,
        description="Enable file logging"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("log_dir")
    @classmethod
    def validate_log_dir(cls, v):
        try:
            log_path = Path(v)
            log_path.mkdir(parents=True, exist_ok=True)
            return str(log_path.resolve())
        except (PermissionError, OSError):
            # If we can't create the directory, just return the path
            return v

    model_config = {"env_prefix": "LOG_"}


class AppSettings(BaseSettings):
    """Application-wide configuration settings"""
    
    # Application metadata
    app_name: str = Field(
        default="FRC GPT Scouting App",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload in development"
    )
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow CORS credentials"
    )
    
    # Default year and event settings
    default_year: int = Field(
        default=2025,
        description="Default competition year"
    )
    current_event_key: Optional[str] = Field(
        default=None,
        description="Current event key"
    )
    
    # Progress tracking settings
    progress_cleanup_hours: int = Field(
        default=24,
        description="Hours to keep progress tracking data"
    )
    max_progress_operations: int = Field(
        default=100,
        description="Maximum concurrent progress operations"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production", "testing"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    model_config = {"env_prefix": "APP_"}


class Settings(BaseSettings):
    """Main application settings combining all configuration sections"""
    
    # Core application settings
    app: AppSettings = Field(default_factory=AppSettings)
    
    # Database configuration
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    # External API configurations
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    tba: TBASettings = Field(default_factory=TBASettings)
    google_sheets: GoogleSheetsSettings = Field(default_factory=GoogleSheetsSettings)
    statbotics: StatboticsSettings = Field(default_factory=StatboticsSettings)
    
    # Internal service configurations
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @model_validator(mode='before')
    @classmethod
    def validate_settings(cls, values):
        """Cross-validation between different settings sections"""
        # Add any cross-section validation logic here
        return values

    def get_base_paths(self) -> Dict[str, Path]:
        """Get all configured base paths"""
        return {
            "cache_dir": Path(self.cache.cache_dir),
            "log_dir": Path(self.logging.log_dir),
            "database_dir": Path(self.database.database_path).parent,
            "service_account_dir": Path(self.google_sheets.service_account_file).parent,
        }

    def get_data_file_path(self, filename: str, year: Optional[int] = None) -> Path:
        """Get path to data files with year substitution"""
        if year is None:
            year = self.app.default_year
        
        # Replace year placeholder in filename
        if "{year}" in filename:
            filename = filename.format(year=year)
        elif "YEAR" in filename:
            filename = filename.replace("YEAR", str(year))
        
        return Path("./app/data") / filename

    def get_config_file_path(self, filename: str, year: Optional[int] = None) -> Path:
        """Get path to config files with year substitution"""
        if year is None:
            year = self.app.default_year
            
        # Replace year placeholder in filename
        if "{year}" in filename:
            filename = filename.format(year=year)
        elif "YEAR" in filename:
            filename = filename.replace("YEAR", str(year))
        
        return Path("./app/config") / filename

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance (for dependency injection)"""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)"""
    global settings
    settings = Settings()
    return settings