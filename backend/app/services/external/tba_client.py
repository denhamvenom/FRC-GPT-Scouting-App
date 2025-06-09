"""
The Blue Alliance API client with caching, retry logic, and error handling.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from .interfaces import TBAClientInterface, HealthCheckResult, ServiceStatus

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class TBAClient(TBAClientInterface):
    """
    Production-ready TBA API client with comprehensive error handling.
    
    Features:
    - Automatic retry with exponential backoff
    - Circuit breaker pattern for resilience  
    - Built-in caching for expensive operations
    - Health monitoring and API key validation
    - Comprehensive logging for debugging
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://www.thebluealliance.com/api/v3",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize TBA client.
        
        Args:
            api_key: TBA API key (defaults to TBA_API_KEY env var)
            base_url: TBA API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__(service_name="TheBlueAlliance", timeout=timeout)
        
        self.api_key = api_key or os.getenv("TBA_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        
        # Default API key for testing if none provided
        if not self.api_key:
            self.api_key = "PpK8kpfWt94Nf15uoK8UbanbFQzZ97rwWwGqnqB9wILs9VBfcNjfRLvlkvYcGqoA"
            logger.warning("Using default TBA API key - configure TBA_API_KEY for production")
        
        self.headers = {
            "X-TBA-Auth-Key": self.api_key,
            "User-Agent": "FRC-GPT-Scouting-App/1.0"
        }
        
        # Cache for expensive operations
        self._cache = {}
        self._cache_ttl = {}
    
    def _cache_key(self, endpoint: str, **params) -> str:
        """Generate cache key for an endpoint and parameters."""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}" if param_str else endpoint
    
    def _is_cache_valid(self, key: str, ttl_seconds: int) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        return (time.time() - self._cache_ttl.get(key, 0)) < ttl_seconds
    
    def _set_cache(self, key: str, data: Any) -> None:
        """Store data in cache with timestamp."""
        self._cache[key] = data
        self._cache_ttl[key] = time.time()
    
    def _get_cache(self, key: str) -> Any:
        """Get data from cache."""
        return self._cache.get(key)
    
    async def _make_request(
        self,
        endpoint: str,
        cache_ttl: Optional[int] = None,
        **params
    ) -> Any:
        """
        Make an HTTP request to TBA API with caching and error handling.
        
        Args:
            endpoint: API endpoint (without base URL)
            cache_ttl: Cache TTL in seconds (None to disable caching)
            **params: Query parameters
            
        Returns:
            API response data
        """
        # Check cache first
        cache_key = self._cache_key(endpoint, **params)
        if cache_ttl and self._is_cache_valid(cache_key, cache_ttl):
            logger.debug(f"Cache hit for {cache_key}")
            return self._get_cache(cache_key)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async def _request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, params=params)
                
                # Handle 404 as None for optional data
                if response.status_code == 404:
                    logger.debug(f"TBA endpoint {endpoint} returned 404")
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                # Cache the result if TTL specified
                if cache_ttl:
                    self._set_cache(cache_key, data)
                    logger.debug(f"Cached {cache_key} for {cache_ttl}s")
                
                return data
        
        try:
            self.record_success()
            return await self.with_retry(_request)
        except Exception as e:
            self.record_failure()
            logger.error(f"TBA API error for {endpoint}: {e}")
            raise
    
    async def health_check(self) -> HealthCheckResult:
        """
        Check the health of TBA API.
        
        Returns:
            HealthCheckResult with service status
        """
        start_time = time.time()
        
        try:
            # Test with a simple API call
            response = await self._make_request("status")
            response_time = int((time.time() - start_time) * 1000)
            
            return HealthCheckResult(
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                metadata={
                    "api_status": response,
                    "endpoint_tested": "status"
                }
            )
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def get_event_teams(self, event_key: str) -> List[Dict[str, Any]]:
        """
        Get simple team listings at an event.
        
        Args:
            event_key: TBA event key (e.g., "2025caln")
            
        Returns:
            List of team objects
        """
        return await self._make_request(
            f"event/{event_key}/teams/simple",
            cache_ttl=24 * 3600  # Cache for 24 hours
        ) or []
    
    async def get_event_matches(self, event_key: str) -> List[Dict[str, Any]]:
        """
        Get simple match listings at an event.
        
        Args:
            event_key: TBA event key
            
        Returns:
            List of match objects
        """
        return await self._make_request(
            f"event/{event_key}/matches/simple",
            cache_ttl=8 * 3600  # Cache for 8 hours
        ) or []
    
    async def get_event_rankings(self, event_key: str) -> Optional[Dict[str, Any]]:
        """
        Get event rankings (qualification points, tie-breakers, etc.).
        
        Args:
            event_key: TBA event key
            
        Returns:
            Rankings object or None if not available
        """
        return await self._make_request(
            f"event/{event_key}/rankings",
            cache_ttl=4 * 3600  # Cache for 4 hours
        )
    
    async def get_match_detail(self, match_key: str) -> Dict[str, Any]:
        """
        Get detailed match breakdown for a specific match.
        
        Args:
            match_key: TBA match key (e.g., "2025caln_qm1")
            
        Returns:
            Detailed match object
        """
        result = await self._make_request(f"match/{match_key}")
        if result is None:
            raise ValueError(f"Match {match_key} not found")
        return result
    
    async def get_team_status_at_event(
        self, team_key: str, event_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a team's current status at an event.
        
        Args:
            team_key: TBA team key (e.g., "frc254")
            event_key: TBA event key
            
        Returns:
            Team status object or None if not available
        """
        return await self._make_request(
            f"team/{team_key}/event/{event_key}/status",
            cache_ttl=1 * 3600  # Cache for 1 hour
        )
    
    async def get_events_by_year(self, year: int) -> List[Dict[str, Any]]:
        """
        Get all events for a specific FRC season year.
        
        Args:
            year: FRC season year (e.g., 2025)
            
        Returns:
            List of event objects sorted by start date
        """
        events = await self._make_request(
            f"events/{year}/simple",
            cache_ttl=7 * 24 * 3600  # Cache for 1 week
        ) or []
        
        # Sort events by start date then name
        return sorted(events, key=lambda e: (e.get("start_date", ""), e.get("name", "")))
    
    async def get_event_details(self, event_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific event.
        
        Args:
            event_key: TBA event key
            
        Returns:
            Detailed event object
        """
        result = await self._make_request(
            f"event/{event_key}",
            cache_ttl=7 * 24 * 3600  # Cache for 1 week
        )
        if result is None:
            raise ValueError(f"Event {event_key} not found")
        return result
    
    async def get_team_details(self, team_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a team.
        
        Args:
            team_key: TBA team key (e.g., "frc254")
            
        Returns:
            Team details object
        """
        result = await self._make_request(
            f"team/{team_key}",
            cache_ttl=7 * 24 * 3600  # Cache for 1 week
        )
        if result is None:
            raise ValueError(f"Team {team_key} not found")
        return result
    
    async def get_team_events(self, team_key: str, year: int) -> List[Dict[str, Any]]:
        """
        Get events that a team attended in a year.
        
        Args:
            team_key: TBA team key
            year: FRC season year
            
        Returns:
            List of event objects
        """
        return await self._make_request(
            f"team/{team_key}/events/{year}/simple",
            cache_ttl=24 * 3600  # Cache for 24 hours
        ) or []
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_ttl.clear()
        logger.info("TBA client cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_entries": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "total_memory_mb": sum(
                len(str(v)) for v in self._cache.values()
            ) / (1024 * 1024)
        }