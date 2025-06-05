# File: backend/app/api/prompt_builder_router.py

from fastapi import APIRouter, HTTPException, Query
from app.services.sheets_service import get_sheet_values
from app.services.schema_service import (
    extract_game_tags_from_manual,
    map_headers_to_tags,
    extract_sheet_id,
)
from app.services.global_cache import cache

router = APIRouter()


@router.post("/prompt-builder", tags=["Prompt Builder"])
async def build_prompt(sheet_url: str = Query(..., description="Google Sheet link or ID")):
    """
    Builds the initial Prompt Builder map from the uploaded manual and scouting sheet.
    """
    # Check if manual text is cached
    manual_text = cache.get("manual_text")
    if not manual_text:
        raise HTTPException(
            status_code=400,
            detail="Manual file not found in system. Please upload manual first via learning setup.",
        )

    # Extract sheet ID from URL or plain ID
    sheet_id = extract_sheet_id(sheet_url)

    # Read headers from the scouting sheet (first row, broad column range)
    try:
        scouting_data = await get_sheet_values("Scouting!A1:Z1", spreadsheet_id=sheet_id)
        if not scouting_data or not scouting_data[0]:
            raise ValueError("No headers found.")
        headers = scouting_data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading Google Sheet headers: {str(e)}")

    # Extract game tags from manual
    game_tags = await extract_game_tags_from_manual(manual_text)

    # Map headers to tags
    header_mapping = await map_headers_to_tags(headers, game_tags)

    return {
        "status": "success",
        "sheet_id": sheet_id,
        "headers": headers,
        "extracted_game_tags": game_tags,
        "header_mapping": header_mapping,
    }


@router.get("/prompt-builder/variables", tags=["Prompt Builder"])
async def get_suggested_variables():
    """
    Get suggested scouting variables based on the game manual analysis.
    """
    game_analysis = cache.get("game_analysis")

    if not game_analysis:
        return {
            "status": "error",
            "message": "No game analysis found. Please upload a game manual first.",
        }

    # Extract scouting variables from game analysis
    scouting_vars = []
    for category, variables in game_analysis.get("scouting_variables", {}).items():
        scouting_vars.extend(variables)

    # Add standard variables that should be present for any game
    standard_vars = [
        "team_number",
        "match_number",
        "alliance_color",
        "match_key",
        "starting_position",
        "no_show",
        "driver_station",
        "comments",
    ]
    scouting_vars.extend(standard_vars)

    # Remove duplicates and sort
    scouting_vars = sorted(list(set(scouting_vars)))

    return {"status": "success", "suggested_variables": scouting_vars}
