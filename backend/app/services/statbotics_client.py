# backend/app/services/statbotics_client.py

import json
import os
from typing import Dict, Any
from statbotics import Statbotics

# Initialize Statbotics client
sb = Statbotics()

# Base directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "config"))

def load_statbotics_field_map(year: int) -> Dict[str, str]:
    """
    Loads the field map configuration for the given year.
    """
    config_path = os.path.join(CONFIG_DIR, f"statbotics_field_map_{year}.json")
    default_path = os.path.join(CONFIG_DIR, "statbotics_field_map_DEFAULT.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(default_path, "r", encoding="utf-8") as f:
            return json.load(f)

def get_nested_value(data: Dict, path: str) -> Any:
    """
    Gets a nested value from a dictionary using a dotted path.
    """
    keys = path.split(".")
    for key in keys:
        data = data.get(key, {})
    return data if data != {} else None

def get_team_epa(team_key: int, year: int) -> Dict[str, Any]:
    """
    Pulls EPA and match-relevant breakdown for a team in a given year.
    Returns a slimmed dictionary based on the field map.
    """
    try:
        raw_data = sb.get_team_year(team_key, year)
        field_map = load_statbotics_field_map(year)

        slimmed_data = {
            "team_number": raw_data.get("team"),
            "team_name": raw_data.get("name")
        }

        for output_field, statbotics_path in field_map.items():
            value = get_nested_value(raw_data, statbotics_path)
            slimmed_data[output_field] = value

        return slimmed_data

    except Exception as e:
        print(f"❌ Error fetching EPA for {team_key} in {year}: {e}")
        return {}
