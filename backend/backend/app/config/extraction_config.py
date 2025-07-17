# backend/app/config/extraction_config.py

import os
from typing import Dict, Any, Optional
from app.types.game_context_types import ExtractionConfig


class ExtractionConfigManager:
    """
    Configuration manager for game context extraction.
    
    Handles loading configuration from environment variables and providing
    defaults for the extraction process.
    """
    
    def __init__(self):
        """Initialize configuration manager with environment-based settings."""
        self._config = self._load_config_from_env()
    
    def _load_config_from_env(self) -> ExtractionConfig:
        """
        Load extraction configuration from environment variables.
        
        Returns:
            ExtractionConfig with environment values or defaults
        """
        return ExtractionConfig(
            max_strategic_elements=int(os.getenv("EXTRACTION_MAX_STRATEGIC_ELEMENTS", "10")),
            max_alliance_considerations=int(os.getenv("EXTRACTION_MAX_ALLIANCE_CONSIDERATIONS", "8")),
            max_key_metrics=int(os.getenv("EXTRACTION_MAX_KEY_METRICS", "12")),
            max_game_pieces=int(os.getenv("EXTRACTION_MAX_GAME_PIECES", "6")),
            extraction_temperature=float(os.getenv("EXTRACTION_TEMPERATURE", "0.1")),
            max_extraction_tokens=int(os.getenv("EXTRACTION_MAX_TOKENS", "4000")),
            cache_ttl_hours=int(os.getenv("EXTRACTION_CACHE_TTL_HOURS", "168")),
            validation_threshold=float(os.getenv("EXTRACTION_VALIDATION_THRESHOLD", "0.8"))
        )
    
    @property
    def config(self) -> ExtractionConfig:
        """Get the current extraction configuration."""
        return self._config
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration with new values.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        # Create new config with updated values
        current_values = {
            'max_strategic_elements': self._config.max_strategic_elements,
            'max_alliance_considerations': self._config.max_alliance_considerations,
            'max_key_metrics': self._config.max_key_metrics,
            'max_game_pieces': self._config.max_game_pieces,
            'extraction_temperature': self._config.extraction_temperature,
            'max_extraction_tokens': self._config.max_extraction_tokens,
            'cache_ttl_hours': self._config.cache_ttl_hours,
            'validation_threshold': self._config.validation_threshold
        }
        
        # Update with provided values
        current_values.update(kwargs)
        
        # Create new config
        self._config = ExtractionConfig(**current_values)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary for serialization.
        
        Returns:
            Dictionary representation of current configuration
        """
        return {
            'max_strategic_elements': self._config.max_strategic_elements,
            'max_alliance_considerations': self._config.max_alliance_considerations,
            'max_key_metrics': self._config.max_key_metrics,
            'max_game_pieces': self._config.max_game_pieces,
            'extraction_temperature': self._config.extraction_temperature,
            'max_extraction_tokens': self._config.max_extraction_tokens,
            'cache_ttl_hours': self._config.cache_ttl_hours,
            'validation_threshold': self._config.validation_threshold
        }
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = ExtractionConfig()
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration settings.
        
        Returns:
            Dictionary with validation results and warnings
        """
        issues = []
        warnings = []
        
        # Validate ranges
        if self._config.max_strategic_elements < 1:
            issues.append("max_strategic_elements must be >= 1")
        elif self._config.max_strategic_elements > 20:
            warnings.append("max_strategic_elements > 20 may result in overly complex extractions")
        
        if self._config.max_alliance_considerations < 1:
            issues.append("max_alliance_considerations must be >= 1")
        
        if self._config.max_key_metrics < 1:
            issues.append("max_key_metrics must be >= 1")
        elif self._config.max_key_metrics > 25:
            warnings.append("max_key_metrics > 25 may result in overly detailed extractions")
        
        if not 0.0 <= self._config.extraction_temperature <= 2.0:
            issues.append("extraction_temperature must be between 0.0 and 2.0")
        elif self._config.extraction_temperature > 0.5:
            warnings.append("extraction_temperature > 0.5 may reduce consistency")
        
        if self._config.max_extraction_tokens < 1000:
            issues.append("max_extraction_tokens should be >= 1000 for complete extractions")
        elif self._config.max_extraction_tokens > 8000:
            warnings.append("max_extraction_tokens > 8000 may increase API costs")
        
        if not 0.5 <= self._config.validation_threshold <= 1.0:
            issues.append("validation_threshold must be between 0.5 and 1.0")
        
        if self._config.cache_ttl_hours < 1:
            issues.append("cache_ttl_hours must be >= 1")
        elif self._config.cache_ttl_hours > 720:  # 30 days
            warnings.append("cache_ttl_hours > 720 may result in stale extractions")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'config': self.get_config_dict()
        }


# Global configuration instance
_config_manager = ExtractionConfigManager()


def get_extraction_config() -> ExtractionConfig:
    """
    Get the global extraction configuration.
    
    Returns:
        Current ExtractionConfig instance
    """
    return _config_manager.config


def update_extraction_config(**kwargs) -> None:
    """
    Update the global extraction configuration.
    
    Args:
        **kwargs: Configuration parameters to update
    """
    _config_manager.update_config(**kwargs)


def get_config_manager() -> ExtractionConfigManager:
    """
    Get the global configuration manager.
    
    Returns:
        ExtractionConfigManager instance
    """
    return _config_manager


# Environment variable documentation
EXTRACTION_ENV_VARS = {
    'EXTRACTION_MAX_STRATEGIC_ELEMENTS': {
        'description': 'Maximum number of strategic elements to extract',
        'type': 'int',
        'default': 10,
        'range': '1-20'
    },
    'EXTRACTION_MAX_ALLIANCE_CONSIDERATIONS': {
        'description': 'Maximum number of alliance considerations to extract',
        'type': 'int', 
        'default': 8,
        'range': '1-15'
    },
    'EXTRACTION_MAX_KEY_METRICS': {
        'description': 'Maximum number of key metrics to extract',
        'type': 'int',
        'default': 12,
        'range': '1-25'
    },
    'EXTRACTION_MAX_GAME_PIECES': {
        'description': 'Maximum number of game pieces to track',
        'type': 'int',
        'default': 6,
        'range': '1-10'
    },
    'EXTRACTION_TEMPERATURE': {
        'description': 'Temperature for GPT extraction (lower = more consistent)',
        'type': 'float',
        'default': 0.1,
        'range': '0.0-2.0'
    },
    'EXTRACTION_MAX_TOKENS': {
        'description': 'Maximum tokens for extraction response',
        'type': 'int',
        'default': 4000,
        'range': '1000-8000'
    },
    'EXTRACTION_CACHE_TTL_HOURS': {
        'description': 'Time to live for cached extractions in hours',
        'type': 'int',
        'default': 168,
        'range': '1-720'
    },
    'EXTRACTION_VALIDATION_THRESHOLD': {
        'description': 'Minimum validation score to accept extraction',
        'type': 'float',
        'default': 0.8,
        'range': '0.5-1.0'
    }
}


def get_env_vars_documentation() -> Dict[str, Dict[str, Any]]:
    """
    Get documentation for extraction environment variables.
    
    Returns:
        Dictionary with environment variable documentation
    """
    return EXTRACTION_ENV_VARS.copy()