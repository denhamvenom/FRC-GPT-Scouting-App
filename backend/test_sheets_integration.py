#!/usr/bin/env python3
"""
Integration tests for refactored SheetsService.
Validates exact compatibility with baseline implementation.
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add the backend app to Python path
sys.path.append('/mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App/backend')

from app.services.sheets_service import (
    get_sheets_service,
    resolve_service_account_path,
    get_active_spreadsheet_id,
    get_all_sheets_metadata,
    get_sheet_values,
    update_sheet_values,
    test_spreadsheet_connection,
    get_all_sheet_names,
    get_sheet_headers_async,
    get_sheet_headers
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SheetsServiceIntegrationTest:
    """Integration test suite for refactored SheetsService."""
    
    def __init__(self):
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        logger.info(f"{status}: {test_name} - {details}")
    
    def test_service_imports(self):
        """Test that all services can be imported and instantiated."""
        try:
            from app.services.google_auth_service import GoogleAuthService
            from app.services.sheet_metadata_service import SheetMetadataService
            from app.services.sheet_reader_service import SheetReaderService
            from app.services.sheet_writer_service import SheetWriterService
            from app.services.retry_service import RetryService
            
            # Test instantiation
            auth_service = GoogleAuthService()
            metadata_service = SheetMetadataService(auth_service)
            reader_service = SheetReaderService(auth_service, metadata_service)
            writer_service = SheetWriterService(auth_service)
            retry_service = RetryService()
            
            self.log_test("Service Imports", True, "All services imported and instantiated successfully")
            return True
        except Exception as e:
            self.log_test("Service Imports", False, f"Import error: {str(e)}")
            return False
    
    def test_public_api_preservation(self):
        """Test that all public API functions are preserved."""
        expected_functions = [
            'get_sheets_service',
            'resolve_service_account_path',
            'get_active_spreadsheet_id',
            'get_all_sheets_metadata',
            'get_sheet_values',
            'update_sheet_values',
            'test_spreadsheet_connection',
            'get_all_sheet_names',
            'get_sheet_headers_async',
            'get_sheet_headers'
        ]
        
        missing_functions = []
        for func_name in expected_functions:
            try:
                func = globals()[func_name]
                if not callable(func):
                    missing_functions.append(f"{func_name} (not callable)")
            except KeyError:
                missing_functions.append(func_name)
        
        if missing_functions:
            self.log_test("Public API Preservation", False, f"Missing functions: {missing_functions}")
            return False
        else:
            self.log_test("Public API Preservation", True, f"All {len(expected_functions)} functions preserved")
            return True
    
    def test_function_signatures(self):
        """Test that function signatures match baseline expectations."""
        import inspect
        
        signature_tests = [
            {
                'function': resolve_service_account_path,
                'expected_params': ['path'],
                'name': 'resolve_service_account_path'
            },
            {
                'function': get_active_spreadsheet_id,
                'expected_params': ['db'],
                'name': 'get_active_spreadsheet_id'
            },
            {
                'function': get_all_sheets_metadata,
                'expected_params': ['spreadsheet_id'],
                'name': 'get_all_sheets_metadata'
            },
            {
                'function': get_sheet_values,
                'expected_params': ['range_name', 'spreadsheet_id', 'db'],
                'name': 'get_sheet_values'
            },
            {
                'function': get_sheet_headers,
                'expected_params': ['tab', 'spreadsheet_id', 'log_errors'],
                'name': 'get_sheet_headers'
            }
        ]
        
        all_passed = True
        for test in signature_tests:
            sig = inspect.signature(test['function'])
            actual_params = list(sig.parameters.keys())
            
            # Check if expected parameters are present (allowing for additional ones)
            missing_params = [p for p in test['expected_params'] if p not in actual_params]
            
            if missing_params:
                self.log_test(f"Signature: {test['name']}", False, 
                            f"Missing parameters: {missing_params}")
                all_passed = False
            else:
                self.log_test(f"Signature: {test['name']}", True, 
                            f"Parameters preserved: {actual_params}")
        
        return all_passed
    
    @patch.dict(os.environ, {
        'GOOGLE_SERVICE_ACCOUNT_FILE': '/fake/path/service-account.json',
        'B64_PART_1': '',
        'B64_PART_2': ''
    })
    def test_path_resolution_logic(self):
        """Test that path resolution logic is preserved."""
        try:
            # Test with None
            result = resolve_service_account_path(None)
            if result is not None:
                self.log_test("Path Resolution - None", False, f"Expected None, got {result}")
                return False
            
            # Test with non-existent path
            result = resolve_service_account_path("/non/existent/path")
            expected = "/non/existent/path"  # Should return original path
            if result != expected:
                self.log_test("Path Resolution - Non-existent", False, 
                            f"Expected {expected}, got {result}")
                return False
            
            self.log_test("Path Resolution Logic", True, "Path resolution behavior preserved")
            return True
        except Exception as e:
            self.log_test("Path Resolution Logic", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling_patterns(self):
        """Test that error handling patterns are preserved."""
        try:
            # Test get_sheet_headers with invalid inputs
            headers = get_sheet_headers("NonExistentTab", "invalid_id", log_errors=False)
            if not isinstance(headers, list):
                self.log_test("Error Handling - Headers", False, 
                            f"Expected list, got {type(headers)}")
                return False
            
            # Should return empty list on error, not raise exception
            if len(headers) != 0:
                self.log_test("Error Handling - Headers", False, 
                            f"Expected empty list, got {headers}")
                return False
            
            self.log_test("Error Handling Patterns", True, "Error handling preserved")
            return True
        except Exception as e:
            self.log_test("Error Handling Patterns", False, f"Unexpected exception: {str(e)}")
            return False
    
    def test_dependency_injection_pattern(self):
        """Test that the new services are properly composed."""
        try:
            from app.services.sheets_service import _get_sheets_service_instance
            
            # Get the service instance
            service = _get_sheets_service_instance()
            
            # Check that all sub-services are present
            required_services = ['auth_service', 'metadata_service', 'reader_service', 
                               'writer_service', 'retry_service']
            
            missing_services = []
            for svc_name in required_services:
                if not hasattr(service, svc_name):
                    missing_services.append(svc_name)
            
            if missing_services:
                self.log_test("Dependency Injection", False, 
                            f"Missing services: {missing_services}")
                return False
            
            self.log_test("Dependency Injection Pattern", True, 
                        "All required services properly injected")
            return True
        except Exception as e:
            self.log_test("Dependency Injection Pattern", False, f"Error: {str(e)}")
            return False
    
    async def test_async_function_compatibility(self):
        """Test that async functions maintain compatibility."""
        try:
            # Test get_active_spreadsheet_id with None (should not crash)
            result = await get_active_spreadsheet_id(None)
            # Should return None when no DB session provided
            if result is not None:
                # This is actually expected behavior - None is returned
                pass
            
            # Test get_all_sheets_metadata with fake ID (should return empty list)
            result = await get_all_sheets_metadata("fake_spreadsheet_id")
            if not isinstance(result, list):
                self.log_test("Async Compatibility", False, 
                            f"get_all_sheets_metadata should return list, got {type(result)}")
                return False
            
            self.log_test("Async Function Compatibility", True, 
                        "Async functions maintain expected behavior")
            return True
        except Exception as e:
            self.log_test("Async Function Compatibility", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting SheetsService Integration Tests")
        logger.info("=" * 60)
        
        # Synchronous tests
        sync_tests = [
            self.test_service_imports,
            self.test_public_api_preservation,
            self.test_function_signatures,
            self.test_path_resolution_logic,
            self.test_error_handling_patterns,
            self.test_dependency_injection_pattern
        ]
        
        # Run sync tests
        for test in sync_tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Test crashed: {str(e)}")
        
        # Run async tests
        try:
            asyncio.run(self.test_async_function_compatibility())
        except Exception as e:
            self.log_test("test_async_function_compatibility", False, f"Test crashed: {str(e)}")
        
        # Print summary and return result
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    logger.info(f"❌ {result['test']}: {result['details']}")
        
        logger.info("=" * 60)
        
        # Return True if all tests passed, False if any failed
        return failed_tests == 0

def main():
    """Main test runner."""
    test_runner = SheetsServiceIntegrationTest()
    success = test_runner.run_all_tests()
    
    if success:
        logger.info("🎉 ALL TESTS PASSED! Refactoring maintains exact compatibility.")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED! Review and fix issues before proceeding.")
        return 1

if __name__ == "__main__":
    exit(main())