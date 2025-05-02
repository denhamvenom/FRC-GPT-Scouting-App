# backend/app/api/schema.py

from fastapi import APIRouter
from app.services.sheets_service import get_sheet_values
from app.services.schema_service import map_headers_to_tags, extract_game_tags_from_manual
from app.services.global_cache import cache

router = APIRouter()

@router.get("/learn", tags=["Schema"])
async def learn_schema():
    """
    Read the scouting spreadsheet headers and map them to Reefscape tags using GPT.
    """
    try:
        # Fetch the first row (headers) from the Scouting tab
        sheet_data = await get_sheet_values("Scouting!A1:Z1")
        headers = sheet_data[0] if sheet_data else []

        if not headers:
            return {"status": "error", "message": "No headers found in sheet."}

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
                "team_number", "match_number", "alliance_color", "auto_score", 
                "teleop_score", "endgame_score", "total_score", "comments",
                "starting_position", "driver_skill", "defense_rating"
            ]
        
        # Map headers to the scouting variables
        mapping = await map_headers_to_tags(headers, scouting_vars)
        
        return {
            "status": "success",
            "headers": headers,
            "mapping": mapping
        }

    except Exception as e:
        import traceback
        print(f"Error in learn_schema: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}