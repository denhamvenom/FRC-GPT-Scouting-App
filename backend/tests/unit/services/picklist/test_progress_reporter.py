"""
Unit tests for PicklistProgressReporter.
"""

import pytest
import time
from unittest.mock import Mock, patch

from app.services.picklist.core.progress_reporter import PicklistProgressReporter


class TestPicklistProgressReporter:
    """Test PicklistProgressReporter functionality."""
    
    @pytest.fixture
    def operation_id(self):
        """Sample operation ID for testing."""
        return "test_operation_123"
    
    @pytest.fixture
    def progress_reporter(self, operation_id):
        """Create progress reporter instance for testing."""
        return PicklistProgressReporter(operation_id)
    
    def test_reporter_initialization(self, progress_reporter, operation_id):
        """Test progress reporter initialization."""
        assert progress_reporter.operation_id == operation_id
        assert hasattr(progress_reporter, 'start_time')
        assert progress_reporter.start_time > 0
    
    def test_update_progress(self, progress_reporter):
        """Test updating progress."""
        progress_reporter.update(25, "Processing teams...", "processing")
        
        # Should be stored in global progress tracker
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        
        assert status is not None
        assert status["percentage"] == 25
        assert status["message"] == "Processing teams..."
        assert status["stage"] == "processing"
    
    def test_update_batch_progress(self, progress_reporter):
        """Test updating batch progress."""
        progress_reporter.update_batch_progress(
            current_batch=2,
            total_batches=5,
            batch_progress=50,
            message="Processing batch 2 of 5"
        )
        
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        
        assert status is not None
        assert "batch_info" in status
        assert status["batch_info"]["current_batch"] == 2
        assert status["batch_info"]["total_batches"] == 5
        assert status["batch_info"]["batch_progress"] == 50
    
    def test_calculate_eta(self, progress_reporter):
        """Test ETA calculation."""
        # Mock time progression
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000
            progress_reporter.start_time = 900  # Started 100 seconds ago
            
            eta = progress_reporter._calculate_eta(50)  # 50% complete
            
            # Should estimate another 100 seconds (same time to complete remaining 50%)
            assert abs(eta - 100) < 1
    
    def test_eta_edge_cases(self, progress_reporter):
        """Test ETA calculation edge cases."""
        # Zero progress should return None
        eta = progress_reporter._calculate_eta(0)
        assert eta is None
        
        # 100% progress should return 0
        eta = progress_reporter._calculate_eta(100)
        assert eta == 0
        
        # Very small progress should cap ETA
        with patch('time.time') as mock_time:
            mock_time.return_value = 2000
            progress_reporter.start_time = 1000  # 1000 seconds ago
            
            eta = progress_reporter._calculate_eta(1)  # 1% complete
            assert eta <= progress_reporter.MAX_ETA_SECONDS
    
    def test_update_with_eta(self, progress_reporter):
        """Test progress update with ETA calculation."""
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000
            progress_reporter.start_time = 900
            
            progress_reporter.update(25, "Quarter done", "processing")
            
            from app.services.progress_tracker import ProgressTracker
            status = ProgressTracker.get_progress(progress_reporter.operation_id)
            
            assert "eta_seconds" in status
            assert status["eta_seconds"] > 0
    
    def test_complete_operation(self, progress_reporter):
        """Test completing an operation."""
        progress_reporter.complete("Operation completed successfully", {"teams_processed": 50})
        
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        
        assert status["percentage"] == 100
        assert status["message"] == "Operation completed successfully"
        assert status["stage"] == "completed"
        assert status["result"]["teams_processed"] == 50
    
    def test_fail_operation(self, progress_reporter):
        """Test failing an operation."""
        error_message = "Something went wrong"
        progress_reporter.fail(error_message)
        
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        
        assert status["percentage"] == 0
        assert status["message"] == error_message
        assert status["stage"] == "failed"
    
    def test_update_with_details(self, progress_reporter):
        """Test progress update with additional details."""
        details = {
            "teams_processed": 25,
            "teams_remaining": 75,
            "current_batch": 1,
            "processing_rate": "2.5 teams/second"
        }
        
        progress_reporter.update(25, "Processing...", "processing", details)
        
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        
        assert status["details"]["teams_processed"] == 25
        assert status["details"]["processing_rate"] == "2.5 teams/second"
    
    def test_multiple_operations(self):
        """Test multiple concurrent operations."""
        reporter1 = PicklistProgressReporter("op1")
        reporter2 = PicklistProgressReporter("op2")
        
        reporter1.update(30, "Operation 1", "processing")
        reporter2.update(60, "Operation 2", "processing")
        
        from app.services.progress_tracker import ProgressTracker
        status1 = ProgressTracker.get_progress("op1")
        status2 = ProgressTracker.get_progress("op2")
        
        assert status1["percentage"] == 30
        assert status2["percentage"] == 60
        assert status1["message"] != status2["message"]
    
    def test_stage_transitions(self, progress_reporter):
        """Test typical stage transitions."""
        stages = [
            (5, "Initializing", "initialization"),
            (20, "Loading data", "data_loading"),
            (40, "Processing teams", "processing"),
            (70, "Generating rankings", "ranking"),
            (90, "Finalizing", "finalization"),
            (100, "Complete", "completed")
        ]
        
        for percentage, message, stage in stages:
            progress_reporter.update(percentage, message, stage)
            
            from app.services.progress_tracker import ProgressTracker
            status = ProgressTracker.get_progress(progress_reporter.operation_id)
            
            assert status["percentage"] == percentage
            assert status["stage"] == stage
    
    def test_time_tracking(self, progress_reporter):
        """Test time tracking functionality."""
        with patch('time.time') as mock_time:
            # Simulate operation running for 30 seconds
            mock_time.side_effect = [1000, 1030]
            
            progress_reporter.update(50, "Halfway", "processing")
            
            from app.services.progress_tracker import ProgressTracker
            status = ProgressTracker.get_progress(progress_reporter.operation_id)
            
            assert status["elapsed_seconds"] == 30
    
    def test_cleanup_on_completion(self, progress_reporter):
        """Test cleanup behavior on completion."""
        progress_reporter.complete("Done")
        
        # Progress should still be accessible immediately after completion
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        assert status is not None
        
        # Test that cleanup can be triggered manually
        ProgressTracker.cleanup_operation(progress_reporter.operation_id)
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        assert status is None
    
    def test_error_handling_in_updates(self, progress_reporter):
        """Test error handling during progress updates."""
        # Should handle invalid percentages gracefully
        progress_reporter.update(-10, "Invalid percentage", "processing")
        progress_reporter.update(150, "Another invalid", "processing")
        
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        
        # Should clamp values to valid range
        assert 0 <= status["percentage"] <= 100
    
    def test_concurrent_updates(self, progress_reporter):
        """Test concurrent progress updates."""
        import threading
        import time
        
        def update_progress(start_pct):
            for i in range(10):
                progress_reporter.update(
                    start_pct + i,
                    f"Update {start_pct + i}",
                    "processing"
                )
                time.sleep(0.01)
        
        # Start multiple threads updating progress
        threads = []
        for start in [10, 30, 50]:
            thread = threading.Thread(target=update_progress, args=(start,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should handle concurrent updates without errors
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        assert status is not None
    
    def test_memory_usage_tracking(self, progress_reporter):
        """Test memory usage tracking in progress."""
        import psutil
        import os
        
        # Get current memory usage
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        details = {"memory_usage_mb": round(memory_mb, 2)}
        progress_reporter.update(50, "Memory test", "processing", details)
        
        from app.services.progress_tracker import ProgressTracker
        status = ProgressTracker.get_progress(progress_reporter.operation_id)
        
        assert "memory_usage_mb" in status["details"]
        assert status["details"]["memory_usage_mb"] > 0