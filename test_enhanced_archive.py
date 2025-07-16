#!/usr/bin/env python3
"""
Test script for the enhanced archive functionality.
Tests the new comprehensive data collection features.
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database.db import SessionLocal
from app.services.archive_service import (
    archive_current_event,
    get_archived_events,
    get_archived_event,
    restore_archived_event,
    _collect_event_specific_files,
    _collect_manual_data_files,
    _collect_cache_files,
    _collect_config_files,
    _collect_manual_processing_data
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_data_collection_functions():
    """Test the individual data collection functions."""
    print("=" * 80)
    print("Testing Enhanced Archive Data Collection Functions")
    print("=" * 80)
    
    # Test event-specific file collection
    print("\n1. Testing event-specific file collection...")
    event_files = _collect_event_specific_files("iri", 2025)
    print(f"   Found {len(event_files)} event-specific files:")
    for filename in event_files.keys():
        print(f"   - {filename}")
    
    # Test manual data file collection
    print("\n2. Testing manual data file collection...")
    manual_files = _collect_manual_data_files(2025)
    print(f"   Found {len(manual_files)} manual data files:")
    for filename in manual_files.keys():
        print(f"   - {filename}")
    
    # Test cache file collection
    print("\n3. Testing cache file collection...")
    cache_files = _collect_cache_files(limit=10)
    print(f"   Found {len(cache_files)} cache files (limited to 10):")
    for filename in list(cache_files.keys())[:5]:  # Show first 5
        print(f"   - {filename}")
    if len(cache_files) > 5:
        print(f"   - ... and {len(cache_files) - 5} more")
    
    # Test config file collection
    print("\n4. Testing config file collection...")
    config_files = _collect_config_files()
    print(f"   Found {len(config_files)} config files:")
    for filename in config_files.keys():
        print(f"   - {filename}")
    
    # Test manual processing data collection
    print("\n5. Testing manual processing data collection...")
    processing_files = _collect_manual_processing_data(2025)
    print(f"   Found {len(processing_files)} manual processing files:")
    for filename in processing_files.keys():
        print(f"   - {filename}")
    
    # Calculate total files that would be included
    total_files = len(event_files) + len(manual_files) + len(cache_files) + len(config_files) + len(processing_files)
    print(f"\n📊 Total files that would be included in archive: {total_files}")
    
    return {
        "event_files": len(event_files),
        "manual_files": len(manual_files),
        "cache_files": len(cache_files),
        "config_files": len(config_files),
        "processing_files": len(processing_files),
        "total_files": total_files
    }

async def test_enhanced_archive_creation():
    """Test creating an archive with the enhanced functionality."""
    print("\n" + "=" * 80)
    print("Testing Enhanced Archive Creation")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Create a test archive for 2025 IRI
        archive_result = await archive_current_event(
            db=db,
            name="2025 IRI Enhanced Test Archive",
            event_key="iri",
            year=2025,
            notes="Testing enhanced archive functionality with comprehensive data collection",
            created_by="test_script"
        )
        
        print(f"Archive creation result: {archive_result['status']}")
        print(f"Message: {archive_result['message']}")
        
        if archive_result['status'] == 'success':
            # Get the archive details
            archive_id = archive_result['archive_id']
            archive_details = await get_archived_event(db, archive_id)
            
            print(f"\n📋 Archive Details:")
            print(f"   ID: {archive_details['id']}")
            print(f"   Name: {archive_details['name']}")
            print(f"   Event: {archive_details['event_key']} ({archive_details['year']})")
            print(f"   Created: {archive_details['created_at']}")
            print(f"   Is Empty: {archive_details['metadata'].get('is_empty', 'Unknown')}")
            
            # Show data types included
            data_types = archive_details['metadata'].get('data_types', {})
            print(f"\n📊 Data Types Included:")
            for data_type, count in data_types.items():
                print(f"   {data_type}: {count} files")
            
            # Show total files
            total_files = sum(data_types.values())
            print(f"   Total data files: {total_files}")
            
            # Show database table counts
            tables = archive_details['metadata'].get('tables', {})
            print(f"\n🗃️ Database Tables:")
            for table_name, count in tables.items():
                print(f"   {table_name}: {count} records")
            
            return archive_id
        else:
            print(f"❌ Archive creation failed: {archive_result['message']}")
            return None
            
    finally:
        db.close()

async def test_archive_listing():
    """Test listing archives to see the enhanced metadata."""
    print("\n" + "=" * 80)
    print("Testing Archive Listing")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        archives = await get_archived_events(db)
        
        print(f"Found {len(archives)} archives:")
        for i, archive in enumerate(archives, 1):
            print(f"\n{i}. {archive['name']}")
            print(f"   Event: {archive['event_key']} ({archive['year']})")
            print(f"   Created: {archive['created_at']}")
            print(f"   Is Empty: {archive['metadata'].get('is_empty', 'Unknown')}")
            
            # Show data types if available
            data_types = archive['metadata'].get('data_types', {})
            if data_types:
                total_files = sum(data_types.values())
                print(f"   Data Files: {total_files}")
                print(f"   Types: {', '.join([f'{k}({v})' for k, v in data_types.items() if v > 0])}")
            
            # Show database table counts
            tables = archive['metadata'].get('tables', {})
            if tables:
                print(f"   DB Tables: {', '.join([f'{k}({v})' for k, v in tables.items()])}")
    
    finally:
        db.close()

async def main():
    """Run all tests."""
    print("🚀 Enhanced Archive Functionality Test Suite")
    print("=" * 80)
    
    try:
        # Test data collection functions
        collection_stats = await test_data_collection_functions()
        
        # Test archive creation
        archive_id = await test_enhanced_archive_creation()
        
        # Test archive listing
        await test_archive_listing()
        
        print("\n" + "=" * 80)
        print("✅ Test Summary")
        print("=" * 80)
        print(f"Data Collection Functions: ✅ Working")
        print(f"Archive Creation: {'✅ Success' if archive_id else '❌ Failed'}")
        print(f"Archive Listing: ✅ Working")
        print(f"Total Files Collected: {collection_stats['total_files']}")
        
        if archive_id:
            print(f"Test Archive ID: {archive_id}")
            print("You can now test the archive restore functionality!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())