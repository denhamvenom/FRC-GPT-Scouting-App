"""
Enhanced test coverage for edge cases and advanced scenarios.
"""

import pytest
import json
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from app.services.picklist.picklist_service import PicklistService
from app.services.picklist.models import (
    PicklistGenerationRequest,
    PickPosition,
    PriorityMetric,
    RankedTeam,
    PicklistGenerationResult
)
from app.services.picklist.exceptions import (
    PicklistValidationError,
    TeamNotFoundException,
    PicklistGenerationError,
    GPTResponseError
)


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    @pytest.fixture
    def service_with_mocks(self):
        """Create service with all mocked dependencies."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"teams": {}, "metadata": {"total_teams": 0}}, f)
            temp_path = f.name
        
        service = PicklistService(temp_path)
        service.data_provider = Mock()
        service.strategy = AsyncMock()
        service.cache_manager = Mock()
        
        yield service
        
        os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_empty_dataset_handling(self, service_with_mocks):
        """Test handling of empty datasets."""
        service_with_mocks.data_provider.get_team_by_number.return_value = None
        service_with_mocks.data_provider.prepare_for_gpt.return_value = []
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        with pytest.raises(TeamNotFoundException):
            await service_with_mocks.generate_picklist(request)
    
    @pytest.mark.asyncio
    async def test_single_team_dataset(self, service_with_mocks):
        """Test handling of dataset with only one team."""
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Only Team"
        }
        service_with_mocks.data_provider.prepare_for_gpt.return_value = [
            {"team_number": 1001, "nickname": "Only Team", "metrics": {"epa": 20}}
        ]
        service_with_mocks.strategy.generate_ranking.return_value = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Only choice"}
        ]
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        result = await service_with_mocks.generate_picklist(request)
        
        assert result.status == "success"
        assert len(result.picklist) == 1
        assert result.picklist[0].team_number == 1001
    
    @pytest.mark.asyncio
    async def test_extremely_large_dataset(self, service_with_mocks):
        """Test handling of extremely large datasets."""
        # Mock 1000 teams
        large_dataset = []
        for i in range(1000, 2000):
            large_dataset.append({
                "team_number": i,
                "nickname": f"Team {i}",
                "metrics": {"epa": 20 + (i % 10)}
            })
        
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Your Team"
        }
        service_with_mocks.data_provider.prepare_for_gpt.return_value = large_dataset
        
        # Mock strategy to return subset
        service_with_mocks.strategy.generate_ranking.return_value = [
            {"team_number": i, "score": 95.0 - i + 1000, "reasoning": f"Team {i}"}
            for i in range(1000, 1050)  # Top 50
        ]
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        result = await service_with_mocks.generate_picklist(request)
        
        assert result.status == "success"
        assert len(result.picklist) == 50
    
    def test_invalid_priority_weights(self, service_with_mocks):
        """Test validation of invalid priority weights."""
        invalid_requests = [
            # Negative weight
            PicklistGenerationRequest(
                your_team_number=1001,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=-1.0)]
            ),
            # Zero weight
            PicklistGenerationRequest(
                your_team_number=1001,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=0.0)]
            ),
            # Extremely large weight
            PicklistGenerationRequest(
                your_team_number=1001,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1000000.0)]
            )
        ]
        
        for request in invalid_requests:
            with pytest.raises(PicklistValidationError):
                service_with_mocks._validate_request(request)
    
    def test_duplicate_priority_metrics(self, service_with_mocks):
        """Test handling of duplicate priority metrics."""
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[
                PriorityMetric(id="epa", name="EPA", weight=1.0),
                PriorityMetric(id="epa", name="EPA Duplicate", weight=2.0)
            ]
        )
        
        with pytest.raises(PicklistValidationError) as exc_info:
            service_with_mocks._validate_request(request)
        
        assert "duplicate" in str(exc_info.value).lower()
    
    def test_invalid_team_numbers(self, service_with_mocks):
        """Test validation of invalid team numbers."""
        invalid_requests = [
            # Negative team number
            PicklistGenerationRequest(
                your_team_number=-1,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
            ),
            # Zero team number
            PicklistGenerationRequest(
                your_team_number=0,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
            ),
            # Extremely large team number
            PicklistGenerationRequest(
                your_team_number=999999,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
            )
        ]
        
        for request in invalid_requests:
            with pytest.raises(PicklistValidationError):
                service_with_mocks._validate_request(request)
    
    @pytest.mark.asyncio
    async def test_cache_corruption_handling(self, service_with_mocks):
        """Test handling of corrupted cache data."""
        # Mock corrupted cache data
        corrupted_data = "invalid_cache_data"
        service_with_mocks.cache_manager.get.return_value = corrupted_data
        
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Test Team"
        }
        service_with_mocks.data_provider.prepare_for_gpt.return_value = [
            {"team_number": 1001, "metrics": {"epa": 20}}
        ]
        service_with_mocks.strategy.generate_ranking.return_value = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Fresh result"}
        ]
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        # Should handle corruption gracefully and regenerate
        result = await service_with_mocks.generate_picklist(request)
        assert result.status == "success"
    
    @pytest.mark.asyncio
    async def test_partial_gpt_response_handling(self, service_with_mocks):
        """Test handling of partial or incomplete GPT responses."""
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Test Team"
        }
        service_with_mocks.data_provider.prepare_for_gpt.return_value = [
            {"team_number": 1001, "metrics": {"epa": 20}},
            {"team_number": 1002, "metrics": {"epa": 18}},
            {"team_number": 1003, "metrics": {"epa": 22}}
        ]
        
        # Mock partial response (missing some teams)
        service_with_mocks.strategy.generate_ranking.return_value = [
            {"team_number": 1003, "score": 95.0, "reasoning": "Top team"}
            # Missing teams 1001 and 1002
        ]
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        result = await service_with_mocks.generate_picklist(request)
        
        # Should handle gracefully
        assert result.status == "success"
        assert len(result.picklist) == 1  # Only returned team
        assert result.missing_team_numbers == [1001, 1002]
    
    @pytest.mark.asyncio
    async def test_memory_pressure_scenarios(self, service_with_mocks):
        """Test behavior under memory pressure."""
        # Mock memory-intensive operations
        huge_dataset = []
        for i in range(10000):  # Very large dataset
            huge_dataset.append({
                "team_number": i,
                "nickname": f"Team {i}",
                "metrics": {"epa": 20, "data": "x" * 1000}  # Large data per team
            })
        
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Test Team"
        }
        service_with_mocks.data_provider.prepare_for_gpt.return_value = huge_dataset
        
        # Mock strategy that handles large data
        service_with_mocks.strategy.generate_ranking.return_value = [
            {"team_number": i, "score": 95.0 - i, "reasoning": f"Team {i}"}
            for i in range(100)  # Return top 100
        ]
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        # Should complete without memory errors
        result = await service_with_mocks.generate_picklist(request)
        assert result.status == "success"
    
    @pytest.mark.asyncio
    async def test_concurrent_modification_handling(self, service_with_mocks):
        """Test handling of concurrent modifications to data."""
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Test Team"
        }
        
        call_count = 0
        def mock_prepare_for_gpt(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [{"team_number": 1001, "metrics": {"epa": 20}}]
            else:
                # Data changed between calls
                return [
                    {"team_number": 1001, "metrics": {"epa": 20}},
                    {"team_number": 1002, "metrics": {"epa": 18}}
                ]
        
        service_with_mocks.data_provider.prepare_for_gpt.side_effect = mock_prepare_for_gpt
        service_with_mocks.strategy.generate_ranking.return_value = [
            {"team_number": 1001, "score": 95.0, "reasoning": "Test"}
        ]
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        # Should handle gracefully
        result = await service_with_mocks.generate_picklist(request)
        assert result.status == "success"
    
    def test_unicode_and_special_characters(self, service_with_mocks):
        """Test handling of unicode and special characters."""
        special_priorities = [
            PriorityMetric(id="特殊_metric", name="Spëcíàl Mëtrïc", weight=1.0),
            PriorityMetric(id="metric_with_emoji_🤖", name="Robot Metric", weight=1.5),
            PriorityMetric(id="metric with spaces", name="Spaced Metric", weight=2.0)
        ]
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=special_priorities
        )
        
        # Should handle unicode gracefully
        service_with_mocks._validate_request(request)  # Should not raise
        cache_key = service_with_mocks._create_cache_key(request)
        assert isinstance(cache_key, str)
    
    @pytest.mark.asyncio
    async def test_infinite_loop_prevention(self, service_with_mocks):
        """Test prevention of infinite loops in retry logic."""
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Test Team"
        }
        service_with_mocks.data_provider.prepare_for_gpt.return_value = [
            {"team_number": 1001, "metrics": {"epa": 20}}
        ]
        
        # Mock strategy that always fails
        service_with_mocks.strategy.generate_ranking.side_effect = Exception("Always fails")
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        # Should eventually give up and raise error
        with pytest.raises(PicklistGenerationError):
            await service_with_mocks.generate_picklist(request)
        
        # Should not have infinite retries
        assert service_with_mocks.strategy.generate_ranking.call_count <= 5
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_on_failure(self, service_with_mocks):
        """Test that resources are cleaned up on failure."""
        service_with_mocks.data_provider.get_team_by_number.return_value = {
            "team_number": 1001,
            "nickname": "Test Team"
        }
        service_with_mocks.data_provider.prepare_for_gpt.return_value = [
            {"team_number": 1001, "metrics": {"epa": 20}}
        ]
        service_with_mocks.strategy.generate_ranking.side_effect = Exception("Failure")
        
        request = PicklistGenerationRequest(
            your_team_number=1001,
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
            cache_key="cleanup_test"
        )
        
        with pytest.raises(PicklistGenerationError):
            await service_with_mocks.generate_picklist(request)
        
        # Cache should be cleaned up (processing marker removed)
        service_with_mocks.cache_manager.delete.assert_called()


class TestPerformanceAndScalability:
    """Test performance and scalability scenarios."""
    
    @pytest.fixture
    def performance_service(self):
        """Create service optimized for performance testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Large realistic dataset
            teams = {}
            for i in range(1000, 1500):  # 500 teams
                teams[str(i)] = {
                    "team_number": i,
                    "nickname": f"Team {i}",
                    "scouting_data": {
                        "auto_points": [10 + (i % 15) for _ in range(7)],
                        "teleop_points": [20 + (i % 20) for _ in range(7)]
                    },
                    "statbotics_data": {"epa": 15 + (i % 10)},
                    "tba_data": {"rank": i - 999}
                }
            
            dataset = {
                "teams": teams,
                "metadata": {"total_teams": 500}
            }
            json.dump(dataset, f)
            temp_path = f.name
        
        service = PicklistService(temp_path)
        
        yield service
        
        os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, performance_service, performance_timer):
        """Test performance with large datasets."""
        # Mock fast GPT response
        mock_response = [
            {"team_number": i, "score": 95.0 - (i - 1000), "reasoning": f"Team {i}"}
            for i in range(1000, 1100)  # Top 100
        ]
        
        with patch.object(performance_service.strategy, 'generate_ranking', return_value=mock_response):
            request = PicklistGenerationRequest(
                your_team_number=1250,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
            )
            
            performance_timer.start()
            result = await performance_service.generate_picklist(request)
            performance_timer.stop()
            
            assert result.status == "success"
            assert len(result.picklist) == 100
            assert performance_timer.elapsed < 2.0  # Should complete within 2 seconds
    
    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, performance_service, memory_tracker):
        """Test memory usage stays reasonable."""
        mock_response = [
            {"team_number": i, "score": 95.0 - (i - 1000), "reasoning": f"Team {i}"}
            for i in range(1000, 1050)
        ]
        
        with patch.object(performance_service.strategy, 'generate_ranking', return_value=mock_response):
            memory_tracker.start()
            
            # Run multiple generations
            for i in range(10):
                request = PicklistGenerationRequest(
                    your_team_number=1250,
                    pick_position=PickPosition.FIRST,
                    priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                    cache_key=f"memory_test_{i}"
                )
                
                result = await performance_service.generate_picklist(request)
                assert result.status == "success"
            
            memory_tracker.stop()
            
            # Memory increase should be reasonable
            assert memory_tracker.memory_delta_mb < 100  # Less than 100MB increase
    
    @pytest.mark.asyncio
    async def test_concurrent_request_scaling(self, performance_service):
        """Test handling of many concurrent requests."""
        mock_response = [
            {"team_number": 1000, "score": 95.0, "reasoning": "Top team"}
        ]
        
        with patch.object(performance_service.strategy, 'generate_ranking', return_value=mock_response):
            # Create many concurrent requests
            tasks = []
            for i in range(20):  # 20 concurrent requests
                request = PicklistGenerationRequest(
                    your_team_number=1250,
                    pick_position=PickPosition.FIRST,
                    priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                    cache_key=f"concurrent_{i}"
                )
                task = performance_service.generate_picklist(request)
                tasks.append(task)
            
            # Execute all concurrently with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=10.0
            )
            
            # All should succeed
            assert len(results) == 20
            for result in results:
                assert result.status == "success"
    
    @pytest.mark.asyncio
    async def test_cache_performance_impact(self, performance_service, performance_timer):
        """Test performance impact of caching."""
        mock_response = [
            {"team_number": 1000, "score": 95.0, "reasoning": "Cached test"}
        ]
        
        with patch.object(performance_service.strategy, 'generate_ranking', return_value=mock_response):
            request = PicklistGenerationRequest(
                your_team_number=1250,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                cache_key="cache_performance_test"
            )
            
            # First request (uncached)
            performance_timer.start()
            result1 = await performance_service.generate_picklist(request)
            performance_timer.stop()
            uncached_time = performance_timer.elapsed
            
            # Second request (cached)
            performance_timer.start()
            result2 = await performance_service.generate_picklist(request)
            performance_timer.stop()
            cached_time = performance_timer.elapsed
            
            assert result1.status == "success"
            assert result2.status == "success"
            assert cached_time < uncached_time * 0.1  # Cached should be much faster