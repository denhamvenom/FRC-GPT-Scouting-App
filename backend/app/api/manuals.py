# backend/app/api/manuals.py

import os
import json
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Body, Depends, Path as FastApiPath
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import datetime

from app.services.manual_parser_service import extract_text_from_selected_sections
from app.database.db import get_db_session
from app.database.models import GameManual

router = APIRouter(prefix="/api/manuals", tags=["Manuals"])

# --- Pydantic Models ---
class TocItem(BaseModel):
    title: str
    level: int
    page: int
    
    class Config:
        extra = "allow"

class SelectedSectionsRequest(BaseModel):
    manual_identifier: str # Original filename of the PDF
    year: int
    selected_sections: List[TocItem]

class ProcessedSectionsResponse(BaseModel):
    message: str
    manual_db_id: int
    saved_text_path: str
    extracted_text_length: int
    sample_text: str
    manual_text_json_created: bool = False
    manual_text_json_path: Optional[str] = None
    game_name_detected: Optional[str] = None

class GameManualBase(BaseModel):
    year: int
    original_filename: str
    sanitized_filename_base: str
    upload_timestamp: Optional[datetime.datetime] = None
    last_accessed_timestamp: Optional[datetime.datetime] = None

class GameManualCreate(GameManualBase):
    stored_pdf_path: Optional[str] = None
    toc_json_path: Optional[str] = None

class GameManualResponse(GameManualBase):
    id: int

    class Config:
        from_attributes = True # Changed from orm_mode for Pydantic v2

class GameManualDetailResponse(GameManualResponse):
    stored_pdf_path: Optional[str] = None
    toc_json_path: Optional[str] = None
    parsed_sections_path: Optional[str] = None
    toc_content: Optional[List[Dict[str, Any]]] = None
    toc_error: Optional[str] = None


# --- Helper Function ---
def sanitize_filename_base_for_path(filename: str) -> str:
    """Sanitizes a filename to be used as a base for paths, returns only the base without extension."""
    base, _ = os.path.splitext(filename)
    sanitized_base = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in base)
    return sanitized_base

# --- API Endpoints ---

@router.post("/process-sections", response_model=ProcessedSectionsResponse)
async def process_selected_sections(
    request_data: SelectedSectionsRequest = Body(...),
    db: Session = Depends(get_db_session)
):
    """
    Processes selected sections from a game manual PDF based on its Table of Contents (ToC).
    Extracts text from these sections and saves it to a new file.
    """
    original_manual_filename = request_data.manual_identifier
    year = request_data.year
    selected_sections_dicts = [item.model_dump() for item in request_data.selected_sections]
    
    s_filename_base = sanitize_filename_base_for_path(original_manual_filename)

    # --- Retrieve GameManual from DB ---
    db_manual = db.query(GameManual).filter_by(
        year=year, 
        sanitized_filename_base=s_filename_base
    ).first()

    if not db_manual:
        raise HTTPException(status_code=404, detail=f"GameManual record not found for {original_manual_filename}, year {year}")
    if not db_manual.stored_pdf_path or not os.path.exists(db_manual.stored_pdf_path):
        raise HTTPException(status_code=404, detail=f"Stored PDF path not found or invalid for manual ID {db_manual.id}")
    if not db_manual.toc_json_path or not os.path.exists(db_manual.toc_json_path):
        raise HTTPException(status_code=404, detail=f"ToC JSON path not found or invalid for manual ID {db_manual.id}")

    pdf_path = db_manual.stored_pdf_path
    toc_json_path = db_manual.toc_json_path

    try:
        with open(toc_json_path, "r", encoding="utf-8") as f:
            full_toc_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading ToC JSON file: {str(e)}")

    # --- Call the extraction service ---
    try:
        extracted_text = await extract_text_from_selected_sections(
            pdf_path=pdf_path,
            selected_sections=selected_sections_dicts,
            toc_data=full_toc_data 
        )
    except Exception as e:
        # Log the exception server-side for more details
        print(f"Error during text extraction from selected sections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text from sections: {str(e)}")

    if not extracted_text or extracted_text.startswith("Error:"):
        raise HTTPException(status_code=400, detail=f"Text extraction resulted in an error or no text: {extracted_text}")
        
    # --- Save the extracted text ---
    # Construct path relative to backend/data/ for consistency
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(current_file_dir, "..", "..")
    parsed_sections_dir = os.path.join(backend_dir, "data", f"manual_processing_data_{year}", "parsed_sections")
    os.makedirs(parsed_sections_dir, exist_ok=True)
    
    output_filename = f"{s_filename_base}_selected_sections.txt"
    saved_text_filepath = os.path.join(parsed_sections_dir, output_filename)
    
    # Initialize variables that will be used in the response
    manual_text_filepath = ""
    game_name = f"FRC {year} Game"

    try:
        with open(saved_text_filepath, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        
        # --- Create manual_text_{year}.json for picklist generator ---
        # This file is expected by the picklist generator service
        app_data_dir = os.path.join(backend_dir, "app", "data")
        os.makedirs(app_data_dir, exist_ok=True)
        
        manual_text_filename = f"manual_text_{year}.json"
        manual_text_filepath = os.path.join(app_data_dir, manual_text_filename)
        
        # Extract game name from the extracted text (look for common patterns)
        game_name = f"FRC {year} Game"  # Default fallback
        
        # Try to extract game name from the text
        text_lines = extracted_text.split('\n')
        for line in text_lines[:20]:  # Check first 20 lines
            line_clean = line.strip()
            if any(keyword in line_clean.upper() for keyword in ['GAME:', 'COMPETITION:', 'SEASON:', 'FIRST']):
                # Look for game names in common formats
                if 'REEFSCAPE' in line_clean.upper():
                    game_name = "REEFSCAPE 2025"
                    break
                elif 'CHARGED UP' in line_clean.upper():
                    game_name = "CHARGED UP 2023"
                    break
                elif 'RAPID REACT' in line_clean.upper():
                    game_name = "RAPID REACT 2022"
                    break
                elif 'INFINITE RECHARGE' in line_clean.upper():
                    game_name = "INFINITE RECHARGE 2020"
                    break
                elif 'DESTINATION: DEEP SPACE' in line_clean.upper():
                    game_name = "DESTINATION: DEEP SPACE 2019"
                    break
                elif 'POWER UP' in line_clean.upper():
                    game_name = "POWER UP 2018"
                    break
                elif 'STEAMWORKS' in line_clean.upper():
                    game_name = "STEAMWORKS 2017"
                    break
                elif 'STRONGHOLD' in line_clean.upper():
                    game_name = "STRONGHOLD 2016"
                    break
        
        # Create the manual text JSON structure expected by picklist generator
        manual_text_data = {
            "game_name": game_name,
            "relevant_sections": extracted_text,
            "year": year,
            "sections_processed": len(selected_sections_dicts),
            "processing_timestamp": datetime.datetime.now().isoformat(),
            "source_manual": original_manual_filename
        }
        
        with open(manual_text_filepath, "w", encoding="utf-8") as f:
            json.dump(manual_text_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created manual_text_{year}.json for picklist generator at: {manual_text_filepath}")
        
        # --- Update DB with parsed_sections_path ---
        db_manual.parsed_sections_path = saved_text_filepath
        db_manual.last_accessed_timestamp = func.now()
        db.commit()
        db.refresh(db_manual)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving extracted text or updating DB: {str(e)}")

    return ProcessedSectionsResponse(
        message="Successfully processed selected sections.",
        manual_db_id=db_manual.id,
        saved_text_path=saved_text_filepath,
        extracted_text_length=len(extracted_text),
        sample_text=extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
        manual_text_json_created=True,
        manual_text_json_path=manual_text_filepath,
        game_name_detected=game_name
    )

@router.get("", response_model=List[GameManualResponse])
async def list_manuals(db: Session = Depends(get_db_session)):
    """
    List all uploaded game manuals.
    """
    manuals = db.query(GameManual).order_by(GameManual.year.desc(), GameManual.original_filename).all()
    return manuals

@router.get("/{manual_id}", response_model=GameManualDetailResponse)
async def get_manual_details(
    manual_id: int = FastApiPath(..., title="The ID of the manual to retrieve"),
    db: Session = Depends(get_db_session)
):
    """
    Get detailed information for a specific game manual, including its ToC.
    """
    db_manual = db.query(GameManual).filter(GameManual.id == manual_id).first()
    if not db_manual:
        raise HTTPException(status_code=404, detail=f"Manual with ID {manual_id} not found.")

    response_data = GameManualDetailResponse.model_validate(db_manual) # Pydantic v2
    
    if db_manual.toc_json_path and os.path.exists(db_manual.toc_json_path):
        try:
            with open(db_manual.toc_json_path, "r", encoding="utf-8") as f:
                response_data.toc_content = json.load(f)
        except Exception as e:
            response_data.toc_error = f"Error reading ToC JSON file: {str(e)}"
            print(f"Error reading ToC for manual {manual_id}: {e}")
    elif db_manual.toc_json_path:
        response_data.toc_error = "ToC JSON file path exists in DB but file not found on disk."
    else:
        response_data.toc_error = "ToC JSON path not specified in DB."

    # Update last_accessed_timestamp
    try:
        db_manual.last_accessed_timestamp = func.now()
        db.commit()
    except Exception as e:
        db.rollback() # Rollback timestamp update error, but still return data
        print(f"Error updating last_accessed_timestamp for manual {manual_id}: {e}")

    return response_data

@router.delete("/{manual_id}", status_code=200)
async def delete_manual(
    manual_id: int = FastApiPath(..., title="The ID of the manual to delete"),
    db: Session = Depends(get_db_session)
):
    """
    Delete a game manual record and its associated files.
    """
    db_manual = db.query(GameManual).filter(GameManual.id == manual_id).first()
    if not db_manual:
        raise HTTPException(status_code=404, detail=f"Manual with ID {manual_id} not found.")

    paths_to_delete = [
        db_manual.stored_pdf_path,
        db_manual.toc_json_path,
        db_manual.parsed_sections_path
    ]
    
    deleted_files_count = 0
    errors_deleting_files = []

    for file_path in paths_to_delete:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files_count += 1
                print(f"Deleted file: {file_path}")
            except Exception as e:
                error_msg = f"Error deleting file {file_path}: {str(e)}"
                print(error_msg)
                errors_deleting_files.append(error_msg)
    
    try:
        db.delete(db_manual)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error deleting manual record: {str(e)}")

    response_message = f"Manual ID {manual_id} ('{db_manual.original_filename}') deleted. {deleted_files_count} associated file(s) removed."
    if errors_deleting_files:
        response_message += " Errors encountered during file deletion: " + "; ".join(errors_deleting_files)
        # Still return 200 as DB record deleted, but include error info
        return {"message": response_message, "file_deletion_errors": errors_deleting_files}

    return {"message": response_message}
