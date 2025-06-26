"""Service for comparing a small set of teams using GPT."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.services.comparison_prompt_service import ComparisonPromptService
from app.services.gpt_analysis_service import GPTAnalysisService
from app.services.metrics_extraction_service import MetricsExtractionService
from app.services.picklist_generator_service import PicklistGeneratorService
from app.services.team_data_service import TeamDataService


class TeamComparisonService:
    """Compare up to three teams and return a ranking and summary."""

    def __init__(self, unified_dataset_path: str) -> None:
        self.data_service = TeamDataService(unified_dataset_path)
        self.prompt_service = ComparisonPromptService()
        self.gpt_service = GPTAnalysisService()
        self.metrics_service = MetricsExtractionService()
        self.generator = PicklistGeneratorService(unified_dataset_path)  # For token checking





    async def compare_teams(
        self,
        team_numbers: List[int],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        question: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # Input validation
        if not team_numbers or len(team_numbers) < 2:
            raise ValueError("At least two teams must be provided")

        # Prepare team data
        teams_data, team_index_map = self.data_service.prepare_teams_data(team_numbers)

        # Create prompts and messages
        system_prompt = self.prompt_service.create_system_prompt(pick_position, len(teams_data))
        messages = self.prompt_service.build_conversation_messages(
            system_prompt, teams_data, your_team_number, pick_position, 
            priorities, team_numbers, team_index_map, self.generator, question, chat_history
        )

        # Token count validation (preserve existing behavior)
        total_content = system_prompt + "\n".join([msg["content"] for msg in messages[1:]])
        self.generator.gpt_service.check_token_count(system_prompt, total_content)

        # Get GPT analysis
        if chat_history and question:
            # Follow-up question
            response_text = await self.gpt_service.get_followup_response(messages)
            return {
                "ordered_teams": None,  # Don't change ranking for follow-up questions
                "summary": response_text,
                "comparison_data": self.metrics_service.extract_comparison_stats(teams_data),  # Use discovery for follow-up
            }
        else:
            # Initial analysis
            data = await self.gpt_service.get_initial_analysis(messages)
            
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
                    suggested_metrics = self.metrics_service.extract_metrics_from_narrative(narrative, teams_data)
                
                return {
                    "ordered_teams": ordered_teams if ordered_teams else teams_data,
                    "summary": data.get("summary", "No detailed analysis provided."),
                    "comparison_data": self.metrics_service.extract_comparison_stats(teams_data, suggested_metrics),
                }
            else:
                # Fallback to old format if needed
                ordered = self.generator.gpt_service.parse_response_with_index_mapping(
                    data, teams_data, team_index_map
                )
                return {
                    "ordered_teams": ordered if ordered else teams_data,
                    "summary": data.get("summary", "Analysis completed."),
                    "comparison_data": self.metrics_service.extract_comparison_stats(teams_data),  # No suggested metrics in fallback
                }
