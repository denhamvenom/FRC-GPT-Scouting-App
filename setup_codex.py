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

missing_creds = not (
    os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    or (os.getenv("B64_PART_1") and os.getenv("B64_PART_2"))
)

if missing_creds:
    print(
        "⚠️  Google service account credentials not found. "
        "Set GOOGLE_SERVICE_ACCOUNT_FILE or B64_PART_1 and B64_PART_2 in your .env"
    )
else:
    # Test Google Sheets service only if credentials are available
    from app.services.sheets_service import get_sheets_service

    try:
        sheets = get_sheets_service()
        print("✅ Google Sheets API initialized successfully.")
    except Exception as e:
        print("❌ Failed to initialize Google Sheets API:", e)
