# backend/tests/test_services/test_data_aggregation_extraction_integration.py

import asyncio
import json
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.data_aggregation_service import DataAggregationService
from app.services.game_context_extractor_service import ExtractionResult


class TestDataAggregationExtractionIntegration:
    """Test integration between DataAggregationService and GameContextExtractorService."""

    @pytest.fixture
    def temp_dataset_file(self):
        """Create a temporary dataset file for testing."""
        dataset = {
            "year": 2025,
            "event_key": "2025arc",
            "teams": {
                "1001": {
                    "team_number": 1001,
                    "nickname": "Test Team 1",
                    "scouting_data": []
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dataset, f)
            yield f.name
        
        os.unlink(f.name)

    @pytest.fixture
    def temp_manual_file(self, temp_dataset_file):
        """Create a temporary manual file for testing."""
        manual_data = {
            "game_name": "REEFSCAPE Test",
            "relevant_sections": "Test game manual content with scoring and strategy information."
        }
        
        # Create manual file in expected location relative to dataset
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(temp_dataset_file)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        manual_path = os.path.join(data_dir, "manual_text_2025.json")
        with open(manual_path, 'w', encoding='utf-8') as f:
            json.dump(manual_data, f)
        
        yield manual_path
        
        if os.path.exists(manual_path):
            os.unlink(manual_path)

    @pytest.fixture
    def mock_extraction_result(self):
        """Create a mock extraction result."""
        return ExtractionResult(
            success=True,
            extracted_context={
                "game_year": 2025,
                "game_name": "REEFSCAPE Test",
                "extraction_version": "1.0",
                "extraction_date": "2025-06-26T10:30:00",
                "scoring_summary": {
                    "autonomous": {
                        "duration_seconds": 15,
                        "key_objectives": ["Score algae", "Place coral"],
                        "point_values": {"algae": 4, "coral": 3},
                        "strategic_notes": "Focus on consistency"
                    },
                    "teleop": {
                        "duration_seconds": 135,
                        "key_objectives": ["Strategic scoring"],
                        "point_values": {"coral_L1": 2, "coral_L2": 4},
                        "strategic_notes": "Higher levels more valuable"
                    },
                    "endgame": {
                        "duration_seconds": 30,
                        "key_objectives": ["Climbing"],
                        "point_values": {"climb": 12},
                        "strategic_notes": "High value activity"
                    }
                },
                "strategic_elements": [
                    {
                        "name": "Coral Placement",
                        "description": "Strategic coral scoring",
                        "strategic_value": "high",
                        "alliance_impact": "Essential for success"
                    }
                ],
                "alliance_considerations": ["Balance capabilities", "Ensure climb capability"],
                "key_metrics": [
                    {
                        "metric_name": "Coral per Match",
                        "description": "Average coral scored",
                        "importance": "high",
                        "calculation_hint": "Total / matches"
                    }
                ]
            },
            processing_time=1.5,
            validation_score=0.95,
            token_usage={"total_tokens": 1000}
        )

    def test_service_initialization_with_extraction_enabled(self, temp_dataset_file):
        """Test service initialization with extraction enabled."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService'):
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            assert service.use_extracted_context is True
            assert service.extractor_service is not None

    def test_service_initialization_with_extraction_disabled(self, temp_dataset_file):
        """Test service initialization with extraction disabled."""
        service = DataAggregationService(temp_dataset_file, use_extracted_context=False)
        
        assert service.use_extracted_context is False
        assert service.extractor_service is None

    def test_service_initialization_extraction_failure_fallback(self, temp_dataset_file):
        """Test fallback when extraction service initialization fails."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService', side_effect=Exception("Init failed")):
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            assert service.use_extracted_context is False
            assert service.extractor_service is None

    def test_load_game_context_extracted_mode_success(self, temp_dataset_file, temp_manual_file, mock_extraction_result):
        """Test loading game context in extracted mode with successful extraction."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            # Mock the async extraction method
            async def mock_extract(manual_data, force_refresh=False):
                return mock_extraction_result
            
            mock_extractor.extract_game_context = mock_extract
            
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            # Load context
            context = service.load_game_context()
            
            assert context is not None
            assert "REEFSCAPE Test" in context
            assert "SCORING SUMMARY" in context
            assert "AUTONOMOUS" in context
            assert "STRATEGIC ELEMENTS" in context

    def test_load_game_context_extracted_mode_failure_fallback(self, temp_dataset_file, temp_manual_file):
        """Test fallback to full manual when extraction fails."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            # Mock failed extraction
            failed_result = ExtractionResult(success=False, error="Extraction failed")
            
            async def mock_extract(manual_data, force_refresh=False):
                return failed_result
            
            mock_extractor.extract_game_context = mock_extract
            
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            # Load context should fall back to full manual
            context = service.load_game_context()
            
            assert context is not None
            assert "REEFSCAPE Test" in context
            assert "Test game manual content" in context

    def test_load_game_context_full_mode(self, temp_dataset_file, temp_manual_file):
        """Test loading game context in full manual mode."""
        service = DataAggregationService(temp_dataset_file, use_extracted_context=False)
        
        context = service.load_game_context()
        
        assert context is not None
        assert "Game: REEFSCAPE Test" in context
        assert "Test game manual content" in context

    def test_load_game_context_no_manual_file(self, temp_dataset_file):
        """Test loading context when manual file doesn't exist."""
        service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
        
        context = service.load_game_context()
        
        assert context is None

    def test_force_extract_game_context_success(self, temp_dataset_file, temp_manual_file, mock_extraction_result):
        """Test forced extraction with success."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            async def mock_extract(manual_data, force_refresh=False):
                return mock_extraction_result
            
            mock_extractor.extract_game_context = mock_extract
            
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            result = service.force_extract_game_context()
            
            assert result["success"] is True
            assert "extraction_result" in result
            assert result["validation_score"] == 0.95

    def test_force_extract_game_context_no_extractor(self, temp_dataset_file):
        """Test forced extraction when extractor not available."""
        service = DataAggregationService(temp_dataset_file, use_extracted_context=False)
        
        result = service.force_extract_game_context()
        
        assert result["success"] is False
        assert "Extraction service not available" in result["error"]

    def test_force_extract_game_context_no_manual(self, temp_dataset_file):
        """Test forced extraction when manual not available."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService'):
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            result = service.force_extract_game_context()
            
            assert result["success"] is False
            assert "Manual data not available" in result["error"]

    def test_get_extraction_status_extracted_mode(self, temp_dataset_file, temp_manual_file):
        """Test extraction status in extracted mode."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            mock_extractor.get_cache_info.return_value = {"cached_extractions": 1}
            mock_extractor._generate_cache_key.return_value = "test_key"
            mock_extractor._load_cached_extraction.return_value = None
            
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            status = service.get_extraction_status()
            
            assert status["extraction_enabled"] is True
            assert status["extractor_available"] is True
            assert status["manual_available"] is True
            assert status["year"] == 2025
            assert "game_name" in status

    def test_get_extraction_status_full_mode(self, temp_dataset_file, temp_manual_file):
        """Test extraction status in full mode."""
        service = DataAggregationService(temp_dataset_file, use_extracted_context=False)
        
        status = service.get_extraction_status()
        
        assert status["extraction_enabled"] is False
        assert status["extractor_available"] is False
        assert status["manual_available"] is True

    def test_set_extraction_mode_enable(self, temp_dataset_file):
        """Test enabling extraction mode."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService'):
            service = DataAggregationService(temp_dataset_file, use_extracted_context=False)
            
            result = service.set_extraction_mode(True)
            
            assert result["success"] is True
            assert result["current_mode"] == "extracted"
            assert service.use_extracted_context is True

    def test_set_extraction_mode_disable(self, temp_dataset_file):
        """Test disabling extraction mode."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService'):
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            result = service.set_extraction_mode(False)
            
            assert result["success"] is True
            assert result["current_mode"] == "full"
            assert service.use_extracted_context is False

    def test_set_extraction_mode_error_revert(self, temp_dataset_file):
        """Test error handling and mode reversion."""
        service = DataAggregationService(temp_dataset_file, use_extracted_context=False)
        
        with patch('app.services.data_aggregation_service.GameContextExtractorService', side_effect=Exception("Init failed")):
            result = service.set_extraction_mode(True)
            
            assert result["success"] is False
            assert result["current_mode"] == "full"
            assert service.use_extracted_context is False

    def test_get_dataset_metadata_includes_extraction_info(self, temp_dataset_file):
        """Test that dataset metadata includes extraction information."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService'):
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            metadata = service.get_dataset_metadata()
            
            assert "extraction_mode" in metadata
            assert "extraction_available" in metadata
            assert metadata["extraction_mode"] == "extracted"
            assert metadata["extraction_available"] is True

    def test_context_formatting_consistency(self, temp_dataset_file, temp_manual_file, mock_extraction_result):
        """Test that extracted context formatting is consistent and usable."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            async def mock_extract(manual_data, force_refresh=False):
                return mock_extraction_result
            
            mock_extractor.extract_game_context = mock_extract
            
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            context = service.load_game_context()
            
            # Verify expected structure
            assert "Game: REEFSCAPE Test (2025)" in context
            assert "SCORING SUMMARY:" in context
            assert "AUTONOMOUS (15s):" in context
            assert "TELEOP (135s):" in context
            assert "ENDGAME (30s):" in context
            assert "STRATEGIC ELEMENTS:" in context
            assert "ALLIANCE CONSIDERATIONS:" in context
            assert "KEY METRICS:" in context
            
            # Verify it's significantly smaller than full manual
            assert len(context) < 1000  # Should be much smaller than typical manual

    def test_async_context_handling(self, temp_dataset_file, temp_manual_file, mock_extraction_result):
        """Test proper handling of async extraction in sync context."""
        with patch('app.services.data_aggregation_service.GameContextExtractorService') as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            
            # Track async context handling
            extraction_called = False
            
            async def mock_extract(manual_data, force_refresh=False):
                nonlocal extraction_called
                extraction_called = True
                return mock_extraction_result
            
            mock_extractor.extract_game_context = mock_extract
            
            service = DataAggregationService(temp_dataset_file, use_extracted_context=True)
            
            # This should handle async properly in sync context
            context = service.load_game_context()
            
            assert extraction_called is True
            assert context is not None


if __name__ == "__main__":
    pytest.main([__file__])