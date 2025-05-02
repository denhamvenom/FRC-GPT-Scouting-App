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
    if not manual_url:
        # No manual provided, return basic structure
        return {
            "scoring_objectives": [],
            "robot_capabilities": [],
            "alliance_strategy": [],
            "ranking_metrics": []
        }
    
    try:
        # Import necessary functions
        from app.services.manual_parser_service import fetch_pdf_from_url, extract_text_from_pdf
        
        # Download and extract text from the manual
        pdf_content = await fetch_pdf_from_url(manual_url)
        if not pdf_content:
            print(f"Failed to download manual from {manual_url}")
            return {
                "status": "error",
                "message": "Failed to download manual",
                "scoring_objectives": [],
                "robot_capabilities": [],
                "alliance_strategy": [],
                "ranking_metrics": []
            }
            
        manual_text = await extract_text_from_pdf(pdf_content)
        if not manual_text or len(manual_text) < 1000:
            print(f"Extracted text from manual is too short: {len(manual_text)} chars")
            return {
                "status": "error",
                "message": "Extracted text from manual is too short",
                "scoring_objectives": [],
                "robot_capabilities": [],
                "alliance_strategy": [],
                "ranking_metrics": []
            }
        
        # Use GPT to analyze the manual for strategic insights
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OpenAI API key not found")
            return {
                "status": "error",
                "message": "OpenAI API key not found",
                "scoring_objectives": [],
                "robot_capabilities": [],
                "alliance_strategy": [],
                "ranking_metrics": []
            }
        
        client = AsyncOpenAI(api_key=api_key)
        
        # Create a prompt for GPT to analyze the manual
        prompt = f"""
        Analyze this FIRST Robotics Competition (FRC) game manual for year {year} and extract strategic insights:
        
        1. Key scoring objectives in priority order
        2. Critical robot capabilities for this game
        3. Important alliance strategy considerations
        4. Key metrics to consider when ranking teams
        
        Return a JSON structure with these insights:
        
        {{
          "scoring_objectives": [
            {{ "name": "objective name", "description": "brief description", "priority": "high/medium/low", "points": "point value if known" }}
          ],
          "robot_capabilities": [
            {{ "capability": "capability name", "importance": "high/medium/low", "reason": "why this matters" }}
          ],
          "alliance_strategy": [
            {{ "strategy": "strategy description", "scenario": "when to use" }}
          ],
          "ranking_metrics": [
            {{ "metric": "metric name", "reason": "why this is important for ranking teams" }}
          ]
        }}
        
        Game Manual Text (excerpt):
        {manual_text[:15000]}  # Use first 15K chars
        """
        
        # Call GPT-4 to analyze the manual
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["status"] = "success"
        
        return result
        
    except Exception as e:
        print(f"Error analyzing manual: {e}")
        return {
            "status": "error",
            "message": str(e),
            "scoring_objectives": [],
            "robot_capabilities": [],
            "alliance_strategy": [],
            "ranking_metrics": []
        }

async def build_picklist_from_unified_data(
    unified_dataset_path: str,
    first_pick_priorities: List[str],
    second_pick_priorities: List[str],
    third_pick_priorities: Optional[List[str]] = None,
    manual_url: Optional[str] = None
) -> List[Dict]:
    """
    Builds a ranked picklist based on strategic priorities and scouting data.

    Args:
        unified_dataset_path: Path to the unified event dataset JSON
        first_pick_priorities: Ranked traits for first pick
        second_pick_priorities: Ranked traits for second pick
        third_pick_priorities: Ranked traits for third pick (optional)
        manual_url: URL to the game manual (optional)

    Returns:
        List[Dict]: Ranked list of teams with reasoning
    """
    # Load unified dataset
    with open(unified_dataset_path, "r", encoding="utf-8") as f:
        unified_data = json.load(f)
    
    # Extract key data
    teams_data = unified_data.get("teams", {})
    year = unified_data.get("year", datetime.now().year)
    
    # Get game insights if manual URL is provided
    game_insights = {}
    if manual_url:
        game_insights = await analyze_game_manual_for_strategy(manual_url, year)
    
    # Construct GPT prompt
    system_prompt = """
You are an expert FRC alliance strategy advisor with deep knowledge of robotics competitions.
You will help rank teams based on scouting data and specific strategic desires for 1st, 2nd, and 3rd picks.
Use the following priorities for each pick and the provided team data to recommend a pick order.

ONLY output valid JSON in this format:
[
  {
    "team_number": 8044,
    "score": 95,
    "reasoning": "Excellent auto, top scorer, fast climber"
  },
  ...
]

Focus heavily on matching the FIRST PICK priorities for top selections.
The SECOND PICK should complement the first pick and consider defensive capabilities.
The THIRD PICK (if applicable) should focus on flexibility or backup roles.

Weight recent matches more heavily than early-season performance.
Take into account consistency and trend of performance.
Consider alliance synergy when making recommendations.
"""

    # Build the full prompt with context
    pick_priorities = {
        "first_pick_priorities": first_pick_priorities,
        "second_pick_priorities": second_pick_priorities,
    }
    
    if third_pick_priorities:
        pick_priorities["third_pick_priorities"] = third_pick_priorities
    
    # Add game insights if available
    if game_insights and game_insights.get("status") == "success":
        pick_priorities["game_insights"] = {
            "scoring_objectives": game_insights.get("scoring_objectives", []),
            "robot_capabilities": game_insights.get("robot_capabilities", []),
            "alliance_strategy": game_insights.get("alliance_strategy", [])
        }
    
    # Add summarized team data
    summarized_teams = {}
    for team_number, team_data in teams_data.items():
        scouting_data = team_data.get("scouting_data", [])
        superscouting_data = team_data.get("superscouting_data", [])
        statbotics_info = team_data.get("statbotics_info", {})
        
        # Calculate some basic metrics
        match_count = len(scouting_data)
        if match_count == 0:
            continue  # Skip teams with no scouting data
            
        # Extract all numeric fields
        numeric_metrics = {}
        for match in scouting_data:
            for key, value in match.items():
                try:
                    if key not in ["team_number", "qual_number", "match_number", "comments"]:
                        val = float(value) if value else 0
                        if key not in numeric_metrics:
                            numeric_metrics[key] = []
                        numeric_metrics[key].append(val)
                except (ValueError, TypeError):
                    pass  # Not a numeric field
        
        # Calculate averages
        avg_metrics = {}
        for key, values in numeric_metrics.items():
            if values:
                avg_metrics[key] = sum(values) / len(values)
        
        # Get EPA data if available
        epa_data = {}
        for key, value in statbotics_info.items():
            if key.startswith("epa_") and value is not None:
                epa_data[key] = value
        
        # Combine into summary
        summarized_teams[team_number] = {
            "nickname": team_data.get("nickname", ""),
            "match_count": match_count,
            "average_metrics": avg_metrics,
            "epa_data": epa_data,
            "recent_matches": scouting_data[-3:] if len(scouting_data) >= 3 else scouting_data,
            "superscouting_notes": [note.get("strategy_notes", "") for note in superscouting_data if "strategy_notes" in note]
        }
    
    user_prompt = {
        "pick_priorities": pick_priorities,
        "teams_data": summarized_teams
    }

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
        
    client = OpenAI(api_key=api_key)

    # Make the API call
    response = client.chat.completions.create(
        model="gpt-4o",  # Use "gpt-4" or "gpt-4o" depending on your access
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt)}
        ],
        temperature=0.2,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )

    output_text = response.choices[0].message.content
    try:
        picklist = json.loads(output_text)
        
        # Add timestamp and creation info
        result = {
            "picklist": picklist,
            "metadata": {
                "created": datetime.now().isoformat(),
                "first_pick_priorities": first_pick_priorities,
                "second_pick_priorities": second_pick_priorities,
                "third_pick_priorities": third_pick_priorities if third_pick_priorities else []
            }
        }
        
        # Save the picklist to a file for reference
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        event_key = os.path.basename(unified_dataset_path).replace("unified_event_", "").replace(".json", "")
        picklist_path = os.path.join(data_dir, f"picklist_{event_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(picklist_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        
        return picklist
    except json.JSONDecodeError:
        raise ValueError("Failed to parse GPT output as JSON.")

async def get_team_stats_for_picklist(unified_dataset_path: str, team_number: int) -> Dict[str, Any]:
    """
    Get detailed team statistics for picklist display.
    
    Args:
        unified_dataset_path: Path to the unified event dataset JSON
        team_number: Team number to get stats for
        
    Returns:
        Dict containing team statistics and performance metrics
    """
    # Load unified dataset
    with open(unified_dataset_path, "r", encoding="utf-8") as f:
        unified_data = json.load(f)
    
    teams_data = unified_data.get("teams", {})
    
    # Check if team exists
    if str(team_number) not in teams_data:
        return {"status": "error", "message": f"Team {team_number} not found in dataset"}
    
    team_data = teams_data[str(team_number)]
    scouting_data = team_data.get("scouting_data", [])
    
    # Get field categories from metadata
    field_categories = unified_data.get("metadata", {}).get("field_categories", {})
    
    # Group metrics by category
    category_metrics = {
        "team_info": {},
        "auto": {},
        "teleop": {},
        "endgame": {},
        "strategy": {},
        "other": {}
    }
    
    # Calculate metrics for each field
    for match in scouting_data:
        for field, value in match.items():
            if field in ["team_number", "qual_number", "match_number", "comments"]:
                continue
                
            # Get category for this field
            category = field_categories.get(field, "other")
            
            # Try to convert to numeric
            try:
                val = float(value) if value else 0
                if field not in category_metrics[category]:
                    category_metrics[category][field] = []
                category_metrics[category][field].append(val)
            except (ValueError, TypeError, KeyError):
                # Handle non-numeric or category doesn't exist
                pass
    
    # Calculate averages and other stats
    stats = {
        "team_number": team_number,
        "nickname": team_data.get("nickname", ""),
        "match_count": len(scouting_data),
        "metrics": {}
    }
    
    for category, fields in category_metrics.items():
        category_stats = {}
        for field, values in fields.items():
            if values:
                category_stats[field] = {
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "values": values
                }
        stats["metrics"][category] = category_stats
    
    # Add EPA data if available
    if "statbotics_info" in team_data:
        stats["epa"] = {k: v for k, v in team_data["statbotics_info"].items() if k.startswith("epa_")}
        
    # Add ranking info if available
    if "ranking_info" in team_data:
        stats["ranking"] = team_data["ranking_info"]
        
    # Add match history
    stats["match_history"] = scouting_data
    
    return stats