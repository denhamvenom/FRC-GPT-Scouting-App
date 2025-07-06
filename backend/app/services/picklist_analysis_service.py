# backend/app/services/picklist_analysis_service.py

import json
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from app.config.openai_config import OPENAI_API_KEY, OPENAI_MODEL
from openai import OpenAI

# Use centralized OpenAI configuration
GPT_MODEL = OPENAI_MODEL

# Base directory setup for file operations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


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

        # Load field selections configuration
        self.field_selections = self._load_field_selections()

        # List of universal metrics that apply to any year
        self.universal_metrics = [
            {
                "id": "reliability",
                "label": "Reliability / Consistency",
                "category": "universal",
            },
            {"id": "driver_skill", "label": "Driver Skill", "category": "universal"},
            {"id": "defense", "label": "Defensive Capability", "category": "universal"},
            {"id": "cycle_time", "label": "Cycle Time", "category": "universal"},
            {
                "id": "alliance_compatibility",
                "label": "Alliance Compatibility",
                "category": "universal",
            },
        ]

        # Try to load game manual info
        self.manual_info = self._load_manual_info()

    def _load_dataset(self) -> Dict[str, Any]:
        """Load the unified dataset from the JSON file."""
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading unified dataset: {e}")
            return {}

    def _load_field_selections(self) -> Dict[str, Any]:
        """
        Load enhanced field selections using unified structure.
        Priority: field_selections.label_mapping → game_labels → fallback
        
        Returns:
            Dictionary mapping field names to enhanced label data and metadata
        """
        try:
            enhanced_selections = {}
            
            # PRIORITY 1: Load from unified field_selections with enhanced label_mapping
            field_selections_path = os.path.join(DATA_DIR, f"field_selections_{self.year}{self.event_key.replace(str(self.year), '')}.json")
            
            if os.path.exists(field_selections_path):
                with open(field_selections_path, "r", encoding="utf-8") as f:
                    field_selections_data = json.load(f)
                
                # Extract enhanced field selections
                field_selections = field_selections_data.get("field_selections", {})
                for field_name, field_info in field_selections.items():
                    if isinstance(field_info, dict):
                        # Store enhanced field information
                        enhanced_info = {
                            "category": field_info.get("category", "unknown"),
                            "source": field_info.get("source", "unknown")
                        }
                        
                        # Add label mapping if available
                        if "label_mapping" in field_info:
                            label_mapping = field_info["label_mapping"]
                            enhanced_info.update({
                                "label": label_mapping.get("label", field_name),
                                "description": label_mapping.get("description", ""),
                                "data_type": label_mapping.get("data_type", "count"),
                                "typical_range": label_mapping.get("typical_range", ""),
                                "usage_context": label_mapping.get("usage_context", ""),
                                "has_enhanced_mapping": True
                            })
                        else:
                            enhanced_info.update({
                                "label": field_name,
                                "description": "",
                                "data_type": "count",
                                "typical_range": "",
                                "usage_context": "",
                                "has_enhanced_mapping": False
                            })
                        
                        enhanced_selections[field_name] = enhanced_info
                
                print(f"Loaded {len(enhanced_selections)} enhanced field selections from unified structure")
            
            # PRIORITY 2: Fallback to game_labels for additional metrics
            game_labels_path = os.path.join(DATA_DIR, f"game_labels_{self.year}.json")
            
            if os.path.exists(game_labels_path):
                with open(game_labels_path, "r", encoding="utf-8") as f:
                    game_labels_data = json.load(f)
                
                # Add game labels not already present from field_selections
                game_labels_added = 0
                for label_info in game_labels_data.get("labels", []):
                    label_name = label_info.get("label", "")
                    
                    # Check if this label isn't already mapped from field_selections
                    found_in_field_selections = any(
                        field_data.get("label") == label_name 
                        for field_data in enhanced_selections.values()
                    )
                    
                    if label_name and not found_in_field_selections:
                        # Add as direct mapping (label name = field name)
                        enhanced_selections[label_name] = {
                            "category": label_info.get("category", "unknown"),
                            "source": "game_labels",
                            "label": label_name,
                            "description": label_info.get("description", ""),
                            "data_type": label_info.get("data_type", "count"),
                            "typical_range": label_info.get("typical_range", ""),
                            "usage_context": label_info.get("usage_context", ""),
                            "has_enhanced_mapping": True
                        }
                        game_labels_added += 1
                
                if game_labels_added > 0:
                    print(f"Added {game_labels_added} fallback metrics from game_labels")
            
            # PRIORITY 3: Legacy support for schema files
            if not enhanced_selections:
                schema_path = os.path.join(DATA_DIR, f"schema_{self.year}.json")
                if os.path.exists(schema_path):
                    with open(schema_path, "r", encoding="utf-8") as f:
                        legacy_data = json.load(f)
                    
                    # Convert legacy format to enhanced format
                    for field_name, category in legacy_data.items():
                        if isinstance(category, str):
                            enhanced_selections[field_name] = {
                                "category": category,
                                "source": "legacy_schema",
                                "label": field_name,
                                "description": "",
                                "data_type": "count",
                                "typical_range": "",
                                "usage_context": "",
                                "has_enhanced_mapping": False
                            }
                    
                    print(f"Loaded {len(enhanced_selections)} legacy field selections")
            
            print(f"Total enhanced field selections loaded: {len(enhanced_selections)}")
            return enhanced_selections
            
        except Exception as e:
            print(f"Error loading enhanced field selections: {e}")
            return {}

    def _load_manual_info(self) -> Dict[str, Any]:
        """Load game manual text and sections."""
        try:
            # Try to load the manual info from the cached file
            manual_info_path = os.path.join(DATA_DIR, f"manual_info_{self.year}.json")
            if os.path.exists(manual_info_path):
                with open(manual_info_path, "r", encoding="utf-8") as f:
                    manual_data = json.load(f)

                # Check if we have cached the processed manual text
                manual_text_path = os.path.join(DATA_DIR, f"manual_text_{self.year}.json")
                if os.path.exists(manual_text_path):
                    with open(manual_text_path, "r", encoding="utf-8") as f:
                        manual_text_data = json.load(f)
                        return {**manual_data, **manual_text_data}

                # Just return the manual URL if we haven't processed the text yet
                return manual_data

            return {}
        except Exception as e:
            print(f"Error loading manual info: {e}")
            return {}

    def identify_superscout_metrics(self) -> List[Dict[str, str]]:
        """
        Identify available superscouting metrics from the dataset.
        Returns list of metric objects with id, label, and category.
        """
        superscout_metrics = []

        # Check if teams have superscouting data
        if not self.teams_data:
            return []

        # Get a sample of teams to analyze superscouting data structure
        # This increases chances of finding all available metrics
        sample_teams = []
        for team_key, team_data in self.teams_data.items():
            if team_data.get("superscouting_data"):
                sample_teams.append(team_data)
                if len(sample_teams) >= 5:  # Sample up to 5 teams
                    break

        if not sample_teams:
            return []  # No superscouting data found

        # Track metrics we've already added
        added_metrics = set()

        # Process superscouting entries from sample teams
        for team_data in sample_teams:
            for entry in team_data.get("superscouting_data", []):
                # Skip empty entries
                if not entry:
                    continue

                # Identify all metrics from the entry
                for field, value in entry.items():
                    # Skip certain fields
                    if field in [
                        "team_number",
                        "match_number",
                        "qual_number",
                        "field_types",
                        "robot_group",
                    ]:
                        continue

                    # Skip metrics we've already added
                    if field in added_metrics:
                        continue

                    # Format metric id and label
                    metric_id = field
                    label = " ".join(w.capitalize() for w in field.split("_"))

                    # Determine category based on field type if available
                    category = "superscout"
                    if "field_types" in entry and field in entry["field_types"]:
                        category = entry["field_types"][field]

                    # Create metric object
                    metric = {"id": metric_id, "label": label, "category": category}

                    # Add all metrics - both numeric and text-based
                    # For text-based metrics, they can be useful for filtering teams
                    superscout_metrics.append(metric)
                    added_metrics.add(field)

        # Sort metrics by category then label
        superscout_metrics.sort(key=lambda m: (m["category"], m["label"]))

        return superscout_metrics

    def identify_game_specific_metrics(self) -> List[Dict[str, Any]]:
        """
        Identify game-specific metrics using enhanced field selections with metadata.
        Returns list of metric objects with id, label, category, and enhanced metadata.
        """
        # Start with metrics from enhanced field selections if available
        if self.field_selections:
            # Group fields by category
            auto_metrics = []
            teleop_metrics = []
            endgame_metrics = []
            strategy_metrics = []
            autonomous_metrics = []  # For "autonomous" category
            strategic_metrics = []   # For "strategic" category
            other_metrics = []

            for field_name, field_info in self.field_selections.items():
                if isinstance(field_info, dict):
                    category = field_info.get("category", "unknown")
                    
                    # Skip ignored fields
                    if category == "ignore":
                        continue

                    # Skip universal fields
                    if category in [
                        "team_number",
                        "match_number",
                        "qual_number",
                        "alliance_color",
                    ]:
                        continue

                    # Use enhanced label or fallback to formatted field name
                    label = field_info.get("label", " ".join(w.capitalize() for w in field_name.split("_")))

                    # Create enhanced metric object
                    metric = {
                        "id": field_name,
                        "label": label,
                        "category": category,
                        "description": field_info.get("description", ""),
                        "data_type": field_info.get("data_type", "count"),
                        "typical_range": field_info.get("typical_range", ""),
                        "usage_context": field_info.get("usage_context", ""),
                        "source": field_info.get("source", "unknown"),
                        "has_enhanced_mapping": field_info.get("has_enhanced_mapping", False)
                    }

                    # Add to appropriate category list
                    if category in ["auto", "autonomous"]:
                        if category == "autonomous":
                            autonomous_metrics.append(metric)
                        else:
                            auto_metrics.append(metric)
                    elif category == "teleop":
                        teleop_metrics.append(metric)
                    elif category == "endgame":
                        endgame_metrics.append(metric)
                    elif category in ["strategy", "strategic"]:
                        if category == "strategic":
                            strategic_metrics.append(metric)
                        else:
                            strategy_metrics.append(metric)
                    else:
                        other_metrics.append(metric)

            # Combine all metrics in phase order, prioritizing enhanced mappings
            all_metrics = (
                autonomous_metrics + auto_metrics + 
                teleop_metrics + endgame_metrics + 
                strategic_metrics + strategy_metrics + 
                other_metrics
            )
            
            # Sort each category by whether it has enhanced mapping (enhanced first)
            def sort_by_enhancement(metric_list):
                return sorted(metric_list, key=lambda m: not m.get("has_enhanced_mapping", False))
            
            return (
                sort_by_enhancement(autonomous_metrics + auto_metrics) +
                sort_by_enhancement(teleop_metrics) +
                sort_by_enhancement(endgame_metrics) +
                sort_by_enhancement(strategic_metrics + strategy_metrics) +
                sort_by_enhancement(other_metrics)
            )
        # Fallback to analyzing dataset structure if no field selections found
        if not self.teams_data:
            return []

        # Get the first team to analyze its scouting data structure
        first_team_key = next(iter(self.teams_data))
        first_team = self.teams_data[first_team_key]

        # Check if there's any scouting data
        if not first_team.get("scouting_data"):
            return []

        # Get the first match scouting data
        first_match = (
            first_team.get("scouting_data", [])[0] if first_team.get("scouting_data") else {}
        )

        # Identify game-specific metrics from field names
        game_metrics = []

        # Categorize metrics by phase
        auto_metrics = []
        teleop_metrics = []
        endgame_metrics = []

        for field, value in first_match.items():
            # Skip common non-game-specific fields
            if field in [
                "team_number",
                "match_number",
                "qual_number",
                "alliance_color",
                "no_show",
                "driver_station",
                "comments",
                "is_virtual_scout",
                "virtual_scout_timestamp",
            ]:
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
                    if isinstance(value, (int, float)) and field not in [
                        "team_number",
                        "match_number",
                        "qual_number",
                    ]:
                        metric_values[field].append(value)

                        # If we know the match outcome, record the value-win pair
                        if won_match is not None:
                            metric_win_pairs[field].append((value, 1 if won_match else 0))

            # Now include superscouting numeric data
            superscouting_data = team_data.get("superscouting_data", [])

            for entry in superscouting_data:
                # Get match outcome (win/loss) if available - similar to above
                alliance_color = entry.get("alliance_color")
                match_number = entry.get("match_number") or entry.get("qual_number")

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

                # Collect values for each numeric superscouting metric
                for field, value in entry.items():
                    if isinstance(value, (int, float)) and field not in [
                        "team_number",
                        "match_number",
                        "qual_number",
                        "robot_group",
                    ]:
                        # Prefix with "super_" to avoid collisions with regular metrics
                        metric_id = field

                        metric_values[metric_id].append(value)

                        # If we know the match outcome, record the value-win pair
                        if won_match is not None:
                            metric_win_pairs[metric_id].append((value, 1 if won_match else 0))

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
                except Exception:
                    win_correlation = 0  # Default to 0 if calculation fails

            stats[metric] = {
                "mean": float(np.mean(values_array)),
                "std": float(np.std(values_array)),
                "min": float(np.min(values_array)),
                "max": float(np.max(values_array)),
                "correlation_to_win": win_correlation,
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
            correlation_score = (
                abs(metric_stats["correlation_to_win"]) * 3
            )  # Weight correlation higher

            # Normalize standard deviation to range for relative importance
            std_normalized = 0
            if metric_stats["mean"] != 0:
                std_normalized = metric_stats["std"] / max(abs(metric_stats["mean"]), 0.001)

            differentiation_score = min(std_normalized, 1.0)  # Cap at 1.0

            # Combine scores
            importance_score = correlation_score + differentiation_score

            metrics_with_scores.append(
                {
                    "id": metric,
                    "label": label,
                    "category": category,
                    "importance_score": importance_score,
                    "win_correlation": metric_stats["correlation_to_win"],
                    "variability": std_normalized,
                }
            )

        # Sort by importance score and take top suggestions
        metrics_with_scores.sort(key=lambda x: x["importance_score"], reverse=True)
        return metrics_with_scores[:num_suggestions]

    def parse_strategy_prompt(self, strategy_prompt: str) -> Dict[str, Any]:
        """
        Parse a natural language strategy description into specific metrics and weights
        using GPT to understand the strategy intent and map to available metrics.

        Args:
            strategy_prompt: Natural language description of desired strategy

        Returns:
            Dict containing interpretation and parsed metrics with weights
        """
        # Get all available metrics
        game_metrics = self.identify_game_specific_metrics()
        superscout_metrics = self.identify_superscout_metrics()  # Add superscouting metrics
        all_metrics = (
            self.universal_metrics + game_metrics + superscout_metrics
        )  # Include them in all metrics

        # Get statistics for metrics
        metrics_stats = self.calculate_metrics_statistics()

        # Prepare enhanced metric information for GPT with metadata
        metric_info = []
        for metric in all_metrics:
            metric_id = metric["id"]
            stats = metrics_stats.get(metric_id, {})

            # Create enhanced description with metadata
            description = {
                "id": metric_id,
                "name": metric["label"],
                "category": metric["category"],
                "stats": {},
                "source": (
                    "superscouting" if metric in superscout_metrics else "regular"
                ),  # Add source to distinguish
                "enhanced_metadata": {}
            }

            # Add enhanced metadata if available (from Sprint 1 improvements)
            if hasattr(metric, 'get') and isinstance(metric, dict):
                enhanced_metadata = {}
                
                if metric.get("description"):
                    enhanced_metadata["description"] = metric["description"]
                if metric.get("data_type"):
                    enhanced_metadata["data_type"] = metric["data_type"]
                if metric.get("typical_range"):
                    enhanced_metadata["typical_range"] = metric["typical_range"]
                if metric.get("usage_context"):
                    enhanced_metadata["usage_context"] = metric["usage_context"]
                if metric.get("has_enhanced_mapping"):
                    enhanced_metadata["has_enhanced_mapping"] = metric["has_enhanced_mapping"]
                
                if enhanced_metadata:
                    description["enhanced_metadata"] = enhanced_metadata

            # Add stats if available
            if stats:
                description["stats"] = {
                    "average": round(stats.get("mean", 0), 2),
                    "min": round(stats.get("min", 0), 2),
                    "max": round(stats.get("max", 0), 2),
                    "correlation_with_winning": round(stats.get("correlation_to_win", 0), 2),
                }

            metric_info.append(description)

        # Build prompt with context about the game and available metrics
        game_context = ""
        if self.manual_info and "url" in self.manual_info:
            game_context = f"For the {self.year} FRC season. "
            if "game_name" in self.manual_info:
                game_context += f"The game is called {self.manual_info['game_name']}. "
            if "relevant_sections" in self.manual_info:
                game_context += self.manual_info["relevant_sections"]
        else:
            game_context = f"For the {self.year} FRC season."
        # Organize metrics by category for better context
        metrics_by_category = {}
        text_field_metrics = []
        
        for metric in metric_info:
            category = metric.get("category", "other")
            data_type = metric.get("enhanced_metadata", {}).get("data_type", "count")
            
            # Separate text fields for special handling
            if data_type == "text":
                text_field_metrics.append(metric)
            else:
                if category not in metrics_by_category:
                    metrics_by_category[category] = []
                metrics_by_category[category].append(metric)

        # Build the enhanced GPT prompt with category groupings
        prompt = f"""
You are an expert FRC (FIRST Robotics Competition) strategist assistant. 
Your task is to analyze a team's strategy request and identify the most relevant metrics for their picklist.

{game_context}

ENHANCED METRIC CATEGORIES:

AUTONOMOUS PHASE METRICS:
{json.dumps(metrics_by_category.get("autonomous", []) + metrics_by_category.get("auto", []), indent=2)}

TELEOP PHASE METRICS:
{json.dumps(metrics_by_category.get("teleop", []), indent=2)}

ENDGAME PHASE METRICS:
{json.dumps(metrics_by_category.get("endgame", []), indent=2)}

STRATEGIC & QUALITATIVE METRICS:
{json.dumps(metrics_by_category.get("strategic", []) + metrics_by_category.get("strategy", []), indent=2)}

TEXT DATA FIELDS (Strategy Notes & Comments):
{json.dumps(text_field_metrics, indent=2)}

UNIVERSAL METRICS:
{json.dumps(metrics_by_category.get("universal", []), indent=2)}

SUPERSCOUTING METRICS:
{json.dumps(metrics_by_category.get("superscout", []), indent=2)}

OTHER METRICS:
{json.dumps(metrics_by_category.get("other", []) + metrics_by_category.get("unknown", []), indent=2)}

CRITICAL INSTRUCTIONS:
- Pay special attention to "enhanced_metadata" fields which contain detailed descriptions, usage_context, typical_range, and data_type information
- TEXT DATA FIELDS contain strategy notes and scout comments - these are especially valuable for understanding team capabilities and strategic approaches
- Metrics with "has_enhanced_mapping": true have richer, more accurate descriptions
- When strategy mentions specific capabilities, prioritize metrics with detailed descriptions in enhanced_metadata
- Consider the "usage_context" field to understand when and how each metric is collected
- Use "typical_range" to understand what constitutes good vs poor performance

The team is building a picklist and has described their strategy needs as follows:
"{strategy_prompt}"

Based on this strategy description and the categorized metrics above, identify the most relevant metrics that would help the team execute their strategy.

PRIORITIZATION GUIDELINES:
1. Enhanced metrics (has_enhanced_mapping: true) over basic metrics
2. Text fields over numeric when strategy involves qualitative assessment
3. Superscouting metrics for robot capabilities and mechanisms
4. Phase-specific metrics that match strategy timing (auto, teleop, endgame)
5. Metrics with high correlation_with_winning for competitive advantage

Provide your response in the following JSON format:
{{
  "interpretation": "Brief interpretation of the strategy in 1-2 sentences",
  "parsed_metrics": [
    {{
      "id": "metric_id",
      "weight": float_value,
      "reason": "Brief reason for selecting this metric, citing enhanced_metadata if available"
    }},
    ...
  ],
  "category_focus": "Primary game phase or strategy type this focuses on"
}}

The weight should be between 0.5 and 3.0, with higher values for metrics that are more critical to the strategy.
Limit your response to 3-6 metrics that best match the strategy.
Only include metrics from the provided lists above.
        """

        try:
            # Call the OpenAI API
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=1000,
            )

            # Parse the response
            result = json.loads(response.choices[0].message.content)

            # Validate and clean up the result
            if "interpretation" not in result or "parsed_metrics" not in result:
                raise ValueError("Invalid response format from GPT")

            # Ensure weights are in the proper range
            for metric in result["parsed_metrics"]:
                if "weight" in metric:
                    metric["weight"] = max(0.5, min(3.0, float(metric["weight"])))
                else:
                    metric["weight"] = 1.0

            # Add category_focus if not present (for backwards compatibility)
            if "category_focus" not in result:
                result["category_focus"] = "general"

            return result

        except Exception as e:
            print(f"Error parsing strategy prompt with GPT: {e}")

            # Fallback to keyword-based parsing if GPT fails
            return self._fallback_keyword_parsing(strategy_prompt, all_metrics)

    def _fallback_keyword_parsing(
        self, strategy_prompt: str, all_metrics: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Fallback method for parsing strategy prompts when GPT is unavailable.
        Uses simple keyword matching to identify relevant metrics.
        """
        lower_prompt = strategy_prompt.lower()
        parsed_metrics = []

        # Keywords mapping to metric categories
        keywords = {
            "auto": ["auto", "autonomous", "beginning"],
            "teleop": ["teleop", "driver", "control", "manual"],
            "endgame": ["end", "final", "climb", "park", "hang"],
            "defense": ["defense", "defensive", "block", "prevent"],
            "scoring": ["score", "scoring", "points", "goal"],
            "reliability": ["consistent", "reliable", "steady", "dependable"],
            "speed": ["fast", "quick", "rapid", "cycle", "speed"],
            # Add more robot mechanism and strategy related keywords for superscouting
            "intake": ["intake", "pickup", "collect", "grab"],
            "amp": ["amp", "amplifier", "amplification"],
            "speaker": ["speaker", "high goal", "upper goal"],
            "note": ["note", "piece", "game piece"],
            "trap": ["trap", "trapping"],
            "ground": ["ground", "floor", "pickup"],
            "source": ["source", "loading", "human player"],
        }

        # Track already added metrics to avoid duplicates
        added_metric_ids = set()

        # First pass: Prioritize superscouting metrics with direct matches
        # These are more likely to contain mechanism types and strategic capabilities
        superscout_metrics = [m for m in all_metrics if "super" in m.get("category", "").lower()]
        for metric in superscout_metrics:
            metric_id = metric["id"]
            metric_label = metric["label"].lower()

            # Check for direct mention of metric name
            if metric_id in lower_prompt or metric_label in lower_prompt:
                weight = 2.5  # Higher weight for direct superscouting mentions

                if metric_id not in added_metric_ids:
                    parsed_metrics.append(
                        {
                            "id": metric_id,
                            "weight": weight,
                            "reason": "Directly mentioned superscouting metric in strategy",
                        }
                    )
                    added_metric_ids.add(metric_id)

        # Second pass: Check other metrics with direct name matches
        for metric in all_metrics:
            metric_id = metric["id"]
            if metric_id in added_metric_ids:  # Skip already added metrics
                continue

            if metric_id in lower_prompt or metric["label"].lower() in lower_prompt:
                weight = 2.0  # Standard weight for direct mentions

                parsed_metrics.append(
                    {
                        "id": metric_id,
                        "weight": weight,
                        "reason": "Directly mentioned in strategy",
                    }
                )
                added_metric_ids.add(metric_id)

        # Third pass: Category and keyword-based matching
        for category, terms in keywords.items():
            matching_terms = [term for term in terms if term in lower_prompt]
            if matching_terms:
                # Find metrics matching this category
                matching_metrics = [
                    m
                    for m in all_metrics
                    if (
                        any(
                            term in m["id"].lower() or term in m["label"].lower()
                            for term in matching_terms
                        )
                        or category in m.get("category", "").lower()
                    )
                    and m["id"] not in added_metric_ids
                ]

                # Prioritize superscouting metrics in matching
                superscouting_matches = [
                    m for m in matching_metrics if "super" in m.get("category", "").lower()
                ]
                other_matches = [
                    m for m in matching_metrics if "super" not in m.get("category", "").lower()
                ]
                sorted_matches = superscouting_matches + other_matches

                # Determine weight based on emphasis
                weight = 1.0
                for term in matching_terms:
                    if f"very {term}" in lower_prompt or f"high {term}" in lower_prompt:
                        weight = 2.0
                    elif f"extremely {term}" in lower_prompt:
                        weight = 3.0

                # Add up to 2 metrics from this category
                for metric in sorted_matches[:2]:
                    parsed_metrics.append(
                        {
                            "id": metric["id"],
                            "weight": weight,
                            "reason": f"Related to {category} mentioned in strategy",
                        }
                    )
                    added_metric_ids.add(metric["id"])

        # Limit to top 6 metrics
        parsed_metrics = parsed_metrics[:6]

        # Create interpretation based on identified metrics
        if parsed_metrics:
            categories = list(
                set(
                    (
                        m["reason"].split("Related to ")[1].split(" mentioned")[0]
                        if "Related to" in m["reason"]
                        else "specific metric"
                    )
                    for m in parsed_metrics
                )
            )
            interpretation = f"Looking for robots with strengths in {', '.join(categories)}."
        else:
            interpretation = "Could not identify specific metrics from your description."

        return {"interpretation": interpretation, "parsed_metrics": parsed_metrics}

    def rank_teams(self, priorities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank teams based on the provided priorities and weights.

        Args:
            priorities: List of metric ID and weight pairs

        Returns:
            List of ranked teams with scores and details
        """
        if not self.teams_data:
            return []

        # Extract priority metrics and weights
        priority_weights = {p["id"]: p.get("weight", 1.0) for p in priorities}

        # Calculate team scores based on weighted metrics
        team_scores = []

        for team_key, team_data in self.teams_data.items():
            try:
                team_number = int(team_key)
            except ValueError:
                continue  # Skip if team_key can't be converted to int

            team_nickname = team_data.get("nickname", f"Team {team_number}")

            # Collect all numeric metrics for this team
            team_metrics = {}

            # Process scouting data
            total_matches = 0
            for match in team_data.get("scouting_data", []):
                # Skip virtual scouts unless there are no real scouts
                if match.get("is_virtual_scout") and total_matches > 0:
                    continue

                total_matches += 1
                for field, value in match.items():
                    if isinstance(value, (int, float)) and field not in [
                        "team_number",
                        "match_number",
                        "qual_number",
                    ]:
                        if field not in team_metrics:
                            team_metrics[field] = []
                        team_metrics[field].append(value)

            # Calculate averages for each metric
            avg_metrics = {}
            for metric, values in team_metrics.items():
                if values:
                    avg_metrics[metric] = sum(values) / len(values)
                    # Add EPA metrics if available
            statbotics_info = team_data.get("statbotics_info", {})
            for key, value in statbotics_info.items():
                if isinstance(value, (int, float)):
                    avg_metrics[key] = value

            # Calculate the overall score based on weighted priorities
            score = 0.0
            used_metrics = []

            for metric_id, weight in priority_weights.items():
                # Handle universal metrics specially
                if metric_id == "reliability":
                    # Calculate reliability as inverse of standard deviation / mean
                    consistency_score = 0
                    consistency_metrics = []

                    for key, values in team_metrics.items():
                        if len(values) > 1:
                            mean = sum(values) / len(values)
                            if mean != 0:
                                std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
                                # Coefficient of variation (lower is better)
                                cv = std / abs(mean) if mean != 0 else 0
                                # Convert to a 0-10 scale (inverse, since lower CV is better)
                                metric_score = max(0, 10 - 10 * min(cv, 1))
                                consistency_score += metric_score
                                consistency_metrics.append(key)

                    # Average across all metrics
                    if consistency_score > 0:
                        num_metrics = len(consistency_metrics)
                        reliability = consistency_score / num_metrics if num_metrics > 0 else 0
                        score += reliability * weight
                        used_metrics.append(
                            {
                                "id": "reliability",
                                "value": reliability,
                                "weighted_value": reliability * weight,
                                "metrics_used": consistency_metrics[
                                    :3
                                ],  # Include up to 3 example metrics
                            }
                        )

                # Handle defense rating (often from superscout)
                elif metric_id == "defense":
                    defense_value = None

                    # Check various possible field names for defense rating
                    defense_fields = [
                        "defense",
                        "defense_rating",
                        "defensive_rating",
                        "defense_skill",
                    ]
                    for field in defense_fields:
                        if field in avg_metrics:
                            defense_value = avg_metrics[field]
                            break

                    # If direct field not found, check superscouting data
                    if defense_value is None and team_data.get("superscouting_data"):
                        defense_ratings = []
                        for entry in team_data["superscouting_data"]:
                            for field in defense_fields:
                                if field in entry and isinstance(entry[field], (int, float)):
                                    defense_ratings.append(entry[field])

                        if defense_ratings:
                            defense_value = sum(defense_ratings) / len(defense_ratings)

                    # If we found a defense value, add it to the score
                    if defense_value is not None:
                        score += defense_value * weight
                        used_metrics.append(
                            {
                                "id": "defense",
                                "value": defense_value,
                                "weighted_value": defense_value * weight,
                            }
                        )

                # Handle driver skill (often from superscout)
                elif metric_id == "driver_skill":
                    skill_value = None

                    # Check various possible field names for driver skill
                    skill_fields = ["driver_skill", "driver_rating", "driving_skill"]
                    for field in skill_fields:
                        if field in avg_metrics:
                            skill_value = avg_metrics[field]
                            break

                    # If direct field not found, check superscouting data
                    if skill_value is None and team_data.get("superscouting_data"):
                        skill_ratings = []
                        for entry in team_data["superscouting_data"]:
                            for field in skill_fields:
                                if field in entry and isinstance(entry[field], (int, float)):
                                    skill_ratings.append(entry[field])

                        if skill_ratings:
                            skill_value = sum(skill_ratings) / len(skill_ratings)

                    # If we found a driver skill value, add it to the score
                    if skill_value is not None:
                        score += skill_value * weight
                        used_metrics.append(
                            {
                                "id": "driver_skill",
                                "value": skill_value,
                                "weighted_value": skill_value * weight,
                            }
                        )

                # Look for direct metric matches
                elif metric_id in avg_metrics:
                    metric_value = avg_metrics[metric_id]
                    score += metric_value * weight
                    used_metrics.append(
                        {
                            "id": metric_id,
                            "value": metric_value,
                            "weighted_value": metric_value * weight,
                        }
                    )

            # Add team to ranking list
            team_scores.append(
                {
                    "team_number": team_number,
                    "nickname": team_nickname,
                    "score": score,
                    "stats": avg_metrics,
                    "metrics_contribution": used_metrics,
                    "match_count": total_matches,
                }
            )

        # Sort teams by score in descending order
        team_scores.sort(key=lambda x: x["score"], reverse=True)

        return team_scores
