#!/usr/bin/env python3
"""
Update baseline metadata based on actual screenshots in the directory
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime

def compute_image_hash(image_path: Path) -> str:
    """Compute hash of image file"""
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def update_metadata():
    """Update metadata.json with current screenshots"""
    baseline_dir = Path(__file__).parent / "visual_baselines"
    
    # Get all PNG files
    screenshots = list(baseline_dir.glob("*.png"))
    
    if not screenshots:
        print("No PNG screenshots found in visual_baselines directory")
        return
    
    metadata = {
        "capture_time": datetime.now().isoformat(),
        "description": "Manual screenshot capture covering all critical workflows and states",
        "total_screenshots": len(screenshots),
        "screenshots": {}
    }
    
    print(f"Processing {len(screenshots)} screenshots...")
    
    for screenshot in screenshots:
        try:
            stat = screenshot.stat()
            hash_value = compute_image_hash(screenshot)
            
            metadata["screenshots"][screenshot.name] = {
                "size": stat.st_size,
                "hash": hash_value,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "captured_manually": True
            }
            
            print(f"  ✓ {screenshot.name}: {stat.st_size} bytes, hash: {hash_value[:8]}...")
            
        except Exception as e:
            print(f"  ✗ Error processing {screenshot.name}: {e}")
    
    # Save updated metadata
    metadata_path = baseline_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nMetadata updated: {metadata_path}")
    print(f"Total screenshots cataloged: {len(metadata['screenshots'])}")
    
    # Show what we have
    print("\nScreenshot inventory:")
    for name, info in metadata["screenshots"].items():
        print(f"  - {name}: {info['size']} bytes")

if __name__ == "__main__":
    update_metadata()