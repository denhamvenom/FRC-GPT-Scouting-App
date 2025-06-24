#!/usr/bin/env python3
"""
Error Scenario Tests
Tests system behavior under error conditions
"""

import pytest
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestErrorScenarios:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def api_client(self):
        """Create API client session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_malformed_json_handling(self, api_client):
        """Test handling of malformed JSON requests"""
        # Send invalid JSON
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            data="{'invalid': json}",  # Malformed JSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, api_client):
        """Test handling of missing required fields"""
        # Schema save without required fields
        response = api_client.post(
            f"{BASE_URL}/api/schema/save-selection",
            json={}  # Missing required fields
        )
        assert response.status_code in [400, 422]
        
        # Team comparison without team numbers
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            json={"wrong_field": "value"}
        )
        assert response.status_code in [400, 422]
    
    def test_invalid_data_types(self, api_client):
        """Test handling of invalid data types"""
        # String where number expected
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            json={"team_numbers": ["not", "numbers"]}
        )
        assert response.status_code in [400, 422]
        
        # Number where string expected
        response = api_client.post(
            f"{BASE_URL}/api/sheet-config",
            json={"sheet_id": 12345, "data_range": "A1:B2"}
        )
        assert response.status_code in [200, 400, 422]  # May accept and convert
    
    def test_boundary_conditions(self, api_client):
        """Test boundary conditions"""
        # Empty arrays
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            json={"team_numbers": []}
        )
        assert response.status_code in [400, 422]
        
        # Very large requests
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            json={"team_numbers": list(range(1, 1000))}  # 999 teams
        )
        assert response.status_code in [200, 400, 422]
        
        # Negative numbers
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            json={"team_numbers": [-1, -2]}
        )
        assert response.status_code in [400, 422]
    
    def test_injection_attempts(self, api_client):
        """Test handling of injection attempts"""
        # SQL injection attempt in string field
        response = api_client.post(
            f"{BASE_URL}/api/sheet-config",
            json={
                "sheet_id": "'; DROP TABLE users; --",
                "data_range": "A1:B2"
            }
        )
        # Should handle safely
        assert response.status_code in [200, 400, 422]
        
        # Script injection in fields
        response = api_client.post(
            f"{BASE_URL}/api/schema/save-selection",
            json={
                "field_id": "<script>alert('xss')</script>",
                "selected": True
            }
        )
        assert response.status_code in [200, 400, 422]
    
    def test_concurrent_error_conditions(self, api_client):
        """Test error handling under concurrent load"""
        import concurrent.futures
        
        def make_bad_request():
            return api_client.post(
                f"{BASE_URL}/api/team-comparison/compare",
                json={"invalid": "data"}
            )
        
        # Send multiple bad requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_bad_request) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should be handled properly
        assert all(r.status_code in [400, 422] for r in results)
    
    def test_timeout_handling(self, api_client):
        """Test handling of slow/timeout scenarios"""
        # Very short timeout to simulate network issues
        try:
            response = api_client.get(
                f"{BASE_URL}/api/health",
                timeout=0.001  # 1ms timeout
            )
        except requests.exceptions.Timeout:
            # This is expected behavior
            pass
        except Exception as e:
            # Other exceptions indicate improper error handling
            pytest.fail(f"Unexpected exception: {e}")
    
    def test_method_not_allowed(self, api_client):
        """Test handling of wrong HTTP methods"""
        # POST to GET-only endpoint
        response = api_client.post(f"{BASE_URL}/api/health")
        assert response.status_code == 405  # Method Not Allowed
        
        # GET to POST-only endpoint
        response = api_client.get(f"{BASE_URL}/api/team-comparison/compare")
        assert response.status_code == 405
    
    def test_content_type_validation(self, api_client):
        """Test content-type header validation"""
        # Wrong content type
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            data="team_numbers=254,1114",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        # Should either handle or reject
        assert response.status_code in [400, 415, 422]
    
    def test_error_response_format(self, api_client):
        """Test that error responses have consistent format"""
        # Trigger various errors
        error_triggers = [
            (f"{BASE_URL}/api/nonexistent", "GET", None),
            (f"{BASE_URL}/api/team-comparison/compare", "POST", {"invalid": "data"}),
            (f"{BASE_URL}/api/health", "POST", None),
        ]
        
        for url, method, data in error_triggers:
            if method == "GET":
                response = api_client.get(url)
            else:
                response = api_client.post(url, json=data)
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    # Should be a dict with error information
                    assert isinstance(error_data, dict)
                    # Should have some error indicator
                    assert any(key in error_data for key in ["detail", "error", "message", "msg"])
                except json.JSONDecodeError:
                    # If not JSON, should at least have text
                    assert len(response.text) > 0


def run_error_tests():
    """Run all error scenario tests"""
    print("=== Running Error Scenario Tests ===")
    
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    import sys
    success = run_error_tests()
    sys.exit(0 if success else 1)