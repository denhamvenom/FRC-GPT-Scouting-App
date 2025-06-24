#!/usr/bin/env python3
"""
End-to-End Workflow Tests
Tests complete user workflows to ensure functionality is preserved
"""

import pytest
import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class TestEndToEndWorkflows:
    """Test complete user workflows"""
    
    @pytest.fixture
    def api_client(self):
        """Create API client session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_health_check(self, api_client):
        """Test basic system health"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_schema_workflow(self, api_client):
        """Test schema loading and selection workflow"""
        # Step 1: Load schema
        response = api_client.get(f"{BASE_URL}/api/schema")
        assert response.status_code == 200
        schema = response.json()
        assert isinstance(schema, list)
        
        # Step 2: Get current selections
        response = api_client.get(f"{BASE_URL}/api/schema/selections")
        assert response.status_code == 200
        selections = response.json()
        
        # Step 3: Save new selection (if schema exists)
        if schema:
            field_id = schema[0].get("id")
            if field_id:
                save_data = {
                    "field_id": field_id,
                    "selected": True
                }
                response = api_client.post(
                    f"{BASE_URL}/api/schema/save-selection",
                    json=save_data
                )
                # May return 200 or 422 depending on data
                assert response.status_code in [200, 422]
    
    def test_sheets_configuration_workflow(self, api_client):
        """Test Google Sheets configuration workflow"""
        # Step 1: Get current sheet config
        response = api_client.get(f"{BASE_URL}/api/sheet-config")
        assert response.status_code in [200, 404]  # 404 if no config yet
        
        # Step 2: Get headers (if configured)
        response = api_client.get(f"{BASE_URL}/api/sheets/headers")
        assert response.status_code in [200, 404, 400]
        
        # Step 3: Validate sheet config can be saved
        config_data = {
            "sheet_id": "test_sheet_id",
            "data_range": "A1:Z100"
        }
        response = api_client.post(f"{BASE_URL}/api/sheet-config", json=config_data)
        # Should accept the config even if it can't connect
        assert response.status_code in [200, 400, 422]
    
    def test_team_comparison_workflow(self, api_client):
        """Test team comparison workflow"""
        # Step 1: Get available teams
        response = api_client.get(f"{BASE_URL}/api/team-comparison/teams")
        assert response.status_code in [200, 404]
        
        # Step 2: If teams available, compare them
        if response.status_code == 200:
            teams = response.json()
            if isinstance(teams, list) and len(teams) >= 2:
                comparison_data = {
                    "team_numbers": [teams[0], teams[1]]
                }
                response = api_client.post(
                    f"{BASE_URL}/api/team-comparison/compare",
                    json=comparison_data
                )
                assert response.status_code in [200, 422]
    
    def test_picklist_generation_workflow(self, api_client):
        """Test picklist generation workflow"""
        # Step 1: Check if we can generate picklist
        response = api_client.get(f"{BASE_URL}/api/picklist/teams")
        assert response.status_code in [200, 404]
        
        # Step 2: Get picklist analysis if available
        response = api_client.get(f"{BASE_URL}/api/picklist-analysis/summary")
        assert response.status_code in [200, 404]
        
        # Step 3: Try to generate new picklist
        generate_data = {
            "strategy": "balanced",
            "team_count": 24
        }
        response = api_client.post(
            f"{BASE_URL}/api/picklist/generate",
            json=generate_data
        )
        # May fail if no data available
        assert response.status_code in [200, 400, 422]
    
    def test_unified_dataset_workflow(self, api_client):
        """Test unified dataset builder workflow"""
        # Step 1: Get available events
        response = api_client.get(f"{BASE_URL}/api/unified-dataset/events")
        assert response.status_code in [200, 404]
        
        # Step 2: If events available, get event data
        if response.status_code == 200:
            events = response.json()
            if isinstance(events, list) and events:
                event_key = events[0] if isinstance(events[0], str) else events[0].get("key")
                if event_key:
                    response = api_client.get(
                        f"{BASE_URL}/api/unified-dataset/event/{event_key}"
                    )
                    assert response.status_code in [200, 404]
    
    def test_validation_workflow(self, api_client):
        """Test data validation workflow"""
        # Step 1: Run validation
        response = api_client.get(f"{BASE_URL}/api/validate")
        assert response.status_code == 200
        
        validation_result = response.json()
        assert isinstance(validation_result, dict)
        # Should have validation results structure
        assert any(key in validation_result for key in ["valid", "errors", "warnings", "status"])
    
    def test_progress_tracking_workflow(self, api_client):
        """Test progress tracking across operations"""
        # Step 1: Check current progress
        response = api_client.get(f"{BASE_URL}/api/progress/status")
        assert response.status_code == 200
        
        status = response.json()
        assert isinstance(status, dict)
        # Should have progress structure
        assert any(key in status for key in ["status", "progress", "message", "current_task"])
    
    def test_error_handling_workflow(self, api_client):
        """Test that errors are handled gracefully"""
        # Test invalid endpoints return proper errors
        response = api_client.get(f"{BASE_URL}/api/nonexistent")
        assert response.status_code == 404
        
        # Test invalid data handling
        response = api_client.post(
            f"{BASE_URL}/api/team-comparison/compare",
            json={"invalid": "data"}
        )
        assert response.status_code in [400, 422]
        
        # Ensure error response has proper structure
        if response.status_code != 200:
            try:
                error_data = response.json()
                assert isinstance(error_data, dict)
                # Should have error details
                assert any(key in error_data for key in ["detail", "error", "message"])
            except json.JSONDecodeError:
                # Some errors might return text
                assert len(response.text) > 0
    
    def test_concurrent_requests(self, api_client):
        """Test system handles concurrent requests properly"""
        import concurrent.futures
        
        def make_request(endpoint):
            return api_client.get(f"{BASE_URL}{endpoint}")
        
        endpoints = [
            "/api/health",
            "/api/schema",
            "/api/progress/status",
            "/api/validate"
        ]
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should complete successfully
        assert all(r.status_code in [200, 404] for r in results)


def run_integration_tests():
    """Run all integration tests and report results"""
    print("=== Running Integration Tests ===")
    
    # Check if services are running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print("ERROR: Backend service not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("ERROR: Backend service not running on port 8000")
        print("Please start the backend with: cd backend && uvicorn app.main:app --reload")
        return False
    
    # Run pytest
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
    success = run_integration_tests()
    sys.exit(0 if success else 1)