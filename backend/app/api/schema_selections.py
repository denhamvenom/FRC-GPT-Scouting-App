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
    event_key: Optional[str] = None
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
    
    Saves all data in unified format to single field_selections_{storage_key}.json file.
    """
    try:
        # Ensure data directory exists
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        # Auto-generate robot groups for superscouting fields if not provided
        if not selections.robot_groups:
            selections.robot_groups = generate_auto_robot_groups_for_save(selections.field_selections)

        # Determine storage key - use event_key if available, fall back to year
        storage_key = selections.event_key if selections.event_key else str(selections.year)
        
        # Build enhanced field selections structure
        enhanced_field_selections = {}
        
        # Get sheet headers to determine source
        try:
            from app.services.sheets_service import get_sheet_headers
            match_headers = get_sheet_headers("Scouting")
            pit_headers = get_sheet_headers("PitScouting", log_errors=False) or []
            super_headers = get_sheet_headers("SuperScouting", log_errors=False) or []
        except Exception as e:
            print(f"Warning: Could not get sheet headers: {str(e)}")
            match_headers = []
            pit_headers = []
            super_headers = []
        
        # Build enhanced field selections with metadata
        for header, category in selections.field_selections.items():
            # Determine source
            if header in match_headers:
                source = "match"
            elif header in pit_headers:
                source = "pit"
            elif header in super_headers:
                source = "super"
            else:
                source = "unknown"
            
            # Build field info
            field_info = {
                "category": category,
                "source": source
            }
            
            # Add label mapping if available
            if selections.label_mappings and header in selections.label_mappings:
                field_info["label_mapping"] = selections.label_mappings[header]
                print(f"✅ Added label mapping for header: '{header}' -> {selections.label_mappings[header]}")
            
            # Add robot group mapping for superscout fields
            if source == "super" and selections.robot_groups:
                for group, headers in selections.robot_groups.items():
                    if header in headers:
                        field_info["robot_group"] = group
                        break
            
            enhanced_field_selections[header] = field_info
        
        # Build unified data structure
        unified_data = {
            "year": selections.year,
            "event_key": selections.event_key,
            "field_selections": enhanced_field_selections,
            "critical_mappings": selections.critical_mappings.model_dump() if selections.critical_mappings else {},
            "robot_groups": selections.robot_groups,
            "manual_url": selections.manual_url
        }
        
        # Save unified data to single file
        selections_path = os.path.join(data_dir, f"field_selections_{storage_key}.json")
        with open(selections_path, "w", encoding="utf-8") as f:
            json.dump(unified_data, f, indent=2)
        
        print(f"✅ Saved unified field selections to: {selections_path}")
        print(f"✅ Enhanced {len([f for f in enhanced_field_selections.values() if 'label_mapping' in f])} fields with label mappings")

        # If manual URL is provided, save it to cache
        if selections.manual_url:
            from app.services.global_cache import cache
            cache["manual_url"] = selections.manual_url
            cache["manual_year"] = selections.year

        return {
            "status": "success",
            "message": "Field selections saved successfully",
            "path": selections_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load-selections/{storage_key}")
async def load_field_selections(storage_key: str):
    """
    Load field selections including label mappings for a given event or year.
    storage_key can be either an event_key (e.g., "2025txhou1") or year (e.g., "2025")
    
    Supports both new unified format and legacy separate files for backward compatibility.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        
        # Try to load unified field selections file first
        selections_path = os.path.join(data_dir, f"field_selections_{storage_key}.json")
        
        if os.path.exists(selections_path):
            with open(selections_path, "r", encoding="utf-8") as f:
                unified_data = json.load(f)
            
            # Check if this is unified format or legacy format
            field_selections_data = unified_data.get("field_selections", {})
            
            # Extract components for frontend compatibility
            field_selections = {}
            label_mappings = {}
            
            for header, field_info in field_selections_data.items():
                if isinstance(field_info, dict):
                    # New unified format
                    field_selections[header] = field_info.get("category", "ignore")
                    if "label_mapping" in field_info:
                        label_mappings[header] = field_info["label_mapping"]
                else:
                    # Legacy simple format
                    field_selections[header] = field_info
            
            print(f"✅ Loaded unified field selections with {len(field_selections)} fields and {len(label_mappings)} label mappings")
            
            return {
                "status": "success",
                "storage_key": storage_key,
                "year": unified_data.get("year", 2025),
                "event_key": unified_data.get("event_key"),
                "field_selections": field_selections,
                "critical_mappings": unified_data.get("critical_mappings", {}),
                "robot_groups": unified_data.get("robot_groups", {}),
                "label_mappings": label_mappings
            }
        
        # Fallback: Try year-based file for backward compatibility
        if len(storage_key) > 4:  # Event keys are longer than year strings
            year_fallback = storage_key[:4]  # Extract year from event key
            year_fallback_path = os.path.join(data_dir, f"field_selections_{year_fallback}.json")
            if os.path.exists(year_fallback_path):
                print(f"Found year-based fallback for {storage_key}: {year_fallback_path}")
                # Recursively call with year fallback
                return await load_field_selections(year_fallback)
        
        # Last resort: Try to load and merge legacy separate files
        legacy_result = load_and_merge_legacy_files(storage_key, data_dir)
        if legacy_result:
            return legacy_result
        
        return {
            "status": "not_found",
            "message": f"No field selections found for {storage_key}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading field selections: {str(e)}")


def load_and_merge_legacy_files(storage_key: str, data_dir: str) -> Optional[Dict[str, Any]]:
    """
    Load and merge legacy separate field_selections and field_metadata files.
    
    Args:
        storage_key: The storage key to load files for
        data_dir: The data directory path
        
    Returns:
        Merged data in expected format, or None if legacy files don't exist
    """
    try:
        legacy_selections_path = os.path.join(data_dir, f"field_selections_{storage_key}.json")
        legacy_metadata_path = os.path.join(data_dir, f"field_metadata_{storage_key}.json")
        
        # Check if legacy selections file exists
        if not os.path.exists(legacy_selections_path):
            return None
        
        # Load legacy selections file
        with open(legacy_selections_path, "r", encoding="utf-8") as f:
            selections_data = json.load(f)
        
        # Load legacy metadata file if it exists
        label_mappings = {}
        if os.path.exists(legacy_metadata_path):
            with open(legacy_metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Extract label mappings from metadata
            for header, field_info in metadata.items():
                if isinstance(field_info, dict) and "label_mapping" in field_info:
                    label_mappings[header] = field_info["label_mapping"]
        
        print(f"✅ Loaded legacy files: {len(selections_data.get('field_selections', {}))} fields, {len(label_mappings)} label mappings")
        
        return {
            "status": "success",
            "storage_key": storage_key,
            "year": selections_data.get("year", 2025),
            "event_key": selections_data.get("event_key"),
            "field_selections": selections_data.get("field_selections", {}),
            "critical_mappings": selections_data.get("critical_mappings", {}),
            "robot_groups": selections_data.get("robot_groups", {}),
            "label_mappings": label_mappings
        }
        
    except Exception as e:
        print(f"Error loading legacy files: {str(e)}")
        return None


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
