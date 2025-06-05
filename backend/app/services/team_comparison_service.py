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
    "summary": "Detailed narrative analysis comparing all teams. Explain strengths, weaknesses, synergies, and strategic considerations. Discuss why each team is ranked in that position and how they complement different alliance strategies. Include specific data points and metrics that influenced the decision."
}}

Analysis Guidelines:
- Consider robot capabilities, consistency, strategic fit, and alliance synergy
- Compare teams directly against each other, highlighting key differentiators  
- Reference specific performance metrics from the data provided
- Explain both strengths and potential concerns for each team
- Consider how teams would work together in different alliance compositions
- Provide actionable insights for pick strategy

The summary should be comprehensive (200-400 words) and help strategists understand not just the ranking but the reasoning behind each decision."""

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

                return {
                    "ordered_teams": ordered_teams if ordered_teams else teams_data,
                    "summary": data.get("summary", "No detailed analysis provided."),
                }
            else:
                # Fallback to old format if needed
                ordered = self.generator._parse_response_with_index_mapping(
                    data, teams_data, team_index_map
                )
                return {
                    "ordered_teams": ordered if ordered else teams_data,
                    "summary": data.get("summary", "Analysis completed."),
                }
