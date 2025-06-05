# backend/app/api/schema.py

import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.sheets_service import get_sheet_values, get_sheet_headers
from app.services.schema_service import map_headers_to_tags, extract_game_tags_from_manual
from app.services.global_cache import cache
from app.database.db import get_db

router = APIRouter()


@router.get("/learn", tags=["Schema"])
async def learn_schema(db: Session = Depends(get_db)):
    """
    Read the scouting spreadsheet headers and map them to Reefscape tags using GPT.
    Handles match scouting, pit scouting, and super scouting.
    """
    try:
        # Load field selections
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")

        # Get the field selections for the current year (default to 2025)
        year = cache.get("manual_year", 2025)
        selections_path = os.path.join(data_dir, f"field_selections_{year}.json")

        if not os.path.exists(selections_path):
            return {
                "status": "error",
                "message": "Field selections not found. Please configure fields first.",
            }

        with open(selections_path, "r", encoding="utf-8") as f:
            selections = json.load(f)

        # Get field selections
        field_selections = selections.get("field_selections", {})

        if not field_selections:
            return {"status": "error", "message": "No field selections found in saved data."}

        # Get critical mappings
        critical_mappings = selections.get(
            "critical_mappings", {"team_number": [], "match_number": []}
        )

        # Get robot groups for superscouting
        robot_groups = selections.get("robot_groups", {})

        # Fetch sheet headers for all scouting types
        match_headers = get_sheet_headers("Scouting")
        pit_headers = get_sheet_headers("PitScouting", log_errors=False) or []
        super_headers = get_sheet_headers("SuperScouting", log_errors=False) or []

        # Generate mappings for all tabs
        mappings = {}

        # Get game analysis from cache if available
        game_analysis = cache.get("game_analysis", {})

        # Extract scouting variables from game analysis
        scouting_vars = []
        if game_analysis and "scouting_variables" in game_analysis:
            for category_vars in game_analysis.get("scouting_variables", {}).values():
                scouting_vars.extend(category_vars)

        # If no variables from game analysis, use default tags
        if not scouting_vars:
            # Use standard FRC variables as a fallback
            scouting_vars = [
                "team_number",
                "match_number",
                "alliance_color",
                "auto_score",
                "teleop_score",
                "endgame_score",
                "total_score",
                "comments",
                "starting_position",
                "driver_skill",
                "defense_rating",
            ]

        # Add our custom categories to the mapping options
        for category, headers in {
            "team_info": ["team_info", "alliance", "color", "position"],
            "auto": ["auto", "autonomous"],
            "teleop": ["teleop", "driver"],
            "endgame": ["endgame", "climb", "park"],
            "strategy": ["strategy", "defense", "skill"],
            "other": ["other"],
        }.items():
            scouting_vars.extend([f"{category}_{i}" for i in range(1, 4)])

        # Add pit scouting specific tags
        pit_vars = scouting_vars + [
            "pit_drivetrain",
            "pit_motors",
            "pit_weight",
            "pit_height",
            "pit_notes",
            "pit_design",
            "pit_programming_language",
        ]

        # Process each scouting tab if present

        # 1. Match Scouting
        if match_headers:
            # Get relevant headers (that aren't ignored)
            relevant_headers = [
                h
                for h in match_headers
                if h in field_selections and field_selections[h] != "ignore"
            ]
            # Map headers to variables
            if relevant_headers:
                match_mapping = await map_headers_to_tags(relevant_headers, scouting_vars)
                mappings["match"] = match_mapping

        # 2. Pit Scouting
        if pit_headers:
            # Get relevant headers (that aren't ignored)
            relevant_headers = [
                h for h in pit_headers if h in field_selections and field_selections[h] != "ignore"
            ]
            # Map headers to variables
            if relevant_headers:
                pit_mapping = await map_headers_to_tags(relevant_headers, pit_vars)
                mappings["pit"] = pit_mapping

        # 3. Super Scouting
        if super_headers and robot_groups:
            # Handle each robot group separately
            super_mapping = {}

            for group, headers in robot_groups.items():
                # Get relevant headers (that aren't ignored)
                relevant_headers = [
                    h for h in headers if h in field_selections and field_selections[h] != "ignore"
                ]
                # Map headers to variables
                if relevant_headers:
                    group_mapping = await map_headers_to_tags(relevant_headers, scouting_vars)
                    super_mapping[group] = group_mapping

            if super_mapping:
                mappings["super"] = super_mapping

        # Store the combined schema
        schema_path = os.path.join(data_dir, f"schema_{year}.json")
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mappings": mappings,
                    "critical_fields": critical_mappings,
                    "robot_groups": robot_groups,
                    "year": year,
                },
                f,
                indent=2,
            )

        return {
            "status": "success",
            "schema_path": schema_path,
            "mappings": mappings,
            "critical_fields": critical_mappings,
        }

    except Exception as e:
        import traceback

        print(f"Error in learn_schema: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}
