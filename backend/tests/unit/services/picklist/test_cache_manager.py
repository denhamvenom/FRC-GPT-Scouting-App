"""
Unit tests for PicklistCacheManager.
"""

import pytest
import time
from unittest.mock import Mock, patch

from app.services.picklist.core.cache_manager import PicklistCacheManager
from app.services.picklist.models import PicklistGenerationResult, RankedTeam


class TestPicklistCacheManager:
    """Test PicklistCacheManager functionality."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance for testing."""
        # Clear class-level cache before each test
        PicklistCacheManager._cache.clear()
        PicklistCacheManager._processing_keys.clear()
        return PicklistCacheManager(ttl=3600)
    
    @pytest.fixture
    def sample_result(self):
        """Sample picklist result for caching."""
        return {
            "status": "success",
            "picklist": [
                {
                    "team_number": 1001,
                    "nickname": "Team Alpha",
                    "score": 95.0,
                    "reasoning": "Top performer",
                    "rank": 1,
                }
            ],
            "analysis": {"total_teams": 1},
            "missing_team_numbers": [],
            "performance": {"generation_time": 10.5},
        }
    
    def test_cache_initialization(self, cache_manager):
        """Test cache manager initialization."""
        assert cache_manager.ttl == 3600
        assert cache_manager._cache == {}
        assert cache_manager._processing_keys == {}
    
    def test_get_empty_cache(self, cache_manager):
        """Test getting from empty cache."""
        result = cache_manager.get("nonexistent_key")
        assert result is None
    
    def test_set_and_get(self, cache_manager, sample_result):
        """Test setting and getting cache values."""
        key = "test_key"
        cache_manager.set(key, sample_result)
        
        retrieved = cache_manager.get(key)
        assert retrieved is not None
        assert retrieved["status"] == "success"
        assert len(retrieved["picklist"]) == 1
    
    def test_cache_expiration(self, cache_manager, sample_result):
        """Test cache expiration."""
        key = "expiring_key"
        
        # Set cache with very short TTL
        cache_manager.ttl = 1
        cache_manager.set(key, sample_result)
        
        # Should be retrievable immediately
        assert cache_manager.get(key) is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache_manager.get(key) is None
    
    def test_mark_processing(self, cache_manager):
        """Test marking key as processing."""
        key = "processing_key"
        cache_manager.mark_processing(key)
        
        # Should return None when processing
        assert cache_manager.get(key) is None
        assert cache_manager.is_processing(key) is True
    
    def test_processing_timeout(self, cache_manager):
        """Test processing timeout cleanup."""
        key = "timeout_key"
        
        # Manually set processing marker with old timestamp
        cache_manager._cache[key] = time.time() - 200  # 200 seconds ago
        
        # Should clean up stale processing marker
        result = cache_manager.get(key)
        assert result is None
        assert key not in cache_manager._cache
    
    def test_clear_cache(self, cache_manager, sample_result):
        """Test clearing cache."""
        cache_manager.set("key1", sample_result)
        cache_manager.set("key2", sample_result)
        cache_manager.mark_processing("key3")
        
        cache_manager.clear_all()
        
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.is_processing("key3") is False
    
    def test_get_stats(self, cache_manager, sample_result):
        """Test getting cache statistics."""
        cache_manager.set("cached_key", sample_result)
        cache_manager.mark_processing("processing_key")
        
        stats = cache_manager.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["processing_entries"] == 1
        assert "expired_entries" in stats
        assert "cache_keys" in stats
    
    def test_delete_specific_key(self, cache_manager, sample_result):
        """Test deleting specific cache key."""
        key = "delete_me"
        cache_manager.set(key, sample_result)
        
        assert cache_manager.get(key) is not None
        
        cache_manager.delete(key)
        
        assert cache_manager.get(key) is None
    
    def test_get_all_keys(self, cache_manager, sample_result):
        """Test getting all cache keys."""
        cache_manager.set("key1", sample_result)
        cache_manager.set("key2", sample_result)
        cache_manager.mark_processing("key3")
        
        keys = cache_manager.get_all_keys()
        
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
    
    def test_shared_cache_between_instances(self, sample_result):
        """Test that cache is shared between instances."""
        manager1 = PicklistCacheManager()
        manager2 = PicklistCacheManager()
        
        manager1.set("shared_key", sample_result)
        
        # Should be accessible from second instance
        assert manager2.get("shared_key") is not None
    
    def test_update_batch_status(self, cache_manager):
        """Test batch status updates."""
        key = "batch_test"
        batch_info = {
            "current_batch": 2,
            "total_batches": 5,
            "progress": 40
        }
        
        cache_manager.update_batch_status(key, batch_info)
        
        # Get the cached entry to check batch info was stored
        cached_entry = cache_manager._cache.get(key)
        assert cached_entry is not None
        assert "batch_processing" in cached_entry
        assert cached_entry["batch_processing"] == batch_info
    
    def test_ttl_operations(self, cache_manager, sample_result):
        """Test TTL-related operations."""
        key = "ttl_test"
        cache_manager.set(key, sample_result, ttl=10)
        
        # Should have TTL
        ttl = cache_manager.get_ttl(key)
        assert ttl is not None
        assert ttl <= 10
        
        # Should be able to extend TTL
        success = cache_manager.extend_ttl(key, 5)
        assert success is True
        
        new_ttl = cache_manager.get_ttl(key)
        assert new_ttl > ttl
    
    def test_expired_cleanup(self, cache_manager, sample_result):
        """Test cleanup of expired entries."""
        # Manually create expired entry by setting expiration in past
        expired_result = sample_result.copy()
        expired_result["_expires_at"] = time.time() - 10  # Expired 10 seconds ago
        cache_manager._cache["expired_key"] = expired_result
        
        cache_manager.set("normal", sample_result)
        
        # Clean up expired entries
        expired_count = cache_manager.clear_expired()
        assert expired_count == 1
        
        # Normal entry should still exist, expired should be gone
        assert cache_manager.get("normal") is not None
        assert cache_manager.get("expired_key") is None
    
    def test_cache_key_operations(self, cache_manager, sample_result):
        """Test various cache key operations."""
        # Valid keys should work
        cache_manager.set("valid_key", sample_result)
        assert cache_manager.get("valid_key") is not None
        assert cache_manager.exists("valid_key") is True
        
        # Non-existent keys
        assert cache_manager.exists("nonexistent") is False
        assert cache_manager.get("nonexistent") is None
    
    def test_wait_for_processing(self, cache_manager, sample_result):
        """Test waiting for processing to complete."""
        key = "wait_test"
        
        # Mark as processing
        cache_manager.mark_processing(key)
        
        # Should return None while processing
        result = cache_manager.wait_for_processing(key, timeout=1)
        assert result is None
        
        # Set result and wait again
        cache_manager.set(key, sample_result)
        result = cache_manager.wait_for_processing(key, timeout=1)
        assert result is not None
    
    def test_processing_status_tracking(self, cache_manager):
        """Test processing status tracking."""
        key = "status_test"
        
        # Mark as processing
        cache_manager.mark_processing(key)
        
        # Get processing status
        status = cache_manager.get_processing_status(key)
        assert status is not None
        assert status["status"] == "processing"
        assert "started_at" in status
        assert "elapsed_seconds" in status