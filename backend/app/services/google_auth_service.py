# backend/app/services/google_auth_service.py

from typing import Optional
import os
import logging
import base64
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from functools import lru_cache

logger = logging.getLogger("google_auth_service")

load_dotenv()

class GoogleAuthService:
    """Handles Google authentication and service account management."""
    
    def __init__(self):
        self.service_account_file_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    
    def resolve_service_account_path(self, path: Optional[str]) -> Optional[str]:
        """Safely resolve a service account file path."""
        if not path:
            return None
        # If the path exists as-is, use it
        if os.path.exists(path):
            return path

        # If path starts with /app/, try to substitute with the project root
        if path.startswith("/app/"):
            # Get the project root (assuming we're in backend/app/services)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # Replace /app/ with the project root
            relative_path = path.replace("/app/", "", 1)
            windows_path = os.path.join(project_root, relative_path)

            if os.path.exists(windows_path):
                return windows_path

        # Try a direct relative path from project root as a fallback
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        fallback_path = os.path.join(project_root, "secrets", "google-service-account.json")

        if os.path.exists(fallback_path):
            logger.info(f"Found service account file at fallback path: {fallback_path}")
            return fallback_path

        # If we get here, we couldn't find the file
        available_dirs = os.listdir(project_root)
        logger.warning(f"Available directories at project root: {available_dirs}")

        # Check if secrets dir exists
        secrets_dir = os.path.join(project_root, "secrets")
        if os.path.exists(secrets_dir):
            logger.warning(f"Secrets directory exists. Contents: {os.listdir(secrets_dir)}")

        # Let the original error happen
        return path
    
    @lru_cache(maxsize=1)
    def get_credentials(self):
        """Get Google service account credentials with caching."""
        part1 = os.getenv("B64_PART_1")
        part2 = os.getenv("B64_PART_2")

        if part1 and part2:
            try:
                joined = part1 + part2
                json_bytes = base64.b64decode(joined)
                service_account_info = json.loads(json_bytes)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.scopes
                )
                logger.info("Loaded service account credentials from split base64 env variables.")
                return credentials
            except Exception as e:
                logger.exception("Failed to decode or parse split base64 credentials.")
                raise
        elif self.service_account_file_env:
            service_account_file = self.resolve_service_account_path(self.service_account_file_env)
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=self.scopes
            )
            logger.info(f"Loaded service account credentials from file: {service_account_file}")
            return credentials
        else:
            raise RuntimeError("No valid Google service account credentials found.")
    
    @lru_cache(maxsize=1)
    def get_sheets_service(self):
        """Create and cache the Google Sheets service."""
        credentials = self.get_credentials()
        return build("sheets", "v4", credentials=credentials)