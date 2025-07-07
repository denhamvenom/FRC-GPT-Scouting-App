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
        self.generator = PicklistGeneratorService(unified_dataset_path)  # For token checking
        # Pass the data aggregation service to metrics service for field selections access
        self.metrics_service = MetricsExtractionService(self.generator.data_service)





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
                # Create a list to store teams with their GPT rankings
                teams_with_ranks = []
                
                # Debug logging
                print(f"DEBUG: team_index_map = {team_index_map}")
                print(f"DEBUG: ranking_data = {ranking_data}")
                
                for rank_item in ranking_data:
                    # Handle multiple possible formats: team_number, team_index, or index
                    if "team_number" in rank_item:
                        team_num = rank_item["team_number"]
                    elif "team_index" in rank_item:
                        # Convert team_index back to team_number using the map
                        team_index = rank_item["team_index"]
                        team_num = team_index_map.get(team_index)
                        if team_num is None:
                            print(f"WARNING: Could not find team_number for team_index {team_index}")
                            continue
                    elif "index" in rank_item:
                        # Convert index back to team_number using the map
                        team_index = rank_item["index"]
                        team_num = team_index_map.get(team_index)
                        print(f"DEBUG: Converting index {team_index} -> team_number {team_num}")
                        if team_num is None:
                            print(f"WARNING: Could not find team_number for index {team_index}")
                            continue
                    else:
                        print(f"WARNING: No team_number, team_index, or index in rank_item: {rank_item}")
                        continue
                    
                    # Find the team data and add ranking info
                    team_data = next((t for t in teams_data if t["team_number"] == team_num), None)
                    if team_data:
                        team_with_ranking = team_data.copy()
                        team_with_ranking["score"] = rank_item.get("score", 0)
                        team_with_ranking["reasoning"] = rank_item.get("brief_reason", "")
                        team_with_ranking["gpt_rank"] = rank_item.get("rank", 999)  # Add GPT rank for sorting
                        teams_with_ranks.append(team_with_ranking)
                
                # Sort teams by their GPT rank (1 = first, 2 = second, etc.)
                ordered_teams = sorted(teams_with_ranks, key=lambda x: x.get("gpt_rank", 999))
                
                # Debug logging to verify correct ordering
                print("DEBUG: Final team ordering:")
                for i, team in enumerate(ordered_teams):
                    print(f"  Position {i+1}: Team {team['team_number']} (GPT rank: {team.get('gpt_rank', 'N/A')}, Score: {team.get('score', 'N/A')})")

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
