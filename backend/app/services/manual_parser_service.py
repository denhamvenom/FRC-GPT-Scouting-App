# backend/app/services/manual_parser_service.py

import os
import fitz  # PyMuPDF
from typing import Dict, List, Optional, Any
import io
from fastapi import UploadFile
from dotenv import load_dotenv
from openai import AsyncOpenAI
import httpx
from app.services.global_cache import cache

load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        file_content: Raw bytes of the PDF file
        
    Returns:
        str: Extracted text content
    """
    pdf_document = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    
    return text

async def fetch_pdf_from_url(url: str) -> Optional[bytes]:
    """
    Download a PDF file from a URL.
    
    Args:
        url: URL pointing to a PDF file
        
    Returns:
        Optional[bytes]: PDF file content or None if download fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=30.0)
            response.raise_for_status()
            return response.content
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None

async def extract_manual_text(manual_file: Optional[UploadFile] = None, manual_url: Optional[str] = None) -> Optional[str]:
    """
    Extract text from either an uploaded PDF file or a PDF URL.
    
    Args:
        manual_file: Optional uploaded PDF file
        manual_url: Optional URL to a PDF file
        
    Returns:
        Optional[str]: Extracted text or None if extraction fails
    """
    if manual_file:
        content = await manual_file.read()
        text = await extract_text_from_pdf(content)
    elif manual_url:
        pdf_content = await fetch_pdf_from_url(manual_url)
        if not pdf_content:
            return None
        text = await extract_text_from_pdf(pdf_content)
    else:
        return None
    
    # Save to global cache
    cache["manual_text"] = text
    
    return text

async def analyze_game_overview(year: int) -> Dict[str, Any]:
    """
    Process a small sample or overview of the game without requiring the full manual
    Uses the more efficient GPT-4.1-nano model to reduce token usage.
    
    Args:
        year: FRC season year
        
    Returns:
        Dict containing basic game information
    """
    # Instead of processing the entire manual, we'll have GPT generate basic info based on the year
    prompt = f"""
You are an expert on FIRST Robotics Competition (FRC) games. For the {year} season, provide a basic overview of:
1. The game name
2. Basic field elements
3. Main scoring actions 
4. Common strategy elements relevant to scouting
5. Recommended scouting variables (in snake_case format)

Output structured JSON only, following this format:
{{
  "game_name": "string",
  "field_elements": ["string", "string"],
  "scoring_actions": ["string", "string"],
  "scouting_variables": ["string", "string"]
}}
"""

    response = await client.chat.completions.create(
        model="gpt-4.1-nano",  # Using nano model here too
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        timeout=30  # Shorter timeout for this simpler request
    )
    
    extracted_info = response.choices[0].message.content
    
    # Parse the JSON response - handle potential JSON formatting issues
    try:
        import json
        # Clean up the response if needed
        if "```json" in extracted_info:
            extracted_info = extracted_info.split("```json")[1].split("```")[0].strip()
        elif "```" in extracted_info:
            extracted_info = extracted_info.split("```")[1].split("```")[0].strip()
            
        result = json.loads(extracted_info)
        
        # Save to cache for reference
        cache["game_analysis"] = result
        
        return result
    except Exception as e:
        print(f"Error parsing GPT response: {e}")
        print(f"Raw response: {extracted_info}")
        # Return a simplified structure if parsing fails
        return {
            "error": "Failed to parse GPT output",
            "raw_response": extracted_info
        }

async def analyze_game_manual_in_chunks(manual_text: str, year: int) -> Dict[str, Any]:
    """
    Analyze the game manual using GPT, processing in smaller chunks to avoid rate limits.
    Uses the more efficient GPT-4.1-nano model to reduce token usage.
    
    Args:
        manual_text: Extracted text from the game manual
        year: FRC season year
        
    Returns:
        Dict containing extracted game information
    """
    # First, let's extract the table of contents or initial part for overall structure
    intro_text = manual_text[:8000]  # First 8K chars
    
    # Step 1: Get the basic game structure and scouting variables
    prompt_intro = f"""
You are analyzing a FIRST Robotics Competition (FRC) game manual for the {year} season.
Based on the introduction section provided, identify:

1. Game name
2. Match structure (auto, teleop duration, etc.)
3. Basic scoring elements
4. Key sections that would contain detailed scoring actions

Output JSON only:
{{
  "game_name": "string",
  "match_structure": {{ "auto_duration": "string", "teleop_duration": "string" }},
  "key_scoring_elements": ["string"],
  "important_sections": ["string"]
}}

Manual Introduction:
{intro_text}
"""

    # Get basic game info - using GPT-4.1-nano for efficiency
    try:
        intro_response = await client.chat.completions.create(
            model="gpt-4.1-nano",  # Using nano model instead of gpt-4o
            messages=[{"role": "user", "content": prompt_intro}],
            temperature=0,
            timeout=30
        )
        
        intro_info = intro_response.choices[0].message.content
        
        import json
        if "```json" in intro_info:
            intro_info = intro_info.split("```json")[1].split("```")[0].strip()
        elif "```" in intro_info:
            intro_info = intro_info.split("```")[1].split("```")[0].strip()
            
        game_info = json.loads(intro_info)
    except Exception as e:
        print(f"Error processing game intro: {e}")
        # Fall back to basic analysis
        return await analyze_game_overview(year)
    
    # Step 2: Extract scouting variables from just the scoring sections
    # Look for sections about scoring, points, ranking, etc.
    relevant_keywords = ["scoring", "points", "ranking", "auto", "autonomous", "teleop", "endgame"]
    
    # Split manual into paragraphs
    paragraphs = manual_text.split("\n\n")
    
    # Filter to paragraphs likely about scoring (sample a subset to stay under limits)
    scoring_paragraphs = []
    for para in paragraphs:
        if any(keyword in para.lower() for keyword in relevant_keywords):
            scoring_paragraphs.append(para)
            # We can process more text with the nano model, but still keep it reasonable
            if len("\n\n".join(scoring_paragraphs)) > 30000:
                break
    
    scoring_text = "\n\n".join(scoring_paragraphs[:75])  # Take first 75 matches or fewer
    
    prompt_variables = f"""
Based on these scoring-related sections from a FIRST Robotics Competition manual for {year}, 
identify the optimal scouting variables a team would want to track.

Group them by category and use snake_case format:

Output JSON only:
{{
  "scouting_variables": {{
    "team_info": ["team_number", "match_number", "alliance_color"],
    "auto_phase": ["auto_variable_1", "auto_variable_2"],
    "teleop_phase": ["teleop_variable_1", "teleop_variable_2"],
    "endgame": ["endgame_variable_1"],
    "penalties": ["penalty_variable_1"],
    "strategy_notes": ["subjective_variable_1"]
  }}
}}

Scoring Sections:
{scoring_text}
"""

    try:
        # Again using nano model
        variables_response = await client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt_variables}],
            temperature=0,
            timeout=30
        )
        
        variables_info = variables_response.choices[0].message.content
        
        if "```json" in variables_info:
            variables_info = variables_info.split("```json")[1].split("```")[0].strip()
        elif "```" in variables_info:
            variables_info = variables_info.split("```")[1].split("```")[0].strip()
            
        variables_data = json.loads(variables_info)
    except Exception as e:
        print(f"Error processing scouting variables: {e}")
        variables_data = {
            "scouting_variables": {
                "team_info": ["team_number", "match_number", "alliance_color"],
                "auto_phase": ["auto_score"],
                "teleop_phase": ["teleop_score"],
                "endgame": ["endgame_score"],
                "penalties": ["fouls"],
                "strategy_notes": ["comments"]
            }
        }
    
    # Combine all results
    combined_result = {
        "game_name": game_info.get("game_name", f"FRC {year} Game"),
        "match_structure": game_info.get("match_structure", {}),
        "field_elements": game_info.get("key_scoring_elements", []),
        "scouting_variables": variables_data.get("scouting_variables", {})
    }
    
    # Save to cache for reference
    cache["game_analysis"] = combined_result
    
    return combined_result