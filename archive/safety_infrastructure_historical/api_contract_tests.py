#!/usr/bin/env python3
"""
API Contract Tests
Ensures API responses maintain exact structure and data types
"""

import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

class APIContractValidator:
    def __init__(self, api_base_url="http://localhost:8000"):
        self.api_base_url = api_base_url
        self.contract_violations = []
        
    def validate_response_structure(self, endpoint: str, response_data: Any, expected_structure: Dict[str, type]) -> bool:
        """Validate response matches expected structure"""
        if not isinstance(response_data, dict):
            self.contract_violations.append(f"{endpoint}: Response is not a dictionary")
            return False
            
        for key, expected_type in expected_structure.items():
            if key not in response_data:
                self.contract_violations.append(f"{endpoint}: Missing required field '{key}'")
                return False
                
            if not isinstance(response_data[key], expected_type):
                self.contract_violations.append(
                    f"{endpoint}: Field '{key}' has wrong type. Expected {expected_type}, got {type(response_data[key])}"
                )
                return False
                
        return True
    
    def test_health_endpoint(self):
        """Test /api/health contract"""
        print("Testing /api/health contract...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/health")
            if response.status_code != 200:
                self.contract_violations.append(f"/api/health: Expected status 200, got {response.status_code}")
                return False
                
            data = response.json()
            expected_structure = {
                "status": str,
                "timestamp": str
            }
            
            return self.validate_response_structure("/api/health", data, expected_structure)
            
        except Exception as e:
            self.contract_violations.append(f"/api/health: Request failed - {str(e)}")
            return False
    
    def test_schema_endpoint(self):
        """Test /api/schema contract"""
        print("Testing /api/schema contract...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/schema")
            if response.status_code != 200:
                self.contract_violations.append(f"/api/schema: Expected status 200, got {response.status_code}")
                return False
                
            data = response.json()
            
            # Schema should return a list
            if not isinstance(data, list):
                self.contract_violations.append("/api/schema: Response should be a list")
                return False
                
            # Each item should have specific fields
            if data:  # If there are items
                item = data[0]
                expected_fields = ["id", "name", "type", "label"]
                for field in expected_fields:
                    if field not in item:
                        self.contract_violations.append(f"/api/schema: Missing field '{field}' in schema item")
                        return False
                        
            return True
            
        except Exception as e:
            self.contract_violations.append(f"/api/schema: Request failed - {str(e)}")
            return False
    
    def test_team_comparison_endpoint(self):
        """Test /api/team-comparison/* contracts"""
        print("Testing /api/team-comparison contracts...")
        
        # Test compare endpoint structure
        try:
            # This might fail if no data, but we're testing contract not data
            response = requests.post(
                f"{self.api_base_url}/api/team-comparison/compare",
                json={"team_numbers": [254, 1114]},
                headers={"Content-Type": "application/json"}
            )
            
            # Contract allows 200 or 422 (validation error)
            if response.status_code not in [200, 422]:
                self.contract_violations.append(
                    f"/api/team-comparison/compare: Unexpected status {response.status_code}"
                )
                
            # If successful, validate response structure
            if response.status_code == 200:
                data = response.json()
                if not isinstance(data, dict):
                    self.contract_violations.append("/api/team-comparison/compare: Response should be a dict")
                    
            return True
            
        except Exception as e:
            self.contract_violations.append(f"/api/team-comparison: Request failed - {str(e)}")
            return False
    
    def test_picklist_endpoint(self):
        """Test /api/picklist/* contracts"""
        print("Testing /api/picklist contracts...")
        
        try:
            response = requests.get(f"{self.api_base_url}/api/picklist/teams")
            
            # Contract allows 200 or 404 (no teams)
            if response.status_code not in [200, 404]:
                self.contract_violations.append(
                    f"/api/picklist/teams: Unexpected status {response.status_code}"
                )
                
            if response.status_code == 200:
                data = response.json()
                if not isinstance(data, list):
                    self.contract_violations.append("/api/picklist/teams: Response should be a list")
                    
            return True
            
        except Exception as e:
            self.contract_violations.append(f"/api/picklist: Request failed - {str(e)}")
            return False
    
    def save_contract_snapshot(self, filename="api_contracts.json"):
        """Save current API response structures for future comparison"""
        print("Saving API contract snapshot...")
        
        endpoints = [
            "/api/health",
            "/api/schema",
            "/api/schema/selections",
            "/api/sheets/headers",
            "/api/picklist/teams",
            "/api/unified-dataset/events"
        ]
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "endpoints": {}
        }
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=5)
                snapshot["endpoints"][endpoint] = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "response_type": str(type(response.json() if response.content else None))
                }
                
                # Store structure example for successful responses
                if response.status_code == 200 and response.content:
                    data = response.json()
                    if isinstance(data, list) and data:
                        snapshot["endpoints"][endpoint]["list_item_keys"] = list(data[0].keys()) if isinstance(data[0], dict) else None
                    elif isinstance(data, dict):
                        snapshot["endpoints"][endpoint]["response_keys"] = list(data.keys())
                        
            except Exception as e:
                snapshot["endpoints"][endpoint] = {"error": str(e)}
        
        with open(filename, 'w') as f:
            json.dump(snapshot, f, indent=2)
            
        print(f"Contract snapshot saved to {filename}")
    
    def run_all_tests(self):
        """Run all contract tests"""
        print("\n=== API Contract Validation ===")
        
        tests = [
            self.test_health_endpoint,
            self.test_schema_endpoint,
            self.test_team_comparison_endpoint,
            self.test_picklist_endpoint
        ]
        
        all_passed = True
        for test in tests:
            passed = test()
            all_passed = all_passed and passed
            
        if self.contract_violations:
            print("\nContract Violations Found:")
            for violation in self.contract_violations:
                print(f"  - {violation}")
        else:
            print("\nAll API contracts validated successfully!")
            
        return all_passed


def main():
    validator = APIContractValidator()
    
    # Save contract snapshot
    validator.save_contract_snapshot("safety/api_contracts.json")
    
    # Run validation tests
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()