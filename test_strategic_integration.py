#!/usr/bin/env python3
"""
Simple integration test for strategic intelligence file generation.

This script validates that the new strategic intelligence integration
works without requiring actual API calls or full environment setup.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_integration():
    """Test the strategic intelligence integration."""
    
    print("🔍 Testing Strategic Intelligence File Generation Integration")
    print("=" * 60)
    
    # Test 1: Verify imports
    print("\n1️⃣ Testing imports...")
    try:
        # Test core service imports
        sys.path.append('backend')
        
        # Test that we can import without executing initialization code
        from unittest.mock import patch
        
        # Mock environment-dependent imports
        with patch('app.config.openai_config.OPENAI_API_KEY', 'test_key'):
            with patch('app.config.openai_config.OPENAI_MODEL', 'gpt-4'):
                from app.services.data_aggregation_service import DataAggregationService
                from app.services.strategic_analysis_service import StrategicAnalysisService
        
        print("   ✅ Core service imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Verify method existence
    print("\n2️⃣ Testing method availability...")
    try:
        # Check DataAggregationService has strategic intelligence method
        data_service_methods = [m for m in dir(DataAggregationService) if 'strategic' in m.lower()]
        assert 'generate_strategic_intelligence_file' in data_service_methods
        print("   ✅ DataAggregationService.generate_strategic_intelligence_file exists")
        
        # Check StrategicAnalysisService has main method
        strategic_service_methods = [m for m in dir(StrategicAnalysisService) if 'generate' in m.lower()]
        assert any('strategic_intelligence' in m for m in strategic_service_methods)
        print("   ✅ StrategicAnalysisService.generate_strategic_intelligence exists")
        
    except Exception as e:
        print(f"   ❌ Method check failed: {e}")
        return False
    
    # Test 3: Verify file structure
    print("\n3️⃣ Testing file structure...")
    try:
        required_files = [
            'backend/app/api/performance_signatures.py',
            'backend/app/services/data_aggregation_service.py',
            'backend/app/services/strategic_analysis_service.py',
            'frontend/src/pages/Validation.tsx'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file missing: {file_path}")
            print(f"   ✅ {file_path} exists")
            
    except Exception as e:
        print(f"   ❌ File structure check failed: {e}")
        return False
    
    # Test 4: Verify API response model
    print("\n4️⃣ Testing API response model...")
    try:
        with patch('app.config.openai_config.OPENAI_API_KEY', 'test_key'):
            with patch('app.config.openai_config.OPENAI_MODEL', 'gpt-4'):
                from app.api.performance_signatures import PerformanceSignatureResponse
        
        # Check response model has strategic intelligence fields
        model_fields = PerformanceSignatureResponse.__annotations__.keys()
        assert 'strategic_intelligence_filepath' in model_fields
        assert 'strategic_teams_analyzed' in model_fields
        print("   ✅ API response model includes strategic intelligence fields")
        
    except Exception as e:
        print(f"   ❌ API response model check failed: {e}")
        return False
    
    # Test 5: Verify frontend integration
    print("\n5️⃣ Testing frontend integration...")
    try:
        with open('frontend/src/pages/Validation.tsx', 'r') as f:
            content = f.read()
        
        # Check for strategic analysis progress steps
        assert 'Generating strategic intelligence for all teams...' in content
        assert 'Processing teams in strategic analysis batches...' in content
        assert 'Creating strategic intelligence files...' in content
        assert 'Strategic analysis complete!' in content
        print("   ✅ Frontend includes strategic analysis progress tracking")
        
        # Check for enhanced success message
        assert 'strategic_teams_analyzed' in content
        print("   ✅ Frontend includes enhanced success messaging")
        
    except Exception as e:
        print(f"   ❌ Frontend integration check failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("\n📋 Integration Summary:")
    print("   • Performance signatures API extended with strategic analysis")
    print("   • DataAggregationService includes strategic intelligence file generation")
    print("   • Frontend validation progress includes strategic analysis steps")
    print("   • API response model supports both signature and intelligence results")
    print("   • Strategic intelligence files will be generated alongside performance signatures")
    print("\n🚀 Ready for end-to-end testing with actual data!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)