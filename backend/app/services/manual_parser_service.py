# backend/app/services/manual_parser_service.py

import io
import json
import os
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
import httpx
from app.services.global_cache import cache
from dotenv import load_dotenv
from fastapi import UploadFile
from openai import AsyncOpenAI

load_dotenv()

GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

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


async def extract_manual_text(
    manual_file: Optional[UploadFile] = None, manual_url: Optional[str] = None
) -> Optional[str]:
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


async def extract_toc_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts the Table of Contents (ToC) from a PDF file.

    Args:
        pdf_path: The file path to the PDF.

    Returns:
        A list of dictionaries, where each dictionary represents a ToC item.
        Example: [{'title': 'Section 1', 'level': 1, 'page': 5}]
        Returns an empty list if no ToC is found or an error occurs.
    """
    toc_list = []
    try:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()  # Returns a list like [[lvl, title, page, ...], ...]
        doc.close()

        if not toc:
            print(f"No ToC found in PDF: {pdf_path}")
            return []

        for item in toc:
            # Ensure item has at least 3 elements (level, title, page)
            if len(item) >= 3:
                level, title, page = item[0], item[1], item[2]
                # Basic cleaning of title
                title = title.strip()
                # Ensure page is an integer
                try:
                    page = int(page)
                except ValueError:
                    print(
                        f"Warning: Could not parse page number for ToC item: {item} in {pdf_path}. Skipping."
                    )
                    continue

                toc_list.append({"level": level, "title": title, "page": page})
            else:
                print(f"Warning: Malformed ToC item encountered: {item} in {pdf_path}")

    except Exception as e:
        print(f"Error extracting ToC from {pdf_path}: {e}")
        return []  # Return empty list on error

    return toc_list


async def extract_text_from_selected_sections(
    pdf_path: str,
    selected_sections: List[Dict[str, Any]],
    toc_data: List[Dict[str, Any]],
) -> str:
    """
    Extracts text from specified sections of a PDF, based on ToC selections.

    Args:
        pdf_path: Path to the PDF file.
        selected_sections: List of selected ToC items (dicts with 'title', 'level', 'page').
        toc_data: The full ToC of the document.

    Returns:
        A single string concatenating text from all selected sections.
    """
    full_extracted_text = ""
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return "Error: PDF file not found."

    if not selected_sections:
        return "Error: No sections selected for extraction."

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return f"Error opening PDF: {e}"

    # Sort toc_data by page number to help find next sections correctly
    # And also by level, so higher level items (like main chapters) come before sub-items if on same page
    sorted_toc_data = sorted(toc_data, key=lambda x: (x["page"], x["level"]))

    for i, section in enumerate(selected_sections):
        start_page_pdf_idx = section["page"] - 1  # ToC pages are 1-indexed, PyMuPDF is 0-indexed
        section_text = f"\n\n--- Section: {section['title']} (Page {section['page']}) ---\n"

        # Determine end_page for the current section
        end_page_pdf_idx = doc.page_count  # Default to end of document

        # Find the current section's index in the *full sorted* ToC
        current_section_toc_index = -1
        for idx, toc_item in enumerate(sorted_toc_data):
            if (
                toc_item["title"] == section["title"]
                and toc_item["page"] == section["page"]
                and toc_item["level"] == section["level"]
            ):
                current_section_toc_index = idx
                break

        if current_section_toc_index != -1:
            # Look for the next ToC item that has a level less than or equal to the current section's level
            # or any item if the current section is a very low-level one (e.g. level 3, next could be level 1, 2, or 3)
            for next_toc_idx in range(current_section_toc_index + 1, len(sorted_toc_data)):
                next_toc_item = sorted_toc_data[next_toc_idx]
                # The end page is the page of the *next* section that is of the same or higher level (smaller level number)
                # OR if the next section is simply on a later page, irrespective of level, if we want to capture everything up to it.
                # For this logic: if next ToC item is same level or higher up (smaller level number), it marks the end.
                if next_toc_item["level"] <= section["level"]:
                    end_page_pdf_idx = (
                        next_toc_item["page"] - 1
                    )  # Text ends before the next section starts
                    break
                # If we encounter a section on a new page that is a sub-section of a *different* higher-level section,
                # that also implies our current section has ended.
                # This is implicitly handled if sorted_toc_data is used correctly to find the *next relevant* section.

        # Ensure start_page is not after end_page (can happen if ToC is messy or it's the last section)
        if start_page_pdf_idx >= end_page_pdf_idx and start_page_pdf_idx < doc.page_count:
            # If it's a single page section or determined to be the last part
            end_page_pdf_idx = start_page_pdf_idx + 1
        elif start_page_pdf_idx >= doc.page_count:
            print(
                f"Warning: Start page {section['page']} for section '{section['title']}' is out of document bounds ({doc.page_count} pages). Skipping."
            )
            continue

        # Extract text from the determined page range
        for page_num in range(start_page_pdf_idx, min(end_page_pdf_idx, doc.page_count)):
            try:
                page_obj = doc.load_page(page_num)
                section_text += page_obj.get_text("text") + "\n"
            except Exception as e:
                print(
                    f"Error extracting text from page {page_num + 1} for section '{section['title']}': {e}"
                )
                section_text += f"\n[Error extracting page {page_num + 1}]\n"

        full_extracted_text += section_text

    doc.close()
    return full_extracted_text.strip()


async def extract_game_relevant_sections(manual_text: str, year: int) -> Dict[str, Any]:
    """
    Extract only the game-relevant sections from the manual text.
    Focuses on gameplay, scoring, and field elements.

    Args:
        manual_text: Full text of the game manual
        year: FRC season year

    Returns:
        Dict with extracted sections and metadata
    """
    # Define keywords for relevant sections
    game_keywords = [
        "game overview",
        "game description",
        "gameplay",
        "match play",
        "scoring",
        "points",
        "auto",
        "autonomous",
        "teleop",
        "driver",
        "endgame",
        "field elements",
        "game pieces",
        "alliance",
        "ranking",
    ]

    # Build a prompt to extract relevant sections
    prompt = f"""
You are analyzing an FRC (FIRST Robotics Competition) game manual for the {year} season.
Extract ONLY the most strategically relevant sections related to:

1. Game overview
2. Scoring mechanisms
3. Field elements
4. Auto, teleop, and endgame phases
5. Ranking point criteria

Focus on information that would be relevant for scouting and alliance selection.
Exclude sections about robot construction rules, safety, event rules, or glossaries.

For each extract, include the section title and content. Keep your total response under 2000 tokens.
Format your response as structured JSON:

{{
  "game_name": "name of the game",
  "sections": [
    {{
      "title": "section title",
      "content": "extracted content"
    }}
  ]
}}
"""

    try:
        # Call the OpenAI API
        response = await client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n\nManual text:\n" + manual_text[:50000],
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )

        # Parse the response
        extracted_data = json.loads(response.choices[0].message.content)

        # Create a condensed version of all relevant sections for context
        relevant_sections = ""
        for section in extracted_data.get("sections", []):
            relevant_sections += f"{section['title']}:\n{section['content']}\n\n"

        # Add the relevant sections to the result
        result = {
            "game_name": extracted_data.get("game_name", f"FRC {year} Game"),
            "relevant_sections": relevant_sections,
        }

        # Save the extracted data to a file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        manual_text_path = os.path.join(data_dir, f"manual_text_{year}.json")
        with open(manual_text_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return result

    except Exception as e:
        print(f"Error extracting game sections from manual: {e}")
        return {"game_name": f"FRC {year} Game", "relevant_sections": ""}


async def analyze_game_manual_in_chunks(manual_text: str, year: int) -> Dict[str, Any]:
    """
    Analyze the game manual using GPT, processing in smaller chunks to avoid rate limits.

    Args:
        manual_text: Extracted text from the game manual
        year: FRC season year

    Returns:
        Dict containing extracted game information
    """
    # Try to extract relevant sections first
    try:
        game_info = await extract_game_relevant_sections(manual_text, year)
        if game_info and "game_name" in game_info:
            # We already have the game info from the relevant sections
            return {
                "game_name": game_info.get("game_name"),
                "scouting_variables": await extract_scouting_variables(
                    game_info.get("relevant_sections", ""), year
                ),
            }
    except Exception as e:
        print(f"Error extracting relevant sections: {e}")

    # Fallback to basic overview if section extraction fails
    return await analyze_game_overview(year)


async def analyze_game_overview(year: int) -> Dict[str, Any]:
    """
    Process a small sample or overview of the game without requiring the full manual.

    Args:
        year: FRC season year

    Returns:
        Dict containing basic game information
    """
    # Create a prompt to get basic game info
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
  "scouting_variables": {{
    "auto_phase": ["auto_variable_1", "auto_variable_2"],
    "teleop_phase": ["teleop_variable_1", "teleop_variable_2"],
    "endgame": ["endgame_variable_1"],
    "strategy": ["strategy_variable_1"]
  }}
}}
"""

    try:
        response = await client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=1000,
        )

        # Parse the response
        extracted_info = json.loads(response.choices[0].message.content)

        # Save to cache for reference
        cache["game_analysis"] = extracted_info

        return extracted_info
    except Exception as e:
        print(f"Error analyzing game overview: {e}")
        # Return minimal structure if analysis fails
        return {
            "game_name": f"FRC {year} Game",
            "field_elements": [],
            "scoring_actions": [],
            "scouting_variables": {
                "auto_phase": ["auto_score"],
                "teleop_phase": ["teleop_score"],
                "endgame": ["endgame_score"],
                "strategy": ["comments"],
            },
        }


async def extract_scouting_variables(game_text: str, year: int) -> Dict[str, List[str]]:
    """
    Extract recommended scouting variables from game text.

    Args:
        game_text: Text describing the game (ideally from relevant sections)
        year: FRC season year

    Returns:
        Dict with category keys and lists of variables as values
    """
    prompt = f"""
Based on this description of the {year} FRC game, suggest optimal scouting variables
that teams should track. Group these variables by category and use snake_case format.

Return ONLY a JSON object with this structure:
{{
  "auto_phase": ["auto_variable_1", "auto_variable_2"],
  "teleop_phase": ["teleop_variable_1", "teleop_variable_2"],
  "endgame": ["endgame_variable_1"],
  "strategy": ["strategy_variable_1"]
}}

Include standard variables like team_number and match_number in each appropriate phase.
Focus only on quantifiable metrics and observations that would be useful for alliance selection.

Game Description:
{game_text}
"""

    try:
        response = await client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=1000,
        )

        # Parse the response
        variables_data = json.loads(response.choices[0].message.content)

        # Ensure we have at least empty lists for each category
        default_categories = ["auto_phase", "teleop_phase", "endgame", "strategy"]
        for category in default_categories:
            if category not in variables_data:
                variables_data[category] = []

        return variables_data
    except Exception as e:
        print(f"Error extracting scouting variables: {e}")
        # Return basic structure if extraction fails
        return {
            "auto_phase": ["auto_score"],
            "teleop_phase": ["teleop_score"],
            "endgame": ["endgame_score"],
            "strategy": ["comments"],
        }
