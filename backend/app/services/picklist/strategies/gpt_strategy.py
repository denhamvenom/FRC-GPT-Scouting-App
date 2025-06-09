"""
GPT-based strategy for picklist generation.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import tiktoken
from openai import OpenAI

from ..exceptions import GPTResponseError, TokenLimitExceededError
from ..models import GPTPrompt, RankedTeam
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class GPTStrategy(BaseStrategy):
    """Strategy that uses GPT for intelligent team ranking."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 100000,
        temperature: float = 0.1,
    ):
        """
        Initialize GPT strategy.

        Args:
            api_key: OpenAI API key (defaults to env var)
            model: GPT model to use
            max_tokens: Maximum tokens allowed
            temperature: Model temperature for randomness
        """
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Only initialize client if API key is available
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("No OpenAI API key provided - GPT strategy will not function")
        
        self.token_encoder = tiktoken.encoding_for_model("gpt-4-turbo")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.token_encoder.encode(text))

    def check_token_limit(self, system_prompt: str, user_prompt: str) -> None:
        """
        Check if prompts exceed token limit.

        Raises:
            TokenLimitExceededError: If token limit exceeded
        """
        total_tokens = self.count_tokens(system_prompt) + self.count_tokens(user_prompt)
        if total_tokens > self.max_tokens:
            raise TokenLimitExceededError(
                f"Token limit exceeded: {total_tokens} > {self.max_tokens}",
                token_count=total_tokens,
                max_tokens=self.max_tokens,
            )

    def create_system_prompt(self, pick_position: str, team_count: int) -> str:
        """Create system prompt for GPT."""
        role_descriptions = {
            "first": "a strong, versatile robot that excels in multiple game aspects",
            "second": "a reliable partner that complements existing alliance strengths",
            "third": "a specialized robot that fills specific alliance needs",
        }

        return f"""You are an expert FRC (FIRST Robotics Competition) strategist analyzing teams for alliance selection.

PICK POSITION: You are picking the {pick_position} robot for your alliance.
This means you need {role_descriptions.get(pick_position, 'a strategic partner')}.

TASK: Rank exactly {team_count} teams based on:
1. Their overall performance metrics
2. Strategic fit for the {pick_position} pick position
3. Reliability and consistency
4. How well they complement your team

OUTPUT FORMAT: You MUST respond with ONLY a valid JSON object in this exact format:
{{
  "p": [
    [team_number, score, "brief reason"],
    [team_number, score, "brief reason"],
    ...
  ],
  "s": "ok"
}}

CRITICAL RULES:
- Include ALL {team_count} teams exactly once - NO DUPLICATES, NO MISSING TEAMS
- Score from 0-100 (higher is better)
- Keep reasons under 100 characters
- Consider game-specific strategies
- Account for your team's strengths/weaknesses
- Return ONLY the JSON object, no other text
- VERIFY: Your output must contain exactly {team_count} unique team numbers"""

    def create_user_prompt(
        self,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        priorities: List[Dict[str, Any]],
        game_context: Optional[str] = None,
    ) -> str:
        """Create user prompt with team data."""
        # Find your team's data
        your_team = next(
            (t for t in teams_data if t.get("team_number") == your_team_number), None
        )

        prompt_parts = []

        # Add game context if available
        if game_context:
            logger.info(f"Adding game context to GPT prompt: {len(game_context)} characters")
            prompt_parts.append(f"GAME CONTEXT:\n{game_context}\n")
        else:
            logger.warning("No game context available to send to GPT")

        # Add your team info
        if your_team:
            prompt_parts.append(f"YOUR TEAM: {your_team_number} - {your_team.get('nickname', '')}")
            if your_team.get("metrics"):
                prompt_parts.append("Your key metrics:")
                for metric, value in list(your_team["metrics"].items())[:5]:
                    prompt_parts.append(f"- {metric}: {value:.2f}")
            prompt_parts.append("")

        # Add priorities
        prompt_parts.append("PRIORITIES (higher weight = more important):")
        for priority in priorities:
            metric_id = priority.get("id", priority.get("metric_id"))
            weight = priority.get("weight", 1.0)
            prompt_parts.append(f"- {metric_id}: weight {weight}")
        prompt_parts.append("")

        # Add team data in compact format
        prompt_parts.append(f"TEAMS TO RANK ({len(teams_data)} teams):")
        for team in teams_data:
            team_line = f"Team {team['team_number']}"
            if team.get("nickname"):
                team_line += f" ({team['nickname']})"

            # Add key metrics
            if team.get("metrics"):
                metric_strs = []
                for metric_id in [p.get("id", p.get("metric_id")) for p in priorities[:5]]:
                    if metric_id in team["metrics"]:
                        metric_strs.append(f"{metric_id}:{team['metrics'][metric_id]:.1f}")
                if metric_strs:
                    team_line += f" | {', '.join(metric_strs)}"

            # Add rank if available
            if team.get("rank"):
                team_line += f" | Rank: {team['rank']}"

            prompt_parts.append(team_line)

        return "\n".join(prompt_parts)

    def parse_gpt_response(self, response_text: str, teams_data: List[Dict[str, Any]]) -> List[RankedTeam]:
        """
        Parse GPT response into ranked teams.

        Args:
            response_text: Raw GPT response
            teams_data: Original teams data for lookups

        Returns:
            List of ranked teams

        Raises:
            GPTResponseError: If parsing fails
        """
        try:
            # Clean the response text - sometimes there might be extra whitespace or formatting
            clean_response = response_text.strip()
            
            # Remove markdown code block formatting if present
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]  # Remove ```
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]  # Remove trailing ```
            
            clean_response = clean_response.strip()
            
            # Log the length and first few chars for debugging
            logger.debug(f"Response length: {len(clean_response)}, first 100 chars: {clean_response[:100]}")
            
            # Try to parse as JSON
            response_data = json.loads(clean_response)

            if "p" not in response_data:
                logger.error(f"Response missing 'p' field. Available fields: {list(response_data.keys())}")
                raise GPTResponseError("Response missing 'p' field", response_text)

            ranked_teams = []
            seen_teams = set()

            for entry in response_data["p"]:
                if len(entry) < 3:
                    logger.warning(f"Entry has insufficient elements: {entry}")
                    continue

                try:
                    team_number = int(entry[0])
                    score = float(entry[1])
                    reasoning = str(entry[2])
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing entry {entry}: {e}")
                    continue

                # Skip duplicates
                if team_number in seen_teams:
                    logger.warning(f"Skipping duplicate team {team_number}")
                    continue

                seen_teams.add(team_number)

                # Find team data
                team_data = next(
                    (t for t in teams_data if t["team_number"] == team_number), None
                )

                if team_data:
                    ranked_teams.append(
                        RankedTeam(
                            team_number=team_number,
                            nickname=team_data.get("nickname", f"Team {team_number}"),
                            score=score,
                            reasoning=reasoning,
                            metrics=team_data.get("metrics", {}),
                        )
                    )
                else:
                    logger.warning(f"Team {team_number} not found in teams_data")

            logger.info(f"Successfully parsed {len(ranked_teams)} teams from GPT response")
            return ranked_teams

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            raise GPTResponseError(f"Invalid JSON response: {e}", response_text)
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")
            logger.error(f"Response text: {response_text}")
            raise GPTResponseError(f"Response parsing failed: {e}", response_text)

    async def generate_ranking(
        self,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        game_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate team ranking using GPT.

        Args:
            teams_data: List of team data
            your_team_number: Your team's number
            pick_position: Pick position
            priorities: Priority metrics
            game_context: Optional game context

        Returns:
            List of ranked teams as dictionaries
        """
        # Validate inputs
        self.validate_inputs(teams_data, your_team_number, pick_position, priorities)

        # Create prompts
        system_prompt = self.create_system_prompt(pick_position, len(teams_data))
        user_prompt = self.create_user_prompt(
            teams_data, your_team_number, priorities, game_context
        )

        # Check token limit
        self.check_token_limit(system_prompt, user_prompt)

        logger.info(f"Generating picklist for {len(teams_data)} teams using GPT")
        logger.info(f"System prompt length: {len(system_prompt)} characters")
        logger.info(f"User prompt length: {len(user_prompt)} characters")
        logger.info(f"User prompt contains game context: {'GAME CONTEXT:' in user_prompt}")

        if not self.client:
            raise GPTResponseError("No OpenAI API key available")

        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4000,
                temperature=self.temperature,
            )

            response_text = response.choices[0].message.content
            
            # Log the raw response for debugging
            logger.debug(f"Raw GPT response: {response_text}")
            
            # Check if response is empty or None
            if not response_text or not response_text.strip():
                raise GPTResponseError("Empty response from GPT", response_text or "")

            # Parse response
            ranked_teams = self.parse_gpt_response(response_text, teams_data)

            # Sort by score
            ranked_teams = self.sort_by_score(ranked_teams)

            # Convert to dictionary format
            return [
                {
                    "team_number": team.team_number,
                    "nickname": team.nickname,
                    "score": team.score,
                    "reasoning": team.reasoning,
                }
                for team in ranked_teams
            ]

        except Exception as e:
            logger.error(f"GPT ranking failed: {e}")
            raise GPTResponseError(f"GPT ranking failed: {e}")