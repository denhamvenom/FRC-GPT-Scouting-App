# backend/app/services/learning_setup_service.py

import random
from typing import Optional, Dict, Any, List
import os
import json
import shutil # Added for file operations
from fastapi import UploadFile

from app.services.statbotics_client import get_team_epa
from app.services.tba_client import get_event_teams
from app.services.manual_parser_service import (
    extract_manual_text, 
    analyze_game_manual_in_chunks, 
    analyze_game_overview, 
    extract_game_relevant_sections,
    extract_toc_from_pdf # Added import
)
from app.services.global_cache import cache
from app.database.db import get_db_session
from app.database.models import GameManual # Import the GameManual model
from sqlalchemy.orm import Session
from sqlalchemy.sql import func # for server_default=func.now()

# Helper function (can be moved to a shared utility module if used elsewhere)
def sanitize_filename_for_path(filename: str) -> str:
    """Sanitizes a filename to be used in a path, keeping it readable, returns only base."""
    base, _ = os.path.splitext(filename)
    sanitized_base = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in base)
    return sanitized_base

async def start_learning_setup(year: int, manual_file: Optional[UploadFile] = None, event_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Pulls sample teams, processes the game manual, and prepares GPT variable discovery.

    Args:
        year: FRC season year
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
    manual_info = {"manual_file_received": manual_file is not None}
    game_analysis = None
    saved_manual_path = None # To store path of saved manual

    # Cache the year for reference
    cache["manual_year"] = year

    # Define paths for manual data files
    # Ensure base_dir is correctly defined relative to the current file's location
    # Assuming this service file is in backend/app/services/
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(current_file_dir, "..", "..") # Moves up to backend/
    data_dir = os.path.join(base_dir, "data") # backend/data
    
    # Directory for saving uploaded PDF manuals
    manuals_pdf_dir = os.path.join(data_dir, "game_manuals", "pdfs")
    os.makedirs(manuals_pdf_dir, exist_ok=True)

    # Paths for JSON data related to manual processing
    json_data_dir = os.path.join(data_dir, f"manual_processing_data_{year}") # Per-year directory for JSONs
    os.makedirs(json_data_dir, exist_ok=True)
    manual_info_path = os.path.join(json_data_dir, f"manual_info_{year}.json")
    manual_text_path = os.path.join(json_data_dir, f"manual_text_{year}.json")
    game_analysis_path = os.path.join(json_data_dir, f"game_analysis_{year}.json")
    
    # Save uploaded manual file if provided
    if manual_file:
        try:
            # Use original filename for the saved PDF
            file_location = os.path.join(manuals_pdf_dir, manual_file.filename)
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(manual_file.file, file_object)
            saved_manual_path = file_location
            manual_info["saved_manual_filename"] = manual_file.filename
            manual_info["saved_manual_path"] = file_location
            print(f"Manual file '{manual_file.filename}' saved to '{file_location}'")

            # --- Add ToC Extraction and Saving ---
            if saved_manual_path and manual_file.filename:
                try:
                    print(f"Attempting to extract ToC from: {saved_manual_path}")
                    toc_data = await extract_toc_from_pdf(saved_manual_path)
                    manual_info["toc_extraction_attempted"] = True
                    if toc_data:
                        manual_info["toc_found"] = True
                        manual_info["toc_data"] = toc_data
                        
                        # Define path for saving ToC JSON
                        toc_dir = os.path.join(json_data_dir, "toc")
                        os.makedirs(toc_dir, exist_ok=True)
                        
                        # Sanitize filename before creating toc_file_name
                        base_filename, ext = os.path.splitext(manual_file.filename)
                        sanitized_base_filename = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in base_filename)
                        toc_file_name = f"{sanitized_base_filename}_toc.json"
                        toc_save_path = os.path.join(toc_dir, toc_file_name)
                        
                        with open(toc_save_path, "w", encoding="utf-8") as f:
                            json.dump(toc_data, f, indent=2)
                        manual_info["toc_saved_path"] = toc_save_path
                        print(f"ToC data saved to '{toc_save_path}'")
                    else:
                        manual_info["toc_found"] = False
                        print(f"No ToC data extracted or ToC was empty for {manual_file.filename}.")
                except Exception as toc_e:
                    print(f"Error during ToC extraction or saving: {toc_e}")
                    manual_info["toc_extraction_error"] = str(toc_e)
            # --- End of ToC Extraction and Saving ---

            # --- Database Operation: Create/Update GameManual record ---
            if manual_file.filename and saved_manual_path: # Ensure we have critical info
                db: Session = next(get_db_session())
                try:
                    original_filename = manual_file.filename
                    s_filename_base = sanitize_filename_for_path(original_filename)
                    
                    db_manual = db.query(GameManual).filter_by(
                        year=year, 
                        sanitized_filename_base=s_filename_base
                    ).first()

                    toc_json_s_path = manual_info.get("toc_saved_path") # Get from earlier step

                    if db_manual:
                        # Update existing record
                        db_manual.stored_pdf_path = saved_manual_path
                        db_manual.toc_json_path = toc_json_s_path
                        db_manual.upload_timestamp = func.now() # Update timestamp
                        db_manual.original_filename = original_filename # In case it changed subtly but base is same
                        print(f"Updating existing GameManual DB record for {original_filename}, year {year}")
                    else:
                        # Create new record
                        db_manual = GameManual(
                            year=year,
                            original_filename=original_filename,
                            sanitized_filename_base=s_filename_base,
                            stored_pdf_path=saved_manual_path,
                            toc_json_path=toc_json_s_path,
                            # parsed_sections_path will be updated later
                        )
                        db.add(db_manual)
                        print(f"Creating new GameManual DB record for {original_filename}, year {year}")
                    
                    db.commit()
                    db.refresh(db_manual)
                    manual_info["manual_db_id"] = db_manual.id
                    manual_info["sanitized_filename_base"] = s_filename_base
                    print(f"GameManual DB record ID {db_manual.id} processed for {original_filename}")

                except Exception as db_e:
                    print(f"Database error processing GameManual for {manual_file.filename}: {db_e}")
                    manual_info["manual_db_error"] = str(db_e)
                    if db: # Check if db session object exists
                        db.rollback()
                finally:
                    if db: # Check if db session object exists
                        db.close()
            # --- End of Database Operation ---

        except Exception as e:
            print(f"Error saving manual file: {e}")
            manual_info["manual_save_error"] = str(e)

    # Check if we already have manual data for this year
    # This section loads info for previously processed manuals (if no new one is uploaded)
    # It might need adjustment if we want to pull from DB instead of just JSON files.
    # For now, keeping it as is, but noting that DB is the single source of truth for paths.
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

            print(f"Found existing manual data for {year} in {json_data_dir}")
        except Exception as e:
            print(f"Error reading existing manual data from {json_data_dir}: {e}")

    # If manual file is provided, prioritize processing it
    if manual_file: # manual_url is removed from this condition
        # Try to process the full manual
        try:
            # Pass None for manual_url as it's removed
            manual_text = await extract_manual_text(manual_file, None) 

            if manual_text:
                # Cache the manual text
                cache["manual_text"] = manual_text
                manual_info["text_length"] = len(manual_text)

                # Extract game-relevant sections
                relevant_sections = await extract_game_relevant_sections(manual_text, year)
                manual_info["game_name"] = relevant_sections.get("game_name")
                manual_info["sections_extracted"] = True

                # Save manual info to a file
                # Store information about the processed file rather than a URL
                info_to_save = {
                    "processed_filename": manual_file.filename if manual_file else None,
                    "game_name": relevant_sections.get("game_name")
                }
                with open(manual_info_path, "w", encoding="utf-8") as f:
                    json.dump(info_to_save, f, indent=2)
                
                # Analyze the manual with GPT in chunks
                game_analysis = await analyze_game_manual_in_chunks(manual_text, year)
                manual_info["analysis_complete"] = game_analysis is not None

                # Save the game analysis to a file
                if game_analysis:
                    with open(game_analysis_path, "w", encoding="utf-8") as f:
                        json.dump(game_analysis, f, indent=2)
            else: # manual_text is None
                manual_info["manual_processing_error"] = "Failed to extract text from manual."
                # Fall back to existing or basic analysis if text extraction fails
                if existing_manual_text and existing_game_analysis:
                    manual_info["text_length"] = len(existing_manual_text.get("relevant_sections", "")) # Consider if this is still valid
                    manual_info["game_name"] = existing_manual_info.get("game_name")
                    manual_info["using_cached_manual"] = True
                    manual_info["analysis_complete"] = True
                    game_analysis = existing_game_analysis
                else:
                    game_analysis = await analyze_game_overview(year)
                    manual_info["analysis_method"] = "basic_overview_due_to_extraction_failure"

        except Exception as e:
            print(f"Error processing manual: {e}")
            manual_info["manual_processing_error"] = str(e)
            # Fall back to existing manual data if available
            if existing_manual_text and existing_game_analysis:
                manual_info["text_length"] = len(existing_manual_text.get("relevant_sections", "")) # Consider if this is still valid
                manual_info["game_name"] = existing_manual_info.get("game_name")
                manual_info["using_cached_manual"] = True
                manual_info["analysis_complete"] = True
                game_analysis = existing_game_analysis
            else:
                # If no existing data, fall back to basic analysis
                game_analysis = await analyze_game_overview(year)
                manual_info["analysis_error"] = str(e) # Keep original error for this path
    else: # No manual_file provided
        # If no manual provided, use existing manual data if available
        if existing_manual_info and existing_manual_text and existing_game_analysis:
            manual_info["text_length"] = len(existing_manual_text.get("relevant_sections", ""))
            manual_info["game_name"] = existing_manual_info.get("game_name")
            manual_info["using_cached_manual"] = True
            manual_info["sections_extracted"] = existing_manual_info.get("sections_extracted", False) # Ensure this key exists
            manual_info["analysis_complete"] = True
            # "url" is no longer relevant here unless it was part of old existing_manual_info
            if "url" in existing_manual_info: # Legacy check
                 manual_info["processed_url_from_cache"] = existing_manual_info.get("url")
            if "processed_filename" in existing_manual_info: # Current check
                 manual_info["processed_filename_from_cache"] = existing_manual_info.get("processed_filename")
            
            # Attempt to load existing ToC if manual data is from cache
            if existing_manual_info and "processed_filename_from_cache" in manual_info:
                cached_filename = manual_info["processed_filename_from_cache"] # This is original_filename
                if cached_filename:
                    s_filename_base = sanitize_filename_for_path(cached_filename)
                    # Try to load from DB first to get the correct paths
                    db: Session = next(get_db_session())
                    try:
                        db_manual = db.query(GameManual).filter_by(
                            year=year,
                            sanitized_filename_base=s_filename_base
                        ).first()
                        if db_manual and db_manual.toc_json_path and os.path.exists(db_manual.toc_json_path):
                            with open(db_manual.toc_json_path, "r", encoding="utf-8") as f:
                                manual_info["toc_data"] = json.load(f)
                            manual_info["toc_saved_path"] = db_manual.toc_json_path
                            manual_info["toc_found"] = True
                            manual_info["toc_from_db_cache"] = True # Indicate source
                            manual_info["manual_db_id"] = db_manual.id
                            manual_info["sanitized_filename_base"] = s_filename_base
                            # Update last_accessed_timestamp (optional, can be done in a dedicated get endpoint too)
                            # db_manual.last_accessed_timestamp = func.now()
                            # db.commit()
                            print(f"Loaded cached ToC from DB-verified path: {db_manual.toc_json_path}")
                        elif db_manual:
                             print(f"DB record for {cached_filename} found, but ToC path '{db_manual.toc_json_path}' missing or invalid.")
                             manual_info["toc_found"] = False
                        else: # Fallback to old logic if not in DB for some reason (should be rare)
                            print(f"No DB record for {cached_filename}, year {year}. Falling back to legacy cache check.")
                            toc_file_name = f"{s_filename_base}_toc.json"
                            expected_toc_path = os.path.join(json_data_dir, "toc", toc_file_name)
                            if os.path.exists(expected_toc_path):
                                with open(expected_toc_path, "r", encoding="utf-8") as f:
                                    manual_info["toc_data"] = json.load(f)
                                manual_info["toc_saved_path"] = expected_toc_path
                                manual_info["toc_found"] = True
                                manual_info["toc_from_legacy_cache"] = True
                                print(f"Loaded cached ToC from legacy path: {expected_toc_path}")
                            else:
                                print(f"No cached ToC found at legacy path {expected_toc_path}")
                                manual_info["toc_found"] = False
                    except Exception as e:
                        print(f"Error loading cached ToC (DB or legacy): {e}")
                        manual_info["toc_cache_load_error"] = str(e)
                    finally:
                        db.close()
            game_analysis = existing_game_analysis

            # Also update the cache
            cache["manual_text"] = existing_manual_text.get("relevant_sections", "") # Or full text if that's what's cached
            cache["game_analysis"] = existing_game_analysis
        else:
            # If no existing data and no manual provided, warn user and do basic analysis
            game_analysis = await analyze_game_overview(year)
            manual_info["analysis_method"] = "basic_overview"
            manual_info["no_manual_warning"] = True
    
    # 4. Return all the information
    return_data = {
        "year": year,
        "manual_info": manual_info,
        "sample_teams": slimmed_team_data,
        "game_analysis": game_analysis
    }
    if saved_manual_path: # Add saved path if a file was processed
        return_data["saved_manual_path"] = saved_manual_path
        
    return return_data