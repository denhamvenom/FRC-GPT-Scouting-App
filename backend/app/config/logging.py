# Logging Configuration and Setup

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import json
from datetime import datetime

from .settings import get_settings


class LoggingConfig:
    """Centralized logging configuration manager"""
    
    def __init__(self):
        self.settings = get_settings().logging
        self._configured = False
        self._loggers: Dict[str, logging.Logger] = {}
    
    def configure_logging(self, force_reconfigure: bool = False):
        """Configure application-wide logging"""
        if self._configured and not force_reconfigure:
            return
        
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set root log level
        root_logger.setLevel(self.settings.log_level)
        
        # Create formatters
        console_formatter = self._create_console_formatter()
        file_formatter = self._create_file_formatter()
        
        # Configure console logging
        if self.settings.enable_console_logging:
            console_handler = self._create_console_handler(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Configure file logging
        if self.settings.enable_file_logging:
            file_handler = self._create_file_handler(file_formatter)
            root_logger.addHandler(file_handler)
        
        # Configure specific loggers
        self._configure_specific_loggers()
        
        self._configured = True
        logging.info("Logging configuration completed")
    
    def _create_console_formatter(self) -> logging.Formatter:
        """Create console log formatter with colors"""
        
        class ColoredFormatter(logging.Formatter):
            """Custom formatter with colors for different log levels"""
            
            # ANSI color codes
            COLORS = {
                'DEBUG': '\033[36m',      # Cyan
                'INFO': '\033[32m',       # Green
                'WARNING': '\033[33m',    # Yellow
                'ERROR': '\033[31m',      # Red
                'CRITICAL': '\033[35m',   # Magenta
                'RESET': '\033[0m'        # Reset
            }
            
            def format(self, record):
                # Add color to level name
                if record.levelname in self.COLORS:
                    record.levelname = (
                        f"{self.COLORS[record.levelname]}{record.levelname}"
                        f"{self.COLORS['RESET']}"
                    )
                
                return super().format(record)
        
        # Simpler format for console
        console_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        return ColoredFormatter(console_format, datefmt="%H:%M:%S")
    
    def _create_file_formatter(self) -> logging.Formatter:
        """Create file log formatter"""
        return logging.Formatter(
            self.settings.log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def _create_console_handler(self, formatter: logging.Formatter) -> logging.StreamHandler:
        """Create console handler"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(self.settings.log_level)
        return handler
    
    def _create_file_handler(self, formatter: logging.Formatter) -> logging.handlers.RotatingFileHandler:
        """Create rotating file handler"""
        log_file = Path(self.settings.log_dir) / "app.log"
        
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self.settings.log_file_max_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=self.settings.log_file_backup_count,
            encoding="utf-8"
        )
        handler.setFormatter(formatter)
        handler.setLevel(self.settings.log_level)
        return handler
    
    def _configure_specific_loggers(self):
        """Configure specific loggers for different components"""
        
        # External API loggers (reduce noise)
        external_loggers = [
            "httpx",
            "httpcore",
            "urllib3",
            "requests",
            "gspread",
            "google",
            "openai",
        ]
        
        for logger_name in external_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)  # Only show warnings and errors
        
        # Application component loggers
        app_loggers = {
            "app.services": logging.INFO,
            "app.api": logging.INFO,
            "app.database": logging.INFO,
            "app.cache": logging.INFO,
        }
        
        for logger_name, level in app_loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            self._loggers[logger_name] = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        if not self._configured:
            self.configure_logging()
        
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]
    
    def create_service_logger(self, service_name: str) -> logging.Logger:
        """Create a specialized logger for a service with file handler"""
        if not self._configured:
            self.configure_logging()
        
        logger_name = f"app.services.{service_name}"
        logger = logging.getLogger(logger_name)
        
        # Check if service-specific file handler already exists
        service_file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                if service_name in handler.baseFilename:
                    service_file_handler = handler
                    break
        
        if not service_file_handler:
            # Create service-specific log file
            service_log_file = Path(self.settings.log_dir) / f"{service_name}.log"
            
            service_file_handler = logging.handlers.RotatingFileHandler(
                filename=service_log_file,
                maxBytes=self.settings.log_file_max_size_mb * 1024 * 1024,
                backupCount=self.settings.log_file_backup_count,
                encoding="utf-8"
            )
            
            # Use file formatter
            service_file_handler.setFormatter(self._create_file_formatter())
            service_file_handler.setLevel(self.settings.log_level)
            
            logger.addHandler(service_file_handler)
        
        self._loggers[logger_name] = logger
        return logger
    
    def get_log_files(self) -> Dict[str, Any]:
        """Get information about all log files"""
        log_dir = Path(self.settings.log_dir)
        if not log_dir.exists():
            return {}
        
        log_files = {}
        for log_file in log_dir.glob("*.log*"):
            try:
                stat = log_file.stat()
                log_files[log_file.name] = {
                    "path": str(log_file),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_current": not any(char.isdigit() for char in log_file.suffix)
                }
            except Exception as e:
                log_files[log_file.name] = {"error": str(e)}
        
        return log_files
    
    def tail_log_file(self, filename: str, lines: int = 100) -> str:
        """Get the last N lines from a log file"""
        log_file = Path(self.settings.log_dir) / filename
        
        if not log_file.exists():
            return f"Log file '{filename}' not found"
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # Read all lines and return the last N
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log file: {e}"
    
    def search_logs(self, query: str, filename: Optional[str] = None, max_lines: int = 1000) -> Dict[str, Any]:
        """Search for a query in log files"""
        log_dir = Path(self.settings.log_dir)
        results = {
            "query": query,
            "files_searched": [],
            "matches": [],
            "total_matches": 0
        }
        
        # Determine which files to search
        if filename:
            files_to_search = [log_dir / filename] if (log_dir / filename).exists() else []
        else:
            files_to_search = list(log_dir.glob("*.log"))
        
        for log_file in files_to_search:
            results["files_searched"].append(log_file.name)
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            results["matches"].append({
                                "file": log_file.name,
                                "line_number": line_num,
                                "content": line.strip()
                            })
                            results["total_matches"] += 1
                            
                            if len(results["matches"]) >= max_lines:
                                break
                    
                    if len(results["matches"]) >= max_lines:
                        break
                        
            except Exception as e:
                results["matches"].append({
                    "file": log_file.name,
                    "error": f"Error searching file: {e}"
                })
        
        return results
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old log files"""
        log_dir = Path(self.settings.log_dir)
        if not log_dir.exists():
            return {"error": "Log directory does not exist"}
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleaned_files = []
        errors = []
        total_size_freed = 0
        
        for log_file in log_dir.glob("*.log.*"):  # Backup files only
            try:
                stat = log_file.stat()
                modified_date = datetime.fromtimestamp(stat.st_mtime)
                
                if modified_date < cutoff_date:
                    size = stat.st_size
                    log_file.unlink()
                    cleaned_files.append({
                        "file": log_file.name,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "modified": modified_date.isoformat()
                    })
                    total_size_freed += size
                    
            except Exception as e:
                errors.append(f"Error cleaning {log_file.name}: {e}")
        
        return {
            "cleaned_files": cleaned_files,
            "total_files_cleaned": len(cleaned_files),
            "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
            "errors": errors,
            "days_to_keep": days_to_keep
        }
    
    def get_logging_stats(self) -> Dict[str, Any]:
        """Get logging system statistics"""
        return {
            "configuration": {
                "log_level": self.settings.log_level,
                "log_dir": self.settings.log_dir,
                "console_logging": self.settings.enable_console_logging,
                "file_logging": self.settings.enable_file_logging,
                "max_file_size_mb": self.settings.log_file_max_size_mb,
                "backup_count": self.settings.log_file_backup_count,
            },
            "loggers": {
                "configured_count": len(self._loggers),
                "logger_names": list(self._loggers.keys()),
            },
            "log_files": self.get_log_files(),
            "is_configured": self._configured,
        }


# Global logging configuration instance
logging_config = LoggingConfig()


def get_logging_config() -> LoggingConfig:
    """Get the global logging configuration instance"""
    return logging_config


def setup_logging(force_reconfigure: bool = False):
    """Setup application logging"""
    logging_config.configure_logging(force_reconfigure)


def get_app_logger(name: str) -> logging.Logger:
    """Get an application logger with the specified name"""
    return logging_config.get_logger(name)


def get_service_logger(service_name: str) -> logging.Logger:
    """Get a service-specific logger with file handler"""
    return logging_config.create_service_logger(service_name)