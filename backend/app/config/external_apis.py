# External API Clients Configuration and Factory

from typing import Optional, Dict, Any
import logging
from pathlib import Path
import json
import base64
import asyncio
from functools import lru_cache

from .settings import get_settings
# Note: TBA and Statbotics clients are function-based, not class-based in current implementation
# These imports are kept as placeholders for future refactoring

logger = logging.getLogger(__name__)


class ExternalAPIConfig:
    """Configuration manager for external API clients"""
    
    def __init__(self):
        self.settings = get_settings()
        self._openai_client: Optional[Any] = None
        self._google_client: Optional[Any] = None
    
    def get_tba_config(self) -> Dict[str, Any]:
        """Get TBA configuration for function-based client"""
        return {
            "api_key": self.settings.tba.api_key,
            "base_url": self.settings.tba.base_url,
            "timeout": self.settings.tba.timeout,
            "max_retries": self.settings.tba.max_retries,
            "user_agent": self.settings.tba.user_agent,
            "cache_duration_hours": self.settings.tba.cache_duration_hours
        }
    
    def get_statbotics_config(self) -> Dict[str, Any]:
        """Get Statbotics configuration for function-based client"""
        return {
            "base_url": self.settings.statbotics.base_url,
            "timeout": self.settings.statbotics.timeout,
            "max_retries": self.settings.statbotics.max_retries,
            "user_agent": self.settings.statbotics.user_agent,
            "cache_duration_hours": self.settings.statbotics.cache_duration_hours
        }
    
    @property
    def openai_client(self):
        """Get or create OpenAI client"""
        if self._openai_client is None:
            try:
                import openai
                
                client_config = {
                    "api_key": self.settings.openai.api_key,
                    "timeout": self.settings.openai.timeout,
                    "max_retries": self.settings.openai.max_retries,
                }
                
                if self.settings.openai.base_url:
                    client_config["base_url"] = self.settings.openai.base_url
                
                self._openai_client = openai.OpenAI(**client_config)
                logger.info("OpenAI client configured successfully")
            except ImportError:
                logger.error("OpenAI package not installed")
                raise
            except Exception as e:
                logger.error(f"Failed to configure OpenAI client: {e}")
                raise
        
        return self._openai_client
    
    @property
    def google_client(self):
        """Get or create Google Sheets client"""
        if self._google_client is None:
            self._google_client = self._create_google_client()
        return self._google_client
    
    def _create_google_client(self):
        """Create Google Sheets client with service account"""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            credentials = self._get_google_credentials()
            if not credentials:
                raise ValueError("Google credentials not available")
            
            # Create client with credentials
            client = gspread.authorize(credentials)
            logger.info("Google Sheets client configured successfully")
            return client
            
        except ImportError:
            logger.error("Google packages not installed (gspread, google-auth)")
            raise
        except Exception as e:
            logger.error(f"Failed to configure Google client: {e}")
            raise
    
    def _get_google_credentials(self):
        """Get Google service account credentials"""
        settings = self.settings.google_sheets
        
        # Try to load from service account file first
        service_account_path = Path(settings.service_account_file)
        if service_account_path.exists():
            try:
                from google.oauth2.service_account import Credentials
                credentials = Credentials.from_service_account_file(
                    service_account_path,
                    scopes=settings.scopes
                )
                logger.info(f"Loaded Google credentials from: {service_account_path}")
                return credentials
            except Exception as e:
                logger.warning(f"Failed to load service account file: {e}")
        
        # Try to construct from base64 parts (fallback for deployment)
        if settings.b64_part_1 and settings.b64_part_2:
            try:
                # Combine and decode base64 parts
                combined_b64 = settings.b64_part_1 + settings.b64_part_2
                service_account_json = base64.b64decode(combined_b64).decode('utf-8')
                service_account_info = json.loads(service_account_json)
                
                from google.oauth2.service_account import Credentials
                credentials = Credentials.from_service_account_info(
                    service_account_info,
                    scopes=settings.scopes
                )
                
                # Save to file for future use
                service_account_path.parent.mkdir(parents=True, exist_ok=True)
                with open(service_account_path, 'w') as f:
                    json.dump(service_account_info, f, indent=2)
                
                logger.info("Reconstructed Google credentials from base64 parts")
                return credentials
            except Exception as e:
                logger.warning(f"Failed to reconstruct service account from base64: {e}")
        
        logger.error("No valid Google credentials found")
        return None
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration for manual client creation"""
        return {
            "api_key": self.settings.openai.api_key,
            "model": self.settings.openai.model,
            "max_tokens": self.settings.openai.max_tokens,
            "temperature": self.settings.openai.temperature,
            "timeout": self.settings.openai.timeout,
            "max_retries": self.settings.openai.max_retries,
            "base_url": self.settings.openai.base_url,
        }
    
    def test_connections(self) -> Dict[str, bool]:
        """Test all external API connections"""
        results = {}
        
        # Test TBA configuration
        try:
            config = self.get_tba_config()
            if config["api_key"]:
                results["tba"] = True
                logger.info("TBA configuration test: OK")
            else:
                results["tba"] = False
                logger.warning("TBA API key not configured")
        except Exception as e:
            results["tba"] = False
            logger.error(f"TBA configuration test failed: {e}")
        
        # Test Statbotics configuration
        try:
            config = self.get_statbotics_config()
            results["statbotics"] = True
            logger.info("Statbotics configuration test: OK")
        except Exception as e:
            results["statbotics"] = False
            logger.error(f"Statbotics configuration test failed: {e}")
        
        # Test OpenAI connection
        try:
            client = self.openai_client
            results["openai"] = True
            logger.info("OpenAI client test: OK")
        except Exception as e:
            results["openai"] = False
            logger.error(f"OpenAI client test failed: {e}")
        
        # Test Google Sheets connection
        try:
            client = self.google_client
            results["google_sheets"] = True
            logger.info("Google Sheets client test: OK")
        except Exception as e:
            results["google_sheets"] = False
            logger.error(f"Google Sheets client test failed: {e}")
        
        return results
    
    def get_client_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all configured clients"""
        return {
            "tba": {
                "base_url": self.settings.tba.base_url,
                "timeout": self.settings.tba.timeout,
                "max_retries": self.settings.tba.max_retries,
                "cache_duration_hours": self.settings.tba.cache_duration_hours,
                "user_agent": self.settings.tba.user_agent,
            },
            "statbotics": {
                "base_url": self.settings.statbotics.base_url,
                "timeout": self.settings.statbotics.timeout,
                "max_retries": self.settings.statbotics.max_retries,
                "cache_duration_hours": self.settings.statbotics.cache_duration_hours,
                "user_agent": self.settings.statbotics.user_agent,
            },
            "openai": {
                "model": self.settings.openai.model,
                "max_tokens": self.settings.openai.max_tokens,
                "temperature": self.settings.openai.temperature,
                "timeout": self.settings.openai.timeout,
                "max_retries": self.settings.openai.max_retries,
                "base_url": self.settings.openai.base_url,
                "has_api_key": bool(self.settings.openai.api_key),
            },
            "google_sheets": {
                "scopes": self.settings.google_sheets.scopes,
                "timeout": self.settings.google_sheets.timeout,
                "max_retries": self.settings.google_sheets.max_retries,
                "batch_size": self.settings.google_sheets.batch_size,
                "service_account_file": self.settings.google_sheets.service_account_file,
                "has_service_account": Path(self.settings.google_sheets.service_account_file).exists(),
                "has_b64_parts": bool(self.settings.google_sheets.b64_part_1 and self.settings.google_sheets.b64_part_2),
            },
        }
    
    def refresh_clients(self):
        """Refresh all client connections"""
        self._openai_client = None
        self._google_client = None
        logger.info("All external API clients refreshed")


# Global external API configuration instance
api_config = ExternalAPIConfig()


def get_api_config() -> ExternalAPIConfig:
    """Get the global external API configuration instance"""
    return api_config


def get_tba_config() -> Dict[str, Any]:
    """Dependency injection function for TBA configuration"""
    return api_config.get_tba_config()


def get_statbotics_config() -> Dict[str, Any]:
    """Dependency injection function for Statbotics configuration"""
    return api_config.get_statbotics_config()


def get_openai_client():
    """Dependency injection function for OpenAI client"""
    return api_config.openai_client


def get_google_client():
    """Dependency injection function for Google client"""
    return api_config.google_client


@lru_cache(maxsize=1)
def get_openai_config() -> Dict[str, Any]:
    """Cached OpenAI configuration for dependency injection"""
    return api_config.get_openai_config()