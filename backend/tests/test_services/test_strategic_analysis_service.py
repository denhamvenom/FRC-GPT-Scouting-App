# backend/tests/test_services/test_strategic_analysis_service.py

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from app.services.strategic_analysis_service import StrategicAnalysisService
from app.types.performance_signature_types import EventPerformanceBaselines, EventBaseline, MetricStatistics
from app.types.strategic_analysis_types import (
    StrategicTier, StrategicRole, classify_strategic_tier, determine_strategic_role
)


@pytest.fixture
def service():
    """Create a StrategicAnalysisService instance for testing."""
    return StrategicAnalysisService()


@pytest.fixture
def sample_teams_data():
    """Create sample teams data for testing."""
    return [
        {
            "team_number": 8044,
            "nickname": "Denham Venom",
            "metrics": {
                "auto_coral_L4": 1.33,
                "teleop_total": 59.4,
                "endgame_total": 1.56,
                "match_count": 7
            },
            "match_count": 7
        },
        {
            "team_number": 16,
            "nickname": "Bomb Squad",
            "metrics": {
                "auto_coral_L4": 2.1,
                "teleop_total": 67.0,
                "endgame_total": 9.11,
                "match_count": 8
            },
            "match_count": 8
        },
        {
            "team_number": 364,
            "nickname": "Miracle",
            "metrics": {
                "auto_coral_L4": 0.5,
                "teleop_total": 23.89,
                "endgame_total": 2.1,
                "match_count": 6
            },
            "match_count": 6
        },
        {
            "team_number": 2973,
            "nickname": "Mad Rockers",
            "metrics": {
                "auto_coral_L4": 1.8,
                "teleop_total": 45.2,
                "endgame_total": 5.6,
                "match_count": 9
            },
            "match_count": 9
        },
        {
            "team_number": 1421,
            "nickname": "Chaos Theory",
            "metrics": {
                "auto_coral_L4": 0.9,
                "teleop_total": 38.7,
                "endgame_total": 7.2,
                "match_count": 5
            },
            "match_count": 5
        }
    ]


@pytest.fixture
def sample_event_baselines():
    """Create sample event baselines for testing."""
    auto_stats = MetricStatistics(
        mean=1.3, std=0.6, median=1.2, min_value=0.5, max_value=2.1,
        sample_size=5, coefficient_of_variation=0.46
    )
    
    teleop_stats = MetricStatistics(
        mean=46.8, std=17.2, median=45.2, min_value=23.89, max_value=67.0,
        sample_size=5, coefficient_of_variation=0.37
    )
    
    return EventPerformanceBaselines(
        event_key="test_event",
        year=2025,
        baselines={
            "auto_coral_L4": EventBaseline(
                metric_name="auto_coral_L4",
                statistics=auto_stats,
                percentiles={"10th": 0.5, "25th": 0.9, "50th": 1.2, "75th": 1.8, "90th": 2.1},
                field_size=5,
                top_performers=1
            ),
            "teleop_total": EventBaseline(
                metric_name="teleop_total",
                statistics=teleop_stats,
                percentiles={"10th": 23.89, "25th": 38.7, "50th": 45.2, "75th": 59.4, "90th": 67.0},
                field_size=5,
                top_performers=1
            )
        },
        total_teams=5,
        avg_matches_per_team=7.0,
        event_level="regional",
        competitive_context={"data_quality": "good"}
    )


class TestStrategicAnalysisService:
    """Test cases for StrategicAnalysisService."""
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.batch_size == 20
        assert service.max_tokens_limit == 100000
        assert service.client is not None
        assert service.token_encoder is not None
    
    def test_calculate_event_baselines_success(self, service, sample_teams_data):
        """Test successful event baseline calculation."""
        baselines = service.calculate_event_baselines(sample_teams_data)
        
        assert isinstance(baselines, EventPerformanceBaselines)
        assert baselines.total_teams == 5
        assert baselines.event_level == "regional"
        assert len(baselines.baselines) >= 3  # Should have auto, teleop, endgame metrics
        
        # Check specific baseline
        auto_baseline = baselines.baselines.get("auto_coral_L4")
        assert auto_baseline is not None
        assert auto_baseline.field_size == 5
        assert auto_baseline.statistics.sample_size == 5
    
    def test_calculate_event_baselines_insufficient_teams(self, service):
        """Test event baseline calculation with insufficient teams."""
        teams_data = [{"team_number": 1, "metrics": {"test": 1.0}}]  # Only 1 team
        
        with pytest.raises(ValueError, match="Insufficient teams for baseline calculation"):
            service.calculate_event_baselines(teams_data)
    
    def test_calculate_event_baselines_no_metrics(self, service):
        """Test event baseline calculation with no numeric metrics."""
        teams_data = [
            {"team_number": 1, "metrics": {"text_fields": {"notes": "good"}}},
            {"team_number": 2, "metrics": {"text_fields": {"notes": "bad"}}},
            {"team_number": 3, "metrics": {"text_fields": {"notes": "ok"}}},
            {"team_number": 4, "metrics": {"text_fields": {"notes": "great"}}},
            {"team_number": 5, "metrics": {"text_fields": {"notes": "average"}}}
        ]
        
        with pytest.raises(ValueError, match="No numeric metrics found in team data"):
            service.calculate_event_baselines(teams_data)
    
    def test_create_team_batches(self, service, sample_teams_data):
        """Test team batch creation."""
        batches = service.create_team_batches(sample_teams_data)
        
        assert len(batches) == 1  # 5 teams should fit in 1 batch (batch_size=20)
        assert len(batches[0]) == 5
        assert batches[0] == sample_teams_data
    
    def test_create_team_batches_multiple(self, service):
        """Test team batch creation with multiple batches."""
        # Create 45 teams to test multiple batches
        teams_data = []
        for i in range(45):
            teams_data.append({
                "team_number": i + 1,
                "nickname": f"Team {i + 1}",
                "metrics": {"test_metric": float(i)}
            })
        
        batches = service.create_team_batches(teams_data)
        
        assert len(batches) == 3  # 45 teams / 20 batch_size = 3 batches
        assert len(batches[0]) == 20
        assert len(batches[1]) == 20
        assert len(batches[2]) == 5
    
    def test_create_index_mapping(self, service, sample_teams_data):
        """Test index mapping creation."""
        index_map = service.create_index_mapping(sample_teams_data)
        
        expected_map = {1: 8044, 2: 16, 3: 364, 4: 2973, 5: 1421}
        assert index_map == expected_map
    
    def test_create_system_prompt(self, service):
        """Test system prompt creation."""
        prompt = service.create_system_prompt(batch_number=1, total_batches=3)
        
        assert "batch 1 of 3" in prompt
        assert "strategic intelligence" in prompt.lower()
        assert "event statistical context" in prompt.lower()
        assert "NO hardcoded game knowledge" in prompt
        assert "JSON" in prompt
    
    def test_create_batch_payload(self, service, sample_teams_data, sample_event_baselines):
        """Test batch payload creation."""
        index_map = {1: 8044, 2: 16, 3: 364}
        batch_teams = sample_teams_data[:3]
        
        payload = service.create_batch_payload(
            batch_teams, index_map, sample_event_baselines, 1, 2
        )
        
        assert payload["task"] == "Generate strategic signatures for batch 1/2"
        assert payload["batch_info"]["batch_number"] == 1
        assert payload["batch_info"]["total_batches"] == 2
        assert payload["batch_info"]["teams_in_batch"] == 3
        assert payload["team_index_map"] == index_map
        assert "event_baselines" in payload
        assert "teams" in payload
        assert len(payload["teams"]) == 3
        
        # Check team data structure
        team_data = payload["teams"][0]
        assert team_data["index"] == 1
        assert team_data["team"] == 8044
        assert "performance_data" in team_data
    
    def test_validate_batch_response_success(self, service):
        """Test successful batch response validation."""
        response = {
            "team_signatures": [
                {"index": 1, "team": 8044},
                {"index": 2, "team": 16},
                {"index": 3, "team": 364}
            ]
        }
        expected_indices = [1, 2, 3]
        
        is_valid, message = service.validate_batch_response(response, expected_indices)
        
        assert is_valid is True
        assert message == "All expected teams processed"
    
    def test_validate_batch_response_missing_teams(self, service):
        """Test batch response validation with missing teams."""
        response = {
            "team_signatures": [
                {"index": 1, "team": 8044},
                {"index": 3, "team": 364}
            ]
        }
        expected_indices = [1, 2, 3]
        
        is_valid, message = service.validate_batch_response(response, expected_indices)
        
        assert is_valid is False
        assert "Missing teams: [2]" in message
    
    def test_validate_batch_response_no_signatures(self, service):
        """Test batch response validation with missing team_signatures."""
        response = {"batch_info": {"status": "complete"}}
        expected_indices = [1, 2, 3]
        
        is_valid, message = service.validate_batch_response(response, expected_indices)
        
        assert is_valid is False
        assert message == "Missing team_signatures in response"
    
    @pytest.mark.asyncio
    @patch('app.services.strategic_analysis_service.AsyncOpenAI')
    async def test_execute_api_call_success(self, mock_openai_class, service):
        """Test successful API call execution."""
        # Mock the OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"status": "success", "team_signatures": []}'
        mock_response.choices[0].finish_reason = "stop"
        
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        # Replace the service client
        service.client = mock_client
        
        result = await service._execute_api_call("system prompt", "user prompt")
        
        assert result["status"] == "success"
        assert "response_data" in result
        assert result["response_data"]["status"] == "success"
    
    @pytest.mark.asyncio
    @patch('app.services.strategic_analysis_service.AsyncOpenAI')
    async def test_execute_api_call_rate_limit(self, mock_openai_class, service):
        """Test API call with rate limit error."""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("429 Rate limit exceeded")
        )
        mock_openai_class.return_value = mock_client
        
        service.client = mock_client
        
        result = await service._execute_api_call("system prompt", "user prompt")
        
        assert result["status"] == "error"
        assert result["error_type"] == "rate_limit"
        assert "429" in result["error"]
    
    @pytest.mark.asyncio
    @patch('app.services.strategic_analysis_service.AsyncOpenAI')
    async def test_execute_api_call_json_error(self, mock_openai_class, service):
        """Test API call with invalid JSON response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'invalid json content'
        mock_response.choices[0].finish_reason = "stop"
        
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client
        
        service.client = mock_client
        
        result = await service._execute_api_call("system prompt", "user prompt")
        
        assert result["status"] == "error"
        assert result["error_type"] == "json_parse_error"
        assert "invalid json content" in result["raw_content"]
    
    @pytest.mark.asyncio
    async def test_process_batch_success(self, service, sample_teams_data, sample_event_baselines):
        """Test successful batch processing."""
        batch_teams = sample_teams_data[:3]
        
        # Mock the API call to return a successful response
        mock_response_data = {
            "batch_info": {"batch_number": 1, "teams_processed": 3, "processing_status": "complete"},
            "team_signatures": [
                {
                    "index": 1,
                    "team": 8044,
                    "enhanced_metrics": {"auto_coral_L4": "1.33±0.7 (strong_consistent, n=7)"},
                    "strategic_profile": "offensive_powerhouse"
                },
                {
                    "index": 2,
                    "team": 16,
                    "enhanced_metrics": {"auto_coral_L4": "2.1±0.5 (dominant_reliable, n=8)"},
                    "strategic_profile": "balanced_contributor"
                },
                {
                    "index": 3,
                    "team": 364,
                    "enhanced_metrics": {"auto_coral_L4": "0.5±0.3 (developing_volatile, n=6)"},
                    "strategic_profile": "developing_team"
                }
            ],
            "batch_insights": {
                "standout_performers": [1, 2],
                "developing_teams": [3]
            }
        }
        
        with patch.object(service, '_execute_api_call_with_retry', return_value={
            "status": "success", "response_data": mock_response_data
        }):
            result = await service.process_batch(batch_teams, sample_event_baselines, 1, 2)
        
        assert result["status"] == "success"
        assert result["teams_processed"] == 3
        assert result["batch_number"] == 1
        assert len(result["signatures"]) == 3
        
        # Check signature format
        signature_8044 = result["signatures"][8044]
        assert signature_8044["team_number"] == 8044
        assert "enhanced_metrics" in signature_8044
        assert signature_8044["strategic_profile"] == "offensive_powerhouse"
    
    @pytest.mark.asyncio
    async def test_process_batch_validation_failure(self, service, sample_teams_data, sample_event_baselines):
        """Test batch processing with validation failure."""
        batch_teams = sample_teams_data[:3]
        
        # Mock response missing a team
        mock_response_data = {
            "team_signatures": [
                {"index": 1, "team": 8044},
                {"index": 3, "team": 364}
                # Missing index 2
            ]
        }
        
        with patch.object(service, '_execute_api_call_with_retry', return_value={
            "status": "success", "response_data": mock_response_data
        }):
            result = await service.process_batch(batch_teams, sample_event_baselines, 1, 2)
        
        assert result["status"] == "error"
        assert "Response validation failed" in result["error"]
        assert "Missing teams: [2]" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_strategic_intelligence_success(self, service, sample_teams_data):
        """Test successful strategic intelligence generation."""
        # Mock the process_batch method to return successful results
        mock_batch_result = {
            "status": "success",
            "signatures": {
                8044: {
                    "team_number": 8044,
                    "enhanced_metrics": {"auto_coral_L4": "1.33±0.7 (strong_consistent, n=7)"},
                    "strategic_profile": "offensive_powerhouse",
                    "batch_number": 1
                }
            },
            "batch_insights": {"standout_performers": [8044]},
            "processing_time": 1.5,
            "teams_processed": 1
        }
        
        with patch.object(service, 'process_batch', return_value=mock_batch_result):
            result = await service.generate_strategic_intelligence(sample_teams_data)
        
        assert result["status"] == "success"
        assert "strategic_signatures" in result
        assert "event_baselines" in result
        assert "processing_summary" in result
        assert result["processing_summary"]["total_teams"] == 5
        assert result["processing_summary"]["successful_batches"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_strategic_intelligence_insufficient_teams(self, service):
        """Test strategic intelligence generation with insufficient teams."""
        teams_data = [{"team_number": 1, "metrics": {"test": 1.0}}]  # Only 1 team
        
        with pytest.raises(ValueError, match="Insufficient teams for strategic analysis"):
            await service.generate_strategic_intelligence(teams_data)
    
    @pytest.mark.asyncio
    async def test_generate_strategic_intelligence_all_batches_fail(self, service, sample_teams_data):
        """Test strategic intelligence generation when all batches fail."""
        # Mock all batches to fail
        mock_batch_result = {
            "status": "error",
            "error": "API call failed",
            "batch_number": 1
        }
        
        with patch.object(service, 'process_batch', return_value=mock_batch_result):
            with pytest.raises(ValueError, match="All batches failed during strategic analysis"):
                await service.generate_strategic_intelligence(sample_teams_data)


class TestStrategicAnalysisTypes:
    """Test cases for strategic analysis type functions."""
    
    def test_classify_strategic_tier(self):
        """Test strategic tier classification."""
        assert classify_strategic_tier(95.0) == StrategicTier.DOMINANT
        assert classify_strategic_tier(80.0) == StrategicTier.STRONG
        assert classify_strategic_tier(60.0) == StrategicTier.SOLID
        assert classify_strategic_tier(30.0, "improving") == StrategicTier.DEVELOPING
        assert classify_strategic_tier(20.0) == StrategicTier.STRUGGLING
    
    def test_determine_strategic_role(self):
        """Test strategic role determination."""
        from app.types.strategic_analysis_types import StrategicSignature
        
        # Create mock signatures for testing
        signatures = {
            "auto_metric": StrategicSignature(
                metric_name="auto_metric",
                base_signature="2.1±0.5",
                strategic_qualifier="dominant_auto_specialist",
                percentile_rank=90.0,
                field_context="field_mean_1.2"
            ),
            "teleop_metric": StrategicSignature(
                metric_name="teleop_metric", 
                base_signature="45.2±8.1",
                strategic_qualifier="solid_consistent",
                percentile_rank=60.0,
                field_context="field_mean_42.1"
            )
        }
        
        role = determine_strategic_role(signatures, 75.0)
        assert role == StrategicRole.AUTO_SPECIALIST
    
    def test_determine_strategic_role_balanced(self):
        """Test strategic role determination for balanced performer."""
        from app.types.strategic_analysis_types import StrategicSignature
        
        # Create signatures with multiple strong areas
        signatures = {}
        for i, metric in enumerate(["auto", "teleop", "endgame", "defense"]):
            signatures[metric] = StrategicSignature(
                metric_name=metric,
                base_signature="5.0±1.0",
                strategic_qualifier="strong_consistent",
                percentile_rank=80.0,
                field_context="field_mean_3.0"
            )
        
        role = determine_strategic_role(signatures, 85.0)
        assert role == StrategicRole.VERSATILE_PERFORMER


if __name__ == "__main__":
    pytest.main([__file__])