# backend/app/services/picklist_gpt_service.py

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("picklist_gpt_service")

GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

class PicklistGPTService:
    """
    Service for handling OpenAI GPT integration specific to picklist generation.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    """

    def __init__(self):
        """Initialize the picklist GPT service with OpenAI client and token encoder."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.token_encoder = tiktoken.encoding_for_model("gpt-4-turbo")
        self.max_tokens_limit = 100000
        
    def prepare_team_data_for_gpt(self, teams_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare team data in a format optimized for GPT analysis.
        
        Args:
            teams_data: Dictionary of team data from the unified dataset
            
        Returns:
            List of team data formatted for GPT prompts
        """
        formatted_teams = []
        
        for team_number, team_data in teams_data.items():
            if isinstance(team_data, dict) and "team_number" in team_data:
                # Extract relevant metrics and format for GPT
                formatted_team = {
                    "team_number": team_data["team_number"],
                    "nickname": team_data.get("nickname", f"Team {team_data['team_number']}"),
                }
                
                # Add performance metrics if available
                if "metrics" in team_data and isinstance(team_data["metrics"], dict):
                    formatted_team["metrics"] = team_data["metrics"]
                
                # Add any additional relevant data
                for key in ["autonomous", "teleop", "endgame", "defense", "reliability"]:
                    if key in team_data:
                        formatted_team[key] = team_data[key]
                
                formatted_teams.append(formatted_team)
        
        return formatted_teams
    
    def check_token_count(self, system_prompt: str, user_prompt: str, max_tokens: int = None) -> None:
        """
        Check if the combined prompts exceed token limits.
        
        Args:
            system_prompt: The system prompt text
            user_prompt: The user prompt text
            max_tokens: Maximum token limit (defaults to instance limit)
            
        Raises:
            ValueError: If token count exceeds limit
        """
        if max_tokens is None:
            max_tokens = self.max_tokens_limit
            
        system_tokens = len(self.token_encoder.encode(system_prompt))
        user_tokens = len(self.token_encoder.encode(user_prompt))
        total_tokens = system_tokens + user_tokens
        
        logger.debug(f"Token count - System: {system_tokens}, User: {user_tokens}, Total: {total_tokens}")
        
        if total_tokens > max_tokens:
            raise ValueError(
                f"Token count {total_tokens} exceeds limit {max_tokens}. "
                f"System: {system_tokens}, User: {user_tokens}"
            )
    
    def create_system_prompt(self, pick_position: str, team_count: int, game_context: Optional[str] = None) -> str:
        """
        Create the system prompt for GPT analysis.
        
        Args:
            pick_position: The pick position ("first", "second", "third")
            team_count: Number of teams to analyze
            game_context: Optional game manual context
            
        Returns:
            Formatted system prompt
        """
        base_prompt = f"""You are an expert FRC (FIRST Robotics Competition) scout and strategist helping create a picklist for alliance selection.

You are analyzing teams for the {pick_position} pick position. Your task is to rank the top {team_count} teams based on:

1. Performance metrics and statistics
2. Strategic value for alliance composition
3. Reliability and consistency
4. Match contribution potential

"""
        
        if game_context:
            base_prompt += f"\nGame Context:\n{game_context}\n\n"
            
        base_prompt += """Your response must be in this exact JSON format:
{
  "p": [[team_number, score, "reasoning"], ...],
  "s": "ok"
}

Where:
- team_number: integer team number
- score: float between 0-100 (higher is better)
- reasoning: brief explanation (max 100 characters)
- Teams ordered by score (highest first)

CRITICAL: Return only valid JSON. No additional text or formatting."""

        return base_prompt
    
    def create_user_prompt(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]],
        team_numbers: Optional[List[int]] = None,
        team_index_map: Optional[Dict[int, int]] = None,
    ) -> str:
        """
        Create the user prompt with team data and priorities.
        
        Args:
            your_team_number: The analyzing team's number
            pick_position: Pick position context
            priorities: Priority weights for different aspects
            teams_data: List of team data for analysis
            team_numbers: Optional list of specific teams to analyze
            team_index_map: Optional mapping for index-based references
            
        Returns:
            Formatted user prompt with team data
        """
        prompt = f"Analyzing for Team {your_team_number} - {pick_position} pick position.\n\n"
        
        # Add priorities section
        if priorities:
            prompt += "PRIORITIES:\n"
            for priority in priorities:
                name = priority.get("name", "Unknown")
                weight = priority.get("weight", 0.0)
                description = priority.get("description", "")
                prompt += f"- {name} (weight: {weight:.2f}): {description}\n"
            prompt += "\n"
        
        # Add teams data
        prompt += "TEAMS TO ANALYZE:\n"
        
        # Filter teams if specific numbers provided
        if team_numbers:
            filtered_teams = [t for t in teams_data if t.get("team_number") in team_numbers]
        else:
            filtered_teams = teams_data
        
        for i, team in enumerate(filtered_teams):
            team_num = team.get("team_number", 0)
            
            # Use index mapping if provided
            display_ref = team_index_map.get(i, team_num) if team_index_map else team_num
            
            prompt += f"Team {display_ref}: {team.get('nickname', f'Team {team_num}')}\n"
            
            # Add metrics if available
            if "metrics" in team and isinstance(team["metrics"], dict):
                for metric, value in team["metrics"].items():
                    prompt += f"  {metric}: {value}\n"
            
            prompt += "\n"
        
        prompt += f"Rank the teams considering the priorities and {pick_position} pick strategy."
        
        return prompt
    
    def create_missing_teams_system_prompt(self, pick_position: str, team_count: int) -> str:
        """
        Create system prompt for ranking missing teams.
        
        Args:
            pick_position: Pick position context
            team_count: Number of missing teams to rank
            
        Returns:
            System prompt for missing teams analysis
        """
        return f"""You are an expert FRC scout analyzing teams NOT yet on the picklist.

Task: Rank the top {team_count} teams that should be added to the existing picklist for {pick_position} pick position.

Focus on:
1. Teams that complement the existing picklist
2. Strategic value additions
3. Filling capability gaps
4. Overall alliance potential

Response format (JSON only):
{{
  "p": [[team_number, score, "reasoning"], ...],
  "s": "ok"
}}

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
        """
        Create user prompt for missing teams analysis.
        
        Args:
            missing_team_numbers: Teams not in current picklist
            ranked_teams: Current picklist teams
            your_team_number: Analyzing team number
            pick_position: Pick position context
            priorities: Priority weights
            teams_data: Team data for analysis
            team_index_map: Optional index mapping
            
        Returns:
            User prompt for missing teams analysis
        """
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
        prompt = f"Team {your_team_number} - {pick_position} pick analysis with reference context.\n\n"
        
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
                    
                    picklist.append({
                        "team_number": team_number,
                        "nickname": nickname,
                        "score": score,
                        "reasoning": reason,
                    })
        
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
            return {
                "status": "error",
                "error": str(e),
                "error_type": "token_limit_exceeded"
            }
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Create and execute API call in thread
                result = await self._execute_api_call(system_prompt, user_prompt)
                
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
                        "attempt": attempt + 1,
                    }
                else:
                    last_exception = Exception(result.get("error", "API call failed"))
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"GPT analysis attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = 1.0 * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        return {
            "status": "error",
            "error": f"GPT analysis failed after {max_retries} attempts: {last_exception}",
            "error_type": "api_failure",
            "attempts": max_retries,
        }
    
    async def _execute_api_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Execute OpenAI API call with threading and timeout.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            
        Returns:
            API call result with status and data
        """
        start_time = time.time()
        result = {"status": "error", "error": "Unknown error"}
        
        def make_api_call():
            nonlocal result
            try:
                response = self.client.chat.completions.create(
                    model=GPT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=4000,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                
                if finish_reason == "length":
                    result = {
                        "status": "error",
                        "error": "Response truncated due to length",
                        "error_type": "response_truncated"
                    }
                    return
                
                # Parse JSON response
                try:
                    response_data = json.loads(content)
                    
                    # Check for overflow status
                    if response_data.get("s") == "overflow" or response_data.get("status") == "overflow":
                        result = {
                            "status": "error",
                            "error": "GPT indicated data overflow",
                            "error_type": "data_overflow"
                        }
                        return
                    
                    result = {
                        "status": "success",
                        "response_data": response_data,
                        "processing_time": time.time() - start_time,
                        "finish_reason": finish_reason,
                    }
                    
                except json.JSONDecodeError as e:
                    result = {
                        "status": "error",
                        "error": f"Invalid JSON response: {e}",
                        "error_type": "json_parse_error",
                        "raw_content": content
                    }
                    
            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    result = {
                        "status": "error",
                        "error": f"Rate limit exceeded: {e}",
                        "error_type": "rate_limit"
                    }
                else:
                    result = {
                        "status": "error",
                        "error": f"API call failed: {e}",
                        "error_type": "api_error"
                    }
        
        # Execute in thread with timeout
        thread = threading.Thread(target=make_api_call)
        thread.start()
        
        # Wait for completion with timeout (30 seconds)
        thread.join(timeout=30.0)
        
        if thread.is_alive():
            # Timeout occurred
            result = {
                "status": "error",
                "error": "API call timeout (30 seconds)",
                "error_type": "timeout"
            }
        
        return result