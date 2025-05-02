# backend/app/services/superscout_parser.py

import os
import json
from typing import List, Dict, Any

# Determine project structure paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Initialize with empty values - will be populated later
FIELD_MAPPING = {}
ROBOT_GROUPS = {
    "robot_1": [],
    "robot_2": [],
    "robot_3": []
}

def load_superscout_config() -> tuple:
    """
    Load the superscouting schema mappings and robot group configuration.
    
    Returns:
        tuple: (field_mapping, robot_groups)
    """
    try:
        # Load field mapping schema
        schema_path = os.path.join(DATA_DIR, "schema_superscout_2025.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            field_mapping = json.load(f)
    except FileNotFoundError:
        print(f"Warning: SuperScouting schema not found at: {schema_path}")
        field_mapping = {}
    
    try:
        # Load robot groups configuration
        groups_path = os.path.join(DATA_DIR, "robot_groups_2025.json")
        with open(groups_path, "r", encoding="utf-8") as f:
            robot_groups = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Robot groups not found at: {groups_path}")
        robot_groups = {
            "robot_1": [],
            "robot_2": [],
            "robot_3": []
        }
    
    return field_mapping, robot_groups

# Load configuration on module import
try:
    FIELD_MAPPING, ROBOT_GROUPS = load_superscout_config()
except Exception as e:
    print(f"Warning: Could not load superscout configuration: {e}")

def parse_superscout_row(row: List[str], headers: List[str]) -> List[Dict[str, Any]]:
    """
    Parses a single row from the SuperScouting sheet into three robot-specific scouting entries.
    
    Args:
        row (List[str]): The full list of cell values for the row.
        headers (List[str]): The full list of headers from A1:Z1.

    Returns:
        List[Dict[str, Any]]: Up to three structured robot scouting dictionaries.
    """
    # If configuration hasn't been loaded yet, load it now
    global FIELD_MAPPING, ROBOT_GROUPS
    if not FIELD_MAPPING:
        FIELD_MAPPING, ROBOT_GROUPS = load_superscout_config()

    # Prepare data for all three robots
    robot_entries = []
    
    # Check if we have any robot groupings
    has_robot_groups = any(len(group) > 0 for group in ROBOT_GROUPS.values())
    
    if has_robot_groups:
        # Process data for each robot group
        for robot_label, robot_headers in ROBOT_GROUPS.items():
            robot_data = {}
            
            # Find common fields that apply to all robots
            common_headers = [h for h in headers if h not in 
                             ROBOT_GROUPS["robot_1"] + 
                             ROBOT_GROUPS["robot_2"] + 
                             ROBOT_GROUPS["robot_3"]]
            
            # Process common fields first (like match number)
            for header in common_headers:
                if header not in FIELD_MAPPING:
                    continue  # Ignore unmapped fields
                
                mapped_field = FIELD_MAPPING.get(header, "ignore")
                if mapped_field == "ignore":
                    continue  # Skip irrelevant fields
                
                try:
                    index = headers.index(header)
                    value = row[index] if index < len(row) else None
                    
                    # Try to convert numeric values
                    if value is not None and isinstance(value, str):
                        try:
                            if value.isdigit():
                                value = int(value)
                            elif value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                                value = float(value)
                        except (ValueError, TypeError):
                            pass
                            
                    robot_data[mapped_field] = value
                except ValueError:
                    continue
            
            # Process robot-specific fields
            for header in robot_headers:
                if header not in FIELD_MAPPING:
                    continue  # Ignore unmapped fields
                
                mapped_field = FIELD_MAPPING.get(header, "ignore")
                if mapped_field == "ignore":
                    continue  # Skip irrelevant fields
                
                try:
                    index = headers.index(header)
                    value = row[index] if index < len(row) else None
                    
                    # Try to convert numeric values
                    if value is not None and isinstance(value, str):
                        try:
                            if value.isdigit():
                                value = int(value)
                            elif value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                                value = float(value)
                        except (ValueError, TypeError):
                            pass
                            
                    robot_data[mapped_field] = value
                except ValueError:
                    continue
            
            # Ensure team_number is present and valid
            if "team_number" in robot_data and robot_data["team_number"] is not None:
                # Make sure team_number is an integer if possible
                try:
                    if isinstance(robot_data["team_number"], str):
                        robot_data["team_number"] = int(robot_data["team_number"])
                except ValueError:
                    pass
                
                # Add robot identifier for later reference
                robot_data["robot_group"] = robot_label
                    
                robot_entries.append(robot_data)
    else:
        # Legacy mode - process as a single entry
        robot_data = {}
        
        for header in headers:
            if header not in FIELD_MAPPING:
                continue  # Ignore unmapped fields
            
            mapped_field = FIELD_MAPPING.get(header, "ignore")
            if mapped_field == "ignore":
                continue  # Skip irrelevant fields
            
            try:
                index = headers.index(header)
                value = row[index] if index < len(row) else None
                robot_data[mapped_field] = value
            except ValueError:
                continue
        
        # Only add robot data if a valid team_number exists
        if "team_number" in robot_data and robot_data["team_number"] is not None:
            # Make sure team_number is an integer if possible
            try:
                if isinstance(robot_data["team_number"], str):
                    robot_data["team_number"] = int(robot_data["team_number"])
            except ValueError:
                pass
                
            robot_entries.append(robot_data)
    
    return robot_entries