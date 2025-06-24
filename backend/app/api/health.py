# backend/app/api/health.py

from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
