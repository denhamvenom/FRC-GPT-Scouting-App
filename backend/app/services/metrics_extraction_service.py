"""Service for handling metric discovery and statistics extraction."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MetricsExtractionService:
    """Handles metric discovery and statistics extraction."""
    
    def extract_metrics_from_narrative(self, narrative: str, teams_data: List[Dict[str, Any]]) -> List[str]:
        """Extract likely metric field names from GPT's narrative text."""
        if not narrative or not teams_data:
            return []
        
        # Get all available field names from the data
        all_fields = set()
        for team in teams_data:
            all_fields.update(team.keys())
        
        # Remove non-metric fields
        all_fields.discard("team_number")
        all_fields.discard("nickname")
        all_fields.discard("reasoning")
        
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
        
        # Common field mappings
        field_mappings = {
            "auto": ["auto", "autonomous"],
            "teleop": ["teleop", "teleoperated"],
            "epa": ["epa"],
            "statbotics_epa_total": ["epa_total", "statbotics_epa_total"],
            "autonomous_score": ["auto", "autonomous"],
            "teleop_score": ["teleop", "teleoperated"],
            "defense": ["defense", "def"],
            "consistency": ["consistency", "consist"],
            "endgame": ["endgame", "end_game"],
            "total": ["total"],
            "avg": ["avg", "average"],
            "points": ["points", "pts"]
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
                if field in team and team[field] is not None:
                    try:
                        float(team[field])
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
                all_data_fields.update(team.keys())
            
            # Remove non-metric fields
            all_data_fields.discard("team_number")
            all_data_fields.discard("nickname")
            all_data_fields.discard("reasoning")
            
            print(f"DEBUG: Available data fields: {sorted(list(all_data_fields))[:10]}...")
            
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
                for key, value in team.items():
                    if key in ["team_number", "nickname", "reasoning"]:
                        continue
                    try:
                        float(value)
                        all_numeric_fields.add(key)
                    except (ValueError, TypeError, AttributeError):
                        continue
            
            # Define priority metrics to show first (if available)
            priority_metrics = [
                "auto_avg_points", "teleop_avg_points", "endgame_avg_points", "total_avg_points",
                "autonomous_score", "teleoperated_score", "endgame_score", "total_score",
                "epa_total", "epa_auto", "epa_teleop", "epa_endgame",
                "consistency_score", "defense_rating", "reliability_score"
            ]
            
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
                if metric in team and team[metric] is not None:
                    try:
                        value = float(team[metric])
                        team_stats["stats"][metric] = value
                    except (ValueError, TypeError):
                        continue
            
            comparison_teams.append(team_stats)
        
        # Debug logging
        print(f"DEBUG: Found {len(ordered_metrics)} metrics: {ordered_metrics[:10]}...")  # Show first 10
        
        return {
            "teams": comparison_teams,
            "metrics": ordered_metrics
        }