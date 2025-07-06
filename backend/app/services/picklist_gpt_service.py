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

                # Add enhanced performance metrics if available
                if "metrics" in team_data and isinstance(team_data["metrics"], dict):
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
                        
                        formatted_team["metrics"] = numeric_metrics
                    else:
                        formatted_team["metrics"] = metrics

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
• Each reason must be ≤10 words, NO REPETITION, cite 1 metric (e.g. "Strong auto_coral_L4_scored: 2.3 avg").
• NO repetitive words or phrases. Be concise and specific.
• If you cannot complete all teams due to length limits, respond only {{"s":"overflow"}}.

{context_note}"""

            # Add scouting labels context if available
            if self.scouting_labels:
                labels_context = self._create_labels_context()
                if labels_context:
                    prompt += f"\n\nSCOUTING METRICS GUIDE:\n{labels_context}"

            if game_context:
                prompt += f"\n\nGame Context:\n{game_context}\n"

            prompt += f"""
EXAMPLE: {{"p":[[1,8.5,"Strong auto_coral_L4_scored: 2.3"],[2,7.9,"High defense_effectiveness_rating"],[3,6.2,"Reliable endgame_climb_successful"]],"s":"ok"}}"""

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

                # Add metrics with scouting label context
                if "metrics" in team and isinstance(team["metrics"], dict):
                    team_with_score["metrics"] = self._enhance_metrics_with_labels(team["metrics"])

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

                if "metrics" in team and isinstance(team["metrics"], dict):
                    team_with_score["metrics"] = self._enhance_metrics_with_labels(team["metrics"])

                teams_with_scores.append(team_with_score)

        return teams_with_scores

    def _enhance_metrics_with_labels(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance metrics with scouting label context for better GPT understanding.
        
        Args:
            metrics: Original team metrics
            
        Returns:
            Enhanced metrics with label context and descriptions
        """
        if not isinstance(metrics, dict):
            logger.warning(f"Expected dict for metrics, got {type(metrics)}")
            return {}
            
        enhanced_metrics = {}
        
        try:
            for field_name, value in metrics.items():
                if not isinstance(field_name, str):
                    logger.warning(f"Skipping non-string field name: {field_name}")
                    continue
                    
                # Check if this field name matches a scouting label
                if field_name in self.scouting_labels:
                    try:
                        label_info = self.scouting_labels[field_name]
                        
                        # Validate label_info structure
                        if not isinstance(label_info, dict):
                            logger.warning(f"Invalid label info for {field_name}: {type(label_info)}")
                            enhanced_metrics[field_name] = value
                            continue
                        
                        # Create enhanced field name with context
                        description = label_info.get("description", "")
                        category = label_info.get("category", "unknown")
                        data_type = label_info.get("data_type", "unknown")
                        typical_range = label_info.get("typical_range", "")
                        
                        # Sanitize values to prevent extremely long context
                        if len(description) > 100:
                            description = description[:97] + "..."
                        
                        # Add the enhanced field with context (only if value is numeric)
                        if isinstance(value, (int, float)):
                            enhanced_field_key = f"{field_name}_[{category}_{data_type}]"
                            enhanced_metrics[enhanced_field_key] = {
                                "value": value,
                                "description": description,
                                "range": typical_range
                            }
                        
                        # Also keep original field name for compatibility
                        enhanced_metrics[field_name] = value
                        
                    except Exception as e:
                        logger.warning(f"Error enhancing metric {field_name}: {e}")
                        enhanced_metrics[field_name] = value
                else:
                    # Keep original field as-is if no label match found
                    enhanced_metrics[field_name] = value
                    
        except Exception as e:
            logger.error(f"Error in metric enhancement: {e}")
            # Fallback to original metrics
            return metrics
                
        return enhanced_metrics

    def _create_labels_context(self) -> str:
        """
        Create enhanced context string with richer metadata for GPT analysis.
        Includes usage_context, typical_range, and data_type information.
        
        Returns:
            Formatted string with enhanced scouting metrics metadata
        """
        if not self.scouting_labels:
            return ""
            
        # Group labels by category for better organization
        categories = {}
        text_fields = []
        
        for label_name, label_info in self.scouting_labels.items():
            category = label_info.get("category", "other")
            data_type = label_info.get("data_type", "count")
            
            # Separate text fields for special handling
            if data_type == "text":
                text_fields.append((label_name, label_info))
            else:
                if category not in categories:
                    categories[category] = []
                categories[category].append((label_name, label_info))
        
        context_parts = []
        
        # Create enhanced descriptions for key categories
        priority_categories = ["autonomous", "teleop", "endgame", "strategic", "defense", "reliability"]
        
        for category in priority_categories:
            if category in categories:
                labels = categories[category]
                category_labels = []
                
                for label_name, label_info in labels[:4]:  # Increased to top 4 per category
                    description = label_info.get("description", "")
                    typical_range = label_info.get("typical_range", "")
                    usage_context = label_info.get("usage_context", "")
                    data_type = label_info.get("data_type", "count")
                    
                    # Create enhanced description with metadata
                    label_desc = description[:60] + "..." if len(description) > 60 else description
                    
                    # Add range and type information
                    metadata_parts = []
                    if typical_range:
                        metadata_parts.append(f"Range: {typical_range}")
                    if data_type and data_type != "count":
                        metadata_parts.append(f"Type: {data_type}")
                    
                    # Format with metadata
                    if metadata_parts:
                        metadata_str = f" ({', '.join(metadata_parts)})"
                        category_labels.append(f"{label_name}: {label_desc}{metadata_str}")
                    else:
                        category_labels.append(f"{label_name}: {label_desc}")
                
                if category_labels:
                    context_parts.append(f"{category.upper()}: {'; '.join(category_labels)}")
        
        # Add text fields section if present
        if text_fields:
            text_labels = []
            for label_name, label_info in text_fields[:3]:  # Top 3 text fields
                description = label_info.get("description", "")
                usage_context = label_info.get("usage_context", "")
                
                # Create description with usage context
                if usage_context:
                    short_usage = usage_context[:50] + "..." if len(usage_context) > 50 else usage_context
                    text_labels.append(f"{label_name}: {description} - {short_usage}")
                else:
                    text_labels.append(f"{label_name}: {description}")
            
            if text_labels:
                context_parts.append(f"TEXT DATA: {'; '.join(text_labels)}")
        
        return "\n".join(context_parts)

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
        # Check token count
        try:
            self.check_token_count(system_prompt, user_prompt)
        except ValueError as e:
            return {"status": "error", "error": str(e), "error_type": "token_limit_exceeded"}

        # Use the proper exponential backoff retry method
        result = await self._execute_api_call_with_retry(system_prompt, user_prompt, max_retries)

        if result["status"] == "success":
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
