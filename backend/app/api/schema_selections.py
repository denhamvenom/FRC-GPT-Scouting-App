# backend/app/api/schema_selections.py

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter()

class FieldSelections(BaseModel):
    field_selections: Dict[str, str]
    manual_url: Optional[str] = None
    year: int

@router.post("/save-selections")
async def save_field_selections(selections: FieldSelections):
    """
    Save field selections and game information.
    """
    try:
        # Ensure data directory exists
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Save selections to file
        selections_path = os.path.join(data_dir, f"field_selections_{selections.year}.json")
        
        with open(selections_path, "w", encoding="utf-8") as f:
            json.dump(selections.dict(), f, indent=2)
            
        # If manual URL is provided, save it to cache
        if selections.manual_url:
            from app.services.global_cache import cache
            cache["manual_url"] = selections.manual_url
            cache["manual_year"] = selections.year
            
        return {
            "status": "success",
            "message": "Field selections saved successfully",
            "path": selections_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))