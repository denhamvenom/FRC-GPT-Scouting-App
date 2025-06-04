# backend/app/services/picklist_generator_service.py

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Set

import tiktoken
from app.services.progress_tracker import ProgressTracker
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "picklist_generator.log", encoding="utf-8"
        ),  # Explicitly use UTF-8 encoding
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("picklist_generator")

# Load environment variables
load_dotenv()

# Allow model selection via environment with a sensible default
GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class PicklistGeneratorService:
    """
    Service for generating ranked picklists using GPT, based on team performance
    metrics and alliance strategy priorities.
    """

    # Class-level cache to share across instances
    _picklist_cache = {}

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

        # Initialize token encoder for the model being used
        self.token_encoder = tiktoken.encoding_for_model("gpt-4-turbo")

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

    def _parse_response_with_index_mapping(
        self,
        response_data: Dict[str, Any],
        teams_data: List[Dict[str, Any]],
        team_index_map: Dict[int, int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse the GPT response and convert indices to team numbers if index mapping is used.

        Args:
            response_data: The parsed JSON response from GPT
            teams_data: The list of team data for lookups
            team_index_map: Optional mapping from indices to team numbers

        Returns:
            List of teams with scores and reasons
        """
        picklist = []
        seen_teams = set()

        # Handle ultra-compact format {"p":[[team,score,"reason"]...],"s":"ok"}
        if "p" in response_data and isinstance(response_data["p"], list):
            for team_entry in response_data["p"]:
                if (
                    len(team_entry) >= 3
                ):  # Ensure we have at least [team/index, score, reason]
                    first_value = int(team_entry[0])

                    # If we have an index map, convert index to team number
                    if team_index_map and first_value in team_index_map:
                        team_number = team_index_map[first_value]
                        logger.debug(
                            f"Mapped index {first_value} to team {team_number}"
                        )
                    else:
                        team_number = first_value

                    # Skip if we've seen this team already
                    if team_number in seen_teams:
                        logger.info(
                            f"Skipping duplicate team {team_number} in response"
                        )
                        continue

                    seen_teams.add(team_number)
                    score = float(team_entry[1])
                    reason = team_entry[2]

                    # Get team nickname from dataset if available
                    team_data = next(
                        (t for t in teams_data if t["team_number"] == team_number), None
                    )
                    nickname = (
                        team_data.get("nickname", f"Team {team_number}")
                        if team_data
                        else f"Team {team_number}"
                    )

                    picklist.append(
                        {
                            "team_number": team_number,
                            "nickname": nickname,
                            "score": score,
                            "reasoning": reason,
                        }
                    )

        return picklist

    def _prepare_team_data_for_gpt(self) -> List[Dict[str, Any]]:
        """
        Prepare a condensed version of team data suitable for the GPT context window.
        Includes key metrics and statistics in a structured format.

        Based on chunk size guidance, we need to minimize the size of the team data
        to reduce input token count and avoid context limits.

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

            # Create condensed team info with only essential fields
            team_info = {
                "team_number": team_number_int,
                "nickname": team_data.get("nickname", f"Team {team_number}"),
                "metrics": {},
                # Only include match count if we have scouting data
                "match_count": (
                    len(team_data.get("scouting_data", []))
                    if team_data.get("scouting_data")
                    else 0
                ),
            }

            # Calculate average metrics from scouting data
            scouting_metrics = {}
            for match in team_data.get("scouting_data", []):
                for key, value in match.items():
                    if isinstance(value, (int, float)) and key not in [
                        "team_number",
                        "match_number",
                        "qual_number",
                    ]:
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

            # Add qualitative notes from superscouting - but only the most recent one to save tokens
            superscouting_notes = []
            for entry in team_data.get("superscouting_data", [])[
                :1
            ]:  # Only use the most recent entry
                if "strategy_notes" in entry and entry["strategy_notes"]:
                    superscouting_notes.append(entry["strategy_notes"])
                if "comments" in entry and entry["comments"]:
                    superscouting_notes.append(entry["comments"])

            if superscouting_notes:
                team_info["superscouting_notes"] = superscouting_notes[
                    :1
                ]  # Limit to 1 note for context size

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

    def _calculate_weighted_score(
        self, team_data: Dict[str, Any], priorities: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate a weighted score for a team based on the given priorities.

        Args:
            team_data: Dictionary containing team metrics
            priorities: List of priority metrics with weights

        Returns:
            Weighted score for the team
        """
        total_score = 0.0
        total_weight = 0.0

        # Get the team's metrics
        team_metrics = team_data.get("metrics", {})

        for priority in priorities:
            metric_id = priority["id"]
            weight = priority.get("weight", 1.0)

            # Check if the metric exists in the team's data
            if metric_id in team_metrics:
                metric_value = team_metrics[metric_id]
                if isinstance(metric_value, (int, float)):
                    # Normalize the metric value (simple approach: assume higher is better)
                    # You might want to add metric-specific normalization logic here
                    normalized_value = metric_value

                    # Add to weighted sum
                    total_score += normalized_value * weight
                    total_weight += weight

        # Calculate final weighted score
        if total_weight > 0:
            return total_score / total_weight
        else:
            return 0.0

    def _check_token_count(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 100000
    ) -> None:
        """
        Check if the combined prompts exceed the token limit.

        Args:
            system_prompt: The system prompt
            user_prompt: The user prompt
            max_tokens: Maximum allowed tokens (default: 100k for safety with 128k model)

        Raises:
            ValueError: If token count exceeds the limit
        """
        try:
            system_tokens = len(self.token_encoder.encode(system_prompt))
            user_tokens = len(self.token_encoder.encode(user_prompt))
            total_tokens = system_tokens + user_tokens

            logger.info(
                f"Token count: system={system_tokens}, user={user_tokens}, total={total_tokens}"
            )

            if total_tokens > max_tokens:
                raise ValueError(
                    f"Prompt too large: {total_tokens} tokens exceeds limit of {max_tokens}. Consider batching teams or trimming fields."
                )
        except Exception as e:
            logger.warning(f"Token counting failed: {str(e)}, proceeding without check")

    def _calculate_similarity_score(
        self, team1_metrics: Dict[str, float], team2_metrics: Dict[str, float]
    ) -> float:
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
        common_metrics = set(team1_metrics.keys()).intersection(
            set(team2_metrics.keys())
        )

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
        exclude_teams: Optional[List[int]] = None,
        request_id: Optional[int] = None,
        cache_key: Optional[str] = None,
        batch_size: int = 20,
        reference_teams_count: int = 3,
        reference_selection: str = "top_middle_bottom",
        use_batching: bool = False,
        final_rerank: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a complete picklist with team rankings.
        Can use either a one-shot approach or batch processing for more consistent results.

        Args:
            your_team_number: Your team's number for alliance compatibility
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric IDs and weights to prioritize
            exclude_teams: Optional list of team numbers to exclude (e.g., already picked)
            request_id: Optional ID for request tracking in logs
            cache_key: Optional cache key for result caching
            batch_size: Number of teams in each batch when using batching (default: 20)
            reference_teams_count: Number of reference teams to include when batching (default: 3)
            reference_selection: Strategy for selecting reference teams
                                ("even_distribution", "percentile", or "top_middle_bottom")
            use_batching: Whether to use batch processing instead of one-shot generation
            final_rerank: After batching, send the combined list back to GPT for
                a final global ranking

        Returns:
            Dict with generated picklist and explanations
        """
        # Debug logging to verify what we're receiving
        logger.info(
            f"Service Layer - Received use_batching={use_batching} (type: {type(use_batching)})"
        )
        logger.info(
            f"Service Layer - batch_size={batch_size}, reference_teams_count={reference_teams_count}"
        )

        # Check cache first - use provided cache_key if available, otherwise generate one
        if cache_key is None:
            # Default cache key generation (fallback for backward compatibility)
            cache_key = f"{your_team_number}_{pick_position}_{json.dumps(priorities)}_{json.dumps(exclude_teams or [])}"

        # Add request_id to log messages if provided
        request_info = f" [Request: {request_id}]" if request_id is not None else ""

        # Add a timestamp to check for active in-progress generations
        current_time = time.time()

        if cache_key in PicklistGeneratorService._picklist_cache:
            cached_result = PicklistGeneratorService._picklist_cache[cache_key]

            # Check if this is an in-progress generation (indicated by a timestamp value)
            if isinstance(cached_result, float):
                # If the generation started less than 2 minutes ago, wait for it to complete
                if current_time - cached_result < 120:  # 2 minute timeout
                    logger.info(
                        f"Detected in-progress picklist generation for same parameters{request_info}, waiting for completion..."
                    )

                    # Wait for a short time to allow the other process to finish
                    for _ in range(12):  # Try for up to 1 minute
                        await asyncio.sleep(5)  # Wait 5 seconds between checks

                        # Check if the result is now available
                        if (
                            cache_key in PicklistGeneratorService._picklist_cache
                            and not isinstance(
                                PicklistGeneratorService._picklist_cache[cache_key],
                                float,
                            )
                        ):
                            logger.info(
                                f"Successfully retrieved result from parallel generation{request_info}"
                            )
                            return PicklistGeneratorService._picklist_cache[cache_key]

                    # If we get here, the other process took too long or failed
                    logger.warning(
                        f"Timeout waiting for parallel generation, proceeding with new generation{request_info}"
                    )
                    # Fall through to generate a new result
                else:
                    # The previous generation is stale, remove it and continue
                    logger.warning(
                        f"Found stale in-progress picklist generation, starting fresh{request_info}"
                    )
                    del PicklistGeneratorService._picklist_cache[cache_key]
            else:
                # We have a valid cached result
                logger.info(f"Using cached picklist{request_info}")
                return cached_result

        # Mark this cache key as "in progress" by storing the current timestamp
        PicklistGeneratorService._picklist_cache[cache_key] = current_time

        # Create a progress tracker immediately
        progress_tracker = ProgressTracker.create_tracker(cache_key)
        progress_tracker.update(
            progress=5,
            message="Starting picklist generation...",
            current_step="initialization",
            status="active",
        )

        # Get your team data
        your_team = self._get_team_by_number(your_team_number)
        if not your_team:
            return {
                "status": "error",
                "message": f"Your team {your_team_number} not found in dataset",
            }

        # Prepare team data for GPT
        teams_data = self._prepare_team_data_for_gpt()

        # Filter out excluded teams
        if exclude_teams:
            teams_data = [
                team for team in teams_data if team["team_number"] not in exclude_teams
            ]

        try:
            # Start comprehensive logging
            logger.info(f"====== STARTING PICKLIST GENERATION ======")
            logger.info(f"Pick position: {pick_position}")
            logger.info(f"Your team: {your_team_number}")
            logger.info(f"Priority metrics count: {len(priorities)}")
            logger.info(f"Total teams to rank: {len(teams_data)}")
            if exclude_teams:
                logger.info(f"Excluded teams: {exclude_teams}")

            # Log the processing mode selected
            if use_batching:
                logger.info(
                    f"Using BATCH PROCESSING with batch_size={batch_size}, reference_teams_count={reference_teams_count}"
                )
                logger.info(f"Reference team selection strategy: {reference_selection}")
            else:
                logger.info("Using ONE-SHOT PROCESSING (processing all teams at once)")

            start_time = time.time()

            # Validate reference selection strategy if batching is enabled
            if use_batching:
                valid_strategies = [
                    "even_distribution",
                    "percentile",
                    "top_middle_bottom",
                ]
                if reference_selection not in valid_strategies:
                    logger.warning(
                        f"Invalid reference selection strategy: {reference_selection}. Using 'top_middle_bottom' instead."
                    )
                    reference_selection = "top_middle_bottom"

            # Choose between batch processing and one-shot processing
            logger.info(
                f"DECISION POINT: use_batching={use_batching}, len(teams_data)={len(teams_data)}, batch_size={batch_size}"
            )
            logger.info(
                f"Condition check: use_batching and len(teams_data) > batch_size = {use_batching and len(teams_data) > batch_size}"
            )

            # TEMPORARY: Force one-shot processing for testing
            logger.info(
                "FORCING ONE-SHOT PROCESSING for testing - ignoring use_batching parameter"
            )
            if False:  # Was: if use_batching and len(teams_data) > batch_size:
                # Use batch processing for large team counts
                logger.info(f"Using batch processing for {len(teams_data)} teams")

                # Create batches of teams
                team_batches = []
                for i in range(0, len(teams_data), batch_size):
                    team_batches.append(teams_data[i : i + batch_size])

                logger.info(f"Split teams into {len(team_batches)} batches")

                # Process each batch and collect results
                batch_results = []
                combined_picklist = []
                reference_teams = []
                total_batches = len(team_batches)

                # Update the cache with batch processing info
                if cache_key:
                    PicklistGeneratorService._picklist_cache[cache_key] = {
                        "status": "in_progress",
                        "batch_processing": {
                            "total_batches": total_batches,
                            "current_batch": 0,
                            "progress_percentage": 0,
                            "processing_complete": False,
                        },
                    }

                for batch_index, batch_teams in enumerate(team_batches):
                    logger.info(
                        f"\n----- Processing Batch {batch_index+1}/{len(team_batches)} -----"
                    )
                    logger.info(f"Batch size: {len(batch_teams)} teams")

                    # Process this batch, including reference teams from previous batches
                    batch_result = await self._process_team_batch(
                        teams_data=batch_teams,
                        reference_teams=reference_teams,
                        your_team_number=your_team_number,
                        pick_position=pick_position,
                        priorities=priorities,
                        batch_index=batch_index,
                        request_id=request_id,
                        cache_key=cache_key,
                    )

                    # Update the cache with progress information
                    if cache_key:
                        current_batch = batch_index + 1
                        progress_percentage = int((current_batch / total_batches) * 100)
                        # Only update if there's an in-progress object (not a timestamp)
                        if (
                            cache_key in PicklistGeneratorService._picklist_cache
                            and isinstance(
                                PicklistGeneratorService._picklist_cache[cache_key],
                                dict,
                            )
                        ):
                            PicklistGeneratorService._picklist_cache[cache_key][
                                "batch_processing"
                            ] = {
                                "total_batches": total_batches,
                                "current_batch": current_batch,
                                "progress_percentage": progress_percentage,
                                "processing_complete": False,
                            }

                    # Check for errors in batch processing
                    if batch_result.get("status") == "error":
                        logger.error(
                            f"Error in batch {batch_index}: {batch_result.get('message')}"
                        )
                        return {
                            "status": "error",
                            "message": f"Error in batch {batch_index}: {batch_result.get('message')}",
                        }

                    # Add successful batch to results
                    batch_results.append(batch_result)

                    # Update reference teams for the next batch from this batch's results
                    if (
                        batch_index < len(team_batches) - 1
                    ):  # Don't need reference teams after the last batch
                        # Select reference teams from the current batch results
                        batch_picklist = batch_result.get("picklist", [])
                        reference_teams = self._select_reference_teams(
                            ranked_teams=batch_picklist,
                            reference_teams_count=reference_teams_count,
                            reference_selection=reference_selection,
                        )
                        logger.info(
                            f"Selected {len(reference_teams)} reference teams for next batch"
                        )

                # Combine results from all batches
                logger.info("\n----- Combining Results from All Batches -----")
                picklist = self._combine_batch_results(
                    batch_results, reference_teams_count
                )

                # Optionally re-rank the combined list using GPT for a final global ordering
                if final_rerank:
                    logger.info("Re-ranking combined picklist for final ordering")
                    picklist = await self._rerank_after_batches(
                        picklist,
                        your_team_number,
                        pick_position,
                        priorities,
                    )

                # Log completion for batch processing
                total_time = time.time() - start_time
                logger.info(f"Total batch processing time: {total_time:.2f}s")
                logger.info(
                    f"Average time per team: {(total_time / len(teams_data)):.2f}s"
                )
                logger.info(f"Final picklist length: {len(picklist)}")

                # Create minimal analysis since we removed it from the schema
                analysis = {
                    "draft_reasoning": "Analysis not included to optimize token usage",
                    "evaluation": "Analysis not included to optimize token usage",
                    "final_recommendations": "Analysis not included to optimize token usage",
                }

                # Assemble final result
                result = {
                    "status": "success",
                    "picklist": picklist,
                    "analysis": analysis,
                    "missing_team_numbers": [],  # All teams should be included through batching
                    "performance": {
                        "total_time": total_time,
                        "team_count": len(teams_data),
                        "avg_time_per_team": (
                            total_time / len(teams_data) if teams_data else 0
                        ),
                        "batch_count": len(team_batches),
                        "batch_size": batch_size,
                        "reference_teams_count": reference_teams_count,
                        "reference_selection": reference_selection,
                    },
                    "batched": True,
                    "batch_processing": {
                        "total_batches": len(team_batches),
                        "current_batch": len(
                            team_batches
                        ),  # Indicates processing is complete
                        "progress_percentage": 100,  # 100% complete
                        "processing_complete": True,
                    },
                }

                # Cache the result
                self._picklist_cache[cache_key] = result

                logger.info(f"====== BATCH PROCESSING COMPLETE ======")
                return result

            else:
                # Use one-shot approach for smaller team counts or when batching is disabled
                logger.info(
                    f"TAKING ONE-SHOT PATH: use_batching={use_batching}, teams_count={len(teams_data)}, batch_size={batch_size}"
                )
                logger.info(f"Using one-shot approach for {len(teams_data)} teams")

                # Initialize variables for one-shot approach
                estimated_time = len(teams_data) * 0.9  # ~0.9 seconds per team estimate
                logger.info(f"Estimated completion time: {estimated_time:.1f} seconds")

                # Create prompts optimized for one-shot completion
                system_prompt = self._create_system_prompt(
                    pick_position, len(teams_data)
                )

                # Create team index mapping
                team_index_map = {}
                for index, team in enumerate(teams_data, start=1):
                    team_index_map[index] = team["team_number"]

                # Get sorted list of team numbers for verification
                team_numbers = sorted([team["team_number"] for team in teams_data])
                logger.info(f"Teams to rank: {len(team_numbers)}")
                logger.info(
                    f"Team numbers: {team_numbers[:10]}... (and {len(team_numbers) - 10} more)"
                )

                user_prompt = self._create_user_prompt(
                    your_team_number,
                    pick_position,
                    priorities,
                    teams_data,
                    team_numbers,
                    team_index_map,
                )

                # Check token count before making the API call
                self._check_token_count(system_prompt, user_prompt)

                # Log prompts (truncated for readability but showing structure)
                truncated_system = (
                    system_prompt[:500] + "..."
                    if len(system_prompt) > 500
                    else system_prompt
                )
                logger.info(f"SYSTEM PROMPT (truncated):\n{truncated_system}")

                # Log just the structure of the user prompt, not the full team data which would be too large
                user_prompt_structure = (
                    "\n".join(user_prompt.split("\n")[:10])
                    + "\n...[Team data truncated]..."
                )
                logger.info(f"USER PROMPT (structure):\n{user_prompt_structure}")

                # Initialize messages
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                # Store parsing context
                parsing_context = {
                    "team_index_map": team_index_map,
                    "teams_data": teams_data,
                }

                # Make a single API call to rank all teams at once
                logger.info(
                    f"--- Requesting complete picklist for {len(team_numbers)} teams ---"
                )
                request_start_time = time.time()

                # Update progress now that we're about to call the API
                progress_tracker.update(
                    progress=10,
                    message=f"Preparing to analyze {len(team_numbers)} teams",
                    current_step="preparation",
                    status="active",
                )

                # Call GPT with optimized settings for one-shot generation
                logger.info("Starting API call...")
                progress_tracker.update(
                    progress=20,
                    message=f"Sending {len(team_numbers)} teams to GPT for analysis",
                    current_step="api_call",
                    status="active",
                )

            # Use exponential backoff for rate limit handling
            max_retries = 3
            initial_delay = 1.0  # Start with a 1-second delay
            response = None
            api_error = None
            api_complete = threading.Event()

            # Create a thread for the API call
            def make_api_call():
                nonlocal response, api_error
                retry_count = 0
                while retry_count <= max_retries:
                    try:
                        response = client.chat.completions.create(
                            model=GPT_MODEL,
                            messages=messages,
                            temperature=0.2,  # Lower temperature for more consistent results
                            max_tokens=4000,  # Prevent truncation by limiting output length
                            response_format={"type": "json_object"},
                        )
                        # Success - break out of the retry loop
                        api_complete.set()
                        return
                    except Exception as e:
                        # Check if it's a rate limit error (typically a 429 status code)
                        is_rate_limit = "429" in str(e)

                        if is_rate_limit and retry_count < max_retries:
                            # Calculate exponential backoff delay
                            retry_count += 1
                            delay = initial_delay * (
                                2**retry_count
                            )  # Exponential backoff

                            logger.warning(
                                f"Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {retry_count}/{max_retries})"
                            )
                            time.sleep(delay)
                        else:
                            # Either not a rate limit error or we've exceeded max retries
                            logger.error(f"API call failed: {str(e)}")
                            api_error = e
                            api_complete.set()
                            return

            # Start the API call in a separate thread
            api_thread = threading.Thread(target=make_api_call)
            api_thread.start()

            # Update progress periodically while waiting for the API response
            start_wait_time = time.time()
            progress_increment = 30  # Start at 20%, go to 50%

            while not api_complete.is_set():
                elapsed = time.time() - start_wait_time
                # Estimate progress based on typical response time (50 seconds)
                estimated_progress = min(50, 20 + (elapsed / 50) * progress_increment)

                progress_tracker.update(
                    progress=estimated_progress,
                    message=f"Analyzing {len(team_numbers)} teams with GPT... ({elapsed:.0f}s)",
                    current_step="api_call",
                    status="active",
                )

                # Wait a bit before checking again
                await asyncio.sleep(1.0)

            # Wait for the thread to complete
            api_thread.join()

            # Check if there was an error
            if api_error:
                raise api_error

            # Log timing and response metadata
            request_time = time.time() - request_start_time
            logger.info(
                f"Total response time: {request_time:.2f}s (avg: {request_time/len(team_numbers):.2f}s per team)"
            )
            logger.info(
                f"Response metadata: finish_reason={response.choices[0].finish_reason}, model={response.model}"
            )

            # Check if the response was truncated due to token limits
            if response.choices[0].finish_reason == "length":
                logger.error("Response was truncated due to token length limit")
                progress_tracker.complete(
                    success=False,
                    message="AI response truncated due to length limits. Try batch processing.",
                    final_data={},
                )
                return {
                    "status": "error",
                    "message": "The AI response was cut off due to length limits. Please try with fewer teams or use batch processing.",
                }

            # Update progress after API response
            progress_tracker.update(
                progress=60,
                message="GPT analysis complete. Processing results...",
                current_step="response_processing",
                status="active",
            )

            # Parse the response
            response_content = response.choices[0].message.content

            # Log a sample of the response (first 200 chars)
            response_sample = (
                response_content[:200] + "..."
                if len(response_content) > 200
                else response_content
            )
            logger.info(f"Response sample: {response_sample}")

            # Parse the JSON response
            try:
                # Log the full raw response (limited to 1000 chars) for debugging purposes
                if len(response_content) > 1000:
                    logger.info(
                        f"Raw JSON response (first 1000 chars):\n{response_content[:1000]}"
                    )
                else:
                    logger.info(f"Raw JSON response:\n{response_content}")

                response_data = json.loads(response_content)

                # Check for overflow condition in ultra-compact format
                if response_data.get("s") == "overflow":
                    logger.warning("GPT returned overflow status - token limit reached")
                    return {
                        "status": "error",
                        "message": "The amount of team data exceeded the token limit. Please try with fewer teams or simplified priorities.",
                    }
                # Check for overflow in regular format
                elif response_data.get("status") == "overflow":
                    logger.warning("GPT returned overflow status - token limit reached")
                    return {
                        "status": "error",
                        "message": "The amount of team data exceeded the token limit. Please try with fewer teams or simplified priorities.",
                    }

                # Handle ultra-compact format {"p":[[team,score,"reason"]...],"s":"ok"}
                if "p" in response_data and isinstance(response_data["p"], list):
                    logger.info(
                        f"Response contains {len(response_data['p'])} teams in ultra-compact format"
                    )

                    # Log first few teams for debugging
                    teams_sample = response_data["p"][:3]
                    logger.info(
                        f"First few teams (ultra-compact): {json.dumps(teams_sample)}"
                    )

                    # Check for repeating patterns in teams
                    team_nums = [
                        int(entry[0]) for entry in response_data["p"] if len(entry) >= 1
                    ]

                    # If we're using index mapping, those numbers are indices, not team numbers
                    if parsing_context.get("team_index_map"):
                        logger.info(
                            "Using index mapping - converting for duplicate detection"
                        )
                        actual_team_nums = []
                        team_index_map = parsing_context["team_index_map"]
                        for idx in team_nums:
                            if idx in team_index_map:
                                actual_team_nums.append(team_index_map[idx])
                            else:
                                actual_team_nums.append(
                                    idx
                                )  # fallback if index not found
                        team_nums = actual_team_nums

                    team_counts = {}
                    for team_num in team_nums:
                        team_counts[team_num] = team_counts.get(team_num, 0) + 1

                    # Check if we have duplicates
                    duplicates = {
                        team: count for team, count in team_counts.items() if count > 1
                    }
                    if duplicates:
                        logger.warning(f"Response contains duplicates: {duplicates}")
                        logger.warning(f"First 20 team numbers: {team_nums[:20]}")

                        # Check if we have a repeating pattern
                        if len(team_nums) > 16:
                            # Check for common sequence lengths
                            for pattern_length in [4, 8, 12, 16]:
                                if len(team_nums) >= pattern_length * 2:
                                    pattern1 = team_nums[:pattern_length]
                                    pattern2 = team_nums[
                                        pattern_length : pattern_length * 2
                                    ]
                                    if pattern1 == pattern2:
                                        logger.warning(
                                            f"Detected repeating pattern of length {pattern_length}"
                                        )
                                        logger.warning(
                                            f"Model is repeating teams instead of ranking all teams"
                                        )
                                        # Truncate to first pattern only to avoid duplicates
                                        logger.warning(
                                            f"Truncating response to first {pattern_length} teams"
                                        )
                                        response_data["p"] = response_data["p"][
                                            :pattern_length
                                        ]
                                        break

                    # Calculate duplication percentage
                    total_entries = len(team_nums)
                    unique_teams = len(team_counts)
                    if total_entries > 0:  # Prevent division by zero
                        duplication_percentage = (
                            (total_entries - unique_teams) / total_entries
                        ) * 100
                        logger.warning(
                            f"Duplication percentage: {duplication_percentage:.1f}%"
                        )

                        # If duplication is extreme (over 80%), warn that model might be in a loop
                        if duplication_percentage > 80 and total_entries > 30:
                            logger.error(
                                f"MODEL APPEARS TO BE LOOPING - {duplication_percentage:.1f}% duplicates"
                            )
                            return {
                                "status": "error",
                                "message": "The model is unable to rank all teams at once. Please try reducing the number of teams to rank (e.g., 25 at a time) or simplify the priorities. The model got stuck repeating the same teams.",
                            }

                    # Use the new helper method to parse with index mapping
                    picklist = self._parse_response_with_index_mapping(
                        response_data,
                        parsing_context.get("teams_data", teams_data),
                        parsing_context.get("team_index_map"),
                    )

                # Handle regular compact format
                elif "picklist" in response_data and isinstance(
                    response_data["picklist"], list
                ):
                    logger.info(
                        f"Response contains {len(response_data['picklist'])} teams in regular format"
                    )

                    # Log first few teams for debugging
                    teams_sample = response_data["picklist"][:3]
                    logger.info(f"First few teams: {json.dumps(teams_sample)}")

                    # Extract the picklist and convert from compact to full format if needed
                    raw_picklist = response_data.get("picklist", [])

                    # Convert compact format {"team":123, "score":45.6, "reason":"text"}
                    # to standard format {"team_number":123, "nickname":"Team 123", "score":45.6, "reasoning":"text"}
                    picklist = []
                    for team_entry in raw_picklist:
                        # Check if using new compact format (has "team" instead of "team_number")
                        if "team" in team_entry and "team_number" not in team_entry:
                            team_number = team_entry["team"]
                            # Get team nickname from dataset if available
                            team_data = next(
                                (
                                    t
                                    for t in teams_data
                                    if t["team_number"] == team_number
                                ),
                                None,
                            )
                            nickname = (
                                team_data.get("nickname", f"Team {team_number}")
                                if team_data
                                else f"Team {team_number}"
                            )

                            picklist.append(
                                {
                                    "team_number": team_number,
                                    "nickname": nickname,
                                    "score": team_entry.get("score", 0.0),
                                    "reasoning": team_entry.get(
                                        "reason", "No reasoning provided"
                                    ),
                                }
                            )
                        else:
                            # Already in standard format
                            picklist.append(team_entry)
                else:
                    logger.warning("Response has no valid picklist")
                    picklist = []

                # Create minimal analysis since we removed it from the schema
                analysis = {
                    "draft_reasoning": "Analysis not included to optimize token usage",
                    "evaluation": "Analysis not included to optimize token usage",
                    "final_recommendations": "Analysis not included to optimize token usage",
                }

            except json.JSONDecodeError as e:
                # Log the error and the full response for debugging
                logger.error(f"JSON parse error: {e}")
                logger.error(
                    f"Full response that couldn't be parsed: {response_content}"
                )

                # Try to fix common JSON issues and salvage what we can
                try:
                    # Try to use a more lenient JSON parser
                    import ast
                    import re

                    # Simple fix for unescaped quotes
                    fixed_content = re.sub(
                        r'(?<!\\)"(?=(,|\]|\}|:))', r'\\"', response_content
                    )

                    # Try parsing again
                    logger.info("Attempting to repair the JSON response...")
                    response_data = json.loads(fixed_content)

                    # If we get here, the fix worked
                    logger.info("Successfully repaired JSON response!")
                    picklist = response_data.get("picklist", [])
                    analysis = response_data.get(
                        "analysis",
                        {
                            "draft_reasoning": "Analysis not available",
                            "evaluation": "Analysis not available",
                            "final_recommendations": "Analysis not available",
                        },
                    )

                except Exception as repair_error:
                    # If repair fails, construct a fallback response
                    logger.error(f"JSON repair failed: {repair_error}")

                    # Extract any team data we can using regex
                    try:
                        logger.info(
                            "Attempting to extract team data from broken JSON..."
                        )

                        # Try to extract from ultra-compact format first
                        # Format: [teamnum,score,"reason"] in a p array
                        compact_pattern = (
                            r'\[\s*(\d+)\s*,\s*([\d\.]+)\s*,\s*"([^"]*)"\s*\]'
                        )
                        compact_teams_extracted = re.findall(
                            compact_pattern, response_content
                        )

                        if compact_teams_extracted:
                            logger.info(
                                f"Extracted {len(compact_teams_extracted)} team entries from broken ultra-compact JSON"
                            )

                            # Log the first few raw extractions for debugging
                            for i, team_raw in enumerate(compact_teams_extracted[:3]):
                                logger.info(
                                    f"Raw extraction {i+1} (ultra-compact): {team_raw}"
                                )

                            picklist = []
                            team_numbers_seen = (
                                set()
                            )  # Track team numbers to detect duplicates in regex extraction

                            for team_match in compact_teams_extracted:
                                try:
                                    team_number = int(team_match[0])
                                    score = float(team_match[1])
                                    reasoning = team_match[2]

                                    # Skip obvious duplicates during extraction
                                    if team_number in team_numbers_seen:
                                        logger.info(
                                            f"Skipping duplicate team {team_number} during regex extraction"
                                        )
                                        continue

                                    team_numbers_seen.add(team_number)

                                    # Get team nickname from dataset if available
                                    team_data = next(
                                        (
                                            t
                                            for t in teams_data
                                            if t["team_number"] == team_number
                                        ),
                                        None,
                                    )
                                    nickname = (
                                        team_data.get("nickname", f"Team {team_number}")
                                        if team_data
                                        else f"Team {team_number}"
                                    )

                                    picklist.append(
                                        {
                                            "team_number": team_number,
                                            "nickname": nickname,
                                            "score": score,
                                            "reasoning": reasoning,
                                        }
                                    )
                                except Exception as team_error:
                                    logger.error(
                                        f"Error parsing team data: {team_error}"
                                    )
                                    continue

                            analysis = {
                                "draft_reasoning": "Analysis not available - recovered from parsing error",
                                "evaluation": "Analysis not available - recovered from parsing error",
                                "final_recommendations": "Analysis not available - recovered from parsing error",
                            }

                            logger.info(
                                f"Salvaged {len(picklist)} teams from broken response"
                            )
                        else:
                            # If not found, try the regular compact format
                            team_pattern1 = r'"team":\s*(\d+),\s*"score":\s*([\d\.]+),\s*"reason":\s*"([^"]*)"'
                            team_pattern2 = r'"team_number":\s*(\d+),\s*"nickname":\s*"([^"]*)",\s*"score":\s*([\d\.]+),\s*"reasoning":\s*"([^"]*)"'

                            teams_extracted1 = re.findall(
                                team_pattern1, response_content
                            )
                            teams_extracted2 = re.findall(
                                team_pattern2, response_content
                            )

                            if teams_extracted1:
                                logger.info(
                                    f"Extracted {len(teams_extracted1)} team entries from broken compact JSON"
                                )

                                # Log the first few raw extractions for debugging
                                for i, team_raw in enumerate(teams_extracted1[:3]):
                                    logger.info(
                                        f"Raw extraction {i+1} (compact): {team_raw}"
                                    )

                                picklist = []
                                team_numbers_seen = (
                                    set()
                                )  # Track team numbers to detect duplicates

                                for team_match in teams_extracted1:
                                    try:
                                        team_number = int(team_match[0])
                                        score = float(team_match[1])
                                        reasoning = team_match[2]

                                        # Skip obvious duplicates during extraction
                                        if team_number in team_numbers_seen:
                                            logger.info(
                                                f"Skipping duplicate team {team_number} during regex extraction"
                                            )
                                            continue

                                        team_numbers_seen.add(team_number)

                                        # Get team nickname from dataset if available
                                        team_data = next(
                                            (
                                                t
                                                for t in teams_data
                                                if t["team_number"] == team_number
                                            ),
                                            None,
                                        )
                                        nickname = (
                                            team_data.get(
                                                "nickname", f"Team {team_number}"
                                            )
                                            if team_data
                                            else f"Team {team_number}"
                                        )

                                        picklist.append(
                                            {
                                                "team_number": team_number,
                                                "nickname": nickname,
                                                "score": score,
                                                "reasoning": reasoning,
                                            }
                                        )
                                    except Exception as team_error:
                                        logger.error(
                                            f"Error parsing team data: {team_error}"
                                        )
                                        continue

                                analysis = {
                                    "draft_reasoning": "Analysis not available - recovered from parsing error",
                                    "evaluation": "Analysis not available - recovered from parsing error",
                                    "final_recommendations": "Analysis not available - recovered from parsing error",
                                }

                                logger.info(
                                    f"Salvaged {len(picklist)} teams from broken response"
                                )
                            elif teams_extracted2:
                                logger.info(
                                    f"Extracted {len(teams_extracted2)} team entries from broken standard JSON"
                                )

                                # Log the first few raw extractions for debugging
                                for i, team_raw in enumerate(teams_extracted2[:3]):
                                    logger.info(f"Raw extraction {i+1}: {team_raw}")

                                picklist = []
                                team_numbers_seen = (
                                    set()
                                )  # Track team numbers to detect duplicates

                                for team_match in teams_extracted2:
                                    try:
                                        team_number = int(team_match[0])
                                        team_name = team_match[1]
                                        score = float(team_match[2])
                                        reasoning = team_match[3]

                                        # Skip obvious duplicates during extraction
                                        if team_number in team_numbers_seen:
                                            logger.info(
                                                f"Skipping duplicate team {team_number} during regex extraction"
                                            )
                                            continue

                                        team_numbers_seen.add(team_number)

                                        picklist.append(
                                            {
                                                "team_number": team_number,
                                                "nickname": team_name,
                                                "score": score,
                                                "reasoning": reasoning,
                                            }
                                        )
                                    except Exception as team_error:
                                        logger.error(
                                            f"Error parsing team data: {team_error}"
                                        )
                                        continue

                                analysis = {
                                    "draft_reasoning": "Analysis not available - recovered from parsing error",
                                    "evaluation": "Analysis not available - recovered from parsing error",
                                    "final_recommendations": "Analysis not available - recovered from parsing error",
                                }

                                logger.info(
                                    f"Salvaged {len(picklist)} teams from broken response"
                                )
                            else:
                                # If we couldn't extract any teams, re-raise the original error
                                logger.error(
                                    "Could not extract any team data from the broken response"
                                )
                                raise e
                    except Exception as extract_error:
                        logger.error(f"Failed to extract team data: {extract_error}")
                        raise e

            # Process the picklist
            logger.info("=== Processing picklist results ===")
            logger.info(f"Total teams received: {len(picklist)}")

            # Update progress - deduplication phase
            progress_tracker.update(
                progress=80,
                message="Removing duplicate teams and finalizing rankings...",
                current_step="deduplication",
                status="active",
            )

            # Check for duplicate teams and handle them intelligently
            team_entries = {}  # Map team numbers to their entries
            duplicates = []

            for team in picklist:
                team_number = team.get("team_number")
                if not team_number:
                    continue  # Skip teams without a valid team number

                if team_number not in team_entries:
                    # First time seeing this team
                    team_entries[team_number] = team
                else:
                    # Found a duplicate team - keep the one with the higher score
                    duplicates.append(team_number)
                    current_score = team_entries[team_number].get("score", 0)
                    new_score = team.get("score", 0)

                    if new_score > current_score:
                        # This new entry has a higher score, use it instead
                        logger.info(
                            f"Team {team_number} appears twice - keeping entry with higher score ({new_score} vs {current_score})"
                        )
                        team_entries[team_number] = team

            # Create the deduplicated picklist from the team_entries map
            deduplicated_picklist = list(team_entries.values())

            if duplicates:
                logger.info(
                    f"Found {len(duplicates)} duplicate teams: {duplicates[:10]}..."
                )
                logger.info(
                    f"Resolved by keeping the entry with higher score for each team"
                )

                # Analyze the duplicates in more detail
                duplicate_counts = {}
                for team_num in duplicates:
                    if team_num not in duplicate_counts:
                        duplicate_counts[team_num] = 0
                    duplicate_counts[team_num] += 1

                # Find teams with the most duplicates
                sorted_duplicates = sorted(
                    duplicate_counts.items(), key=lambda x: x[1], reverse=True
                )
                if sorted_duplicates:
                    logger.info(f"Most duplicated teams: {sorted_duplicates[:5]}")

                    # Log positions of a highly duplicated team
                    if sorted_duplicates[0][1] > 1:
                        most_duplicated = sorted_duplicates[0][0]
                        positions = [
                            i
                            for i, team in enumerate(picklist)
                            if team.get("team_number") == most_duplicated
                        ]
                        logger.info(
                            f"Team {most_duplicated} appears at positions: {positions}"
                        )

            logger.info(f"After deduplication: {len(deduplicated_picklist)} teams")

            # Check if we're missing teams
            available_team_numbers = {team["team_number"] for team in teams_data}
            ranked_team_numbers = {
                team["team_number"] for team in deduplicated_picklist
            }
            missing_team_numbers = available_team_numbers - ranked_team_numbers

            # Debug: Log the first 5 teams in the picklist before deduplication
            if picklist and len(picklist) > 0:
                logger.info(
                    f"First 5 raw teams from GPT response BEFORE deduplication:"
                )
                for i, team in enumerate(picklist[:5]):
                    logger.info(
                        f"  Raw Team {i+1}: {team.get('team_number')} - {team.get('nickname')}"
                    )

                # Also log team numbers in sequence to check for patterns in the duplicates
                team_numbers_sequence = [t.get("team_number") for t in picklist[:20]]
                logger.info(
                    f"First 20 team numbers in response: {team_numbers_sequence}"
                )

            # Log the completeness
            coverage_percent = (
                (len(ranked_team_numbers) / len(available_team_numbers)) * 100
                if available_team_numbers
                else 0
            )
            logger.info(
                f"GPT coverage: {coverage_percent:.1f}% ({len(ranked_team_numbers)} of {len(available_team_numbers)} teams)"
            )

            # If we're missing teams, add them to the end
            if missing_team_numbers:
                logger.warning(
                    f"Missing {len(missing_team_numbers)} teams from GPT response"
                )
                if (
                    len(missing_team_numbers) <= 10
                ):  # Only log all missing teams if there aren't too many
                    logger.warning(
                        f"Missing team numbers: {sorted(list(missing_team_numbers))}"
                    )
                else:
                    logger.warning(
                        f"First 10 missing team numbers: {sorted(list(missing_team_numbers))[:10]}..."
                    )

                # Get the lowest score from the existing picklist
                min_score = (
                    min([team["score"] for team in deduplicated_picklist])
                    if deduplicated_picklist
                    else 0.0
                )
                backup_score = max(
                    0.1, min_score * 0.5
                )  # Use half of the minimum score or 0.1, whichever is higher
                logger.info(f"Using backup score {backup_score} for missing teams")

                # Add missing teams to the end of the picklist
                for team_number in missing_team_numbers:
                    # Find the team data
                    team_data = next(
                        (t for t in teams_data if t["team_number"] == team_number), None
                    )
                    if team_data:
                        # Add to the end with a lower score
                        deduplicated_picklist.append(
                            {
                                "team_number": team_number,
                                "nickname": team_data.get(
                                    "nickname", f"Team {team_number}"
                                ),
                                "score": backup_score,
                                "reasoning": "Added to complete the picklist - not enough data available for detailed analysis",
                                "is_fallback": True,  # Flag to indicate this team was added as a fallback
                            }
                        )

            # Assemble final result
            result = {
                "status": "success",
                "picklist": deduplicated_picklist,
                "analysis": analysis,
                "missing_team_numbers": (
                    list(missing_team_numbers) if missing_team_numbers else []
                ),
                "performance": {
                    "total_time": request_time,
                    "team_count": len(team_numbers),
                    "avg_time_per_team": (
                        request_time / len(team_numbers) if team_numbers else 0
                    ),
                    "missing_teams": len(missing_team_numbers),
                    "duplicate_teams": len(duplicates),
                },
                "batched": False,
                "batch_processing": {
                    "total_batches": 1,
                    "current_batch": 1,  # Indicates processing is complete
                    "progress_percentage": 100,  # 100% complete
                    "processing_complete": True,
                },
            }

            # Log completion stats
            total_time = time.time() - start_time
            logger.info(f"====== PICKLIST GENERATION COMPLETE ======")
            logger.info(
                f"Total time: {total_time:.2f}s for {len(deduplicated_picklist)} teams"
            )
            logger.info(
                f"Average time per team: {(total_time / len(deduplicated_picklist) if deduplicated_picklist else 0):.2f}s"
            )
            logger.info(f"Final picklist length: {len(deduplicated_picklist)}")

            # Update progress - completion
            progress_tracker.complete(
                f"Successfully generated picklist for {len(deduplicated_picklist)} teams"
            )

            # Cache the result, replacing the "in progress" timestamp
            self._picklist_cache[cache_key] = result

            logger.info(f"Successfully completed picklist generation{request_info}")
            return result

        except Exception as e:
            logger.error(
                f"Error generating picklist with GPT: {str(e)}{request_info}",
                exc_info=True,
            )

            # Update progress tracker with failure
            if "progress_tracker" in locals():
                progress_tracker.fail(f"Picklist generation failed: {str(e)}")

            # Clean up the in-progress flag from cache so future requests can proceed
            if cache_key in self._picklist_cache and isinstance(
                self._picklist_cache[cache_key], float
            ):
                del self._picklist_cache[cache_key]

            return {
                "status": "error",
                "message": f"Failed to generate picklist: {str(e)}",
            }

    def _create_system_prompt(self, pick_position: str, team_count: int) -> str:
        """
        Create the system prompt for GPT based on the pick position.
        Optimized for one-shot generation of the complete picklist.

        Args:
            pick_position: 'first', 'second', or 'third'
            team_count: Total number of teams to rank

        Returns:
            System prompt string
        """
        position_context = {
            "first": "First pick teams should be overall powerhouse teams that excel in multiple areas.",
            "second": "Second pick teams should complement the first pick and address specific needs.",
            "third": "Third pick teams are more specialized, often focusing on a single critical function.",
        }

        context_note = position_context.get(pick_position, "")
        # Adjust the prompt based on whether we're using team index mapping
        index_rule = ""
        team_reference = "team"
        if team_count > 0:  # This is a signal that we're using index mapping
            index_rule = (
                f"• Use indices 1-{team_count} from TEAM_INDEX_MAP exactly once.\n"
            )
            team_reference = "index"

        return f"""You are GPT‑4.1, an FRC alliance strategist.
Return one‑line minified JSON:
{{"p":[[{team_reference},score,"reason"]…],"s":"ok"}}

CRITICAL RULES
• Rank all {team_count} teams/indices, each exactly once.  
{index_rule}• Sort by weighted performance, then synergy with Team {{your_team_number}} for {pick_position} pick.  
• Each reason must be ≤10 words, NO REPETITION, cite 1 metric (e.g. "Strong auto: 3.2 avg").
• NO repetitive words or phrases. Be concise and specific.
• If you cannot complete all teams due to length limits, respond only {{"s":"overflow"}}.

{context_note}

EXAMPLE: {{"p":[[1,8.5,"Strong auto: 2.8 avg"],[2,7.9,"Consistent defense"],[3,6.2,"Reliable endgame"]],"s":"ok"}}"""

    def _create_user_prompt(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]],
        team_numbers: List[int] = None,
        team_index_map: Dict[int, int] = None,
    ) -> str:
        """
        Create the user prompt for GPT with all necessary context.

        Args:
            your_team_number: Your team's number
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric priorities with weights
            teams_data: Prepared team data for context
            team_numbers: List of team numbers to verify inclusion

        Returns:
            User prompt string
        """
        # Find your team's data
        your_team_info = next(
            (team for team in teams_data if team["team_number"] == your_team_number),
            None,
        )

        # Calculate weighted scores for each team before passing to GPT
        teams_with_scores = []

        # If we have an index map, format teams with indices
        if team_index_map:
            # Create reverse map for quick lookup
            team_to_index = {v: k for k, v in team_index_map.items()}

            for team in teams_data:
                weighted_score = self._calculate_weighted_score(team, priorities)
                team_with_score = team.copy()
                team_with_score["weighted_score"] = weighted_score
                # Add index if available
                if team["team_number"] in team_to_index:
                    team_with_score["index"] = team_to_index[team["team_number"]]
                teams_with_scores.append(team_with_score)
        else:
            for team in teams_data:
                weighted_score = self._calculate_weighted_score(team, priorities)
                team_with_score = team.copy()
                team_with_score["weighted_score"] = weighted_score
                teams_with_scores.append(team_with_score)

        # Include team index mapping if provided
        team_index_info = ""
        if team_index_map:
            team_index_info = f"""
TEAM_INDEX_MAP = {json.dumps(team_index_map)}
⚠️ CRITICAL: Use indices 1 through {len(team_index_map)} from TEAM_INDEX_MAP exactly once.
⚠️ Your response MUST use indices, NOT team numbers: [[1,score,"reason"],[2,score,"reason"]...]
⚠️ Each index from 1 to {len(team_index_map)} must appear EXACTLY ONCE.
"""

        prompt = f"""YOUR_TEAM_PROFILE = {json.dumps(your_team_info) if your_team_info else "{}"} 
PRIORITY_METRICS  = {json.dumps(priorities)}   # include weight field
GAME_CONTEXT      = {json.dumps(self.game_context) if self.game_context else "null"}
TEAM_NUMBERS_TO_INCLUDE = {json.dumps(team_numbers)}{team_index_info}
AVAILABLE_TEAMS = {json.dumps(teams_with_scores)}     # include pre‑computed weighted_score

Please produce output following RULES.
"""
        return prompt

    async def rank_missing_teams(
        self,
        missing_team_numbers: List[int],
        ranked_teams: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        batch_size: int = 20,  # Smaller batch size to avoid rate limits and token limits
        request_id: Optional[int] = None,
        cache_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate rankings for teams that were missed in the initial picklist generation.

        Args:
            missing_team_numbers: List of team numbers that need to be ranked
            ranked_teams: List of teams already ranked (provides context)
            your_team_number: Your team's number for alliance compatibility
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric IDs and weights to prioritize

        Returns:
            Dict with rankings for the previously missing teams
        """
        # Check cache first - use provided cache_key if available, otherwise generate one
        if cache_key is None:
            # Default cache key generation (fallback for backward compatibility)
            cache_key = f"missing_{your_team_number}_{pick_position}_{json.dumps(priorities)}_{json.dumps(missing_team_numbers)}"

        # Add request_id to log messages if provided
        request_info = f" [Request: {request_id}]" if request_id is not None else ""

        # Add a timestamp to check for active in-progress generations
        current_time = time.time()

        if cache_key in self._picklist_cache:
            cached_result = self._picklist_cache[cache_key]

            # Check if this is an in-progress generation (indicated by a timestamp value)
            if isinstance(cached_result, float):
                # If the generation started less than 2 minutes ago, wait for it to complete
                if current_time - cached_result < 120:  # 2 minute timeout
                    logger.info(
                        f"Detected in-progress missing teams ranking for same parameters{request_info}, waiting for completion..."
                    )

                    # Wait for a short time to allow the other process to finish
                    for _ in range(12):  # Try for up to 1 minute
                        await asyncio.sleep(5)  # Wait 5 seconds between checks

                        # Check if the result is now available
                        if cache_key in self._picklist_cache and not isinstance(
                            self._picklist_cache[cache_key], float
                        ):
                            logger.info(
                                f"Successfully retrieved result from parallel missing teams ranking{request_info}"
                            )
                            return self._picklist_cache[cache_key]

                    # If we get here, the other process took too long or failed
                    logger.warning(
                        f"Timeout waiting for parallel missing teams ranking, proceeding with new generation{request_info}"
                    )
                    # Fall through to generate a new result
                else:
                    # The previous generation is stale, remove it and continue
                    logger.warning(
                        f"Found stale in-progress missing teams ranking, starting fresh{request_info}"
                    )
                    del self._picklist_cache[cache_key]
            else:
                # We have a valid cached result
                logger.info(f"Using cached missing teams ranking{request_info}")
                return cached_result

        # Mark this cache key as "in progress" by storing the current timestamp
        self._picklist_cache[cache_key] = current_time

        # Get your team data
        your_team = self._get_team_by_number(your_team_number)
        if not your_team:
            return {
                "status": "error",
                "message": f"Your team {your_team_number} not found in dataset",
            }

        # Prepare team data for GPT (only for missing teams)
        all_teams_data = self._prepare_team_data_for_gpt()
        teams_data = [
            team
            for team in all_teams_data
            if team["team_number"] in missing_team_numbers
        ]

        if not teams_data:
            return {
                "status": "error",
                "message": f"No team data found for missing teams",
            }

        try:
            # Start comprehensive logging
            logger.info(f"====== STARTING MISSING TEAMS RANKING ======")
            logger.info(f"Pick position: {pick_position}")
            logger.info(f"Your team: {your_team_number}")
            logger.info(f"Priority metrics count: {len(priorities)}")
            logger.info(f"Missing teams to rank: {len(teams_data)}")
            logger.info(f"Missing team numbers: {missing_team_numbers}")

            # Initialize variables
            start_time = time.time()
            estimated_time = (
                len(teams_data) * 0.5
            )  # ~0.5 seconds per team (faster for smaller batch)
            logger.info(f"Estimated completion time: {estimated_time:.1f} seconds")

            # Create specialized system prompt for missing teams
            system_prompt = self._create_missing_teams_system_prompt(
                pick_position, len(teams_data)
            )

            # Create specialized user prompt for missing teams that includes already-ranked teams
            user_prompt = self._create_missing_teams_user_prompt(
                your_team_number, pick_position, priorities, teams_data, ranked_teams
            )

            # Log prompts (truncated for readability)
            truncated_system = (
                system_prompt[:500] + "..."
                if len(system_prompt) > 500
                else system_prompt
            )
            logger.info(f"MISSING TEAMS SYSTEM PROMPT (truncated):\n{truncated_system}")

            # Initialize messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Make a single API call to rank missing teams
            logger.info(
                f"--- Requesting rankings for {len(missing_team_numbers)} missing teams ---"
            )
            request_start_time = time.time()

            # Call GPT with optimized settings
            logger.info("Starting API call...")

            # Use exponential backoff for rate limit handling
            max_retries = 3
            initial_delay = 1.0  # Start with a 1-second delay
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    response = client.chat.completions.create(
                        model=GPT_MODEL,
                        messages=messages,
                        temperature=0.2,
                        response_format={"type": "json_object"},
                        max_tokens=4000,  # Increased to match main method
                    )
                    # Success - break out of the retry loop
                    break
                except Exception as e:
                    # Check if it's a rate limit error (typically a 429 status code)
                    is_rate_limit = "429" in str(e)

                    if is_rate_limit and retry_count < max_retries:
                        # Calculate exponential backoff delay
                        retry_count += 1
                        delay = initial_delay * (2**retry_count)  # Exponential backoff

                        logger.warning(
                            f"Rate limit hit when ranking missing teams. Retrying in {delay:.2f} seconds... (Attempt {retry_count}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        # Either not a rate limit error or we've exceeded max retries
                        logger.error(f"API call for missing teams failed: {str(e)}")
                        raise  # Re-raise the exception

            # Log timing and response metadata
            request_time = time.time() - request_start_time
            logger.info(
                f"Total response time: {request_time:.2f}s (avg: {request_time/len(teams_data):.2f}s per team)"
            )
            logger.info(
                f"Response metadata: finish_reason={response.choices[0].finish_reason}, model={response.model}"
            )

            # Check if the response was truncated due to token limits
            if response.choices[0].finish_reason == "length":
                logger.error("Response was truncated due to token length limit")
                return {
                    "status": "error",
                    "message": "The AI response was cut off due to length limits. Please try with fewer teams or use batch processing.",
                }

            # Parse the response
            response_content = response.choices[0].message.content
            response_sample = (
                response_content[:200] + "..."
                if len(response_content) > 200
                else response_content
            )
            logger.info(f"Response sample: {response_sample}")

            # Parse the JSON response with error handling
            try:
                # Log the full raw response (limited to 1000 chars) for debugging purposes
                if len(response_content) > 1000:
                    logger.info(
                        f"Raw JSON response (first 1000 chars):\n{response_content[:1000]}"
                    )
                else:
                    logger.info(f"Raw JSON response:\n{response_content}")

                response_data = json.loads(response_content)

                # Check for overflow condition in ultra-compact format
                if response_data.get("s") == "overflow":
                    logger.warning("GPT returned overflow status - token limit reached")
                    return {
                        "status": "error",
                        "message": "The amount of team data exceeded the token limit. Please try with fewer teams or simplified priorities.",
                    }
                # Check for overflow in regular format
                elif response_data.get("status") == "overflow":
                    logger.warning("GPT returned overflow status - token limit reached")
                    return {
                        "status": "error",
                        "message": "The amount of team data exceeded the token limit. Please try with fewer teams or simplified priorities.",
                    }

                # Handle ultra-compact format {"p":[[team,score,"reason"]...],"s":"ok"}
                if "p" in response_data and isinstance(response_data["p"], list):
                    logger.info(
                        f"Response contains {len(response_data['p'])} teams in ultra-compact format"
                    )

                    # Log first few teams for debugging
                    teams_sample = response_data["p"][:3]
                    logger.info(
                        f"First few teams (ultra-compact): {json.dumps(teams_sample)}"
                    )

                    # Check for repeating patterns in teams
                    team_nums = [
                        int(entry[0]) for entry in response_data["p"] if len(entry) >= 1
                    ]
                    team_counts = {}
                    for team_num in team_nums:
                        team_counts[team_num] = team_counts.get(team_num, 0) + 1

                    # Check if we have duplicates
                    duplicates = {
                        team: count for team, count in team_counts.items() if count > 1
                    }
                    if duplicates:
                        logger.warning(f"Response contains duplicates: {duplicates}")
                        logger.warning(f"First 20 team numbers: {team_nums[:20]}")

                        # Check if we have a repeating pattern
                        if len(team_nums) > 16:
                            # Check for common sequence lengths
                            for pattern_length in [4, 8, 12, 16]:
                                if len(team_nums) >= pattern_length * 2:
                                    pattern1 = team_nums[:pattern_length]
                                    pattern2 = team_nums[
                                        pattern_length : pattern_length * 2
                                    ]
                                    if pattern1 == pattern2:
                                        logger.warning(
                                            f"Detected repeating pattern of length {pattern_length}"
                                        )
                                        logger.warning(
                                            f"Model is repeating teams instead of ranking all teams"
                                        )
                                        # Truncate to first pattern only to avoid duplicates
                                        logger.warning(
                                            f"Truncating response to first {pattern_length} teams"
                                        )
                                        response_data["p"] = response_data["p"][
                                            :pattern_length
                                        ]
                                        break

                    # Calculate duplication percentage
                    total_entries = len(team_nums)
                    unique_teams = len(team_counts)
                    if total_entries > 0:  # Prevent division by zero
                        duplication_percentage = (
                            (total_entries - unique_teams) / total_entries
                        ) * 100
                        logger.warning(
                            f"Duplication percentage: {duplication_percentage:.1f}%"
                        )

                        # If duplication is extreme (over 80%), warn that model might be in a loop
                        if duplication_percentage > 80 and total_entries > 30:
                            logger.error(
                                f"MODEL APPEARS TO BE LOOPING - {duplication_percentage:.1f}% duplicates"
                            )
                            return {
                                "status": "error",
                                "message": "The model is unable to rank all missing teams at once. Please try reducing the number of teams to rank (e.g., 10-20 at a time) or simplify the priorities. The model got stuck repeating the same teams.",
                            }

                    # Convert ultra-compact format to standard format
                    rankings = []
                    seen_teams = set()  # Track teams we've already added

                    for team_entry in response_data["p"]:
                        if (
                            len(team_entry) >= 3
                        ):  # Ensure we have at least [team/index, score, reason]
                            first_value = int(team_entry[0])

                            # If we have an index map, convert index to team number
                            if team_index_map and first_value in team_index_map:
                                team_number = team_index_map[first_value]
                                logger.debug(
                                    f"Mapped index {first_value} to team {team_number}"
                                )
                            else:
                                team_number = first_value

                            # Skip if we've seen this team already
                            if team_number in seen_teams:
                                logger.info(
                                    f"Skipping duplicate team {team_number} in response"
                                )
                                continue

                            seen_teams.add(team_number)
                            score = float(team_entry[1])
                            reason = team_entry[2]

                            # Get team nickname from dataset if available
                            team_data = next(
                                (
                                    t
                                    for t in teams_data
                                    if t["team_number"] == team_number
                                ),
                                None,
                            )
                            nickname = (
                                team_data.get("nickname", f"Team {team_number}")
                                if team_data
                                else f"Team {team_number}"
                            )

                            rankings.append(
                                {
                                    "team_number": team_number,
                                    "nickname": nickname,
                                    "score": score,
                                    "reasoning": reason,
                                }
                            )

                # Handle regular compact format
                elif "missing_team_rankings" in response_data and isinstance(
                    response_data["missing_team_rankings"], list
                ):
                    logger.info(
                        f"Response contains {len(response_data['missing_team_rankings'])} teams in regular format"
                    )

                    # Log first few teams for debugging
                    teams_sample = response_data["missing_team_rankings"][:3]
                    logger.info(f"First few teams: {json.dumps(teams_sample)}")

                    raw_rankings = response_data["missing_team_rankings"]

                    # Convert compact format to standard format if needed
                    rankings = []
                    for team_entry in raw_rankings:
                        # Check if using new compact format (has "team" instead of "team_number")
                        if "team" in team_entry and "team_number" not in team_entry:
                            team_number = team_entry["team"]
                            # Get team nickname from dataset if available
                            team_data = next(
                                (
                                    t
                                    for t in teams_data
                                    if t["team_number"] == team_number
                                ),
                                None,
                            )
                            nickname = (
                                team_data.get("nickname", f"Team {team_number}")
                                if team_data
                                else f"Team {team_number}"
                            )

                            rankings.append(
                                {
                                    "team_number": team_number,
                                    "nickname": nickname,
                                    "score": team_entry.get("score", 0.0),
                                    "reasoning": team_entry.get(
                                        "reason", "No reasoning provided"
                                    ),
                                }
                            )
                        else:
                            # Already in standard format
                            rankings.append(team_entry)
                else:
                    logger.warning("Response has no valid rankings")
                    rankings = []

            except json.JSONDecodeError as e:
                # Apply same JSON error recovery as in generate_picklist
                logger.error(f"JSON parse error: {e}")
                try:
                    # Try to use regex to extract team data
                    import re

                    # Try to extract from ultra-compact format first
                    # Format: [teamnum,score,"reason"] in a p array
                    compact_pattern = r'\[\s*(\d+)\s*,\s*([\d\.]+)\s*,\s*"([^"]*)"\s*\]'
                    compact_teams_extracted = re.findall(
                        compact_pattern, response_content
                    )

                    if compact_teams_extracted:
                        logger.info(
                            f"Extracted {len(compact_teams_extracted)} team entries from broken ultra-compact JSON"
                        )

                        # Log the first few raw extractions for debugging
                        for i, team_raw in enumerate(compact_teams_extracted[:3]):
                            logger.info(
                                f"Raw extraction {i+1} (ultra-compact): {team_raw}"
                            )

                        # Also log team numbers in sequence to check for patterns in the duplicates
                        team_numbers_sequence = [
                            int(t[0]) for t in compact_teams_extracted[:20]
                        ]
                        logger.info(
                            f"First 20 team numbers in missing teams response: {team_numbers_sequence}"
                        )

                        rankings = []
                        team_numbers_seen = (
                            set()
                        )  # Track team numbers to detect duplicates in regex extraction

                        for team_match in compact_teams_extracted:
                            try:
                                team_number = int(team_match[0])
                                score = float(team_match[1])
                                reasoning = team_match[2]

                                # Skip obvious duplicates during extraction
                                if team_number in team_numbers_seen:
                                    logger.info(
                                        f"Skipping duplicate team {team_number} during regex extraction"
                                    )
                                    continue

                                team_numbers_seen.add(team_number)

                                # Get team nickname from dataset if available
                                team_data = next(
                                    (
                                        t
                                        for t in teams_data
                                        if t["team_number"] == team_number
                                    ),
                                    None,
                                )
                                nickname = (
                                    team_data.get("nickname", f"Team {team_number}")
                                    if team_data
                                    else f"Team {team_number}"
                                )

                                rankings.append(
                                    {
                                        "team_number": team_number,
                                        "nickname": nickname,
                                        "score": score,
                                        "reasoning": reasoning,
                                    }
                                )
                            except Exception as team_error:
                                logger.error(f"Error parsing team data: {team_error}")
                                continue

                        logger.info(
                            f"Salvaged {len(rankings)} teams from broken response"
                        )
                    else:
                        # Try older formats if ultra-compact format not found
                        team_pattern1 = r'"team":\s*(\d+),\s*"score":\s*([\d\.]+),\s*"reason":\s*"([^"]*)"'
                        team_pattern2 = r'"team_number":\s*(\d+),\s*"nickname":\s*"([^"]*)",\s*"score":\s*([\d\.]+),\s*"reasoning":\s*"([^"]*)"'

                        teams_extracted1 = re.findall(team_pattern1, response_content)
                        teams_extracted2 = re.findall(team_pattern2, response_content)

                        if teams_extracted1:
                            logger.info(
                                f"Extracted {len(teams_extracted1)} team entries from broken compact JSON"
                            )

                            # Log the first few raw extractions for debugging
                            for i, team_raw in enumerate(teams_extracted1[:3]):
                                logger.info(
                                    f"Raw extraction {i+1} (compact): {team_raw}"
                                )

                            rankings = []
                            team_numbers_seen = (
                                set()
                            )  # Track team numbers to detect duplicates

                            for team_match in teams_extracted1:
                                try:
                                    team_number = int(team_match[0])
                                    score = float(team_match[1])
                                    reasoning = team_match[2]

                                    # Skip obvious duplicates during extraction
                                    if team_number in team_numbers_seen:
                                        logger.info(
                                            f"Skipping duplicate team {team_number} during regex extraction"
                                        )
                                        continue

                                    team_numbers_seen.add(team_number)

                                    # Get team nickname from dataset if available
                                    team_data = next(
                                        (
                                            t
                                            for t in teams_data
                                            if t["team_number"] == team_number
                                        ),
                                        None,
                                    )
                                    nickname = (
                                        team_data.get("nickname", f"Team {team_number}")
                                        if team_data
                                        else f"Team {team_number}"
                                    )

                                    rankings.append(
                                        {
                                            "team_number": team_number,
                                            "nickname": nickname,
                                            "score": score,
                                            "reasoning": reasoning,
                                        }
                                    )
                                except Exception as team_error:
                                    logger.error(
                                        f"Error parsing team data: {team_error}"
                                    )
                                    continue

                            logger.info(
                                f"Salvaged {len(rankings)} teams from broken response"
                            )
                        elif teams_extracted2:
                            logger.info(
                                f"Extracted {len(teams_extracted2)} team entries from broken standard JSON"
                            )

                            # Log the first few raw extractions for debugging
                            for i, team_raw in enumerate(teams_extracted2[:3]):
                                logger.info(f"Raw extraction {i+1}: {team_raw}")

                            rankings = []
                            team_numbers_seen = (
                                set()
                            )  # Track team numbers to detect duplicates

                            for team_match in teams_extracted2:
                                try:
                                    team_number = int(team_match[0])
                                    team_name = team_match[1]
                                    score = float(team_match[2])
                                    reasoning = team_match[3]

                                    # Skip obvious duplicates during extraction
                                    if team_number in team_numbers_seen:
                                        logger.info(
                                            f"Skipping duplicate team {team_number} during regex extraction of missing teams"
                                        )
                                        continue

                                    team_numbers_seen.add(team_number)

                                    rankings.append(
                                        {
                                            "team_number": team_number,
                                            "nickname": team_name,
                                            "score": score,
                                            "reasoning": reasoning,
                                        }
                                    )
                                except Exception as team_error:
                                    logger.error(
                                        f"Error parsing team data: {team_error}"
                                    )
                                    continue

                            logger.info(
                                f"Salvaged {len(rankings)} teams from broken response"
                            )
                        else:
                            # If we couldn't extract any teams, raise error
                            logger.error(
                                "Could not extract any team data from the broken response"
                            )
                            rankings = []
                except Exception as extract_error:
                    logger.error(f"Failed to extract team data: {extract_error}")
                    rankings = []

            # Process the missing team rankings
            logger.info("=== Processing missing team rankings ===")
            logger.info(f"Total teams received: {len(rankings)}")

            # Check for duplicate teams and handle them intelligently - same logic as in generate_picklist
            team_entries = {}  # Map team numbers to their entries
            duplicates = []

            for team in rankings:
                team_number = team.get("team_number")
                if not team_number:
                    continue  # Skip teams without a valid team number

                if team_number not in team_entries:
                    # First time seeing this team
                    team_entries[team_number] = team
                else:
                    # Found a duplicate team - keep the one with the higher score
                    duplicates.append(team_number)
                    current_score = team_entries[team_number].get("score", 0)
                    new_score = team.get("score", 0)

                    if new_score > current_score:
                        # This new entry has a higher score, use it instead
                        logger.info(
                            f"Missing team {team_number} appears twice - keeping entry with higher score ({new_score} vs {current_score})"
                        )
                        team_entries[team_number] = team

            # Create the deduplicated rankings from the team_entries map
            deduplicated_rankings = list(team_entries.values())

            if duplicates:
                logger.info(
                    f"Found {len(duplicates)} duplicate teams in missing teams rankings: {duplicates[:10]}..."
                )
                logger.info(
                    f"Resolved by keeping the entry with higher score for each team"
                )

                # Analyze the duplicates in more detail
                duplicate_counts = {}
                for team_num in duplicates:
                    if team_num not in duplicate_counts:
                        duplicate_counts[team_num] = 0
                    duplicate_counts[team_num] += 1

                # Find teams with the most duplicates
                sorted_duplicates = sorted(
                    duplicate_counts.items(), key=lambda x: x[1], reverse=True
                )
                if sorted_duplicates:
                    logger.info(
                        f"Most duplicated teams in missing teams rankings: {sorted_duplicates[:5]}"
                    )

                    # Log positions of a highly duplicated team
                    if sorted_duplicates[0][1] > 1:
                        most_duplicated = sorted_duplicates[0][0]
                        positions = [
                            i
                            for i, team in enumerate(rankings)
                            if team.get("team_number") == most_duplicated
                        ]
                        logger.info(
                            f"Team {most_duplicated} appears at positions: {positions}"
                        )

            logger.info(f"After deduplication: {len(deduplicated_rankings)} teams")

            # Check if we got all the missing teams
            ranked_team_numbers = {
                team["team_number"] for team in deduplicated_rankings
            }
            still_missing = set(missing_team_numbers) - ranked_team_numbers

            # Log the completeness
            coverage_percent = (
                (len(ranked_team_numbers) / len(missing_team_numbers)) * 100
                if missing_team_numbers
                else 0
            )
            logger.info(
                f"GPT coverage: {coverage_percent:.1f}% ({len(ranked_team_numbers)} of {len(missing_team_numbers)} teams)"
            )

            # For any teams that are still missing, add fallbacks
            if still_missing:
                logger.warning(f"Still missing {len(still_missing)} teams")
                logger.warning(f"Missing team numbers: {sorted(list(still_missing))}")

                # Get avg score from the ranked teams we were able to get for better consistency
                avg_score = (
                    sum([team["score"] for team in deduplicated_rankings])
                    / len(deduplicated_rankings)
                    if deduplicated_rankings
                    else 0.1
                )
                backup_score = max(0.1, avg_score * 0.7)  # Use 70% of avg score
                logger.info(
                    f"Using backup score {backup_score} for still missing teams"
                )

                # Add still missing teams to the rankings
                for team_number in still_missing:
                    team_data = next(
                        (t for t in teams_data if t["team_number"] == team_number), None
                    )
                    if team_data:
                        deduplicated_rankings.append(
                            {
                                "team_number": team_number,
                                "nickname": team_data.get(
                                    "nickname", f"Team {team_number}"
                                ),
                                "score": backup_score,
                                "reasoning": "Added to complete the picklist - not enough data available for detailed analysis",
                                "is_fallback": True,
                            }
                        )

            # Assemble final result
            result = {
                "status": "success",
                "missing_team_rankings": deduplicated_rankings,
                "performance": {
                    "total_time": request_time,
                    "team_count": len(missing_team_numbers),
                    "avg_time_per_team": (
                        request_time / len(missing_team_numbers)
                        if missing_team_numbers
                        else 0
                    ),
                    "missing_teams": len(still_missing),
                    "duplicate_teams": len(duplicates),
                },
            }

            # Log completion stats
            total_time = time.time() - start_time
            logger.info(f"====== MISSING TEAMS RANKING COMPLETE ======")
            logger.info(
                f"Total time: {total_time:.2f}s for {len(deduplicated_rankings)} teams"
            )
            logger.info(
                f"Average time per team: {(total_time / len(deduplicated_rankings) if deduplicated_rankings else 0):.2f}s"
            )

            # Cache the result, replacing the "in progress" timestamp
            self._picklist_cache[cache_key] = result

            logger.info(f"Successfully completed missing teams ranking{request_info}")
            return result

        except Exception as e:
            logger.error(
                f"Error ranking missing teams with GPT: {str(e)}{request_info}",
                exc_info=True,
            )

            # Clean up the in-progress flag from cache so future requests can proceed
            if cache_key in self._picklist_cache and isinstance(
                self._picklist_cache[cache_key], float
            ):
                del self._picklist_cache[cache_key]

            return {
                "status": "error",
                "message": f"Failed to rank missing teams: {str(e)}",
            }

    def _create_missing_teams_system_prompt(
        self, pick_position: str, team_count: int
    ) -> str:
        """
        Create a specialized system prompt for ranking missing teams.
        Uses the ultra-compact schema to optimize token usage.

        Args:
            pick_position: 'first', 'second', or 'third'
            team_count: Number of missing teams to rank

        Returns:
            System prompt string
        """
        position_context = {
            "first": "First pick teams should be overall powerhouse teams that excel in multiple areas.",
            "second": "Second pick teams should complement the first pick and address specific needs.",
            "third": "Third pick teams are more specialized, often focusing on a single critical function.",
        }

        return f"""You are GPT-4o, an FRC pick-list strategist.

TASK
Rank ALL {team_count} unique missing teams for the {pick_position} pick of Team {{your_team_number}}.
Return MINIFIED JSON, ONE LINE, NO SPACES/NEWLINES using THIS exact shape:

{{"p":[[team,score,"reason"]...],"s":"ok"}}

⚠️ CRITICAL RULES:
1. Each team MUST appear EXACTLY ONCE. NO DUPLICATES ALLOWED!
2. Include ALL {team_count} teams from MISSING_TEAM_NUMBERS.
3. Each reason must be ≤8 words, NO REPETITION, cite 1 metric (e.g. "Strong climber: 15s").
4. NO repetitive words or phrases. Be concise and specific.
5. NO whitespaces, tabs, or line-breaks in the output.
6. If you cannot fit ALL {team_count} teams, STOP and ONLY return: {{"s":"overflow"}}

EXAMPLE: {{"p":[[1234,7.2,"Fast auto: 3.1 avg"],[5678,6.8,"Reliable endgame"]],"s":"ok"}}

ULTRA-COMPACT STRUCTURE EXPLANATION:
- "p" is the array of team entries (replaces "missing_team_rankings")
- Each team is [team_number, score, "reason"] (array instead of object)
- "s" is status ("ok" or "overflow")

TOKEN OPTIMIZATION EXAMPLES (use different teams):
- [254, 98.3, "Strong autonomous EPA 25.7"]
- [1678, 92.1, "Excellent climb consistency 96%"]
- [3310, 87.5, "High teleop scoring average 15.2 points"]
- [118, 85.2, "Great defense rating 8.9"]

VALIDATION REQUIREMENTS:
1. Verify ALL {team_count} teams are included - CHECK CLOSELY!
2. Check for duplicated team numbers - NONE ALLOWED!
3. Verify your reasoning strings are ≤ 12 words each
4. Ensure JSON is complete, valid, and has NO WHITESPACE

Additional context: {position_context.get(pick_position, "")}

OVERFLOW HANDLING: If you cannot include all {team_count} teams, return ONLY {{"s":"overflow"}} - nothing else.
KEY REQUIREMENT: Make your rankings consistent with the examples of already-ranked teams.
"""

    def _create_missing_teams_user_prompt(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        missing_teams_data: List[Dict[str, Any]],
        ranked_teams: List[Dict[str, Any]],
    ) -> str:
        """
        Create a specialized user prompt for ranking missing teams.
        Includes samples of already-ranked teams for stylistic consistency.

        Args:
            your_team_number: Your team's number
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric priorities with weights
            missing_teams_data: Data for teams that need to be ranked
            ranked_teams: Teams that have already been ranked (for context)

        Returns:
            User prompt string
        """
        # Find your team's data
        your_team_info = next(
            (
                team
                for team in self._prepare_team_data_for_gpt()
                if team["team_number"] == your_team_number
            ),
            None,
        )

        # Get top and bottom examples from ranked teams
        ranked_sample = []
        if ranked_teams and len(ranked_teams) > 2:
            # Include top, middle, and bottom ranked teams as examples
            ranked_sample.append(ranked_teams[0])  # Top team
            middle_idx = len(ranked_teams) // 2
            ranked_sample.append(ranked_teams[middle_idx])  # Middle team
            ranked_sample.append(ranked_teams[-1])  # Bottom team

        missing_team_numbers = [team["team_number"] for team in missing_teams_data]

        prompt = f"""YOUR_TEAM_PROFILE = {json.dumps(your_team_info, indent=2) if your_team_info else "{}"} 
PRIORITY_METRICS  = {json.dumps(priorities, indent=2)}
MISSING_TEAM_NUMBERS = {json.dumps(missing_team_numbers)}

ALREADY_RANKED_EXAMPLES = {json.dumps(ranked_sample, indent=2)}

⚠️ CRITICAL INSTRUCTIONS:
1. You MUST rank ONLY the teams in MISSING_TEAM_NUMBERS.
2. Each team MUST appear EXACTLY ONCE in your output. NO DUPLICATES ALLOWED!
3. Use the same metrics and style as the ALREADY_RANKED_EXAMPLES.
4. Evaluate for alliance synergy with Team {your_team_number}.
5. Maintain consistent scoring scale with ALREADY_RANKED_EXAMPLES.
6. VERIFY before submitting that you've included ALL teams in MISSING_TEAM_NUMBERS.
7. Use the ultra-compact format: {{"p":[[team,score,"reason"]...],"s":"ok"}}

VALIDATION CHECKLIST:
- ✓ Each team from MISSING_TEAM_NUMBERS appears exactly once
- ✓ No team is duplicated or missing
- ✓ Each reason is ≤ 12 words
- ✓ Metrics are cited in each reason
- ✓ JSON format is correct with no whitespace

TEAMS_TO_RANK = {json.dumps(missing_teams_data, indent=2)}

End of prompt.
"""
        return prompt

    def _select_reference_teams(
        self,
        ranked_teams: List[Dict[str, Any]],
        reference_teams_count: int,
        reference_selection: str,
    ) -> List[Dict[str, Any]]:
        """
        Select reference teams from already ranked teams using specified strategy.

        Args:
            ranked_teams: List of already ranked teams
            reference_teams_count: Number of reference teams to select
            reference_selection: Strategy for selecting reference teams
                                 ('even_distribution', 'percentile', or 'top_middle_bottom')

        Returns:
            List of selected reference teams
        """
        if not ranked_teams or reference_teams_count <= 0:
            return []

        # Limit reference count to the available teams
        reference_teams_count = min(reference_teams_count, len(ranked_teams))

        # Sort teams by score to ensure consistent selection
        sorted_teams = sorted(
            ranked_teams, key=lambda x: x.get("score", 0), reverse=True
        )

        if reference_selection == "top_middle_bottom":
            # Always select top, middle, and bottom teams
            selected_indices = []

            # Always include the top team
            if len(sorted_teams) > 0:
                selected_indices.append(0)

            # Include the middle team if we have at least 3 teams
            if len(sorted_teams) >= 3:
                selected_indices.append(len(sorted_teams) // 2)

            # Include the bottom team if we have at least 2 teams
            if len(sorted_teams) >= 2:
                selected_indices.append(len(sorted_teams) - 1)

            # Add more teams evenly distributed if needed
            if reference_teams_count > len(selected_indices):
                # Calculate how many additional teams we need
                additional_needed = reference_teams_count - len(selected_indices)

                # Create evenly spaced indices for the remaining slots
                remaining_indices = list(range(len(sorted_teams)))
                # Remove already selected indices
                for idx in selected_indices:
                    if idx in remaining_indices:
                        remaining_indices.remove(idx)

                # Select additional teams with even spacing
                step = len(remaining_indices) / (additional_needed + 1)
                for i in range(1, additional_needed + 1):
                    idx = min(len(remaining_indices) - 1, int(i * step) - 1)
                    if idx >= 0 and idx < len(remaining_indices):
                        selected_indices.append(remaining_indices[idx])

            # Get the teams at the selected indices
            reference_teams = [
                sorted_teams[i]
                for i in sorted(selected_indices)
                if i < len(sorted_teams)
            ]

        elif reference_selection == "percentile":
            # Select teams at specific percentiles
            reference_teams = []

            # Calculate percentile step
            if reference_teams_count > 1:
                step = 100 / (reference_teams_count - 1)
            else:
                step = 50  # Just take the median if only one team requested

            # Select teams at each percentile
            for i in range(reference_teams_count):
                percentile = min(100, i * step)
                index = int((len(sorted_teams) - 1) * (percentile / 100))
                reference_teams.append(sorted_teams[index])

        else:  # Default to "even_distribution"
            # Select teams with even spacing from top to bottom
            step = len(sorted_teams) / (reference_teams_count)
            reference_teams = []

            for i in range(reference_teams_count):
                index = min(len(sorted_teams) - 1, int(i * step))
                reference_teams.append(sorted_teams[index])

        logger.info(
            f"Selected {len(reference_teams)} reference teams using '{reference_selection}' strategy"
        )
        for i, team in enumerate(reference_teams):
            logger.info(
                f"  Reference team {i+1}: {team['team_number']} (score: {team.get('score', 0):.1f})"
            )

        return reference_teams

    def get_batch_processing_status(self, cache_key: str) -> Dict[str, Any]:
        """
        Get the current status of a batch processing job.

        Args:
            cache_key: The cache key for the job

        Returns:
            Dict with batch processing status information
        """
        # Check if this is an in-progress job
        if cache_key in self._picklist_cache:
            cached_data = self._picklist_cache[cache_key]

            # If it's a timestamp, it's in progress but no batches have completed yet
            if isinstance(cached_data, float):
                return {
                    "status": "in_progress",
                    "batch_processing": {
                        "total_batches": 0,  # Unknown at this point
                        "current_batch": 0,
                        "progress_percentage": 0,
                        "processing_complete": False,
                    },
                }
            # If it's a dictionary with batch_processing info, return the status
            elif isinstance(cached_data, dict) and "batch_processing" in cached_data:
                return {
                    "status": (
                        "in_progress"
                        if not cached_data["batch_processing"].get(
                            "processing_complete"
                        )
                        else "success"
                    ),
                    "batch_processing": cached_data["batch_processing"],
                }
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

        # Not found in cache
        return {
            "status": "not_found",
            "batch_processing": {
                "total_batches": 0,
                "current_batch": 0,
                "progress_percentage": 0,
                "processing_complete": False,
            },
        }

    async def _process_team_batch(
        self,
        teams_data: List[Dict[str, Any]],
        reference_teams: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        batch_index: int,
        request_id: Optional[int] = None,
        cache_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a single batch of teams, including reference teams.

        Args:
            teams_data: Team data for this batch
            reference_teams: Reference teams from previous batches for consistent scoring
            your_team_number: Your team's number for alliance compatibility
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric IDs and weights to prioritize
            batch_index: Index of the current batch (for logging)
            request_id: Optional request ID for logging

        Returns:
            Dict with batch results containing ranked teams
        """
        try:
            # Combine batch teams and reference teams
            combined_teams = teams_data.copy()

            # Add reference teams if this isn't the first batch
            reference_team_numbers = set()
            if batch_index > 0 and reference_teams:
                # Track which teams are reference teams
                for team in reference_teams:
                    reference_team_numbers.add(team["team_number"])

                # Add reference teams to the batch
                combined_teams.extend(reference_teams)

                logger.info(
                    f"Batch {batch_index}: Added {len(reference_teams)} reference teams to the batch"
                )
                logger.info(
                    f"Batch {batch_index}: Reference team numbers: {sorted(list(reference_team_numbers))}"
                )

            # Get list of team numbers in this batch
            batch_team_numbers = sorted(
                [team["team_number"] for team in combined_teams]
            )

            logger.info(
                f"Batch {batch_index}: Processing {len(combined_teams)} teams (including {len(reference_teams)} reference teams)"
            )
            logger.info(
                f"Batch {batch_index}: Team numbers: {batch_team_numbers[:10]}... (and {len(batch_team_numbers) - 10} more)"
                if len(batch_team_numbers) > 10
                else f"Batch {batch_index}: Team numbers: {batch_team_numbers}"
            )

            # Create prompt for this batch
            system_prompt = self._create_system_prompt(
                pick_position, len(combined_teams)
            )

            # Create a modified user prompt with reference team context
            user_prompt = self._create_user_prompt_with_reference_teams(
                your_team_number,
                pick_position,
                priorities,
                combined_teams,
                batch_team_numbers,
                reference_team_numbers,
            )

            # Check token count before making the API call
            self._check_token_count(system_prompt, user_prompt)

            # Initialize messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Log start of API call
            request_start_time = time.time()
            logger.info(f"Batch {batch_index}: Starting API call...")

            # Use exponential backoff for rate limit handling
            max_retries = 3
            initial_delay = 1.0  # Start with a 1-second delay
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    response = client.chat.completions.create(
                        model=GPT_MODEL,
                        messages=messages,
                        temperature=0.2,  # Lower temperature for more consistent results
                        response_format={"type": "json_object"},
                        max_tokens=4000,  # Increased to prevent truncation with the compact schema
                    )
                    # Success - break out of the retry loop
                    break
                except Exception as e:
                    # Check if it's a rate limit error (typically a 429 status code)
                    is_rate_limit = "429" in str(e)

                    if is_rate_limit and retry_count < max_retries:
                        # Calculate exponential backoff delay
                        retry_count += 1
                        delay = initial_delay * (2**retry_count)  # Exponential backoff

                        logger.warning(
                            f"Batch {batch_index}: Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {retry_count}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        # Either not a rate limit error or we've exceeded max retries
                        logger.error(f"Batch {batch_index}: API call failed: {str(e)}")
                        raise  # Re-raise the exception

            # Log timing and response metadata
            request_time = time.time() - request_start_time
            logger.info(
                f"Batch {batch_index}: Response time: {request_time:.2f}s (avg: {request_time/len(combined_teams):.2f}s per team)"
            )

            # Parse the response
            response_content = response.choices[0].message.content

            # Log a sample of the response (first 200 chars)
            response_sample = (
                response_content[:200] + "..."
                if len(response_content) > 200
                else response_content
            )
            logger.info(f"Batch {batch_index}: Response sample: {response_sample}")

            # Parse the JSON response - reuse existing parsing code
            response_data = json.loads(response_content)

            # Check for overflow condition in ultra-compact format
            if (
                response_data.get("s") == "overflow"
                or response_data.get("status") == "overflow"
            ):
                logger.warning(
                    f"Batch {batch_index}: GPT returned overflow status - token limit reached"
                )
                return {
                    "status": "error",
                    "message": f"Batch {batch_index}: The amount of team data exceeded the token limit.",
                }

            # Handle ultra-compact format {"p":[[team,score,"reason"]...],"s":"ok"}
            picklist = []

            if "p" in response_data and isinstance(response_data["p"], list):
                logger.info(
                    f"Batch {batch_index}: Response contains {len(response_data['p'])} teams in ultra-compact format"
                )

                # Log first few teams for debugging
                teams_sample = response_data["p"][:3]
                logger.info(
                    f"Batch {batch_index}: First few teams (ultra-compact): {json.dumps(teams_sample)}"
                )

                # Convert ultra-compact format to standard format
                seen_teams = set()  # Track teams we've already added

                for team_entry in response_data["p"]:
                    if (
                        len(team_entry) >= 3
                    ):  # Ensure we have at least [team, score, reason]
                        team_number = int(team_entry[0])

                        # Skip if we've seen this team already
                        if team_number in seen_teams:
                            logger.info(
                                f"Batch {batch_index}: Skipping duplicate team {team_number} in response"
                            )
                            continue

                        seen_teams.add(team_number)
                        score = float(team_entry[1])
                        reason = team_entry[2]

                        # Get team nickname from dataset if available
                        team_data = next(
                            (
                                t
                                for t in combined_teams
                                if t["team_number"] == team_number
                            ),
                            None,
                        )
                        nickname = (
                            team_data.get("nickname", f"Team {team_number}")
                            if team_data
                            else f"Team {team_number}"
                        )

                        # Mark reference teams
                        is_reference = team_number in reference_team_numbers

                        picklist.append(
                            {
                                "team_number": team_number,
                                "nickname": nickname,
                                "score": score,
                                "reasoning": reason,
                                "is_reference": is_reference,
                            }
                        )

            elif "picklist" in response_data and isinstance(
                response_data["picklist"], list
            ):
                logger.info(
                    f"Batch {batch_index}: Response contains {len(response_data['picklist'])} teams in regular format"
                )

                # Extract the picklist and convert from compact to full format if needed
                raw_picklist = response_data.get("picklist", [])

                # Convert compact format {"team":123, "score":45.6, "reason":"text"}
                # to standard format {"team_number":123, "nickname":"Team 123", "score":45.6, "reasoning":"text"}
                for team_entry in raw_picklist:
                    # Check if using new compact format (has "team" instead of "team_number")
                    if "team" in team_entry and "team_number" not in team_entry:
                        team_number = team_entry["team"]
                        # Get team nickname from dataset if available
                        team_data = next(
                            (
                                t
                                for t in combined_teams
                                if t["team_number"] == team_number
                            ),
                            None,
                        )
                        nickname = (
                            team_data.get("nickname", f"Team {team_number}")
                            if team_data
                            else f"Team {team_number}"
                        )

                        # Mark reference teams
                        is_reference = team_number in reference_team_numbers

                        picklist.append(
                            {
                                "team_number": team_number,
                                "nickname": nickname,
                                "score": team_entry.get("score", 0.0),
                                "reasoning": team_entry.get(
                                    "reason", "No reasoning provided"
                                ),
                                "is_reference": is_reference,
                            }
                        )
                    else:
                        # Already in standard format - add reference flag
                        team_number = team_entry.get("team_number")
                        is_reference = team_number in reference_team_numbers
                        team_entry["is_reference"] = is_reference
                        picklist.append(team_entry)
            else:
                logger.warning(f"Batch {batch_index}: Response has no valid picklist")

            # Log batch completion
            logger.info(
                f"Batch {batch_index}: Successfully processed {len(picklist)} teams"
            )

            return {
                "status": "success",
                "batch_index": batch_index,
                "picklist": picklist,
                "request_time": request_time,
            }

        except Exception as e:
            logger.error(
                f"Batch {batch_index}: Error processing batch: {str(e)}", exc_info=True
            )
            return {
                "status": "error",
                "batch_index": batch_index,
                "message": f"Error processing batch {batch_index}: {str(e)}",
            }

    def _create_user_prompt_with_reference_teams(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]],
        team_numbers: List[int],
        reference_team_numbers: Set[int] = None,
    ) -> str:
        """
        Create a user prompt for GPT with team data and reference team indicators.

        Args:
            your_team_number: Your team's number
            pick_position: 'first', 'second', or 'third'
            priorities: List of metric priorities with weights
            teams_data: Prepared team data for context
            team_numbers: List of team numbers to verify inclusion
            reference_team_numbers: Set of team numbers that are reference teams

        Returns:
            User prompt string
        """
        # Find your team's data
        your_team_info = next(
            (team for team in teams_data if team["team_number"] == your_team_number),
            None,
        )

        reference_info = ""
        if reference_team_numbers and len(reference_team_numbers) > 0:
            reference_info = f"""
REFERENCE_TEAM_NUMBERS = {json.dumps(sorted(list(reference_team_numbers)))}

IMPORTANT: The teams in REFERENCE_TEAM_NUMBERS are reference teams from previous batches.
Your scoring should be CONSISTENT with these reference teams. Use them as anchors to
calibrate your scoring and maintain a similar scale for the new teams in this batch.
"""

        # Calculate weighted scores for each team before passing to GPT
        teams_with_scores = []
        for team in teams_data:
            weighted_score = self._calculate_weighted_score(team, priorities)
            team_with_score = team.copy()
            team_with_score["weighted_score"] = weighted_score
            teams_with_scores.append(team_with_score)

        prompt = f"""YOUR_TEAM_PROFILE = {json.dumps(your_team_info) if your_team_info else "{}"} 
PRIORITY_METRICS  = {json.dumps(priorities)}   # include weight field
GAME_CONTEXT      = {json.dumps(self.game_context) if self.game_context else "null"}
TEAM_NUMBERS_TO_INCLUDE = {json.dumps(team_numbers)}
{reference_info}
AVAILABLE_TEAMS = {json.dumps(teams_with_scores)}     # include pre‑computed weighted_score

Please produce output following RULES.
"""
        return prompt

    def _combine_batch_results(
        self, batch_results: List[Dict[str, Any]], reference_teams_count: int
    ) -> List[Dict[str, Any]]:
        """
        Combine results from multiple batches into a single ranked list.

        Args:
            batch_results: List of successful batch processing results
            reference_teams_count: Number of reference teams used (for normalization)

        Returns:
            Combined and normalized picklist
        """
        if not batch_results:
            return []

        # Extract all teams from all batches
        all_teams = []
        reference_scores = {}  # Map of team_number to list of scores across batches

        # First pass: collect reference teams and their scores across batches
        for batch in batch_results:
            batch_picklist = batch.get("picklist", [])

            for team in batch_picklist:
                if team.get("is_reference", False):
                    team_number = team["team_number"]
                    if team_number not in reference_scores:
                        reference_scores[team_number] = []
                    reference_scores[team_number].append(team["score"])

        # Calculate average score for each reference team
        reference_avg_scores = {}
        for team_number, scores in reference_scores.items():
            reference_avg_scores[team_number] = sum(scores) / len(scores)

        logger.info(f"Reference teams with average scores: {reference_avg_scores}")

        # Calculate normalization factors for each batch
        batch_normalization_factors = []

        for batch_index, batch in enumerate(batch_results):
            batch_picklist = batch.get("picklist", [])

            # Skip empty batches
            if not batch_picklist:
                batch_normalization_factors.append(1.0)  # No normalization needed
                continue

            # Find reference teams in this batch
            batch_reference_teams = [
                (team["team_number"], team["score"])
                for team in batch_picklist
                if team.get("is_reference", False)
                and team["team_number"] in reference_avg_scores
            ]

            # Skip normalization for the first batch
            if batch_index == 0 or not batch_reference_teams:
                batch_normalization_factors.append(1.0)  # No normalization needed
                continue

            # Calculate normalization factor based on reference team scores
            normalization_sum = 0
            normalization_count = 0

            for team_number, batch_score in batch_reference_teams:
                avg_score = reference_avg_scores[team_number]
                # Avoid division by zero
                if batch_score != 0:
                    normalization_sum += avg_score / batch_score
                    normalization_count += 1

            # Calculate the average normalization factor
            normalization_factor = (
                normalization_sum / normalization_count
                if normalization_count > 0
                else 1.0
            )

            # Log the normalization details
            logger.info(
                f"Batch {batch_index}: Normalization factor = {normalization_factor:.4f} (based on {normalization_count} reference teams)"
            )
            batch_normalization_factors.append(normalization_factor)

        # Second pass: add all teams with normalized scores
        for batch_index, batch in enumerate(batch_results):
            batch_picklist = batch.get("picklist", [])
            normalization_factor = batch_normalization_factors[batch_index]

            for team in batch_picklist:
                # Skip reference teams (except from first batch)
                if team.get("is_reference", False) and batch_index > 0:
                    continue

                # Apply normalization to the score
                if normalization_factor != 1.0:
                    original_score = team["score"]
                    team["score"] = original_score * normalization_factor
                    team["original_score"] = (
                        original_score  # Keep track of the original score
                    )

                # Remove the reference flag
                if "is_reference" in team:
                    del team["is_reference"]

                all_teams.append(team)

        # Remove any potential duplicates (keeping the one from the earliest batch)
        unique_teams = {}
        for team in all_teams:
            team_number = team["team_number"]
            if team_number not in unique_teams:
                unique_teams[team_number] = team

        # Convert to list and sort by score (descending)
        combined_picklist = list(unique_teams.values())
        combined_picklist.sort(key=lambda x: x.get("score", 0), reverse=True)

        return combined_picklist

    async def _rerank_after_batches(
        self,
        combined_picklist: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Send the combined picklist back to GPT for a final global ranking."""

        team_numbers = [t["team_number"] for t in combined_picklist]

        all_teams = self._prepare_team_data_for_gpt()
        teams_data = [t for t in all_teams if t["team_number"] in team_numbers]

        # Keep original order for mapping
        teams_data.sort(key=lambda t: team_numbers.index(t["team_number"]))

        system_prompt = self._create_system_prompt(pick_position, len(teams_data))
        team_index_map = {i + 1: t["team_number"] for i, t in enumerate(teams_data)}
        user_prompt = self._create_user_prompt(
            your_team_number,
            pick_position,
            priorities,
            teams_data,
            team_numbers,
            team_index_map,
        )

        self._check_token_count(system_prompt, user_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=4000,
            )
            response_data = json.loads(response.choices[0].message.content)
            picklist = self._parse_response_with_index_mapping(
                response_data, teams_data, team_index_map
            )
            return picklist if picklist else combined_picklist
        except Exception as e:
            logger.error(f"Final re-ranking failed: {e}")
            return combined_picklist

    def merge_and_update_picklist(
        self, picklist: List[Dict[str, Any]], user_rankings: List[Dict[str, Any]]
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
                new_picklist.append(
                    {
                        "team_number": team_number,
                        "nickname": ranking.get("nickname", f"Team {team_number}"),
                        "score": ranking.get("score", 0.0),
                        "reasoning": "Manually added by user",
                    }
                )

        return new_picklist
