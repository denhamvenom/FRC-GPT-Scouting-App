# backend/app/api/sheets.py (update existing file)

from fastapi import APIRouter, Query
from app.services.sheets_service import get_sheet_values

router = APIRouter()

# Note: The /headers endpoint has been moved to sheets_headers.py
# with support for spreadsheet_id parameter
