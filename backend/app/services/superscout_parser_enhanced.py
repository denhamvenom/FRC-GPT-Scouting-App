# backend/app/services/superscout_parser_enhanced.py

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
                        print(f"Loaded robot groups from {filename} with {sum(len(g) for g in robot_groups.values())} total fields")
                        break
                    else:
                        robot_groups = data
                        print(f"Loaded robot groups from {filename} with {sum(len(g) for g in robot_groups.values())} total fields")
                        break
    except FileNotFoundError:
        print(f"Warning: Robot groups not found in data directory")
        robot_groups = {
            "robot_1": [],
            "robot_2": [],
            "robot_3": []
        }
    except Exception as e:
        print(f"Error loading robot groups: {e}")
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
    ENHANCED VERSION: Preserves both field types and original headers for better data context.
    
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
    
    # Store insights about the data for later reference
    robot_insights = {}
    field_categories = {}
    
    if has_robot_groups:
        # Process data for each robot group
        for robot_label, robot_headers in ROBOT_GROUPS.items():
            robot_data = {}
            
            # Add a field for storing categorization data
            robot_data["field_types"] = {}
            
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
                    
                    # Create a key that combines the mapped field type and the original field name
                    # This preserves both categorization and specific field identity
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
                    
                    # Create a key that combines the mapped field type and the original field name
                    # This preserves both categorization and specific field identity
                    field_key = header.replace(" ", "_").lower()
                    
                    # Store the actual data
                    robot_data[field_key] = value
                    
                    # Store the field type for categorization
                    robot_data["field_types"][field_key] = mapped_field
                    
                    # For team_number, also store it under standardized key
                    if mapped_field == "team_number":
                        robot_data["team_number"] = value
                    
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
        
        # Add a field for storing categorization data
        robot_data["field_types"] = {}
        
        for header in headers:
            if header not in FIELD_MAPPING:
                continue  # Ignore unmapped fields
            
            mapped_field = FIELD_MAPPING.get(header, "ignore")
            if mapped_field == "ignore":
                continue  # Skip irrelevant fields
            
            try:
                index = headers.index(header)
                value = row[index] if index < len(row) else None
                
                # Create a key that combines the mapped field type and the original field name
                field_key = header.replace(" ", "_").lower()
                
                # Store the actual data
                robot_data[field_key] = value
                
                # Store the field type for categorization
                robot_data["field_types"][field_key] = mapped_field
                
                # For critical fields, also store them under standardized keys
                if mapped_field in ["team_number", "match_number"]:
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