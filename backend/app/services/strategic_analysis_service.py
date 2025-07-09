# backend/app/services/strategic_analysis_service.py

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config.openai_config import OPENAI_API_KEY, OPENAI_MODEL
from app.types.performance_signature_types import (
    EventPerformanceBaselines,
    EventBaseline,
    MetricStatistics,
    calculate_metric_statistics,
    calculate_percentiles
)

import tiktoken
from openai import AsyncOpenAI

logger = logging.getLogger("strategic_analysis_service")


class StrategicAnalysisService:
    """
    Service for generating strategic intelligence through batched GPT processing.
    
    Processes teams in batches of 20 to generate strategic qualifiers and performance signatures
    using event-wide statistical context only (no hardcoded game context).
    
    Thread Safety: Not thread-safe due to shared state
    Dependencies: OpenAI client, token encoder
    """

    def __init__(self):
        """Initialize the strategic analysis service with OpenAI configuration."""
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Handle tiktoken encoding with fallback for unsupported models
        try:
            self.token_encoder = tiktoken.encoding_for_model(OPENAI_MODEL)
        except KeyError:
            self.token_encoder = tiktoken.get_encoding("cl100k_base")
            logger.info(f"Using fallback encoding 'cl100k_base' for model {OPENAI_MODEL}")
        
        self.max_tokens_limit = 100000
        self.batch_size = 20
        
    def calculate_event_baselines(self, teams_data: List[Dict[str, Any]]) -> EventPerformanceBaselines:
        """
        Calculate statistical baselines across entire event for all metrics.
        
        Args:
            teams_data: List of team data with metrics
            
        Returns:
            EventPerformanceBaselines with statistical context for all metrics
            
        Raises:
            ValueError: When insufficient data for baseline calculation
        """
        if len(teams_data) < 5:
            raise ValueError(f"Insufficient teams for baseline calculation: {len(teams_data)} < 5")
        
        logger.info(f"Calculating event baselines for {len(teams_data)} teams")
        
        # Collect all metric values across teams
        metric_values = {}
        total_matches = 0
        team_count = 0
        
        for team_data in teams_data:
            if not isinstance(team_data, dict) or "metrics" not in team_data:
                continue
                
            team_count += 1
            team_metrics = team_data["metrics"]
            
            # Count matches for this team
            if "match_count" in team_data:
                total_matches += team_data["match_count"]
            
            # Process each metric
            if isinstance(team_metrics, dict):
                for metric_name, metric_value in team_metrics.items():
                    # Skip non-numeric metrics and text fields
                    if (metric_name == "text_fields" or 
                        not isinstance(metric_value, (int, float))):
                        continue
                    
                    if metric_name not in metric_values:
                        metric_values[metric_name] = []
                    metric_values[metric_name].append(float(metric_value))
        
        if not metric_values:
            raise ValueError("No numeric metrics found in team data")
        
        # Calculate baselines for each metric
        baselines = {}
        
        for metric_name, values in metric_values.items():
            if len(values) < 3:  # Need minimum samples
                logger.warning(f"Insufficient data for metric {metric_name}: {len(values)} teams")
                continue
            
            try:
                # Calculate statistics
                stats = calculate_metric_statistics(values)
                percentiles = calculate_percentiles(values)
                
                # Count top performers (90th percentile and above)
                p90_threshold = percentiles.get("90th", float('inf'))
                top_performers = sum(1 for v in values if v >= p90_threshold)
                
                baseline = EventBaseline(
                    metric_name=metric_name,
                    statistics=stats,
                    percentiles=percentiles,
                    field_size=len(values),
                    top_performers=top_performers
                )
                
                baselines[metric_name] = baseline
                
            except Exception as e:
                logger.error(f"Error calculating baseline for {metric_name}: {e}")
                continue
        
        # Determine event level based on team count
        if team_count >= 60:
            event_level = "championship"
        elif team_count >= 40:
            event_level = "district"
        else:
            event_level = "regional"
        
        # Calculate competitive context
        avg_matches = total_matches / team_count if team_count > 0 else 0
        
        competitive_context = {
            "total_teams": team_count,
            "avg_matches_per_team": round(avg_matches, 1),
            "event_level": event_level,
            "metrics_available": len(baselines),
            "data_quality": "good" if len(baselines) >= 10 else "limited"
        }
        
        return EventPerformanceBaselines(
            event_key="current_event",  # Will be set by caller
            year=2025,  # Will be updated by caller
            baselines=baselines,
            total_teams=team_count,
            avg_matches_per_team=avg_matches,
            event_level=event_level,
            competitive_context=competitive_context
        )

    def create_team_batches(self, teams_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Split team data into batches for processing.
        
        Args:
            teams_data: List of team data to batch
            
        Returns:
            List of team data batches
        """
        batches = []
        for i in range(0, len(teams_data), self.batch_size):
            batch = teams_data[i:i + self.batch_size]
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} batches from {len(teams_data)} teams")
        return batches

    def create_index_mapping(self, batch_teams: List[Dict[str, Any]]) -> Dict[int, int]:
        """
        Create index mapping for batch processing.
        
        Args:
            batch_teams: Teams in current batch
            
        Returns:
            Dictionary mapping indices (1-based) to team numbers
        """
        index_map = {}
        for index, team in enumerate(batch_teams, start=1):
            team_number = team.get("team_number", 0)
            index_map[index] = team_number
        
        return index_map

    def create_system_prompt(self, batch_number: int, total_batches: int) -> str:
        """
        Create system prompt for strategic analysis batch processing.
        
        Args:
            batch_number: Current batch number (1-indexed)
            total_batches: Total number of batches
            
        Returns:
            System prompt for GPT strategic analysis
        """
        return f"""You are an expert FRC strategic analyst processing batch {batch_number} of {total_batches}.

TASK: Generate strategic intelligence for teams using ONLY statistical patterns and event baselines.

CRITICAL REQUIREMENTS:
• Use ONLY event statistical context provided - NO hardcoded game knowledge
• Process ALL teams in the batch exactly once using the index mapping
• Generate strategic qualifiers based on performance patterns relative to event field
• Focus on comparative performance within event context only

RESPONSE FORMAT (JSON):
{{
  "batch_info": {{
    "batch_number": {batch_number},
    "teams_processed": [count],
    "missing_teams": [],
    "processing_status": "complete"
  }},
  "team_signatures": [
    {{
      "index": [team_index],
      "team": [team_number],
      "enhanced_metrics": {{
        "metric_name": "value±std (strategic_qualifier, n=samples)"
      }},
      "strategic_profile": "performance_pattern_based_role"
    }}
  ],
  "batch_insights": {{
    "standout_performers": [indices_of_top_teams],
    "developing_teams": [indices_of_improving_teams],
    "specialist_roles": {{
      "category": [indices_with_specialization]
    }}
  }}
}}

STRATEGIC QUALIFIER GUIDELINES:
• Use performance relative to event field: "dominant", "strong", "solid", "developing", "struggling"  
• Add reliability context: "consistent", "volatile", "reliable", "machine_like"
• Include specialization if evident: "specialist", "generalist", "balanced"
• Note trends when clear: "improving", "stable", "declining"

EXAMPLE QUALIFIERS:
• "dominant_consistent_scorer" (90th+ percentile, low variance)
• "strong_reliable_generalist" (75th+ percentile, balanced across metrics)
• "developing_improving_specialist" (showing upward trend in specific area)

NO GAME-SPECIFIC TERMS: Avoid any references to specific game elements, pieces, or mechanisms."""

    def create_batch_payload(
        self, 
        batch_teams: List[Dict[str, Any]], 
        index_map: Dict[int, int],
        event_baselines: EventPerformanceBaselines,
        batch_number: int,
        total_batches: int
    ) -> Dict[str, Any]:
        """
        Create the complete payload for batch processing.
        
        Args:
            batch_teams: Teams in current batch
            index_map: Index to team number mapping
            event_baselines: Event-wide statistical baselines
            batch_number: Current batch number
            total_batches: Total number of batches
            
        Returns:
            Complete batch payload for GPT processing
        """
        # Convert event baselines to serializable format
        baselines_data = {}
        for metric_name, baseline in event_baselines.baselines.items():
            baselines_data[metric_name] = {
                "min": baseline.statistics.min_value,
                "max": baseline.statistics.max_value,
                "mean": round(baseline.statistics.mean, 2),
                "std": round(baseline.statistics.std, 2),
                "percentiles": {k: round(v, 2) for k, v in baseline.percentiles.items()},
                "top_performers": baseline.top_performers,
                "field_size": baseline.field_size
            }

        # Prepare team data for batch
        teams_payload = []
        for index, team in enumerate(batch_teams, start=1):
            team_data = {
                "index": index,
                "team": team.get("team_number", 0),
                "nickname": team.get("nickname", f"Team {team.get('team_number', 0)}"),
                "performance_data": {}
            }
            
            # Add metrics with statistical context
            if "metrics" in team and isinstance(team["metrics"], dict):
                for metric_name, value in team["metrics"].items():
                    if (metric_name != "text_fields" and 
                        isinstance(value, (int, float)) and
                        metric_name in event_baselines.baselines):
                        
                        baseline = event_baselines.baselines[metric_name]
                        percentile = baseline.get_percentile_rank(value)
                        
                        team_data["performance_data"][metric_name] = {
                            "value": round(float(value), 2),
                            "percentile": round(percentile, 1),
                            "field_context": f"field_mean_{round(baseline.statistics.mean, 1)}"
                        }
            
            # Add qualitative data if available
            qualitative = {}
            if "metrics" in team and "text_fields" in team["metrics"]:
                text_fields = team["metrics"]["text_fields"]
                if isinstance(text_fields, dict):
                    for field_name, field_data in text_fields.items():
                        if isinstance(field_data, dict) and "value" in field_data:
                            qualitative[field_name] = field_data["value"]
                        elif isinstance(field_data, str):
                            qualitative[field_name] = field_data
            
            if qualitative:
                team_data["qualitative"] = qualitative
            
            teams_payload.append(team_data)

        return {
            "task": f"Generate strategic signatures for batch {batch_number}/{total_batches}",
            "batch_info": {
                "batch_number": batch_number,
                "total_batches": total_batches,
                "teams_in_batch": len(batch_teams)
            },
            "team_index_map": index_map,
            "event_baselines": baselines_data,
            "competitive_context": event_baselines.competitive_context,
            "teams": teams_payload
        }

    def validate_batch_response(
        self, 
        response: Dict[str, Any], 
        expected_indices: List[int]
    ) -> Tuple[bool, str]:
        """
        Validate that batch response contains all expected teams.
        
        Args:
            response: GPT response data
            expected_indices: List of expected team indices
            
        Returns:
            Tuple of (is_valid, message)
        """
        if "team_signatures" not in response:
            return False, "Missing team_signatures in response"
        
        processed_indices = set()
        for team_sig in response["team_signatures"]:
            if "index" in team_sig:
                processed_indices.add(team_sig["index"])
        
        expected_indices_set = set(expected_indices)
        missing_indices = expected_indices_set - processed_indices
        
        if missing_indices:
            return False, f"Missing teams: {sorted(missing_indices)}"
        
        unexpected_indices = processed_indices - expected_indices_set
        if unexpected_indices:
            logger.warning(f"Unexpected teams in response: {sorted(unexpected_indices)}")
        
        return True, "All expected teams processed"

    async def process_batch(
        self,
        batch_teams: List[Dict[str, Any]],
        event_baselines: EventPerformanceBaselines,
        batch_number: int,
        total_batches: int
    ) -> Dict[str, Any]:
        """
        Process a single batch of teams for strategic analysis.
        
        Args:
            batch_teams: Teams in this batch
            event_baselines: Event statistical baselines
            batch_number: Current batch number (1-indexed)
            total_batches: Total number of batches
            
        Returns:
            Batch processing result with enhanced team signatures
            
        Raises:
            ValueError: When batch processing fails validation
        """
        start_time = time.time()
        
        # Create index mapping
        index_map = self.create_index_mapping(batch_teams)
        expected_indices = list(index_map.keys())
        
        logger.info(f"Processing batch {batch_number}/{total_batches} with {len(batch_teams)} teams")
        
        # Create prompts
        system_prompt = self.create_system_prompt(batch_number, total_batches)
        batch_payload = self.create_batch_payload(
            batch_teams, index_map, event_baselines, batch_number, total_batches
        )
        
        user_prompt = json.dumps(batch_payload)
        
        # Check token limits
        try:
            self._check_token_count(system_prompt, user_prompt)
        except ValueError as e:
            return {
                "status": "error",
                "error": f"Token limit exceeded: {e}",
                "batch_number": batch_number
            }
        
        # Execute GPT call with retry
        try:
            result = await self._execute_api_call_with_retry(system_prompt, user_prompt)
            
            if result["status"] != "success":
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown API error"),
                    "batch_number": batch_number
                }
            
            response_data = result["response_data"]
            
            # Validate response completeness
            is_valid, validation_message = self.validate_batch_response(response_data, expected_indices)
            if not is_valid:
                return {
                    "status": "error",
                    "error": f"Response validation failed: {validation_message}",
                    "batch_number": batch_number
                }
            
            # Convert indices back to team numbers
            enhanced_signatures = {}
            for team_sig in response_data.get("team_signatures", []):
                index = team_sig.get("index")
                if index in index_map:
                    team_number = index_map[index]
                    enhanced_signatures[team_number] = {
                        "team_number": team_number,
                        "enhanced_metrics": team_sig.get("enhanced_metrics", {}),
                        "strategic_profile": team_sig.get("strategic_profile", ""),
                        "batch_number": batch_number
                    }
            
            return {
                "status": "success",
                "signatures": enhanced_signatures,
                "batch_insights": response_data.get("batch_insights", {}),
                "processing_time": time.time() - start_time,
                "batch_number": batch_number,
                "teams_processed": len(enhanced_signatures)
            }
            
        except Exception as e:
            logger.error(f"Exception in batch {batch_number} processing: {e}")
            return {
                "status": "error",
                "error": f"Processing exception: {str(e)}",
                "batch_number": batch_number
            }

    def _check_token_count(self, system_prompt: str, user_prompt: str) -> None:
        """
        Check if prompts exceed token limits.
        
        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            
        Raises:
            ValueError: When token limit is exceeded
        """
        try:
            system_tokens = len(self.token_encoder.encode(system_prompt))
            user_tokens = len(self.token_encoder.encode(user_prompt))
            total_tokens = system_tokens + user_tokens
            
            logger.info(f"Token count: system={system_tokens}, user={user_tokens}, total={total_tokens}")
            
            if total_tokens > self.max_tokens_limit:
                raise ValueError(
                    f"Prompt too large: {total_tokens} tokens exceeds limit of {self.max_tokens_limit}"
                )
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, proceeding without check")

    async def _execute_api_call_with_retry(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute OpenAI API call with exponential backoff retry.
        
        Args:
            system_prompt: System prompt for GPT
            user_prompt: User prompt with data
            max_retries: Maximum retry attempts
            
        Returns:
            API call result with status and data
        """
        initial_delay = 1.0
        retry_count = 0

        while retry_count < max_retries:
            try:
                result = await self._execute_api_call(system_prompt, user_prompt)
                
                if result.get("error_type") == "rate_limit":
                    retry_count += 1
                    if retry_count < max_retries:
                        delay = initial_delay * (2**retry_count)
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {retry_count}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        return {
                            "status": "error",
                            "error": f"Rate limit exceeded after {max_retries} attempts",
                            "error_type": "rate_limit_exhausted"
                        }
                else:
                    return result

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    delay = initial_delay * (2**retry_count)
                    logger.info(f"API call failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    return {
                        "status": "error",
                        "error": f"API call failed after {max_retries} attempts: {e}",
                        "error_type": "api_failure"
                    }

        return {
            "status": "error",
            "error": "Unexpected retry loop exit",
            "error_type": "unknown"
        }

    async def _execute_api_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Execute a single OpenAI API call for strategic analysis.
        
        Args:
            system_prompt: System prompt for GPT
            user_prompt: User prompt with team data
            
        Returns:
            API call result
        """
        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Lower temperature for more consistent strategic analysis
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            if finish_reason == "length":
                return {
                    "status": "error",
                    "error": "Response truncated due to length",
                    "error_type": "response_truncated",
                }

            try:
                response_data = json.loads(content)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error": f"Invalid JSON response: {e}",
                    "error_type": "json_parse_error",
                    "raw_content": content,
                }

            return {
                "status": "success",
                "response_data": response_data,
                "processing_time": time.time() - start_time,
                "finish_reason": finish_reason,
            }

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                return {
                    "status": "error",
                    "error": f"Rate limit exceeded: {e}",
                    "error_type": "rate_limit",
                }

            return {
                "status": "error",
                "error": f"API call failed: {e}",
                "error_type": "api_error",
            }

    async def generate_strategic_intelligence(
        self, 
        teams_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate strategic intelligence for all teams using batched processing.
        
        Args:
            teams_data: List of team data with metrics
            
        Returns:
            Complete strategic intelligence with enhanced signatures
            
        Raises:
            ValueError: When insufficient data or processing fails
        """
        if len(teams_data) < 5:
            raise ValueError(f"Insufficient teams for strategic analysis: {len(teams_data)} < 5")
        
        start_time = time.time()
        logger.info(f"Starting strategic intelligence generation for {len(teams_data)} teams")
        
        # Calculate event baselines
        try:
            event_baselines = self.calculate_event_baselines(teams_data)
            logger.info(f"Calculated baselines for {len(event_baselines.baselines)} metrics")
        except Exception as e:
            raise ValueError(f"Failed to calculate event baselines: {e}")
        
        # Create batches
        batches = self.create_team_batches(teams_data)
        total_batches = len(batches)
        
        logger.info(f"Processing {total_batches} batches of teams")
        
        # Process all batches
        all_signatures = {}
        batch_insights = []
        successful_batches = 0
        
        for batch_number, batch_teams in enumerate(batches, start=1):
            try:
                batch_result = await self.process_batch(
                    batch_teams, event_baselines, batch_number, total_batches
                )
                
                if batch_result["status"] == "success":
                    all_signatures.update(batch_result["signatures"])
                    batch_insights.append(batch_result["batch_insights"])
                    successful_batches += 1
                    
                    logger.info(f"Batch {batch_number} completed: {batch_result['teams_processed']} teams processed")
                else:
                    logger.error(f"Batch {batch_number} failed: {batch_result.get('error', 'Unknown error')}")
                
                # Small delay between batches
                if batch_number < total_batches:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Exception processing batch {batch_number}: {e}")
                continue
        
        if successful_batches == 0:
            raise ValueError("All batches failed during strategic analysis")
        
        # Compile final results
        total_time = time.time() - start_time
        
        strategic_intelligence = {
            "status": "success",
            "strategic_signatures": all_signatures,
            "event_baselines": {
                "total_teams": event_baselines.total_teams,
                "metrics_available": len(event_baselines.baselines),
                "event_level": event_baselines.event_level,
                "competitive_context": event_baselines.competitive_context
            },
            "processing_summary": {
                "total_teams": len(teams_data),
                "teams_processed": len(all_signatures),
                "successful_batches": successful_batches,
                "total_batches": total_batches,
                "processing_time": round(total_time, 2)
            },
            "batch_insights": batch_insights,
            "generation_timestamp": time.time()
        }
        
        logger.info(
            f"Strategic intelligence completed: {len(all_signatures)}/{len(teams_data)} teams processed "
            f"in {successful_batches}/{total_batches} successful batches ({total_time:.1f}s)"
        )
        
        return strategic_intelligence