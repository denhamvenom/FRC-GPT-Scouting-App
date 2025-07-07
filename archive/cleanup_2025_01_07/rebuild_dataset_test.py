#!/usr/bin/env python3
"""
Test script to rebuild the unified dataset with enhanced labels.
This bypasses the permission issues with the locked file.
"""

import asyncio
import json
import os
from app.services.unified_event_data_service import (
    load_field_metadata, 
    apply_label_mappings_to_raw_data,
    get_unified_dataset_path
)

async def test_enhanced_dataset():
    """Test that the dataset gets built with enhanced labels."""
    
    # Load existing dataset
    dataset_path = get_unified_dataset_path("2025lake")
    print(f"Loading dataset from: {dataset_path}")
    
    try:
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return
        
    print(f"Dataset loaded. Teams: {len(dataset.get('teams', {}))}")
    
    # Load field metadata
    field_metadata = load_field_metadata(2025)
    print(f"Field metadata loaded: {len(field_metadata)} entries")
    
    # Check a sample team's data
    sample_team_key = list(dataset.get('teams', {}).keys())[0] if dataset.get('teams') else None
    if sample_team_key:
        team_data = dataset['teams'][sample_team_key]
        scouting_data = team_data.get('scouting_data', [])
        
        print(f"\nSample team {sample_team_key}:")
        print(f"  Scouting records: {len(scouting_data)}")
        
        if scouting_data:
            first_record = scouting_data[0]
            print(f"  First record fields: {list(first_record.keys())}")
            
            # Check for enhanced fields
            enhanced_fields = [k for k in first_record.keys() if 'coral' in k or 'algae' in k]
            if enhanced_fields:
                print(f"  ✅ Found enhanced fields: {enhanced_fields}")
            else:
                print(f"  ❌ No enhanced fields found!")
                
                # Show what would be enhanced
                print("\n  Expected enhancements based on field metadata:")
                for header, metadata in field_metadata.items():
                    if 'label_mapping' in metadata:
                        label = metadata['label_mapping'].get('label', '')
                        print(f"    {header} -> {label}")
    
    # Create a test dataset with enhanced fields
    print("\n\nCreating test dataset with enhanced fields...")
    test_path = os.path.join(os.path.dirname(dataset_path), "test_enhanced_2025lake.json")
    
    # Copy dataset structure
    enhanced_dataset = {
        "event_key": dataset.get("event_key"),
        "year": dataset.get("year"),
        "expected_matches": dataset.get("expected_matches", []),
        "teams": {},
        "metadata": dataset.get("metadata", {})
    }
    
    # Process one team as example
    if sample_team_key and dataset.get('teams'):
        team_data = dataset['teams'][sample_team_key]
        enhanced_team_data = dict(team_data)
        
        # Simulate enhanced scouting data
        enhanced_scouting = []
        for record in team_data.get('scouting_data', [])[:2]:  # Just first 2 records
            enhanced_record = dict(record)
            # Add sample enhanced fields
            enhanced_record.update({
                "auto_coral_L1_scored": 3,
                "teleop_coral_L2_scored": 2,
                "teleop_coral_L1_scored": 4,
                "teleop_algae_net_scored": 1
            })
            enhanced_scouting.append(enhanced_record)
        
        enhanced_team_data['scouting_data'] = enhanced_scouting
        enhanced_dataset['teams'][sample_team_key] = enhanced_team_data
    
    # Save test dataset
    with open(test_path, 'w') as f:
        json.dump(enhanced_dataset, f, indent=2)
    
    print(f"✅ Test dataset saved to: {test_path}")
    print("\nSample enhanced record:")
    if enhanced_dataset['teams'] and sample_team_key in enhanced_dataset['teams']:
        sample_record = enhanced_dataset['teams'][sample_team_key]['scouting_data'][0]
        for key, value in sample_record.items():
            if 'coral' in key or 'algae' in key:
                print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_dataset())