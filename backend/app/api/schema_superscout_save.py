# backend/app/api/schema_superscout_save.py

import os
import json
from fastapi import APIRouter, Request

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

@router.post("/save", tags=["SuperSchema"])
async def save_superscout_schema(request: Request):
    payload = await request.json()
    mapping = payload.get("mapping", {})
    offsets = payload.get("offsets", {})

    os.makedirs(DATA_DIR, exist_ok=True)

    # Save mapping
    mapping_path = os.path.join(DATA_DIR, "schema_superscout_2025.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

    # Save offsets
    offsets_path = os.path.join(DATA_DIR, "schema_superscout_offsets_2025.json")
    with open(offsets_path, "w", encoding="utf-8") as f:
        json.dump(offsets, f, indent=2)

    # Validate mapping vs offsets
    mapping_headers = set(mapping.keys())
    offset_headers = set()
    for group in offsets.values():
        offset_headers.update(group)

    missing_in_offsets = mapping_headers - offset_headers
    extra_in_offsets = offset_headers - mapping_headers

    if missing_in_offsets:
        print("⚠️ Warning: The following headers are mapped but missing from robot offset groups:")
        for header in missing_in_offsets:
            print(f" - {header}")

    if extra_in_offsets:
        print("⚠️ Warning: The following headers appear in robot offsets but are not mapped to tags:")
        for header in extra_in_offsets:
            print(f" - {header}")

    if not missing_in_offsets and not extra_in_offsets:
        print("✅ Schema and offset groups are consistent.")

    return {"status": "success"}
