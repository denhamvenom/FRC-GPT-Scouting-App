# backend/tests/test_services/test_compact_data_encoding.py

import json
import os
import pytest
import tempfile
from typing import Dict, Any, List

from app.services.compact_data_encoding_service import CompactDataEncodingService


class TestCompactDataEncodingService:
    """
    Comprehensive tests for CompactDataEncodingService.
    Tests agnostic behavior with multiple years and events.
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
    def sample_field_selections_2025lake(self) -> Dict[str, Any]:
        """Sample field selections for 2025 Lake event with different metrics."""
        return {
            "year": 2025,
            "event_key": "2025lake",
            "field_selections": {
                "Team Number": {"category": "team_number"},
                "Match Num": {"category": "match_number"},
                "Auto Points Scored": {
                    "category": "auto",
                    "label_mapping": {
                        "label": "Auto Total Points",
                        "category": "autonomous",
                        "data_type": "count"
                    }
                },
                "Teleop Game Pieces": {
                    "category": "teleop",
                    "label_mapping": {
                        "label": "teleop_total_pieces",
                        "category": "teleop",
                        "data_type": "count"
                    }
                },
                "Defense Time": {
                    "category": "defense",
                    "label_mapping": {
                        "label": "defense_time_seconds",
                        "category": "defensive",
                        "data_type": "count"
                    }
                },
                "Driver Rating": {
                    "category": "driver",
                    "label_mapping": {
                        "label": "driver_skill_rating",
                        "category": "subjective",
                        "data_type": "rating",
                        "typical_range": "1-5"
                    }
                },
                "Match Notes": {
                    "category": "notes",
                    "label_mapping": {
                        "label": "scout_comments",
                        "category": "strategic",
                        "data_type": "text"
                    }
                }
            }
        }
    
    @pytest.fixture
    def sample_field_selections_2024champs(self) -> Dict[str, Any]:
        """Sample field selections for 2024 Championships (different game)."""
        return {
            "year": 2024,
            "event_key": "2024champs",
            "field_selections": {
                "Team": {"category": "team_number"},
                "Match": {"category": "match_number"},
                "Auto Mobility": {
                    "category": "auto",
                    "label_mapping": {
                        "label": "auto_mobility_achieved",
                        "category": "autonomous",
                        "data_type": "boolean"
                    }
                },
                "Auto Notes Scored": {
                    "category": "auto",
                    "label_mapping": {
                        "label": "Auto Total Points",
                        "category": "autonomous",
                        "data_type": "count"
                    }
                },
                "Teleop Speaker": {
                    "category": "teleop",
                    "label_mapping": {
                        "label": "teleop_speaker_notes",
                        "category": "teleop",
                        "data_type": "count"
                    }
                },
                "Teleop Amp": {
                    "category": "teleop",
                    "label_mapping": {
                        "label": "teleop_amp_notes",
                        "category": "teleop",
                        "data_type": "count"
                    }
                },
                "Climb Status": {
                    "category": "endgame",
                    "label_mapping": {
                        "label": "endgame_climb_status",
                        "category": "endgame",
                        "data_type": "text"
                    }
                },
                "Comments": {
                    "category": "notes",
                    "label_mapping": {
                        "label": "scout_comments",
                        "category": "strategic",
                        "data_type": "text"
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
                    "teleop_total_pieces": 12.3,
                    "endgame_total_points": 10,
                    "driver_skill_rating": 4.8,
                    "defense_time_seconds": 15.2
                },
                "text_data": {
                    "scout_comments": "Very consistent autonomous routine. Great driver that can score from anywhere. Climbs reliably every match.",
                    "auto_starting_position": "Center position"
                }
            },
            {
                "team_number": 254,
                "nickname": "The Cheesy Poofs",
                "weighted_score": 9.5,
                "metrics": {
                    "Auto Total Points": 9.0,
                    "teleop_total_pieces": 14.5,
                    "endgame_total_points": 12,
                    "driver_skill_rating": 5.0,
                    "defense_time_seconds": 8.5
                },
                "text_data": {
                    "scout_comments": "Elite team. Fast cycles and excellent strategy.",
                    "auto_starting_position": "Variable"
                }
            },
            {
                "team_number": 118,
                "nickname": "Robonauts",
                "weighted_score": 8.7,
                "metrics": {
                    "Auto Total Points": 7.2,
                    "teleop_total_pieces": 11.8,
                    "endgame_total_points": 9,
                    "driver_skill_rating": 4.5
                },
                "text_data": {
                    "scout_comments": "Solid all around. Sometimes has intake issues but recovers well."
                }
            }
        ]
    
    def test_init_with_valid_data(self, tmp_path, sample_field_selections_2025iri):
        """Test initialization with valid field selections."""
        # Create temporary data directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Write field selections file
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        # Initialize service
        service = CompactDataEncodingService(2025, "2025iri", str(data_dir))
        
        assert service.year == 2025
        assert service.event_key == "2025iri"
        assert service.event_code == "iri"
        assert len(service.field_selections) > 0
        assert len(service.metric_codes) > 0
    
    def test_metric_code_generation_common_metrics(self, tmp_path, sample_field_selections_2025iri):
        """Test that common metrics get consistent short codes."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = CompactDataEncodingService(2025, "2025iri", str(data_dir))
        
        # Check common metric codes
        assert "AP" in service.metric_codes  # Auto Points
        assert service.metric_codes["AP"] == "Auto Total Points"
        
        assert "EP" in service.metric_codes  # Endgame Points
        assert service.metric_codes["EP"] == "endgame_total_points"
        
        assert "SC" in service.metric_codes  # Scout Comments
        assert service.metric_codes["SC"] == "scout_comments"
    
    def test_metric_code_generation_unique_metrics(self, tmp_path, sample_field_selections_2025iri):
        """Test that unique metrics get intelligently abbreviated codes."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = CompactDataEncodingService(2025, "2025iri", str(data_dir))
        
        # Check that teleop coral metric gets an abbreviation
        coral_code = None
        for code, name in service.metric_codes.items():
            if "CORAL" in name:
                coral_code = code
                break
        
        assert coral_code is not None
        assert len(coral_code) <= 4  # Should be reasonably short
    
    def test_different_events_different_codes(self, tmp_path, sample_field_selections_2025iri, 
                                            sample_field_selections_2025lake):
        """Test that different events generate appropriate codes for their metrics."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Setup IRI event
        filepath_iri = data_dir / "field_selections_2025iri.json"
        with open(filepath_iri, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        # Setup Lake event
        filepath_lake = data_dir / "field_selections_2025lake.json"
        with open(filepath_lake, "w") as f:
            json.dump(sample_field_selections_2025lake, f)
        
        # Create services for both events
        service_iri = CompactDataEncodingService(2025, "2025iri", str(data_dir))
        service_lake = CompactDataEncodingService(2025, "2025lake", str(data_dir))
        
        # Both should have Auto Points with same code
        assert "AP" in service_iri.metric_codes
        assert "AP" in service_lake.metric_codes
        
        # Lake should have unique codes for its metrics
        assert "DR" in service_lake.metric_codes  # Driver Rating
        assert service_lake.metric_codes["DR"] == "driver_skill_rating"
        
        # Check defense time
        defense_code = None
        for code, name in service_lake.metric_codes.items():
            if "defense_time" in name:
                defense_code = code
                break
        assert defense_code is not None
    
    def test_encode_decode_reversibility(self, tmp_path, sample_field_selections_2025lake, sample_team_data):
        """Test that encoding and decoding is fully reversible."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025lake.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025lake, f)
        
        service = CompactDataEncodingService(2025, "2025lake", str(data_dir))
        
        # Encode teams
        encoded_teams = []
        for i, team in enumerate(sample_team_data, start=1):
            encoded = service.encode_team_to_array(team, i)
            encoded_teams.append(encoded)
        
        # Create lookup tables
        lookup_tables = service.create_lookup_tables(sample_team_data)
        
        # Decode teams
        for i, encoded in enumerate(encoded_teams):
            decoded = service.decode_array_to_team(encoded, lookup_tables)
            original = sample_team_data[i]
            
            # Check basic fields
            assert decoded["team_number"] == original["team_number"]
            assert decoded["nickname"] == original["nickname"]
            assert decoded["weighted_score"] == original["weighted_score"]
            
            # Check metrics (may not have all if some are 0)
            for metric, value in original["metrics"].items():
                if value != 0:
                    assert metric in decoded["metrics"]
                    assert abs(decoded["metrics"][metric] - value) < 0.01
    
    def test_text_compression(self, tmp_path, sample_field_selections_2025iri):
        """Test text data compression."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = CompactDataEncodingService(2025, "2025iri", str(data_dir))
        
        # Test long comment compression
        long_comment = "This robot has an extremely consistent autonomous routine that scores multiple game pieces. The teleoperated period shows great driver skill with fast cycling times. Endgame climbing is very reliable and they help alliance partners."
        
        compressed = service._compress_single_text(long_comment)
        
        # Should be significantly shorter
        assert len(compressed) < len(long_comment) * 0.5
        assert len(compressed) <= 80
        
        # Should preserve key information
        assert "auto" in compressed
        assert "climb" in compressed or "end" in compressed
    
    def test_custom_metric_handling(self, tmp_path, sample_field_selections_2025iri):
        """Test adding custom metrics dynamically."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = CompactDataEncodingService(2025, "2025iri", str(data_dir))
        
        # Add custom metrics
        code1 = service.add_custom_metric("custom_shooting_accuracy")
        code2 = service.add_custom_metric("special_autonomous_path")
        code3 = service.add_custom_metric("custom_shooting_accuracy")  # Duplicate
        
        # Should generate unique codes
        assert code1 != code2
        assert code1 == code3  # Same metric should get same code
        
        # Codes should be reasonably short
        assert len(code1) <= 4
        assert len(code2) <= 4
    
    def test_token_reduction_calculation(self, tmp_path, sample_field_selections_2025lake, sample_team_data):
        """Test token reduction calculation."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025lake.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025lake, f)
        
        service = CompactDataEncodingService(2025, "2025lake", str(data_dir))
        
        # Create original JSON
        original_json = json.dumps(sample_team_data, indent=2)
        
        # Encode teams
        encoded_teams = []
        for i, team in enumerate(sample_team_data, start=1):
            encoded = service.encode_team_to_array(team, i)
            encoded_teams.append(encoded)
        
        # Create lookup tables
        lookup_tables = service.create_lookup_tables(sample_team_data)
        
        # Calculate reduction
        reduction_stats = service.calculate_token_reduction(original_json, encoded_teams, lookup_tables)
        
        # Should achieve significant reduction
        assert reduction_stats["reduction_percentage"] > 40  # At least 40% reduction
        assert reduction_stats["compact_size"] < reduction_stats["original_size"]
        assert reduction_stats["token_reduction_estimate"] > 40
    
    def test_cross_year_compatibility(self, tmp_path, sample_field_selections_2024champs):
        """Test that service works with different game years."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2024champs.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2024champs, f)
        
        # Should work with 2024 game
        service = CompactDataEncodingService(2024, "2024champs", str(data_dir))
        
        assert service.year == 2024
        assert service.event_code == "champs"
        assert len(service.metric_codes) > 0
        
        # Should have appropriate codes for 2024 game
        found_speaker = False
        found_amp = False
        for code, name in service.metric_codes.items():
            if "speaker" in name.lower():
                found_speaker = True
            if "amp" in name.lower():
                found_amp = True
        
        assert found_speaker
        assert found_amp
    
    def test_missing_field_selections_error(self, tmp_path):
        """Test error handling when field selections file is missing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        with pytest.raises(ValueError, match="Field selections file not found"):
            CompactDataEncodingService(2025, "2025nonexistent", str(data_dir))
    
    def test_empty_team_data_handling(self, tmp_path, sample_field_selections_2025iri):
        """Test handling of teams with missing data."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025iri.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025iri, f)
        
        service = CompactDataEncodingService(2025, "2025iri", str(data_dir))
        
        # Team with minimal data
        minimal_team = {
            "team_number": 9999,
            "nickname": "Test Team",
            "weighted_score": 5.0,
            "metrics": {},
            "text_data": {}
        }
        
        # Should handle gracefully
        encoded = service.encode_team_to_array(minimal_team, 1)
        assert encoded[0] == 1  # index
        assert encoded[1] == 9999  # team number
        assert encoded[2] == "Test Team"
        assert encoded[3] == 5.0
        assert isinstance(encoded[4], list)  # metrics array
    
    def test_performance_with_many_teams(self, tmp_path, sample_field_selections_2025lake):
        """Test performance with 50+ teams."""
        # Setup
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        filepath = data_dir / "field_selections_2025lake.json"
        with open(filepath, "w") as f:
            json.dump(sample_field_selections_2025lake, f)
        
        service = CompactDataEncodingService(2025, "2025lake", str(data_dir))
        
        # Generate 50 teams
        many_teams = []
        for i in range(50):
            team = {
                "team_number": 100 + i,
                "nickname": f"Team {100 + i}",
                "weighted_score": 5.0 + (i % 10) * 0.5,
                "metrics": {
                    "Auto Total Points": 2.0 + (i % 5),
                    "teleop_total_pieces": 8.0 + (i % 7),
                    "endgame_total_points": 5.0 + (i % 4),
                    "driver_skill_rating": 3.0 + (i % 3) * 0.5,
                    "defense_time_seconds": 10.0 + (i % 6) * 2
                },
                "text_data": {
                    "scout_comments": f"Team {100 + i} has consistent performance in all areas."
                }
            }
            many_teams.append(team)
        
        # Time encoding
        import time
        start_time = time.time()
        
        encoded_teams = []
        for i, team in enumerate(many_teams, start=1):
            encoded = service.encode_team_to_array(team, i)
            encoded_teams.append(encoded)
        
        encoding_time = time.time() - start_time
        
        # Should be fast
        assert encoding_time < 1.0  # Less than 1 second for 50 teams
        
        # Check reduction
        original_json = json.dumps(many_teams, indent=2)
        lookup_tables = service.create_lookup_tables(many_teams)
        reduction_stats = service.calculate_token_reduction(original_json, encoded_teams, lookup_tables)
        
        # Should maintain good reduction even with many teams
        assert reduction_stats["reduction_percentage"] > 45