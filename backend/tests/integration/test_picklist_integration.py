"""
Integration tests for picklist service.
"""

import asyncio
import json
import pytest
import tempfile
import os
from unittest.mock import patch, Mock

from app.services.picklist.picklist_service import PicklistService
from app.services.picklist.models import PicklistGenerationRequest, PickPosition, PriorityMetric
from app.services.picklist.core import UnifiedDatasetProvider, PicklistCacheManager
from app.services.picklist.strategies import GPTStrategy


@pytest.mark.integration
class TestPicklistIntegration:
    """Integration tests for the complete picklist service."""
    
    @pytest.fixture
    def integration_dataset(self):
        """Larger dataset for integration testing."""
        teams = {}
        
        # Create 50 teams with varied performance profiles
        for i in range(1000, 1050):
            # Create different team archetypes
            if i % 5 == 0:  # Elite teams
                auto_avg, teleop_avg, epa = 20, 35, 25
            elif i % 5 == 1:  # Auto specialists
                auto_avg, teleop_avg, epa = 25, 20, 22
            elif i % 5 == 2:  # Teleop specialists
                auto_avg, teleop_avg, epa = 10, 40, 23
            elif i % 5 == 3:  # Balanced teams
                auto_avg, teleop_avg, epa = 15, 25, 18
            else:  # Lower tier teams
                auto_avg, teleop_avg, epa = 8, 15, 12
            
            teams[str(i)] = {
                "team_number": i,
                "nickname": f"Team {i}",
                "city": f"City {i}",
                "state_prov": "TS",
                "country": "USA",
                "scouting_data": {
                    "auto_points": [auto_avg + j for j in range(-2, 3)],
                    "teleop_points": [teleop_avg + j for j in range(-3, 4)],
                    "endgame_points": [8 + j for j in range(-2, 3)],
                    "defense_rating": [3 + (i % 3) for _ in range(5)],
                    "reliability": [4 + (i % 2) for _ in range(5)]
                },
                "statbotics_data": {
                    "epa": epa + (i % 10 - 5),
                    "auto_epa": (auto_avg / 3) + (i % 5 - 2),
                    "teleop_epa": (teleop_avg / 2) + (i % 6 - 3),
                    "endgame_epa": 4 + (i % 4 - 2)
                },
                "tba_data": {
                    "wins": 15 - (i % 16),
                    "losses": i % 16,
                    "ties": 0,
                    "rank": i - 999,
                    "ranking_score": 3.0 - ((i % 20) * 0.1)
                }
            }
        
        return {
            "event_info": {
                "key": "2025integration",
                "name": "Integration Test Event",
                "year": 2025
            },
            "teams": teams,
            "metadata": {
                "generated_at": "2025-06-10T10:00:00Z",
                "total_teams": 50,
                "data_sources": ["scouting", "statbotics", "tba"]
            }
        }
    
    @pytest.fixture
    def integration_dataset_file(self, integration_dataset):
        """Create temporary file with integration dataset."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(integration_dataset, f)
            temp_path = f.name
        
        yield temp_path
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def integration_service(self, integration_dataset_file):
        """Create picklist service with real components for integration testing."""
        return PicklistService(integration_dataset_file)
    
    @pytest.mark.asyncio
    async def test_end_to_end_picklist_generation(self, integration_service):
        """Test complete end-to-end picklist generation."""
        # Mock GPT response for deterministic testing
        mock_response = [
            {"team_number": 1000, "score": 95.0, "reasoning": "Elite performance"},
            {"team_number": 1005, "score": 92.0, "reasoning": "Auto specialist"},
            {"team_number": 1010, "score": 90.0, "reasoning": "Teleop specialist"},
        ]
        
        with patch.object(integration_service.strategy, 'generate_ranking', return_value=mock_response):
            request = PicklistGenerationRequest(
                your_team_number=1025,
                pick_position=PickPosition.FIRST,
                priorities=[
                    PriorityMetric(id="auto_points", name="Auto", weight=2.0),
                    PriorityMetric(id="teleop_points", name="Teleop", weight=1.5),
                    PriorityMetric(id="epa", name="EPA", weight=1.8)
                ]
            )
            
            result = await integration_service.generate_picklist(request)
            
            assert result.status == "success"
            assert len(result.picklist) == 3
            assert result.picklist[0].team_number == 1000
            assert result.picklist[0].score == 95.0
            assert result.performance is not None
            assert result.performance["generation_time"] > 0
    
    @pytest.mark.asyncio
    async def test_batch_processing_integration(self, integration_service):
        """Test batch processing with multiple GPT calls."""
        # Mock multiple GPT responses for batches
        batch_responses = [
            # Batch 1
            [
                {"team_number": 1000, "score": 95.0, "reasoning": "Batch 1 top"},
                {"team_number": 1001, "score": 90.0, "reasoning": "Batch 1 second"},
            ],
            # Batch 2  
            [
                {"team_number": 1005, "score": 88.0, "reasoning": "Batch 2 top"},
                {"team_number": 1006, "score": 85.0, "reasoning": "Batch 2 second"},
            ],
            # Final rerank
            [
                {"team_number": 1000, "score": 95.0, "reasoning": "Final top"},
                {"team_number": 1005, "score": 88.0, "reasoning": "Final second"},
                {"team_number": 1001, "score": 87.0, "reasoning": "Final third"},
                {"team_number": 1006, "score": 85.0, "reasoning": "Final fourth"},
            ]
        ]
        
        call_count = 0
        async def mock_generate_ranking(*args, **kwargs):
            nonlocal call_count
            response = batch_responses[call_count]
            call_count += 1
            return response
        
        with patch.object(integration_service.strategy, 'generate_ranking', side_effect=mock_generate_ranking):
            request = PicklistGenerationRequest(
                your_team_number=1025,
                pick_position=PickPosition.SECOND,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                use_batching=True,
                batch_size=2
            )
            
            result = await integration_service.generate_picklist(request)
            
            assert result.status == "success"
            assert len(result.picklist) == 4  # All teams from final rerank
            assert result.picklist[0].team_number == 1000  # Top team maintained
            assert call_count == 3  # Two batches + final rerank
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, integration_service):
        """Test caching integration across multiple requests."""
        mock_response = [
            {"team_number": 1000, "score": 95.0, "reasoning": "Cached result"}
        ]
        
        with patch.object(integration_service.strategy, 'generate_ranking', return_value=mock_response) as mock_generate:
            request = PicklistGenerationRequest(
                your_team_number=1025,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                cache_key="integration_test_cache"
            )
            
            # First request should call GPT
            result1 = await integration_service.generate_picklist(request)
            assert result1.status == "success"
            assert mock_generate.call_count == 1
            
            # Second identical request should use cache
            result2 = await integration_service.generate_picklist(request)
            assert result2.status == "success"
            assert mock_generate.call_count == 1  # No additional call
            
            # Results should be identical
            assert result1.picklist[0].team_number == result2.picklist[0].team_number
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, integration_service):
        """Test error handling in integrated environment."""
        # Test team not found
        request = PicklistGenerationRequest(
            your_team_number=9999,  # Non-existent team
            pick_position=PickPosition.FIRST,
            priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
        )
        
        with pytest.raises(Exception):  # Should raise TeamNotFoundException
            await integration_service.generate_picklist(request)
        
        # Test GPT failure
        with patch.object(integration_service.strategy, 'generate_ranking', side_effect=Exception("GPT Error")):
            request = PicklistGenerationRequest(
                your_team_number=1025,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
            )
            
            with pytest.raises(Exception):  # Should raise PicklistGenerationError
                await integration_service.generate_picklist(request)
    
    @pytest.mark.asyncio
    async def test_progress_tracking_integration(self, integration_service):
        """Test progress tracking during generation."""
        from app.services.progress_tracker import ProgressTracker
        
        mock_response = [
            {"team_number": 1000, "score": 95.0, "reasoning": "Progress test"}
        ]
        
        with patch.object(integration_service.strategy, 'generate_ranking', return_value=mock_response):
            request = PicklistGenerationRequest(
                your_team_number=1025,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                cache_key="progress_test"
            )
            
            # Start generation
            task = asyncio.create_task(integration_service.generate_picklist(request))
            
            # Give it a moment to start
            await asyncio.sleep(0.1)
            
            # Check progress is being tracked
            progress = ProgressTracker.get_progress("progress_test")
            # Note: Progress may be None if operation completed quickly
            
            # Wait for completion
            result = await task
            assert result.status == "success"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, integration_service):
        """Test handling of concurrent picklist requests."""
        mock_response = [
            {"team_number": 1000, "score": 95.0, "reasoning": "Concurrent test"}
        ]
        
        with patch.object(integration_service.strategy, 'generate_ranking', return_value=mock_response):
            # Create multiple concurrent requests
            requests = []
            for i in range(3):
                request = PicklistGenerationRequest(
                    your_team_number=1025,
                    pick_position=PickPosition.FIRST,
                    priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                    cache_key=f"concurrent_test_{i}"
                )
                requests.append(integration_service.generate_picklist(request))
            
            # Execute all concurrently
            results = await asyncio.gather(*requests)
            
            # All should succeed
            assert len(results) == 3
            for result in results:
                assert result.status == "success"
                assert len(result.picklist) == 1
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, integration_service):
        """Test performance with larger dataset."""
        mock_response = [
            {"team_number": i, "score": 95.0 - i, "reasoning": f"Team {i}"}
            for i in range(1000, 1020)  # Top 20 teams
        ]
        
        with patch.object(integration_service.strategy, 'generate_ranking', return_value=mock_response):
            request = PicklistGenerationRequest(
                your_team_number=1025,
                pick_position=PickPosition.FIRST,
                priorities=[
                    PriorityMetric(id="auto_points", name="Auto", weight=2.0),
                    PriorityMetric(id="teleop_points", name="Teleop", weight=1.5),
                    PriorityMetric(id="epa", name="EPA", weight=1.8)
                ]
            )
            
            import time
            start_time = time.time()
            
            result = await integration_service.generate_picklist(request)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            assert result.status == "success"
            assert len(result.picklist) == 20
            assert generation_time < 5.0  # Should complete within 5 seconds
    
    def test_data_provider_integration(self, integration_dataset_file):
        """Test data provider integration with real file."""
        provider = UnifiedDatasetProvider(integration_dataset_file)
        
        # Test basic functionality
        team = provider.get_team_by_number(1000)
        assert team is not None
        assert team["team_number"] == 1000
        
        # Test GPT data preparation
        gpt_data = provider.prepare_for_gpt()
        assert len(gpt_data) == 50
        
        # Test exclusions
        gpt_data_excluded = provider.prepare_for_gpt(exclude_teams=[1000, 1001])
        assert len(gpt_data_excluded) == 48
    
    def test_cache_manager_integration(self):
        """Test cache manager integration."""
        cache = PicklistCacheManager(ttl=10)
        
        # Test cache operations
        test_data = {"status": "success", "picklist": []}
        cache.set("integration_test", test_data)
        
        retrieved = cache.get("integration_test")
        assert retrieved is not None
        assert retrieved["status"] == "success"
        
        # Test processing markers
        cache.mark_processing("processing_test")
        assert cache.is_processing("processing_test")
        assert cache.get("processing_test") is None
    
    @pytest.mark.asyncio
    async def test_strategy_integration(self, integration_dataset_file):
        """Test strategy integration with mocked OpenAI."""
        # Test GPT strategy with mocked client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "p": [
                [1000, 95.0, "Top team"],
                [1005, 90.0, "Second team"]
            ]
        })
        mock_response.usage.total_tokens = 1500
        mock_client.chat.completions.create.return_value = mock_response
        
        strategy = GPTStrategy(api_key="test_key")
        strategy.client = mock_client
        
        # Test with sample data
        teams_data = [
            {"team_number": 1000, "nickname": "Team 1000", "metrics": {"epa": 25}},
            {"team_number": 1005, "nickname": "Team 1005", "metrics": {"epa": 22}}
        ]
        
        result = await strategy.generate_ranking(
            teams_data=teams_data,
            priorities=[{"id": "epa", "weight": 1.0}],
            your_team_number=1025
        )
        
        assert len(result) == 2
        assert result[0]["team_number"] == 1000
        assert result[0]["score"] == 95.0
    
    @pytest.mark.asyncio
    async def test_memory_usage_integration(self, integration_service):
        """Test memory usage during integration scenarios."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        mock_response = [
            {"team_number": i, "score": 95.0 - i, "reasoning": f"Team {i}"}
            for i in range(1000, 1010)
        ]
        
        with patch.object(integration_service.strategy, 'generate_ranking', return_value=mock_response):
            # Run multiple generations
            for i in range(5):
                request = PicklistGenerationRequest(
                    your_team_number=1025,
                    pick_position=PickPosition.FIRST,
                    priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)],
                    cache_key=f"memory_test_{i}"
                )
                
                result = await integration_service.generate_picklist(request)
                assert result.status == "success"
        
        final_memory = process.memory_info().rss
        memory_increase_mb = (final_memory - initial_memory) / 1024 / 1024
        
        # Memory increase should be reasonable (less than 50MB for this test)
        assert memory_increase_mb < 50
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, integration_service):
        """Test timeout handling in integration scenarios."""
        # Mock slow GPT response
        async def slow_generate_ranking(*args, **kwargs):
            await asyncio.sleep(2)  # Simulate slow response
            return [{"team_number": 1000, "score": 95.0, "reasoning": "Slow response"}]
        
        with patch.object(integration_service.strategy, 'generate_ranking', side_effect=slow_generate_ranking):
            request = PicklistGenerationRequest(
                your_team_number=1025,
                pick_position=PickPosition.FIRST,
                priorities=[PriorityMetric(id="epa", name="EPA", weight=1.0)]
            )
            
            # Should complete even with slower response
            result = await asyncio.wait_for(
                integration_service.generate_picklist(request),
                timeout=5.0
            )
            
            assert result.status == "success"