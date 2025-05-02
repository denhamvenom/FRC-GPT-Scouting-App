# backend/app/services/schema_superscout_service.py

import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

GPT_MODEL = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SUPER_TAGS = [
    "team_number",
    "starting_position",
    "auto_behavior",
    "auto_contact",
    "defense_level",
    "penalties",
    "yellow_card",
    "red_card",
    "driver_skill",
    "field_awareness",
    "strategy_notes",
    "robot_connection_issue",
    "no_show"
]

async def map_superscout_headers(headers: List[str]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """
    Return:
    - Header → Tag mapping
    - Robot Groups → List of headers for each robot
    """

    prompt_mapping = f"""
You are a technical assistant for a robotics scouting system. The following are valid tags for superscouting observations:

{SUPER_TAGS}

You are given a list of column headers from a scouting sheet. 
For each header, return the most appropriate tag from the list above. Use "ignore" if no suitable tag applies.

Return ONLY raw JSON:
{{
  "Header 1": "tag_name",
  "Header 2": "tag_name",
  ...
}}

Headers:
{headers}
"""

    prompt_offsets = f"""
The following are spreadsheet column headers collected during superscouting. 
They include data for three robots per match, grouped horizontally.

Your job is to split the headers into three groups: 
Robot 1 columns, Robot 2 columns, and Robot 3 columns.

Return ONLY raw JSON:
{{
  "robot_1": ["Header 1", "Header 2", ...],
  "robot_2": ["Header 3", "Header 4", ...],
  "robot_3": ["Header 5", "Header 6", ...]
}}

Headers:
{headers}
"""

    # Mapping headers -> tags
    response_map = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt_mapping}],
        temperature=0,
        timeout=15
    )

    content_map = response_map.choices[0].message.content.strip()
    if content_map.startswith("```json"):
        content_map = content_map[7:]
    if content_map.startswith("```"):
        content_map = content_map[3:]
    if content_map.endswith("```"):
        content_map = content_map[:-3]

    try:
        mapping = eval(content_map)
    except Exception as e:
        print("Mapping parse error:", e)
        mapping = {"error": "Failed to parse mapping output."}

    # Grouping offsets robot_1/2/3
    response_offsets = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt_offsets}],
        temperature=0,
        timeout=15
    )

    content_offsets = response_offsets.choices[0].message.content.strip()
    if content_offsets.startswith("```json"):
        content_offsets = content_offsets[7:]
    if content_offsets.startswith("```"):
        content_offsets = content_offsets[3:]
    if content_offsets.endswith("```"):
        content_offsets = content_offsets[:-3]

    try:
        offsets = eval(content_offsets)
    except Exception as e:
        print("Offsets parse error:", e)
        offsets = {"error": "Failed to parse offset output."}

    return mapping, offsets
