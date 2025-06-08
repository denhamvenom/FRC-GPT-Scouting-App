"""
Cache manager for picklist service.
"""

import logging
import time
from typing import Any, Dict, Optional

from ..interfaces import CacheManager

logger = logging.getLogger(__name__)


class PicklistCacheManager(CacheManager):
    """In-memory cache manager for picklist generation."""

    # Class-level cache to share across instances
    _cache: Dict[str, Any] = {}
    _processing_keys: Dict[str, float] = {}

    def __init__(self, ttl: int = 3600):
        """
        Initialize cache manager.

        Args:
            ttl: Default time-to-live in seconds
        """
        self.ttl = ttl

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache if not expired."""
        if key in self._cache:
            cached_data = self._cache[key]
            
            # Check if it's a timestamp (processing marker)
            if isinstance(cached_data, float):
                # Check if processing timeout exceeded (2 minutes)
                if time.time() - cached_data > 120:
                    logger.warning(f"Stale processing marker found for key: {key}")
                    del self._cache[key]
                    return None
                return None  # Still processing
            
            # Check for expiration if TTL is set
            if isinstance(cached_data, dict) and "_expires_at" in cached_data:
                if time.time() > cached_data["_expires_at"]:
                    logger.info(f"Cache expired for key: {key}")
                    del self._cache[key]
                    return None
                
                # Return data without internal fields
                return {k: v for k, v in cached_data.items() if not k.startswith("_")}
            
            return cached_data
        
        return None

    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        cache_ttl = ttl or self.ttl
        
        if cache_ttl:
            value["_expires_at"] = time.time() + cache_ttl
        
        self._cache[key] = value
        
        # Remove from processing if it was there
        if key in self._processing_keys:
            del self._processing_keys[key]
        
        logger.debug(f"Cached result for key: {key} (TTL: {cache_ttl}s)")

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._processing_keys:
            del self._processing_keys[key]

    def is_processing(self, key: str) -> bool:
        """Check if key is currently being processed."""
        if key in self._cache and isinstance(self._cache[key], float):
            # Check if not stale
            if time.time() - self._cache[key] < 120:
                return True
            else:
                # Clean up stale processing marker
                del self._cache[key]
        
        return key in self._processing_keys

    def mark_processing(self, key: str) -> None:
        """Mark key as being processed."""
        current_time = time.time()
        self._cache[key] = current_time
        self._processing_keys[key] = current_time

    def wait_for_processing(self, key: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """
        Wait for processing to complete and return result.

        Args:
            key: Cache key
            timeout: Maximum time to wait in seconds

        Returns:
            Cached result or None if timeout
        """
        start_time = time.time()
        check_interval = 5  # seconds

        while time.time() - start_time < timeout:
            result = self.get(key)
            if result is not None:
                return result
            
            if not self.is_processing(key):
                # Processing finished but no result
                return None
            
            time.sleep(check_interval)
        
        logger.warning(f"Timeout waiting for processing of key: {key}")
        return None

    def get_processing_status(self, key: str) -> Optional[Dict[str, Any]]:
        """Get processing status for a key."""
        if key in self._cache:
            cached_data = self._cache[key]
            
            if isinstance(cached_data, float):
                # It's a processing timestamp
                elapsed = time.time() - cached_data
                return {
                    "status": "processing",
                    "started_at": cached_data,
                    "elapsed_seconds": elapsed,
                }
            elif isinstance(cached_data, dict) and "batch_processing" in cached_data:
                # Batch processing status
                return cached_data.get("batch_processing")
        
        return None

    def clear_expired(self) -> int:
        """Clear expired entries from cache."""
        current_time = time.time()
        expired_keys = []
        
        for key, value in self._cache.items():
            if isinstance(value, dict) and "_expires_at" in value:
                if current_time > value["_expires_at"]:
                    expired_keys.append(key)
            elif isinstance(value, float):
                # Clean up stale processing markers
                if current_time - value > 120:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._processing_keys:
                del self._processing_keys[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def update_batch_status(self, key: str, batch_info: Dict[str, Any]) -> None:
        """
        Update batch processing status in cache.
        
        Args:
            key: Cache key
            batch_info: Batch processing information
        """
        if key in self._cache:
            cached_data = self._cache.get(key, {})
            if isinstance(cached_data, dict):
                cached_data["batch_processing"] = batch_info
                self._cache[key] = cached_data
            else:
                # Create new batch status entry
                self._cache[key] = {"batch_processing": batch_info}
    
    def get_all_keys(self) -> list[str]:
        """Get all cache keys."""
        return list(self._cache.keys())
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        current_time = time.time()
        total_entries = len(self._cache)
        processing_entries = len(self._processing_keys)
        expired_entries = 0
        
        for key, value in self._cache.items():
            if isinstance(value, dict) and "_expires_at" in value:
                if current_time > value["_expires_at"]:
                    expired_entries += 1
        
        return {
            "total_entries": total_entries,
            "processing_entries": processing_entries,
            "expired_entries": expired_entries,
            "cache_keys": list(self._cache.keys()),
        }
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache (regardless of expiration)."""
        return key in self._cache
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for cached entry.
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds or None if not found/no TTL
        """
        if key in self._cache:
            cached_data = self._cache[key]
            if isinstance(cached_data, dict) and "_expires_at" in cached_data:
                remaining = cached_data["_expires_at"] - time.time()
                return max(0, int(remaining))
        return None
    
    def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """
        Extend TTL for cached entry.
        
        Args:
            key: Cache key
            additional_seconds: Seconds to add to current TTL
            
        Returns:
            True if TTL was extended, False if key not found
        """
        if key in self._cache:
            cached_data = self._cache[key]
            if isinstance(cached_data, dict) and "_expires_at" in cached_data:
                cached_data["_expires_at"] += additional_seconds
                self._cache[key] = cached_data
                logger.debug(f"Extended TTL for key: {key} by {additional_seconds}s")
                return True
        return False
    
    def clear_all(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self._processing_keys.clear()
        logger.info(f"Cleared all {count} cache entries")