# backend/app/services/sheets_service.py

from typing import Any
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# ENV Vars
SERVICE_ACCOUNT_FILE_ENV = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Path resolution logic to handle both Windows and Linux/Docker paths
def resolve_service_account_path(path: str) -> str:
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
        print(f"Found service account file at fallback path: {fallback_path}")
        return fallback_path
    
    # If we get here, we couldn't find the file
    available_dirs = os.listdir(project_root)
    print(f"Available directories at project root: {available_dirs}")
    
    # Check if secrets dir exists
    secrets_dir = os.path.join(project_root, "secrets")
    if os.path.exists(secrets_dir):
        print(f"Secrets directory exists. Contents: {os.listdir(secrets_dir)}")
    
    # Let the original error happen
    return path

# Resolve the service account file path
SERVICE_ACCOUNT_FILE = resolve_service_account_path(SERVICE_ACCOUNT_FILE_ENV)
print(f"Using service account file: {SERVICE_ACCOUNT_FILE}")

# Setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheets_service = build("sheets", "v4", credentials=credentials)

async def get_sheet_values(range_name: str) -> list[list[Any]]:
    """Read data from a Google Sheet."""
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    values = result.get("values", [])
    return values

async def update_sheet_values(range_name: str, values: list[list[Any]]) -> dict[str, Any]:
    """Write data to a Google Sheet."""
    body = {"values": values}
    sheet = sheets_service.spreadsheets()
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body,
    ).execute()
    return result