# backend/app/api/sheets_headers.py

from fastapi import APIRouter, HTTPException, Query
from app.services.sheets_service import get_sheet_values

router = APIRouter(prefix="/api/sheets", tags=["Sheets"])

@router.get("/headers")
async def get_sheet_headers(tab: str = Query(..., description="Sheet tab name")):
    """
    Get headers from a specific tab in the Google Sheet.
    
    Args:
        tab: The name of the sheet tab (e.g., "Scouting", "SuperScouting")
        
    Returns:
        Dict with headers array
    """
    try:
        # Fetch first row (headers) from the specified tab
        # Using A1:ZZ1 to get all potential columns
        range_name = f"{tab}!A1:ZZ1"
        result = await get_sheet_values(range_name)
        
        if not result or len(result) == 0:
            return {
                "status": "error",
                "message": f"No headers found in {tab} tab"
            }
        
        # Return the headers (first row)
        headers = result[0]
        
        return {
            "status": "success", 
            "tab": tab,
            "headers": headers,
            "count": len(headers)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching headers from {tab}: {str(e)}"
        ) 