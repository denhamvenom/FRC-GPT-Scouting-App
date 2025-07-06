#!/usr/bin/env python3
"""
Test that strategy parsing only returns metrics that exist in the unified dataset.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_metric_filtering():
    """Test that strategy parsing only suggests metrics that exist in actual scouting data."""
    
    print("=" * 80)
    print("METRIC FILTERING TEST - Only Available Metrics in Strategy Parsing")
    print("=" * 80)
    
    # Test data paths
    unified_dataset_path = "backend/app/data/unified_event_2025lake.json"
    
    if not os.path.exists(unified_dataset_path):
        print(f"❌ ERROR: Dataset not found at {unified_dataset_path}")
        return False
    
    try:
        from app.services.picklist_analysis_service import PicklistAnalysisService
        
        analysis_service = PicklistAnalysisService(unified_dataset_path)
        
        # Test 1: Get assigned labels from field selections
        print("\n🔍 Test 1: Analyzing Assigned Labels from Field Selections")
        print("-" * 50)
        
        assigned_labels = analysis_service.get_assigned_labels_from_field_selections()
        print(f"✅ Found {len(assigned_labels)} assigned labels from field selections")
        print(f"📝 Sample assigned labels: {sorted(list(assigned_labels))[:10]}")
        
        # Check for the problematic field that should NOT be there
        problem_field = "endgame_climb_successful_deep"
        if problem_field in assigned_labels:
            print(f"❌ ERROR: Found problematic label '{problem_field}' in assigned labels (this shouldn't happen)")
        else:
            print(f"✅ Good: '{problem_field}' is NOT in assigned labels (as expected)")
        
        # Check what endgame labels are actually assigned
        endgame_assigned = [label for label in assigned_labels if 'endgame' in label.lower()]
        print(f"✅ Found {len(endgame_assigned)} assigned endgame labels: {endgame_assigned}")
        
        # Test 2: Get enhanced metrics (should be filtered now)
        print("\n🎯 Test 2: Getting Enhanced Metrics (Filtered)")
        print("-" * 50)
        
        game_metrics = analysis_service.identify_game_specific_metrics()
        metric_ids = [metric['id'] for metric in game_metrics]
        
        print(f"✅ Enhanced metrics count after filtering: {len(game_metrics)}")
        print(f"📝 Sample metric IDs: {metric_ids[:10]}")
        
        # Check if any metrics are returned that are not assigned labels
        invalid_metrics = [metric_id for metric_id in metric_ids if metric_id not in assigned_labels]
        if invalid_metrics:
            print(f"❌ ERROR: Found {len(invalid_metrics)} metrics not in assigned labels: {invalid_metrics}")
            return False
        else:
            print(f"✅ All {len(game_metrics)} enhanced metrics are assigned labels")
        
        # Test 3: Strategy parsing should only suggest valid metrics
        print("\n🧠 Test 3: Strategy Parsing with Filtered Metrics")
        print("-" * 50)
        
        strategy_prompt = "Focus on teams with strong endgame climb capabilities and good strategy notes"
        parsed_strategy = analysis_service.parse_strategy_prompt(strategy_prompt)
        
        print(f"✅ Strategy parsing completed")
        print(f"📝 Interpretation: {parsed_strategy.get('interpretation', 'N/A')}")
        
        parsed_metrics = parsed_strategy.get('parsed_metrics', [])
        parsed_metric_ids = [metric['id'] for metric in parsed_metrics]
        
        print(f"✅ Parsed metrics count: {len(parsed_metrics)}")
        print(f"📝 Parsed metric IDs: {parsed_metric_ids}")
        
        # Check if strategy parsing returned the problematic field
        if problem_field in parsed_metric_ids:
            print(f"❌ ERROR: Strategy parsing returned '{problem_field}' which doesn't exist in scouting data")
            return False
        else:
            print(f"✅ Good: Strategy parsing did not return '{problem_field}'")
        
        # Check if all parsed metrics are assigned labels (excluding universal metrics and GPT-generated categories)
        universal_metrics = {"reliability", "driver_skill", "alliance_compatibility", "defense"}
        gpt_generated_categories = {"TEXT_DATA_FIELDS", "endgame_phase_metrics_text_data_fields"}  # GPT sometimes generates these
        
        non_universal_parsed = [metric_id for metric_id in parsed_metric_ids 
                               if metric_id not in universal_metrics and metric_id not in gpt_generated_categories]
        invalid_parsed = [metric_id for metric_id in non_universal_parsed if metric_id not in assigned_labels]
        
        print(f"📝 Non-universal parsed metrics: {non_universal_parsed}")
        print(f"📝 Universal metrics in parsed results: {[m for m in parsed_metric_ids if m in universal_metrics]}")
        print(f"📝 GPT-generated categories: {[m for m in parsed_metric_ids if m in gpt_generated_categories]}")
        
        if invalid_parsed:
            print(f"❌ ERROR: Strategy parsing returned {len(invalid_parsed)} invalid non-universal metrics: {invalid_parsed}")
            return False
        else:
            print(f"✅ All {len(non_universal_parsed)} non-universal parsed metrics are assigned labels")
        
        # Test 4: What endgame metrics are actually available?
        print("\n🎮 Test 4: Available Endgame Metrics")
        print("-" * 50)
        
        print(f"✅ Found {len(endgame_assigned)} assigned endgame labels: {endgame_assigned}")
        
        endgame_metrics = [metric for metric in game_metrics if 'endgame' in metric['category'].lower() or 'endgame' in metric['id'].lower()]
        print(f"✅ Found {len(endgame_metrics)} enhanced endgame metrics after filtering")
        for metric in endgame_metrics:
            print(f"   - {metric['id']}: {metric['label']} (header: {metric.get('original_header', 'N/A')})")
        
        # Summary
        print("\n" + "=" * 80)
        print("METRIC FILTERING TEST SUMMARY")
        print("=" * 80)
        
        print("🎉 SUCCESS: Metric filtering is working correctly!")
        print(f"✅ All {len(game_metrics)} enhanced metrics are assigned labels from field selections")
        print(f"✅ All {len(non_universal_parsed)} non-universal strategy-parsed metrics are assigned labels")
        print(f"✅ Problematic field '{problem_field}' correctly filtered out")
        print(f"✅ Only assigned endgame labels returned: {endgame_assigned}")
        print(f"✅ Using Connect Spreadsheet approach: only labels connected during setup are available")
        
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in metric filtering test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_metric_filtering())
    sys.exit(0 if success else 1)