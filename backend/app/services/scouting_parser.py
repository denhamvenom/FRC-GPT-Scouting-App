# backend/app/services/scouting_parser.py

import os
import json
from typing import List, Dict, Any
from app.services.schema_loader import get_match_mapping


def parse_scouting_row(row: List[str], headers: List[str]) -> Dict[str, Any]:
    """
    Parses a single row from the Match Scouting sheet.

    Args:
        row (List[str]): The full list of cell values for the row.
        headers (List[str]): The full list of headers from A1:Z1.

    Returns:
        Dict[str, Any]: Structured scouting dictionary
    """

    # Get schema mapping - ensure schemas are loaded first
    from app.services.schema_loader import load_schemas
    
    # Load schemas if not already loaded
    if not get_match_mapping():
        try:
            load_schemas(2025)  # Default to 2025, should be configurable
        except Exception as e:
            print(f"Warning: Could not load schemas: {e}")
    
    schema_data = get_match_mapping()
    scouting_data = {}

    # Handle multiple possible formats of schema data
    match_mapping = {}

    # Check if the schema is directly a mapping dictionary
    if isinstance(schema_data, dict) and all(isinstance(k, str) for k in schema_data.keys()):
        match_mapping = schema_data
    # Check if it's the nested format with 'mappings' key
    elif (
        isinstance(schema_data, dict)
        and "mappings" in schema_data
        and "match" in schema_data["mappings"]
    ):
        match_mapping = schema_data["mappings"]["match"]

    print(f"\U0001f535 Schema structure: {type(schema_data)}")
    print(f"\U0001f535 Using mapping with {len(match_mapping)} entries")

    # Special handling for "Team Number" and "Qual Number" if they're missing from mapping
    if "Team Number" not in match_mapping:
        match_mapping["Team Number"] = "team_number"
    if "Qual Number" not in match_mapping:
        match_mapping["Qual Number"] = "match_number"

    for header in headers:
        if header not in match_mapping:
            # Try case-insensitive match
            matching_key = next(
                (k for k in match_mapping.keys() if k.lower() == header.lower()), None
            )
            if matching_key:
                header = matching_key
            else:
                # Handle common field names
                if "team" in header.lower() and "number" in header.lower():
                    match_mapping[header] = "team_number"
                elif (
                    "match" in header.lower() or "qual" in header.lower()
                ) and "number" in header.lower():
                    match_mapping[header] = "match_number"
                else:
                    # print(f"Header '{header}' not found in mapping")
                    continue

        mapped_field = match_mapping.get(header, "ignore")
        if mapped_field == "ignore":
            # print(f"Header '{header}' mapped to 'ignore'")
            continue

        try:
            index = headers.index(header)
            value = row[index] if index < len(row) else None

            # Try to convert numeric values to integers or floats
            if value is not None and isinstance(value, str):
                value = value.strip()
                try:
                    # Check if it's an integer
                    if value.isdigit():
                        value = int(value)
                    # Check if it's a float
                    elif value.replace(".", "", 1).isdigit() and value.count(".") < 2:
                        value = float(value)
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    pass

            # Check if there's a label mapping for enhanced field names
            enhanced_field_name = mapped_field
            try:
                # Load field metadata to get label mappings
                data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
                metadata_path = os.path.join(data_dir, "field_metadata_2025.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        field_metadata = json.load(f)
                    
                    if header in field_metadata and "label_mapping" in field_metadata[header]:
                        label_mapping = field_metadata[header]["label_mapping"]
                        if "label" in label_mapping:
                            enhanced_field_name = label_mapping["label"]
            except Exception as e:
                # If we can't load metadata, use the original field name
                pass

            scouting_data[enhanced_field_name] = value
            
            # Also store with original mapped field name for backwards compatibility
            if enhanced_field_name != mapped_field:
                scouting_data[mapped_field] = value

            # Special case for "qual_number" -> also store as "match_number" for compatibility
            if mapped_field == "qual_number" and "match_number" not in scouting_data:
                scouting_data["match_number"] = value
            # Special case for "match_number" -> also store as "qual_number" for compatibility
            elif mapped_field == "match_number" and "qual_number" not in scouting_data:
                scouting_data["qual_number"] = value

        except ValueError:
            continue

    # Only return entries that have a valid team_number
    team_number = scouting_data.get("team_number")
    if not team_number:
        return {}

    # Try to convert team_number to integer if it's a string
    if isinstance(team_number, str):
        try:
            # Remove emojis and non-digit characters, keeping only numbers
            import re
            clean_team_number = re.sub(r'[^\d]', '', team_number)
            if clean_team_number:
                scouting_data["team_number"] = int(clean_team_number)
            else:
                # If no digits found, keep original value
                pass
        except ValueError:
            # Keep as string if integer conversion fails
            pass

    # Ensure match_number and qual_number are present and consistent
    match_number = scouting_data.get("match_number")
    qual_number = scouting_data.get("qual_number")

    if match_number is not None and qual_number is None:
        scouting_data["qual_number"] = match_number
    elif qual_number is not None and match_number is None:
        scouting_data["match_number"] = qual_number

    return scouting_data


def parse_scouting_row_with_field_selections(row: List[str], headers: List[str], field_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a single row from the Match Scouting sheet using field_selections metadata.
    
    Args:
        row (List[str]): The full list of cell values for the row.
        headers (List[str]): The full list of headers from the Google Sheet.
        field_metadata (Dict[str, Any]): Field metadata from field_selections_{event_key}.json
        
    Returns:
        Dict[str, Any]: Structured scouting dictionary
    """
    scouting_data = {}
    
    if not field_metadata:
        print("🔴 No field metadata provided - cannot parse row")
        return {}
    
    # Extract critical mappings to identify team_number and match_number fields
    critical_mappings = {}
    if "critical_mappings" in field_metadata:
        for critical_field, header_list in field_metadata["critical_mappings"].items():
            for header_name in header_list:
                critical_mappings[header_name] = critical_field
    
    # Extract field selections for category and label mapping
    field_selections = field_metadata.get("field_selections", {})
    
    print(f"🔵 Processing row with {len(headers)} headers using field_selections")
    print(f"🔵 Critical mappings found: {critical_mappings}")
    print(f"🔵 Field selections available: {len(field_selections)}")
    
    for header in headers:
        try:
            index = headers.index(header)
            value = row[index] if index < len(row) else None
            
            # Skip empty values
            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue
            
            # Clean up the value
            if isinstance(value, str):
                value = value.strip()
                
                # Try to convert to appropriate type
                try:
                    if value.isdigit():
                        value = int(value)
                    elif value.replace(".", "", 1).isdigit() and value.count(".") < 2:
                        value = float(value)
                except (ValueError, TypeError):
                    pass  # Keep as string
            
            # Check if this is a critical field (team_number, match_number)
            if header in critical_mappings:
                mapped_field = critical_mappings[header]
                scouting_data[mapped_field] = value
                print(f"🔵 Mapped critical field: {header} -> {mapped_field} = {value}")
                continue
            
            # Check if this header is in field_selections
            if header in field_selections:
                field_info = field_selections[header]
                
                # Get the category for basic categorization
                category = field_info.get("category", "other")
                
                # Skip ignored fields
                if category == "ignore":
                    continue
                
                # Use enhanced label name if available
                if isinstance(field_info, dict) and "label_mapping" in field_info:
                    label_mapping = field_info["label_mapping"]
                    if isinstance(label_mapping, dict) and "label" in label_mapping:
                        enhanced_field_name = label_mapping["label"]
                        scouting_data[enhanced_field_name] = value
                        print(f"🔵 Enhanced field: {header} -> {enhanced_field_name} = {value}")
                        continue
                
                # Fallback to using header name with category prefix
                if category in ["auto", "teleop", "endgame", "strategy"]:
                    # Use original header as field name for basic categorization
                    scouting_data[header] = value
                    print(f"🔵 Basic field: {header} -> {header} = {value}")
            else:
                # Header not in field_selections - check for common patterns
                header_lower = header.lower()
                if "team" in header_lower and "number" in header_lower:
                    scouting_data["team_number"] = value
                    print(f"🔵 Pattern-matched team field: {header} -> team_number = {value}")
                elif ("match" in header_lower or "qual" in header_lower) and "number" in header_lower:
                    scouting_data["match_number"] = value
                    print(f"🔵 Pattern-matched match field: {header} -> match_number = {value}")
                else:
                    print(f"🟡 Unmapped header: {header}")
                    
        except (ValueError, IndexError) as e:
            print(f"🔴 Error processing header {header}: {e}")
            continue
    
    # Validate that we have required fields
    if "team_number" not in scouting_data:
        print(f"🔴 CRITICAL: No team_number found in parsed data")
        print(f"🔴 Available fields: {list(scouting_data.keys())}")
        return {}
    
    # Ensure team_number is an integer
    try:
        if isinstance(scouting_data["team_number"], str):
            # Remove any non-digit characters
            import re
            clean_team_number = re.sub(r'[^\d]', '', scouting_data["team_number"])
            if clean_team_number:
                scouting_data["team_number"] = int(clean_team_number)
    except (ValueError, TypeError):
        print(f"🔴 Could not convert team_number to int: {scouting_data['team_number']}")
        return {}
    
    # Ensure match_number consistency
    if "match_number" in scouting_data and "qual_number" not in scouting_data:
        scouting_data["qual_number"] = scouting_data["match_number"]
    elif "qual_number" in scouting_data and "match_number" not in scouting_data:
        scouting_data["match_number"] = scouting_data["qual_number"]
    
    print(f"🟢 Successfully parsed row: team={scouting_data.get('team_number')}, match={scouting_data.get('match_number')}")
    return scouting_data
