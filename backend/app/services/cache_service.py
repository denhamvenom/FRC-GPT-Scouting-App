# backend/app/services/cache_service.py

import os
import json
import time
import hashlib
from typing import Any, Optional, Dict, Union, Callable
import asyncio
import functools

# Base directory for cache files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "cache")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


class CacheService:
    """
    Service for caching expensive API calls and computation results.
    """

    # In-memory cache
    _memory_cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _get_cache_key(key_parts: Union[str, Dict[str, Any], list, tuple]) -> str:
        """
        Generate a unique cache key from various input types.

        Args:
            key_parts: String, dictionary, list, or tuple to use for key generation

        Returns:
            A unique hash string for the key parts
        """
        if isinstance(key_parts, str):
            data_str = key_parts
        else:
            data_str = json.dumps(key_parts, sort_keys=True)

        return hashlib.md5(data_str.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_cache_file_path(cache_key: str) -> str:
        """
        Get the file path for a cache key.

        Args:
            cache_key: The cache key

        Returns:
            Path to the cache file
        """
        return os.path.join(CACHE_DIR, f"{cache_key}.json")

    @classmethod
    def get_cached_data(cls, cache_key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """
        Get data from cache if it exists and is not expired.

        Args:
            cache_key: The cache key
            max_age_seconds: Maximum age of the cache in seconds

        Returns:
            Cached data or None if not found or expired
        """
        # Check memory cache first
        if cache_key in cls._memory_cache:
            cache_data = cls._memory_cache[cache_key]
            if time.time() - cache_data["timestamp"] <= max_age_seconds:
                return cache_data["data"]
            # Remove from memory if expired
            del cls._memory_cache[cache_key]

        # Check file cache
        cache_file = cls._get_cache_file_path(cache_key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # Check if cache is still valid
                if time.time() - cache_data["timestamp"] <= max_age_seconds:
                    # Also add to memory cache for faster access next time
                    cls._memory_cache[cache_key] = cache_data
                    return cache_data["data"]
            except Exception as e:
                print(f"Error reading cache file {cache_file}: {e}")

        return None

    @classmethod
    def save_to_cache(cls, cache_key: str, data: Any, persist: bool = True) -> None:
        """
        Save data to cache.

        Args:
            cache_key: The cache key
            data: The data to cache
            persist: Whether to save to disk (True) or just memory (False)
        """
        cache_data = {"timestamp": time.time(), "data": data}

        # Save to memory cache
        cls._memory_cache[cache_key] = cache_data

        # Also save to file if requested
        if persist:
            cache_file = cls._get_cache_file_path(cache_key)
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)
            except Exception as e:
                print(f"Error writing to cache file {cache_file}: {e}")

    @classmethod
    def clear_cache(cls, older_than_seconds: Optional[int] = None) -> int:
        """
        Clear all cache files or only those older than a certain age.

        Args:
            older_than_seconds: If provided, only clear cache older than this many seconds

        Returns:
            Number of cache files removed
        """
        count = 0
        current_time = time.time()

        # Clear memory cache
        if older_than_seconds is None:
            count += len(cls._memory_cache)
            cls._memory_cache.clear()
        else:
            keys_to_remove = []
            for key, data in cls._memory_cache.items():
                if current_time - data["timestamp"] > older_than_seconds:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del cls._memory_cache[key]

            count += len(keys_to_remove)

        # Clear file cache
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(CACHE_DIR, filename)

                if older_than_seconds is not None:
                    # Check if file is old enough to delete
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)

                        if current_time - cache_data["timestamp"] <= older_than_seconds:
                            continue  # Skip this file, it's not old enough
                    except Exception:
                        pass  # If we can't read the file, delete it anyway

                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    print(f"Error removing cache file {file_path}: {e}")

        return count


def cached(max_age_seconds: int = 3600, persist: bool = True):
    """
    Decorator for caching function results.

    Args:
        max_age_seconds: Maximum age of the cache in seconds
        persist: Whether to save to disk (True) or just memory (False)

    Returns:
        Decorated function
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate a cache key from the function name and arguments
            cache_key_parts = {"func": func.__name__, "args": args, "kwargs": kwargs}
            cache_key = CacheService._get_cache_key(cache_key_parts)

            # Try to get from cache
            cached_result = CacheService.get_cached_data(cache_key, max_age_seconds)
            if cached_result is not None:
                return cached_result

            # Not in cache, call the function
            result = await func(*args, **kwargs)

            # Save the result to cache
            CacheService.save_to_cache(cache_key, result, persist)

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate a cache key from the function name and arguments
            cache_key_parts = {"func": func.__name__, "args": args, "kwargs": kwargs}
            cache_key = CacheService._get_cache_key(cache_key_parts)

            # Try to get from cache
            cached_result = CacheService.get_cached_data(cache_key, max_age_seconds)
            if cached_result is not None:
                return cached_result

            # Not in cache, call the function
            result = func(*args, **kwargs)

            # Save the result to cache
            CacheService.save_to_cache(cache_key, result, persist)

            return result

        # Return the appropriate wrapper based on whether the function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
