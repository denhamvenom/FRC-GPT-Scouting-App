# backend/app/services/picklist_service.py

import json
import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, OpenAI
from datetime import datetime

async def analyze_game_manual_for_strategy(manual_url: Optional[str], year: int) -> Dict[str, Any]:
    """
    Analyze game manual to extract strategic insights for picklist generation.
    
    Args:
        manual_url: URL to the game manual PDF
        year: FRC season year
        
    Returns:
        Dict containing strategic insights
    """
    # Download and extract text from the PDF
    if not manual_url:
        return {"status": "no_manual"}
    try:
        # Example: use httpx or aiohttp to fetch PDF bytes
        import httpx
        resp = httpx.get(manual_url)
        resp.raise_for_status()
        pdf_content = resp.content
    except Exception as e:
        print(f"Failed to download manual from {manual_url}: {e}")
        return {
            "status": "error",
            "message": "Failed to download manual",
            "scoring_objectives": [],
            "robot_capabilities": [],
            "alliance_strategy": [],
            "ranking_metrics": []
        }
    
    # Extract text (stubbed out)
    from .pdf_utils import extract_text_from_pdf
    manual_text = await extract_text_from_pdf(pdf_content)
    if not manual_text or len(manual_text) < 1000:
        print(f"Extracted text from manual is too short: {len(manual_text)} chars")
        return {
            "status": "error",
            "message": "Extracted manual text too short",
            "scoring_objectives": [],
            "robot_capabilities": [],
            "alliance_strategy": [],
            "ranking_metrics": []
        }
    
    # TODO: parse manual_text for sections, goals, and objectives
    insights = {
        "status": "success",
        "scoring_objectives": [],
        "robot_capabilities": [],
        "alliance_strategy": [],
        "ranking_metrics": []
    }
    return insights


async def generate_picklist(
    unified_dataset_path: str,
    first_pick_priorities: List[str],
    second_pick_priorities: List[str],
    third_pick_priorities: List[str],
    manual_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate picklist recommendations based on unified dataset and priorities.
    """
    # Load unified dataset
    with open(unified_dataset_path, "r", encoding="utf-8") as f:
        unified_data = json.load(f)

    # Extract key data
    teams_data = unified_data.get("teams", {})
    year = unified_data.get("year", datetime.now().year)

    # Analyze game manual if provided
    game_insights: Dict[str, Any] = {}
    if manual_url:
        game_insights = await analyze_game_manual_for_strategy(manual_url, year)

    # Summarize per-team metrics
    summarized_teams: Dict[int, Dict[str, Any]] = {}
    for team_number, team_data in teams_data.items():
        scouting_data = team_data.get("scouting_data", [])
        # skip teams with no scouting data
        if not scouting_data:
            continue

        superscouting_data = team_data.get("superscouting_data", [])
        statbotics_info = team_data.get("statbotics_info", {})

        # Calculate some basic metrics
        match_count = len(scouting_data)
        # (we know match_count > 0)

        # Extract all numeric fields
        numeric_metrics: Dict[str, List[float]] = {}
        for match in scouting_data:
            for key, value in match.items():
                if key in ["team_number", "qual_number", "match_number", "comments"]:
                    continue
                try:
                    val = float(value) if value is not None else 0.0
                    numeric_metrics.setdefault(key, []).append(val)
                except (ValueError, TypeError):
                    # non-numeric field
                    pass

        # Compute averages and other stats
        avg_metrics: Dict[str, float] = {}
        for key, values in numeric_metrics.items():
            if values:
                avg_metrics[key] = sum(values) / len(values)

        # EPA data
        epa_data: Dict[str, Any] = {}
        for key, value in statbotics_info.items():
            if key.startswith("epa_") and value is not None:
                epa_data[key] = value

        # Ranking info
        ranking_info = team_data.get("ranking_info", {})

        # Build summary
        summarized_teams[team_number] = {
            "match_count": match_count,
            "averages": avg_metrics,
            "epa": epa_data,
            "ranking": ranking_info,
            "scoring_summary": {
                "total_score": sum(avg_metrics.values()),
                "component_scores": avg_metrics
            },
            # include any superscouting notes
            "superscouting_notes": [note.get("strategy_notes", "") for note in superscouting_data if "strategy_notes" in note]
        }

    # Construct OpenAI system + user prompt
    system_prompt = (
        "You are an expert FRC alliance strategy advisor. "
        "Given team scouting summaries and pick priorities, rank the teams for first, second, and third pick."
    )

    pick_priorities: Dict[str, Any] = {
        "first_pick_priorities": first_pick_priorities,
        "second_pick_priorities": second_pick_priorities
    }
    if third_pick_priorities:
        pick_priorities["third_pick_priorities"] = third_pick_priorities
    if game_insights.get("status") == "success":
        pick_priorities["game_insights"] = game_insights

    user_prompt: Dict[str, Any] = {
        "pick_priorities": pick_priorities,
        "teams_data": summarized_teams
    }

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found")
    client = OpenAI(api_key=api_key)

    # Call OpenAI (synchronous for example; switch to async as needed)
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt)}
        ],
        temperature=0.2,
        max_tokens=1500
    )

    # Parse response
    try:
        picklist = json.loads(response.choices[0].message.content)
    except Exception:
        raise ValueError(f"Invalid response format: {response.choices[0].message.content}")

    # Return picklist array
    return picklist
