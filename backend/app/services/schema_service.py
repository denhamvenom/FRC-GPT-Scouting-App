# File: backend/app/services/schema_service.py

from typing import List, Dict
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastapi import UploadFile
from app.services.global_cache import cache

load_dotenv()

GPT_MODEL = "gpt-4.1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def extract_game_tags_from_manual(manual_text: str) -> List[str]:
    """
    Extract standardized tags from the uploaded game manual.
    Could use GPT or simple parsing to identify field names (e.g., "auto_coral_l1").
    Returns a list of tag strings.
    """
    prompt = f"""
You are a technical assistant. Given the text of a FIRST Robotics Competition game manual,
extract all standardized action and scoring tags (snake_case) that correspond to match data fields.
Return a JSON list of strings, e.g. ["team_number", "auto_coral_l1", ...].
"""
    response = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt + "\nManual Text:\n" + manual_text}],
        temperature=0.2,
        timeout=30
    )
    content = response.choices[0].message.content.strip()
    try:
        tags = eval(content)
        return tags if isinstance(tags, list) else []
    except Exception:
        return []

async def map_headers_to_tags(headers: List[str], game_tags: List[str]) -> Dict[str, str]:
    """
    Map spreadsheet column headers to the provided list of standardized game tags.
    Uses GPT to align each header with the best match or 'ignore'.
    """
    prompt = f"""
You are a technical assistant for a robotics competition.
Below is a list of valid standardized tags for the current game:
{game_tags}

You are given a list of spreadsheet column headers collected by human scouts.
For each header, map it to the most appropriate tag from the list above.
If no good match exists, assign it the value 'ignore'.

Return ONLY valid raw JSON in this format (no explanation, no markdown):
{{
  "Header 1": "tag_name",
  "Header 2": "tag_name",
  ...
}}

Headers:
{headers}
"""
    response = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        timeout=30
    )
    content = response.choices[0].message.content.strip()
    for fence in ("```json", "```"):
        content = content.strip().lstrip(fence).rstrip(fence)
    try:
        return eval(content)
    except Exception:
        return {h: "error" for h in headers}

async def extract_manual_text(manual_file: UploadFile) -> str:
    """
    Read uploaded manual file and extract text content.
    Assumes plain text or decodable bytes.
    Also saves it to the global cache.
    """
    content = await manual_file.read()
    text = content.decode("utf-8", errors="ignore")
    cache['manual_text'] = text
    return text

def extract_sheet_id(sheet_url: str) -> str:
    """
    Extracts the Google Sheet ID from a full URL or returns the ID if already given.
    """
    if "/d/" in sheet_url:
        return sheet_url.split("/d/")[1].split("/")[0]
    return sheet_url.strip()
