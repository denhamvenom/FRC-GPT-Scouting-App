# backend/tests/test_services/test_game_context_extractor_service.py

import asyncio
import json
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.game_context_extractor_service import (
    GameContextExtractorService,
    ExtractionResult,
    ValidationResult
)
from app.types.game_context_types import (
    validate_extracted_context_schema,
    create_sample_extracted_context,
    ExtractionConfig
)


class TestGameContextExtractorService:
    """Test suite for GameContextExtractorService."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_manual_data(self):
        """Create sample manual data for testing."""
        return {
            "game_name": "REEFSCAPE",
            "relevant_sections": """
            2025 FRC Game: REEFSCAPE
            
            GAME OVERVIEW:
            REEFSCAPE is played on a field with coral reefs and algae processors.
            
            SCORING:
            Autonomous Period (15 seconds):
            - Algae in processor: 4 points
            - Coral placement: 3 points
            
            Teleop Period (135 seconds):
            - Coral L1: 2 points
            - Coral L2: 4 points  
            - Coral L3: 6 points
            - Algae in net: 1 point
            
            Endgame (30 seconds):
            - Shallow climb: 3 points
            - Deep climb: 12 points
            - Barge support: 2 points
            
            STRATEGIC ELEMENTS:
            - Coral placement becomes more valuable at higher levels
            - Algae processing provides consistent scoring
            - Deep climbing requires specialized mechanisms
            """
        }

    @pytest.fixture
    def sample_extracted_context(self):
        """Create sample extracted context for testing."""
        return {
            "game_year": 2025,
            "game_name": "REEFSCAPE", 
            "extraction_version": "1.0",
            "extraction_date": "2025-06-26T10:30:00",
            "scoring_summary": {
                "autonomous": {
                    "duration_seconds": 15,
                    "key_objectives": ["Score algae in processor", "Place coral"],
                    "point_values": {"algae_processor": 4, "coral_placement": 3},
                    "strategic_notes": "Focus on consistent scoring"
                },
                "teleop": {
                    "duration_seconds": 135,
                    "key_objectives": ["Coral placement", "Algae processing"],
                    "point_values": {"coral_L1": 2, "coral_L2": 4, "coral_L3": 6},
                    "strategic_notes": "Higher levels more valuable"
                },
                "endgame": {
                    "duration_seconds": 30,
                    "key_objectives": ["Climbing", "Barge support"],
                    "point_values": {"shallow_climb": 3, "deep_climb": 12},
                    "strategic_notes": "Deep climb high value"
                }
            },
            "strategic_elements": [
                {
                    "name": "Coral Placement",
                    "description": "Scoring coral at different levels",
                    "strategic_value": "high",
                    "alliance_impact": "Essential for competitive scoring"
                }
            ],
            "alliance_considerations": [
                "Balance coral and algae capabilities",
                "Ensure climbing capability"
            ],
            "key_metrics": [
                {
                    "metric_name": "Coral per Match",
                    "description": "Average coral scored",
                    "importance": "high",
                    "calculation_hint": "Total coral divided by matches"
                }
            ],
            "game_pieces": [
                {
                    "name": "Coral",
                    "scoring_locations": ["L1", "L2", "L3"],
                    "point_values": {"L1": 2, "L2": 4, "L3": 6},
                    "strategic_notes": "Higher levels exponentially valuable"
                }
            ]
        }

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client for testing."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        mock_message.content = json.dumps({
            "game_year": 2025,
            "game_name": "REEFSCAPE",
            "scoring_summary": {
                "autonomous": {
                    "duration_seconds": 15,
                    "key_objectives": ["Score algae"],
                    "point_values": {"algae": 4},
                    "strategic_notes": "Focus on consistency"
                },
                "teleop": {
                    "duration_seconds": 135,
                    "key_objectives": ["Score coral"],
                    "point_values": {"coral": 2},
                    "strategic_notes": "Scale with levels"
                },
                "endgame": {
                    "duration_seconds": 30,
                    "key_objectives": ["Climb"],
                    "point_values": {"climb": 12},
                    "strategic_notes": "High value activity"
                }
            },
            "strategic_elements": [],
            "alliance_considerations": [],
            "key_metrics": [],
            "game_pieces": []
        })
        
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        return mock_client

    def test_service_initialization(self, temp_cache_dir):
        """Test service initialization with valid parameters."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        assert service.cache_dir == temp_cache_dir
        assert service.extraction_version == "1.0"
        assert service.max_tokens == 4000
        assert os.path.exists(temp_cache_dir)

    def test_service_initialization_invalid_api_key(self, temp_cache_dir):
        """Test service initialization with invalid API key."""
        with patch('app.services.game_context_extractor_service.OPENAI_API_KEY', None):
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                GameContextExtractorService(cache_dir=temp_cache_dir)

    def test_validate_manual_data_valid(self, temp_cache_dir, sample_manual_data):
        """Test manual data validation with valid data."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        # Should not raise exception
        service._validate_manual_data(sample_manual_data)

    def test_validate_manual_data_invalid(self, temp_cache_dir):
        """Test manual data validation with invalid data."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        # Test missing relevant_sections
        with pytest.raises(ValueError, match="must contain 'relevant_sections'"):
            service._validate_manual_data({"game_name": "Test"})
            
        # Test empty relevant_sections
        with pytest.raises(ValueError, match="cannot be empty"):
            service._validate_manual_data({
                "game_name": "Test",
                "relevant_sections": ""
            })
            
        # Test missing game_name
        with pytest.raises(ValueError, match="must contain 'game_name'"):
            service._validate_manual_data({"relevant_sections": "content"})

    def test_generate_cache_key(self, temp_cache_dir, sample_manual_data):
        """Test cache key generation."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        key1 = service._generate_cache_key(sample_manual_data)
        key2 = service._generate_cache_key(sample_manual_data)
        
        # Same data should generate same key
        assert key1 == key2
        assert len(key1) == 64  # SHA-256 hash length
        
        # Different data should generate different key
        modified_data = sample_manual_data.copy()
        modified_data["relevant_sections"] += " extra content"
        key3 = service._generate_cache_key(modified_data)
        assert key1 != key3

    def test_cache_and_load_extraction(self, temp_cache_dir, sample_extracted_context):
        """Test caching and loading of extraction results."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        # Create extraction result
        result = ExtractionResult(
            success=True,
            extracted_context=sample_extracted_context,
            processing_time=1.5,
            token_usage={"total_tokens": 1000},
            validation_score=0.95
        )
        
        # Cache the result
        cache_key = "test_cache_key"
        service._cache_extraction(cache_key, result)
        
        # Load from cache
        loaded_result = service._load_cached_extraction(cache_key)
        
        assert loaded_result is not None
        assert loaded_result.success is True
        assert loaded_result.extracted_context == sample_extracted_context
        assert loaded_result.processing_time == 1.5
        assert loaded_result.validation_score == 0.95

    def test_load_cached_extraction_missing(self, temp_cache_dir):
        """Test loading extraction when cache file doesn't exist."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        result = service._load_cached_extraction("nonexistent_key")
        assert result is None

    def test_validation_result_creation(self):
        """Test ValidationResult creation and properties."""
        result = ValidationResult(
            is_valid=True,
            completeness_score=0.9,
            accuracy_score=0.8,
            issues=[],
            recommendations=["Add more detail"]
        )
        
        assert result.is_valid is True
        assert abs(result.overall_score - 0.85) < 0.001  # Handle floating point precision

    def test_validate_extraction_valid(self, temp_cache_dir, sample_extracted_context, sample_manual_data):
        """Test validation of valid extracted context."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        validation = service.validate_extraction(sample_extracted_context, sample_manual_data)
        
        assert validation.is_valid is True
        assert validation.completeness_score > 0.8
        assert validation.accuracy_score > 0.8
        assert len(validation.issues) == 0

    def test_validate_extraction_missing_fields(self, temp_cache_dir, sample_manual_data):
        """Test validation with missing required fields."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        incomplete_context = {
            "game_year": 2025,
            # Missing other required fields
        }
        
        validation = service.validate_extraction(incomplete_context, sample_manual_data)
        
        assert validation.is_valid is False
        assert validation.completeness_score < 0.5
        assert len(validation.issues) > 0

    def test_get_extraction_prompt(self, temp_cache_dir):
        """Test extraction prompt generation."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        system_prompt, user_prompt_template = service.get_extraction_prompt()
        
        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt_template, str)
        assert "FRC" in system_prompt
        assert "alliance selection" in system_prompt
        assert "{manual_content}" in user_prompt_template

    @pytest.mark.asyncio
    async def test_extract_game_context_success(self, temp_cache_dir, sample_manual_data, mock_openai_client):
        """Test successful game context extraction."""
        with patch('app.services.game_context_extractor_service.AsyncOpenAI', return_value=mock_openai_client):
            service = GameContextExtractorService(cache_dir=temp_cache_dir)
            
            result = await service.extract_game_context(sample_manual_data)
            
            assert result.success is True
            assert result.extracted_context is not None
            assert "game_year" in result.extracted_context
            assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_extract_game_context_cached(self, temp_cache_dir, sample_manual_data, sample_extracted_context):
        """Test extraction returns cached result when available."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        # Cache a result first
        cache_key = service._generate_cache_key(sample_manual_data)
        cached_result = ExtractionResult(
            success=True,
            extracted_context=sample_extracted_context,
            validation_score=0.9
        )
        service._cache_extraction(cache_key, cached_result)
        
        # Extract should return cached result
        result = await service.extract_game_context(sample_manual_data)
        
        assert result.success is True
        assert result.extracted_context == sample_extracted_context

    @pytest.mark.asyncio
    async def test_extract_game_context_force_refresh(self, temp_cache_dir, sample_manual_data, mock_openai_client):
        """Test extraction with force refresh bypasses cache."""
        with patch('app.services.game_context_extractor_service.AsyncOpenAI', return_value=mock_openai_client):
            service = GameContextExtractorService(cache_dir=temp_cache_dir)
            
            # Cache a result first
            cache_key = service._generate_cache_key(sample_manual_data)
            cached_result = ExtractionResult(success=True, extracted_context={"old": "data"})
            service._cache_extraction(cache_key, cached_result)
            
            # Force refresh should bypass cache and call API
            result = await service.extract_game_context(sample_manual_data, force_refresh=True)
            
            assert result.success is True
            assert mock_openai_client.chat.completions.create.called

    def test_get_cache_info(self, temp_cache_dir, sample_extracted_context):
        """Test cache information retrieval."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        # Add some cached data
        result = ExtractionResult(success=True, extracted_context=sample_extracted_context)
        service._cache_extraction("test_key", result)
        
        cache_info = service.get_cache_info()
        
        assert "cache_directory" in cache_info
        assert cache_info["cached_extractions"] == 1
        assert "extraction_version" in cache_info
        assert len(cache_info["files"]) == 1

    def test_clear_cache(self, temp_cache_dir, sample_extracted_context):
        """Test cache clearing functionality."""
        service = GameContextExtractorService(cache_dir=temp_cache_dir)
        
        # Add multiple cached results
        result = ExtractionResult(success=True, extracted_context=sample_extracted_context)
        service._cache_extraction("test_key_1", result)
        service._cache_extraction("test_key_2", result)
        
        # Clear cache
        clear_result = service.clear_cache()
        
        assert clear_result["cleared_files"] == 2
        assert service.get_cache_info()["cached_extractions"] == 0

    @pytest.mark.asyncio
    async def test_perform_extraction_api_error(self, temp_cache_dir, sample_manual_data):
        """Test extraction handling of API errors."""
        with patch('app.services.game_context_extractor_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            service = GameContextExtractorService(cache_dir=temp_cache_dir)
            
            result = await service._perform_extraction(sample_manual_data)
            
            assert result.success is False
            assert "API Error" in result.error

    @pytest.mark.asyncio 
    async def test_perform_extraction_invalid_json(self, temp_cache_dir, sample_manual_data):
        """Test extraction handling of invalid JSON response."""
        with patch('app.services.game_context_extractor_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            
            mock_message.content = "Invalid JSON content"
            mock_choice.message = mock_message
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            service = GameContextExtractorService(cache_dir=temp_cache_dir)
            
            result = await service._perform_extraction(sample_manual_data)
            
            assert result.success is False
            assert "Failed to parse extraction JSON" in result.error

    @pytest.mark.asyncio
    async def test_perform_extraction_truncated_response(self, temp_cache_dir, sample_manual_data):
        """Test extraction handling of truncated response."""
        with patch('app.services.game_context_extractor_service.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_choice = Mock()
            
            mock_choice.finish_reason = "length"  # Truncated due to length
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            service = GameContextExtractorService(cache_dir=temp_cache_dir)
            
            result = await service._perform_extraction(sample_manual_data)
            
            assert result.success is False
            assert "truncated due to length" in result.error


class TestExtractedContextTypes:
    """Test suite for extracted context type validation."""

    @pytest.fixture
    def sample_extracted_context(self):
        """Create sample extracted context for testing."""
        return {
            "game_year": 2025,
            "game_name": "REEFSCAPE", 
            "extraction_version": "1.0",
            "extraction_date": "2025-06-26T10:30:00",
            "scoring_summary": {
                "autonomous": {
                    "duration_seconds": 15,
                    "key_objectives": ["Score algae in processor", "Place coral"],
                    "point_values": {"algae_processor": 4, "coral_placement": 3},
                    "strategic_notes": "Focus on consistent scoring"
                },
                "teleop": {
                    "duration_seconds": 135,
                    "key_objectives": ["Coral placement", "Algae processing"],
                    "point_values": {"coral_L1": 2, "coral_L2": 4, "coral_L3": 6},
                    "strategic_notes": "Higher levels more valuable"
                },
                "endgame": {
                    "duration_seconds": 30,
                    "key_objectives": ["Climbing", "Barge support"],
                    "point_values": {"shallow_climb": 3, "deep_climb": 12},
                    "strategic_notes": "Deep climb high value"
                }
            },
            "strategic_elements": [
                {
                    "name": "Coral Placement",
                    "description": "Scoring coral at different levels",
                    "strategic_value": "high",
                    "alliance_impact": "Essential for competitive scoring"
                }
            ],
            "alliance_considerations": [
                "Balance coral and algae capabilities",
                "Ensure climbing capability"
            ],
            "key_metrics": [
                {
                    "metric_name": "Coral per Match",
                    "description": "Average coral scored",
                    "importance": "high",
                    "calculation_hint": "Total coral divided by matches"
                }
            ],
            "game_pieces": [
                {
                    "name": "Coral",
                    "scoring_locations": ["L1", "L2", "L3"],
                    "point_values": {"L1": 2, "L2": 4, "L3": 6},
                    "strategic_notes": "Higher levels exponentially valuable"
                }
            ]
        }

    def test_validate_extracted_context_schema_valid(self, sample_extracted_context):
        """Test schema validation with valid context."""
        from app.types.game_context_types import validate_extracted_context_schema
        
        errors = validate_extracted_context_schema(sample_extracted_context)
        assert len(errors) == 0

    def test_validate_extracted_context_schema_missing_fields(self):
        """Test schema validation with missing required fields."""
        from app.types.game_context_types import validate_extracted_context_schema
        
        incomplete_context = {
            "game_year": 2025,
            # Missing other required fields
        }
        
        errors = validate_extracted_context_schema(incomplete_context)
        assert len(errors) > 0
        assert any("Missing required field" in error for error in errors)

    def test_validate_extracted_context_schema_invalid_types(self):
        """Test schema validation with invalid field types."""
        from app.types.game_context_types import validate_extracted_context_schema
        
        invalid_context = {
            "game_year": "not_an_integer",  # Should be int
            "game_name": "Test Game",
            "extraction_version": "1.0",
            "extraction_date": "2025-06-26",
            "scoring_summary": "not_a_dict",  # Should be dict
            "strategic_elements": "not_a_list",  # Should be list
            "alliance_considerations": [],
            "key_metrics": [],
            "game_pieces": []
        }
        
        errors = validate_extracted_context_schema(invalid_context)
        assert len(errors) > 0

    def test_create_sample_extracted_context(self):
        """Test sample context creation."""
        from app.types.game_context_types import create_sample_extracted_context
        
        sample = create_sample_extracted_context()
        
        assert sample.game_year == 2025
        assert sample.game_name == "REEFSCAPE"
        assert len(sample.strategic_elements) > 0
        assert len(sample.key_metrics) > 0


class TestExtractionConfig:
    """Test suite for ExtractionConfig."""

    def test_extraction_config_defaults(self):
        """Test extraction config with default values."""
        from app.types.game_context_types import ExtractionConfig
        
        config = ExtractionConfig()
        
        assert config.max_strategic_elements == 10
        assert config.max_alliance_considerations == 8
        assert config.validation_threshold == 0.8
        assert config.extraction_temperature == 0.1

    def test_extraction_config_custom_values(self):
        """Test extraction config with custom values."""
        from app.types.game_context_types import ExtractionConfig
        
        config = ExtractionConfig(
            max_strategic_elements=5,
            validation_threshold=0.9,
            extraction_temperature=0.2
        )
        
        assert config.max_strategic_elements == 5
        assert config.validation_threshold == 0.9
        assert config.extraction_temperature == 0.2


if __name__ == "__main__":
    pytest.main([__file__])