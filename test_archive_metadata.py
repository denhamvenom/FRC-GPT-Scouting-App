#!/usr/bin/env python3
"""
Test script to verify that the enhanced archive metadata is being created correctly.
"""

import sys
import os
import json
import asyncio
import logging

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database.db import SessionLocal
from app.services.archive_service import get_archived_events, archive_current_event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_archive_metadata():
    """Test that archives have the correct metadata structure."""
    print("=" * 80)
    print("Testing Archive Metadata Structure")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Get all archives
        archives = await get_archived_events(db)
        
        print(f"Found {len(archives)} archives:")
        print()
        
        for i, archive in enumerate(archives, 1):
            print(f"{i}. {archive['name']}")
            print(f"   Event: {archive['event_key']} ({archive['year']})")
            print(f"   Created: {archive['created_at']}")
            print(f"   Is Empty: {archive['metadata'].get('is_empty', 'Unknown')}")
            
            # Check if it has the old format (tables only)
            metadata = archive['metadata']
            has_tables = 'tables' in metadata and metadata['tables']
            has_data_types = 'data_types' in metadata and metadata['data_types']
            
            print(f"   Has tables: {has_tables}")
            print(f"   Has data_types: {has_data_types}")
            
            if has_tables:
                print("   📊 Database Tables:")
                for table, count in metadata['tables'].items():
                    print(f"      {table}: {count}")
            
            if has_data_types:
                print("   🎯 Enhanced Data Types:")
                for data_type, count in metadata['data_types'].items():
                    if count > 0:
                        print(f"      {data_type}: {count}")
            
            print()
    
    finally:
        db.close()

async def create_test_archive():
    """Create a test archive to verify the metadata structure."""
    print("=" * 80)
    print("Creating Test Archive")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Create a test archive
        result = await archive_current_event(
            db=db,
            name="Metadata Test Archive",
            event_key="test",
            year=2025,
            notes="Testing metadata structure",
            created_by="test_script"
        )
        
        print(f"Archive creation: {result['status']}")
        if result['status'] == 'success':
            print(f"Archive ID: {result['archive_id']}")
            
            # Check the metadata structure
            metadata = result['metadata']
            print("\nMetadata structure:")
            print(json.dumps(metadata, indent=2))
            
            return result['archive_id']
        else:
            print(f"Error: {result['message']}")
            return None
    
    finally:
        db.close()

async def main():
    """Run the metadata tests."""
    print("🧪 Archive Metadata Test Suite")
    print("=" * 80)
    
    try:
        # Test existing archives
        await test_archive_metadata()
        
        # Create a new test archive
        test_archive_id = await create_test_archive()
        
        if test_archive_id:
            print("\n✅ Test archive created successfully!")
            print("The frontend should now display the enhanced data types.")
        else:
            print("\n❌ Test archive creation failed.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())