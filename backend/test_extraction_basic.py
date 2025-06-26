#!/usr/bin/env python3
"""
Basic test script to validate game context extraction functionality.
This tests the core integration without complex async mocking.
"""

import asyncio
import json
import os
import tempfile
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_aggregation_service import DataAggregationService
from app.services.game_context_extractor_service import GameContextExtractorService


def create_test_files():
    """Create temporary test files."""
    # Create dataset file
    dataset = {
        "year": 2025,
        "event_key": "2025arc",
        "teams": {
            "1001": {
                "team_number": 1001,
                "nickname": "Test Team",
                "scouting_data": []
            }
        }
    }
    
    dataset_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(dataset, dataset_file)
    dataset_file.close()
    
    # Create manual file with minimal content
    manual_data = {
        "game_name": "REEFSCAPE Test",
        "relevant_sections": """
        Game Overview:
        REEFSCAPE is an underwater-themed game with coral and algae.
        
        Scoring:
        Autonomous (15 seconds):
        - Algae in processor: 4 points
        - Coral placement: 3 points
        
        Teleop (135 seconds):
        - Coral L1: 2 points
        - Coral L2: 4 points
        - Coral L3: 6 points
        
        Endgame (30 seconds):
        - Shallow climb: 3 points
        - Deep climb: 12 points
        
        Strategy:
        Teams should focus on coral placement for higher scoring.
        Deep climbing requires specialized mechanisms.
        """
    }
    
    # Create data directory structure
    base_dir = os.path.dirname(dataset_file.name)
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    manual_file = os.path.join(data_dir, "manual_text_2025.json")
    with open(manual_file, 'w', encoding='utf-8') as f:
        json.dump(manual_data, f)
    
    return dataset_file.name, manual_file


def test_extraction_service():
    """Test the extraction service directly."""
    print("Testing extraction service...")
    
    try:
        # Create cache directory
        cache_dir = tempfile.mkdtemp()
        service = GameContextExtractorService(cache_dir=cache_dir)
        
        # Test manual data
        manual_data = {
            "game_name": "REEFSCAPE Test",
            "relevant_sections": "Test content for extraction..."
        }
        
        # Run extraction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                service.extract_game_context(manual_data, force_refresh=True)
            )
            
            if result.success:
                print("✓ Extraction successful")
                print(f"  Processing time: {result.processing_time:.2f}s")
                print(f"  Validation score: {result.validation_score:.2f}")
                return True
            else:
                print(f"✗ Extraction failed: {result.error}")
                return False
                
        finally:
            loop.close()
            
    except Exception as e:
        print(f"✗ Exception in extraction service: {e}")
        return False


def test_data_aggregation_integration():
    """Test DataAggregationService integration."""
    print("\nTesting DataAggregationService integration...")
    
    try:
        dataset_file, manual_file = create_test_files()
        
        # Test with extraction disabled (should work)
        print("Testing with extraction disabled...")
        service_full = DataAggregationService(dataset_file, use_extracted_context=False)
        context_full = service_full.load_game_context()
        
        if context_full:
            print("✓ Full manual context loaded successfully")
            print(f"  Context size: {len(context_full)} characters")
        else:
            print("✗ Failed to load full manual context")
            return False
        
        # Test extraction status
        print("Testing extraction status...")
        status = service_full.get_extraction_status()
        print(f"  Extraction enabled: {status['extraction_enabled']}")
        print(f"  Manual available: {status['manual_available']}")
        
        # Test mode switching
        print("Testing mode switching...")
        result = service_full.set_extraction_mode(True)
        if result['success']:
            print("✓ Successfully switched to extraction mode")
        else:
            print(f"✗ Failed to switch mode: {result.get('error', 'Unknown error')}")
        
        # Cleanup
        os.unlink(dataset_file)
        os.unlink(manual_file)
        os.rmdir(os.path.dirname(manual_file))
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in integration test: {e}")
        return False


def test_metadata():
    """Test metadata includes extraction information."""
    print("\nTesting metadata...")
    
    try:
        dataset_file, manual_file = create_test_files()
        
        service = DataAggregationService(dataset_file, use_extracted_context=False)
        metadata = service.get_dataset_metadata()
        
        expected_fields = ['extraction_mode', 'extraction_available', 'has_game_context']
        for field in expected_fields:
            if field in metadata:
                print(f"✓ Metadata contains {field}: {metadata[field]}")
            else:
                print(f"✗ Missing metadata field: {field}")
                return False
        
        # Cleanup
        os.unlink(dataset_file)
        os.unlink(manual_file)
        os.rmdir(os.path.dirname(manual_file))
        
        return True
        
    except Exception as e:
        print(f"✗ Exception in metadata test: {e}")
        return False


def main():
    """Run all basic tests."""
    print("=" * 50)
    print("Game Context Extraction - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        test_extraction_service,
        test_data_aggregation_integration,
        test_metadata
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Passed: {sum(results)}/{len(results)}")
    print(f"  Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())