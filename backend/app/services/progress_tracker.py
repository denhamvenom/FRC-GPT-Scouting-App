# backend/app/services/progress_tracker.py

import time
from typing import Dict, Any, Optional
import json

class ProgressTracker:
    """
    Service for tracking progress of long-running operations.
    Provides a way to update and retrieve progress information.
    """
    
    _instances: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def create_tracker(cls, operation_id: str) -> 'ProgressTracker':
        """
        Create a new progress tracker for a specific operation.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            A new ProgressTracker instance
        """
        tracker = cls(operation_id)
        cls._instances[operation_id] = {
            "status": "initializing",
            "message": "Operation starting...",
            "progress": 0,
            "start_time": time.time(),
            "current_step": "",
            "steps_completed": [],
            "estimated_time_remaining": None,
            "last_update": time.time()
        }
        return tracker
    
    @classmethod
    def get_progress(cls, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current progress of an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Current progress information or None if not found
        """
        if operation_id not in cls._instances:
            return None
        
        progress_data = cls._instances[operation_id].copy()
        
        # Calculate duration
        current_time = time.time()
        duration = current_time - progress_data["start_time"]
        progress_data["duration"] = round(duration, 1)
        
        # Check if we need to update the "active" status
        if progress_data["status"] == "active" and (current_time - progress_data["last_update"]) > 60:
            progress_data["status"] = "stalled"
            progress_data["message"] = "Operation may have stalled."
            cls._instances[operation_id]["status"] = "stalled"
            cls._instances[operation_id]["message"] = "Operation may have stalled."
        
        return progress_data
    
    @classmethod
    def list_operations(cls) -> Dict[str, Dict[str, Any]]:
        """
        List all tracked operations and their progress.
        
        Returns:
            Dictionary of operation_id -> progress data
        """
        return {op_id: cls.get_progress(op_id) for op_id in cls._instances}
    
    @classmethod
    def clean_old_operations(cls, max_age_seconds: int = 3600) -> int:
        """
        Remove operations that haven't been updated for a while.
        
        Args:
            max_age_seconds: Maximum age in seconds to keep inactive operations
            
        Returns:
            Number of operations removed
        """
        current_time = time.time()
        to_remove = []
        
        for op_id, data in cls._instances.items():
            if data["status"] in ["completed", "failed"] and (current_time - data["last_update"]) > max_age_seconds:
                to_remove.append(op_id)
        
        for op_id in to_remove:
            del cls._instances[op_id]
        
        return len(to_remove)
    
    def __init__(self, operation_id: str):
        """
        Initialize a progress tracker for a specific operation.
        
        Args:
            operation_id: Unique identifier for the operation
        """
        self.operation_id = operation_id
    
    def update(self, progress: float, message: str, current_step: str = "", status: str = "active") -> None:
        """
        Update the progress of the operation.
        
        Args:
            progress: Progress percentage (0-100)
            message: Current progress message
            current_step: Name of the current step
            status: Operation status ("initializing", "active", "completed", "failed")
        """
        if self.operation_id not in self._instances:
            return
        
        # Ensure progress is within bounds
        progress = max(0, min(100, progress))
        
        # Update the progress information
        self._instances[self.operation_id].update({
            "status": status,
            "message": message,
            "progress": progress,
            "current_step": current_step,
            "last_update": time.time()
        })
        
        # Add to completed steps if moving to a new step
        if current_step and current_step != self._instances[self.operation_id].get("current_step"):
            previous_step = self._instances[self.operation_id].get("current_step")
            if previous_step and previous_step not in self._instances[self.operation_id]["steps_completed"]:
                self._instances[self.operation_id]["steps_completed"].append(previous_step)
        
        # Update estimated time remaining based on progress if possible
        if progress > 0:
            elapsed_time = time.time() - self._instances[self.operation_id]["start_time"]
            estimated_total = elapsed_time / (progress / 100)
            remaining = estimated_total - elapsed_time
            self._instances[self.operation_id]["estimated_time_remaining"] = max(0, round(remaining, 1))
    
    def complete(self, message: str = "Operation completed successfully") -> None:
        """
        Mark the operation as completed.
        
        Args:
            message: Completion message
        """
        if self.operation_id not in self._instances:
            return
        
        self._instances[self.operation_id].update({
            "status": "completed",
            "message": message,
            "progress": 100,
            "current_step": "completed",
            "last_update": time.time(),
            "estimated_time_remaining": 0
        })
    
    def fail(self, message: str = "Operation failed") -> None:
        """
        Mark the operation as failed.
        
        Args:
            message: Failure message
        """
        if self.operation_id not in self._instances:
            return
        
        self._instances[self.operation_id].update({
            "status": "failed",
            "message": message,
            "last_update": time.time()
        })
    
    def to_json(self) -> str:
        """
        Convert the current progress to JSON.
        
        Returns:
            JSON string of progress data
        """
        return json.dumps(self.get_progress(self.operation_id))