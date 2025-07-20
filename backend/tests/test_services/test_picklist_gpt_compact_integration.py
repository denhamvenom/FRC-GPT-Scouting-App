# backend/tests/test_services/test_picklist_gpt_compact_integration.py

import json
import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from app.services.picklist_gpt_service import PicklistGPTService


class TestPicklistGPTCompactIntegration:
    """
    Tests for Sprint 2 compact encoding integration with PicklistGPTService.
    Verifies token reduction and functionality preservation.
    """
    
    @pytest.fixture
    def sample_field_selections_2025iri(self) -> Dict[str, Any]:
        """Sample field selections for 2025 IRI event."""
        return {
            "year": 2025,
            "event_key": "2025iri",
            "field_selections": {
                "Team": {"category": "team_number"},
                "Match": {"category": "match_number"},
                "Auto Zone": {
                    "category": "auto",
                    "label_mapping": {
                        "label": "auto_starting_position",
                        "category": "autonomous",
                        "data_type": "text"
                    }
                },
                "Auto piece count (L1/L2/Algae 0.5pc)": {
                    "category": "auto",
                    "label_mapping": {
                        "label": "Auto Total Points",
                        "category": "autonomous",
                        "data_type": "count",
                        "typical_range": "0-40"
                    }
                },
                "Tele Branch Coral Scored (L2-L4)": {
                    "category": "teleop",
                    "label_mapping": {
                        "label": "Teleop CORAL Scored in Branch (L2-L4)",
                        "category": "teleop",
                        "data_type": "count",
                        "typical_range": "0-25"
                    }
                },
                "Notes": {
                    "category": "strategy",
                    "label_mapping": {
                        "label": "scout_comments",
                        "category": "strategic",
                        "data_type": "text"
                    }
                },
                "Endgame Status": {
                    "category": "endgame",
                    "label_mapping": {
                        "label": "endgame_total_points",
                        "category": "endgame",
                        "data_type": "count",
                        "typical_range": "0-15"
                    }
                }
            }
        }
    
    @pytest.fixture
    def sample_team_data(self) -> List[Dict[str, Any]]:
        """Sample team data for testing."""
        return [
            {
                "team_number": 1678,
                "nickname": "Citrus Circuits",
                "weighted_score": 9.2,
                "metrics": {
                    "Auto Total Points": 8.5,
                    "Teleop CORAL Scored in Branch (L2-L4)": 12.3,
                    "endgame_total_points": 10,
                    "teleop_total_points": 25.5
                },
                "text_data": {
                    "scout_comments": "Very consistent autonomous routine. Great driver that can score from anywhere on the field. Climbs reliably every single match without fail.",
                    "auto_starting_position": "Center position near the community"
                }
            },
            {
                "team_number": 254,
                "nickname": "The Cheesy Poofs",
                "weighted_score": 9.5,
                "metrics": {
                    "Auto Total Points": 9.0,
                    "Teleop CORAL Scored in Branch (L2-L4)": 14.5,
                    "endgame_total_points": 12,
                    "teleop_total_points": 28.2
                },
                "text_data": {
                    "scout_comments": "Elite team with extremely fast cycles and excellent strategic decision making. Always adapts to match situation.",
                    "auto_starting_position": "Variable positioning based on strategy"
                }
            },
            {
                "team_number": 118,
                "nickname": "Robonauts",
                "weighted_score": 8.7,
                "metrics": {
                    "Auto Total Points": 7.2,
                    "Teleop CORAL Scored in Branch (L2-L4)": 11.8,
                    "endgame_total_points": 9,
                    "teleop_total_points": 22.1
                },
                "text_data": {
                    "scout_comments": "Solid all around team. Sometimes has intake mechanism issues but recovers well and continues scoring."
                }
            },
            {
                "team_number": 1421,
                "nickname": "Team Chaos",
                "weighted_score": 8.1,
                "metrics": {
                    "Auto Total Points": 6.8,
                    "Teleop CORAL Scored in Branch (L2-L4)": 10.2,
                    "endgame_total_points": 8,
                    "teleop_total_points": 19.5
                },
                "text_data": {
                    "scout_comments": "Inconsistent performance. Sometimes exceptional, sometimes struggles with basic tasks."
                }
            },
            {
                "team_number": 2036,
                "nickname": "InTech MegaBots",
                "weighted_score": 7.8,
                "metrics": {
                    "Auto Total Points": 5.5,
                    "Teleop CORAL Scored in Branch (L2-L4)": 9.8,
                    "endgame_total_points": 7,
                    "teleop_total_points": 18.2
                },
                "text_data": {
                    "scout_comments": "Decent robot but drivers need more practice. Mechanical issues in several matches."
                }
            }
        ]
    
    @pytest.fixture
    def sample_priorities(self) -> List[Dict[str, Any]]:
        """Sample priorities for testing."""
        return [
            {"id": "Auto Total Points", "weight": 0.3},
            {"id": "Teleop CORAL Scored in Branch (L2-L4)", "weight": 0.4},
            {"id": "endgame_total_points", "weight": 0.3}
        ]
    
    def test_service_initialization_with_compact_encoding(self):
        """Test service initializes with compact encoding enabled."""
        service = PicklistGPTService()
        assert service.use_compact_encoding == True
        assert service.compact_encoder is None  # Not initialized until needed
    
    def test_compact_encoder_initialization(self, tmp_path, sample_field_selections_2025iri):
        """Test compact encoder is initialized correctly."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = PicklistGPTService()
        
        # Initialize with data directory override
        service.initialize_compact_encoder(2025, "2025iri")
        
        # Patch the data directory
        with patch('app.services.compact_data_encoding_service.CompactDataEncodingService.__init__') as mock_init:
            mock_init.return_value = None
            service.initialize_compact_encoder(2025, "2025iri")
            mock_init.assert_called_once_with(2025, "2025iri")
    
    def test_create_user_prompt_compact_vs_standard(self, tmp_path, sample_field_selections_2025iri, 
                                                   sample_team_data, sample_priorities):
        """Test user prompt generation with compact vs standard encoding."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = PicklistGPTService()
        
        # Test standard encoding
        standard_prompt, standard_map, standard_lookup = service.create_user_prompt(
            your_team_number=1678,
            pick_position="first",
            priorities=sample_priorities,
            teams_data=sample_team_data,
            force_index_mapping=True
        )
        
        # Test compact encoding
        service.initialize_compact_encoder(2025, "2025iri")
        with patch.object(service.compact_encoder, 'data_dir', str(data_dir)):
            compact_prompt, compact_map, compact_lookup = service.create_user_prompt(
                your_team_number=1678,
                pick_position="first",
                priorities=sample_priorities,
                teams_data=sample_team_data,
                force_index_mapping=True,
                year=2025,
                event_key="2025iri"
            )
        
        # Verify both return valid data
        assert standard_prompt is not None
        assert compact_prompt is not None
        assert standard_map == compact_map  # Same team index mapping
        assert standard_lookup is None  # No lookup tables for standard
        assert compact_lookup is not None  # Lookup tables for compact
        
        # Verify compact format has lookup tables
        assert "METRIC_CODES" in compact_lookup
        assert "TEAM_INDEX_MAP" in compact_lookup
        assert "METRIC_ORDER" in compact_lookup
        
        # Verify token reduction
        standard_size = len(standard_prompt)
        compact_size = len(compact_prompt)
        reduction_percent = ((standard_size - compact_size) / standard_size) * 100
        
        # Should achieve significant reduction
        assert reduction_percent > 30, f"Expected >30% reduction, got {reduction_percent:.1f}%"
    
    def test_system_prompt_with_lookup_tables(self, tmp_path, sample_field_selections_2025iri):
        """Test system prompt includes lookup tables when compact encoding is used."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = PicklistGPTService()
        service.initialize_compact_encoder(2025, "2025iri")
        
        # Create sample lookup tables
        lookup_tables = {
            "METRIC_CODES": {"AP": "Auto Total Points", "TC": "Teleop CORAL Scored in Branch (L2-L4)"},
            "TEAM_INDEX_MAP": {1: 1678, 2: 254, 3: 118},
            "METRIC_ORDER": ["AP", "TC"]
        }
        
        # Test system prompt with lookup tables
        system_prompt = service.create_system_prompt(
            pick_position="first",
            team_count=3,
            game_context="Test game context",
            use_ultra_compact=True,
            lookup_tables=lookup_tables
        )
        
        # Verify lookup tables are included
        assert "METRIC CODES:" in system_prompt
        assert '"AP":"Auto Total Points"' in system_prompt
        assert "DATA FORMAT:" in system_prompt
        assert "Metrics are in this order:" in system_prompt
    
    def test_text_data_compression_with_compact_encoding(self, tmp_path, sample_field_selections_2025iri):
        """Test text data compression works correctly with compact encoding."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = PicklistGPTService()
        service.initialize_compact_encoder(2025, "2025iri")
        
        # Test text compression
        long_text_data = {
            "scout_comments": "This robot has an extremely consistent autonomous routine that scores multiple game pieces during the autonomous period. The teleoperated period shows great driver skill with fast cycling times and strategic positioning. Endgame climbing is very reliable and they help alliance partners climb as well.",
            "auto_starting_position": "Center position near the community zone"
        }
        
        compressed = service._optimize_text_data(long_text_data)
        
        # Should return compressed format
        assert "_compressed" in compressed
        assert len(compressed["_compressed"]) < 100  # Should be significantly shorter
    
    def test_end_to_end_token_reduction(self, tmp_path, sample_field_selections_2025iri,
                                       sample_team_data, sample_priorities):
        """Test end-to-end token reduction across system and user prompts."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = PicklistGPTService()
        
        # Generate standard prompts
        standard_user_prompt, standard_map, _ = service.create_user_prompt(
            your_team_number=1678,
            pick_position="first",
            priorities=sample_priorities,
            teams_data=sample_team_data,
            force_index_mapping=True
        )
        
        standard_system_prompt = service.create_system_prompt(
            pick_position="first",
            team_count=len(sample_team_data),
            game_context="Test game context",
            use_ultra_compact=True
        )
        
        # Generate compact prompts
        service.initialize_compact_encoder(2025, "2025iri")
        with patch.object(service.compact_encoder, 'data_dir', str(data_dir)):
            compact_user_prompt, compact_map, lookup_tables = service.create_user_prompt(
                your_team_number=1678,
                pick_position="first",
                priorities=sample_priorities,
                teams_data=sample_team_data,
                force_index_mapping=True,
                year=2025,
                event_key="2025iri"
            )
        
        compact_system_prompt = service.create_system_prompt(
            pick_position="first",
            team_count=len(sample_team_data),
            game_context="Test game context",
            use_ultra_compact=True,
            lookup_tables=lookup_tables
        )
        
        # Calculate total token reduction
        standard_total = len(standard_system_prompt) + len(standard_user_prompt)
        compact_total = len(compact_system_prompt) + len(compact_user_prompt)
        
        total_reduction = ((standard_total - compact_total) / standard_total) * 100
        
        # Should achieve Sprint 2 goal of 40% additional reduction
        assert total_reduction > 40, f"Expected >40% total reduction, got {total_reduction:.1f}%"
        
        # Log the results for verification
        print(f"\nTOKEN REDUCTION RESULTS:")
        print(f"Standard system prompt: {len(standard_system_prompt)} chars")
        print(f"Compact system prompt: {len(compact_system_prompt)} chars")
        print(f"Standard user prompt: {len(standard_user_prompt)} chars")
        print(f"Compact user prompt: {len(compact_user_prompt)} chars")
        print(f"Total reduction: {total_reduction:.1f}%")
    
    def test_backward_compatibility_when_compact_disabled(self, sample_team_data, sample_priorities):
        """Test service works normally when compact encoding is disabled."""
        service = PicklistGPTService()
        service.use_compact_encoding = False
        
        # Should work without compact encoding
        prompt, index_map, lookup_tables = service.create_user_prompt(
            your_team_number=1678,
            pick_position="first",
            priorities=sample_priorities,
            teams_data=sample_team_data,
            force_index_mapping=True
        )
        
        assert prompt is not None
        assert index_map is not None
        assert lookup_tables is None  # No lookup tables when compact disabled
    
    def test_compact_encoding_fallback_on_error(self, sample_team_data, sample_priorities):
        """Test service falls back to standard encoding when compact encoding fails."""
        service = PicklistGPTService()
        
        # Try to use compact encoding without proper initialization
        prompt, index_map, lookup_tables = service.create_user_prompt(
            your_team_number=1678,
            pick_position="first",
            priorities=sample_priorities,
            teams_data=sample_team_data,
            force_index_mapping=True,
            year=2025,
            event_key="2025nonexistent"  # Non-existent event
        )
        
        # Should fall back to standard encoding
        assert prompt is not None
        assert index_map is not None
        assert lookup_tables is None  # No lookup tables when compact fails
    
    def test_metric_filtering_with_compact_encoding(self, tmp_path, sample_field_selections_2025iri,
                                                   sample_team_data, sample_priorities):
        """Test metric filtering works correctly with compact encoding."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = PicklistGPTService()
        service.initialize_compact_encoder(2025, "2025iri")
        
        # Store priorities for metric filtering
        service._current_priorities = sample_priorities
        
        # Test metric filtering
        with patch.object(service.compact_encoder, 'data_dir', str(data_dir)):
            prompt, index_map, lookup_tables = service.create_user_prompt(
                your_team_number=1678,
                pick_position="first",
                priorities=sample_priorities,
                teams_data=sample_team_data,
                force_index_mapping=True,
                year=2025,
                event_key="2025iri"
            )
        
        # Verify metric codes are generated
        assert lookup_tables is not None
        assert "METRIC_CODES" in lookup_tables
        assert len(lookup_tables["METRIC_CODES"]) > 0