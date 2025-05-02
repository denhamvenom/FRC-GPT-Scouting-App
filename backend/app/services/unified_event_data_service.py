# backend/app/services/unified_event_data_service.py

import os
import json
from typing import List, Dict, Any, Optional

from app.services.schema_loader import load_schemas
from app.services.scouting_parser import parse_scouting_row
from app.services.superscout_parser import parse_superscout_row
from app.services.tba_client import get_event_teams, get_event_matches, get_event_rankings
from app.services.statbotics_client import get_team_epa
from app.services.sheets_service import get_sheet_values

def get_unified_dataset_path(event_key: str) -> str:
    """
    Get the path for a unified dataset based on the event key.
    
    Args:
        event_key: The event key, e.g., "2025arc"
        
    Returns:
        str: The full path to the unified dataset JSON file
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    return os.path.join(data_dir, f"unified_event_{event_key}.json")

def sanitize_for_json(obj: Any) -> Any:
    """
    Sanitize values for safe JSON serialization.
    
    Args:
        obj: Any Python object to sanitize
        
    Returns:
        The sanitized object with None values replaced with empty strings
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif obj is None:
        return ""
    else:
        return obj

async def build_unified_dataset(
    event_key: str, 
    year: int, 
    force_rebuild: bool = False,
    scouting_tab: str = "Scouting", 
    superscout_tab: str = "SuperScouting"
) -> str:
    """
    Build a unified dataset combining scouting data, TBA data, and Statbotics data.
    
    Args:
        event_key: The event key, e.g., "2025arc"
        year: The season year, e.g., 2025
        force_rebuild: Whether to rebuild even if dataset already exists
        scouting_tab: Name of the scouting tab in Google Sheets
        superscout_tab: Name of the superscouting tab in Google Sheets
        
    Returns:
        str: Path to the unified dataset JSON file
    """
    print(f"\U0001F535 Loading schemas for {year}")
    load_schemas(year)
    
    # Check if dataset already exists and if we should rebuild
    output_path = get_unified_dataset_path(event_key)
    if os.path.exists(output_path) and not force_rebuild:
        print(f"\u2705 Using existing unified dataset: {output_path}")
        return output_path

    # 1. Parse Match Scouting Data
    print("\U0001F535 Fetching Match Scouting data...")
    scouting_raw = await get_sheet_values(f"{scouting_tab}!A1:ZZ")
    headers = scouting_raw[0] if scouting_raw else []
    scouting_rows = scouting_raw[1:] if scouting_raw else []

    scouting_parsed = []
    for row in scouting_rows:
        parsed = parse_scouting_row(row, headers)
        if parsed:
            # Ensure match_number is present and is an integer
            if "match_number" in parsed and parsed["match_number"] is not None:
                try:
                    parsed["match_number"] = int(parsed["match_number"])
                except (ValueError, TypeError):
                    pass  # Keep as is if conversion fails
            if "qual_number" in parsed and parsed["qual_number"] is not None:
                try:
                    parsed["qual_number"] = int(parsed["qual_number"])
                except (ValueError, TypeError):
                    pass  # Keep as is if conversion fails
                    
            # Ensure team_number is an integer
            if "team_number" in parsed and parsed["team_number"] is not None:
                try:
                    parsed["team_number"] = int(parsed["team_number"])
                except (ValueError, TypeError):
                    pass  # Keep as is if conversion fails
                    
            scouting_parsed.append(parsed)

    # 2. Parse SuperScouting Data
    print("\U0001F535 Fetching SuperScouting data...")
    superscouting_raw = await get_sheet_values(f"{superscout_tab}!A1:ZZ")
    superscouting_headers = superscouting_raw[0] if superscouting_raw else []
    superscouting_rows = superscouting_raw[1:] if superscouting_raw else []

    superscouting_parsed = []
    for row in superscouting_rows:
        parsed_robots = parse_superscout_row(row, superscouting_headers)
        
        # Each row can generate multiple robot entries due to robot grouping
        for robot_data in parsed_robots:
            # Only include entries with valid team numbers
            if "team_number" in robot_data and robot_data["team_number"]:
                # Ensure match_number is present if available
                if "match_number" in robot_data and robot_data["match_number"] is not None:
                    try:
                        robot_data["match_number"] = int(robot_data["match_number"])
                    except (ValueError, TypeError):
                        pass
                        
                # Ensure qual_number is present if available
                if "qual_number" in robot_data and robot_data["qual_number"] is not None:
                    try:
                        robot_data["qual_number"] = int(robot_data["qual_number"])
                    except (ValueError, TypeError):
                        pass
                
                # Add to parsed data
                superscouting_parsed.append(robot_data)

    # 3. Pull TBA Data
    print("\U0001F535 Fetching TBA Teams, Matches, Rankings...")
    event_teams = await get_event_teams(event_key)
    event_matches = await get_event_matches(event_key)
    event_rankings = await get_event_rankings(event_key)

    # 3.5 Build Expected Match List
    expected_matches = []

    for match in event_matches:
        if match.get("comp_level") == "qm":  # Only qualification matches
            match_number = match.get("match_number")
            alliances = match.get("alliances", {})

            for color in ["blue", "red"]:
                teams = alliances.get(color, {}).get("team_keys", [])
                for team_key in teams:
                    if team_key.startswith("frc"):
                        team_number = int(team_key[3:])
                        expected_matches.append({
                            "match_number": match_number,
                            "team_number": team_number,
                            "alliance_color": color
                        })
    
    # Debug info about expected matches
    print(f"\U0001F535 Built {len(expected_matches)} expected match-team combinations")

    # 4. Pull Statbotics Data for each team
    print("\U0001F535 Fetching Statbotics EPA data...")
    statbotics_data = {}
    
    for team in event_teams:
        team_number = team.get("team_number")
        try:
            team_stats = get_team_epa(team_number, year)
            if team_stats:
                statbotics_data[team_number] = team_stats
        except Exception as e:
            print(f"Error fetching Statbotics data for team {team_number}: {e}")

    # 5. Merge all data
    print("\U0001F7E2 Merging datasets...")
    unified_data = {}

    for team in event_teams:
        team_number = team.get("team_number")
        team_key = f"frc{team_number}"

        # Get team's scouting data - ensure we're using string versions of team_number for comparison
        team_scouting = [
            r for r in scouting_parsed 
            if str(r.get("team_number")) == str(team_number)
        ]
        
        # Get team's superscouting data
        team_superscouting = [
            r for r in superscouting_parsed 
            if str(r.get("team_number")) == str(team_number)
        ]
        
        # Get team's statbotics data
        team_statbotics = statbotics_data.get(team_number, {})
        
        # Get team's ranking data
        team_ranking = next(
            (r for r in event_rankings.get("rankings", []) if r.get("team_key") == team_key), 
            {}
        ) if event_rankings else {}

        unified_data[str(team_number)] = {
            "team_number": team_number,
            "nickname": team.get("nickname"),
            "scouting_data": team_scouting,
            "superscouting_data": team_superscouting,
            "tba_info": team,
            "statbotics_info": team_statbotics,
            "ranking_info": team_ranking
        }

    # 6. Save unified data locally
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    output_payload = {
        "event_key": event_key,
        "year": year,
        "expected_matches": expected_matches,
        "teams": sanitize_for_json(unified_data),
        "metadata": {
            "scouting_headers": headers,
            "superscouting_headers": superscouting_headers,
            "created_timestamp": __import__('datetime').datetime.now().isoformat(),
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\u2705 Unified dataset saved to: {output_path}")
    print(f"\u2705 Dataset contains {len(expected_matches)} expected match-team combinations")
    print(f"\u2705 Dataset contains {len(unified_data)} teams")

    return output_path