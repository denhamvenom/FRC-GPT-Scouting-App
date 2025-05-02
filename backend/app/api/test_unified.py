# backend/app/api/test_unified.py

from fastapi import APIRouter
from app.services.unified_event_data_service import build_unified_dataset

router = APIRouter()

@router.get("/api/test/unified")
async def test_unified():
    try:
        await build_unified_dataset(event_key="2025arc", year=2025)
        return {"status": "success", "message": "Unified dataset built successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
