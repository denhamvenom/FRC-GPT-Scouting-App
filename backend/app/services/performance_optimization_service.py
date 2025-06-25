# backend/app/services/performance_optimization_service.py

import hashlib
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("performance_optimization_service")


class PerformanceOptimizationService:
    """
    Service for handling caching, optimization, and resource management.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    """

    def __init__(self, shared_cache: Dict[str, Any]):
        """
        Initialize the performance optimization service.
        
        Args:
            shared_cache: Shared cache dictionary for storing results
        """
        self.cache = shared_cache
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "total_requests": 0
        }

    def generate_cache_key(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: Dict[str, float],
        exclude_teams: Optional[List[int]] = None,
        team_count: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a deterministic cache key based on input parameters.
        
        Args:
            your_team_number: Team number making the request
            pick_position: Pick position context
            priorities: Priority weights
            exclude_teams: Teams to exclude from analysis
            team_count: Number of teams to include
            **kwargs: Additional parameters
            
        Returns:
            Unique cache key string
        """
        # Create a stable representation of the parameters
        cache_components = {
            "team": your_team_number,
            "position": pick_position,
            "priorities": sorted(priorities.items()) if priorities else [],
            "exclude": sorted(exclude_teams) if exclude_teams else [],
            "count": team_count,
        }
        
        # Add relevant kwargs
        for key in ["batch_size", "use_batching", "reference_teams_count"]:
            if key in kwargs:
                cache_components[key] = kwargs[key]

        # Convert to string and hash
        cache_string = str(cache_components)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        
        # Create human-readable prefix
        prefix = f"picklist_{your_team_number}_{pick_position}"
        
        return f"{prefix}_{cache_hash[:12]}"

    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached result if available and not expired.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached result or None if not found/expired
        """
        self.cache_stats["total_requests"] += 1
        
        if cache_key not in self.cache:
            self.cache_stats["misses"] += 1
            return None

        cached_data = self.cache[cache_key]
        
        # Handle different cache data types
        if isinstance(cached_data, float):
            # Timestamp-based cache entry (still processing)
            self.cache_stats["hits"] += 1
            return {"status": "processing", "timestamp": cached_data}
        
        elif isinstance(cached_data, dict):
            # Check if it's a batch processing entry
            if "batch_processing" in cached_data:
                self.cache_stats["hits"] += 1
                return cached_data
            
            # Check expiration if timestamp is available
            timestamp = cached_data.get("timestamp")
            if timestamp and self._is_cache_expired(timestamp):
                self._invalidate_cache_key(cache_key)
                self.cache_stats["misses"] += 1
                return None
            
            self.cache_stats["hits"] += 1
            return cached_data
        
        else:
            # Unknown cache format, invalidate
            self._invalidate_cache_key(cache_key)
            self.cache_stats["misses"] += 1
            return None

    def store_cached_result(
        self, 
        cache_key: str, 
        result: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Store a result in the cache with optional TTL.
        
        Args:
            cache_key: Cache key to store under
            result: Result data to cache
            ttl_seconds: Time-to-live in seconds (optional)
        """
        cached_data = result.copy()
        
        # Add timestamp for expiration tracking
        cached_data["timestamp"] = time.time()
        
        if ttl_seconds:
            cached_data["expires_at"] = time.time() + ttl_seconds
        
        self.cache[cache_key] = cached_data
        logger.debug(f"Cached result for key: {cache_key}")

    def mark_cache_processing(self, cache_key: str) -> None:
        """
        Mark a cache key as currently being processed.
        
        Args:
            cache_key: Cache key to mark
        """
        self.cache[cache_key] = time.time()
        logger.debug(f"Marked cache key as processing: {cache_key}")

    def _is_cache_expired(self, timestamp: float, default_ttl: int = 3600) -> bool:
        """
        Check if a cached entry has expired.
        
        Args:
            timestamp: Cache entry timestamp
            default_ttl: Default TTL in seconds
            
        Returns:
            True if expired
        """
        expiration_time = timestamp + default_ttl
        return time.time() > expiration_time

    def _invalidate_cache_key(self, cache_key: str) -> None:
        """
        Remove a specific cache key.
        
        Args:
            cache_key: Cache key to remove
        """
        if cache_key in self.cache:
            del self.cache[cache_key]
            self.cache_stats["invalidations"] += 1
            logger.debug(f"Invalidated cache key: {cache_key}")

    def invalidate_cache_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match (simple string contains)
            
        Returns:
            Number of keys invalidated
        """
        keys_to_remove = []
        
        for cache_key in self.cache.keys():
            if pattern in cache_key:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            self._invalidate_cache_key(key)
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache keys matching pattern: {pattern}")
        return len(keys_to_remove)

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.cache_stats["total_requests"]
        hit_rate = (
            self.cache_stats["hits"] / total_requests * 100 
            if total_requests > 0 else 0.0
        )
        
        return {
            "cache_size": len(self.cache),
            "total_requests": total_requests,
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "invalidations": self.cache_stats["invalidations"],
            "memory_usage_estimate": self._estimate_cache_memory_usage()
        }

    def _estimate_cache_memory_usage(self) -> Dict[str, int]:
        """
        Estimate cache memory usage.
        
        Returns:
            Dictionary with memory usage estimates
        """
        total_entries = len(self.cache)
        
        # Simple estimation - in reality you'd use more sophisticated methods
        estimated_bytes_per_entry = 1024  # 1KB average per cache entry
        estimated_total_bytes = total_entries * estimated_bytes_per_entry
        
        return {
            "total_entries": total_entries,
            "estimated_bytes": estimated_total_bytes,
            "estimated_mb": round(estimated_total_bytes / (1024 * 1024), 2)
        }

    def cleanup_expired_cache(self, max_age_seconds: int = 3600) -> int:
        """
        Remove expired cache entries.
        
        Args:
            max_age_seconds: Maximum age for cache entries
            
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        keys_to_remove = []
        
        for cache_key, cached_data in self.cache.items():
            should_remove = False
            
            if isinstance(cached_data, float):
                # Timestamp-only entries (processing markers)
                if current_time - cached_data > max_age_seconds:
                    should_remove = True
            elif isinstance(cached_data, dict):
                # Check explicit expiration
                if "expires_at" in cached_data:
                    if current_time > cached_data["expires_at"]:
                        should_remove = True
                # Check timestamp-based expiration
                elif "timestamp" in cached_data:
                    if current_time - cached_data["timestamp"] > max_age_seconds:
                        should_remove = True
            
            if should_remove:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            self._invalidate_cache_key(key)
        
        logger.info(f"Cleaned up {len(keys_to_remove)} expired cache entries")
        return len(keys_to_remove)

    def optimize_memory_usage(self, max_cache_size: int = 1000) -> Dict[str, Any]:
        """
        Optimize memory usage by removing old cache entries if needed.
        
        Args:
            max_cache_size: Maximum number of cache entries to keep
            
        Returns:
            Optimization report
        """
        current_size = len(self.cache)
        
        if current_size <= max_cache_size:
            return {
                "action": "no_cleanup_needed",
                "current_size": current_size,
                "max_size": max_cache_size,
                "removed_entries": 0
            }
        
        # Sort cache entries by timestamp (oldest first)
        cache_items = []
        for key, data in self.cache.items():
            timestamp = None
            
            if isinstance(data, float):
                timestamp = data
            elif isinstance(data, dict) and "timestamp" in data:
                timestamp = data["timestamp"]
            
            cache_items.append((key, timestamp or 0))
        
        cache_items.sort(key=lambda x: x[1])
        
        # Remove oldest entries
        entries_to_remove = current_size - max_cache_size
        removed_keys = []
        
        for i in range(entries_to_remove):
            key = cache_items[i][0]
            self._invalidate_cache_key(key)
            removed_keys.append(key)
        
        return {
            "action": "cleanup_performed",
            "current_size": len(self.cache),
            "max_size": max_cache_size,
            "removed_entries": len(removed_keys),
            "removed_keys": removed_keys[:10]  # Show first 10 for debugging
        }

    def get_cache_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive cache health report.
        
        Returns:
            Cache health analysis
        """
        stats = self.get_cache_statistics()
        current_time = time.time()
        
        # Analyze cache entry ages
        entry_ages = []
        processing_entries = 0
        expired_entries = 0
        
        for cached_data in self.cache.values():
            if isinstance(cached_data, float):
                age = current_time - cached_data
                entry_ages.append(age)
                processing_entries += 1
            elif isinstance(cached_data, dict) and "timestamp" in cached_data:
                age = current_time - cached_data["timestamp"]
                entry_ages.append(age)
                
                # Check if expired
                if self._is_cache_expired(cached_data["timestamp"]):
                    expired_entries += 1
        
        # Calculate age statistics
        if entry_ages:
            avg_age = sum(entry_ages) / len(entry_ages)
            max_age = max(entry_ages)
            min_age = min(entry_ages)
        else:
            avg_age = max_age = min_age = 0
        
        health_score = 100.0
        recommendations = []
        
        # Evaluate health factors
        if stats["hit_rate_percent"] < 50:
            health_score -= 20
            recommendations.append("Low cache hit rate - consider adjusting cache strategy")
        
        if expired_entries > len(self.cache) * 0.1:  # More than 10% expired
            health_score -= 15
            recommendations.append("Many expired entries - run cache cleanup")
        
        if processing_entries > len(self.cache) * 0.2:  # More than 20% processing
            health_score -= 10
            recommendations.append("Many processing entries - check for stuck operations")
        
        if len(self.cache) > 1000:
            health_score -= 10
            recommendations.append("Large cache size - consider memory optimization")
        
        return {
            "health_score": max(0, round(health_score, 1)),
            "statistics": stats,
            "entry_analysis": {
                "total_entries": len(self.cache),
                "processing_entries": processing_entries,
                "expired_entries": expired_entries,
                "average_age_seconds": round(avg_age, 1),
                "max_age_seconds": round(max_age, 1),
                "min_age_seconds": round(min_age, 1)
            },
            "recommendations": recommendations,
            "timestamp": current_time
        }

    def precompute_common_scenarios(
        self, 
        common_team_numbers: List[int],
        common_positions: List[str],
        common_priorities: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Prepare cache entries for common scenarios to improve response times.
        
        Args:
            common_team_numbers: Frequently analyzed teams
            common_positions: Common pick positions
            common_priorities: Common priority configurations
            
        Returns:
            Precomputation report
        """
        precompute_report = {
            "scenarios_identified": 0,
            "cache_keys_generated": [],
            "estimated_coverage": 0.0
        }
        
        # Generate cache keys for common scenarios
        for team_number in common_team_numbers:
            for position in common_positions:
                for priorities in common_priorities:
                    cache_key = self.generate_cache_key(
                        your_team_number=team_number,
                        pick_position=position,
                        priorities=priorities
                    )
                    
                    precompute_report["cache_keys_generated"].append(cache_key)
                    precompute_report["scenarios_identified"] += 1
        
        # Calculate estimated coverage
        # This would require analysis of actual request patterns in practice
        precompute_report["estimated_coverage"] = min(
            precompute_report["scenarios_identified"] / 100.0, 1.0
        )
        
        logger.info(f"Identified {precompute_report['scenarios_identified']} scenarios for precomputation")
        
        return precompute_report