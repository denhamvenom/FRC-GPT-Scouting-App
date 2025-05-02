# backend/app/api/schema_superscout.py

from fastapi import APIRouter
from app.services.sheets_service import get_sheet_values
from app.services.schema_superscout_service import map_superscout_headers

router = APIRouter()

@router.get("/learn", tags=["SuperSchema"])
async def learn_superscout_schema():
    sheet_data = await get_sheet_values("SuperScouting!A1:Z1")
    headers = sheet_data[0] if sheet_data else []
    if not headers:
        return {"status": "error", "message": "No headers found in SuperScouting tab"}
    mapping, offsets = await map_superscout_headers(headers)
    return {
        "status": "success",
        "headers": headers,
        "mapping": mapping,
        "offsets": offsets
    }
