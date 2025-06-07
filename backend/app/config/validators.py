# Configuration Validation and Health Checks

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
import asyncio
import json
from datetime import datetime

from .settings import get_settings
from .database import get_database
from .external_apis import get_api_config

logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Comprehensive configuration validation and health checking"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_config = get_database()
        self.api_config = get_api_config()
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all configuration validations"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "validations": {},
            "warnings": [],
            "errors": [],
            "critical_errors": []
        }
        
        # Run all validation categories
        validation_methods = [
            ("environment", self._validate_environment),
            ("file_system", self._validate_file_system),
            ("database", self._validate_database),
            ("external_apis", self._validate_external_apis),
            ("logging", self._validate_logging),
            ("cache", self._validate_cache),
            ("year_specific", self._validate_year_specific_config),
        ]
        
        for category, method in validation_methods:
            try:
                category_result = method()
                results["validations"][category] = category_result
                
                # Collect warnings and errors
                if "warnings" in category_result:
                    results["warnings"].extend(category_result["warnings"])
                if "errors" in category_result:
                    results["errors"].extend(category_result["errors"])
                if "critical_errors" in category_result:
                    results["critical_errors"].extend(category_result["critical_errors"])
                    
            except Exception as e:
                logger.error(f"Validation failed for {category}: {e}")
                results["validations"][category] = {
                    "status": "error",
                    "error": str(e)
                }
                results["critical_errors"].append(f"{category}: {e}")
        
        # Determine overall status
        if results["critical_errors"]:
            results["overall_status"] = "critical"
        elif results["errors"]:
            results["overall_status"] = "error"
        elif results["warnings"]:
            results["overall_status"] = "warning"
        else:
            results["overall_status"] = "healthy"
        
        return results
    
    def _validate_environment(self) -> Dict[str, Any]:
        """Validate environment variables and settings"""
        result = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "critical_errors": [],
            "details": {}
        }
        
        # Required environment variables
        required_vars = [
            ("OPENAI_API_KEY", self.settings.openai.api_key),
            ("TBA_API_KEY", self.settings.tba.api_key),
        ]
        
        for var_name, var_value in required_vars:
            if not var_value or var_value.strip() == "":
                result["critical_errors"].append(f"Required environment variable {var_name} is not set")
                result["status"] = "critical"
            else:
                result["details"][var_name] = "✓ Set"
        
        # Optional but recommended variables
        optional_vars = [
            ("GOOGLE_SERVICE_ACCOUNT_FILE", self.settings.google_sheets.service_account_file),
            ("GOOGLE_SHEET_ID", self.settings.google_sheets.sheet_id),
        ]
        
        for var_name, var_value in optional_vars:
            if not var_value:
                result["warnings"].append(f"Optional variable {var_name} is not set")
            else:
                result["details"][var_name] = "✓ Set"
        
        # Validate environment setting
        valid_environments = ["development", "staging", "production", "testing"]
        if self.settings.app.environment not in valid_environments:
            result["errors"].append(f"Invalid environment: {self.settings.app.environment}")
        
        # Validate port range
        if not 1 <= self.settings.app.port <= 65535:
            result["errors"].append(f"Invalid port: {self.settings.app.port}")
        
        # Check debug mode in production
        if self.settings.app.environment == "production" and self.settings.app.debug:
            result["warnings"].append("Debug mode is enabled in production environment")
        
        return result
    
    def _validate_file_system(self) -> Dict[str, Any]:
        """Validate file system paths and permissions"""
        result = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "details": {}
        }
        
        # Check all configured directories
        directories_to_check = self.settings.get_base_paths()
        
        for dir_name, dir_path in directories_to_check.items():
            try:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    result["details"][dir_name] = f"✓ Created: {dir_path}"
                else:
                    result["details"][dir_name] = f"✓ Exists: {dir_path}"
                
                # Check write permissions
                test_file = dir_path / ".write_test"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    result["details"][f"{dir_name}_writable"] = "✓ Writable"
                except Exception:
                    result["errors"].append(f"Directory {dir_path} is not writable")
                    result["details"][f"{dir_name}_writable"] = "✗ Not writable"
                    
            except Exception as e:
                result["errors"].append(f"Failed to create/access directory {dir_path}: {e}")
                result["details"][dir_name] = f"✗ Error: {e}"
        
        # Check specific files
        files_to_check = [
            ("google_service_account", Path(self.settings.google_sheets.service_account_file)),
            ("database", Path(self.settings.database.database_path)),
        ]
        
        for file_name, file_path in files_to_check:
            if file_path.exists():
                result["details"][file_name] = f"✓ Exists: {file_path}"
                
                # Check file is readable
                try:
                    file_path.read_text()
                    result["details"][f"{file_name}_readable"] = "✓ Readable"
                except Exception:
                    result["warnings"].append(f"File {file_path} exists but is not readable")
            else:
                if file_name == "google_service_account":
                    result["warnings"].append(f"Google service account file not found: {file_path}")
                else:
                    result["details"][file_name] = f"! Will be created: {file_path}"
        
        return result
    
    def _validate_database(self) -> Dict[str, Any]:
        """Validate database configuration and connectivity"""
        result = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "details": {}
        }
        
        try:
            # Test database connection
            connection_success = self.db_config.test_connection()
            if connection_success:
                result["details"]["connection"] = "✓ Connection successful"
                
                # Get database info
                db_info = self.db_config.get_database_info()
                result["details"]["database_info"] = db_info
                
                # Check tables
                if "tables" in db_info:
                    table_count = len(db_info["tables"])
                    result["details"]["tables"] = f"✓ {table_count} tables found"
                    
                    if table_count == 0:
                        result["warnings"].append("Database has no tables - may need initialization")
                else:
                    result["warnings"].append("Could not retrieve table information")
                
            else:
                result["errors"].append("Database connection failed")
                result["status"] = "error"
                
        except Exception as e:
            result["critical_errors"] = [f"Database validation failed: {e}"]
            result["status"] = "critical"
        
        # Validate database settings
        if self.settings.database.pool_size <= 0:
            result["errors"].append("Invalid database pool size")
        
        if self.settings.database.pool_timeout <= 0:
            result["errors"].append("Invalid database pool timeout")
        
        return result
    
    def _validate_external_apis(self) -> Dict[str, Any]:
        """Validate external API configurations and test connections"""
        result = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "details": {}
        }
        
        try:
            # Test all API connections
            connection_results = self.api_config.test_connections()
            
            for api_name, success in connection_results.items():
                if success:
                    result["details"][f"{api_name}_connection"] = "✓ Connection successful"
                else:
                    result["warnings"].append(f"{api_name} connection failed")
                    result["details"][f"{api_name}_connection"] = "✗ Connection failed"
            
            # Get client information
            client_info = self.api_config.get_client_info()
            result["details"]["client_info"] = client_info
            
            # Validate specific API settings
            if self.settings.openai.temperature < 0 or self.settings.openai.temperature > 2:
                result["errors"].append("Invalid OpenAI temperature setting")
            
            if self.settings.openai.max_tokens <= 0:
                result["errors"].append("Invalid OpenAI max_tokens setting")
            
        except Exception as e:
            result["errors"].append(f"External API validation failed: {e}")
            result["status"] = "error"
        
        return result
    
    def _validate_logging(self) -> Dict[str, Any]:
        """Validate logging configuration"""
        result = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "details": {}
        }
        
        try:
            from .logging import get_logging_config
            log_config = get_logging_config()
            
            # Get logging stats
            log_stats = log_config.get_logging_stats()
            result["details"]["configuration"] = log_stats["configuration"]
            result["details"]["log_files"] = log_stats["log_files"]
            
            # Check log directory
            log_dir = Path(self.settings.logging.log_dir)
            if log_dir.exists() and log_dir.is_dir():
                result["details"]["log_directory"] = f"✓ Exists: {log_dir}"
            else:
                result["warnings"].append(f"Log directory does not exist: {log_dir}")
            
            # Validate log level
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if self.settings.logging.log_level not in valid_levels:
                result["errors"].append(f"Invalid log level: {self.settings.logging.log_level}")
            
            # Check file size limits
            if self.settings.logging.log_file_max_size_mb <= 0:
                result["errors"].append("Invalid log file max size")
            
        except Exception as e:
            result["errors"].append(f"Logging validation failed: {e}")
        
        return result
    
    def _validate_cache(self) -> Dict[str, Any]:
        """Validate cache configuration"""
        result = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "details": {}
        }
        
        # Check cache directory
        cache_dir = Path(self.settings.cache.cache_dir)
        if cache_dir.exists():
            result["details"]["cache_directory"] = f"✓ Exists: {cache_dir}"
            
            # Check cache files
            cache_files = list(cache_dir.glob("*.json"))
            result["details"]["cache_files"] = f"{len(cache_files)} cache files found"
            
            # Calculate cache size
            total_size = sum(f.stat().st_size for f in cache_files)
            size_mb = total_size / (1024 * 1024)
            result["details"]["cache_size_mb"] = round(size_mb, 2)
            
            # Check if cache is approaching size limit
            if size_mb > self.settings.cache.max_cache_size_mb * 0.9:
                result["warnings"].append("Cache size is approaching the configured limit")
            
        else:
            result["warnings"].append(f"Cache directory does not exist: {cache_dir}")
        
        # Validate cache settings
        if self.settings.cache.default_ttl_hours <= 0:
            result["errors"].append("Invalid cache TTL setting")
        
        if self.settings.cache.max_cache_size_mb <= 0:
            result["errors"].append("Invalid cache size limit")
        
        return result
    
    def _validate_year_specific_config(self) -> Dict[str, Any]:
        """Validate year-specific configuration files"""
        result = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "details": {}
        }
        
        current_year = self.settings.app.default_year
        
        # Year-specific files to check
        year_files = [
            f"schema_{current_year}.json",
            f"schema_superscout_{current_year}.json",
            f"critical_mappings_{current_year}.json",
            f"manual_text_{current_year}.json",
            f"robot_groups_{current_year}.json",
            f"statbotics_field_map_{current_year}.json",
        ]
        
        for filename in year_files:
            file_path = self.settings.get_data_file_path(filename)
            config_file_path = self.settings.get_config_file_path(filename)
            
            # Check in both data and config directories
            if file_path.exists():
                result["details"][filename] = f"✓ Found in data: {file_path}"
                
                # Try to parse JSON files
                if filename.endswith('.json'):
                    try:
                        with open(file_path, 'r') as f:
                            json.load(f)
                        result["details"][f"{filename}_valid"] = "✓ Valid JSON"
                    except json.JSONDecodeError as e:
                        result["errors"].append(f"Invalid JSON in {filename}: {e}")
                        
            elif config_file_path.exists():
                result["details"][filename] = f"✓ Found in config: {config_file_path}"
            else:
                result["warnings"].append(f"Year-specific file not found: {filename}")
                result["details"][filename] = "✗ Not found"
        
        return result
    
    def quick_health_check(self) -> Dict[str, Any]:
        """Perform a quick health check of critical components"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "checks": {}
        }
        
        # Database connectivity
        try:
            db_ok = self.db_config.test_connection()
            result["checks"]["database"] = "✓" if db_ok else "✗"
        except Exception:
            result["checks"]["database"] = "✗"
        
        # Critical directories
        try:
            paths = self.settings.get_base_paths()
            all_paths_ok = all(path.exists() for path in paths.values())
            result["checks"]["file_system"] = "✓" if all_paths_ok else "✗"
        except Exception:
            result["checks"]["file_system"] = "✗"
        
        # Required environment variables
        required_ok = bool(
            self.settings.openai.api_key and 
            self.settings.tba.api_key
        )
        result["checks"]["environment"] = "✓" if required_ok else "✗"
        
        # Determine overall status
        if all(check == "✓" for check in result["checks"].values()):
            result["status"] = "healthy"
        else:
            result["status"] = "unhealthy"
        
        return result
    
    def generate_config_report(self) -> Dict[str, Any]:
        """Generate a comprehensive configuration report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": self.validate_all(),
            "configuration_summary": {
                "app": {
                    "name": self.settings.app.app_name,
                    "version": self.settings.app.app_version,
                    "environment": self.settings.app.environment,
                    "debug": self.settings.app.debug,
                    "default_year": self.settings.app.default_year,
                },
                "database": {
                    "type": "SQLite" if self.settings.database.database_url.startswith("sqlite") else "Other",
                    "path": self.settings.database.database_path,
                    "echo_sql": self.settings.database.echo_sql,
                },
                "external_apis": {
                    "openai_model": self.settings.openai.model,
                    "openai_temperature": self.settings.openai.temperature,
                    "tba_base_url": self.settings.tba.base_url,
                    "statbotics_base_url": self.settings.statbotics.base_url,
                },
                "logging": {
                    "level": self.settings.logging.log_level,
                    "console_enabled": self.settings.logging.enable_console_logging,
                    "file_enabled": self.settings.logging.enable_file_logging,
                },
                "cache": {
                    "directory": self.settings.cache.cache_dir,
                    "ttl_hours": self.settings.cache.default_ttl_hours,
                    "max_size_mb": self.settings.cache.max_cache_size_mb,
                }
            }
        }
        
        return report


# Global configuration validator instance
config_validator = ConfigurationValidator()


def get_config_validator() -> ConfigurationValidator:
    """Get the global configuration validator instance"""
    return config_validator


def validate_configuration() -> Dict[str, Any]:
    """Validate all configuration and return results"""
    return config_validator.validate_all()


def quick_health_check() -> Dict[str, Any]:
    """Perform a quick health check"""
    return config_validator.quick_health_check()


def generate_config_report() -> Dict[str, Any]:
    """Generate a comprehensive configuration report"""
    return config_validator.generate_config_report()