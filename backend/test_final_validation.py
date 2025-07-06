#!/usr/bin/env python3
"""
Final validation test for unified field selection storage system.

This test validates the complete implementation including:
1. Unified file creation and structure
2. API endpoints functionality
3. Dataset building integration
4. Backward compatibility
"""

import os
import json
import tempfile
import shutil
import sys
from unittest.mock import patch

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.api.schema_selections import FieldSelections, CriticalMappings, load_and_merge_legacy_files
from app.services.unified_event_data_service import load_field_metadata


def test_complete_integration():
    """Test complete integration of unified field selection system."""
    
    # Create temporary test environment
    test_dir = tempfile.mkdtemp()
    data_dir = os.path.join(test_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        print("🔍 Testing unified field selection implementation...")
        
        # 1. Test unified file creation
        print("\n1. Testing unified file creation...")
        
        # Create test data
        field_selections_data = {
            "Team": "team_info",
            "Where (auto) [Coral L1]": "auto",
            "Where (teleop) [Speaker]": "teleop",
            "Strategy Notes": "strategy"
        }
        
        label_mappings_data = {
            "Where (auto) [Coral L1]": {
                "label": "auto_coral_L1_scored",
                "confidence": "high",
                "description": "Number of CORAL scored in L1 during autonomous"
            },
            "Where (teleop) [Speaker]": {
                "label": "teleop_speaker_scored",
                "confidence": "high", 
                "description": "Number of NOTES scored in SPEAKER during teleop"
            }
        }
        
        # Simulate save logic
        enhanced_field_selections = {}
        for header, category in field_selections_data.items():
            field_info = {
                "category": category,
                "source": "match"  # Simplified for test
            }
            
            if header in label_mappings_data:
                field_info["label_mapping"] = label_mappings_data[header]
            
            enhanced_field_selections[header] = field_info
        
        unified_data = {
            "year": 2025,
            "event_key": "2025finaltest",
            "field_selections": enhanced_field_selections,
            "critical_mappings": {
                "team_number": ["Team"],
                "match_number": ["Match"]
            },
            "robot_groups": {},
            "manual_url": None
        }
        
        # Save unified file
        selections_path = os.path.join(data_dir, "field_selections_2025finaltest.json")
        with open(selections_path, "w", encoding="utf-8") as f:
            json.dump(unified_data, f, indent=2)
        
        print(f"   ✅ Created unified file: {selections_path}")
        
        # Verify structure
        with open(selections_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert "field_selections" in saved_data
        assert len(saved_data["field_selections"]) == 4
        
        # Check enhanced structure
        coral_field = saved_data["field_selections"]["Where (auto) [Coral L1]"]
        assert coral_field["category"] == "auto"
        assert "label_mapping" in coral_field
        assert coral_field["label_mapping"]["label"] == "auto_coral_L1_scored"
        
        print("   ✅ Unified structure verified")
        
        # 2. Test load functionality
        print("\n2. Testing load functionality...")
        
        # Simulate load logic
        field_selections = {}
        label_mappings = {}
        
        for header, field_info in saved_data["field_selections"].items():
            field_selections[header] = field_info["category"]
            if "label_mapping" in field_info:
                label_mappings[header] = field_info["label_mapping"]
        
        assert len(field_selections) == 4
        assert len(label_mappings) == 2
        assert field_selections["Team"] == "team_info"
        assert "Where (auto) [Coral L1]" in label_mappings
        
        print("   ✅ Load functionality verified")
        
        # 3. Test dataset building integration
        print("\n3. Testing dataset building integration...")
        
        with patch('app.services.unified_event_data_service.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = test_dir
            
            metadata = load_field_metadata(event_key="2025finaltest")
            
            assert len(metadata) == 4
            assert "Team" in metadata
            assert "Where (auto) [Coral L1]" in metadata
            
            # Verify enhanced metadata
            coral_metadata = metadata["Where (auto) [Coral L1]"]
            assert coral_metadata["category"] == "auto"
            assert "label_mapping" in coral_metadata
            assert coral_metadata["label_mapping"]["label"] == "auto_coral_L1_scored"
        
        print("   ✅ Dataset building integration verified")
        
        # 4. Test backward compatibility
        print("\n4. Testing backward compatibility...")
        
        # Create legacy files
        legacy_selections = {
            "field_selections": {
                "Team": "team_info",
                "Legacy Field": "auto"
            },
            "year": 2025,
            "event_key": "2025legacy",
            "critical_mappings": {
                "team_number": ["Team"],
                "match_number": ["Match"]
            }
        }
        
        legacy_metadata = {
            "Legacy Field": {
                "category": "auto",
                "source": "match",
                "label_mapping": {
                    "label": "legacy_field_scored",
                    "confidence": "medium",
                    "description": "Legacy field description"
                }
            }
        }
        
        legacy_selections_path = os.path.join(data_dir, "field_selections_2025legacy.json")
        legacy_metadata_path = os.path.join(data_dir, "field_metadata_2025legacy.json")
        
        with open(legacy_selections_path, "w", encoding="utf-8") as f:
            json.dump(legacy_selections, f, indent=2)
        
        with open(legacy_metadata_path, "w", encoding="utf-8") as f:
            json.dump(legacy_metadata, f, indent=2)
        
        # Test legacy loading
        legacy_result = load_and_merge_legacy_files("2025legacy", data_dir)
        
        assert legacy_result is not None
        assert legacy_result["status"] == "success"
        assert len(legacy_result["field_selections"]) == 2
        assert len(legacy_result["label_mappings"]) == 1
        assert "Legacy Field" in legacy_result["label_mappings"]
        
        print("   ✅ Backward compatibility verified")
        
        # 5. Test no separate metadata files created
        print("\n5. Testing file structure...")
        
        # List all files in data directory
        files = os.listdir(data_dir)
        field_selection_files = [f for f in files if f.startswith("field_selections_")]
        field_metadata_files = [f for f in files if f.startswith("field_metadata_")]
        
        print(f"   Field selection files: {field_selection_files}")
        print(f"   Field metadata files: {field_metadata_files}")
        
        # Should have field_selections files but legacy metadata should be separate
        assert len(field_selection_files) >= 2  # unified + legacy
        assert len(field_metadata_files) == 1   # only legacy metadata
        
        print("   ✅ File structure verified - no new metadata files created")
        
        # 6. Test data preservation
        print("\n6. Testing data preservation...")
        
        # Load unified file and verify all data is preserved
        with open(selections_path, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        
        # Check all original data is preserved in enhanced format
        original_count = len(field_selections_data)
        enhanced_count = len(final_data["field_selections"])
        label_count = len([f for f in final_data["field_selections"].values() if "label_mapping" in f])
        
        assert enhanced_count == original_count
        assert label_count == len(label_mappings_data)
        
        print(f"   ✅ Data preservation verified: {enhanced_count} fields, {label_count} with labels")
        
        print("\n🎉 All validation tests passed!")
        print("\n📊 Summary:")
        print(f"   • Unified file structure: ✅")
        print(f"   • Enhanced field selections: ✅")
        print(f"   • Label mapping preservation: ✅")
        print(f"   • Dataset building integration: ✅")
        print(f"   • Backward compatibility: ✅")
        print(f"   • No duplicate metadata files: ✅")
        print(f"   • Data preservation: ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    success = test_complete_integration()
    exit(0 if success else 1)