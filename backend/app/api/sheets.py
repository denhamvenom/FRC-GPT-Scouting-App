# backend/app/api/sheets.py (update existing file)

from fastapi import APIRouter, Query
from app.services.sheets_service import get_sheet_values

router = APIRouter()

@router.get("/headers")
async def get_headers(tab: str = Query(..., description="Sheet tab name")):
    """
    Get headers from a specific tab in the Google Sheet.
    """
    try:
        data = await get_sheet_values(f"{tab}!A1:Z1")
        headers = data[0] if data and len(data) > 0 else []
        
        return {
            "status": "success",
            "tab": tab,
            "headers": headers
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }