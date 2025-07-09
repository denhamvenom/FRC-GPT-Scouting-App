#!/usr/bin/env python3
"""
Test script to validate synthesis integration is working.
Run this after clicking "Process Selections" to verify synthesis cache files are created.
"""

import os
import json
import glob
from datetime import datetime

def check_sprint1_integration():
    """Check if Sprint 1 context processing is working correctly."""
    
    print("🔍 SPRINT 1 CONTEXT PROCESSING CHECK")
    print("=" * 50)
    
    # Check cache directory
    cache_dir = "/mnt/c/Users/frc80/OneDrive/Documents/FRC-GPT-Scouting-App/backend/app/cache"
    
    if not os.path.exists(cache_dir):
        print("❌ Cache directory not found:", cache_dir)
        return False
    
    print(f"✅ Cache directory exists: {cache_dir}")
    
    # Look for extraction cache files (the new focus)
    extraction_dir = os.path.join(cache_dir, "game_context")
    extraction_files = []
    if os.path.exists(extraction_dir):
        extraction_files = glob.glob(os.path.join(extraction_dir, "*.json"))
    
    print(f"\n📊 Context Extraction files found: {len(extraction_files)}")
    
    if extraction_files:
        print("✅ Context extraction files detected:")
        for file_path in extraction_files[-2:]:  # Show last 2 files
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                filename = os.path.basename(file_path)
                print(f"  📄 {filename}")
                
                if 'extracted_context' in data:
                    extracted = data['extracted_context']
                    print(f"     Game: {extracted.get('game_name', 'Unknown')} ({extracted.get('game_year', 'Unknown')})")
                    print(f"     Version: {extracted.get('extraction_version', 'unknown')}")
                    print(f"     Date: {extracted.get('extraction_date', 'unknown')}")
                    
                    # Show scoring summary
                    if 'scoring_summary' in extracted:
                        scoring = extracted['scoring_summary']
                        phases = [p for p in ['autonomous', 'teleop', 'endgame'] if p in scoring]
                        print(f"     Phases: {', '.join(phases)}")
                        
                        # Show sample point values
                        if 'autonomous' in scoring and 'point_values' in scoring['autonomous']:
                            auto_points = scoring['autonomous']['point_values']
                            sample_points = list(auto_points.items())[:2]
                            print(f"     Sample Points: {dict(sample_points)}")
                
                print()
                
            except Exception as e:
                print(f"  ❌ Error reading {filename}: {e}")
    else:
        print("❌ No extraction cache files found")
        print("   This means extraction hasn't been triggered yet.")
        print("   Try clicking 'Process Selections' in the Manual Setup.")
    
    # Check manual text files
    data_dir = "/mnt/c/Users/frc80/OneDrive/Documents/FRC-GPT-Scouting-App/backend/app/data"
    manual_files = glob.glob(os.path.join(data_dir, "manual_text_*.json"))
    print(f"\n📚 Manual text files found: {len(manual_files)}")
    
    for manual_file in manual_files:
        print(f"  📄 {os.path.basename(manual_file)}")
        
        # Check if manual has individual_sections (our new structure)
        try:
            with open(manual_file, 'r') as f:
                manual_data = json.load(f)
            
            if 'individual_sections' in manual_data:
                section_count = len(manual_data['individual_sections'])
                print(f"     Individual sections: {section_count}")
            
            if 'section_count' in manual_data:
                print(f"     Section count: {manual_data['section_count']}")
                
        except Exception as e:
            print(f"     Error reading manual: {e}")
    
    print("\n" + "=" * 50)
    if extraction_files:
        print("✅ SPRINT 1 CONTEXT PROCESSING: WORKING")
        print("✅ Using structured extraction instead of synthesis")
        print(f"✅ Extraction files: {len(extraction_files)} cached")
        print("✅ Sprint 1 validation: SUCCESS")
    else:
        print("⚠️  SPRINT 1 CONTEXT PROCESSING: NOT YET TRIGGERED")
        print("⚠️  Action needed: Click 'Process Selections' in Manual Setup")
    
    return len(extraction_files) > 0

if __name__ == "__main__":
    check_sprint1_integration()