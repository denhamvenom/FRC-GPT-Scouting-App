"""
JSON utilities for picklist service.

Provides JSON compression, validation, and ultra-compact formatting
for token optimization in GPT responses.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class JSONCompressor:
    """
    Compresses JSON data for token optimization.
    
    Reduces token usage by:
    - Removing unnecessary whitespace
    - Abbreviating field names
    - Omitting null/default values
    """
    
    # Field abbreviations for token optimization
    FIELD_ABBREVIATIONS = {
        "team_number": "t",
        "nickname": "n", 
        "score": "s",
        "reasoning": "r",
        "picklist": "p",
        "status": "st",
        "metrics": "m",
        "priority": "pr",
        "weight": "w",
    }
    
    def __init__(self):
        """Initialize JSON compressor."""
        pass
    
    def compress_json(self, data: Dict[str, Any], use_abbreviations: bool = True) -> str:
        """
        Compress JSON data for token optimization.
        
        Args:
            data: JSON data to compress
            use_abbreviations: Whether to use field abbreviations
            
        Returns:
            Compressed JSON string
        """
        if use_abbreviations:
            data = self._abbreviate_fields(data)
        
        # Remove null values
        data = self._remove_nulls(data)
        
        # Serialize with minimal formatting
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    
    def decompress_json(self, json_str: str) -> Dict[str, Any]:
        """
        Decompress JSON with abbreviated fields.
        
        Args:
            json_str: Compressed JSON string
            
        Returns:
            Decompressed data with full field names
        """
        data = json.loads(json_str)
        return self._expand_fields(data)
    
    def _abbreviate_fields(self, data: Any) -> Any:
        """Recursively abbreviate field names."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                abbreviated_key = self.FIELD_ABBREVIATIONS.get(key, key)
                result[abbreviated_key] = self._abbreviate_fields(value)
            return result
        elif isinstance(data, list):
            return [self._abbreviate_fields(item) for item in data]
        else:
            return data
    
    def _expand_fields(self, data: Any) -> Any:
        """Recursively expand abbreviated field names."""
        reverse_abbrev = {v: k for k, v in self.FIELD_ABBREVIATIONS.items()}
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                expanded_key = reverse_abbrev.get(key, key)
                result[expanded_key] = self._expand_fields(value)
            return result
        elif isinstance(data, list):
            return [self._expand_fields(item) for item in data]
        else:
            return data
    
    def _remove_nulls(self, data: Any) -> Any:
        """Recursively remove null/empty values."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                cleaned_value = self._remove_nulls(value)
                if cleaned_value is not None and cleaned_value != "" and cleaned_value != []:
                    result[key] = cleaned_value
            return result
        elif isinstance(data, list):
            return [self._remove_nulls(item) for item in data if item is not None]
        else:
            return data


class UltraCompactFormatter:
    """
    Creates ultra-compact JSON format for maximum token efficiency.
    
    Format: {"p":[[team,score,"reason"]...],"s":"ok"}
    Reduces token usage by ~75% compared to standard format.
    """
    
    def __init__(self):
        """Initialize ultra-compact formatter."""
        pass
    
    def format_picklist(
        self, 
        teams: List[Dict[str, Any]], 
        status: str = "ok"
    ) -> str:
        """
        Format team list as ultra-compact JSON.
        
        Args:
            teams: List of team dictionaries
            status: Status indicator
            
        Returns:
            Ultra-compact JSON string
        """
        # Convert teams to compact array format
        compact_teams = []
        for team in teams:
            team_entry = [
                team.get("team_number", team.get("team")),
                team.get("score", 0.0),
                team.get("reasoning", team.get("reason", ""))
            ]
            compact_teams.append(team_entry)
        
        # Create ultra-compact structure
        ultra_compact = {
            "p": compact_teams,
            "s": status
        }
        
        return json.dumps(ultra_compact, separators=(',', ':'))
    
    def parse_ultra_compact(
        self, 
        ultra_compact_str: str
    ) -> Tuple[List[Tuple[int, float, str]], str]:
        """
        Parse ultra-compact format back to team data.
        
        Args:
            ultra_compact_str: Ultra-compact JSON string
            
        Returns:
            Tuple of (team_list, status)
        """
        data = json.loads(ultra_compact_str)
        
        teams = []
        for entry in data.get("p", []):
            if len(entry) >= 3:
                teams.append((int(entry[0]), float(entry[1]), str(entry[2])))
        
        status = data.get("s", "unknown")
        
        return teams, status
    
    def create_with_index_mapping(
        self,
        teams: List[Dict[str, Any]],
        create_index_map: bool = False
    ) -> Tuple[str, Optional[Dict[int, int]]]:
        """
        Create ultra-compact format with optional index mapping.
        
        For very large datasets, uses indices instead of team numbers
        to further reduce token usage.
        
        Args:
            teams: List of team dictionaries
            create_index_map: Whether to create index mapping
            
        Returns:
            Tuple of (ultra_compact_json, index_map)
        """
        if not create_index_map:
            return self.format_picklist(teams), None
        
        # Create index mapping
        index_map = {}
        compact_teams = []
        
        for idx, team in enumerate(teams):
            team_number = team.get("team_number", team.get("team"))
            index_map[idx] = team_number
            
            team_entry = [
                idx,  # Use index instead of team number
                team.get("score", 0.0),
                team.get("reasoning", team.get("reason", ""))
            ]
            compact_teams.append(team_entry)
        
        ultra_compact = {
            "p": compact_teams,
            "s": "ok"
        }
        
        json_str = json.dumps(ultra_compact, separators=(',', ':'))
        return json_str, index_map


class JSONValidator:
    """
    Validates JSON structures for picklist operations.
    """
    
    def __init__(self):
        """Initialize JSON validator."""
        pass
    
    def validate_picklist_response(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate picklist response structure.
        
        Args:
            data: Response data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for required fields
        if "p" in data:
            # Ultra-compact format
            errors.extend(self._validate_ultra_compact(data))
        elif "picklist" in data:
            # Standard format
            errors.extend(self._validate_standard_format(data))
        elif isinstance(data, list):
            # Direct list format
            errors.extend(self._validate_list_format(data))
        else:
            errors.append("Unknown response format")
        
        return errors
    
    def _validate_ultra_compact(self, data: Dict[str, Any]) -> List[str]:
        """Validate ultra-compact format."""
        errors = []
        
        picklist = data.get("p")
        if not isinstance(picklist, list):
            errors.append("'p' field must be a list")
            return errors
        
        for idx, entry in enumerate(picklist):
            if not isinstance(entry, list):
                errors.append(f"Entry {idx} must be a list")
                continue
            
            if len(entry) < 3:
                errors.append(f"Entry {idx} must have at least 3 elements")
                continue
            
            # Validate team number/index
            try:
                int(entry[0])
            except (ValueError, TypeError):
                errors.append(f"Entry {idx}: team number must be integer")
            
            # Validate score
            try:
                float(entry[1])
            except (ValueError, TypeError):
                errors.append(f"Entry {idx}: score must be numeric")
            
            # Validate reasoning
            if not isinstance(entry[2], str):
                errors.append(f"Entry {idx}: reasoning must be string")
        
        return errors
    
    def _validate_standard_format(self, data: Dict[str, Any]) -> List[str]:
        """Validate standard picklist format."""
        errors = []
        
        picklist = data.get("picklist")
        if not isinstance(picklist, list):
            errors.append("'picklist' field must be a list")
            return errors
        
        for idx, team in enumerate(picklist):
            if not isinstance(team, dict):
                errors.append(f"Team {idx} must be a dictionary")
                continue
            
            # Check required fields
            required_fields = ["team_number", "score"]
            for field in required_fields:
                if field not in team and field.replace("_", "") not in team:
                    errors.append(f"Team {idx}: missing {field}")
        
        return errors
    
    def _validate_list_format(self, data: List[Any]) -> List[str]:
        """Validate direct list format."""
        errors = []
        
        for idx, item in enumerate(data):
            if isinstance(item, list):
                if len(item) < 3:
                    errors.append(f"Item {idx}: list must have at least 3 elements")
            elif isinstance(item, dict):
                if "team_number" not in item and "team" not in item:
                    errors.append(f"Item {idx}: missing team identifier")
            else:
                errors.append(f"Item {idx}: must be list or dictionary")
        
        return errors


# Convenience functions
def compact_json(data: Dict[str, Any], use_abbreviations: bool = True) -> str:
    """Compact JSON data for token optimization."""
    compressor = JSONCompressor()
    return compressor.compress_json(data, use_abbreviations)


def format_ultra_compact(teams: List[Dict[str, Any]], status: str = "ok") -> str:
    """Format teams as ultra-compact JSON."""
    formatter = UltraCompactFormatter()
    return formatter.format_picklist(teams, status)


def validate_json_structure(data: Dict[str, Any]) -> List[str]:
    """Validate JSON structure for picklist operations."""
    validator = JSONValidator()
    return validator.validate_picklist_response(data)


def calculate_token_savings(original: str, compressed: str) -> Dict[str, Any]:
    """
    Calculate token savings from compression.
    
    Args:
        original: Original JSON string
        compressed: Compressed JSON string
        
    Returns:
        Dictionary with savings statistics
    """
    original_len = len(original)
    compressed_len = len(compressed)
    savings = original_len - compressed_len
    savings_percent = (savings / original_len * 100) if original_len > 0 else 0
    
    return {
        "original_length": original_len,
        "compressed_length": compressed_len,
        "bytes_saved": savings,
        "savings_percent": round(savings_percent, 2),
        "compression_ratio": round(compressed_len / original_len, 3) if original_len > 0 else 0,
    }