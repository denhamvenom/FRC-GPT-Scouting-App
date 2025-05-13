# backend/app/services/learning_setup_service.py

import random
from typing import Optional, Dict, Any, List
import os
import json
from fastapi import UploadFile

from app.services.statbotics_client import get_team_epa
from app.services.tba_client import get_event_teams
from app.services.manual_parser_service import extract_manual_text, analyze_game_manual_in_chunks, analyze_game_overview, extract_game_relevant_sections
from app.services.global_cache import cache

async def start_learning_setup(year: int, manual_url: Optional[str] = None, manual_file: Optional[UploadFile] = None, event_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Pulls sample teams, processes the game manual, and prepares GPT variable discovery.

    Args:
        year: FRC season year
        manual_url: Optional URL to game manual PDF
        manual_file: Optional uploaded game manual PDF
        event_key: Optional event key to fetch teams from

    Returns:
        Dict containing setup information and analysis
    """
    # Use the provided event key if available, otherwise fall back to the default
    sample_event_key = event_key if event_key else f"{year}arc"  # Default event key pattern

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

    # 3. Process manual, with improved handling for existing manual data
    manual_info = {"manual_file_received": manual_file is not None, "manual_url": manual_url}
    game_analysis = None

    # Cache the year for reference
    cache["manual_year"] = year

    # Define paths for manual data files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    manual_info_path = os.path.join(data_dir, f"manual_info_{year}.json")
    manual_text_path = os.path.join(data_dir, f"manual_text_{year}.json")
    game_analysis_path = os.path.join(data_dir, f"game_analysis_{year}.json")

    # Check if we already have manual data for this year
    existing_manual_info = None
    existing_manual_text = None
    existing_game_analysis = None

    if os.path.exists(manual_info_path):
        try:
            with open(manual_info_path, "r", encoding="utf-8") as f:
                existing_manual_info = json.load(f)

            # Check if there's also a manual text file
            if os.path.exists(manual_text_path):
                with open(manual_text_path, "r", encoding="utf-8") as f:
                    existing_manual_text = json.load(f)

            # Check if there's a game analysis file
            if os.path.exists(game_analysis_path):
                with open(game_analysis_path, "r", encoding="utf-8") as f:
                    existing_game_analysis = json.load(f)

            print(f"Found existing manual data for {year}")
        except Exception as e:
            print(f"Error reading existing manual data: {e}")

    # If manual file or URL is provided, prioritize processing it
    if manual_file or manual_url:
        # Try to process the full manual
        try:
            manual_text = await extract_manual_text(manual_file, manual_url)

            if manual_text:
                # Cache the manual text
                cache["manual_text"] = manual_text
                manual_info["text_length"] = len(manual_text)

                # Extract game-relevant sections
                relevant_sections = await extract_game_relevant_sections(manual_text, year)
                manual_info["game_name"] = relevant_sections.get("game_name")
                manual_info["sections_extracted"] = True

                # Save manual info (including URL) to a file
                with open(manual_info_path, "w", encoding="utf-8") as f:
                    json.dump({"url": manual_url, "game_name": relevant_sections.get("game_name")}, f, indent=2)

                # Analyze the manual with GPT in chunks
                game_analysis = await analyze_game_manual_in_chunks(manual_text, year)
                manual_info["analysis_complete"] = game_analysis is not None

                # Save the game analysis to a file
                if game_analysis:
                    with open(game_analysis_path, "w", encoding="utf-8") as f:
                        json.dump(game_analysis, f, indent=2)
        except Exception as e:
            print(f"Error processing manual: {e}")
            # Fall back to existing manual data if available
            if existing_manual_text and existing_game_analysis:
                manual_info["text_length"] = len(existing_manual_text.get("relevant_sections", ""))
                manual_info["game_name"] = existing_manual_info.get("game_name")
                manual_info["using_cached_manual"] = True
                manual_info["analysis_complete"] = True
                game_analysis = existing_game_analysis
            else:
                # If no existing data, fall back to basic analysis
                game_analysis = await analyze_game_overview(year)
                manual_info["analysis_error"] = str(e)
    else:
        # If no manual provided, use existing manual data if available
        if existing_manual_text and existing_game_analysis:
            manual_info["text_length"] = len(existing_manual_text.get("relevant_sections", ""))
            manual_info["game_name"] = existing_manual_info.get("game_name")
            manual_info["using_cached_manual"] = True
            manual_info["sections_extracted"] = True
            manual_info["analysis_complete"] = True
            manual_info["url"] = existing_manual_info.get("url")
            game_analysis = existing_game_analysis

            # Also update the cache
            cache["manual_text"] = existing_manual_text.get("relevant_sections", "")
            cache["game_analysis"] = existing_game_analysis
        else:
            # If no existing data and no manual provided, warn user and do basic analysis
            game_analysis = await analyze_game_overview(year)
            manual_info["analysis_method"] = "basic_overview"
            manual_info["no_manual_warning"] = True
    
    # 4. Return all the information
    return {
        "year": year,
        "manual_info": manual_info,
        "sample_teams": slimmed_team_data,
        "game_analysis": game_analysis
    }