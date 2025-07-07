#!/usr/bin/env python3
"""
Test the new comparative reasoning in GPT rankings.
This will generate a picklist and show the improved explanations.
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

async def test_comparative_reasoning():
    """Test the new comparative reasoning approach with a small subset of teams."""
    
    print("=" * 80)
    print("COMPARATIVE REASONING TEST")
    print("=" * 80)
    
    # Test data paths
    unified_dataset_path = "backend/app/data/unified_event_2025lake.json"
    
    if not os.path.exists(unified_dataset_path):
        print(f"❌ ERROR: Dataset not found at {unified_dataset_path}")
        return False
    
    try:
        from app.services.data_aggregation_service import DataAggregationService
        from app.services.picklist_generator_service import PicklistGeneratorService
        
        # Initialize services
        data_service = DataAggregationService(unified_dataset_path)
        generator_service = PicklistGeneratorService(unified_dataset_path)
        
        # Test with a smaller set for clearer comparative examples
        test_priorities = [
            {"id": "teleop_coral_L4_scored", "weight": 3.0, "reason": "Primary teleop scoring"},
            {"id": "auto_coral_L1_scored", "weight": 2.0, "reason": "Auto reliability"},
            {"id": "endgame_total_points", "weight": 1.5, "reason": "Endgame contribution"}
        ]
        
        print("\\n🎯 Generating picklist with COMPARATIVE REASONING...")
        print("-" * 50)
        
        # Generate picklist with new comparative reasoning
        result = await generator_service.generate_picklist(
            your_team_number=8044,
            pick_position="first",
            priorities=test_priorities,
            batch_size=15,  # Smaller set for clearer examples
            use_batching=False
        )
        
        if result.get("status") == "success":
            teams = result.get("teams", [])
            
            print(f"✅ Generated picklist with {len(teams)} teams")
            print("\\n📊 TOP 10 TEAMS WITH COMPARATIVE REASONING:")
            print("-" * 50)
            
            for i, team in enumerate(teams[:10], 1):
                team_number = team.get("team_number", "Unknown")
                score = team.get("score", 0)
                reasoning = team.get("reasoning", "No reasoning provided")
                
                print(f"{i:2d}. Team {team_number:<4} (Score: {score:.1f})")
                print(f"    Reasoning: {reasoning}")
                print()
            
            print("\\n🔍 ANALYSIS OF REASONING QUALITY:")
            print("-" * 50)
            
            # Analyze if reasoning is comparative
            comparative_count = 0
            total_explanations = len(teams[:10])
            
            comparative_keywords = ["than", "vs", "better", "weaker", "above", "below", "outranks", "edges out", "falls short"]
            
            for team in teams[:10]:
                reasoning = team.get("reasoning", "").lower()
                if any(keyword in reasoning for keyword in comparative_keywords):
                    comparative_count += 1
            
            comparative_percentage = (comparative_count / total_explanations) * 100
            
            print(f"✅ Comparative explanations: {comparative_count}/{total_explanations} ({comparative_percentage:.1f}%)")
            
            if comparative_percentage >= 70:
                print("🎉 SUCCESS: Most explanations use comparative reasoning!")
            elif comparative_percentage >= 40:
                print("⚠️  PARTIAL: Some explanations use comparative reasoning")
            else:
                print("❌ NEEDS WORK: Few explanations use comparative reasoning")
            
            # Show example improvements
            print("\\n💡 EXAMPLE REASONING IMPROVEMENTS:")
            print("-" * 50)
            
            for i, team in enumerate(teams[:3], 1):
                old_style = f"Strong teleop_coral_L4_scored: High"
                new_style = team.get("reasoning", "")
                
                print(f"Team #{i}:")
                print(f"  Old style: '{old_style}'")
                print(f"  New style: '{new_style}'")
                print()
            
            return True
            
        else:
            print(f"❌ ERROR: Picklist generation failed: {result.get('message', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in comparative reasoning test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_comparative_reasoning())
    if success:
        print("\\n" + "=" * 80)
        print("✅ COMPARATIVE REASONING TEST COMPLETED")
        print("The GPT prompts have been updated to provide better contextual explanations!")
        print("=" * 80)
    sys.exit(0 if success else 1)