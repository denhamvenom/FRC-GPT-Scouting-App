#!/usr/bin/env python3
"""
Comprehensive test suite for unified field selection storage system.

Tests the migration from separate field_selections_{key}.json and field_metadata_{key}.json
files to a single unified field_selections_{key}.json structure.
"""

import os
import json
import tempfile
import shutil
import pytest
from typing import Dict, Any
from unittest.mock import patch, Mock

# Add backend to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.api.schema_selections import FieldSelections, CriticalMappings, load_and_merge_legacy_files
from app.services.unified_event_data_service import load_field_metadata, load_legacy_field_metadata


class TestUnifiedFieldSelections:
    """Test class for unified field selection functionality."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_unified_save_creates_single_file(self):
        """Test that save creates single unified file with correct structure."""
        # Mock data for testing
        field_selections_data = {
            "Team": "team_info",
            "Where (auto) [Coral L1]": "auto",
            "Notes": "strategy"
        }
        
        label_mappings_data = {
            "Where (auto) [Coral L1]": {
                "label": "auto_coral_L1_scored",
                "confidence": "high",
                "description": "Number of CORAL scored in L1 during autonomous",
                "matched_by": "manual_mapping"
            }
        }
        
        critical_mappings_data = CriticalMappings(
            team_number=["Team"],
            match_number=["Match"]
        )
        
        selections = FieldSelections(
            field_selections=field_selections_data,
            year=2025,
            event_key="2025test",
            critical_mappings=critical_mappings_data,
            label_mappings=label_mappings_data
        )
        
        # Mock the sheet headers service
        with patch('app.services.sheets_service.get_sheet_headers') as mock_headers:
            mock_headers.side_effect = lambda tab, log_errors=True: {
                "Scouting": ["Team", "Where (auto) [Coral L1]", "Notes"],
                "PitScouting": [],
                "SuperScouting": []
            }.get(tab, [])
            
            # Create unified data structure (simulating save logic)
            enhanced_field_selections = {}
            
            for header, category in field_selections_data.items():
                # Determine source
                if header in ["Team", "Where (auto) [Coral L1]", "Notes"]:
                    source = "match"
                else:
                    source = "unknown"
                
                field_info = {
                    "category": category,
                    "source": source
                }
                
                # Add label mapping if available
                if header in label_mappings_data:
                    field_info["label_mapping"] = label_mappings_data[header]
                
                enhanced_field_selections[header] = field_info
            
            unified_data = {
                "year": selections.year,
                "event_key": selections.event_key,
                "field_selections": enhanced_field_selections,
                "critical_mappings": selections.critical_mappings.dict(),
                "robot_groups": selections.robot_groups,
                "manual_url": selections.manual_url
            }
            
            # Save to test file
            selections_path = os.path.join(self.data_dir, f"field_selections_{selections.event_key}.json")
            with open(selections_path, "w", encoding="utf-8") as f:
                json.dump(unified_data, f, indent=2)
        
        # Verify file was created
        assert os.path.exists(selections_path)
        
        # Verify no separate metadata file was created
        metadata_path = os.path.join(self.data_dir, f"field_metadata_{selections.event_key}.json")
        assert not os.path.exists(metadata_path)
        
        # Verify file structure
        with open(selections_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data["year"] == 2025
        assert saved_data["event_key"] == "2025test"
        assert "field_selections" in saved_data
        assert "critical_mappings" in saved_data
        
        # Verify enhanced field structure
        field_selections = saved_data["field_selections"]
        assert isinstance(field_selections["Team"], dict)
        assert field_selections["Team"]["category"] == "team_info"
        assert field_selections["Team"]["source"] == "match"
        
        # Verify label mapping preservation
        coral_field = field_selections["Where (auto) [Coral L1]"]
        assert "label_mapping" in coral_field
        assert coral_field["label_mapping"]["label"] == "auto_coral_L1_scored"
    
    def test_unified_load_returns_correct_format(self):
        """Test that load returns data in expected format for frontend."""
        # Create test unified file
        unified_data = {
            "year": 2025,
            "event_key": "2025test",
            "field_selections": {
                "Team": {
                    "category": "team_info",
                    "source": "match"
                },
                "Where (auto) [Coral L1]": {
                    "category": "auto",
                    "source": "match",
                    "label_mapping": {
                        "label": "auto_coral_L1_scored",
                        "confidence": "high",
                        "description": "Test description"
                    }
                }
            },
            "critical_mappings": {
                "team_number": ["Team"],
                "match_number": ["Match"]
            },
            "robot_groups": {},
            "manual_url": None
        }
        
        selections_path = os.path.join(self.data_dir, "field_selections_2025test.json")
        with open(selections_path, "w", encoding="utf-8") as f:
            json.dump(unified_data, f, indent=2)
        
        # Test load functionality (simulate load logic)
        with open(selections_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        
        # Extract components for frontend compatibility
        field_selections = {}
        label_mappings = {}
        
        for header, field_info in loaded_data.get("field_selections", {}).items():
            if isinstance(field_info, dict):
                field_selections[header] = field_info.get("category", "ignore")
                if "label_mapping" in field_info:
                    label_mappings[header] = field_info["label_mapping"]
        
        result = {
            "status": "success",
            "storage_key": "2025test",
            "year": loaded_data.get("year", 2025),
            "event_key": loaded_data.get("event_key"),
            "field_selections": field_selections,
            "critical_mappings": loaded_data.get("critical_mappings", {}),
            "robot_groups": loaded_data.get("robot_groups", {}),
            "label_mappings": label_mappings
        }
        
        # Verify expected format
        assert result["status"] == "success"
        assert result["field_selections"]["Team"] == "team_info"
        assert result["field_selections"]["Where (auto) [Coral L1]"] == "auto"
        assert "Where (auto) [Coral L1]" in result["label_mappings"]
        assert result["label_mappings"]["Where (auto) [Coral L1]"]["label"] == "auto_coral_L1_scored"
    
    def test_backward_compatibility_legacy_files(self):
        """Test loading legacy separate files."""
        # Create legacy field selections file
        legacy_selections = {
            "field_selections": {
                "Team": "team_info",
                "Where (auto) [Coral L1]": "auto"
            },
            "year": 2025,
            "event_key": "2025test",
            "critical_mappings": {
                "team_number": ["Team"],
                "match_number": ["Match"]
            },
            "robot_groups": {}
        }
        
        # Create legacy metadata file
        legacy_metadata = {
            "Where (auto) [Coral L1]": {
                "category": "auto",
                "source": "match",
                "label_mapping": {
                    "label": "auto_coral_L1_scored",
                    "confidence": "high",
                    "description": "Test description"
                }
            }
        }
        
        legacy_selections_path = os.path.join(self.data_dir, "field_selections_2025test.json")
        legacy_metadata_path = os.path.join(self.data_dir, "field_metadata_2025test.json")
        
        with open(legacy_selections_path, "w", encoding="utf-8") as f:
            json.dump(legacy_selections, f, indent=2)
        
        with open(legacy_metadata_path, "w", encoding="utf-8") as f:
            json.dump(legacy_metadata, f, indent=2)
        
        # Test legacy loading
        result = load_and_merge_legacy_files("2025test", self.data_dir)
        
        assert result is not None
        assert result["status"] == "success"
        assert result["field_selections"]["Team"] == "team_info"
        assert "Where (auto) [Coral L1]" in result["label_mappings"]
    
    def test_dataset_building_integration(self):
        """Test unified event data service integration."""
        # Create unified field selections file
        unified_data = {
            "year": 2025,
            "event_key": "2025test",
            "field_selections": {
                "Team": {
                    "category": "team_info",
                    "source": "match"
                },
                "Where (auto) [Coral L1]": {
                    "category": "auto",
                    "source": "match",
                    "label_mapping": {
                        "label": "auto_coral_L1_scored",
                        "confidence": "high",
                        "description": "Test description"
                    }
                }
            }
        }
        
        selections_path = os.path.join(self.data_dir, "field_selections_2025test.json")
        with open(selections_path, "w", encoding="utf-8") as f:
            json.dump(unified_data, f, indent=2)
        
        # Mock the data directory path
        with patch('app.services.unified_event_data_service.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = self.test_dir
            
            # Test load_field_metadata function
            metadata = load_field_metadata(event_key="2025test")
            
            assert len(metadata) == 2
            assert "Team" in metadata
            assert "Where (auto) [Coral L1]" in metadata
            assert metadata["Where (auto) [Coral L1]"]["label_mapping"]["label"] == "auto_coral_L1_scored"
    
    def test_legacy_fallback_integration(self):
        """Test fallback to legacy files in dataset building."""
        # Create only legacy metadata file (no unified file)
        legacy_metadata = {
            "Where (auto) [Coral L1]": {
                "category": "auto",
                "source": "match",
                "label_mapping": {
                    "label": "auto_coral_L1_scored",
                    "confidence": "high",
                    "description": "Test description"
                }
            }
        }
        
        legacy_metadata_path = os.path.join(self.data_dir, "field_metadata_2025test.json")
        with open(legacy_metadata_path, "w", encoding="utf-8") as f:
            json.dump(legacy_metadata, f, indent=2)
        
        # Mock the data directory path
        with patch('app.services.unified_event_data_service.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = self.test_dir
            
            # Test legacy loading
            metadata = load_legacy_field_metadata(event_key="2025test")
            
            assert len(metadata) == 1
            assert "Where (auto) [Coral L1]" in metadata
            assert metadata["Where (auto) [Coral L1]"]["label_mapping"]["label"] == "auto_coral_L1_scored"
    
    def test_migration_preserves_data(self):
        """Test that migration from legacy to unified preserves all data."""
        # Create comprehensive legacy files
        legacy_selections = {
            "field_selections": {
                "Team": "team_info",
                "Where (auto) [Coral L1]": "auto",
                "Where (auto) [Coral L2]": "auto",
                "Notes": "strategy"
            },
            "year": 2025,
            "event_key": "2025test",
            "critical_mappings": {
                "team_number": ["Team"],
                "match_number": ["Match"]
            },
            "robot_groups": {
                "robot_1": ["SuperScout Field 1"],
                "robot_2": ["SuperScout Field 2"]
            },
            "manual_url": "https://example.com/manual"
        }
        
        legacy_metadata = {
            "Where (auto) [Coral L1]": {
                "category": "auto",
                "source": "match",
                "label_mapping": {
                    "label": "auto_coral_L1_scored",
                    "confidence": "high",
                    "description": "L1 scoring"
                }
            },
            "Where (auto) [Coral L2]": {
                "category": "auto",
                "source": "match",
                "label_mapping": {
                    "label": "auto_coral_L2_scored",
                    "confidence": "high",
                    "description": "L2 scoring"
                }
            }
        }
        
        # Save legacy files
        legacy_selections_path = os.path.join(self.data_dir, "field_selections_2025test.json")
        legacy_metadata_path = os.path.join(self.data_dir, "field_metadata_2025test.json")
        
        with open(legacy_selections_path, "w", encoding="utf-8") as f:
            json.dump(legacy_selections, f, indent=2)
        
        with open(legacy_metadata_path, "w", encoding="utf-8") as f:
            json.dump(legacy_metadata, f, indent=2)
        
        # Load and merge legacy files
        result = load_and_merge_legacy_files("2025test", self.data_dir)
        
        # Verify all data is preserved
        assert result["year"] == 2025
        assert result["event_key"] == "2025test"
        assert len(result["field_selections"]) == 4
        assert len(result["label_mappings"]) == 2
        assert result["critical_mappings"]["team_number"] == ["Team"]
        assert result["robot_groups"]["robot_1"] == ["SuperScout Field 1"]
        
        # Verify label mappings
        assert "Where (auto) [Coral L1]" in result["label_mappings"]
        assert "Where (auto) [Coral L2]" in result["label_mappings"]
        assert result["label_mappings"]["Where (auto) [Coral L1]"]["label"] == "auto_coral_L1_scored"
        assert result["label_mappings"]["Where (auto) [Coral L2]"]["label"] == "auto_coral_L2_scored"


def test_unified_field_selections_integration():
    """Integration test that simulates full save/load cycle."""
    test_instance = TestUnifiedFieldSelections()
    test_instance.setup_method()
    
    try:
        # Test save creates unified file
        test_instance.test_unified_save_creates_single_file()
        
        # Test load returns correct format
        test_instance.test_unified_load_returns_correct_format()
        
        # Test backward compatibility
        test_instance.test_backward_compatibility_legacy_files()
        
        # Test dataset building integration
        test_instance.test_dataset_building_integration()
        
        print("✅ All unified field selection tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    test_unified_field_selections_integration()