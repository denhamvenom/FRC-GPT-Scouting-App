#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.unified_event_data_service import build_unified_dataset

async def test_rebuild():
    """Test rebuilding the unified dataset with force_rebuild=True"""
    print("🔄 Testing unified dataset rebuild with force_rebuild=True...")
    
    try:
        result_path = await build_unified_dataset(
            event_key="2025iri",
            year=2025,
            force_rebuild=True,  # Force rebuild to see debug messages
            operation_id="test_rebuild_001"
        )
        print(f"✅ Rebuild completed successfully: {result_path}")
    except Exception as e:
        print(f"❌ Rebuild failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rebuild())