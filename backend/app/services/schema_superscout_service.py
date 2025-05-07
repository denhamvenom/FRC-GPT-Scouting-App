# backend/app/services/schema_superscout_service.py

import os
from typing import List, Dict, Tuple, Any
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

GPT_MODEL = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SUPER_TAGS = [
    # Critical Fields
    "team_number",
    "match_number",
    
    # Positioning and Starting
    "starting_position",
    "alliance_color",
    
    # Game Phases
    "auto_behavior",
    "auto_strategy",
    "teleop_strategy",
    "endgame_strategy",
    
    # Action Types (How robots perform actions)
    "pickup_type",         # HOW robot picks up game pieces (ground, human player, etc)
    "scoring_method",      # HOW robot scores (high, low, etc)
    "climbing_method",     # HOW robot climbs/parks
    "scoring_position",    # WHERE on the field robot typically scores
    
    # Performance Metrics
    "auto_contact",
    "defense_level",
    "offense_effectiveness",
    "penalties",
    "yellow_card",
    "red_card",
    "driver_skill",
    "field_awareness",
    
    # Issues and Notes
    "strategy_notes",
    "robot_connection_issue",
    "no_show",
    "mechanism_failure",
    "general_comments"
]

async def map_superscout_headers(headers: List[str], sample_data: List[List[str]] = None) -> Tuple[Dict[str, str], Dict[str, List[str]], Dict[str, Any]]:
    """
    Return:
    - Header → Tag mapping
    - Robot Groups → List of headers for each robot
    - Data insights → Information about data content and special patterns
    
    Args:
        headers: List of column headers from the spreadsheet
        sample_data: Sample rows of data to provide context about the actual content
    """
    
    # Format sample data for the prompt
    sample_data_str = ""
    if sample_data and len(sample_data) > 0:
        sample_data_str = "Sample data for each header:\n"
        for i, header in enumerate(headers):
            if i < len(headers):
                values = []
                for row in sample_data[:5]:  # Use up to 5 rows of sample data
                    if i < len(row):
                        values.append(str(row[i]))
                sample_values = ", ".join([v for v in values if v])
                sample_data_str += f"'{header}': [{sample_values}]\n"

    prompt_mapping = f"""
You are a technical assistant for a robotics scouting system. The following are valid tags for superscouting observations:

{SUPER_TAGS}

You are given a list of column headers from a scouting sheet AND sample data for each column. 
For each header, analyze both the header name AND its sample data to determine the most appropriate tag.
Pay special attention to what the data actually represents, not just what the header is called.

For example, a column named "Robot 1 tele pickup" with values like "ground intake", "human player", "none" 
should be mapped to a tag that represents HOW a robot performs actions, not just that it's a teleop field.

For each header, return the most appropriate tag from the list above. Use "ignore" if no suitable tag applies.

Return ONLY raw JSON:
{{
  "Header 1": "tag_name",
  "Header 2": "tag_name",
  ...
}}

Headers:
{headers}

{sample_data_str}
"""

    prompt_offsets = f"""
The following are spreadsheet column headers collected during superscouting. 
They include data for three robots per match, grouped horizontally.

Your job is to split the headers into three groups: 
Robot 1 columns, Robot 2 columns, and Robot 3 columns.

Analyze both the header names AND the sample data for clues about which robot a column belongs to.
Look for patterns like:
- Headers containing "Robot 1", "R1", etc.
- Similar columns that appear in groups for different robots (like "R1 Pickup", "R2 Pickup", "R3 Pickup")
- Sample data that indicates the column applies to specific robots

Return ONLY raw JSON:
{{
  "robot_1": ["Header 1", "Header 2", ...],
  "robot_2": ["Header 3", "Header 4", ...],
  "robot_3": ["Header 5", "Header 6", ...]
}}

Headers:
{headers}

{sample_data_str}
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
    
    # Generate insights about the data content
    prompt_insights = f"""
Analyze the headers and sample data to provide insights about what information is being collected and how it's structured.
Focus especially on fields that contain HOW robots perform actions rather than just what they do.

For example, fields like "Robot 1 tele pickup" with values like "ground intake", "human player", etc. tell us HOW
the robot is performing pickup actions, which is critical strategic information.

Provide your insights in the following JSON format:
{{
  "content_insights": [
    {{
      "header": "Header name",
      "tag": "mapped_tag",
      "values": ["sample value 1", "sample value 2"],
      "insight": "Description of what this data tells us about HOW robots perform actions"
    }},
    ...
  ],
  "strategic_insights": "Overall analysis of the most important strategic information in this dataset",
  "robot_comparison_fields": ["field1", "field2"] // Fields that would be most useful for comparing robots
}}

Headers and sample data:
{headers}

{sample_data_str}
"""

    try:
        # Call GPT for insights
        response_insights = await client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt_insights}],
            temperature=0.3,
            timeout=15
        )
        
        content_insights = response_insights.choices[0].message.content.strip()
        if content_insights.startswith("```json"):
            content_insights = content_insights[7:]
        if content_insights.startswith("```"):
            content_insights = content_insights[3:]
        if content_insights.endswith("```"):
            content_insights = content_insights[:-3]
            
        try:
            insights = eval(content_insights)
        except Exception as e:
            print("Insights parse error:", e)
            insights = {"error": "Failed to parse insights output."}
    except Exception as e:
        print("Error generating insights:", e)
        insights = {
            "content_insights": [],
            "strategic_insights": "Could not analyze data content.",
            "robot_comparison_fields": []
        }

    return mapping, offsets, insights
