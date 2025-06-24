from fastapi import APIRouter, HTTPException
import os
import logging
from typing import List, Dict, Any, Optional

router = APIRouter()


@router.get("/logs/picklist", response_model=Dict[str, Any])
async def get_picklist_logs(lines: int = 100):
    """
    Get the recent logs from the picklist generator.
    This is a debugging endpoint to help understand the GPT process.

    Args:
        lines: Number of recent log lines to return (default: 100)
    """
    try:
        log_file_path = "picklist_generator.log"

        if not os.path.exists(log_file_path):
            return {
                "status": "error",
                "message": "Log file does not exist yet. Generate a picklist first.",
            }

        # Use tail -n approach for efficiency with large log files
        with open(log_file_path, "r") as f:
            # Read the whole file if smaller than the requested lines
            log_lines = f.readlines()

            # Get the last 'lines' number of entries
            recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines

            # Clean up newlines
            recent_logs = [line.strip() for line in recent_logs]

        return {"status": "success", "log_count": len(recent_logs), "logs": recent_logs}
    except Exception as e:
        logging.error(f"Error reading picklist logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")
