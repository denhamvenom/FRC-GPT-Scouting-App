# backend/app/services/data_aggregation_service.py

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("data_aggregation_service")


class DataAggregationService:
    """
    Service for collecting, transforming, and validating data from multiple sources.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    """

    def __init__(self, unified_dataset_path: str):
        """
        Initialize the data aggregation service.
        
        Args:
            unified_dataset_path: Path to the unified dataset JSON file
        """
        self.dataset_path = unified_dataset_path
        self.dataset = self._load_dataset()
        self.teams_data = self.dataset.get("teams", {})
        self.year = self.dataset.get("year", 2025)
        self.event_key = self.dataset.get("event_key", f"{self.year}arc")

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
        Load the game manual text for context.
        
        Returns:
            Game context text or None if not available
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            manual_text_path = os.path.join(data_dir, f"manual_text_{self.year}.json")

            if os.path.exists(manual_text_path):
                with open(manual_text_path, "r", encoding="utf-8") as f:
                    manual_data = json.load(f)
                    # Combine game name and relevant sections
                    game_context = f"Game: {manual_data.get('game_name', '')}\n\n{manual_data.get('relevant_sections', '')}"
                    logger.info(f"Loaded game context for {self.year}")
                    return game_context
            else:
                logger.warning(f"Game manual not found: {manual_text_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading game context: {e}")
            return None

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
            "has_game_context": self.load_game_context() is not None
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

        # Add Statbotics data
        if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
            for metric, value in team_data["statbotics"].items():
                if isinstance(value, (int, float)):
                    aggregated["metrics"][f"statbotics_{metric}"] = value
            aggregated["data_sources"].append("statbotics")

        # Add ranking data
        if "ranking" in team_data and isinstance(team_data["ranking"], dict):
            ranking = team_data["ranking"]
            aggregated["rank"] = ranking.get("rank")
            aggregated["record"] = {
                "wins": ranking.get("wins", 0),
                "losses": ranking.get("losses", 0),
                "ties": ranking.get("ties", 0)
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