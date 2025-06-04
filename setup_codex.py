import os
import subprocess
import sys

# Install production and dev dependencies
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"], check=True)

# Add backend to path
sys.path.append(os.path.abspath("backend"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Test Google Sheets service
from app.services.sheets_service import get_sheets_service

try:
    sheets = get_sheets_service()
    print("✅ Google Sheets API initialized successfully.")
except Exception as e:
    print("❌ Failed to initialize Google Sheets API:", e)
