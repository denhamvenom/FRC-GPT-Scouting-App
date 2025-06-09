"""
External service abstractions for all third-party API integrations.

This package provides a unified abstraction layer for external services including:
- OpenAI GPT API for intelligent analysis
- The Blue Alliance API for FRC data
- Statbotics API for EPA metrics  
- Google Sheets API for scouting data

Key components:
- Interfaces: Abstract base classes for all external clients
- Clients: Concrete implementations with error handling and retry logic
- Adapters: Legacy compatibility layers
- Factories: Service discovery and dependency injection
"""

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
from .factories import ClientFactory, get_client_factory

__all__ = [
    # Interfaces
    "ExternalClient",
    "OpenAIClientInterface", 
    "TBAClientInterface",
    "StatboticsClientInterface",
    "SheetsClientInterface",
    # Concrete clients
    "OpenAIClient",
    "TBAClient", 
    "StatboticsClient",
    "SheetsClient",
    # Factory
    "ClientFactory",
    "get_client_factory",
]