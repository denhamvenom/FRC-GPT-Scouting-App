# backend/app/api/schema_save.py

import os
import json
from fastapi import APIRouter, Request

router = APIRouter()

# Properly resolve the backend base path dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

@router.post("/save", tags=["Schema"])
async def save_schema(request: Request):
    mapping = await request.json()

    # Ensure the data/ directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Save schema file into backend/data/schema_2025.json
    schema_path = os.path.join(DATA_DIR, "schema_2025.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

    return {"status": "success"}
