# backend/app/api/field_selection.py

import os
import json
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/schema", tags=["Schema"])

# Properly resolve the backend base path dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@router.post("/save-selections")
async def save_field_selections(request: Request):
    """
    Save field selection mappings, including critical fields and robot groups.

    Expects a JSON payload with:
    - field_selections: Dict mapping headers to categories
    - critical_mappings: Dict identifying team_number and match_number fields
    - robot_groups: Dict organizing headers into robot-specific groups
    - year: Integer year
    - manual_url: Optional string URL to game manual
    """
    try:
        # Parse request body
        data = await request.json()

        field_selections = data.get("field_selections", {})
        critical_mappings = data.get("critical_mappings", {})
        robot_groups = data.get("robot_groups", {})
        year = data.get("year", 2025)
        manual_url = data.get("manual_url", "")

        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)

        # Generate standard schema mappings from field selections
        schema_mappings = {}
        superscout_mappings = {}

        # Split into regular and superscouting mappings
        for header, category in field_selections.items():
            # Skip ignored fields
            if category == "ignore":
                continue

            # Determine if this is a superscouting field based on robot groups
            is_superscout = any(header in group for group in robot_groups.values())

            if is_superscout:
                superscout_mappings[header] = category
            else:
                schema_mappings[header] = category

        # Save schema file (regular scouting)
        schema_path = os.path.join(DATA_DIR, f"schema_{year}.json")
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema_mappings, f, indent=2)

        # Save superscouting schema
        superscout_path = os.path.join(DATA_DIR, f"schema_superscout_{year}.json")
        with open(superscout_path, "w", encoding="utf-8") as f:
            json.dump(superscout_mappings, f, indent=2)

        # Save robot groups configuration
        robot_groups_path = os.path.join(DATA_DIR, f"robot_groups_{year}.json")
        with open(robot_groups_path, "w", encoding="utf-8") as f:
            json.dump(robot_groups, f, indent=2)

        # Save critical field mappings
        critical_path = os.path.join(DATA_DIR, f"critical_mappings_{year}.json")
        with open(critical_path, "w", encoding="utf-8") as f:
            json.dump(critical_mappings, f, indent=2)

        # Save game manual URL if provided
        if manual_url:
            manual_info_path = os.path.join(DATA_DIR, f"manual_info_{year}.json")
            with open(manual_info_path, "w", encoding="utf-8") as f:
                json.dump({"url": manual_url}, f, indent=2)

        # Validate the saved configuration
        validation_results = validate_field_mapping(
            field_selections, critical_mappings, robot_groups
        )

        return {
            "status": "success",
            "files_saved": [
                f"schema_{year}.json",
                f"schema_superscout_{year}.json",
                f"robot_groups_{year}.json",
                f"critical_mappings_{year}.json",
            ],
            "validation": validation_results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving field selections: {str(e)}")


def validate_field_mapping(field_selections, critical_mappings, robot_groups):
    """
    Validates the field mappings for consistency and completeness.
    """
    issues = []
    warnings = []

    # Check if critical fields are mapped
    if not critical_mappings.get("team_number"):
        issues.append("Team Number field is not mapped")

    if not critical_mappings.get("match_number"):
        issues.append("Match Number field is not mapped")

    # Check robot groups for consistency
    all_robot_headers = []
    for group, headers in robot_groups.items():
        all_robot_headers.extend(headers)

    # Check for duplicates across robot groups
    duplicate_headers = []
    seen_headers = set()

    for header in all_robot_headers:
        if header in seen_headers:
            duplicate_headers.append(header)
        else:
            seen_headers.add(header)

    if duplicate_headers:
        warnings.append(
            f"Headers assigned to multiple robot groups: {', '.join(duplicate_headers)}"
        )

    # Check that all robot group headers are actually mapped
    unmapped_headers = []
    for header in all_robot_headers:
        if header not in field_selections or field_selections[header] == "ignore":
            unmapped_headers.append(header)

    if unmapped_headers:
        warnings.append(
            f"Headers in robot groups are marked as 'ignore': {', '.join(unmapped_headers)}"
        )

    return {"issues": issues, "warnings": warnings, "is_valid": len(issues) == 0}


@router.get("/field-selections/{year}")
async def get_field_selections(year: int = 2025):
    """
    Get the current field selection configuration.
    """
    try:
        # Load all configuration files
        schema_path = os.path.join(DATA_DIR, f"schema_{year}.json")
        superscout_path = os.path.join(DATA_DIR, f"schema_superscout_{year}.json")
        robot_groups_path = os.path.join(DATA_DIR, f"robot_groups_{year}.json")
        critical_path = os.path.join(DATA_DIR, f"critical_mappings_{year}.json")
        manual_info_path = os.path.join(DATA_DIR, f"manual_info_{year}.json")

        # Check if the files exist
        if not os.path.exists(schema_path):
            return {
                "status": "not_found",
                "message": f"No field selection configuration found for year {year}",
            }

        # Load schema mappings
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_mappings = json.load(f)

        # Load superscouting schema if it exists
        superscout_mappings = {}
        if os.path.exists(superscout_path):
            with open(superscout_path, "r", encoding="utf-8") as f:
                superscout_mappings = json.load(f)

        # Load robot groups if they exist
        robot_groups = {}
        if os.path.exists(robot_groups_path):
            with open(robot_groups_path, "r", encoding="utf-8") as f:
                robot_groups = json.load(f)

        # Load critical mappings if they exist
        critical_mappings = {}
        if os.path.exists(critical_path):
            with open(critical_path, "r", encoding="utf-8") as f:
                critical_mappings = json.load(f)

        # Load manual info if it exists
        manual_url = ""
        if os.path.exists(manual_info_path):
            with open(manual_info_path, "r", encoding="utf-8") as f:
                manual_info = json.load(f)
                manual_url = manual_info.get("url", "")

        # Combine all mappings into field_selections
        field_selections = {**schema_mappings, **superscout_mappings}

        return {
            "status": "success",
            "year": year,
            "field_selections": field_selections,
            "robot_groups": robot_groups,
            "critical_mappings": critical_mappings,
            "manual_url": manual_url,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading field selections: {str(e)}")
