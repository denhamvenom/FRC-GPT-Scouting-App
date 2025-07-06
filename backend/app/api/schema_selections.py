# backend/app/api/schema_selections.py

import os
import json
import re
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
    label_mappings: Optional[Dict[str, Any]] = None


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

        # Auto-generate robot groups for superscouting fields if not provided
        if not selections.robot_groups:
            selections.robot_groups = generate_auto_robot_groups_for_save(selections.field_selections)

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
                category_mapping[header] = {"category": category, "source": source}

                # Add label mapping if available
                if selections.label_mappings and header in selections.label_mappings:
                    category_mapping[header]["label_mapping"] = selections.label_mappings[header]
                    print(f"✅ Added label mapping for header: '{header}' -> {selections.label_mappings[header]}")
                elif selections.label_mappings:
                    print(f"❌ No label mapping found for header: '{header}'")

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
            "path": selections_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load-selections/{year}")
async def load_field_selections(year: int = 2025):
    """
    Load field selections including label mappings for a given year.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        
        # Load the main field selections
        selections_path = os.path.join(data_dir, f"field_selections_{year}.json")
        if not os.path.exists(selections_path):
            return {
                "status": "not_found",
                "message": f"No field selections found for year {year}"
            }
            
        with open(selections_path, "r", encoding="utf-8") as f:
            selections_data = json.load(f)
        
        # Load field metadata (which includes label mappings)
        metadata_path = os.path.join(data_dir, f"field_metadata_{year}.json")
        label_mappings = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Extract label mappings from metadata
            for header, field_info in metadata.items():
                if isinstance(field_info, dict) and "label_mapping" in field_info:
                    label_mappings[header] = field_info["label_mapping"]
        
        return {
            "status": "success",
            "year": year,
            "field_selections": selections_data.get("field_selections", {}),
            "critical_mappings": selections_data.get("critical_mappings", {}),
            "robot_groups": selections_data.get("robot_groups", {}),
            "label_mappings": label_mappings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading field selections: {str(e)}")


def generate_auto_robot_groups_for_save(field_selections: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Auto-generate robot groups for superscouting fields.
    
    Args:
        field_selections: Dictionary of field selections from the frontend
        
    Returns:
        Dictionary mapping robot labels to their field lists
    """
    # Get superscouting headers
    try:
        from app.services.sheets_service import get_sheet_headers
        super_headers = get_sheet_headers("SuperScouting", log_errors=False) or []
    except Exception:
        # Fallback: get superscouting fields from field_selections
        super_headers = [header for header, category in field_selections.items() 
                        if category != "ignore"]
    
    # Filter to only include superscouting fields that are not ignored
    active_super_headers = [header for header in super_headers 
                           if header in field_selections and field_selections[header] != "ignore"]
    
    auto_groups = {
        "robot_1": [],
        "robot_2": [],
        "robot_3": []
    }
    
    # Try to detect existing robot patterns first
    robot_patterns = [
        [re.compile(r'robot\s*1|r1\b', re.IGNORECASE), re.compile(r'robot\s*2|r2\b', re.IGNORECASE), re.compile(r'robot\s*3|r3\b', re.IGNORECASE)],
        [re.compile(r'\b1\s*[-_]'), re.compile(r'\b2\s*[-_]'), re.compile(r'\b3\s*[-_]')],
        [re.compile(r'_1_'), re.compile(r'_2_'), re.compile(r'_3_')],
        [re.compile(r'\b1\b'), re.compile(r'\b2\b'), re.compile(r'\b3\b')]  # More general pattern
    ]
    
    pattern_found = False
    for pattern_set in robot_patterns:
        r1_headers = [h for h in active_super_headers if pattern_set[0].search(h)]
        r2_headers = [h for h in active_super_headers if pattern_set[1].search(h)]
        r3_headers = [h for h in active_super_headers if pattern_set[2].search(h)]
        
        # If we found substantial matches for at least two robots, use this pattern
        if len(r1_headers) > 0 and len(r2_headers) > 0:
            auto_groups["robot_1"] = r1_headers
            auto_groups["robot_2"] = r2_headers
            auto_groups["robot_3"] = r3_headers
            pattern_found = True
            print(f"Auto-detected robot pattern for save: R1={len(r1_headers)}, R2={len(r2_headers)}, R3={len(r3_headers)} fields")
            break
    
    # If no patterns found, assign ALL active superscouting fields to ALL robots
    if not pattern_found:
        print(f"No robot patterns detected for save. Assigning all {len(active_super_headers)} active superscouting fields to all 3 robots.")
        for robot_label in auto_groups.keys():
            auto_groups[robot_label] = active_super_headers.copy()
    
    return auto_groups
