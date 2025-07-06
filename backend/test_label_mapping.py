#!/usr/bin/env python3

import json
import os
from app.services.unified_event_data_service import apply_label_mappings_to_raw_data, load_field_metadata

def test_label_mapping():
    print("Testing label mapping functionality...")
    
    # Load the field metadata
    field_metadata = load_field_metadata(2025)
    print(f"Loaded field metadata: {len(field_metadata)} entries")
    
    # Sample data that matches the field metadata
    sample_headers = [
        "Timestamp",
        "Scout Name", 
        "Team Number",
        "Auto piece count (Trough/L2 half value) [x1]",
        "# of pieces scored on branches (L2-L4) [1x]",
        "# of algae scored (Net & Processor) [1x]"
    ]
    
    sample_row = [
        "2025-01-01 12:00:00",
        "Test Scout",
        "1234",
        "3",  # Auto coral L1 scored
        "2",  # Teleop coral L2 scored  
        "1"   # Teleop algae net scored
    ]
    
    print(f"Sample headers: {sample_headers}")
    print(f"Sample row: {sample_row}")
    
    # Apply label mappings
    enhanced_fields = apply_label_mappings_to_raw_data(sample_row, sample_headers, field_metadata)
    
    print(f"Enhanced fields: {enhanced_fields}")
    
    # Check if we got the expected enhancements
    expected_labels = [
        "auto_coral_L1_scored",
        "teleop_coral_L2_scored", 
        "teleop_algae_net_scored"
    ]
    
    found_labels = []
    for label in expected_labels:
        if label in enhanced_fields:
            found_labels.append(label)
            print(f"✅ Found enhanced field: {label} = {enhanced_fields[label]}")
        else:
            print(f"❌ Missing enhanced field: {label}")
    
    print(f"Found {len(found_labels)}/{len(expected_labels)} expected labels")
    
    if len(found_labels) == len(expected_labels):
        print("🎉 Label mapping test PASSED!")
        return True
    else:
        print("❌ Label mapping test FAILED!")
        return False

if __name__ == "__main__":
    test_label_mapping()