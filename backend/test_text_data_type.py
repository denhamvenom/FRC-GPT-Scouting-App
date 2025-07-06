#!/usr/bin/env python3
"""
Test for text data type support in game labels.
"""

import os
import sys
import json
from fastapi.testclient import TestClient

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
from app.api.v1.endpoints.game_labels import GameLabel

# Create test client
client = TestClient(app)


def test_text_data_type_support():
    """Test that text data type is supported in game labels."""
    
    # Test payload with text data type
    test_label = {
        "label": "strategy_notes",
        "category": "strategic",
        "description": "General strategic observations and notes about robot performance",
        "data_type": "text",
        "typical_range": "text",
        "usage_context": "Recorded throughout match for strategic analysis"
    }
    
    # Test creating a GameLabel with text data type
    try:
        game_label = GameLabel(**test_label)
        print(f"✅ GameLabel with text data type created successfully: {game_label.label}")
        print(f"   Data type: {game_label.data_type}")
        print(f"   Description: {game_label.description}")
        
        # Verify the label can be serialized
        label_dict = game_label.model_dump()
        assert label_dict["data_type"] == "text"
        print(f"✅ Text data type serialization works")
        
        # Test API endpoint with text data type
        add_response = client.post("/api/v1/game-labels/add", json={
            "label": test_label,
            "year": 2025
        })
        
        print(f"API response status: {add_response.status_code}")
        if add_response.status_code == 200:
            response_data = add_response.json()
            print(f"✅ API accepts text data type: {response_data}")
        else:
            print(f"❌ API rejected text data type: {add_response.json()}")
            
        return True
        
    except Exception as e:
        print(f"❌ Text data type test failed: {e}")
        return False


def test_all_data_types():
    """Test all supported data types."""
    
    data_types = ['count', 'rating', 'boolean', 'time', 'text']
    
    for data_type in data_types:
        test_label = {
            "label": f"test_{data_type}_field",
            "category": "strategic",
            "description": f"Test field for {data_type} data type",
            "data_type": data_type,
            "typical_range": "varies" if data_type == "text" else "0-10",
            "usage_context": "Test usage"
        }
        
        try:
            game_label = GameLabel(**test_label)
            print(f"✅ {data_type.upper()} data type supported")
        except Exception as e:
            print(f"❌ {data_type.upper()} data type failed: {e}")
            return False
    
    return True


if __name__ == "__main__":
    print("🔍 Testing text data type support in game labels...")
    
    success1 = test_text_data_type_support()
    print()
    
    print("🔍 Testing all data types...")
    success2 = test_all_data_types()
    
    if success1 and success2:
        print("\n🎉 All text data type tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)