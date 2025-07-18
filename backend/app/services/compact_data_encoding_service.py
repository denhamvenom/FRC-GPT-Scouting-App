# backend/app/services/compact_data_encoding_service.py

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("compact_data_encoding_service")


class CompactDataEncodingService:
    """
    Service for encoding team data into compact format to reduce token usage.
    
    CRITICAL: This service is completely agnostic to:
    - Game year (2020, 2025, 2030, etc.)
    - Event (any regional, district, championship)
    - Metrics (dynamically loaded from field_selections)
    - Custom labels (handles user-added metrics)
    
    Thread Safety: Thread-safe (all operations are stateless or read-only after init)
    Dependencies: None (loads field_selections dynamically)
    """
    
    def __init__(self, year: int, event_key: str, data_dir: Optional[str] = None):
        """
        Initialize the compact encoding service for a specific event.
        
        Args:
            year: Game year (e.g., 2025)
            event_key: Event key (e.g., "2025iri", "2025lake", etc.)
            data_dir: Optional data directory path (defaults to app/data)
            
        Raises:
            ValueError: If field_selections file cannot be loaded
        """
        self.year = year
        self.event_key = event_key
        
        # Extract event code from event_key (e.g., "2025iri" -> "iri")
        self.event_code = event_key.replace(str(year), "")
        
        # Set data directory
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(base_dir, "data")
        else:
            self.data_dir = data_dir
            
        # Load field selections for this event
        self.field_selections = self.load_field_selections()
        
        # Generate metric codes dynamically
        self.metric_codes = self.generate_metric_codes()
        self.reverse_metric_codes = {v: k for k, v in self.metric_codes.items()}
        
        # Initialize custom metric tracking
        self._next_custom_code_index = 1
        self._custom_metric_codes = {}
        
        logger.info(f"Initialized CompactDataEncodingService for {event_key}")
        logger.info(f"Generated {len(self.metric_codes)} metric codes")
    
    def load_field_selections(self) -> Dict[str, Any]:
        """
        Load event-specific field selections dynamically.
        
        Returns:
            Field selections dictionary for the event
            
        Raises:
            ValueError: If file cannot be loaded
        """
        filename = f"field_selections_{self.year}{self.event_code}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                field_selections = data.get("field_selections", {})
                logger.info(f"Loaded {len(field_selections)} field selections from {filename}")
                return field_selections
        except FileNotFoundError:
            raise ValueError(f"Field selections file not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in field selections file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading field selections: {e}")
    
    def generate_metric_codes(self) -> Dict[str, str]:
        """
        Generate metric codes dynamically from field selections.
        
        This method creates short codes for metrics based on their names,
        ensuring no collisions and maintaining readability where possible.
        
        Returns:
            Dictionary mapping short codes to full metric names
        """
        metric_codes = {}
        used_codes = set()
        
        # Priority 1: Common metrics across all FRC games (2-letter codes)
        common_mappings = {
            "AP": ["auto", "point"],  # Auto Points
            "TP": ["teleop", "point", "total"],  # Teleop Points
            "EP": ["endgame", "point", "climb"],  # Endgame Points
            "DR": ["driver", "skill", "rating"],  # Driver Rating
            "DT": ["defense", "time"],  # Defense Time
            "SC": ["scout", "comment", "notes"],  # Scout Comments
            "SP": ["start", "position", "zone"],  # Starting Position
            "MN": ["match", "number"],  # Match Number
            "TN": ["team", "number"],  # Team Number
        }
        
        # Apply common mappings first
        for code, keywords in common_mappings.items():
            for field_name, field_info in self.field_selections.items():
                if self._matches_keywords(field_name, field_info, keywords):
                    if code not in used_codes:
                        # Get the actual metric name from label_mapping if available
                        if isinstance(field_info, dict) and "label_mapping" in field_info:
                            metric_name = field_info["label_mapping"].get("label", field_name)
                        else:
                            metric_name = field_name
                        
                        metric_codes[code] = metric_name
                        used_codes.add(code)
                        break
        
        # Priority 2: Generate codes for remaining metrics
        for field_name, field_info in self.field_selections.items():
            # Skip if already mapped
            metric_name = self._get_metric_name(field_info, field_name)
            if metric_name in metric_codes.values():
                continue
                
            # Skip system fields
            if field_info.get("category") in ["ignore", "team_number", "match_number"]:
                continue
            
            # Generate abbreviation
            code = self._generate_abbreviation(metric_name, used_codes)
            metric_codes[code] = metric_name
            used_codes.add(code)
        
        return metric_codes
    
    def _matches_keywords(self, field_name: str, field_info: Dict[str, Any], keywords: List[str]) -> bool:
        """
        Check if a field matches all provided keywords.
        
        Args:
            field_name: Original field name
            field_info: Field information dictionary
            keywords: List of keywords to match
            
        Returns:
            True if all keywords are found in field name or label
        """
        # Get the metric name from label mapping if available
        search_text = field_name.lower()
        if isinstance(field_info, dict) and "label_mapping" in field_info:
            label = field_info["label_mapping"].get("label", "")
            search_text = f"{search_text} {label.lower()}"
        
        # Check if all keywords are present
        return all(keyword.lower() in search_text for keyword in keywords)
    
    def _get_metric_name(self, field_info: Dict[str, Any], field_name: str) -> str:
        """
        Extract the actual metric name from field info.
        
        Args:
            field_info: Field information dictionary
            field_name: Original field name
            
        Returns:
            The metric name to use for encoding
        """
        if isinstance(field_info, dict) and "label_mapping" in field_info:
            return field_info["label_mapping"].get("label", field_name)
        return field_name
    
    def _generate_abbreviation(self, metric_name: str, used_codes: Set[str]) -> str:
        """
        Generate a unique abbreviation for a metric name.
        
        This method uses intelligent abbreviation strategies:
        1. First letters of significant words (2-3 chars)
        2. First + consonants if collision (3-4 chars)
        3. Numbered suffix if still collision
        
        Args:
            metric_name: Full metric name
            used_codes: Set of already used codes
            
        Returns:
            Unique abbreviation code
        """
        # Clean and tokenize the metric name
        clean_name = re.sub(r'[^\w\s]', ' ', metric_name)
        words = [w for w in clean_name.split() if len(w) > 2 or w.lower() in ['l1', 'l2', 'l3', 'l4']]
        
        # Strategy 1: First letters of significant words
        if len(words) >= 2:
            # Take first letter of each significant word
            code = ''.join(word[0].upper() for word in words[:3])
            if code not in used_codes and len(code) >= 2:
                return code
        
        # Strategy 2: Use more characters from important words
        if words:
            # Take more chars from first word
            code = words[0][:3].upper()
            if len(words) > 1:
                code = words[0][:2].upper() + words[1][0].upper()
            
            if code not in used_codes:
                return code
        
        # Strategy 3: Add consonants or numbers
        base_code = words[0][:2].upper() if words else metric_name[:2].upper()
        for i in range(1, 10):
            candidate = f"{base_code}{i}"
            if candidate not in used_codes:
                return candidate
        
        # Fallback: Use first 4 chars with number
        base = metric_name[:4].upper().replace(' ', '')
        for i in range(1, 100):
            candidate = f"{base}{i}"
            if candidate not in used_codes:
                return candidate
        
        # Ultimate fallback
        return f"M{len(used_codes) + 1}"
    
    def encode_team_to_array(self, team_data: Dict[str, Any], team_index: int) -> List[Any]:
        """
        Convert team data from JSON to compact array format.
        
        Args:
            team_data: Team data dictionary with metrics and text_data
            team_index: Index number for this team (1-based)
            
        Returns:
            Compact array representation of team data
        """
        # Start with index, team number, nickname, weighted score
        array = [
            team_index,
            team_data.get("team_number", 0),
            team_data.get("nickname", ""),
            team_data.get("weighted_score", 0.0)
        ]
        
        # Create metrics array in consistent order
        metrics_array = []
        metrics = team_data.get("metrics", {})
        
        # Add metrics in the order of our metric codes
        for code in sorted(self.metric_codes.keys()):
            metric_name = self.metric_codes[code]
            value = metrics.get(metric_name, 0)
            
            # Round numeric values to 2 decimal places
            if isinstance(value, (int, float)):
                value = round(value, 2)
            
            metrics_array.append(value)
        
        # Add text data if present
        text_data = team_data.get("text_data", {})
        if text_data:
            # Compress text data
            compressed_text = self._compress_text_data(text_data)
            metrics_array.append(compressed_text)
        
        array.append(metrics_array)
        return array
    
    def _compress_text_data(self, text_data: Dict[str, str]) -> str:
        """
        Compress text data into a single string with separators.
        
        Args:
            text_data: Dictionary of text fields
            
        Returns:
            Compressed text string
        """
        compressed_parts = []
        
        for field_name, value in text_data.items():
            if not value or not isinstance(value, str):
                continue
                
            # Find code for this field
            code = None
            for c, name in self.metric_codes.items():
                if name == field_name:
                    code = c
                    break
            
            if not code:
                # Generate code for custom field
                code = self.add_custom_metric(field_name)
            
            # Compress the value
            compressed_value = self._compress_single_text(value)
            compressed_parts.append(f"{code}:{compressed_value}")
        
        return "|".join(compressed_parts)
    
    def _compress_single_text(self, text: str) -> str:
        """
        Compress a single text value using abbreviations and key terms.
        
        Args:
            text: Original text value
            
        Returns:
            Compressed text
        """
        if len(text) <= 20:
            return text
        
        # Common substitutions for FRC terms (game-agnostic)
        substitutions = {
            "autonomous": "auto",
            "teleoperated": "teleop",
            "endgame": "end",
            "defense": "def",
            "offense": "off",
            "consistent": "const",
            "inconsistent": "incons",
            "reliable": "rel",
            "unreliable": "unrel",
            "aggressive": "aggr",
            "defensive": "def",
            "strategy": "strat",
            "position": "pos",
            "starting": "start",
            "climbing": "climb",
            "scoring": "score",
            "intake": "int",
            "shooter": "shoot",
            "drivetrain": "drive",
            "mechanism": "mech",
            "broken": "broke",
            "disabled": "dis",
            "tipped": "tip",
            "fell": "fall",
        }
        
        compressed = text.lower()
        for long_form, short_form in substitutions.items():
            compressed = compressed.replace(long_form, short_form)
        
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = compressed.split()
        filtered_words = [w for w in words if w not in stop_words or len(words) <= 5]
        
        compressed = " ".join(filtered_words)
        
        # Truncate if still too long
        if len(compressed) > 80:
            compressed = compressed[:77] + "..."
        
        return compressed
    
    def create_lookup_tables(self, teams_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create lookup tables for the compact encoding.
        
        Args:
            teams_data: List of team data dictionaries
            
        Returns:
            Dictionary containing:
            - METRIC_CODES: Mapping of codes to full metric names
            - TEAM_INDEX_MAP: Mapping of indices to team numbers
            - CUSTOM_CODES: Any custom metric codes added
        """
        # Create team index map
        team_index_map = {}
        for index, team in enumerate(teams_data, start=1):
            team_index_map[index] = team["team_number"]
        
        # Combine standard and custom metric codes
        all_metric_codes = {**self.metric_codes, **self._custom_metric_codes}
        
        return {
            "METRIC_CODES": all_metric_codes,
            "TEAM_INDEX_MAP": team_index_map,
            "METRIC_ORDER": sorted(self.metric_codes.keys()),
        }
    
    def add_custom_metric(self, metric_name: str) -> str:
        """
        Add a custom metric dynamically and generate a code for it.
        
        Args:
            metric_name: Name of the custom metric
            
        Returns:
            Generated code for the metric
        """
        # Check if already exists
        for code, name in {**self.metric_codes, **self._custom_metric_codes}.items():
            if name == metric_name:
                return code
        
        # Generate new code
        used_codes = set(self.metric_codes.keys()) | set(self._custom_metric_codes.keys())
        
        # Try intelligent abbreviation first
        code = self._generate_abbreviation(metric_name, used_codes)
        
        # Store the custom metric code
        self._custom_metric_codes[code] = metric_name
        logger.info(f"Added custom metric: {code} -> {metric_name}")
        
        return code
    
    def decode_array_to_team(self, array: List[Any], lookup_tables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode a compact array back to team data dictionary.
        
        Args:
            array: Compact array representation
            lookup_tables: Lookup tables with metric codes and team mappings
            
        Returns:
            Decoded team data dictionary
        """
        if len(array) < 5:
            raise ValueError(f"Invalid array format: expected at least 5 elements, got {len(array)}")
        
        # Extract basic info
        team_data = {
            "index": array[0],
            "team_number": array[1],
            "nickname": array[2],
            "weighted_score": array[3],
            "metrics": {},
            "text_data": {}
        }
        
        # Extract metrics array
        metrics_array = array[4]
        if not isinstance(metrics_array, list):
            return team_data
        
        # Decode metrics using metric order
        metric_codes = lookup_tables.get("METRIC_CODES", {})
        metric_order = lookup_tables.get("METRIC_ORDER", sorted(metric_codes.keys()))
        
        # Map values back to metric names
        for i, code in enumerate(metric_order):
            if i < len(metrics_array):
                metric_name = metric_codes.get(code, code)
                value = metrics_array[i]
                
                # Skip empty values
                if value != 0 and value != "" and value is not None:
                    team_data["metrics"][metric_name] = value
        
        # Check for compressed text data at the end
        if len(metrics_array) > len(metric_order):
            compressed_text = metrics_array[-1]
            if isinstance(compressed_text, str) and ":" in compressed_text:
                text_data = self._decompress_text_data(compressed_text, metric_codes)
                team_data["text_data"] = text_data
        
        return team_data
    
    def _decompress_text_data(self, compressed: str, metric_codes: Dict[str, str]) -> Dict[str, str]:
        """
        Decompress text data from compressed format.
        
        Args:
            compressed: Compressed text string
            metric_codes: Metric code mappings
            
        Returns:
            Dictionary of text fields
        """
        text_data = {}
        
        parts = compressed.split("|")
        for part in parts:
            if ":" not in part:
                continue
                
            code, value = part.split(":", 1)
            field_name = metric_codes.get(code, code)
            text_data[field_name] = value
        
        return text_data
    
    def calculate_token_reduction(self, original_json: str, compact_arrays: List[List[Any]], 
                                lookup_tables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the token reduction achieved by compact encoding.
        
        Args:
            original_json: Original JSON string
            compact_arrays: List of compact arrays
            lookup_tables: Lookup tables for the encoding
            
        Returns:
            Dictionary with token counts and reduction percentage
        """
        # Create compact format string
        compact_data = {
            "METRIC_CODES": lookup_tables["METRIC_CODES"],
            "TEAM_INDEX_MAP": lookup_tables["TEAM_INDEX_MAP"],
            "AVAILABLE_TEAMS": compact_arrays
        }
        compact_json = json.dumps(compact_data, separators=(',', ':'))
        
        # Calculate sizes
        original_size = len(original_json)
        compact_size = len(compact_json)
        reduction_pct = ((original_size - compact_size) / original_size) * 100
        
        # Estimate token counts (rough approximation: 1 token ≈ 4 characters)
        original_tokens = original_size // 4
        compact_tokens = compact_size // 4
        
        return {
            "original_size": original_size,
            "compact_size": compact_size,
            "reduction_percentage": round(reduction_pct, 1),
            "original_tokens_estimate": original_tokens,
            "compact_tokens_estimate": compact_tokens,
            "token_reduction_estimate": round(((original_tokens - compact_tokens) / original_tokens) * 100, 1)
        }