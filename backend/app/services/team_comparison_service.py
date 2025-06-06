"""Service for comparing a small set of teams using GPT."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from app.services.picklist_generator_service import PicklistGeneratorService

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class TeamComparisonService:
    """Compare up to three teams and return a ranking and summary."""

    def __init__(self, unified_dataset_path: str) -> None:
        self.generator = PicklistGeneratorService(unified_dataset_path)

    def _create_comparison_system_prompt(self, pick_position: str, num_teams: int) -> str:
        """Create a system prompt specifically for team comparison with narrative analysis."""
        return f"""You are an expert FRC (FIRST Robotics Competition) strategist analyzing {num_teams} teams for {pick_position} pick selection.

Your task is to:
1. Rank the teams in order of preference for {pick_position} pick position
2. Provide detailed narrative analysis explaining your reasoning
3. Return response in JSON format with both ranking data and comprehensive summary

Required JSON format:
{{
    "ranking": [
        {{"team_number": 1234, "rank": 1, "score": 85.5, "brief_reason": "Strong auto, consistent scoring"}},
        {{"team_number": 5678, "rank": 2, "score": 78.2, "brief_reason": "Solid defense, reliable partner"}}
    ],
    "summary": "Detailed narrative analysis comparing all teams. Explain strengths, weaknesses, synergies, and strategic considerations. Discuss why each team is ranked in that position and how they complement different alliance strategies. Include specific data points and metrics that influenced the decision.",
    "key_metrics": ["field_name_1", "field_name_2", "field_name_3", "field_name_4", "field_name_5"]
}}

Analysis Guidelines:
- Consider robot capabilities, consistency, strategic fit, and alliance synergy
- Compare teams directly against each other, highlighting key differentiators  
- Reference specific performance metrics from the data provided
- Explain both strengths and potential concerns for each team
- Consider how teams would work together in different alliance compositions
- Provide actionable insights for pick strategy

Key Metrics Selection (CRITICAL):
- The "key_metrics" field is REQUIRED and must contain 4-6 field names from the team data
- ONLY use field names that EXACTLY match column names in the provided data
- If you mention "autonomous score" in your analysis, look for field names like "autonomous_score", "auto_avg_points", "auto_points"
- If you mention "teleop score", look for field names like "teleop_score", "teleoperated_score", "teleop_avg_points"  
- If you mention "EPA", look for field names like "epa_total", "epa_auto", "epa_teleop"
- Choose metrics that directly influenced your ranking decision and show clear differences between teams
- DO NOT include "rank", "team_number", "nickname", "matches_played", or administrative fields
- Example: ["autonomous_score", "teleop_avg_points", "epa_total", "consistency_rating", "defense_score"]

The summary should be comprehensive (200-400 words) and help strategists understand not just the ranking but the reasoning behind each decision."""

    def _extract_metrics_from_narrative(self, narrative: str, teams_data: List[Dict[str, Any]]) -> List[str]:
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

    def _find_matching_field(self, suggested_metric: str, available_fields: set, teams_data: List[Dict[str, Any]]) -> Optional[str]:
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

    def _extract_comparison_stats(self, teams_data: List[Dict[str, Any]], suggested_metrics: Optional[List[str]] = None) -> Dict[str, Any]:
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
                matched_field = self._find_matching_field(metric, all_data_fields, teams_data)
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

    async def compare_teams(
        self,
        team_numbers: List[int],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        question: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not team_numbers or len(team_numbers) < 2:
            raise ValueError("At least two teams must be provided")

        teams_data_all = self.generator._prepare_team_data_for_gpt()
        teams_data = [t for t in teams_data_all if t["team_number"] in team_numbers]
        if len(teams_data) != len(team_numbers):
            found = {t["team_number"] for t in teams_data}
            missing = [n for n in team_numbers if n not in found]
            raise ValueError(f"Teams not found in dataset: {missing}")

        teams_data.sort(key=lambda t: team_numbers.index(t["team_number"]))
        team_index_map = {i + 1: t["team_number"] for i, t in enumerate(teams_data)}

        # Create a custom system prompt for team comparison that includes narrative analysis
        comparison_system_prompt = self._create_comparison_system_prompt(
            pick_position, len(teams_data)
        )

        # Build conversation messages
        messages = [{"role": "system", "content": comparison_system_prompt}]

        # Add chat history if this is a follow-up question
        if chat_history and question:
            # For follow-up questions, include the original analysis context
            base_prompt = self.generator._create_user_prompt(
                your_team_number,
                pick_position,
                priorities,
                teams_data,
                team_numbers,
                team_index_map,
            )
            messages.append({"role": "user", "content": base_prompt})

            # Add the conversation history
            for msg in chat_history:
                if msg["type"] == "question":
                    messages.append(
                        {"role": "user", "content": f"FOLLOW-UP QUESTION: {msg['content']}"}
                    )
                elif msg["type"] == "answer":
                    messages.append({"role": "assistant", "content": msg["content"]})

            # Add the new question
            messages.append({"role": "user", "content": f"FOLLOW-UP QUESTION: {question}"})
        else:
            # Initial analysis or standalone question
            user_prompt = self.generator._create_user_prompt(
                your_team_number,
                pick_position,
                priorities,
                teams_data,
                team_numbers,
                team_index_map,
            )
            
            # Add available field names to help GPT choose correctly
            if teams_data:
                sample_fields = list(teams_data[0].keys())
                # Remove non-metric fields for the sample
                metric_fields = [f for f in sample_fields if f not in ["team_number", "nickname", "reasoning"]]
                user_prompt += f"\n\nAVAILABLE FIELD NAMES: {metric_fields[:15]}"
            
            if question:
                user_prompt += f"\nQUESTION = {question}\nReturn answer in 'summary' field."

            messages.append({"role": "user", "content": user_prompt})

        # Check token count for the entire conversation
        total_content = comparison_system_prompt + "\n".join(
            [msg["content"] for msg in messages[1:]]
        )
        self.generator._check_token_count(comparison_system_prompt, total_content)

        # For follow-up questions, use a different response format
        if chat_history and question:
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                temperature=0.2,
                max_tokens=1500,
            )
            # For follow-up questions, return the response directly as summary
            # and don't update the ranking unless specifically requested
            return {
                "ordered_teams": None,  # Don't change ranking for follow-up questions
                "summary": response.choices[0].message.content.strip(),
                "comparison_data": self._extract_comparison_stats(teams_data),  # Use discovery for follow-up
            }
        else:
            # Initial analysis - use JSON format for structured response
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=2000,
            )
            data = json.loads(response.choices[0].message.content)
            
            # Debug logging
            print(f"DEBUG: GPT Response: {data}")

            # Parse the new comparison format
            if "ranking" in data:
                # New format with detailed ranking and summary
                ranking_data = data["ranking"]
                ordered_teams = []
                for rank_item in ranking_data:
                    # Find the team data and add ranking info
                    team_num = rank_item["team_number"]
                    team_data = next((t for t in teams_data if t["team_number"] == team_num), None)
                    if team_data:
                        team_with_ranking = team_data.copy()
                        team_with_ranking["score"] = rank_item.get("score", 0)
                        team_with_ranking["reasoning"] = rank_item.get("brief_reason", "")
                        ordered_teams.append(team_with_ranking)

                # Extract GPT-suggested key metrics
                suggested_metrics = data.get("key_metrics", [])
                print(f"DEBUG: Suggested metrics from GPT: {suggested_metrics}")
                
                # If GPT didn't provide good metrics, extract from narrative
                if not suggested_metrics or suggested_metrics == ["rank"]:
                    print("DEBUG: GPT didn't provide useful metrics, extracting from narrative")
                    narrative = data.get("summary", "")
                    suggested_metrics = self._extract_metrics_from_narrative(narrative, teams_data)
                
                return {
                    "ordered_teams": ordered_teams if ordered_teams else teams_data,
                    "summary": data.get("summary", "No detailed analysis provided."),
                    "comparison_data": self._extract_comparison_stats(teams_data, suggested_metrics),
                }
            else:
                # Fallback to old format if needed
                ordered = self.generator._parse_response_with_index_mapping(
                    data, teams_data, team_index_map
                )
                return {
                    "ordered_teams": ordered if ordered else teams_data,
                    "summary": data.get("summary", "Analysis completed."),
                    "comparison_data": self._extract_comparison_stats(teams_data),  # No suggested metrics in fallback
                }
