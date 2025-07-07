"""Service for handling metric discovery and statistics extraction."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MetricsExtractionService:
    """Handles metric discovery and statistics extraction."""
    
    def __init__(self, data_service=None):
        """Initialize with optional data service for field mappings."""
        self.data_service = data_service
    
    def _get_priority_metrics_from_field_selections(self) -> List[str]:
        """Get priority metrics based on field selections data."""
        if not self.data_service:
            print("DEBUG: No data_service available")
            return []
        
        # Check different possible locations for field_selections
        field_selections = None
        if hasattr(self.data_service, 'field_selections'):
            field_selections = getattr(self.data_service, 'field_selections', {})
        elif hasattr(self.data_service, 'dataset') and 'field_selections' in self.data_service.dataset:
            field_selections = self.data_service.dataset['field_selections']
        
        if not field_selections:
            print("DEBUG: No field_selections found in data_service")
            return []
        
        print(f"DEBUG: Found field_selections with {len(field_selections)} entries")
        priority_metrics = []
        
        # Define priority order by category and importance
        category_priority = ['auto', 'teleop', 'endgame', 'strategy']
        
        for category in category_priority:
            # Get fields in this category that have label mappings
            for field_name, field_info in field_selections.items():
                if isinstance(field_info, dict) and field_info.get('category') == category:
                    # Use the enhanced label if available, otherwise the original field name
                    label_mapping = field_info.get('label_mapping', {})
                    if label_mapping and 'label' in label_mapping:
                        priority_metrics.append(label_mapping['label'])
                    else:
                        # Use original field name if it's a meaningful metric
                        if field_name not in ['team_number', 'match_number', 'qual_number']:
                            priority_metrics.append(field_name)
        
        # Also include statbotics metrics which are commonly valuable
        statbotics_metrics = [
            'statbotics_epa_total', 'statbotics_epa_auto', 
            'statbotics_epa_teleop', 'statbotics_epa_endgame'
        ]
        priority_metrics.extend(statbotics_metrics)
        
        return priority_metrics
    
    def _get_field_mappings_from_selections(self, suggested_metric: str) -> Dict[str, List[str]]:
        """Get field mappings based on field selections data."""
        if not self.data_service or not hasattr(self.data_service, 'field_selections'):
            return {}
        
        field_selections = getattr(self.data_service, 'field_selections', {})
        mappings = {}
        
        # Build mappings based on label mappings and field names
        for field_name, field_info in field_selections.items():
            if isinstance(field_info, dict):
                # Get the enhanced label if available
                label_mapping = field_info.get('label_mapping', {})
                if label_mapping and 'label' in label_mapping:
                    enhanced_label = label_mapping['label']
                    # Create mapping from both directions
                    mappings[enhanced_label.lower()] = [enhanced_label, field_name]
                    mappings[field_name.lower()] = [field_name, enhanced_label]
                
                # Also map by category
                category = field_info.get('category')
                if category and category not in ['ignore', 'team_number', 'match_number']:
                    if category not in mappings:
                        mappings[category] = []
                    if label_mapping and 'label' in label_mapping:
                        mappings[category].append(label_mapping['label'])
                    else:
                        mappings[category].append(field_name)
        
        return mappings
    
    def extract_metrics_from_narrative(self, narrative: str, teams_data: List[Dict[str, Any]]) -> List[str]:
        """Extract likely metric field names from GPT's narrative text."""
        if not narrative or not teams_data:
            return []
        
        # Get all available field names from the data
        all_fields = set()
        for team in teams_data:
            # Add top-level fields
            all_fields.update(team.keys())
            
            # Add metrics from metrics dictionary
            if "metrics" in team and isinstance(team["metrics"], dict):
                all_fields.update(team["metrics"].keys())
        
        # Remove non-metric fields
        all_fields.discard("team_number")
        all_fields.discard("nickname")
        all_fields.discard("reasoning")
        all_fields.discard("metrics")
        all_fields.discard("data_sources")
        all_fields.discard("record")
        
        narrative_lower = narrative.lower()
        found_metrics = []
        
        # Define patterns to look for in the narrative
        metric_patterns = {
            "autonomous": ["autonomous", "auto"],
            "teleop": ["teleop", "teleoperated", "driver-controlled"],
            "epa": ["epa", "expected points added"],
            "consistency": ["consistency", "consistent"],
            "defense": ["defense", "defensive"],
            "endgame": ["endgame", "end game"],
            "total": ["total"],
            "average": ["average", "avg"],
            "score": ["score"],
            "points": ["points"],
            "reliability": ["reliability", "reliable"]
        }
        
        # Look for field names that match patterns mentioned in narrative
        for field in all_fields:
            field_lower = field.lower()
            
            # Direct field name mention
            if field_lower in narrative_lower:
                found_metrics.append(field)
                continue
            
            # Pattern matching
            for pattern_key, patterns in metric_patterns.items():
                if pattern_key in field_lower:
                    for pattern in patterns:
                        if pattern in narrative_lower:
                            found_metrics.append(field)
                            break
                    if field in found_metrics:
                        break
        
        # Remove duplicates and limit to reasonable number
        found_metrics = list(dict.fromkeys(found_metrics))[:8]
        print(f"DEBUG: Extracted metrics from narrative: {found_metrics}")
        
        return found_metrics

    def find_matching_field(self, suggested_metric: str, available_fields: set, teams_data: List[Dict[str, Any]]) -> Optional[str]:
        """Find the best matching field name for a GPT-suggested metric."""
        suggested_lower = suggested_metric.lower()
        
        # Direct match first
        if suggested_metric in available_fields:
            return suggested_metric
        
        # Get dynamic field mappings from field selections if available
        field_mappings = self._get_field_mappings_from_selections(suggested_lower)
        
        # Fall back to basic mappings if no field selections
        if not field_mappings:
            field_mappings = {
                "auto": ["auto", "autonomous"],
                "teleop": ["teleop", "teleoperated"],
                "strategy": ["strategy", "endgame"],
                "epa": ["epa", "statbotics_epa"],
                "statbotics_epa_total": ["epa_total", "statbotics_epa_total", "epa"],
                "endgame": ["endgame", "end_game", "strategy"],
                "total": ["total"],
                "avg": ["avg", "average"],
                "points": ["points", "pts"],
                "scored": ["scored", "score"],
                "win_percentage": ["win_percentage", "win_rate", "winrate"]
            }
        
        # Try mapping-based matching
        search_terms = field_mappings.get(suggested_lower, [suggested_lower])
        
        # Find fields that contain any of the search terms
        candidate_fields = []
        for field in available_fields:
            field_lower = field.lower()
            for term in search_terms:
                if term in field_lower:
                    candidate_fields.append(field)
                    break
        
        # Validate candidates have numeric data
        for field in candidate_fields:
            for team in teams_data:
                value = None
                
                # Check top-level first
                if field in team and team[field] is not None:
                    value = team[field]
                
                # Check metrics dictionary
                elif "metrics" in team and isinstance(team["metrics"], dict) and field in team["metrics"]:
                    value = team["metrics"][field]
                
                if value is not None:
                    try:
                        float(value)
                        print(f"DEBUG: Mapped '{suggested_metric}' to '{field}'")
                        return field
                    except (ValueError, TypeError):
                        continue
        
        print(f"DEBUG: Could not map '{suggested_metric}' to any field")
        return None

    def extract_comparison_stats(self, teams_data: List[Dict[str, Any]], suggested_metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract key statistics for visual comparison table."""
        if not teams_data:
            return {"teams": [], "metrics": []}
        
        comparison_teams = []
        
        # Use GPT-suggested metrics if available, otherwise fall back to discovery
        if suggested_metrics:
            # Map GPT's suggested metrics to actual field names in data
            ordered_metrics = []
            all_data_fields = set()
            
            # Collect all available field names
            for team in teams_data:
                # Add top-level fields
                all_data_fields.update(team.keys())
                
                # Add metrics from metrics dictionary
                if "metrics" in team and isinstance(team["metrics"], dict):
                    all_data_fields.update(team["metrics"].keys())
            
            # Remove non-metric fields
            all_data_fields.discard("team_number")
            all_data_fields.discard("nickname")
            all_data_fields.discard("reasoning")
            all_data_fields.discard("metrics")
            all_data_fields.discard("data_sources")
            all_data_fields.discard("record")
            
            print(f"DEBUG: Available data fields (first 15): {sorted(list(all_data_fields))[:15]}")
            print(f"DEBUG: Total available fields: {len(all_data_fields)}")
            
            for metric in suggested_metrics:
                matched_field = self.find_matching_field(metric, all_data_fields, teams_data)
                if matched_field:
                    ordered_metrics.append(matched_field)
            
            print(f"DEBUG: Using GPT-suggested metrics: {ordered_metrics}")
        else:
            # Fallback to automatic discovery
            all_numeric_fields = set()
            
            # First pass: collect all numeric fields from all teams
            for team in teams_data:
                # Check top-level fields first (for backward compatibility)
                for key, value in team.items():
                    if key in ["team_number", "nickname", "reasoning", "metrics", "data_sources", "record"]:
                        continue
                    try:
                        float(value)
                        all_numeric_fields.add(key)
                    except (ValueError, TypeError, AttributeError):
                        continue
                
                # Check metrics dictionary (where the actual metrics are stored)
                if "metrics" in team and isinstance(team["metrics"], dict):
                    for key, value in team["metrics"].items():
                        try:
                            float(value)
                            all_numeric_fields.add(key)
                        except (ValueError, TypeError, AttributeError):
                            continue
            
            # Get priority metrics dynamically from field selections
            priority_metrics = self._get_priority_metrics_from_field_selections()
            print(f"DEBUG: Dynamic priority metrics from field selections: {priority_metrics[:10]}...")
            
            # If no field selections available, fall back to basic metrics that commonly exist
            if not priority_metrics:
                priority_metrics = [
                    "auto", "teleop", "endgame", "total",
                    "auto_avg", "teleop_avg", "endgame_avg", "total_avg",
                    "statbotics_epa_total", "statbotics_epa_auto", "statbotics_epa_teleop", "statbotics_epa_endgame",
                    "win_percentage"
                ]
                print(f"DEBUG: Using fallback priority metrics: {priority_metrics[:5]}...")
            
            # Order metrics: priority first, then alphabetical
            ordered_metrics = []
            for metric in priority_metrics:
                if metric in all_numeric_fields:
                    ordered_metrics.append(metric)
                    all_numeric_fields.remove(metric)
            
            # Add remaining metrics alphabetically (limit to prevent overflow)
            ordered_metrics.extend(sorted(all_numeric_fields)[:10])
            print(f"DEBUG: Using discovered metrics: {ordered_metrics[:5]}...")
        
        # Second pass: extract values for all teams
        for team in teams_data:
            team_stats = {
                "team_number": team["team_number"],
                "nickname": team.get("nickname", ""),
                "stats": {}
            }
            
            for metric in ordered_metrics:
                value = None
                
                # Check top-level fields first (for backward compatibility)
                if metric in team and team[metric] is not None:
                    value = team[metric]
                
                # Check metrics dictionary (preferred location)
                elif "metrics" in team and isinstance(team["metrics"], dict) and metric in team["metrics"]:
                    value = team["metrics"][metric]
                
                # Try to convert to float if we found a value
                if value is not None:
                    try:
                        team_stats["stats"][metric] = float(value)
                    except (ValueError, TypeError):
                        continue
            
            comparison_teams.append(team_stats)
        
        # Debug logging
        print(f"DEBUG: Found {len(ordered_metrics)} metrics: {ordered_metrics[:10]}...")  # Show first 10
        
        return {
            "teams": comparison_teams,
            "metrics": ordered_metrics
        }