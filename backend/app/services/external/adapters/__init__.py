"""
Legacy compatibility adapters for external service clients.

This package provides adapter classes that maintain compatibility with existing
service implementations while migrating to the new external service architecture.
These adapters will be gradually phased out as services are updated to use
the new client interfaces directly.
"""

from .openai_adapter import OpenAILegacyAdapter
from .google_adapter import GoogleSheetsLegacyAdapter

__all__ = [
    "OpenAILegacyAdapter",
    "GoogleSheetsLegacyAdapter",
]