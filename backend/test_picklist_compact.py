#!/usr/bin/env python3
"""
Test script for the ultra-compact JSON picklist generation.
"""

import os
import sys
import asyncio
import json
from app.services.picklist_generator_service import PicklistGeneratorService

# Configuration - update these paths as needed
TEST_DATASET_PATH = os.path.abspath("app/data/unified_dataset.json")

async def test_picklist_generator():
    """Test the picklist generator with the ultra-compact format."""
    
    # Check if dataset exists
    if not os.path.exists(TEST_DATASET_PATH):
        print(f"Error: Test dataset not found at {TEST_DATASET_PATH}")
        print("Please create a test dataset or update the path in this script")
        sys.exit(1)
    
    # Initialize the service
    service = PicklistGeneratorService(TEST_DATASET_PATH)
    
    # Sample test data
    your_team_number = 254  # Example team
    pick_position = "first"
    priorities = [
        {"id": "statbotics_epa_end", "weight": 2.0},
        {"id": "statbotics_epa_teleop", "weight": 1.5},
        {"id": "statbotics_epa_auto", "weight": 1.2}
    ]
    
    # Generate a picklist with just a few teams for quick testing
    test_teams = service._prepare_team_data_for_gpt()[:5]  # Just first 5 teams
    
    # Debug info
    print(f"Testing with {len(test_teams)} teams")
    print(f"Team numbers: {[t['team_number'] for t in test_teams]}")
    
    # Override the teams_data attribute with our sample
    original_teams_data = service.teams_data
    try:
        # Create a mock teams_data with just a few teams
        mock_teams_data = {}
        for team in test_teams:
            mock_teams_data[str(team["team_number"])] = {
                "nickname": team.get("nickname", f"Team {team['team_number']}"),
                "metrics": team.get("metrics", {})
            }
        
        service.teams_data = mock_teams_data
        
        # Call the generator
        result = await service.generate_picklist(
            your_team_number=your_team_number,
            pick_position=pick_position,
            priorities=priorities
        )
        
        # Print result
        print("\n--- Picklist Result ---")
        print(json.dumps(result, indent=2))
        
        # Check for success
        if result.get("status") == "success":
            print("\n✅ Picklist generation successful")
            print(f"Generated rankings for {len(result.get('picklist', []))} teams")
        else:
            print("\n❌ Picklist generation failed")
            print(f"Error: {result.get('message', 'Unknown error')}")
        
    finally:
        # Restore original data
        service.teams_data = original_teams_data

if __name__ == "__main__":
    asyncio.run(test_picklist_generator())