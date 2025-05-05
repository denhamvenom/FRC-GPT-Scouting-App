# backend/app/services/picklist_analysis_service.py

import json
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI
from collections import defaultdict

# Base directory setup for file operations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

class PicklistAnalysisService:
    """
    Service for analyzing scouting data to generate picklist recommendations
    and identify important metrics based on statistical analysis.
    """
    
    def __init__(self, unified_dataset_path: str):
        """
        Initialize the picklist analysis service with the path to the unified dataset.
        
        Args:
            unified_dataset_path: Path to the unified dataset JSON file
        """
        self.dataset_path = unified_dataset_path
        self.dataset = self._load_dataset()
        self.teams_data = self.dataset.get("teams", {})
        self.year = self.dataset.get("year", 2025)
        self.event_key = self.dataset.get("event_key", f"{self.year}arc")
        
        # Cache for metric calculations
        self.metric_cache = {}
        
        # List of universal metrics that apply to any year
        self.universal_metrics = [
            {"id": "reliability", "label": "Reliability / Consistency", "category": "universal"},
            {"id": "driver_skill", "label": "Driver Skill", "category": "universal"},
            {"id": "defense", "label": "Defensive Capability", "category": "universal"},
            {"id": "cycle_time", "label": "Cycle Time", "category": "universal"},
            {"id": "alliance_compatibility", "label": "Alliance Compatibility", "category": "universal"}
        ]
    
    def _load_dataset(self) -> Dict[str, Any]:
        """Load the unified dataset from the JSON file."""
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading unified dataset: {e}")
            return {}
    
    def identify_game_specific_metrics(self) -> List[Dict[str, str]]:
        """
        Identify game-specific metrics based on the scouting data fields.
        Returns list of metric objects with id, label, and category.
        """
        if not self.teams_data:
            return []
        
        # Get the first team to analyze its scouting data structure
        first_team_key = next(iter(self.teams_data))
        first_team = self.teams_data[first_team_key]
        
        # Check if there's any scouting data
        if not first_team.get("scouting_data"):
            return []
        
        # Get the first match scouting data
        first_match = first_team.get("scouting_data", [])[0] if first_team.get("scouting_data") else {}
        
        # Identify game-specific metrics from field names
        game_metrics = []
        
        # Categorize metrics by phase
        auto_metrics = []
        teleop_metrics = []
        endgame_metrics = []
        
        for field, value in first_match.items():
            # Skip common non-game-specific fields
            if field in ["team_number", "match_number", "qual_number", "alliance_color", 
                         "no_show", "driver_station", "comments"]:
                continue
            
            # Skip non-numeric fields for statistical analysis
            if not isinstance(value, (int, float)):
                continue
            
            metric_id = field
            
            # Format the label from snake_case to Title Case
            label = " ".join(w.capitalize() for w in field.split("_"))
            
            # Determine the game phase category
            if field.startswith("auto_"):
                category = "auto"
                auto_metrics.append({"id": metric_id, "label": label, "category": category})
            elif field.startswith("teleop_") or field.startswith("tele_"):
                category = "teleop"
                teleop_metrics.append({"id": metric_id, "label": label, "category": category})
            elif field.startswith("endgame_") or "climb" in field or "park" in field:
                category = "endgame"
                endgame_metrics.append({"id": metric_id, "label": label, "category": category})
            else:
                category = "other"
                game_metrics.append({"id": metric_id, "label": label, "category": category})
        
        # Combine all metrics, placing them in phase order
        return auto_metrics + teleop_metrics + endgame_metrics + game_metrics
    
    def calculate_metrics_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistical properties of each metric across all teams.
        
        Returns:
            Dict with metric_id -> stats dictionary containing:
            - mean: Average value across all teams
            - std: Standard deviation
            - min: Minimum value
            - max: Maximum value
            - correlation_to_win: Correlation coefficient with match wins
        """
        if self.metric_cache.get("stats"):
            return self.metric_cache["stats"]
        
        # Collect all numeric metrics from all teams
        metric_values = defaultdict(list)
        metric_win_pairs = defaultdict(list)
        
        for team_key, team_data in self.teams_data.items():
            scouting_data = team_data.get("scouting_data", [])
            
            for match in scouting_data:
                # Get match outcome (win/loss) if available
                alliance_color = match.get("alliance_color")
                match_number = match.get("match_number") or match.get("qual_number")
                
                # Default to None if we can't determine win status
                won_match = None
                
                # Try to find match in TBA matches
                if match_number and alliance_color:
                    tba_matches = self.dataset.get("tba_matches", [])
                    for tba_match in tba_matches:
                        if tba_match.get("match_number") == match_number:
                            # Check if this alliance won
                            alliance_result = tba_match.get("alliances", {}).get(alliance_color, {})
                            if alliance_result:
                                # TBA marks the winner with "winner" field
                                won_match = alliance_result.get("winner", False)
                            break
                
                # Collect values for each metric
                for field, value in match.items():
                    if isinstance(value, (int, float)) and field not in ["team_number", "match_number", "qual_number"]:
                        metric_values[field].append(value)
                        
                        # If we know the match outcome, record the value-win pair
                        if won_match is not None:
                            metric_win_pairs[field].append((value, 1 if won_match else 0))
        
        # Calculate statistics for each metric
        stats = {}
        for metric, values in metric_values.items():
            values_array = np.array(values, dtype=float)
            
            # Calculate correlation with winning
            win_correlation = 0
            if metric in metric_win_pairs and len(metric_win_pairs[metric]) > 5:
                # Unzip the pairs into separate arrays
                metric_vals, win_vals = zip(*metric_win_pairs[metric])
                
                # Calculate correlation coefficient
                try:
                    win_correlation = np.corrcoef(metric_vals, win_vals)[0, 1]
                except:
                    win_correlation = 0  # Default to 0 if calculation fails
            
            stats[metric] = {
                "mean": float(np.mean(values_array)),
                "std": float(np.std(values_array)),
                "min": float(np.min(values_array)),
                "max": float(np.max(values_array)),
                "correlation_to_win": win_correlation
            }
        
        # Cache the results
        self.metric_cache["stats"] = stats
        return stats
    
    def get_suggested_priorities(self, num_suggestions: int = 10) -> List[Dict[str, Any]]:
        """
        Generate suggested priorities based on statistical analysis.
        
        Args:
            num_suggestions: Number of suggested priorities to return
            
        Returns:
            List of priority suggestions with id, label, category, and importance_score
        """
        # Get the statistical metrics
        stats = self.calculate_metrics_statistics()
        
        # Identify metrics with highest correlation to winning or greatest differentiation power
        metrics_with_scores = []
        
        for metric, metric_stats in stats.items():
            # Format the label from snake_case to Title Case
            label = " ".join(w.capitalize() for w in metric.split("_"))
            
            # Determine category based on metric name
            if metric.startswith("auto_"):
                category = "auto"
            elif metric.startswith("teleop_") or metric.startswith("tele_"):
                category = "teleop"
            elif metric.startswith("endgame_") or "climb" in metric or "park" in metric:
                category = "endgame"
            else:
                category = "other"
            
            # Calculate an importance score based on:
            # 1. Correlation with winning (most important)
            # 2. Variability between teams (to find differentiating metrics)
            correlation_score = abs(metric_stats["correlation_to_win"]) * 3  # Weight correlation higher
            
            # Normalize standard deviation to range for relative importance
            std_normalized = 0
            if metric_stats["mean"] != 0:
                std_normalized = metric_stats["std"] / max(abs(metric_stats["mean"]), 0.001)
            
            differentiation_score = min(std_normalized, 1.0)  # Cap at 1.0
            
            # Combine scores
            importance_score = correlation_score + differentiation_score
            
            metrics_with_scores.append({
                "id": metric,
                "label": label,
                "category": category,
                "importance_score": importance_score,
                "win_correlation": metric_stats["correlation_to_win"],
                "variability": std_normalized
            })
        
        # Sort by importance score and take top suggestions
        metrics_with_scores.sort(key=lambda x: x["importance_score"], reverse=True)
        return metrics_with_scores[:num_suggestions]