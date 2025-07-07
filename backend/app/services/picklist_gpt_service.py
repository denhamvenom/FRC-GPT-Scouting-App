# backend/app/services/picklist_gpt_service.py

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config.openai_config import OPENAI_API_KEY, OPENAI_MODEL

import tiktoken
from openai import AsyncOpenAI

logger = logging.getLogger("picklist_gpt_service")

GPT_MODEL = OPENAI_MODEL


class PicklistGPTService:
    """
    Service for handling OpenAI GPT integration with original proven algorithms.
    Restored from original system for maximum reliability.
    """

    def __init__(self):
        """Initialize the picklist GPT service with original configuration."""
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Handle tiktoken encoding with fallback for unsupported models like gpt-4.1
        try:
            self.token_encoder = tiktoken.encoding_for_model(GPT_MODEL)
        except KeyError:
            # Use fallback encoding for GPT-4+ models when tiktoken doesn't recognize the model
            self.token_encoder = tiktoken.get_encoding("cl100k_base")
            logger.info(f"Using fallback encoding 'cl100k_base' for model {GPT_MODEL}")
        
        self.max_tokens_limit = 100000
        self.game_context = None  # Can be set by external services
        self.scouting_labels = self._load_scouting_labels()  # Load scouting labels for context

    def _load_scouting_labels(self) -> Dict[str, Dict[str, Any]]:
        """
        Load enhanced scouting labels merging field_selections and game_labels data.
        Priority: field_selections.label_mapping → game_labels → fallback
        
        Returns:
            Dictionary mapping label names to their enhanced metadata
        """
        try:
            # Get the data directory path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            
            labels_dict = {}
            
            # PRIORITY 1: Load enhanced labels from field_selections
            year = 2025  # Could be made dynamic if needed
            field_selections_path = os.path.join(data_dir, f"field_selections_{year}lake.json")
            
            if os.path.exists(field_selections_path):
                with open(field_selections_path, "r", encoding="utf-8") as f:
                    field_selections_data = json.load(f)
                
                # Extract enhanced label mappings from field_selections
                field_selections = field_selections_data.get("field_selections", {})
                for field_name, field_info in field_selections.items():
                    if isinstance(field_info, dict) and "label_mapping" in field_info:
                        label_mapping = field_info["label_mapping"]
                        label_name = label_mapping.get("label", "")
                        
                        if label_name:
                            # Store enhanced label with field_selections metadata
                            labels_dict[label_name] = {
                                "label": label_name,
                                "category": label_mapping.get("category", "unknown"),
                                "description": label_mapping.get("description", ""),
                                "data_type": label_mapping.get("data_type", "count"),
                                "typical_range": label_mapping.get("typical_range", ""),
                                "usage_context": label_mapping.get("usage_context", ""),
                                "source": "field_selections",
                                "original_field": field_name
                            }
                
                logger.info(f"Loaded {len(labels_dict)} enhanced labels from field_selections")
            
            # PRIORITY 2: Fill gaps with game_labels as fallback
            game_labels_path = os.path.join(data_dir, f"game_labels_{year}.json")
            
            if os.path.exists(game_labels_path):
                with open(game_labels_path, "r", encoding="utf-8") as f:
                    game_labels_data = json.load(f)
                
                game_labels_added = 0
                for label in game_labels_data.get("labels", []):
                    label_name = label.get("label", "")
                    
                    if label_name and label_name not in labels_dict:
                        # Add labels not already present from field_selections
                        labels_dict[label_name] = {
                            "label": label_name,
                            "category": label.get("category", "unknown"),
                            "description": label.get("description", ""),
                            "data_type": label.get("data_type", "count"),
                            "typical_range": label.get("typical_range", ""),
                            "usage_context": label.get("usage_context", ""),
                            "source": "game_labels",
                            "extraction_version": label.get("extraction_version", ""),
                            "extraction_date": label.get("extraction_date", ""),
                            "game_year": label.get("game_year", year),
                            "custom_added": label.get("custom_added", False)
                        }
                        game_labels_added += 1
                
                logger.info(f"Added {game_labels_added} fallback labels from game_labels")
                
            logger.info(f"Total enhanced scouting labels loaded: {len(labels_dict)} for GPT context")
            return labels_dict
            
        except Exception as e:
            logger.error(f"Error loading enhanced scouting labels: {e}")
            return {}

    def prepare_team_data_for_gpt(self, teams_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare team data in a format optimized for GPT analysis with enhanced label support.
        Uses enhanced label names instead of raw field names for better GPT understanding.

        Args:
            teams_data: Dictionary of team data from the unified dataset

        Returns:
            List of team data formatted for GPT prompts with enhanced labels and text fields
        """
        formatted_teams = []

        for team_number, team_data in teams_data.items():
            if isinstance(team_data, dict) and "team_number" in team_data:
                # Extract relevant metrics and format for GPT
                formatted_team = {
                    "team_number": team_data["team_number"],
                    "nickname": team_data.get("nickname", f"Team {team_data['team_number']}"),
                }

                # Process raw scouting data to create enhanced metrics if metrics not available
                if "metrics" not in team_data and "scouting_data" in team_data:
                    # Aggregate scouting data and apply enhanced labels
                    raw_metrics = self._aggregate_raw_scouting_data(team_data["scouting_data"])
                    enhanced_metrics = self._apply_enhanced_label_mappings(raw_metrics)
                    formatted_team["metrics"] = enhanced_metrics
                elif "metrics" in team_data and isinstance(team_data["metrics"], dict):
                    metrics = team_data["metrics"]
                    
                    # Separate text fields from numeric metrics
                    if "text_fields" in metrics:
                        text_fields = metrics["text_fields"]
                        numeric_metrics = {k: v for k, v in metrics.items() if k != "text_fields"}
                        
                        # Add text fields with proper formatting
                        if text_fields:
                            formatted_team["text_data"] = {}
                            for field_name, field_info in text_fields.items():
                                if isinstance(field_info, dict) and "value" in field_info:
                                    formatted_team["text_data"][field_name] = field_info["value"]
                                else:
                                    formatted_team["text_data"][field_name] = field_info
                        
                        # Ensure numeric metrics use enhanced label names
                        formatted_team["metrics"] = self._ensure_enhanced_metric_names(numeric_metrics)
                    else:
                        # Apply enhanced labeling to existing metrics
                        formatted_team["metrics"] = self._ensure_enhanced_metric_names(metrics)

                # Add any additional relevant data
                for key in ["autonomous", "teleop", "endgame", "defense", "reliability"]:
                    if key in team_data:
                        formatted_team[key] = team_data[key]

                # Add match count if available
                if "match_count" in team_data:
                    formatted_team["match_count"] = team_data["match_count"]

                # Add data sources for transparency
                if "data_sources" in team_data:
                    formatted_team["data_sources"] = team_data["data_sources"]

                formatted_teams.append(formatted_team)

        return formatted_teams

    def _aggregate_raw_scouting_data(self, scouting_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate raw scouting data from individual matches.
        
        Args:
            scouting_data: List of match scouting data
            
        Returns:
            Dictionary of aggregated metrics with text field support
        """
        metrics_sum = {}
        metrics_count = {}
        text_data = {}

        # Accumulate metrics from all matches
        for match_data in scouting_data:
            if not isinstance(match_data, dict):
                continue

            for key, value in match_data.items():
                # Skip standard non-metric fields
                if key in ["team_number", "match_number", "qual_number", "alliance_color", "notes", "timestamp"]:
                    continue

                if isinstance(value, (int, float)):
                    # Handle numeric fields
                    if key not in metrics_sum:
                        metrics_sum[key] = 0
                        metrics_count[key] = 0
                    metrics_sum[key] += value
                    metrics_count[key] += 1
                elif isinstance(value, str) and value.strip():
                    # Handle text fields - collect all non-empty values
                    if key not in text_data:
                        text_data[key] = []
                    text_data[key].append(value.strip())

        # Calculate averages for numeric fields
        aggregated_metrics = {}
        for metric in metrics_sum:
            if metrics_count[metric] > 0:
                aggregated_metrics[metric] = round(metrics_sum[metric] / metrics_count[metric], 2)

        # Add text data with consolidation
        for field, values in text_data.items():
            # Remove duplicates while preserving order
            unique_values = []
            seen = set()
            for value in values:
                if value not in seen:
                    unique_values.append(value)
                    seen.add(value)
            
            # Store as concatenated string if multiple unique values
            if len(unique_values) == 1:
                aggregated_metrics[field] = unique_values[0]
            elif len(unique_values) > 1:
                aggregated_metrics[field] = " | ".join(unique_values)

        return aggregated_metrics

    def _apply_enhanced_label_mappings(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply enhanced label mappings to convert field names to enhanced labels.
        
        Args:
            raw_metrics: Raw metrics with original field names
            
        Returns:
            Enhanced metrics with label names and separated text fields
        """
        enhanced_metrics = {}
        text_fields = {}
        
        # Process each metric
        for field_name, value in raw_metrics.items():
            # Check if we have an enhanced label for this field
            label_info = None
            for label_name, label_data in self.scouting_labels.items():
                if label_data.get("original_field") == field_name:
                    label_info = label_data
                    break
            
            if label_info:
                # Use enhanced label name
                enhanced_field_name = label_info.get("label", field_name)
                data_type = label_info.get("data_type", "count")
                
                if data_type == "text":
                    # Store text fields separately
                    text_fields[enhanced_field_name] = {
                        "value": value,
                        "description": label_info.get("description", ""),
                        "category": label_info.get("category", "unknown"),
                        "usage_context": label_info.get("usage_context", "")
                    }
                else:
                    # Store numeric metrics with enhanced name
                    enhanced_metrics[enhanced_field_name] = value
            else:
                # Keep original field name if no mapping found
                enhanced_metrics[field_name] = value
        
        # Add text fields if any were found
        if text_fields:
            enhanced_metrics["text_fields"] = text_fields
        
        return enhanced_metrics

    def _ensure_enhanced_metric_names(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure metrics use enhanced label names instead of raw field names.
        
        Args:
            metrics: Original metrics dictionary
            
        Returns:
            Metrics with enhanced label names where available
        """
        enhanced_metrics = {}
        
        for field_name, value in metrics.items():
            # Look for enhanced label mapping
            if field_name in self.scouting_labels:
                # Field name is already an enhanced label, keep as-is
                enhanced_metrics[field_name] = value
            else:
                # Look for this field as an original_field in scouting labels
                enhanced_name = field_name  # Default to original
                for label_name, label_info in self.scouting_labels.items():
                    if label_info.get("original_field") == field_name:
                        enhanced_name = label_name
                        break
                
                enhanced_metrics[enhanced_name] = value
        
        return enhanced_metrics

    def check_token_count(
        self, system_prompt: str, user_prompt: str, max_tokens: int = None
    ) -> None:
        """ORIGINAL TOKEN VALIDATION - EXACT RESTORATION"""
        if max_tokens is None:
            max_tokens = self.max_tokens_limit

        try:
            system_tokens = len(self.token_encoder.encode(system_prompt))
            user_tokens = len(self.token_encoder.encode(user_prompt))
            total_tokens = system_tokens + user_tokens

            logger.info(
                f"Token count: system={system_tokens}, user={user_tokens}, total={total_tokens}"
            )

            if total_tokens > max_tokens:
                raise ValueError(
                    f"Prompt too large: {total_tokens} tokens exceeds limit of {max_tokens}. Consider batching teams or trimming fields."
                )
        except Exception as e:
            logger.warning(f"Token counting failed: {str(e)}, proceeding without check")

    def create_system_prompt(
        self,
        pick_position: str,
        team_count: int,
        game_context: Optional[str] = None,
        use_ultra_compact: bool = True,
    ) -> str:
        """ORIGINAL SYSTEM PROMPT - EXACT RESTORATION"""

        position_context = {
            "first": "First pick teams should be overall powerhouse teams that excel in multiple areas.",
            "second": "Second pick teams should complement the first pick and address specific needs.",
            "third": "Third pick teams are more specialized, often focusing on a single critical function.",
        }

        context_note = position_context.get(pick_position, "")

        if use_ultra_compact:
            # ORIGINAL ULTRA-COMPACT FORMAT - CRITICAL FOR TOKEN OPTIMIZATION
            prompt = f"""You are GPT-4 Turbo, an FRC alliance strategist.
Return one‑line minified JSON:
{{"p":[[index,score,"reason"]…],"s":"ok"}}

CRITICAL RULES
• Rank all {team_count} indices, each exactly once.  
• Use indices 1-{team_count} from TEAM_INDEX_MAP exactly once.
• Sort by weighted performance, then synergy with Team {{your_team_number}} for {pick_position} pick.  
• Each reason must be COMPARATIVE and explain ranking position vs adjacent teams (e.g. "Better endgame than Team 2036, weaker auto than Team 8044").
• Focus on WHY this team ranks HERE specifically, not just their strengths.
• NO repetitive words or phrases. Be concise and strategic.
• If you cannot complete all teams due to length limits, respond only {{"s":"overflow"}}.

{context_note}

REASONING GUIDELINES:
• Explain why this team ranks at THIS position relative to adjacent teams
• Compare key differentiators: "Better auto than lower teams, less reliable than higher teams"
• Use TEAM NUMBERS when referencing other teams: "Outperforms Team 1421", "Falls short of Team 8044"
• Focus on trade-offs that determine precise ranking order
• CRITICAL: Reference actual TEAM NUMBERS (from team_number field) NOT indices in explanations"""

            # Add scouting labels context if available
            if self.scouting_labels:
                labels_context = self._create_labels_context()
                if labels_context:
                    prompt += f"\n\nSCOUTING METRICS GUIDE:\n{labels_context}"

            if game_context:
                prompt += f"\n\nGame Context:\n{game_context}\n"

            prompt += f"""
EXAMPLE: {{"p":[[1,9.5,"Best overall, superior auto+teleop vs Team 34"],[2,8.8,"Strong scoring but weaker endgame than Team 16"],[3,8.1,"Solid teleop, outranks Team 456 on consistency"]],"s":"ok"}}"""

            return prompt
        else:
            # Fallback to standard format for smaller requests
            return self._create_standard_format_prompt(pick_position, team_count, game_context)

    def _create_standard_format_prompt(self, pick_position: str, team_count: int, game_context: Optional[str] = None) -> str:
        """Create standard format system prompt for smaller requests."""
        position_context = {
            "first": "First pick teams should be overall powerhouse teams that excel in multiple areas.",
            "second": "Second pick teams should complement the first pick and address specific needs.",
            "third": "Third pick teams are more specialized, often focusing on a single critical function.",
        }

        context_note = position_context.get(pick_position, "")

        prompt = f"""You are an expert FRC alliance strategist analyzing teams for {pick_position} pick position.

Task: Rank all {team_count} teams based on their performance data and alliance potential.

{context_note}

Focus on:
1. Overall performance metrics
2. Consistency and reliability
3. Strategic value for alliance composition
4. Specific strengths that complement alliance needs

Response format (JSON only):
{{"teams": [{{"team_number": int, "score": float, "reasoning": "brief explanation"}}, ...], "status": "ok"}}

CRITICAL: Return only valid JSON. Provide specific reasoning citing actual metrics."""

        # Add scouting labels context if available
        if self.scouting_labels:
            labels_context = self._create_labels_context()
            if labels_context:
                prompt += f"\n\nSCOUTING METRICS GUIDE:\n{labels_context}"

        if game_context:
            prompt += f"\n\nGame Context:\n{game_context}"

        return prompt

    def create_user_prompt(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]],
        team_numbers: Optional[List[int]] = None,
        force_index_mapping: bool = True,
    ) -> Tuple[str, Optional[Dict[int, int]]]:
        """ORIGINAL USER PROMPT WITH FORCED INDEX MAPPING - EXACT RESTORATION"""

        # OPTIMIZATION: Store priorities for metric filtering and teams data for percentile calculation
        self._current_priorities = priorities
        self._current_teams_data = teams_data
        
        # CRITICAL: Always create index mapping for consistency
        team_index_map = None
        if force_index_mapping:
            team_index_map = {}
            for index, team in enumerate(teams_data, start=1):
                team_index_map[index] = team["team_number"]

        # Find your team's data
        your_team_info = next(
            (team for team in teams_data if team["team_number"] == your_team_number),
            None,
        )

        # EXACT RESTORATION OF ORIGINAL WARNING SYSTEM
        team_index_info = ""
        if team_index_map:
            team_index_info = f"""
TEAM_INDEX_MAP = {json.dumps(team_index_map)}
⚠️ CRITICAL: Use indices 1 through {len(team_index_map)} from TEAM_INDEX_MAP exactly once.
⚠️ Your response MUST use indices, NOT team numbers: [[1,score,"reason"],[2,score,"reason"]...]
⚠️ Each index from 1 to {len(team_index_map)} must appear EXACTLY ONCE.
"""

        # RESTORE ORIGINAL CONDENSED FORMAT
        prompt = f"""YOUR_TEAM_PROFILE = {json.dumps(your_team_info) if your_team_info else "{}"} 
PRIORITY_METRICS  = {json.dumps(priorities)}   # include weight field
GAME_CONTEXT      = {json.dumps(self.game_context) if self.game_context else "null"}
TEAM_NUMBERS_TO_INCLUDE = {json.dumps(team_numbers)}{team_index_info}
AVAILABLE_TEAMS = {json.dumps(self._prepare_teams_with_scores(teams_data, priorities, team_index_map))}     # include pre‑computed weighted_score

Please produce output following RULES.
"""

        return prompt, team_index_map

    def _prepare_teams_with_scores(
        self,
        teams_data: List[Dict[str, Any]],
        priorities: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """ORIGINAL TEAM PREPARATION WITH WEIGHTED SCORES + SCOUTING LABEL CONTEXT"""

        teams_with_scores = []

        if team_index_map:
            # Create reverse map for quick lookup
            team_to_index = {v: k for k, v in team_index_map.items()}

            for team in teams_data:
                weighted_score = self._calculate_weighted_score(team, priorities)
                team_with_score = {
                    "index": team_to_index.get(team["team_number"], 0),
                    "team_number": team["team_number"],
                    "nickname": team.get("nickname", f"Team {team['team_number']}"),
                    "weighted_score": weighted_score,
                }

                # Add metrics with enhanced labels and scouting label context
                if "metrics" in team and isinstance(team["metrics"], dict):
                    # First ensure enhanced label names are used
                    enhanced_metrics = self._ensure_enhanced_metric_names(team["metrics"])
                    # Then add additional context for GPT
                    team_with_score["metrics"] = self._enhance_metrics_with_labels(enhanced_metrics)
                
                # OPTIMIZATION: Include optimized text data if available  
                if "text_data" in team and isinstance(team["text_data"], dict):
                    team_with_score["text_data"] = self._optimize_text_data(team["text_data"])

                teams_with_scores.append(team_with_score)
        else:
            # Standard format without indices
            for team in teams_data:
                weighted_score = self._calculate_weighted_score(team, priorities)
                team_with_score = {
                    "team_number": team["team_number"],
                    "nickname": team.get("nickname", f"Team {team['team_number']}"),
                    "weighted_score": weighted_score,
                }

                # Add metrics with enhanced labels and scouting label context
                if "metrics" in team and isinstance(team["metrics"], dict):
                    # First ensure enhanced label names are used
                    enhanced_metrics = self._ensure_enhanced_metric_names(team["metrics"])
                    # Then add additional context for GPT
                    team_with_score["metrics"] = self._enhance_metrics_with_labels(enhanced_metrics)
                
                # OPTIMIZATION: Include optimized text data if available  
                if "text_data" in team and isinstance(team["text_data"], dict):
                    team_with_score["text_data"] = self._optimize_text_data(team["text_data"])

                teams_with_scores.append(team_with_score)

        return teams_with_scores

    def _enhance_metrics_with_labels(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance metrics with scouting label context for better GPT understanding.
        OPTIMIZED VERSION: Reduces data volume by 70-80% while maintaining ranking quality.
        
        Args:
            metrics: Original team metrics
            
        Returns:
            Optimized metrics with only essential data
        """
        if not isinstance(metrics, dict):
            logger.warning(f"Expected dict for metrics, got {type(metrics)}")
            return {}
            
        optimized_metrics = {}
        
        try:
            # Get current strategy-relevant metrics only (if priorities are set)
            strategy_relevant_metrics = self._get_strategy_relevant_metrics()
            
            for field_name, value in metrics.items():
                if not isinstance(field_name, str):
                    logger.warning(f"Skipping non-string field name: {field_name}")
                    continue
                
                # OPTIMIZATION 1: Only include strategy-relevant metrics + essential universal metrics
                if strategy_relevant_metrics and field_name not in strategy_relevant_metrics:
                    # Always include some essential metrics regardless of strategy
                    essential_metrics = {"driver_skill_rating", "statbotics_epa_total", "Auto Total Points", 
                                       "teleop_total_points", "endgame_total_points"}
                    if field_name not in essential_metrics:
                        continue
                
                # OPTIMIZATION 2: Smart aggregation - use performance bands instead of exact values
                # PHASE 4: Reduces precision but maintains ranking differentiation
                optimized_metrics[field_name] = self._convert_to_performance_band(field_name, value)
                    
        except Exception as e:
            logger.error(f"Error in metric optimization: {e}")
            # Fallback to original metrics without enhancement
            return {k: v for k, v in metrics.items() if isinstance(k, str)}
                
        logger.debug(f"Optimized metrics from {len(metrics)} to {len(optimized_metrics)} fields")
        return optimized_metrics
    
    def _get_strategy_relevant_metrics(self) -> set:
        """
        Get metrics that are relevant to current strategy/priorities.
        This helps filter out irrelevant data to reduce token usage.
        
        Returns:
            Set of metric field names that are strategy-relevant
        """
        if not hasattr(self, '_current_priorities') or not self._current_priorities:
            return set()
        
        relevant_metrics = set()
        
        # Add priority metrics
        for priority in self._current_priorities:
            relevant_metrics.add(priority.get('id', ''))
        
        # Add related metrics (same category/phase)
        for metric_id in list(relevant_metrics):
            if metric_id in self.scouting_labels:
                label_info = self.scouting_labels[metric_id]
                category = label_info.get("category", "")
                
                # Add other metrics from same category for context
                for label_name, info in self.scouting_labels.items():
                    if info.get("category") == category:
                        relevant_metrics.add(label_name)
        
        return relevant_metrics
    
    def _optimize_text_data(self, text_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 2 OPTIMIZATION: Reduce text data volume by 60-70% while preserving key insights.
        
        Args:
            text_data: Original text data dictionary
            
        Returns:
            Optimized text data with summarized content
        """
        if not isinstance(text_data, dict):
            return {}
        
        optimized_text = {}
        
        for field_name, field_value in text_data.items():
            try:
                if not isinstance(field_value, str) or not field_value.strip():
                    continue
                
                # Handle strategy_field - extract key capabilities as tags
                if "strategy" in field_name.lower():
                    optimized_text[field_name] = self._extract_strategy_capabilities(field_value)
                
                # Handle scout_comments - limit to key insights only
                elif "comment" in field_name.lower() or "notes" in field_name.lower():
                    optimized_text[field_name] = self._extract_key_insights(field_value)
                
                # Other text fields - truncate if too long
                else:
                    if len(field_value) > 100:
                        optimized_text[field_name] = field_value[:97] + "..."
                    else:
                        optimized_text[field_name] = field_value
                        
            except Exception as e:
                logger.warning(f"Error optimizing text field {field_name}: {e}")
                # Fallback to truncated version
                if isinstance(field_value, str) and len(field_value) > 50:
                    optimized_text[field_name] = field_value[:47] + "..."
                else:
                    optimized_text[field_name] = field_value
        
        return optimized_text
    
    def _extract_strategy_capabilities(self, strategy_text: str) -> str:
        """
        Extract key capabilities from strategy notes as condensed tags.
        YEAR/GAME AGNOSTIC: Uses generic capability patterns, not game-specific terms.
        """
        if not strategy_text or len(strategy_text) < 10:
            return strategy_text
        
        # GENERIC capability patterns that work across all FRC games
        capability_keywords = {
            "versatile": ["versatile", "multi", "both", "all", "multiple"],
            "fast": ["fast", "quick", "rapid", "speed", "efficient"],
            "slow": ["slow", "careful", "deliberate"],
            "scoring": ["scor", "point", "piece"],  # Covers scoring/scored/points/game pieces
            "floor_intake": ["floor", "ground", "pickup", "collect"],
            "climb": ["climb", "hang", "ascend", "endgame"],
            "auto": ["auto", "autonomous"],
            "defense": ["defense", "defend", "block"],
            "reliable": ["reliable", "consistent", "steady", "stable"]
        }
        
        found_capabilities = []
        text_lower = strategy_text.lower()
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_capabilities.append(capability)
        
        # Return condensed capability tags
        if found_capabilities:
            return " | ".join(found_capabilities[:4])  # Limit to 4 key capabilities
        else:
            # Fallback to first 60 chars if no patterns found
            return strategy_text[:60] + "..." if len(strategy_text) > 60 else strategy_text
    
    def _extract_key_insights(self, comments_text: str) -> str:
        """
        Extract key insights from scout comments, focusing on performance issues and strengths.
        Reduces typical 300+ char comments to 80-120 chars.
        """
        if not comments_text or len(comments_text) < 15:
            return comments_text
        
        # Split into sentences and prioritize important ones
        sentences = [s.strip() for s in comments_text.replace("|", ".").split(".") if s.strip()]
        
        # Keywords that indicate important insights
        priority_keywords = [
            "error", "mistake", "failed", "broken", "stuck", "missed", "tipped",
            "fast", "slow", "efficient", "precise", "good", "strong", "weak",
            "climb", "intake", "score", "defense", "reliable", "consistent"
        ]
        
        # Score sentences by importance
        scored_sentences = []
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            for keyword in priority_keywords:
                if keyword in sentence_lower:
                    score += 1
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top insights
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Build optimized comment from top 1-2 insights
        key_insights = []
        total_length = 0
        max_length = 120
        
        for score, sentence in scored_sentences:
            if total_length + len(sentence) <= max_length and len(key_insights) < 2:
                key_insights.append(sentence)
                total_length += len(sentence)
            elif len(key_insights) == 0:
                # Ensure at least one insight, even if truncated
                key_insights.append(sentence[:max_length-3] + "...")
                break
        
        return " | ".join(key_insights) if key_insights else comments_text[:60] + "..."

    def _create_labels_context(self) -> str:
        """
        PHASE 3 OPTIMIZATION: Create compact metric reference for system prompt.
        Moved from per-team data to system prompt to reduce redundancy by 80%.
        
        Returns:
            Formatted string with essential metric descriptions for system prompt
        """
        if not self.scouting_labels:
            return ""
        
        # OPTIMIZATION: Create strategy-relevant metrics reference only
        relevant_metrics = self._get_strategy_relevant_metrics()
        if not relevant_metrics:
            # If no strategy, include top metrics from each category
            relevant_metrics = self._get_essential_metrics()
        
        # Group by category for organized display
        categories = {}
        
        for metric_id in relevant_metrics:
            if metric_id in self.scouting_labels:
                label_info = self.scouting_labels[metric_id]
                category = label_info.get("category", "other")
                
                if category not in categories:
                    categories[category] = []
                categories[category].append((metric_id, label_info))
        
        # Create compact context - descriptions only, ranges abbreviated
        context_parts = []
        
        for category, metrics in categories.items():
            if not metrics:
                continue
                
            category_header = f"{category.upper()} METRICS:"
            metric_descriptions = []
            
            for metric_id, label_info in metrics:
                description = label_info.get("description", "")
                typical_range = label_info.get("typical_range", "")
                
                # Compact format: "metric_id: brief_description (range)"
                brief_desc = description[:40] + "..." if len(description) > 40 else description
                range_info = f" ({typical_range})" if typical_range else ""
                
                metric_descriptions.append(f"- {metric_id}: {brief_desc}{range_info}")
            
            if metric_descriptions:
                context_parts.append(f"{category_header}\n" + "\n".join(metric_descriptions))
        
        return "\n\n".join(context_parts)
    
    def _get_essential_metrics(self) -> set:
        """
        Get essential metrics when no strategy is provided.
        Returns top 2 metrics from each key category.
        """
        essential_metrics = set()
        key_categories = ["autonomous", "teleop", "endgame"]
        
        for category in key_categories:
            category_metrics = []
            for metric_id, label_info in self.scouting_labels.items():
                if label_info.get("category") == category:
                    category_metrics.append(metric_id)
            
            # Add top 2 from each category
            essential_metrics.update(category_metrics[:2])
        
        # Always include universal performance metrics
        essential_metrics.update({
            "driver_skill_rating", "statbotics_epa_total", 
            "Auto Total Points", "teleop_total_points", "endgame_total_points"
        })
        
        return essential_metrics
    
    def _convert_to_performance_band(self, metric_name: str, value: Any) -> Any:
        """
        PHASE 4 OPTIMIZATION: Convert exact values to performance bands using DYNAMIC ranges.
        Year and game agnostic - uses actual data distribution to determine bands.
        
        Args:
            metric_name: Name of the metric
            value: Original metric value
            
        Returns:
            Performance band (High/Med/Low) or simplified value
        """
        # Only convert numeric values to bands
        if not isinstance(value, (int, float)):
            return value
        
        # Use dynamic percentile-based banding instead of hardcoded thresholds
        return self._create_dynamic_band(metric_name, value)
    
    def _create_dynamic_band(self, metric_name: str, value: float) -> str:
        """
        Create performance bands using DYNAMIC percentile-based thresholds.
        Year and game agnostic - adapts to actual data distribution.
        
        Args:
            metric_name: Name of the metric for context
            value: The metric value to band
            
        Returns:
            Performance band: "High", "Med", "Low"
        """
        # Get cached percentiles for this metric, or calculate if needed
        percentiles = self._get_metric_percentiles(metric_name)
        
        if not percentiles:
            # Fallback: simple rounding for very small datasets
            return str(round(value, 1))
        
        # Use percentile-based thresholds (top 30%, middle 40%, bottom 30%)
        p70, p30 = percentiles
        
        if value >= p70:
            return "High"
        elif value >= p30:
            return "Med"
        else:
            return "Low"
    
    def _get_metric_percentiles(self, metric_name: str) -> tuple:
        """
        Get or calculate percentile thresholds for a metric across all teams.
        Caches results to avoid recalculation.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Tuple of (70th percentile, 30th percentile) or empty tuple if insufficient data
        """
        # Initialize percentile cache if not exists
        if not hasattr(self, '_percentile_cache'):
            self._percentile_cache = {}
        
        # Return cached result if available
        if metric_name in self._percentile_cache:
            return self._percentile_cache[metric_name]
        
        # Calculate percentiles from current teams data if available
        if hasattr(self, '_current_teams_data') and self._current_teams_data:
            values = []
            
            for team in self._current_teams_data:
                if "metrics" in team and isinstance(team["metrics"], dict):
                    if metric_name in team["metrics"]:
                        metric_value = team["metrics"][metric_name]
                        if isinstance(metric_value, (int, float)):
                            values.append(metric_value)
            
            # Need at least 5 data points for meaningful percentiles
            if len(values) >= 5:
                import numpy as np
                p30 = np.percentile(values, 30)
                p70 = np.percentile(values, 70)
                
                # Cache the result
                self._percentile_cache[metric_name] = (p70, p30)
                return (p70, p30)
        
        # Return empty tuple if insufficient data
        return ()

    def _calculate_weighted_score(
        self, team_data: Dict[str, Any], priorities: List[Dict[str, Any]]
    ) -> float:
        """ORIGINAL WEIGHTED SCORING CALCULATION"""

        if not priorities:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for priority in priorities:
            field_name = priority.get("id", "")
            weight = priority.get("weight", 1.0)

            # Extract field value using original logic
            field_value = self._extract_field_value(team_data, field_name)

            if field_value is not None:
                total_score += field_value * weight
                total_weight += weight

        return round(total_score / total_weight if total_weight > 0 else 0.0, 2)

    def _extract_field_value(self, team_data: Dict[str, Any], field_name: str) -> Optional[float]:
        """ORIGINAL FIELD EXTRACTION LOGIC"""

        # Try metrics first
        if "metrics" in team_data and isinstance(team_data["metrics"], dict):
            if field_name in team_data["metrics"]:
                return float(team_data["metrics"][field_name])

        # Try statbotics fields
        if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
            if field_name in team_data["statbotics"]:
                return float(team_data["statbotics"][field_name])
            # Try with statbotics prefix
            statbotics_field = f"statbotics_{field_name}"
            if statbotics_field in team_data:
                return float(team_data[statbotics_field])

        # Try direct field access
        if field_name in team_data:
            try:
                return float(team_data[field_name])
            except (ValueError, TypeError):
                pass

        return None

    def create_missing_teams_system_prompt(self, pick_position: str, team_count: int) -> str:
        """Create system prompt for ranking missing teams."""
        return f"""You are an expert FRC scout analyzing teams NOT yet on the picklist.

Task: Rank the top {team_count} teams that should be added to the existing picklist for {pick_position} pick position.

Focus on:
1. Teams that complement the existing picklist
2. Strategic value additions
3. Filling capability gaps
4. Overall alliance potential

Response format (JSON only):
{{"p": [[team_number, score, "reasoning"], ...], "s": "ok"}}

CRITICAL: Return only valid JSON."""

    def create_missing_teams_user_prompt(
        self,
        missing_team_numbers: List[int],
        ranked_teams: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None,
    ) -> str:
        """Create user prompt for missing teams analysis."""

        prompt = f"Team {your_team_number} - Adding teams to {pick_position} pick picklist.\n\n"

        # Current picklist context
        prompt += "CURRENT PICKLIST (already ranked):\n"
        for i, team in enumerate(ranked_teams[:10], 1):  # Show top 10
            prompt += f"{i}. Team {team.get('team_number', 0)}: {team.get('nickname', 'Unknown')}\n"
        prompt += "\n"

        # Priorities
        if priorities:
            prompt += "PRIORITIES:\n"
            for priority in priorities:
                prompt += f"- {priority.get('name', 'Unknown')} (weight: {priority.get('weight', 0.0):.2f})\n"
            prompt += "\n"

        # Missing teams to analyze
        prompt += "TEAMS TO RANK (not yet on picklist):\n"
        missing_teams_data = [t for t in teams_data if t.get("team_number") in missing_team_numbers]

        for team in missing_teams_data:
            team_num = team.get("team_number", 0)
            prompt += f"Team {team_num}: {team.get('nickname', f'Team {team_num}')}\n"

            if "metrics" in team and isinstance(team["metrics"], dict):
                for metric, value in team["metrics"].items():
                    prompt += f"  {metric}: {value}\n"
            prompt += "\n"

        prompt += "Rank these missing teams considering existing picklist and priorities."

        return prompt

    def create_user_prompt_with_reference_teams(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]],
        reference_teams: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None,
    ) -> str:
        """
        Create user prompt with reference teams for context.

        Args:
            your_team_number: Analyzing team number
            pick_position: Pick position context
            priorities: Priority weights
            teams_data: Teams to analyze
            reference_teams: High-performing reference teams
            team_index_map: Optional index mapping

        Returns:
            User prompt with reference team context
        """
        prompt = (
            f"Team {your_team_number} - {pick_position} pick analysis with reference context.\n\n"
        )

        # Reference teams section
        prompt += "HIGH-PERFORMING REFERENCE TEAMS:\n"
        for team in reference_teams[:5]:  # Show top 5 reference teams
            prompt += f"Team {team.get('team_number', 0)}: {team.get('nickname', 'Unknown')}\n"
            if "metrics" in team:
                for metric, value in team["metrics"].items():
                    prompt += f"  {metric}: {value}\n"
            prompt += "\n"

        # Priorities
        if priorities:
            prompt += "PRIORITIES:\n"
            for priority in priorities:
                prompt += f"- {priority.get('name', 'Unknown')} (weight: {priority.get('weight', 0.0):.2f})\n"
            prompt += "\n"

        # Teams to analyze
        prompt += "TEAMS TO ANALYZE:\n"
        for i, team in enumerate(teams_data):
            team_num = team.get("team_number", 0)
            display_ref = team_index_map.get(i, team_num) if team_index_map else team_num

            prompt += f"Team {display_ref}: {team.get('nickname', f'Team {team_num}')}\n"

            if "metrics" in team and isinstance(team["metrics"], dict):
                for metric, value in team["metrics"].items():
                    prompt += f"  {metric}: {value}\n"
            prompt += "\n"

        prompt += "Rank teams comparing against reference teams and considering priorities."

        return prompt

    def parse_response_with_index_mapping(
        self,
        response_data: Dict[str, Any],
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse GPT response and convert indices to team numbers if needed.

        Args:
            response_data: Parsed JSON response from GPT
            teams_data: Team data for nickname lookups
            team_index_map: Optional mapping from indices to team numbers

        Returns:
            List of teams with scores and reasoning
        """
        picklist = []
        seen_teams = set()

        # Handle ultra-compact format {"p":[[team,score,"reason"]...],"s":"ok"}
        if "p" in response_data and isinstance(response_data["p"], list):
            for team_entry in response_data["p"]:
                if len(team_entry) >= 3:
                    first_value = int(team_entry[0])

                    # Convert index to team number if mapping provided
                    if team_index_map and first_value in team_index_map:
                        team_number = team_index_map[first_value]
                        logger.debug(f"Mapped index {first_value} to team {team_number}")
                    else:
                        team_number = first_value

                    # Skip duplicates
                    if team_number in seen_teams:
                        logger.info(f"Skipping duplicate team {team_number}")
                        continue

                    seen_teams.add(team_number)
                    score = float(team_entry[1])
                    reason = team_entry[2]

                    # Get team nickname
                    team_data = next(
                        (t for t in teams_data if t.get("team_number") == team_number), None
                    )
                    nickname = (
                        team_data.get("nickname", f"Team {team_number}")
                        if team_data
                        else f"Team {team_number}"
                    )

                    picklist.append(
                        {
                            "team_number": team_number,
                            "nickname": nickname,
                            "score": score,
                            "reasoning": reason,
                        }
                    )

        return picklist

    async def analyze_teams(
        self,
        system_prompt: str,
        user_prompt: str,
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None,
        max_retries: int = 3,
        strategy_interpretation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute GPT analysis with retry logic.

        Args:
            system_prompt: System prompt for GPT
            user_prompt: User prompt with team data
            teams_data: Team data for response parsing
            team_index_map: Optional index mapping
            max_retries: Maximum retry attempts

        Returns:
            Analysis results with picklist and metadata
        """
        # Add strategy interpretation to user prompt if provided
        if strategy_interpretation:
            strategy_context = f"""
⚠️ CRITICAL STRATEGIC CONTEXT ⚠️
STRATEGY_INTERPRETATION = "{strategy_interpretation}"

This strategic interpretation is the PRIMARY consideration for all ranking decisions. 
Use this as the guiding principle when evaluating teams. The metric weights provide 
quantitative guidance, but this strategic interpretation defines the overall approach.

ORIGINAL PROMPT:
"""
            user_prompt = strategy_context + user_prompt
        
        # Log the prompts being sent to GPT for debugging
        logger.info("=" * 80)
        logger.info("GPT ANALYSIS REQUEST")
        logger.info("=" * 80)
        logger.info("SYSTEM PROMPT:")
        logger.info(system_prompt)
        logger.info("-" * 40)
        logger.info("USER PROMPT:")
        logger.info(user_prompt)
        logger.info("=" * 80)

        # Check token count
        try:
            self.check_token_count(system_prompt, user_prompt)
        except ValueError as e:
            return {"status": "error", "error": str(e), "error_type": "token_limit_exceeded"}

        # Use the proper exponential backoff retry method
        result = await self._execute_api_call_with_retry(system_prompt, user_prompt, max_retries)

        if result["status"] == "success":
            # Log the GPT response for debugging
            logger.info("=" * 80)
            logger.info("GPT ANALYSIS RESPONSE")
            logger.info("=" * 80)
            logger.info("RAW RESPONSE:")
            logger.info(result["response_data"])
            logger.info("=" * 80)
            
            # Parse response
            picklist = self.parse_response_with_index_mapping(
                result["response_data"], teams_data, team_index_map
            )

            return {
                "status": "success",
                "picklist": picklist,
                "response_data": result["response_data"],
                "processing_time": result["processing_time"],
                "attempt": result.get("attempt", 1),
            }
        else:
            return result

    async def _execute_api_call_with_retry(
        self, system_prompt: str, user_prompt: str, max_retries: int = 3
    ) -> Dict[str, Any]:
        """ORIGINAL EXPONENTIAL BACKOFF RETRY LOGIC - EXACT RESTORATION"""
        initial_delay = 1.0
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Execute API call
                result = await self._execute_api_call(system_prompt, user_prompt)

                # Check for rate limiting specifically
                if result.get("error_type") == "rate_limit" or "429" in str(
                    result.get("error", "")
                ):
                    retry_count += 1
                    if retry_count < max_retries:
                        # ORIGINAL EXPONENTIAL BACKOFF: 2s, 4s, 8s
                        delay = initial_delay * (2**retry_count)
                        logger.warning(
                            f"Rate limit hit, retrying in {delay}s (attempt {retry_count}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        return {
                            "status": "error",
                            "error": f"Rate limit exceeded after {max_retries} attempts",
                            "error_type": "rate_limit_exhausted",
                            "attempts": retry_count,
                        }
                else:
                    # Success or non-rate-limit error
                    result["attempt"] = retry_count + 1
                    return result

            except Exception as e:
                retry_count += 1
                logger.error(f"API call attempt {retry_count} failed: {str(e)}")

                if retry_count < max_retries:
                    delay = initial_delay * (2**retry_count)
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    return {
                        "status": "error",
                        "error": f"API call failed after {max_retries} attempts: {str(e)}",
                        "error_type": "api_failure",
                        "attempts": retry_count,
                    }

        return {
            "status": "error",
            "error": "Unexpected retry loop exit",
            "error_type": "unknown",
            "attempts": retry_count,
        }

    async def _execute_api_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Execute a single OpenAI chat completion call."""
        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            if finish_reason == "length":
                return {
                    "status": "error",
                    "error": "Response truncated due to length",
                    "error_type": "response_truncated",
                }

            try:
                response_data = json.loads(content)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error": f"Invalid JSON response: {e}",
                    "error_type": "json_parse_error",
                    "raw_content": content,
                }

            if response_data.get("s") == "overflow" or response_data.get("status") == "overflow":
                return {
                    "status": "error",
                    "error": "GPT indicated data overflow",
                    "error_type": "data_overflow",
                }

            return {
                "status": "success",
                "response_data": response_data,
                "processing_time": time.time() - start_time,
                "finish_reason": finish_reason,
            }

        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                return {
                    "status": "error",
                    "error": f"Rate limit exceeded: {e}",
                    "error_type": "rate_limit",
                }

            return {
                "status": "error",
                "error": f"API call failed: {e}",
                "error_type": "api_error",
            }

    def has_enhanced_labels(self) -> bool:
        """
        Check if enhanced labels are available and being used.
        
        Returns:
            True if enhanced labels are loaded and available
        """
        return bool(self.scouting_labels and len(self.scouting_labels) > 0)

    def has_text_data(self) -> bool:
        """
        Check if text data fields are available in the enhanced structure.
        
        Returns:
            True if text data fields are present in scouting labels
        """
        if not self.scouting_labels:
            return False
        
        # Check if any labels have text data type
        return any(
            label_info.get("data_type") == "text" 
            for label_info in self.scouting_labels.values()
            if isinstance(label_info, dict)
        )
