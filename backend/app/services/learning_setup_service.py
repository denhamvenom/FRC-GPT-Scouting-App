# backend/app/services/learning_setup_service.py

import random
from typing import Optional, Dict, Any, List
from fastapi import UploadFile

from app.services.statbotics_client import get_team_epa
from app.services.tba_client import get_event_teams
from app.services.manual_parser_service import extract_manual_text, analyze_game_manual_in_chunks, analyze_game_overview
from app.services.global_cache import cache

async def start_learning_setup(year: int, manual_url: Optional[str] = None, manual_file: Optional[UploadFile] = None) -> Dict[str, Any]:
    """
    Pulls sample teams, processes the game manual, and prepares GPT variable discovery.
    
    Args:
        year: FRC season year
        manual_url: Optional URL to game manual PDF
        manual_file: Optional uploaded game manual PDF
        
    Returns:
        Dict containing setup information and analysis
    """
    # For now, use sample event for pulling teams (can be dynamic later)
    sample_event_key = f"{year}arc"  # Default event key pattern
    
    # 1. Pull sample teams from TBA
    event_teams = await get_event_teams(sample_event_key)
    team_keys = [team["key"].replace("frc", "") for team in event_teams]

    # 2. Randomly sample 3 teams and get their EPA data
    sample_team_keys = random.sample(team_keys, min(3, len(team_keys)))
    slimmed_team_data = []
    
    for team_key in sample_team_keys:
        team_epa = get_team_epa(int(team_key), year)
        if team_epa:
            slimmed_team_data.append(team_epa)

    # 3. Process manual if provided
    manual_info = {"manual_file_received": manual_file is not None, "manual_url": manual_url}
    game_analysis = None
    
    # Cache the year for reference
    cache["manual_year"] = year
    
    if manual_file or manual_url:
        # Try to process the full manual
        try:
            manual_text = await extract_manual_text(manual_file, manual_url)
            
            if manual_text:
                # Cache the manual text
                cache["manual_text"] = manual_text
                manual_info["text_length"] = len(manual_text)
                
                # Analyze the manual with GPT in chunks to avoid rate limits
                game_analysis = await analyze_game_manual_in_chunks(manual_text, year)
                manual_info["analysis_complete"] = game_analysis is not None
        except Exception as e:
            print(f"Error processing manual: {e}")
            # Fall back to basic analysis without manual
            game_analysis = await analyze_game_overview(year)
            manual_info["analysis_error"] = str(e)
    else:
        # If no manual provided, do a basic analysis
        game_analysis = await analyze_game_overview(year)
        manual_info["analysis_method"] = "basic_overview"
    
    # 4. Return all the information
    return {
        "year": year,
        "manual_info": manual_info,
        "sample_teams": slimmed_team_data,
        "game_analysis": game_analysis
    }