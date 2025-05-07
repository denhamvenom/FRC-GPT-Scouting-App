from fastapi import APIRouter
import os
import json
from app.services.schema_superscout_service import map_superscout_headers
from app.services.sheets_service import get_sheet_values
from app.services.unified_event_data_service import build_unified_dataset

router = APIRouter(prefix="/api/test", tags=["Testing"])

@router.get("/enhanced-schema")
async def test_enhanced_schema():
    """
    Test endpoint for verifying enhanced schema mapping with data content analysis.
    """
    # Fetch headers and sample data
    headers_data = await get_sheet_values('SuperScouting!A1:Z1')
    headers = headers_data[0] if headers_data else []
    
    sample_data = await get_sheet_values('SuperScouting!A2:Z6')
    
    # Run enhanced schema mapping
    mapping, offsets, insights = await map_superscout_headers(headers, sample_data)
    
    # Save the results for inspection
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Save mapping
    mapping_path = os.path.join(data_dir, "schema_superscout_2025.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    
    # Save offsets
    offsets_path = os.path.join(data_dir, "schema_superscout_offsets_2025.json")
    with open(offsets_path, "w", encoding="utf-8") as f:
        json.dump(offsets, f, indent=2)
    
    # Save insights
    insights_path = os.path.join(data_dir, "schema_superscout_insights_2025.json")
    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2)
    
    # Rebuild unified dataset with enhanced schema
    unified_path = await build_unified_dataset(
        event_key="2025arc",
        year=2025,
        force_rebuild=True
    )
    
    # Get sample of superscouting data from unified dataset
    with open(unified_path, "r", encoding="utf-8") as f:
        unified_data = json.load(f)
    
    # Find a team with superscouting data
    superscout_examples = []
    for team_num, team_data in unified_data.get("teams", {}).items():
        superscout_data = team_data.get("superscouting_data", [])
        if superscout_data:
            superscout_examples.append({
                "team_number": team_num,
                "superscout_data": superscout_data[0]  # Include first entry
            })
            if len(superscout_examples) >= 3:  # Get up to 3 examples
                break
    
    return {
        "status": "success",
        "mapping": mapping,
        "offsets": offsets,
        "insights": insights,
        "unified_dataset_path": unified_path,
        "superscout_examples": superscout_examples
    }