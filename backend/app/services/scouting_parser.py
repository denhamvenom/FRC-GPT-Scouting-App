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

    match_mapping = get_match_mapping()
    scouting_data = {}

    # Debug: Print mapping to verify
    # print(f"Match mapping: {json.dumps(match_mapping, indent=2)}")

    for header in headers:
        if header not in match_mapping:
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
                    elif value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                        value = float(value)
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    pass
            
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
            scouting_data["team_number"] = int(team_number)
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