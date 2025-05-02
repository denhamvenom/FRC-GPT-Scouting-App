# backend/app/api/setup.py

from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from app.services.learning_setup_service import start_learning_setup

router = APIRouter(prefix="/api/setup", tags=["Setup"])

@router.post("/start")
async def start_setup(
    year: int = Form(...),
    manual_url: Optional[str] = Form(None),
    manual_file: Optional[UploadFile] = File(None)
):
    """
    Starts the learning setup process.
    """
    result = await start_learning_setup(year, manual_url, manual_file)
    return result
