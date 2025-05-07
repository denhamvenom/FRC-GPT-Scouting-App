# backend/app/api/schema_superscout.py

import os
import json
from fastapi import APIRouter
from app.services.sheets_service import get_sheet_values
from app.services.schema_superscout_service import map_superscout_headers

# Determine project structure paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

router = APIRouter()

@router.get("/learn", tags=["SuperSchema"])
async def learn_superscout_schema():
    # Get headers (first row)
    sheet_data = await get_sheet_values("SuperScouting!A1:Z1")
    headers = sheet_data[0] if sheet_data else []
    if not headers:
        return {"status": "error", "message": "No headers found in SuperScouting tab"}
    
    # Get sample data (next few rows) to provide context about what the fields actually contain
    sample_data = await get_sheet_values("SuperScouting!A2:Z6")  # Get 5 rows of sample data
    
    # Pass both headers and sample data to the mapping function for better context
    mapping, offsets, insights = await map_superscout_headers(headers, sample_data)
    
    # Save mapping and offsets
    try:
        # Save mapping
        mapping_path = os.path.join(DATA_DIR, "schema_superscout_2025.json")
        os.makedirs(os.path.dirname(mapping_path), exist_ok=True)
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)
        
        # Save offsets
        offsets_path = os.path.join(DATA_DIR, "schema_superscout_offsets_2025.json")
        with open(offsets_path, "w", encoding="utf-8") as f:
            json.dump(offsets, f, indent=2)
            
        # Also save insights about data content
        insights_path = os.path.join(DATA_DIR, "schema_superscout_insights_2025.json")
        with open(insights_path, "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2)
    except Exception as e:
        print(f"Error saving schema files: {e}")
    
    return {
        "status": "success",
        "headers": headers,
        "mapping": mapping,
        "offsets": offsets,
        "insights": insights,
        "sample_analyzed": True if sample_data else False
    }
