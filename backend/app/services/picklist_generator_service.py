# backend/app/services/picklist_generator_service.py

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PicklistGeneratorService:
    """
    Service for generating ranked picklists using GPT, based on team performance
    metrics and alliance strategy priorities.
    """
    
    def __init__(self, unified_dataset_path: str):
        """
        Initialize the picklist generator with the unified dataset.
        
        Args:
            unified_dataset_path: Path to the unified dataset JSON file
        """
        self.dataset_path = unified_dataset_path
        self.dataset = self._load_dataset()
        self.teams_data = self.dataset.get("teams", {})
        self.year = self.dataset.get("year", 2025)
        self.event_key = self.dataset.get("event_key", f"{self.year}arc")
        
        # Load manual text for game context if available
        self.game_context = self._load_game_context()
        
        # Internal cache to avoid duplicate GPT calls
        self._picklist_cache = {}
    
    def _load_dataset(self) -> Dict[str, Any]:
        """Load the unified dataset from the JSON file."""
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading unified dataset: {e}")
            return {}
    
    def _load_game_context(self) -> Optional[str]:
        """Load the game manual text for context."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            manual_text_path = os.path.join(data_dir, f"manual_text_{self.year}.json")
            
            if os.path.exists(manual_text_path):
                with open(manual_text_path, "r", encoding="utf-8") as f:
                    manual_data = json.load(f)
                    # Combine game name and relevant sections
                    return f"Game: {manual_data.get('game_name', '')}\n\n{manual_data.get('relevant_sections', '')}"
            return None
        except Exception as e:
            print(f"Error loading game context: {e}")
            return None
    
    def _prepare_team_data_for_gpt(self) -> List[Dict[str, Any]]:
        """
        Prepare a condensed version of team data suitable for the GPT context window.
        Includes key metrics and statistics in a structured format.
        
        Returns:
            List of dictionaries with team data
        """
        condensed_teams = []
        
        for team_number, team_data in self.teams_data.items():
            # Skip entries that don't have a valid team number
            try:
                team_number_int = int(team_number)
            except (ValueError, TypeError):
                continue
                
            # Create basic team info
            team_info = {
                "team_number": team_number_int,
                "nickname": team_data.get("nickname", f"Team {team_number}"),
                "metrics": {},
                "match_count": len(team_data.get("scouting_data", [])),
            }
            
            # Calculate average metrics from scouting data
            scouting_metrics = {}
            for match in team_data.get("scouting_data", []):
                for key, value in match.items():
                    if isinstance(value, (int, float)) and key not in ["team_number", "match_number", "qual_number"]:
                        if key not in scouting_metrics:
                            scouting_metrics[key] = []
                        scouting_metrics[key].append(value)
            
            # Calculate averages 
            for metric, values in scouting_metrics.items():
                if values:
                    team_info["metrics"][metric] = sum(values) / len(values)
            
            # Add Statbotics metrics if available
            statbotics_info = team_data.get("statbotics_info", {})
            for key, value in statbotics_info.items():
                if isinstance(value, (int, float)):
                    team_info["metrics"][f"statbotics_{key}"] = value
            
            # Add ranking info if available
            ranking_info = team_data.get("ranking_info", {})
            rank = ranking_info.get("rank")
            if rank is not None:
                team_info["rank"] = rank
                
            # Add record if available
            record = ranking_info.get("record")
            if record:
                team_info["record"] = record
            
            # Add qualitative notes from superscouting
            superscouting_notes = []
            for entry in team_data.get("superscouting_data", []):
                if "strategy_notes" in entry and entry["strategy_notes"]:
                    superscouting_notes.append(entry["strategy_notes"])
                if "comments" in entry and entry["comments"]:
                    superscouting_notes.append(entry["comments"])
            
            if superscouting_notes:
                team_info["superscouting_notes"] = superscouting_notes[:3]  # Limit to 3 notes for context size
            
            condensed_teams.append(team_info)
        
        return condensed_teams
    
    def _get_team_by_number(self, team_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific team's data by team number.
        
        Args:
            team_number: The team number to look up
            
        Returns:
            Dictionary with team data or None if not found
        """
        team_str = str(team_number)
        return self.teams_data.get(team_str)
    
    def _calculate_similarity_score(self, team1_metrics: Dict[str, float], team2_metrics: Dict[str, float]) -> float:
        """
        Calculate a similarity score between two teams based on their metrics.
        Higher score means more similar teams.
        
        Args:
            team1_metrics: Metrics dictionary for first team
            team2_metrics: Metrics dictionary for second team
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Find common metrics
        common_metrics = set(team1_metrics.keys()).intersection(set(team2_metrics.keys()))
        
        if not common_metrics:
            return 0.0
        
        similarity = 0.0
        for metric in common_metrics:
            # Calculate normalized difference
            max_val = max(abs(team1_metrics[metric]), abs(team2_metrics[metric]))
            if max_val > 0:  # Avoid division by zero
                diff = abs(team1_metrics[metric] - team2_metrics[metric]) / max_val
                similarity += 1.0 - min(diff, 1.0)  # Cap difference at 1.0
            else:
                similarity += 1.0  # Both values are zero, perfect match
        
        # Average similarity across all metrics
        return similarity / len(common_metrics) if common_metrics else 0.0
    
    async def generate_picklist(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        exclude_teams: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Generate a picklist for the specified pick position based on priorities.
        
        Args:
            your_team_number: Your team's number for alliance compatibility
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric IDs and weights to prioritize
            exclude_teams: Optional list of team numbers to exclude (e.g., already picked)
            
        Returns:
            Dict with generated picklist and explanations
        """
        # Check cache first
        cache_key = f"{your_team_number}_{pick_position}_{json.dumps(priorities)}_{json.dumps(exclude_teams or [])}"
        if cache_key in self._picklist_cache:
            return self._picklist_cache[cache_key]
        
        # Get your team data
        your_team = self._get_team_by_number(your_team_number)
        if not your_team:
            return {
                "status": "error",
                "message": f"Your team {your_team_number} not found in dataset"
            }
        
        # Prepare team data for GPT
        teams_data = self._prepare_team_data_for_gpt()
        
        # Filter out excluded teams
        if exclude_teams:
            teams_data = [team for team in teams_data if team["team_number"] not in exclude_teams]
        
        # Create prompt for GPT
        system_prompt = self._create_system_prompt(pick_position)
        user_prompt = self._create_user_prompt(your_team_number, pick_position, priorities, teams_data)
        
        try:
            # Log the prompt (debug only, remove in production)
            print(f"Generating {pick_position} picklist with {len(priorities)} priorities for team {your_team_number}")
            
            # Call GPT with the draft-evaluate-final approach
            response = client.chat.completions.create(
                model="gpt-4.1-mini",  # Use the specified model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            
            # Parse and validate the response
            result = json.loads(response.choices[0].message.content)
            
            # Cache the result
            self._picklist_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"Error generating picklist with GPT: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate picklist: {str(e)}"
            }
    
    def _create_system_prompt(self, pick_position: str) -> str:
        """
        Create the system prompt for GPT based on the pick position.
        
        Args:
            pick_position: 'first', 'second', or 'third'
            
        Returns:
            System prompt string
        """
        position_context = {
            "first": "First pick teams should be overall powerhouse teams that excel in multiple areas.",
            "second": "Second pick teams should complement the first pick and address specific needs.",
            "third": "Third pick teams are more specialized, often focusing on a single critical function."
        }
        
        return f"""You are an expert FRC (FIRST Robotics Competition) strategist specializing in alliance selection. 
You analyze team performance data and generate optimal picklists for alliance selection.

For this task, you are generating a {pick_position} pick list. {position_context.get(pick_position, "")}

Follow a draft-evaluate-final approach:
1. DRAFT: Create an initial ranking based on the metrics and weights provided.
2. EVALUATE: Critically analyze the draft, considering alliance synergy, complementary capabilities, and strategy fit.
3. FINAL: Produce a refined ranking with justifications for each team's position.

Your output must be structured JSON with the following format:
{{
  "status": "success",
  "picklist": [
    {{
      "team_number": int,
      "nickname": string,
      "score": float,
      "reasoning": string
    }},
    ...
  ],
  "analysis": {{
    "draft_reasoning": string,
    "evaluation": string,
    "final_recommendations": string
  }}
}}

Be concise but insightful in your reasoning. Focus on how each team would contribute to a successful alliance.
"""
    
    def _create_user_prompt(
        self, 
        your_team_number: int, 
        pick_position: str, 
        priorities: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]]
    ) -> str:
        """
        Create the user prompt for GPT with all necessary context.
        
        Args:
            your_team_number: Your team's number
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric priorities with weights
            teams_data: Prepared team data for context
            
        Returns:
            User prompt string
        """
        # Find your team's data
        your_team_info = next((team for team in teams_data if team["team_number"] == your_team_number), None)
        
        prompt = f"""Generate a {pick_position.upper()} PICK picklist for FRC team {your_team_number}.

YOUR TEAM PROFILE:
{json.dumps(your_team_info, indent=2) if your_team_info else "Team data not available"}

PRIORITY METRICS (with weights from 0.5 to 3.0):
{json.dumps(priorities, indent=2)}

GAME CONTEXT:
{self.game_context or "Game context not available"}

AVAILABLE TEAMS:
{json.dumps(teams_data, indent=2)}

For this {pick_position} pick, please:
1. DRAFT an initial ranking focused purely on the priority metrics
2. EVALUATE the ranking critically, considering alliance synergy with team {your_team_number}
3. FINALIZE a picklist of the top 15 teams with scores and reasoning

Consider the relative importance of each metric based on their weights. Higher weights (closer to 3.0) should have more influence than lower weights (closer to 0.5).

Provide a comprehensive analysis explaining your ranking decisions and strategic considerations.
"""
        return prompt

    def merge_and_update_picklist(
        self,
        picklist: List[Dict[str, Any]],
        user_rankings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge an existing picklist with user-defined rankings.
        
        Args:
            picklist: Original generated picklist
            user_rankings: User-modified rankings with team numbers and positions
            
        Returns:
            Updated picklist with user modifications
        """
        # Create a map of team numbers to their picklist entries
        team_map = {entry["team_number"]: entry for entry in picklist}
        
        # Create a new picklist based on user rankings
        new_picklist = []
        for ranking in user_rankings:
            team_number = ranking["team_number"]
            if team_number in team_map:
                # Add the team with original data but at the new position
                new_picklist.append(team_map[team_number])
            else:
                # Team not in original picklist, add with minimal info
                new_picklist.append({
                    "team_number": team_number,
                    "nickname": ranking.get("nickname", f"Team {team_number}"),
                    "score": ranking.get("score", 0.0),
                    "reasoning": "Manually added by user"
                })
        
        return new_picklist