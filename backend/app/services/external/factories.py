"""
Factory pattern for creating and managing external service clients.

Provides centralized configuration, dependency injection, and service discovery
for all external API integrations.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Type, TypeVar

from ...config.settings import get_settings
from .interfaces import (
    ExternalClient,
    OpenAIClientInterface,
    TBAClientInterface,
    StatboticsClientInterface,
    SheetsClientInterface,
)
from .openai_client import OpenAIClient
from .tba_client import TBAClient
from .statbotics_client import StatboticsClient
from .sheets_client import SheetsClient

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=ExternalClient)


class ClientFactory:
    """
    Factory for creating and managing external service clients.
    
    Features:
    - Singleton pattern for client instances
    - Configuration management from settings
    - Health monitoring and client rotation
    - Dependency injection for testing
    - Comprehensive logging and error handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize client factory.
        
        Args:
            config: Optional configuration override
        """
        self.config = config or {}
        self._clients: Dict[str, ExternalClient] = {}
        self._client_configs: Dict[str, Dict[str, Any]] = {}
        
        # Load settings
        try:
            self.settings = get_settings()
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
            self.settings = None
        
        self._setup_default_configs()
    
    def _setup_default_configs(self) -> None:
        """Setup default configurations for all client types."""
        
        # OpenAI configuration
        self._client_configs["openai"] = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "default_model": "gpt-4o",
            "max_tokens": 100000,
            "timeout": 60.0,
            "max_retries": 3,
        }
        
        # TBA configuration
        self._client_configs["tba"] = {
            "api_key": os.getenv("TBA_API_KEY"),
            "base_url": "https://www.thebluealliance.com/api/v3",
            "timeout": 30.0,
            "max_retries": 3,
        }
        
        # Statbotics configuration
        self._client_configs["statbotics"] = {
            "timeout": 30.0,
            "max_retries": 3,
            "config_dir": None,  # Will auto-detect
        }
        
        # Google Sheets configuration  
        self._client_configs["sheets"] = {
            "service_account_file": os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
            "timeout": 30.0,
            "max_retries": 3,
            "scopes": ["https://www.googleapis.com/auth/spreadsheets"],
        }
        
        # Apply any config overrides
        for service, config in self.config.items():
            if service in self._client_configs:
                self._client_configs[service].update(config)
    
    def get_openai_client(self, **kwargs) -> OpenAIClientInterface:
        """
        Get or create OpenAI client.
        
        Args:
            **kwargs: Override configuration parameters
            
        Returns:
            OpenAI client instance
        """
        if "openai" not in self._clients:
            config = {**self._client_configs["openai"], **kwargs}
            
            logger.info("Creating new OpenAI client")
            self._clients["openai"] = OpenAIClient(**config)
        
        return self._clients["openai"]
    
    def get_tba_client(self, **kwargs) -> TBAClientInterface:
        """
        Get or create TBA client.
        
        Args:
            **kwargs: Override configuration parameters
            
        Returns:
            TBA client instance
        """
        if "tba" not in self._clients:
            config = {**self._client_configs["tba"], **kwargs}
            
            logger.info("Creating new TBA client")
            self._clients["tba"] = TBAClient(**config)
        
        return self._clients["tba"]
    
    def get_statbotics_client(self, **kwargs) -> StatboticsClientInterface:
        """
        Get or create Statbotics client.
        
        Args:
            **kwargs: Override configuration parameters
            
        Returns:
            Statbotics client instance
        """
        if "statbotics" not in self._clients:
            config = {**self._client_configs["statbotics"], **kwargs}
            
            logger.info("Creating new Statbotics client")
            self._clients["statbotics"] = StatboticsClient(**config)
        
        return self._clients["statbotics"]
    
    def get_sheets_client(self, **kwargs) -> SheetsClientInterface:
        """
        Get or create Google Sheets client.
        
        Args:
            **kwargs: Override configuration parameters
            
        Returns:
            Google Sheets client instance
        """
        if "sheets" not in self._clients:
            config = {**self._client_configs["sheets"], **kwargs}
            
            logger.info("Creating new Google Sheets client")
            self._clients["sheets"] = SheetsClient(**config)
        
        return self._clients["sheets"]
    
    def get_client(self, service_name: str, **kwargs) -> ExternalClient:
        """
        Get client by service name.
        
        Args:
            service_name: Name of the service (openai, tba, statbotics, sheets)
            **kwargs: Override configuration parameters
            
        Returns:
            Client instance
            
        Raises:
            ValueError: If service name is not recognized
        """
        service_name = service_name.lower()
        
        if service_name == "openai":
            return self.get_openai_client(**kwargs)
        elif service_name == "tba":
            return self.get_tba_client(**kwargs)
        elif service_name == "statbotics":
            return self.get_statbotics_client(**kwargs)
        elif service_name == "sheets":
            return self.get_sheets_client(**kwargs)
        else:
            raise ValueError(f"Unknown service name: {service_name}")
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health checks on all registered clients.
        
        Returns:
            Dictionary with health status for each client
        """
        results = {}
        
        for service_name, client in self._clients.items():
            try:
                health_result = await client.health_check()
                results[service_name] = {
                    "status": health_result.status,
                    "response_time_ms": health_result.response_time_ms,
                    "error_message": health_result.error_message,
                    "metadata": health_result.metadata,
                }
            except Exception as e:
                results[service_name] = {
                    "status": "error",
                    "error_message": str(e),
                }
        
        return results
    
    def register_client(
        self,
        service_name: str,
        client: ExternalClient,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a custom client instance.
        
        Args:
            service_name: Name of the service
            client: Client instance
            config: Optional configuration
        """
        self._clients[service_name] = client
        if config:
            self._client_configs[service_name] = config
        
        logger.info(f"Registered custom client for {service_name}")
    
    def remove_client(self, service_name: str) -> None:
        """
        Remove a client from the factory.
        
        Args:
            service_name: Name of the service to remove
        """
        if service_name in self._clients:
            del self._clients[service_name]
            logger.info(f"Removed client for {service_name}")
    
    def clear_all_clients(self) -> None:
        """Clear all registered clients."""
        self._clients.clear()
        logger.info("Cleared all clients from factory")
    
    def get_registered_services(self) -> List[str]:
        """Get list of registered service names."""
        return list(self._clients.keys())
    
    def update_config(self, service_name: str, config: Dict[str, Any]) -> None:
        """
        Update configuration for a service.
        
        Args:
            service_name: Name of the service
            config: New configuration parameters
        """
        if service_name in self._client_configs:
            self._client_configs[service_name].update(config)
            
            # Remove existing client to force recreation with new config
            if service_name in self._clients:
                del self._clients[service_name]
            
            logger.info(f"Updated configuration for {service_name}")
        else:
            logger.warning(f"No configuration found for service {service_name}")
    
    def get_client_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all clients.
        
        Returns:
            Dictionary with client statistics
        """
        stats = {
            "total_clients": len(self._clients),
            "services": {},
        }
        
        for service_name, client in self._clients.items():
            client_stats = {
                "service_name": client.service_name,
                "circuit_breaker_failures": client._circuit_breaker_failures,
                "is_circuit_open": client.is_circuit_breaker_open(),
            }
            
            # Add service-specific stats if available
            if hasattr(client, "get_cache_stats"):
                client_stats["cache_stats"] = client.get_cache_stats()
            
            stats["services"][service_name] = client_stats
        
        return stats


# Global factory instance
_global_factory: Optional[ClientFactory] = None


def get_client_factory(config: Optional[Dict[str, Any]] = None) -> ClientFactory:
    """
    Get the global client factory instance.
    
    Args:
        config: Optional configuration for first-time initialization
        
    Returns:
        Global ClientFactory instance
    """
    global _global_factory
    
    if _global_factory is None:
        _global_factory = ClientFactory(config)
        logger.info("Initialized global client factory")
    
    return _global_factory


def reset_client_factory() -> None:
    """Reset the global client factory (useful for testing)."""
    global _global_factory
    _global_factory = None
    logger.info("Reset global client factory")


# Convenience functions for common clients
def get_openai_client(**kwargs) -> OpenAIClientInterface:
    """Get OpenAI client from global factory."""
    return get_client_factory().get_openai_client(**kwargs)


def get_tba_client(**kwargs) -> TBAClientInterface:
    """Get TBA client from global factory."""
    return get_client_factory().get_tba_client(**kwargs)


def get_statbotics_client(**kwargs) -> StatboticsClientInterface:
    """Get Statbotics client from global factory."""
    return get_client_factory().get_statbotics_client(**kwargs)


def get_sheets_client(**kwargs) -> SheetsClientInterface:
    """Get Google Sheets client from global factory."""
    return get_client_factory().get_sheets_client(**kwargs)