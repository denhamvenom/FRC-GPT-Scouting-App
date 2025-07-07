#!/usr/bin/env python3
"""
Test script to verify label enhancement works with existing data.
"""
import json
import sys
import os

# Add app to path
sys.path.append('app')
from services.unified_event_data_service import apply_label_mappings_to_raw_data, load_field_metadata

def test_enhancement():
    print("Testing label enhancement...")
    
    # Load field metadata
    field_metadata = load_field_metadata(2025)
    print(f"Loaded field metadata with {len(field_metadata)} entries")
    
    # Load dataset
    with open('app/data/unified_event_2025lake.json', 'r') as f:
        data = json.load(f)
    
    headers = data.get('metadata', {}).get('scouting_headers', [])
    print(f"Headers: {headers[:10]}")
    
    # Test with a sample row of data
    sample_row = ['2025-01-01', 'TestScout', '1', '1234', 'blue', 'path1', 'yes', '5', '2', '1', '0', '3', '1', '0', '8', '4', '2', '1', '5', '2', '1']
    
    # Apply enhancement
    enhanced = apply_label_mappings_to_raw_data(sample_row, headers, field_metadata)
    print(f"\nEnhanced fields: {enhanced}")
    
    # Now let's manually enhance one team's data to test
    team_num = next(iter(data['teams'].keys()))
    team_data = data['teams'][team_num]
    
    if team_data.get('scouting_data'):
        print(f"\nOriginal team {team_num} first match: {team_data['scouting_data'][0]}")
        
        # We would need the original raw row data to enhance it properly
        # For now, let's just add some sample enhanced fields manually
        enhanced_match = team_data['scouting_data'][0].copy()
        enhanced_match.update({
            'auto_coral_L1_scored': 2,
            'auto_coral_L2_scored': 1, 
            'teleop_coral_L1_scored': 4,
            'teleop_coral_L2_scored': 2,
            'auto_total_score': enhanced_match.get('auto', 0),
            'teleop_total_score': enhanced_match.get('teleop', 0)
        })
        print(f"Enhanced match data: {enhanced_match}")

if __name__ == "__main__":
    test_enhancement()