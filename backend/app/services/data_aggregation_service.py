# backend/app/services/data_aggregation_service.py

import json
import logging
import os
from typing import Any, Dict, List, Optional

from app.services.game_context_extractor_service import GameContextExtractorService
from app.config.extraction_config import get_extraction_config

logger = logging.getLogger("data_aggregation_service")


class DataAggregationService:
    """
    Service for collecting, transforming, and validating data from multiple sources.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    """

    def __init__(self, unified_dataset_path: str, use_extracted_context: bool = True):
        """
        Initialize the data aggregation service.
        
        Args:
            unified_dataset_path: Path to the unified dataset JSON file
            use_extracted_context: Whether to use extracted context (True) or full manual (False)
        """
        self.dataset_path = unified_dataset_path
        self.dataset = self._load_dataset()
        self.teams_data = self.dataset.get("teams", {})
        self.year = self.dataset.get("year", 2025)
        self.event_key = self.dataset.get("event_key", f"{self.year}arc")
        self.use_extracted_context = use_extracted_context
        
        # Initialize extraction service if using extracted context
        if self.use_extracted_context:
            try:
                cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "cache", "game_context"
                )
                self.extractor_service = GameContextExtractorService(cache_dir=cache_dir)
                logger.info("Initialized game context extractor service")
            except Exception as e:
                logger.warning(f"Failed to initialize extractor service: {e}")
                logger.warning("Falling back to full manual context")
                self.use_extracted_context = False
                self.extractor_service = None
        else:
            self.extractor_service = None

    def _load_dataset(self) -> Dict[str, Any]:
        """
        Load the unified dataset from the JSON file.
        
        Returns:
            Loaded dataset dictionary
        """
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
                logger.info(f"Loaded dataset from {self.dataset_path}")
                return dataset
        except FileNotFoundError:
            logger.error(f"Dataset file not found: {self.dataset_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in dataset file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading unified dataset: {e}")
            return {}

    def load_game_context(self) -> Optional[str]:
        """
        Load the game context for picklist generation.
        
        If extraction is enabled, returns optimized extracted context.
        Otherwise, returns the full manual text.
        
        Returns:
            Game context text or None if not available
        """
        try:
            manual_data = self._load_manual_data()
            if not manual_data:
                return None
                
            # Use extracted context if available and enabled
            if self.use_extracted_context and self.extractor_service:
                return self._get_extracted_context(manual_data)
            else:
                # Fall back to full manual context
                return self._get_full_manual_context(manual_data)
                
        except Exception as e:
            logger.error(f"Error loading game context: {e}")
            return None

    def _load_manual_data(self) -> Optional[Dict[str, Any]]:
        """
        Load the raw manual data from JSON file.
        
        Returns:
            Manual data dictionary or None if not available
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            manual_text_path = os.path.join(data_dir, f"manual_text_{self.year}.json")

            if os.path.exists(manual_text_path):
                with open(manual_text_path, "r", encoding="utf-8") as f:
                    manual_data = json.load(f)
                    logger.debug(f"Loaded manual data for {self.year}")
                    return manual_data
            else:
                logger.warning(f"Game manual not found: {manual_text_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading manual data: {e}")
            return None

    def _get_extracted_context(self, manual_data: Dict[str, Any]) -> Optional[str]:
        """
        Get extracted game context using the extraction service.
        
        Args:
            manual_data: Raw manual data dictionary
            
        Returns:
            Extracted context string or None if extraction fails
        """
        try:
            import asyncio
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_extraction_sync, manual_data)
                        extraction_result = future.result()
                else:
                    # Safe to run directly
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data)
                    )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data)
                    )
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            
            if extraction_result.success and extraction_result.extracted_context:
                # Convert extracted context to string format for compatibility
                extracted_data = extraction_result.extracted_context
                
                # Format extracted context for GPT consumption
                context_parts = []
                
                # Game information
                context_parts.append(f"Game: {extracted_data.get('game_name', '')} ({extracted_data.get('game_year', self.year)})")
                
                # Scoring summary
                if 'scoring_summary' in extracted_data:
                    context_parts.append("\nSCORING SUMMARY:")
                    scoring = extracted_data['scoring_summary']
                    
                    for phase in ['autonomous', 'teleop', 'endgame']:
                        if phase in scoring:
                            phase_data = scoring[phase]
                            context_parts.append(f"\n{phase.upper()} ({phase_data.get('duration_seconds', 0)}s):")
                            context_parts.append(f"  Objectives: {', '.join(phase_data.get('key_objectives', []))}")
                            context_parts.append(f"  Point Values: {phase_data.get('point_values', {})}")
                            if phase_data.get('strategic_notes'):
                                context_parts.append(f"  Strategy: {phase_data['strategic_notes']}")
                
                # Strategic elements
                if 'strategic_elements' in extracted_data and extracted_data['strategic_elements']:
                    context_parts.append("\nSTRATEGIC ELEMENTS:")
                    for element in extracted_data['strategic_elements']:
                        context_parts.append(f"- {element.get('name', '')}: {element.get('description', '')} (Impact: {element.get('alliance_impact', '')})")
                
                # Alliance considerations
                if 'alliance_considerations' in extracted_data and extracted_data['alliance_considerations']:
                    context_parts.append("\nALLIANCE CONSIDERATIONS:")
                    for consideration in extracted_data['alliance_considerations']:
                        context_parts.append(f"- {consideration}")
                
                # Key metrics
                if 'key_metrics' in extracted_data and extracted_data['key_metrics']:
                    context_parts.append("\nKEY METRICS:")
                    for metric in extracted_data['key_metrics']:
                        context_parts.append(f"- {metric.get('metric_name', '')}: {metric.get('description', '')} (Importance: {metric.get('importance', '')})")
                
                formatted_context = '\n'.join(context_parts)
                
                # Log token savings
                original_size = len(manual_data.get('relevant_sections', ''))
                extracted_size = len(formatted_context)
                savings = 100 * (1 - extracted_size / original_size) if original_size > 0 else 0
                
                logger.info(f"Using extracted context for {self.year} (Size reduction: {savings:.1f}%)")
                logger.info(f"Context size: {original_size} -> {extracted_size} characters")
                
                return formatted_context
            else:
                logger.warning(f"Extraction failed: {extraction_result.error}")
                logger.warning("Falling back to full manual context")
                return self._get_full_manual_context(manual_data)
                
        except Exception as e:
            logger.error(f"Error in extracted context: {e}")
            logger.warning("Falling back to full manual context")
            return self._get_full_manual_context(manual_data)

    def _get_full_manual_context(self, manual_data: Dict[str, Any]) -> str:
        """
        Get full manual context (original behavior).
        
        Args:
            manual_data: Raw manual data dictionary
            
        Returns:
            Full manual context string
        """
        game_context = f"Game: {manual_data.get('game_name', '')}\n\n{manual_data.get('relevant_sections', '')}"
        logger.info(f"Using full manual context for {self.year}")
        return game_context

    def _run_extraction_sync(self, manual_data: Dict[str, Any]) -> Any:
        """
        Helper method to run extraction in a new event loop.
        
        Args:
            manual_data: Manual data to extract from
            
        Returns:
            ExtractionResult from the extraction process
        """
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.extractor_service.extract_game_context(manual_data)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def _run_force_extraction_sync(self, manual_data: Dict[str, Any]) -> Any:
        """
        Helper method to run force extraction in a new event loop.
        
        Args:
            manual_data: Manual data to extract from
            
        Returns:
            ExtractionResult from the force extraction process
        """
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.extractor_service.extract_game_context(manual_data, force_refresh=True)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def force_extract_game_context(self) -> Dict[str, Any]:
        """
        Force extraction of game context, bypassing cache.
        
        Returns:
            Dictionary with extraction results and status
        """
        if not self.extractor_service:
            return {
                "success": False,
                "error": "Extraction service not available",
                "message": "Enable extracted context mode to use this feature"
            }
        
        try:
            manual_data = self._load_manual_data()
            if not manual_data:
                return {
                    "success": False,
                    "error": "Manual data not available",
                    "message": f"Could not load manual data for year {self.year}"
                }
            
            import asyncio
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create a new loop in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_force_extraction_sync, manual_data)
                        extraction_result = future.result()
                else:
                    # Safe to run directly
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data, force_refresh=True)
                    )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    extraction_result = loop.run_until_complete(
                        self.extractor_service.extract_game_context(manual_data, force_refresh=True)
                    )
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
            
            if extraction_result.success:
                return {
                    "success": True,
                    "extraction_result": extraction_result.extracted_context,
                    "processing_time": extraction_result.processing_time,
                    "validation_score": extraction_result.validation_score,
                    "token_usage": extraction_result.token_usage,
                    "message": f"Successfully extracted context for {self.year}"
                }
            else:
                return {
                    "success": False,
                    "error": extraction_result.error,
                    "processing_time": extraction_result.processing_time,
                    "message": "Extraction failed"
                }
                
        except Exception as e:
            logger.error(f"Error in force extraction: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during extraction"
            }

    def get_extraction_status(self) -> Dict[str, Any]:
        """
        Get status of game context extraction for current year.
        
        Returns:
            Dictionary with extraction status information
        """
        status = {
            "year": self.year,
            "extraction_enabled": self.use_extracted_context,
            "extractor_available": self.extractor_service is not None,
            "manual_available": False,
            "cached_extraction": False,
            "cache_info": {}
        }
        
        # Check manual availability
        manual_data = self._load_manual_data()
        status["manual_available"] = manual_data is not None
        
        if manual_data:
            status["manual_size"] = len(manual_data.get('relevant_sections', ''))
            status["game_name"] = manual_data.get('game_name', 'Unknown')
        
        # Check cache status if extractor available
        if self.extractor_service:
            try:
                status["cache_info"] = self.extractor_service.get_cache_info()
                
                # Check if we have a cached extraction for current manual
                if manual_data:
                    cache_key = self.extractor_service._generate_cache_key(manual_data)
                    cached_result = self.extractor_service._load_cached_extraction(cache_key)
                    status["cached_extraction"] = cached_result is not None
                    if cached_result:
                        status["cache_validation_score"] = cached_result.validation_score
                        
            except Exception as e:
                logger.warning(f"Error getting cache status: {e}")
                status["cache_error"] = str(e)
        
        return status

    def set_extraction_mode(self, use_extracted_context: bool) -> Dict[str, Any]:
        """
        Enable or disable extracted context mode.
        
        Args:
            use_extracted_context: Whether to use extracted context
            
        Returns:
            Dictionary with operation results
        """
        previous_mode = self.use_extracted_context
        
        try:
            if use_extracted_context and not self.extractor_service:
                # Initialize extraction service
                cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "cache", "game_context"
                )
                self.extractor_service = GameContextExtractorService(cache_dir=cache_dir)
                logger.info("Initialized game context extractor service")
            
            self.use_extracted_context = use_extracted_context
            
            return {
                "success": True,
                "previous_mode": "extracted" if previous_mode else "full",
                "current_mode": "extracted" if use_extracted_context else "full",
                "message": f"Switched to {'extracted' if use_extracted_context else 'full'} context mode"
            }
            
        except Exception as e:
            # Revert on error
            self.use_extracted_context = previous_mode
            logger.error(f"Error setting extraction mode: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "current_mode": "extracted" if previous_mode else "full",
                "message": "Failed to change extraction mode"
            }

    def get_teams_data(self) -> Dict[str, Any]:
        """
        Get the teams data from the dataset.
        
        Returns:
            Dictionary of team data
        """
        return self.teams_data

    def get_dataset_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the dataset.
        
        Returns:
            Dataset metadata
        """
        metadata = {
            "year": self.year,
            "event_key": self.event_key,
            "teams_count": len(self.teams_data),
            "dataset_path": self.dataset_path,
            "has_game_context": self.load_game_context() is not None,
            "extraction_mode": "extracted" if self.use_extracted_context else "full",
            "extraction_available": self.extractor_service is not None
        }

        # Analyze available data types
        data_types = {
            "scouting_data": 0,
            "statbotics": 0,
            "ranking": 0,
            "superscouting": 0
        }

        for team_data in self.teams_data.values():
            if isinstance(team_data, dict):
                for data_type in data_types:
                    if data_type in team_data:
                        data_types[data_type] += 1

        metadata["data_availability"] = data_types
        
        return metadata

    def validate_dataset(self) -> Dict[str, Any]:
        """
        Validate the dataset for completeness and consistency.
        
        Returns:
            Validation report
        """
        validation_report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "team_issues": {},
            "summary": {}
        }

        if not self.dataset:
            validation_report["valid"] = False
            validation_report["errors"].append("Dataset is empty or failed to load")
            return validation_report

        # Check required fields
        required_fields = ["teams", "year", "event_key"]
        for field in required_fields:
            if field not in self.dataset:
                validation_report["valid"] = False
                validation_report["errors"].append(f"Missing required field: {field}")

        # Validate teams data
        if "teams" not in self.dataset:
            validation_report["valid"] = False
            validation_report["errors"].append("No teams data found")
        else:
            teams_validation = self._validate_teams_data(self.teams_data)
            validation_report["team_issues"] = teams_validation["issues"]
            validation_report["warnings"].extend(teams_validation["warnings"])
            validation_report["summary"]["teams_with_issues"] = len(teams_validation["issues"])

        # Summary statistics
        validation_report["summary"].update({
            "total_teams": len(self.teams_data),
            "year": self.year,
            "event_key": self.event_key,
            "has_errors": len(validation_report["errors"]) > 0,
            "has_warnings": len(validation_report["warnings"]) > 0
        })

        return validation_report

    def _validate_teams_data(self, teams_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate individual teams data.
        
        Args:
            teams_data: Dictionary of team data
            
        Returns:
            Teams validation report
        """
        issues = {}
        warnings = []

        for team_key, team_data in teams_data.items():
            team_issues = []
            
            if not isinstance(team_data, dict):
                team_issues.append("Team data is not a dictionary")
                continue

            # Check required team fields
            if "team_number" not in team_data:
                team_issues.append("Missing team_number")
            elif not isinstance(team_data["team_number"], int):
                team_issues.append("team_number is not an integer")

            if "nickname" not in team_data:
                team_issues.append("Missing nickname")

            # Validate scouting data if present
            if "scouting_data" in team_data:
                if not isinstance(team_data["scouting_data"], list):
                    team_issues.append("scouting_data is not a list")
                elif len(team_data["scouting_data"]) == 0:
                    warnings.append(f"Team {team_data.get('team_number', team_key)} has no scouting data")

            # Validate statbotics data if present
            if "statbotics" in team_data:
                if not isinstance(team_data["statbotics"], dict):
                    team_issues.append("statbotics data is not a dictionary")

            if team_issues:
                issues[str(team_data.get("team_number", team_key))] = team_issues

        return {"issues": issues, "warnings": warnings}

    def filter_teams_by_criteria(
        self,
        exclude_teams: Optional[List[int]] = None,
        min_matches: int = 0,
        require_statbotics: bool = False,
        require_scouting_data: bool = False
    ) -> Dict[str, Any]:
        """
        Filter teams based on specified criteria.
        
        Args:
            exclude_teams: List of team numbers to exclude
            min_matches: Minimum number of matches required
            require_statbotics: Whether to require Statbotics data
            require_scouting_data: Whether to require scouting data
            
        Returns:
            Filtered teams data
        """
        filtered_teams = {}
        exclude_set = set(exclude_teams or [])

        for team_key, team_data in self.teams_data.items():
            if not isinstance(team_data, dict):
                continue

            team_number = team_data.get("team_number")
            if team_number in exclude_set:
                continue

            # Check scouting data requirements
            if require_scouting_data:
                scouting_data = team_data.get("scouting_data", [])
                if not isinstance(scouting_data, list) or len(scouting_data) == 0:
                    continue

                if len(scouting_data) < min_matches:
                    continue

            # Check Statbotics requirements
            if require_statbotics:
                if "statbotics" not in team_data or not isinstance(team_data["statbotics"], dict):
                    continue

            filtered_teams[team_key] = team_data

        logger.info(f"Filtered teams: {len(self.teams_data)} -> {len(filtered_teams)}")
        return filtered_teams

    def aggregate_team_metrics(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate metrics for a single team from all available data sources.
        
        Args:
            team_data: Individual team data
            
        Returns:
            Aggregated team metrics
        """
        aggregated = {
            "team_number": team_data.get("team_number"),
            "nickname": team_data.get("nickname", f"Team {team_data.get('team_number', 'Unknown')}"),
            "metrics": {},
            "data_sources": []
        }

        # Aggregate scouting data
        if "scouting_data" in team_data and isinstance(team_data["scouting_data"], list):
            scouting_metrics = self._aggregate_scouting_metrics(team_data["scouting_data"])
            aggregated["metrics"].update(scouting_metrics)
            aggregated["data_sources"].append("scouting")
            aggregated["match_count"] = len(team_data["scouting_data"])

        # Add Statbotics data (check both 'statbotics' and 'statbotics_info' for compatibility)
        statbotics_data = team_data.get("statbotics") or team_data.get("statbotics_info", {})
        if statbotics_data and isinstance(statbotics_data, dict):
            for metric, value in statbotics_data.items():
                if isinstance(value, (int, float)):
                    aggregated["metrics"][f"statbotics_{metric}"] = value
            aggregated["data_sources"].append("statbotics")

        # Add ranking data (check both 'ranking' and 'ranking_info' for compatibility)
        ranking_data = team_data.get("ranking") or team_data.get("ranking_info", {})
        if ranking_data and isinstance(ranking_data, dict):
            aggregated["rank"] = ranking_data.get("rank")
            aggregated["record"] = {
                "wins": ranking_data.get("wins", 0),
                "losses": ranking_data.get("losses", 0),
                "ties": ranking_data.get("ties", 0)
            }
            
            # Calculate win percentage
            total_matches = aggregated["record"]["wins"] + aggregated["record"]["losses"] + aggregated["record"]["ties"]
            if total_matches > 0:
                aggregated["metrics"]["win_percentage"] = aggregated["record"]["wins"] / total_matches
            
            aggregated["data_sources"].append("ranking")

        # Add superscouting notes (limited for token efficiency)
        if "superscouting" in team_data and isinstance(team_data["superscouting"], list):
            if team_data["superscouting"]:
                aggregated["superscouting_notes"] = [team_data["superscouting"][0]]
                aggregated["data_sources"].append("superscouting")

        return aggregated

    def _aggregate_scouting_metrics(self, scouting_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate average metrics from scouting data.
        
        Args:
            scouting_data: List of match scouting data
            
        Returns:
            Dictionary of averaged metrics
        """
        metrics_sum = {}
        metrics_count = {}

        # Accumulate metrics from all matches
        for match_data in scouting_data:
            if not isinstance(match_data, dict):
                continue

            for key, value in match_data.items():
                # Skip non-numeric fields
                if key in ["team_number", "match_number", "alliance_color", "notes", "timestamp"]:
                    continue

                if isinstance(value, (int, float)):
                    if key not in metrics_sum:
                        metrics_sum[key] = 0
                        metrics_count[key] = 0
                    metrics_sum[key] += value
                    metrics_count[key] += 1

        # Calculate averages
        averaged_metrics = {}
        for metric in metrics_sum:
            if metrics_count[metric] > 0:
                averaged_metrics[metric] = round(metrics_sum[metric] / metrics_count[metric], 2)

        return averaged_metrics

    def get_teams_for_analysis(
        self,
        exclude_teams: Optional[List[int]] = None,
        team_numbers: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get teams prepared for analysis with all aggregated data.
        
        Args:
            exclude_teams: List of team numbers to exclude
            team_numbers: Specific team numbers to include (if provided, only these teams)
            
        Returns:
            List of teams ready for analysis
        """
        # Filter teams based on criteria
        filtered_teams = self.filter_teams_by_criteria(exclude_teams=exclude_teams)

        # If specific team numbers provided, filter to only those
        if team_numbers:
            team_numbers_set = set(team_numbers)
            filtered_teams = {
                key: data for key, data in filtered_teams.items()
                if data.get("team_number") in team_numbers_set
            }

        # Aggregate metrics for each team
        teams_for_analysis = []
        for team_data in filtered_teams.values():
            aggregated_team = self.aggregate_team_metrics(team_data)
            teams_for_analysis.append(aggregated_team)

        # Sort by team number for consistency
        teams_for_analysis.sort(key=lambda x: x.get("team_number", 0))

        logger.info(f"Prepared {len(teams_for_analysis)} teams for analysis")
        return teams_for_analysis

    def get_data_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the available data.
        
        Returns:
            Dictionary with data statistics
        """
        stats = {
            "total_teams": len(self.teams_data),
            "teams_with_scouting": 0,
            "teams_with_statbotics": 0,
            "teams_with_ranking": 0,
            "teams_with_superscouting": 0,
            "total_matches": 0,
            "average_matches_per_team": 0.0,
            "metrics_available": set()
        }

        total_matches = 0
        teams_with_matches = 0

        for team_data in self.teams_data.values():
            if not isinstance(team_data, dict):
                continue

            # Count data source availability
            if "scouting_data" in team_data and isinstance(team_data["scouting_data"], list):
                stats["teams_with_scouting"] += 1
                match_count = len(team_data["scouting_data"])
                total_matches += match_count
                if match_count > 0:
                    teams_with_matches += 1

                # Collect available metrics
                for match in team_data["scouting_data"]:
                    if isinstance(match, dict):
                        for key in match.keys():
                            if key not in ["team_number", "match_number", "alliance_color", "notes"]:
                                stats["metrics_available"].add(key)

            if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
                stats["teams_with_statbotics"] += 1
                for key in team_data["statbotics"].keys():
                    stats["metrics_available"].add(f"statbotics_{key}")

            if "ranking" in team_data and isinstance(team_data["ranking"], dict):
                stats["teams_with_ranking"] += 1

            if "superscouting" in team_data and isinstance(team_data["superscouting"], list):
                if team_data["superscouting"]:
                    stats["teams_with_superscouting"] += 1

        stats["total_matches"] = total_matches
        stats["average_matches_per_team"] = (
            total_matches / teams_with_matches if teams_with_matches > 0 else 0.0
        )
        stats["metrics_available"] = list(stats["metrics_available"])

        return stats

    def refresh_dataset(self) -> bool:
        """
        Reload the dataset from file.
        
        Returns:
            True if reload was successful
        """
        try:
            new_dataset = self._load_dataset()
            if new_dataset:
                self.dataset = new_dataset
                self.teams_data = self.dataset.get("teams", {})
                self.year = self.dataset.get("year", 2025)
                self.event_key = self.dataset.get("event_key", f"{self.year}arc")
                logger.info("Dataset refreshed successfully")
                return True
            else:
                logger.error("Failed to refresh dataset")
                return False
        except Exception as e:
            logger.error(f"Error refreshing dataset: {e}")
            return False