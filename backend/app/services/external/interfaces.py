"""
Abstract interfaces for all external service clients.

This module defines the contracts that all external service clients must implement,
ensuring consistent error handling, retry logic, and method signatures across
different third-party integrations.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    """Status of external service."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult(BaseModel):
    """Result of a health check operation."""
    status: ServiceStatus
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    last_success: Optional[str] = None
    metadata: Dict[str, Any] = {}


class RetryConfig(BaseModel):
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    requests_per_second: float = 10.0
    burst_limit: int = 50
    backoff_factor: float = 1.5


class ExternalClient(ABC):
    """
    Abstract base class for all external service clients.
    
    Provides common functionality for health checking, error handling,
    retry logic, and circuit breaking.
    """
    
    def __init__(
        self,
        service_name: str,
        retry_config: Optional[RetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize external client.
        
        Args:
            service_name: Name of the external service
            retry_config: Configuration for retry behavior
            rate_limit_config: Configuration for rate limiting
            timeout: Default request timeout in seconds
        """
        self.service_name = service_name
        self.retry_config = retry_config or RetryConfig()
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.timeout = timeout
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = None
    
    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """
        Check the health of the external service.
        
        Returns:
            HealthCheckResult with service status and metadata
        """
        pass
    
    async def with_retry(self, operation, *args, **kwargs):
        """
        Execute an operation with retry logic.
        
        Args:
            operation: The async function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.retry_config.max_attempts - 1:
                    # Last attempt failed
                    break
                
                # Calculate delay for next attempt
                delay = min(
                    self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                    self.retry_config.max_delay
                )
                
                if self.retry_config.jitter:
                    import random
                    delay *= (0.5 + random.random() * 0.5)
                
                await asyncio.sleep(delay)
        
        # All attempts failed, raise the last exception
        raise last_exception
    
    def is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open (service unavailable)."""
        if self._circuit_breaker_failures >= 5:
            if self._circuit_breaker_last_failure:
                import time
                # Circuit breaker opens for 60 seconds after 5 failures
                return (time.time() - self._circuit_breaker_last_failure) < 60
        return False
    
    def record_success(self):
        """Record a successful operation."""
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = None
    
    def record_failure(self):
        """Record a failed operation."""
        import time
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = time.time()


class OpenAIClientInterface(ExternalClient):
    """Interface for OpenAI API client."""
    
    @abstractmethod
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a completion using OpenAI API.
        
        Args:
            messages: List of messages in OpenAI format
            model: Model to use for completion
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            API response with completion
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        """
        Count tokens in text for the given model.
        
        Args:
            text: Text to count tokens for
            model: Model to use for token counting
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate the OpenAI API key.
        
        Returns:
            True if API key is valid
        """
        pass


class TBAClientInterface(ExternalClient):
    """Interface for The Blue Alliance API client."""
    
    @abstractmethod
    async def get_event_teams(self, event_key: str) -> List[Dict[str, Any]]:
        """Get teams at an event."""
        pass
    
    @abstractmethod
    async def get_event_matches(self, event_key: str) -> List[Dict[str, Any]]:
        """Get matches at an event."""
        pass
    
    @abstractmethod
    async def get_event_rankings(self, event_key: str) -> Optional[Dict[str, Any]]:
        """Get event rankings."""
        pass
    
    @abstractmethod
    async def get_match_detail(self, match_key: str) -> Dict[str, Any]:
        """Get detailed match information."""
        pass
    
    @abstractmethod
    async def get_team_status_at_event(
        self, team_key: str, event_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get team status at an event."""
        pass
    
    @abstractmethod
    async def get_events_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Get all events for a year."""
        pass
    
    @abstractmethod
    async def get_event_details(self, event_key: str) -> Dict[str, Any]:
        """Get detailed event information."""
        pass


class StatboticsClientInterface(ExternalClient):
    """Interface for Statbotics API client."""
    
    @abstractmethod
    async def get_team_epa(self, team_number: int, year: int) -> Dict[str, Any]:
        """
        Get EPA data for a team in a given year.
        
        Args:
            team_number: Team number (e.g., 254)
            year: FRC season year
            
        Returns:
            Dictionary with EPA metrics and team info
        """
        pass
    
    @abstractmethod
    async def get_event_teams_epa(
        self, event_key: str, year: int
    ) -> List[Dict[str, Any]]:
        """
        Get EPA data for all teams at an event.
        
        Args:
            event_key: TBA event key
            year: FRC season year
            
        Returns:
            List of team EPA data
        """
        pass
    
    @abstractmethod
    def load_field_mapping(self, year: int) -> Dict[str, str]:
        """
        Load field mapping configuration for a year.
        
        Args:
            year: FRC season year
            
        Returns:
            Dictionary mapping output fields to Statbotics paths
        """
        pass


class SheetsClientInterface(ExternalClient):
    """Interface for Google Sheets API client."""
    
    @abstractmethod
    async def get_sheet_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        value_render_option: str = "UNFORMATTED_VALUE",
    ) -> List[List[Any]]:
        """
        Get values from a sheet range.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range (e.g., "Sheet1!A1:D10")
            value_render_option: How values should be rendered
            
        Returns:
            2D list of cell values
        """
        pass
    
    @abstractmethod
    async def update_sheet_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "RAW",
    ) -> Dict[str, Any]:
        """
        Update values in a sheet range.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range
            values: 2D list of values to write
            value_input_option: How values should be interpreted
            
        Returns:
            API response
        """
        pass
    
    @abstractmethod
    async def get_spreadsheet_metadata(
        self, spreadsheet_id: str
    ) -> Dict[str, Any]:
        """
        Get metadata about a spreadsheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            
        Returns:
            Spreadsheet metadata including sheet names
        """
        pass
    
    @abstractmethod
    async def get_sheet_headers(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        header_row: int = 1,
    ) -> List[str]:
        """
        Get headers from a specific sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            header_row: Row number containing headers (1-indexed)
            
        Returns:
            List of header strings
        """
        pass
    
    @abstractmethod
    async def test_connection(
        self, spreadsheet_id: str, sheet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test connection to a spreadsheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Optional sheet name to test
            
        Returns:
            Test result with status and details
        """
        pass