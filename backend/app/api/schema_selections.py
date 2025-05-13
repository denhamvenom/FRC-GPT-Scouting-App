# backend/app/api/schema_selections.py

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List, Any

router = APIRouter()

class CriticalMappings(BaseModel):
    team_number: List[str]
    match_number: List[str]

class FieldSelections(BaseModel):
    field_selections: Dict[str, str]
    manual_url: Optional[str] = None
    year: int
    critical_mappings: Optional[CriticalMappings] = None
    robot_groups: Optional[Dict[str, List[str]]] = None

@router.post("/save-selections")
async def save_field_selections(selections: FieldSelections):
    """
    Save field selections and game information.

    Handles categorized field mappings for:
    - Match scouting
    - Pit scouting
    - Super scouting with robot groupings
    - Critical field mappings (team/match numbers)
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

        # Generate and save field category mapping for later use
        try:
            category_mapping = {}

            # Check if field source can be inferred from headers - to be used later
            # For instance, detect if fields are from match, pit, or super scouting
            from app.services.sheets_service import get_sheet_headers

            match_headers = get_sheet_headers("Scouting")
            pit_headers = get_sheet_headers("PitScouting", log_errors=False) or []
            super_headers = get_sheet_headers("SuperScouting", log_errors=False) or []

            # Tag each field with its source
            for header, category in selections.field_selections.items():
                if header in match_headers:
                    source = "match"
                elif header in pit_headers:
                    source = "pit"
                elif header in super_headers:
                    source = "super"
                else:
                    source = "unknown"

                # Store both category and source
                category_mapping[header] = {
                    "category": category,
                    "source": source
                }

                # Add robot group mapping for superscout fields
                if source == "super" and selections.robot_groups:
                    for group, headers in selections.robot_groups.items():
                        if header in headers:
                            category_mapping[header]["robot_group"] = group
                            break

            # Save the enhanced field metadata
            metadata_path = os.path.join(data_dir, f"field_metadata_{selections.year}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(category_mapping, f, indent=2)

        except Exception as e:
            # Non-critical error, log but continue
            print(f"Warning: Could not generate field category mapping: {str(e)}")

        return {
            "status": "success",
            "message": "Field selections saved successfully",
            "path": selections_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))