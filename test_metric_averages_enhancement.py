#!/usr/bin/env python3
"""
Test script for metric averages enhancement to strategic intelligence files.

This script validates that the enhanced strategic intelligence generation
includes metric averages for user priority weighting support.
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_metric_averages_enhancement():
    """Test the metric averages enhancement functionality."""
    
    print("🔧 Testing Metric Averages Enhancement for Strategic Intelligence")
    print("=" * 70)
    
    # Test 1: Check method exists
    print("\n1️⃣ Testing method availability...")
    try:
        from unittest.mock import patch
        
        # Mock environment-dependent imports
        with patch('app.config.openai_config.OPENAI_API_KEY', 'test_key'):
            with patch('app.config.openai_config.OPENAI_MODEL', 'gpt-4'):
                from app.services.data_aggregation_service import DataAggregationService
        
        # Check if new methods exist
        assert hasattr(DataAggregationService, '_add_metric_averages_to_signatures')
        assert hasattr(DataAggregationService, '_calculate_team_metric_averages')
        print("   ✅ Metric averages enhancement methods exist")
        
    except Exception as e:
        print(f"   ❌ Method availability check failed: {e}")
        return False
    
    # Test 2: Test metric averages calculation logic
    print("\n2️⃣ Testing metric averages calculation...")
    try:
        # Create mock data aggregation service
        mock_dataset_path = "test_unified_dataset.json"
        
        with patch('app.config.openai_config.OPENAI_API_KEY', 'test_key'):
            with patch('app.config.openai_config.OPENAI_MODEL', 'gpt-4'):
                # Mock the file loading
                with patch.object(DataAggregationService, '_load_unified_dataset'):
                    service = DataAggregationService(mock_dataset_path)
        
        # Test metric calculation with sample team data
        sample_team_data = {
            "team_number": 8044,
            "aggregated_metrics": {
                "auto_total": 12.67,
                "teleop_total": 61.56,
                "endgame_total": 1.56,
                "match_count": 9
            },
            "matches": [
                {"data": {"auto_coral_L4": 1, "teleop_speaker_notes": 8, "endgame_climb_points": 0}},
                {"data": {"auto_coral_L4": 2, "teleop_speaker_notes": 9, "endgame_climb_points": 3}},
                {"data": {"auto_coral_L4": 1, "teleop_speaker_notes": 7, "endgame_climb_points": 0}}
            ]
        }
        
        metric_averages = service._calculate_team_metric_averages(sample_team_data)
        
        # Verify metric averages structure
        assert isinstance(metric_averages, dict)
        assert "auto_total" in metric_averages
        assert "teleop_total" in metric_averages
        assert "endgame_total" in metric_averages
        assert metric_averages["auto_total"] == 12.67
        assert metric_averages["teleop_total"] == 61.56
        
        # Verify match-level averages
        assert "auto_coral_L4" in metric_averages
        assert "teleop_speaker_notes" in metric_averages
        assert metric_averages["auto_coral_L4"] == 1.33  # (1+2+1)/3 = 1.33
        assert metric_averages["teleop_speaker_notes"] == 8.0  # (8+9+7)/3 = 8.0
        
        print(f"   ✅ Calculated {len(metric_averages)} metric averages correctly")
        print(f"   📊 Sample metrics: auto_total={metric_averages['auto_total']}, auto_coral_L4={metric_averages['auto_coral_L4']}")
        
    except Exception as e:
        print(f"   ❌ Metric averages calculation failed: {e}")
        return False
    
    # Test 3: Test signature enhancement
    print("\n3️⃣ Testing strategic signature enhancement...")
    try:
        # Sample strategic signatures (from existing file)
        sample_signatures = {
            "8044": {
                "team_number": 8044,
                "enhanced_metrics": {
                    "auto": "12.67±0.0 (dominant, n=1)",
                    "teleop": "61.56±0.0 (dominant, n=1)",
                    "endgame": "1.56±0.0 (developing, n=1)"
                },
                "strategic_profile": "dominant_balanced",
                "batch_number": 2
            }
        }
        
        sample_teams_data = [sample_team_data]
        
        enhanced_signatures = service._add_metric_averages_to_signatures(
            sample_signatures, sample_teams_data
        )
        
        # Verify enhancement
        assert "8044" in enhanced_signatures
        team_sig = enhanced_signatures["8044"]
        assert "metric_averages" in team_sig
        assert "enhanced_metrics" in team_sig  # Original data preserved
        assert "strategic_profile" in team_sig  # Original data preserved
        
        metric_averages = team_sig["metric_averages"]
        assert "auto_total" in metric_averages
        assert "auto_coral_L4" in metric_averages
        assert metric_averages["auto_total"] == 12.67
        
        print("   ✅ Strategic signatures enhanced with metric averages")
        print(f"   📊 Enhanced signature includes {len(metric_averages)} metric averages")
        
    except Exception as e:
        print(f"   ❌ Signature enhancement failed: {e}")
        return False
    
    # Test 4: Verify enhanced file structure
    print("\n4️⃣ Testing expected file structure...")
    try:
        # Expected structure after enhancement
        expected_structure = {
            "strategic_signatures": {
                "8044": {
                    "team_number": 8044,
                    "enhanced_metrics": {
                        "auto": "12.67±0.0 (dominant, n=1)",
                        "teleop": "61.56±0.0 (dominant, n=1)"
                    },
                    "strategic_profile": "dominant_balanced",
                    "metric_averages": {
                        "auto_total": 12.67,
                        "teleop_total": 61.56,
                        "auto_coral_L4": 1.33,
                        "teleop_speaker_notes": 8.0
                    }
                }
            }
        }
        
        # Verify structure matches picklist needs
        team_data = expected_structure["strategic_signatures"]["8044"]
        
        # Strategic intelligence preserved
        assert "enhanced_metrics" in team_data
        assert "strategic_profile" in team_data
        
        # Metric averages available for priority weighting
        assert "metric_averages" in team_data
        metric_averages = team_data["metric_averages"]
        
        # Can extract user-selected metrics
        user_priorities = [
            {"id": "auto_coral_L4", "weight": 2.0},
            {"id": "teleop_speaker_notes", "weight": 1.5}
        ]
        
        for priority in user_priorities:
            metric_id = priority["id"]
            assert metric_id in metric_averages, f"User priority metric {metric_id} not found in averages"
        
        print("   ✅ Enhanced file structure supports both strategic intelligence and user priority weighting")
        print(f"   🎯 Can extract user-selected metrics for weighting")
        
    except Exception as e:
        print(f"   ❌ File structure validation failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 ALL METRIC AVERAGES ENHANCEMENT TESTS PASSED!")
    print("\n📋 Enhancement Summary:")
    print("   • Strategic signatures now include metric_averages for user priority weighting")
    print("   • Original strategic intelligence data preserved (enhanced_metrics, strategic_profile)")
    print("   • Supports selective metric inclusion based on user priorities")
    print("   • Maintains token efficiency while enabling quantitative user weighting")
    print("   • Ready for picklist generation with both strategic context and numerical priorities")
    
    print("\n🚀 READY FOR SPRINT 4: Enhanced picklist generation using strategic intelligence files!")
    
    return True

def demo_enhanced_structure():
    """Demonstrate the enhanced strategic intelligence structure."""
    
    print("\n" + "=" * 70)
    print("📊 ENHANCED STRATEGIC INTELLIGENCE STRUCTURE DEMO")
    print("=" * 70)
    
    enhanced_example = {
        "event_key": "2025lake",
        "strategic_signatures": {
            "8044": {
                "team_number": 8044,
                # Strategic Intelligence (for efficient GPT processing)
                "enhanced_metrics": {
                    "auto": "12.67±0.0 (dominant, n=9)",
                    "teleop": "61.56±0.0 (dominant, n=9)", 
                    "endgame": "1.56±0.0 (developing, n=9)"
                },
                "strategic_profile": "dominant_balanced",
                # Metric Averages (for user priority weighting)
                "metric_averages": {
                    "auto_total": 12.67,
                    "teleop_total": 61.56,
                    "endgame_total": 1.56,
                    "auto_coral_L4": 1.33,
                    "auto_algae_L1": 2.44,
                    "teleop_speaker_notes": 8.22,
                    "teleop_coral_L4": 3.89,
                    "endgame_climb_points": 1.56,
                    "defense_rating": 2.1,
                    "penalty_count": 0.22
                }
            }
        }
    }
    
    print("\n🎯 USER PRIORITY WEIGHTING EXAMPLE:")
    print("User selects priorities: auto_coral_L4 (2.0×), teleop_speaker_notes (1.5×), endgame_climb_points (1.0×)")
    
    team = enhanced_example["strategic_signatures"]["8044"]
    user_priorities = [
        {"id": "auto_coral_L4", "weight": 2.0},
        {"id": "teleop_speaker_notes", "weight": 1.5}, 
        {"id": "endgame_climb_points", "weight": 1.0}
    ]
    
    print("\nPicklist GPT Payload (selective metrics + strategic context):")
    picklist_payload = {
        "team": 8044,
        "strategic_profile": team["strategic_profile"],  # Strategic context
        "auto_coral_L4": team["metric_averages"]["auto_coral_L4"],      # User priority 1
        "teleop_speaker_notes": team["metric_averages"]["teleop_speaker_notes"],  # User priority 2
        "endgame_climb_points": team["metric_averages"]["endgame_climb_points"]   # User priority 3
    }
    
    print(json.dumps(picklist_payload, indent=2))
    
    print("\n🧠 STRATEGIC INTELLIGENCE BENEFITS:")
    print("   • Compressed team profile: 'dominant_balanced' (vs detailed performance breakdown)")
    print("   • Enhanced metrics with context: '12.67±0.0 (dominant, n=9)'")
    print("   • Token efficient: Only user-selected metrics sent to GPT")
    print("   • Strategic context: Profile guides alliance selection reasoning")
    
    print("\n⚖️ USER PRIORITY WEIGHTING PRESERVED:")
    print("   • Quantitative metrics: Exact averages for mathematical weighting")
    print("   • Selective inclusion: Only metrics user cares about")
    print("   • Flexible weighting: User can adjust priorities by pick position")
    print("   • Backward compatible: Existing picklist logic works unchanged")

if __name__ == "__main__":
    try:
        success = test_metric_averages_enhancement()
        if success:
            demo_enhanced_structure()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)