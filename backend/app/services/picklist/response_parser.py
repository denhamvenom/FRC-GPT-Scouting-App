"""
Response parsing logic for GPT picklist generation.

This module handles parsing of various JSON formats returned by GPT,
including ultra-compact format, error recovery, and team data enrichment.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import GPTResponseError
from .models import RankedTeam

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    Handles parsing and error recovery for GPT responses.
    
    Supports multiple JSON formats including ultra-compact format
    for token optimization and provides comprehensive error recovery.
    """
    
    # Regex patterns for different formats
    ULTRA_COMPACT_PATTERN = r'\[\s*(\d+)\s*,\s*([\d\.]+)\s*,\s*"([^"]*)"\s*\]'
    COMPACT_PATTERN = r'"team":\s*(\d+),\s*"score":\s*([\d\.]+),\s*"reason":\s*"([^"]*)"'
    STANDARD_PATTERN = (
        r'"team_number":\s*(\d+),\s*"nickname":\s*"([^"]*)",'
        r'\s*"score":\s*([\d\.]+),\s*"reasoning":\s*"([^"]*)"'
    )
    
    def __init__(self):
        """Initialize response parser."""
        pass
    
    def parse_gpt_response(
        self, 
        response_text: str, 
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None
    ) -> List[RankedTeam]:
        """
        Parse GPT response into ranked teams with comprehensive error handling.
        
        Args:
            response_text: Raw GPT response
            teams_data: Original teams data for lookups
            team_index_map: Optional mapping from index to team number
            
        Returns:
            List of ranked teams
            
        Raises:
            GPTResponseError: If parsing fails completely
        """
        try:
            # Clean and preprocess response
            clean_response = self._clean_response_text(response_text)
            
            # Log for debugging
            logger.debug(f"Cleaned response length: {len(clean_response)}")
            logger.debug(f"First 200 chars: {clean_response[:200]}")
            
            # Try JSON parsing first
            try:
                response_data = json.loads(clean_response)
                return self._parse_json_response(response_data, teams_data, team_index_map)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed: {e}, attempting error recovery")
                return self._parse_with_error_recovery(clean_response, teams_data)
                
        except Exception as e:
            logger.error(f"Complete response parsing failure: {e}")
            logger.error(f"Response text: {response_text}")
            raise GPTResponseError(f"Response parsing failed: {e}", response_text)
    
    def _clean_response_text(self, response_text: str) -> str:
        """
        Clean and normalize response text.
        
        Args:
            response_text: Raw response
            
        Returns:
            Cleaned response text
        """
        if not response_text:
            raise GPTResponseError("Empty response from GPT", "")
        
        clean_response = response_text.strip()
        
        # Remove markdown code block formatting
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        elif clean_response.startswith("```"):
            clean_response = clean_response[3:]
        
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        
        return clean_response.strip()
    
    def _parse_json_response(
        self,
        response_data: Dict[str, Any],
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None
    ) -> List[RankedTeam]:
        """
        Parse valid JSON response data.
        
        Args:
            response_data: Parsed JSON data
            teams_data: Original teams data
            team_index_map: Optional index mapping
            
        Returns:
            List of ranked teams
        """
        # Handle ultra-compact format
        if "p" in response_data:
            return self._parse_ultra_compact_format(
                response_data, teams_data, team_index_map
            )
        
        # Handle standard picklist format
        if "picklist" in response_data:
            return self._parse_standard_format(response_data["picklist"], teams_data)
        
        # Handle direct list format
        if isinstance(response_data, list):
            return self._parse_list_format(response_data, teams_data)
        
        raise GPTResponseError(
            f"Unknown response format. Available keys: {list(response_data.keys())}",
            str(response_data)
        )
    
    def _parse_ultra_compact_format(
        self,
        response_data: Dict[str, Any],
        teams_data: List[Dict[str, Any]],
        team_index_map: Optional[Dict[int, int]] = None
    ) -> List[RankedTeam]:
        """
        Parse ultra-compact format: {"p":[[team,score,"reason"]],"s":"ok"}
        
        Args:
            response_data: Response containing "p" key
            teams_data: Original teams data
            team_index_map: Optional index to team number mapping
            
        Returns:
            List of ranked teams
        """
        if "p" not in response_data:
            raise GPTResponseError("Response missing 'p' field", str(response_data))
        
        ranked_teams = []
        seen_teams = set()
        
        for entry in response_data["p"]:
            if not isinstance(entry, list) or len(entry) < 3:
                logger.warning(f"Invalid entry format: {entry}")
                continue
            
            try:
                # Parse entry components
                team_identifier = int(entry[0])
                score = float(entry[1])
                reasoning = str(entry[2])
                
                # Convert index to team number if mapping provided
                if team_index_map and team_identifier in team_index_map:
                    team_number = team_index_map[team_identifier]
                else:
                    team_number = team_identifier
                
                # Skip duplicates
                if team_number in seen_teams:
                    logger.warning(f"Skipping duplicate team {team_number}")
                    continue
                
                seen_teams.add(team_number)
                
                # Create ranked team
                ranked_team = self._create_ranked_team(
                    team_number, score, reasoning, teams_data
                )
                if ranked_team:
                    ranked_teams.append(ranked_team)
                    
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"Error parsing ultra-compact entry {entry}: {e}")
                continue
        
        logger.info(f"Parsed {len(ranked_teams)} teams from ultra-compact format")
        return ranked_teams
    
    def _parse_standard_format(
        self, 
        picklist_data: List[Dict[str, Any]], 
        teams_data: List[Dict[str, Any]]
    ) -> List[RankedTeam]:
        """
        Parse standard picklist format.
        
        Args:
            picklist_data: List of team dictionaries
            teams_data: Original teams data
            
        Returns:
            List of ranked teams
        """
        ranked_teams = []
        seen_teams = set()
        
        for team_data in picklist_data:
            try:
                team_number = int(team_data.get("team_number", team_data.get("team")))
                score = float(team_data.get("score", 0.0))
                reasoning = str(team_data.get("reasoning", team_data.get("reason", "")))
                
                if team_number in seen_teams:
                    logger.warning(f"Skipping duplicate team {team_number}")
                    continue
                
                seen_teams.add(team_number)
                
                ranked_team = self._create_ranked_team(
                    team_number, score, reasoning, teams_data
                )
                if ranked_team:
                    ranked_teams.append(ranked_team)
                    
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error parsing standard entry {team_data}: {e}")
                continue
        
        return ranked_teams
    
    def _parse_list_format(
        self, 
        response_list: List[Any], 
        teams_data: List[Dict[str, Any]]
    ) -> List[RankedTeam]:
        """
        Parse direct list format (array of teams or arrays).
        
        Args:
            response_list: List of team data
            teams_data: Original teams data
            
        Returns:
            List of ranked teams
        """
        ranked_teams = []
        seen_teams = set()
        
        for item in response_list:
            try:
                if isinstance(item, list) and len(item) >= 3:
                    # Array format [team, score, reason]
                    team_number = int(item[0])
                    score = float(item[1])
                    reasoning = str(item[2])
                elif isinstance(item, dict):
                    # Dictionary format
                    team_number = int(item.get("team_number", item.get("team")))
                    score = float(item.get("score", 0.0))
                    reasoning = str(item.get("reasoning", item.get("reason", "")))
                else:
                    logger.warning(f"Unknown list item format: {item}")
                    continue
                
                if team_number in seen_teams:
                    continue
                
                seen_teams.add(team_number)
                
                ranked_team = self._create_ranked_team(
                    team_number, score, reasoning, teams_data
                )
                if ranked_team:
                    ranked_teams.append(ranked_team)
                    
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error parsing list entry {item}: {e}")
                continue
        
        return ranked_teams
    
    def _parse_with_error_recovery(
        self, 
        response_text: str, 
        teams_data: List[Dict[str, Any]]
    ) -> List[RankedTeam]:
        """
        Attempt to recover teams from malformed JSON using regex.
        
        Args:
            response_text: Raw response text
            teams_data: Original teams data
            
        Returns:
            List of ranked teams
            
        Raises:
            GPTResponseError: If all recovery attempts fail
        """
        logger.info("Attempting error recovery with regex patterns")
        
        # Try simple JSON repair first
        try:
            repaired = self._repair_json(response_text)
            response_data = json.loads(repaired)
            return self._parse_json_response(response_data, teams_data)
        except json.JSONDecodeError:
            logger.debug("JSON repair failed, proceeding with regex extraction")
        
        # Try regex extraction for different formats
        recovery_methods = [
            (self.ULTRA_COMPACT_PATTERN, self._extract_ultra_compact_teams),
            (self.COMPACT_PATTERN, self._extract_compact_teams),
            (self.STANDARD_PATTERN, self._extract_standard_teams),
        ]
        
        for pattern, extractor in recovery_methods:
            try:
                teams = extractor(response_text, teams_data, pattern)
                if teams:
                    logger.info(f"Recovered {len(teams)} teams using regex pattern")
                    return teams
            except Exception as e:
                logger.debug(f"Regex recovery failed with pattern {pattern}: {e}")
        
        raise GPTResponseError(
            "All parsing and recovery attempts failed", response_text
        )
    
    def _repair_json(self, response_text: str) -> str:
        """
        Attempt simple JSON repairs.
        
        Args:
            response_text: Malformed JSON text
            
        Returns:
            Potentially repaired JSON text
        """
        # Fix unescaped quotes
        repaired = re.sub(r'(?<!\\)"(?=(,|\]|\}|:))', r'\\"', response_text)
        
        # Fix trailing commas
        repaired = re.sub(r',(\s*[\]}])', r'\1', repaired)
        
        # Fix missing quotes around keys
        repaired = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired)
        
        return repaired
    
    def _extract_ultra_compact_teams(
        self, 
        response_text: str, 
        teams_data: List[Dict[str, Any]], 
        pattern: str
    ) -> List[RankedTeam]:
        """Extract teams using ultra-compact regex pattern."""
        matches = re.findall(pattern, response_text)
        ranked_teams = []
        seen_teams = set()
        
        for match in matches:
            try:
                team_number = int(match[0])
                score = float(match[1])
                reasoning = match[2]
                
                if team_number in seen_teams:
                    continue
                
                seen_teams.add(team_number)
                
                ranked_team = self._create_ranked_team(
                    team_number, score, reasoning, teams_data
                )
                if ranked_team:
                    ranked_teams.append(ranked_team)
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"Error parsing regex match {match}: {e}")
                continue
        
        return ranked_teams
    
    def _extract_compact_teams(
        self, 
        response_text: str, 
        teams_data: List[Dict[str, Any]], 
        pattern: str
    ) -> List[RankedTeam]:
        """Extract teams using compact regex pattern."""
        matches = re.findall(pattern, response_text)
        ranked_teams = []
        seen_teams = set()
        
        for match in matches:
            try:
                team_number = int(match[0])
                score = float(match[1])
                reasoning = match[2]
                
                if team_number in seen_teams:
                    continue
                
                seen_teams.add(team_number)
                
                ranked_team = self._create_ranked_team(
                    team_number, score, reasoning, teams_data
                )
                if ranked_team:
                    ranked_teams.append(ranked_team)
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"Error parsing regex match {match}: {e}")
                continue
        
        return ranked_teams
    
    def _extract_standard_teams(
        self, 
        response_text: str, 
        teams_data: List[Dict[str, Any]], 
        pattern: str
    ) -> List[RankedTeam]:
        """Extract teams using standard regex pattern."""
        matches = re.findall(pattern, response_text)
        ranked_teams = []
        seen_teams = set()
        
        for match in matches:
            try:
                team_number = int(match[0])
                # match[1] is nickname (ignored, we'll get from teams_data)
                score = float(match[2])
                reasoning = match[3]
                
                if team_number in seen_teams:
                    continue
                
                seen_teams.add(team_number)
                
                ranked_team = self._create_ranked_team(
                    team_number, score, reasoning, teams_data
                )
                if ranked_team:
                    ranked_teams.append(ranked_team)
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"Error parsing regex match {match}: {e}")
                continue
        
        return ranked_teams
    
    def _create_ranked_team(
        self,
        team_number: int,
        score: float,
        reasoning: str,
        teams_data: List[Dict[str, Any]]
    ) -> Optional[RankedTeam]:
        """
        Create a RankedTeam object with enriched data.
        
        Args:
            team_number: Team number
            score: Team score
            reasoning: Reasoning text
            teams_data: Original teams data for enrichment
            
        Returns:
            RankedTeam object or None if team not found
        """
        # Find team data for enrichment
        team_data = next(
            (t for t in teams_data if t.get("team_number") == team_number), None
        )
        
        if not team_data:
            logger.warning(f"Team {team_number} not found in teams_data")
            return None
        
        return RankedTeam(
            team_number=team_number,
            nickname=team_data.get("nickname", f"Team {team_number}"),
            score=score,
            reasoning=reasoning,
            metrics=team_data.get("metrics", {}),
        )
    
    def resolve_duplicate_teams(
        self, ranked_teams: List[RankedTeam]
    ) -> List[RankedTeam]:
        """
        Resolve duplicate teams by keeping the one with higher score.
        
        Args:
            ranked_teams: List of ranked teams that may contain duplicates
            
        Returns:
            List with duplicates resolved
        """
        team_map = {}
        
        for team in ranked_teams:
            team_number = team.team_number
            
            if team_number not in team_map:
                team_map[team_number] = team
            else:
                # Keep the team with higher score
                if team.score > team_map[team_number].score:
                    logger.info(
                        f"Replacing duplicate team {team_number}: "
                        f"old score {team_map[team_number].score}, "
                        f"new score {team.score}"
                    )
                    team_map[team_number] = team
                else:
                    logger.info(
                        f"Keeping duplicate team {team_number}: "
                        f"existing score {team_map[team_number].score}, "
                        f"discarding score {team.score}"
                    )
        
        return list(team_map.values())
    
    def detect_response_patterns(self, response_text: str) -> Dict[str, Any]:
        """
        Analyze response text to detect patterns and format.
        
        Args:
            response_text: Raw response text
            
        Returns:
            Dictionary with pattern analysis
        """
        analysis = {
            "format": "unknown",
            "has_json": False,
            "has_arrays": False,
            "has_markdown": False,
            "ultra_compact_matches": 0,
            "compact_matches": 0,
            "standard_matches": 0,
        }
        
        # Check for JSON structure
        try:
            json.loads(self._clean_response_text(response_text))
            analysis["has_json"] = True
        except json.JSONDecodeError:
            pass
        
        # Check for markdown formatting
        if "```" in response_text:
            analysis["has_markdown"] = True
        
        # Count pattern matches
        analysis["ultra_compact_matches"] = len(
            re.findall(self.ULTRA_COMPACT_PATTERN, response_text)
        )
        analysis["compact_matches"] = len(
            re.findall(self.COMPACT_PATTERN, response_text)
        )
        analysis["standard_matches"] = len(
            re.findall(self.STANDARD_PATTERN, response_text)
        )
        
        # Determine likely format
        if analysis["has_json"] and '"p":' in response_text:
            analysis["format"] = "ultra_compact"
        elif analysis["has_json"] and '"picklist":' in response_text:
            analysis["format"] = "standard"
        elif analysis["ultra_compact_matches"] > 0:
            analysis["format"] = "ultra_compact_regex"
        elif analysis["compact_matches"] > 0:
            analysis["format"] = "compact_regex"
        elif analysis["standard_matches"] > 0:
            analysis["format"] = "standard_regex"
        
        return analysis