# backend/app/services/logging_config.py

import os
import logging
import datetime


def setup_logging():
    """
    Configure logging for the application
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    # Create a timestamped log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"archive_service_{timestamp}.log")

    # Configure the root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],  # Also log to console
    )

    # Configure specific loggers
    logging.getLogger("archive_service").setLevel(logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reduce SQL logging

    # Log the start of the application
    logging.info(f"=== Logging initialized, writing to {log_file} ===")

    return log_file
