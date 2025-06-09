"""
Statbotics API client with field mapping, caching, and error handling.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from statbotics import Statbotics

from .interfaces import StatboticsClientInterface, HealthCheckResult, ServiceStatus

logger = logging.getLogger(__name__)


class StatboticsClient(StatboticsClientInterface):
    """
    Production-ready Statbotics API client with comprehensive error handling.
    
    Features:
    - Automatic retry with exponential backoff
    - Circuit breaker pattern for resilience
    - Year-specific field mapping configuration
    - Built-in caching for EPA data
    - Health monitoring and validation
    - Comprehensive logging for debugging
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        config_dir: Optional[str] = None,
    ):
        """
        Initialize Statbotics client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            config_dir: Directory containing field mapping configs
        """
        super().__init__(service_name="Statbotics", timeout=timeout)
        
        self.max_retries = max_retries
        
        # Set up config directory
        if config_dir:
            self.config_dir = config_dir
        else:
            # Default to app/config directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir = os.path.normpath(
                os.path.join(base_dir, "..", "..", "config")
            )
        
        # Initialize Statbotics client
        try:
            self.client = Statbotics()
            logger.info("Statbotics client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Statbotics client: {e}")
            self.client = None
        
        # Cache for field mappings and EPA data
        self._field_mapping_cache = {}
        self._epa_cache = {}
        self._epa_cache_ttl = {}
    
    def load_field_mapping(self, year: int) -> Dict[str, str]:
        """
        Load field mapping configuration for a year.
        
        Args:
            year: FRC season year
            
        Returns:
            Dictionary mapping output fields to Statbotics paths
        """
        if year in self._field_mapping_cache:
            return self._field_mapping_cache[year]
        
        year_config_path = os.path.join(self.config_dir, f"statbotics_field_map_{year}.json")
        default_config_path = os.path.join(self.config_dir, "statbotics_field_map_DEFAULT.json")
        
        # Try year-specific config first
        config_path = year_config_path if os.path.exists(year_config_path) else default_config_path
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                field_mapping = json.load(f)
            
            self._field_mapping_cache[year] = field_mapping
            logger.info(f"Loaded field mapping for {year} from {config_path}")
            return field_mapping
            
        except FileNotFoundError:
            logger.error(f"No field mapping config found for {year}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in field mapping config: {e}")
            return {}
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """
        Get a nested value from a dictionary using a dotted path.
        
        Args:
            data: Dictionary to extract from
            path: Dotted path (e.g., "epa.breakdown.total_points")
            
        Returns:
            Value at the path or None if not found
        """
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current if current != {} else None
    
    def _cache_key(self, team_number: int, year: int) -> str:
        """Generate cache key for EPA data."""
        return f"epa_{team_number}_{year}"
    
    def _is_epa_cache_valid(self, key: str, ttl_seconds: int = 24 * 3600) -> bool:
        """Check if cached EPA data is still valid."""
        if key not in self._epa_cache:
            return False
        return (time.time() - self._epa_cache_ttl.get(key, 0)) < ttl_seconds
    
    def _set_epa_cache(self, key: str, data: Any) -> None:
        """Store EPA data in cache with timestamp."""
        self._epa_cache[key] = data
        self._epa_cache_ttl[key] = time.time()
    
    def _get_epa_cache(self, key: str) -> Any:
        """Get EPA data from cache."""
        return self._epa_cache.get(key)
    
    async def health_check(self) -> HealthCheckResult:
        """
        Check the health of Statbotics API.
        
        Returns:
            HealthCheckResult with service status
        """
        if not self.client:
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                error_message="Statbotics client not initialized"
            )
        
        start_time = time.time()
        
        try:
            # Test with a known team from a recent year
            test_data = await self.get_team_epa(254, 2024)
            response_time = int((time.time() - start_time) * 1000)
            
            # Check if we got reasonable data
            if test_data and "team_number" in test_data:
                self.record_success()
                return HealthCheckResult(
                    status=ServiceStatus.HEALTHY,
                    response_time_ms=response_time,
                    metadata={
                        "test_team": 254,
                        "test_year": 2024,
                        "has_epa_data": "epa_total" in test_data
                    }
                )
            else:
                return HealthCheckResult(
                    status=ServiceStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message="API responding but data quality issues"
                )
                
        except Exception as e:
            self.record_failure()
            response_time = int((time.time() - start_time) * 1000)
            return HealthCheckResult(
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def get_team_epa(self, team_number: int, year: int) -> Dict[str, Any]:
        """
        Get EPA data for a team in a given year.
        
        Args:
            team_number: Team number (e.g., 254)
            year: FRC season year
            
        Returns:
            Dictionary with EPA metrics and team info
        """
        # Check cache first
        cache_key = self._cache_key(team_number, year)
        if self._is_epa_cache_valid(cache_key):
            logger.debug(f"Cache hit for team {team_number} EPA data")
            return self._get_epa_cache(cache_key)
        
        if not self.client:
            logger.error("Statbotics client not initialized")
            return {
                "team_number": team_number,
                "team_name": f"Team {team_number}",
                "epa_total": None
            }
        
        async def _get_epa():
            try:
                # Get raw data from Statbotics
                raw_data = self.client.get_team_year(team_number, year)
                
                # Always include basic team info
                result = {
                    "team_number": raw_data.get("team", team_number),
                    "team_name": raw_data.get("name", f"Team {team_number}")
                }
                
                # Load field mapping and extract EPA data
                try:
                    field_mapping = self.load_field_mapping(year)
                    
                    for output_field, statbotics_path in field_mapping.items():
                        value = self._get_nested_value(raw_data, statbotics_path)
                        result[output_field] = value
                        
                    logger.debug(f"Extracted EPA data for team {team_number}: {len(field_mapping)} fields")
                    
                except Exception as mapping_error:
                    logger.warning(f"Field mapping error for {year}: {mapping_error}")
                    # Add basic EPA field as fallback
                    result["epa_total"] = self._get_nested_value(raw_data, "epa.total_points")
                
                # Cache the result
                self._set_epa_cache(cache_key, result)
                
                return result
                
            except Exception as e:
                logger.error(f"Error fetching EPA data for team {team_number} in {year}: {e}")
                # Return basic info even on error
                return {
                    "team_number": team_number,
                    "team_name": f"Team {team_number}",
                    "epa_total": None
                }
        
        try:
            self.record_success()
            return await self.with_retry(_get_epa)
        except Exception as e:
            self.record_failure()
            logger.error(f"Failed to get EPA data for team {team_number}: {e}")
            # Return fallback data
            return {
                "team_number": team_number,
                "team_name": f"Team {team_number}",
                "epa_total": None
            }
    
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
        if not self.client:
            logger.error("Statbotics client not initialized")
            return []
        
        try:
            # Get event data from Statbotics
            event_data = self.client.get_event(event_key)
            
            if not event_data or "teams" not in event_data:
                logger.warning(f"No team data found for event {event_key}")
                return []
            
            # Get EPA data for each team
            teams_epa = []
            for team_data in event_data["teams"]:
                team_number = team_data.get("team", 0)
                if team_number:
                    epa_data = await self.get_team_epa(team_number, year)
                    teams_epa.append(epa_data)
            
            logger.info(f"Retrieved EPA data for {len(teams_epa)} teams at {event_key}")
            return teams_epa
            
        except Exception as e:
            logger.error(f"Error getting event teams EPA for {event_key}: {e}")
            return []
    
    async def get_team_performance_trend(
        self, team_number: int, years: List[int]
    ) -> Dict[str, Any]:
        """
        Get EPA performance trend for a team across multiple years.
        
        Args:
            team_number: Team number
            years: List of years to analyze
            
        Returns:
            Dictionary with trend data
        """
        trend_data = {
            "team_number": team_number,
            "years": {},
            "trend": "stable"  # stable, improving, declining
        }
        
        epa_values = []
        
        for year in sorted(years):
            epa_data = await self.get_team_epa(team_number, year)
            epa_total = epa_data.get("epa_total")
            
            trend_data["years"][year] = {
                "epa_total": epa_total,
                "team_name": epa_data.get("team_name")
            }
            
            if epa_total is not None:
                epa_values.append(epa_total)
        
        # Calculate trend
        if len(epa_values) >= 2:
            first_half = epa_values[:len(epa_values)//2]
            second_half = epa_values[len(epa_values)//2:]
            
            if sum(second_half) > sum(first_half) * 1.1:
                trend_data["trend"] = "improving"
            elif sum(second_half) < sum(first_half) * 0.9:
                trend_data["trend"] = "declining"
        
        return trend_data
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._field_mapping_cache.clear()
        self._epa_cache.clear()
        self._epa_cache_ttl.clear()
        logger.info("Statbotics client cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "field_mapping_entries": len(self._field_mapping_cache),
            "epa_cache_entries": len(self._epa_cache),
            "cached_years": list(self._field_mapping_cache.keys()),
            "cache_memory_mb": sum(
                len(str(v)) for v in self._epa_cache.values()
            ) / (1024 * 1024)
        }