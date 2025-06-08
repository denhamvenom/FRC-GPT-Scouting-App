"""
Progress reporter for picklist generation.
"""

import logging
from typing import Any, Dict, Optional

from app.services.progress_tracker import ProgressTracker

from ..interfaces import ProgressReporter

logger = logging.getLogger(__name__)


class PicklistProgressReporter(ProgressReporter):
    """Progress reporter implementation using the global progress tracker."""

    def __init__(self, operation_id: str):
        """
        Initialize progress reporter.

        Args:
            operation_id: Unique identifier for the operation
        """
        self.operation_id = operation_id
        self.tracker = ProgressTracker.create_tracker(operation_id)

    def update(
        self,
        progress: int,
        message: str,
        current_step: Optional[str] = None,
        status: str = "active",
    ) -> None:
        """Update progress."""
        self.tracker.update(
            progress=progress,
            message=message,
            current_step=current_step,
            status=status,
        )
        logger.debug(f"Progress [{self.operation_id}]: {progress}% - {message}")

    def complete(self, message: str) -> None:
        """Mark operation as complete."""
        self.tracker.update(
            progress=100,
            message=message,
            status="completed",
        )
        logger.info(f"Operation completed [{self.operation_id}]: {message}")

    def error(self, message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark operation as failed."""
        current_progress = ProgressTracker.get_progress(self.operation_id)
        progress = current_progress.get("progress", 0) if current_progress else 0
        self.tracker.update(
            progress=progress,
            message=f"Error: {message}",
            status="failed",
        )
        logger.error(f"Operation failed [{self.operation_id}]: {message}")
        if error_details:
            logger.error(f"Error details: {error_details}")

    def update_batch_progress(
        self, current_batch: int, total_batches: int, message: str
    ) -> None:
        """Update progress for batch processing."""
        progress = int((current_batch / total_batches) * 100)
        self.update(
            progress=progress,
            message=message,
            current_step=f"Batch {current_batch}/{total_batches}",
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current progress status."""
        return ProgressTracker.get_progress(self.operation_id) or {}

    @staticmethod
    def get_tracker_status(operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status for any operation ID."""
        return ProgressTracker.get_progress(operation_id)