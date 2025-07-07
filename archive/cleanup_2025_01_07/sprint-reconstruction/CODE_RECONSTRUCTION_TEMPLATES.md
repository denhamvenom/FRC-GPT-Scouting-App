# CODE RECONSTRUCTION TEMPLATES

This file contains exact code templates extracted from the original system to be implemented during reconstruction.

---

## 🔧 TEMPLATE 1: Ultra-Compact GPT Service (picklist_gpt_service.py)

### Complete Method Replacements:

```python
# backend/app/services/picklist_gpt_service.py

import asyncio
import json
import logging
import os
import threading
import time
import re
from typing import Any, Dict, List, Optional, Tuple

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("picklist_gpt_service")

GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

class PicklistGPTService:
    """
    Service for handling OpenAI GPT integration with original proven algorithms.
    Restored from original system for maximum reliability.
    """

    def __init__(self):
        """Initialize the picklist GPT service with original configuration."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.token_encoder = tiktoken.encoding_for_model("gpt-4-turbo")
        self.max_tokens_limit = 100000
        self.game_context = None  # Can be set by external services
        
    def check_token_count(self, system_prompt: str, user_prompt: str, max_tokens: int = None) -> None:
        """ORIGINAL TOKEN VALIDATION - EXACT RESTORATION"""
        if max_tokens is None:
            max_tokens = self.max_tokens_limit
            
        try:
            system_tokens = len(self.token_encoder.encode(system_prompt))
            user_tokens = len(self.token_encoder.encode(user_prompt))
            total_tokens = system_tokens + user_tokens
            
            logger.info(f"Token count: system={system_tokens}, user={user_tokens}, total={total_tokens}")
            
            if total_tokens > max_tokens:
                raise ValueError(
                    f"Prompt too large: {total_tokens} tokens exceeds limit of {max_tokens}. Consider batching teams or trimming fields."
                )
        except Exception as e:
            logger.warning(f"Token counting failed: {str(e)}, proceeding without check")
    
    def create_system_prompt(self, pick_position: str, team_count: int, game_context: Optional[str] = None, use_ultra_compact: bool = True) -> str:
        """ORIGINAL SYSTEM PROMPT - EXACT RESTORATION"""
        
        position_context = {
            "first": "First pick teams should be overall powerhouse teams that excel in multiple areas.",
            "second": "Second pick teams should complement the first pick and address specific needs.",
            "third": "Third pick teams are more specialized, often focusing on a single critical function.",
        }
        
        context_note = position_context.get(pick_position, "")
        
        if use_ultra_compact:
            # ORIGINAL ULTRA-COMPACT FORMAT - CRITICAL FOR TOKEN OPTIMIZATION
            prompt = f"""You are GPT‑4.1, an FRC alliance strategist.
Return one‑line minified JSON:
{{"p":[[index,score,"reason"]…],"s":"ok"}}

CRITICAL RULES
• Rank all {team_count} indices, each exactly once.  
• Use indices 1-{team_count} from TEAM_INDEX_MAP exactly once.
• Sort by weighted performance, then synergy with Team {{your_team_number}} for {pick_position} pick.  
• Each reason must be ≤10 words, NO REPETITION, cite 1 metric (e.g. "Strong auto: 3.2 avg").
• NO repetitive words or phrases. Be concise and specific.
• If you cannot complete all teams due to length limits, respond only {{"s":"overflow"}}.

{context_note}"""
            
            if game_context:
                prompt += f"\n\nGame Context:\n{game_context}\n"
                
            prompt += f"""
EXAMPLE: {{"p":[[1,8.5,"Strong auto: 2.8 avg"],[2,7.9,"Consistent defense"],[3,6.2,"Reliable endgame"]],"s":"ok"}}"""
            
            return prompt
        else:
            # Fallback to standard format for smaller requests
            return self._create_standard_format_prompt(pick_position, team_count, game_context)
    
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
    
    def _prepare_teams_with_scores(self, teams_data: List[Dict[str, Any]], priorities: List[Dict[str, Any]], team_index_map: Optional[Dict[int, int]] = None) -> List[Dict[str, Any]]:
        """ORIGINAL TEAM PREPARATION WITH WEIGHTED SCORES"""
        
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
                    "weighted_score": weighted_score
                }
                
                # Add condensed metrics
                if "metrics" in team and isinstance(team["metrics"], dict):
                    team_with_score["metrics"] = team["metrics"]
                    
                teams_with_scores.append(team_with_score)
        else:
            # Standard format without indices
            for team in teams_data:
                weighted_score = self._calculate_weighted_score(team, priorities)
                team_with_score = {
                    "team_number": team["team_number"],
                    "nickname": team.get("nickname", f"Team {team['team_number']}"),
                    "weighted_score": weighted_score
                }
                
                if "metrics" in team and isinstance(team["metrics"], dict):
                    team_with_score["metrics"] = team["metrics"]
                    
                teams_with_scores.append(team_with_score)
        
        return teams_with_scores
    
    def _calculate_weighted_score(self, team_data: Dict[str, Any], priorities: List[Dict[str, Any]]) -> float:
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

    async def analyze_teams(
        self,
        system_prompt: str,
        user_prompt: str,
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """ORIGINAL ANALYSIS WITH FULL ERROR RECOVERY"""
        
        # Check token count
        try:
            self.check_token_count(system_prompt, user_prompt)
        except ValueError as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": "token_limit_exceeded"
            }
        
        # Execute with retry logic
        result = await self._execute_api_call_with_retry(system_prompt, user_prompt, max_retries)
        
        if result["status"] == "success":
            # Parse response with full recovery system
            picklist = self.parse_response_with_recovery(
                result.get("response_data", {}),
                result.get("raw_content", ""),
                teams_data,
                team_index_map
            )
            
            return {
                "status": "success",
                "picklist": picklist,
                "response_data": result["response_data"],
                "processing_time": result.get("processing_time", 0),
                "finish_reason": result.get("finish_reason", ""),
            }
        else:
            return result

    async def _execute_api_call_with_retry(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """ORIGINAL EXPONENTIAL BACKOFF RETRY LOGIC - EXACT RESTORATION"""
        
        initial_delay = 1.0
        retry_count = 0
        start_time = time.time()
        
        while retry_count <= max_retries:
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
                    return {
                        "status": "error",
                        "error": "Response truncated due to length",
                        "error_type": "response_truncated"
                    }
                
                # Parse JSON response
                try:
                    response_data = json.loads(content)
                    
                    # Check for overflow status
                    if response_data.get("s") == "overflow" or response_data.get("status") == "overflow":
                        return {
                            "status": "error",
                            "error": "GPT indicated data overflow",
                            "error_type": "data_overflow"
                        }
                    
                    return {
                        "status": "success",
                        "response_data": response_data,
                        "raw_content": content,
                        "processing_time": time.time() - start_time,
                        "finish_reason": finish_reason,
                    }
                    
                except json.JSONDecodeError as e:
                    return {
                        "status": "error",
                        "error": f"Invalid JSON response: {e}",
                        "error_type": "json_parse_error",
                        "raw_content": content
                    }
                    
            except Exception as e:
                # CRITICAL: Check if it's a rate limit error
                error_str = str(e)
                is_rate_limit = "429" in error_str
                
                if is_rate_limit and retry_count < max_retries:
                    retry_count += 1
                    delay = initial_delay * (2**retry_count)  # Exponential backoff: 2s, 4s, 8s
                    
                    logger.warning(
                        f"Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {retry_count}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    return {
                        "status": "error",
                        "error": f"API call failed: {str(e)}",
                        "error_type": "rate_limit" if is_rate_limit else "api_error"
                    }
        
        return {
            "status": "error",
            "error": f"Failed after {max_retries} retries",
            "error_type": "max_retries_exceeded"
        }

    def parse_response_with_recovery(
        self,
        response_data: Dict[str, Any],
        raw_content: str,
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """ORIGINAL 4-LAYER ERROR RECOVERY SYSTEM - EXACT RESTORATION"""
        
        # Layer 1: Ultra-compact format parsing
        if "p" in response_data and isinstance(response_data["p"], list):
            logger.debug("Using ultra-compact format parsing")
            return self._parse_ultra_compact_format(response_data, teams_data, team_index_map)
        
        # Layer 2: Standard compact format parsing
        if "picklist" in response_data:
            logger.debug("Using standard format parsing")
            return self._parse_standard_format(response_data, teams_data, team_index_map)
        
        # Layer 3: Regex extraction from malformed JSON
        logger.warning("Attempting regex extraction from malformed response")
        return self._regex_extract_teams(raw_content, teams_data, team_index_map)

    def _parse_ultra_compact_format(self, response_data: Dict[str, Any], teams_data: List[Dict[str, Any]], team_index_map: Optional[Dict[int, int]] = None) -> List[Dict[str, Any]]:
        """ORIGINAL ULTRA-COMPACT FORMAT PARSER"""
        
        picklist = []
        seen_teams = set()
        
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

    def _parse_standard_format(self, response_data: Dict[str, Any], teams_data: List[Dict[str, Any]], team_index_map: Optional[Dict[int, int]] = None) -> List[Dict[str, Any]]:
        """ORIGINAL STANDARD FORMAT PARSER"""
        
        picklist = []
        seen_teams = set()
        
        for team_entry in response_data["picklist"]:
            team_number = team_entry.get("team_number")
            if team_number and team_number not in seen_teams:
                seen_teams.add(team_number)
                
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
                    "score": team_entry.get("score", 0.0),
                    "reasoning": team_entry.get("reasoning", ""),
                })
        
        return picklist

    def _regex_extract_teams(self, content: str, teams_data: List[Dict[str, Any]], team_index_map: Optional[Dict[int, int]] = None) -> List[Dict[str, Any]]:
        """ORIGINAL REGEX EXTRACTION PATTERNS - EXACT RESTORATION"""
        
        # Pattern for ultra-compact format: [index, score, "reason"]
        compact_pattern = r'\[\s*(\d+)\s*,\s*([\d\.]+)\s*,\s*"([^"]*)"\s*\]'
        matches = re.findall(compact_pattern, content)
        
        picklist = []
        seen_teams = set()
        
        for match in matches:
            try:
                index_or_team = int(match[0])
                score = float(match[1])
                reason = match[2]
                
                # Convert index to team number if mapping provided
                if team_index_map and index_or_team in team_index_map:
                    team_number = team_index_map[index_or_team]
                    logger.debug(f"Regex: Mapped index {index_or_team} to team {team_number}")
                else:
                    team_number = index_or_team
                
                if team_number not in seen_teams:
                    seen_teams.add(team_number)
                    
                    # Get team data
                    team_data = next(
                        (t for t in teams_data if t.get("team_number") == team_number), None
                    )
                    nickname = team_data.get("nickname", f"Team {team_number}") if team_data else f"Team {team_number}"
                    
                    picklist.append({
                        "team_number": team_number,
                        "nickname": nickname,
                        "score": score,
                        "reasoning": reason,
                    })
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse regex match {match}: {e}")
                continue
        
        return sorted(picklist, key=lambda x: x["score"], reverse=True)

    def _create_standard_format_prompt(self, pick_position: str, team_count: int, game_context: Optional[str] = None) -> str:
        """Fallback standard format prompt for smaller requests"""
        
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
  "picklist": [
    {"team_number": 123, "score": 95.5, "reasoning": "Strong auto and reliable"},
    {"team_number": 456, "score": 87.2, "reasoning": "Excellent defense"}
  ],
  "status": "ok"
}

Where:
- team_number: integer team number
- score: float between 0-100 (higher is better)
- reasoning: brief explanation (max 50 characters)
- Teams ordered by score (highest first)

CRITICAL: Return only valid JSON. No additional text or formatting."""

        return base_prompt

    # Missing teams methods (simplified for space)
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
```

---

## 🔧 TEMPLATE 2: Processing Strategy Restoration (picklist_generator_service.py)

### Key Method Updates:

```python
# backend/app/services/picklist_generator_service.py

def _determine_processing_strategy(self, teams_data: List[Dict[str, Any]], use_batching: Optional[bool] = None) -> Tuple[bool, str]:
    """ORIGINAL AUTOMATIC BATCHING DECISION - EXACT RESTORATION"""
    
    team_count = len(teams_data)
    
    # ORIGINAL LOGIC: Automatic batching for >20 teams
    if use_batching is None:
        # Auto-decide based on team count (ORIGINAL THRESHOLD)
        should_batch = team_count > 20
        reason = f"Auto-selected {'batching' if should_batch else 'single'} for {team_count} teams (threshold: 20)"
    else:
        # Respect explicit user choice but warn if suboptimal
        should_batch = use_batching
        reason = f"User-specified {'batching' if should_batch else 'single'} for {team_count} teams"
        
        if team_count > 20 and not use_batching:
            logger.warning(f"Single processing forced for {team_count} teams - may encounter rate limits")
        elif team_count <= 15 and use_batching:
            logger.warning(f"Batching forced for only {team_count} teams - may be inefficient")
    
    logger.info(f"Processing strategy: {reason}")
    return should_batch, reason

def _calculate_optimal_batch_size(self, team_count: int, priorities_count: int) -> int:
    """ORIGINAL BATCH SIZE CALCULATION - EXACT RESTORATION"""
    
    # ORIGINAL CONSTANTS
    base_batch_size = 20
    max_batch_size = 25
    min_batch_size = 15
    
    # Adjust based on priorities complexity (original had this logic)
    if priorities_count > 5:
        adjusted_size = base_batch_size - 2
    elif priorities_count > 3:
        adjusted_size = base_batch_size - 1
    else:
        adjusted_size = base_batch_size
    
    # Ensure within bounds
    final_size = max(min_batch_size, min(max_batch_size, adjusted_size))
    
    logger.debug(f"Calculated batch size: {final_size} for {team_count} teams with {priorities_count} priorities")
    return final_size

async def _orchestrate_single_processing(
    self, teams_data, your_team_number, pick_position, normalized_priorities, cache_key
) -> Dict[str, Any]:
    """ORIGINAL SINGLE PROCESSING WITH INDEX MAPPING - EXACT RESTORATION"""
    
    # ALWAYS use index mapping for single processing (original did this)
    team_index_map = {}
    for index, team in enumerate(teams_data, 1):
        team_index_map[index] = team["team_number"]
    
    logger.info(f"Single processing {len(teams_data)} teams with index mapping to prevent duplicates")
    
    # Create prompts with index mapping
    system_prompt = self.gpt_service.create_system_prompt(
        pick_position, len(teams_data), self.game_context, use_ultra_compact=True
    )
    
    user_prompt, _ = self.gpt_service.create_user_prompt(
        your_team_number, pick_position, normalized_priorities, teams_data,
        team_numbers=[t["team_number"] for t in teams_data],
        force_index_mapping=True
    )
    
    # Execute analysis with full error recovery
    analysis_result = await self.gpt_service.analyze_teams(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        teams_data=teams_data,
        team_index_map=team_index_map
    )
    
    if analysis_result.get("status") == "success":
        picklist = analysis_result["picklist"]
        
        # ORIGINAL MISSING TEAM DETECTION AND HANDLING
        final_picklist = await self._handle_missing_teams(
            picklist, teams_data, your_team_number, pick_position, normalized_priorities
        )
        
        return {
            "status": "success", 
            "picklist": final_picklist,
            "total_teams": len(final_picklist), 
            "cache_key": cache_key,
            "processing_strategy": "single_with_index_mapping"
        }
    else:
        return {
            "status": "error", 
            "error": analysis_result.get("error", "Analysis failed"),
            "cache_key": cache_key
        }

async def _handle_missing_teams(
    self,
    picklist: List[Dict[str, Any]],
    all_teams_data: List[Dict[str, Any]],
    your_team_number: int,
    pick_position: str,
    priorities: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """ORIGINAL MISSING TEAM HANDLING - EXACT RESTORATION"""
    
    # ORIGINAL SET DIFFERENCE CALCULATION
    available_team_numbers = {team["team_number"] for team in all_teams_data}
    ranked_team_numbers = {team["team_number"] for team in picklist}
    missing_team_numbers = available_team_numbers - ranked_team_numbers
    
    if not missing_team_numbers:
        logger.info("No missing teams detected")
        return picklist
    
    logger.warning(f"Missing {len(missing_team_numbers)} teams: {sorted(missing_team_numbers)}")
    
    # ORIGINAL MISSING TEAM RANKING WITH SMALLER BATCH SIZE
    missing_teams_data = [t for t in all_teams_data if t["team_number"] in missing_team_numbers]
    
    try:
        missing_result = await self.gpt_service.analyze_teams(
            system_prompt=self.gpt_service.create_missing_teams_system_prompt(
                pick_position, len(missing_teams_data)
            ),
            user_prompt=self.gpt_service.create_missing_teams_user_prompt(
                list(missing_team_numbers), picklist, your_team_number,
                pick_position, priorities, missing_teams_data
            ),
            teams_data=missing_teams_data
        )
        
        if missing_result.get("status") == "success":
            missing_picklist = missing_result.get("picklist", [])
            logger.info(f"Successfully ranked {len(missing_picklist)} missing teams")
            
            # MERGE WITH ORIGINAL PICKLIST
            combined_picklist = picklist + missing_picklist
            
            # ORIGINAL DEDUPLICATION AND SORTING
            seen_teams = {}
            for team in combined_picklist:
                team_number = team.get("team_number")
                if team_number not in seen_teams or team.get("score", 0) > seen_teams[team_number].get("score", 0):
                    seen_teams[team_number] = team
            
            final_list = sorted(seen_teams.values(), key=lambda x: x.get("score", 0), reverse=True)
            logger.info(f"Final picklist: {len(final_list)} teams after missing team integration")
            return final_list
        
    except Exception as e:
        logger.error(f"Failed to rank missing teams: {str(e)}")
    
    logger.warning("Using original picklist without missing teams")
    return picklist
```

---

## 🔧 TEMPLATE 3: Performance Optimization Service

### Complete Service Implementation:

```python
# backend/app/services/performance_optimization_service.py

import logging
from typing import Dict, List, Any, Optional
import statistics

logger = logging.getLogger("performance_optimization_service")

class PerformanceOptimizationService:
    """
    Service for optimizing team data and token usage.
    Restored from original system algorithms.
    """
    
    def __init__(self, cache_instance=None):
        """Initialize with cache reference for result storage."""
        self._cache = cache_instance or {}
        
    def condense_team_data_for_gpt(self, teams_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ORIGINAL TEAM DATA CONDENSATION - EXACT RESTORATION"""
        
        condensed_teams = []
        
        for team_data in teams_data:
            condensed_team = {
                "team_number": team_data["team_number"],
                "nickname": team_data.get("nickname", f"Team {team_data['team_number']}")
            }
            
            # ORIGINAL METRICS CONDENSATION
            if "scouting_data" in team_data and team_data["scouting_data"]:
                condensed_team["metrics"] = self._condense_metrics(team_data["scouting_data"])
            elif "metrics" in team_data:
                # Already condensed metrics
                condensed_team["metrics"] = team_data["metrics"]
            
            # ORIGINAL STATBOTICS INTEGRATION
            if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
                for key, value in team_data["statbotics"].items():
                    condensed_team[f"statbotics_{key}"] = value
            
            # ORIGINAL SUPERSCOUTING LIMITATION (1 note max)
            if "superscouting" in team_data and team_data["superscouting"]:
                notes = team_data["superscouting"]
                if isinstance(notes, list) and notes:
                    condensed_team["superscouting"] = notes[0][:100]  # Take only first note, limit to 100 chars
                elif isinstance(notes, str):
                    condensed_team["superscouting"] = notes[:100]  # Limit to 100 chars
            
            condensed_teams.append(condensed_team)
        
        logger.debug(f"Condensed {len(teams_data)} teams for GPT processing")
        return condensed_teams

    def _condense_metrics(self, scouting_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """ORIGINAL METRICS AVERAGING - EXACT RESTORATION"""
        
        if not scouting_data:
            return {}
        
        # ORIGINAL ESSENTIAL FIELDS ONLY
        essential_fields = [
            "auto_points", "teleop_points", "endgame_points",
            "auto_mobility", "auto_docking", "teleop_scoring_rate",
            "defense_rating", "driver_skill", "consistency_rating",
            "auto_gamepieces", "teleop_gamepieces", "endgame_climb",
            "penalty_count", "foul_count", "tech_foul_count"
        ]
        
        metrics = {}
        for field in essential_fields:
            values = []
            for match in scouting_data:
                if isinstance(match.get(field), (int, float)):
                    values.append(match[field])
            
            if values:
                # Use median for more robust average with outliers
                if len(values) >= 3:
                    metrics[field] = round(statistics.median(values), 2)
                else:
                    metrics[field] = round(sum(values) / len(values), 2)
        
        return metrics

    def calculate_weighted_score(self, team_data: Dict[str, Any], priorities: List[Dict[str, Any]]) -> float:
        """ORIGINAL WEIGHTED SCORING - EXACT RESTORATION"""
        
        if not priorities:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for priority in priorities:
            field_name = priority.get("id", "")
            weight = priority.get("weight", 1.0)
            
            # ORIGINAL FIELD MAPPING
            field_value = self._extract_field_value(team_data, field_name)
            
            if field_value is not None:
                total_score += field_value * weight
                total_weight += weight
        
        return round(total_score / total_weight if total_weight > 0 else 0.0, 2)

    def _extract_field_value(self, team_data: Dict[str, Any], field_name: str) -> Optional[float]:
        """ORIGINAL FIELD EXTRACTION LOGIC - EXACT RESTORATION"""
        
        # Try metrics first (most common location)
        if "metrics" in team_data and isinstance(team_data["metrics"], dict):
            if field_name in team_data["metrics"]:
                try:
                    return float(team_data["metrics"][field_name])
                except (ValueError, TypeError):
                    pass
        
        # Try statbotics fields
        if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
            if field_name in team_data["statbotics"]:
                try:
                    return float(team_data["statbotics"][field_name])
                except (ValueError, TypeError):
                    pass
        
        # Try statbotics with prefix
        statbotics_field = f"statbotics_{field_name}"
        if statbotics_field in team_data:
            try:
                return float(team_data[statbotics_field])
            except (ValueError, TypeError):
                pass
        
        # Try direct field access
        if field_name in team_data:
            try:
                return float(team_data[field_name])
            except (ValueError, TypeError):
                pass
        
        # Handle common field mappings
        field_mappings = {
            "auto": "auto_points",
            "teleop": "teleop_points", 
            "endgame": "endgame_points",
            "defense": "defense_rating",
            "consistency": "consistency_rating"
        }
        
        if field_name in field_mappings:
            return self._extract_field_value(team_data, field_mappings[field_name])
        
        return None

    def estimate_token_usage(
        self, 
        teams_count: int, 
        priorities_count: int, 
        use_ultra_compact: bool = True,
        has_game_context: bool = False
    ) -> Dict[str, int]:
        """ORIGINAL TOKEN ESTIMATION - EXACT RESTORATION"""
        
        # ORIGINAL TOKEN ESTIMATION FORMULAS
        base_system_tokens = 200 if use_ultra_compact else 400
        base_user_tokens = 150
        
        # ORIGINAL PER-TEAM TOKEN COSTS
        tokens_per_team = 25 if use_ultra_compact else 45
        tokens_per_priority = 15
        
        # Game context adds tokens
        game_context_tokens = 100 if has_game_context else 0
        
        estimated_input = (
            base_system_tokens + 
            base_user_tokens + 
            (teams_count * tokens_per_team) + 
            (priorities_count * tokens_per_priority) +
            game_context_tokens
        )
        
        # ORIGINAL OUTPUT ESTIMATION
        estimated_output = teams_count * (8 if use_ultra_compact else 15)
        
        total_tokens = estimated_input + estimated_output
        
        # Add safety margin
        total_with_margin = int(total_tokens * 1.1)
        
        return {
            "input_tokens": estimated_input,
            "output_tokens": estimated_output,
            "total_tokens": total_tokens,
            "total_with_margin": total_with_margin,
            "optimization_used": "ultra_compact" if use_ultra_compact else "standard",
            "within_limits": total_with_margin < 100000
        }

    def should_use_batching(self, teams_count: int, priorities_count: int) -> bool:
        """ORIGINAL BATCHING DECISION LOGIC"""
        
        # Estimate token usage
        estimation = self.estimate_token_usage(teams_count, priorities_count, use_ultra_compact=True)
        
        # ORIGINAL DECISION FACTORS
        # 1. Team count threshold (primary)
        if teams_count > 20:
            return True
        
        # 2. Token limit threshold (secondary) 
        if estimation["total_with_margin"] > 80000:  # 80% of limit
            return True
        
        # 3. Priority complexity (tertiary)
        if priorities_count > 6:
            return True
        
        return False

    def get_optimal_processing_strategy(
        self, 
        teams_count: int, 
        priorities_count: int,
        user_preference: Optional[bool] = None
    ) -> Dict[str, Any]:
        """COMPREHENSIVE PROCESSING STRATEGY RECOMMENDATION"""
        
        # Calculate recommendations
        auto_batch_recommended = self.should_use_batching(teams_count, priorities_count)
        token_estimation = self.estimate_token_usage(teams_count, priorities_count)
        
        # Determine final strategy
        if user_preference is not None:
            use_batching = user_preference
            strategy_source = "user_specified"
        else:
            use_batching = auto_batch_recommended
            strategy_source = "auto_determined"
        
        # Calculate batch parameters if batching
        batch_size = 20
        if use_batching:
            # Adjust batch size based on priorities
            if priorities_count > 5:
                batch_size = 18
            elif priorities_count > 3:
                batch_size = 19
            else:
                batch_size = 20
        
        return {
            "use_batching": use_batching,
            "strategy_source": strategy_source,
            "batch_size": batch_size,
            "estimated_batches": (teams_count // batch_size) + (1 if teams_count % batch_size else 0) if use_batching else 1,
            "token_estimation": token_estimation,
            "recommendations": {
                "auto_batch_recommended": auto_batch_recommended,
                "reason": self._get_strategy_reason(teams_count, priorities_count, auto_batch_recommended)
            }
        }

    def _get_strategy_reason(self, teams_count: int, priorities_count: int, recommended_batching: bool) -> str:
        """Explain why a strategy was recommended"""
        
        if recommended_batching:
            reasons = []
            if teams_count > 20:
                reasons.append(f"team count ({teams_count}) exceeds threshold (20)")
            
            estimation = self.estimate_token_usage(teams_count, priorities_count)
            if estimation["total_with_margin"] > 80000:
                reasons.append(f"token usage ({estimation['total_with_margin']}) near limit")
            
            if priorities_count > 6:
                reasons.append(f"high priority complexity ({priorities_count})")
            
            return f"Batching recommended: {', '.join(reasons)}"
        else:
            return f"Single processing optimal: {teams_count} teams with {priorities_count} priorities fits comfortably"

    def store_cached_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Store result in performance cache"""
        if self._cache is not None:
            self._cache[cache_key] = result
            logger.debug(f"Cached result for key: {cache_key}")

    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result"""
        if self._cache is not None and cache_key in self._cache:
            logger.debug(f"Retrieved cached result for key: {cache_key}")
            return self._cache[cache_key]
        return None
```

---

## 🔧 TEMPLATE 4: Batch Processing with Threading

### Threading-Based Batch Processing:

```python
# backend/app/services/batch_processing_service.py

import asyncio
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable

from app.services.progress_tracker import ProgressTracker

logger = logging.getLogger("batch_processing_service")

class BatchProcessingService:
    """
    Service for batch processing with threading and progress tracking.
    Restored from original system.
    """
    
    def __init__(self):
        """Initialize batch processing service."""
        self._batch_cache = {}
        
    async def process_batches_with_threading(
        self,
        batches: List[List[Dict[str, Any]]],
        cache_key: str,
        batch_processor_func: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """ORIGINAL THREADING-BASED BATCH PROCESSING - EXACT RESTORATION"""
        
        total_batches = len(batches)
        successful_batches = 0
        combined_results = []
        
        # ORIGINAL PROGRESS TRACKER INITIALIZATION
        progress_tracker = ProgressTracker.create_tracker(cache_key)
        progress_tracker.update(0, f"Starting batch processing ({total_batches} batches)")
        
        # Initialize batch processing status
        self.initialize_batch_processing(cache_key, total_batches)
        
        for batch_idx, batch_teams in enumerate(batches):
            try:
                # ORIGINAL PROGRESS UPDATE PATTERN
                progress_msg = f"Processing batch {batch_idx + 1} of {total_batches}"
                progress_percentage = (batch_idx / total_batches) * 100
                progress_tracker.update(progress_percentage, progress_msg)
                
                # ORIGINAL THREADING FOR BATCH PROCESSING
                batch_complete = threading.Event()
                batch_result = None
                batch_error = None
                
                def process_batch():
                    nonlocal batch_result, batch_error
                    try:
                        # Create event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Run the async batch processor
                        batch_result = loop.run_until_complete(
                            batch_processor_func(
                                teams_data=batch_teams,
                                batch_index=batch_idx,
                                cache_key=cache_key,
                                **kwargs
                            )
                        )
                    except Exception as e:
                        batch_error = e
                    finally:
                        batch_complete.set()
                        if 'loop' in locals():
                            loop.close()
                
                # Start batch processing in thread
                batch_thread = threading.Thread(target=process_batch)
                batch_thread.start()
                
                # ORIGINAL PROGRESS UPDATES DURING PROCESSING
                start_time = time.time()
                while not batch_complete.is_set():
                    await asyncio.sleep(1)  # Update every second
                    elapsed = time.time() - start_time
                    
                    # Update with sub-progress indication
                    sub_progress = min(10, elapsed * 2)  # Show incremental progress
                    progress_tracker.update(
                        progress_percentage + (sub_progress / total_batches),
                        f"{progress_msg} - {elapsed:.1f}s elapsed"
                    )
                    
                    # Timeout protection (original had 60s timeout per batch)
                    if elapsed > 60:
                        logger.warning(f"Batch {batch_idx + 1} timeout after 60 seconds")
                        break
                
                batch_thread.join(timeout=5)  # Give thread 5 seconds to cleanup
                
                if batch_error:
                    raise batch_error
                
                if batch_result and batch_result.get("status") == "success":
                    batch_picklist = batch_result.get("picklist", [])
                    combined_results.extend(batch_picklist)
                    successful_batches += 1
                    
                    # Update batch progress in cache
                    self.update_batch_progress(cache_key, batch_idx, batch_result)
                    
                    logger.info(f"Batch {batch_idx + 1}/{total_batches} completed: {len(batch_picklist)} teams")
                else:
                    logger.error(f"Batch {batch_idx + 1} returned invalid result: {batch_result}")
                
            except Exception as e:
                logger.error(f"Batch {batch_idx + 1} failed: {str(e)}")
                progress_tracker.update(
                    (batch_idx / total_batches) * 100,
                    f"Batch {batch_idx + 1} failed: {str(e)}"
                )
        
        # Final results processing
        if successful_batches > 0:
            # Remove duplicates and sort (original logic)
            seen_teams = {}
            for team in combined_results:
                team_number = team.get("team_number")
                if team_number not in seen_teams or team.get("score", 0) > seen_teams[team_number].get("score", 0):
                    seen_teams[team_number] = team
            
            final_picklist = sorted(seen_teams.values(), key=lambda x: x.get("score", 0), reverse=True)
            
            progress_tracker.complete(f"Batch processing completed: {successful_batches}/{total_batches} successful")
            
            # Mark batch processing as complete
            self.complete_batch_processing(cache_key, final_picklist, successful_batches, total_batches)
            
            return {
                "status": "success",
                "picklist": final_picklist,
                "batches_processed": successful_batches,
                "total_batches": total_batches,
                "total_teams": len(final_picklist)
            }
        else:
            progress_tracker.fail("All batches failed")
            
            self.fail_batch_processing(cache_key, "All batches failed")
            
            return {
                "status": "error",
                "error": "All batches failed",
                "batches_processed": 0,
                "total_batches": total_batches
            }

    def initialize_batch_processing(self, cache_key: str, total_batches: int) -> None:
        """Initialize batch processing status tracking"""
        self._batch_cache[cache_key] = {
            "status": "in_progress",
            "batch_processing": {
                "total_batches": total_batches,
                "current_batch": 0,
                "progress_percentage": 0,
                "processing_complete": False,
                "batches_completed": [],
                "start_time": time.time()
            }
        }

    def update_batch_progress(self, cache_key: str, batch_index: int, batch_result: Dict[str, Any]) -> None:
        """Update progress for a completed batch"""
        if cache_key in self._batch_cache:
            batch_info = self._batch_cache[cache_key]["batch_processing"]
            batch_info["current_batch"] = batch_index + 1
            batch_info["progress_percentage"] = ((batch_index + 1) / batch_info["total_batches"]) * 100
            batch_info["batches_completed"].append({
                "batch_index": batch_index,
                "team_count": len(batch_result.get("picklist", [])),
                "status": batch_result.get("status", "unknown")
            })

    def complete_batch_processing(self, cache_key: str, final_picklist: List[Dict[str, Any]], successful_batches: int, total_batches: int) -> None:
        """Mark batch processing as complete"""
        if cache_key in self._batch_cache:
            self._batch_cache[cache_key].update({
                "status": "success",
                "picklist": final_picklist,
                "total_teams": len(final_picklist),
                "processing_time": time.time() - self._batch_cache[cache_key]["batch_processing"]["start_time"]
            })
            self._batch_cache[cache_key]["batch_processing"]["processing_complete"] = True

    def fail_batch_processing(self, cache_key: str, error_message: str) -> None:
        """Mark batch processing as failed"""
        if cache_key in self._batch_cache:
            self._batch_cache[cache_key].update({
                "status": "error",
                "error": error_message,
                "processing_time": time.time() - self._batch_cache[cache_key]["batch_processing"]["start_time"]
            })
            self._batch_cache[cache_key]["batch_processing"]["processing_complete"] = True

    def get_batch_processing_status(self, cache_key: str) -> Dict[str, Any]:
        """Get current batch processing status - ORIGINAL LOGIC"""
        if cache_key in self._batch_cache:
            return self._batch_cache[cache_key]
        
        # Check if it's in the main picklist cache (compatibility)
        from app.services.picklist_generator_service import PicklistGeneratorService
        if hasattr(PicklistGeneratorService, '_picklist_cache') and cache_key in PicklistGeneratorService._picklist_cache:
            cached_data = PicklistGeneratorService._picklist_cache[cache_key]
            
            # If it's a timestamp, it's in progress but no batches have completed yet
            if isinstance(cached_data, float):
                return {
                    "status": "in_progress",
                    "batch_processing": {
                        "total_batches": 0,
                        "current_batch": 0,
                        "progress_percentage": 0,
                        "processing_complete": False,
                    },
                }
            # If it's a dictionary with batch_processing info, return the status
            elif isinstance(cached_data, dict) and "batch_processing" in cached_data:
                return cached_data
            # Otherwise, it's a completed non-batch job
            else:
                return {
                    "status": "success",
                    "batch_processing": {
                        "total_batches": 1,
                        "current_batch": 1,
                        "progress_percentage": 100,
                        "processing_complete": True,
                    },
                }
        
        # Not found in any cache
        return {
            "status": "not_found",
            "batch_processing": {
                "total_batches": 0,
                "current_batch": 0,
                "progress_percentage": 0,
                "processing_complete": False,
            },
        }
```

This comprehensive reconstruction template provides the exact algorithms and patterns from the original system. Each template maintains the proven logic while fitting into the refactored service architecture.