# backend/app/services/superscout_parser_enhanced.py

import os
import json
import re
from typing import List, Dict, Any

# Determine project structure paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Initialize with empty values - will be populated later
FIELD_MAPPING = {}
ROBOT_GROUPS = {"robot_1": [], "robot_2": [], "robot_3": []}


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
            print(f"Loaded superscouting schema with {len(field_mapping)} mappings")
    except FileNotFoundError:
        print(f"Warning: SuperScouting schema not found at: {schema_path}")
        field_mapping = {}

    try:
        # Try both possible file names for robot groups
        robot_groups = {}
        for filename in ["robot_groups_2025.json", "field_selections_2025.json"]:
            groups_path = os.path.join(DATA_DIR, filename)
            if os.path.exists(groups_path):
                with open(groups_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Check if the file is the field_selections format
                    if "robot_groups" in data:
                        robot_groups = data["robot_groups"]
                        print(
                            f"Loaded robot groups from {filename} with {sum(len(g) for g in robot_groups.values())} total fields"
                        )
                        break
                    else:
                        robot_groups = data
                        print(
                            f"Loaded robot groups from {filename} with {sum(len(g) for g in robot_groups.values())} total fields"
                        )
                        break
    except FileNotFoundError:
        print("Warning: Robot groups not found in data directory")
        robot_groups = {"robot_1": [], "robot_2": [], "robot_3": []}
    except Exception as e:
        print(f"Error loading robot groups: {e}")
        robot_groups = {"robot_1": [], "robot_2": [], "robot_3": []}

    return field_mapping, robot_groups


# Load configuration on module import
try:
    FIELD_MAPPING, ROBOT_GROUPS = load_superscout_config()
except Exception as e:
    print(f"Warning: Could not load superscout configuration: {e}")


def parse_superscout_row(row: List[str], headers: List[str]) -> List[Dict[str, Any]]:
    """
    Parses a single row from the SuperScouting sheet into three robot-specific scouting entries.
    ENHANCED VERSION: Auto-generates robot field mappings for all three robots.

    Args:
        row (List[str]): The full list of cell values for the row.
        headers (List[str]): The full list of headers from A1:Z1.

    Returns:
        List[Dict[str, Any]]: Three structured robot scouting dictionaries.
    """
    # If configuration hasn't been loaded yet, load it now
    global FIELD_MAPPING, ROBOT_GROUPS
    if not FIELD_MAPPING:
        FIELD_MAPPING, ROBOT_GROUPS = load_superscout_config()

    # Prepare data for all three robots
    robot_entries = []

    # Auto-generate robot groups for all three robots
    auto_robot_groups = generate_auto_robot_groups(headers)

    # Process data for each robot (1, 2, 3)
    for robot_num in range(1, 4):
        robot_label = f"robot_{robot_num}"
        robot_data = {}

        # Add a field for storing categorization data
        robot_data["field_types"] = {}

        # Get robot-specific headers for this robot
        robot_headers = auto_robot_groups.get(robot_label, [])

        # Process all fields that apply to this robot
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
                        elif value.replace(".", "", 1).isdigit() and value.count(".") < 2:
                            value = float(value)
                    except (ValueError, TypeError):
                        pass

                # Create a standardized field key
                field_key = header.replace(" ", "_").lower()

                # Store the actual data
                robot_data[field_key] = value

                # Store the field type for categorization
                robot_data["field_types"][field_key] = mapped_field

                # For team_number and match_number, also store them under standardized keys
                if mapped_field in ["team_number", "match_number"]:
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

    return robot_entries


def generate_auto_robot_groups(headers: List[str]) -> Dict[str, List[str]]:
    """
    Automatically generates robot groups by detecting robot-specific patterns
    or assigning all fields to all robots if no patterns are found.
    
    Args:
        headers: List of header names from the superscouting sheet
        
    Returns:
        Dictionary mapping robot labels to their field lists
    """
    auto_groups = {
        "robot_1": [],
        "robot_2": [],
        "robot_3": []
    }
    
    # Try to detect existing robot patterns first
    robot_patterns = [
        [re.compile(r'robot\s*1|r1\b', re.IGNORECASE), re.compile(r'robot\s*2|r2\b', re.IGNORECASE), re.compile(r'robot\s*3|r3\b', re.IGNORECASE)],
        [re.compile(r'\b1\s*[-_]'), re.compile(r'\b2\s*[-_]'), re.compile(r'\b3\s*[-_]')],
        [re.compile(r'_1_'), re.compile(r'_2_'), re.compile(r'_3_')],
        [re.compile(r'\b1\b'), re.compile(r'\b2\b'), re.compile(r'\b3\b')]  # More general pattern
    ]
    
    pattern_found = False
    for pattern_set in robot_patterns:
        r1_headers = [h for h in headers if pattern_set[0].search(h)]
        r2_headers = [h for h in headers if pattern_set[1].search(h)]
        r3_headers = [h for h in headers if pattern_set[2].search(h)]
        
        # If we found substantial matches for at least two robots, use this pattern
        if len(r1_headers) > 0 and len(r2_headers) > 0:
            auto_groups["robot_1"] = r1_headers
            auto_groups["robot_2"] = r2_headers
            auto_groups["robot_3"] = r3_headers
            pattern_found = True
            print(f"Auto-detected robot pattern: R1={len(r1_headers)}, R2={len(r2_headers)}, R3={len(r3_headers)} fields")
            break
    
    # If no patterns found, assign ALL superscouting fields to ALL robots
    if not pattern_found:
        print(f"No robot patterns detected. Assigning all {len(headers)} fields to all 3 robots.")
        for robot_label in auto_groups.keys():
            auto_groups[robot_label] = headers.copy()
    
    return auto_groups
