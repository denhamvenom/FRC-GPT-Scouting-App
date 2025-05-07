from fastapi import APIRouter
import os
import json
from app.services.unified_event_data_service import build_unified_dataset

router = APIRouter(prefix="/api/test", tags=["Testing"])

@router.get("/rebuild-dataset")
async def rebuild_dataset():
    """
    Rebuild the unified dataset using the enhanced superscout parser
    that preserves field categories.
    """
    # Force rebuild with enhanced parser
    unified_path = await build_unified_dataset(
        event_key="2025arc",
        year=2025,
        force_rebuild=True
    )
    
    # Read a sample from the rebuilt dataset
    with open(unified_path, "r", encoding="utf-8") as f:
        unified_data = json.load(f)
    
    # Check for a team with superscouting data
    superscout_examples = []
    for team_num, team_data in unified_data.get("teams", {}).items():
        superscout_data = team_data.get("superscouting_data", [])
        if superscout_data:
            # Extract just the first entry for each team
            example = {
                "team_number": team_num,
                "superscout_data": superscout_data[0]
            }
            superscout_examples.append(example)
            if len(superscout_examples) >= 3:  # Limit to 3 examples
                break
    
    return {
        "status": "success",
        "message": f"Unified dataset rebuilt at: {unified_path}",
        "superscout_examples": superscout_examples
    }