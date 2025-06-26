"""Service for handling prompt generation for team comparison analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ComparisonPromptService:
    """Handles prompt generation for team comparison analysis."""
    
    def create_system_prompt(self, pick_position: str, num_teams: int) -> str:
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
    
    def build_conversation_messages(
        self, 
        system_prompt: str,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        team_numbers: List[int],
        team_index_map: Dict[int, int],
        generator_service,  # PicklistGeneratorService instance for prompt building
        question: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        """Build conversation messages for GPT.
        
        Args:
            system_prompt: The system prompt to use
            teams_data: Team data for analysis
            your_team_number: The user's team number
            pick_position: Pick position (first, second, third)
            priorities: List of metric priorities
            team_numbers: List of team numbers being compared
            team_index_map: Mapping of index to team number
            generator_service: PicklistGeneratorService instance for prompt building
            question: Optional follow-up question
            chat_history: Optional chat history for follow-up questions
            
        Returns:
            List of conversation messages for GPT
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history if this is a follow-up question
        if chat_history and question:
            # For follow-up questions, include the original analysis context
            base_prompt = generator_service.gpt_service.create_user_prompt(
                your_team_number,
                pick_position,
                priorities,
                teams_data,
                team_numbers,
                team_index_map
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
            user_prompt = generator_service.gpt_service.create_user_prompt(
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
        
        return messages