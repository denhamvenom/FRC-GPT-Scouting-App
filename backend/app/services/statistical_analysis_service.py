# backend/app/services/statistical_analysis_service.py

import json
import logging
import statistics
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime

from app.types.performance_signature_types import (
    EventBaseline, EventPerformanceBaselines, MetricStatistics,
    calculate_metric_statistics, calculate_percentiles
)

logger = logging.getLogger("statistical_analysis_service")


class StatisticalAnalysisService:
    """
    Service for calculating event-wide statistical baselines and team percentiles.
    
    This service provides game-agnostic statistical analysis by:
    1. Auto-detecting metrics from unified dataset structure
    2. Calculating event-wide baselines for percentile rankings
    3. Supporting any metric type (numerical data)
    4. Maintaining complete year/event/game agnosticism
    
    Thread Safety: Thread-safe for read operations, not thread-safe for writes
    Dependencies: Unified dataset with teams and scouting data
    """
    
    def __init__(self, unified_dataset: Dict[str, Any]):
        """
        Initialize statistical analysis service with validated dataset.
        
        Args:
            unified_dataset: Complete unified dataset with teams and scouting data
            
        Raises:
            ValueError: If dataset structure is invalid
        """
        self._validate_dataset_structure(unified_dataset)
        self.dataset = unified_dataset
        self.event_key = unified_dataset.get("event_key", "unknown")
        self.year = unified_dataset.get("year", datetime.now().year)
        self.teams_data = unified_dataset.get("teams", {})
        
        logger.info(f"Initialized statistical analysis for {self.event_key} ({len(self.teams_data)} teams)")
    
    def _validate_dataset_structure(self, dataset: Dict[str, Any]) -> None:
        """Validate that dataset has required structure for analysis."""
        if not isinstance(dataset, dict):
            raise ValueError("Dataset must be a dictionary")
        
        if "teams" not in dataset:
            raise ValueError("Dataset must contain 'teams' section")
        
        teams = dataset["teams"]
        if not isinstance(teams, dict):
            raise ValueError("Teams section must be a dictionary")
        
        # Verify at least one team has scouting data
        has_scouting_data = False
        for team_data in teams.values():
            if isinstance(team_data, dict) and "scouting_data" in team_data:
                scouting_data = team_data["scouting_data"]
                if isinstance(scouting_data, list) and len(scouting_data) > 0:
                    has_scouting_data = True
                    break
        
        if not has_scouting_data:
            raise ValueError("No teams found with valid scouting data")
    
    def auto_detect_metrics(self) -> Set[str]:
        """
        Auto-detect all numerical metrics from scouting data structure.
        
        This method is completely game-agnostic and works by:
        1. Examining all scouting records across all teams
        2. Identifying fields with numerical values
        3. Excluding non-metric fields (timestamps, names, etc.)
        
        Returns:
            Set of metric names found in the data
        """
        detected_metrics = set()
        excluded_fields = {
            "match_number", "qual_number", "team_number", "timestamp", 
            "scout_name", "alliance", "alliance_color", "scout_comments",
            "strategy_field", "driver_skill_rating"  # Qualitative fields
        }
        
        logger.info("Auto-detecting metrics from scouting data...")
        
        sample_count = 0
        for team_number, team_data in self.teams_data.items():
            if not isinstance(team_data, dict) or "scouting_data" not in team_data:
                continue
            
            scouting_data = team_data["scouting_data"]
            if not isinstance(scouting_data, list):
                continue
            
            for match in scouting_data:
                if not isinstance(match, dict):
                    continue
                
                sample_count += 1
                for field_name, value in match.items():
                    # Skip excluded fields
                    if field_name.lower() in excluded_fields:
                        continue
                    
                    # Check if field contains numerical data
                    if self._is_numerical_metric(value):
                        detected_metrics.add(field_name)
                
                # Sample first 50 matches for efficiency
                if sample_count >= 50:
                    break
            
            if sample_count >= 50:
                break
        
        logger.info(f"Detected {len(detected_metrics)} numerical metrics: {sorted(detected_metrics)}")
        return detected_metrics
    
    def _is_numerical_metric(self, value: Any) -> bool:
        """Check if a value represents a numerical metric."""
        if isinstance(value, (int, float)):
            return True
        
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        
        return False
    
    def extract_metric_values(self, metric_name: str) -> Dict[str, List[float]]:
        """
        Extract all values for a specific metric across all teams.
        
        Args:
            metric_name: Name of the metric to extract
            
        Returns:
            Dictionary mapping team_number -> list of metric values
        """
        metric_values = {}
        
        for team_number, team_data in self.teams_data.items():
            if not isinstance(team_data, dict) or "scouting_data" not in team_data:
                continue
            
            scouting_data = team_data["scouting_data"]
            if not isinstance(scouting_data, list):
                continue
            
            team_values = []
            for match in scouting_data:
                if not isinstance(match, dict) or metric_name not in match:
                    continue
                
                value = match[metric_name]
                try:
                    numeric_value = float(value)
                    team_values.append(numeric_value)
                except (ValueError, TypeError):
                    continue
            
            if team_values:  # Only include teams with actual data
                metric_values[team_number] = team_values
        
        return metric_values
    
    def calculate_event_baseline(self, metric_name: str) -> EventBaseline:
        """
        Calculate event-wide statistical baseline for a metric.
        
        Args:
            metric_name: Name of the metric to analyze
            
        Returns:
            EventBaseline with comprehensive statistics
            
        Raises:
            ValueError: If metric has insufficient data
        """
        metric_values = self.extract_metric_values(metric_name)
        
        if not metric_values:
            raise ValueError(f"No data found for metric: {metric_name}")
        
        # Flatten all values for event-wide statistics
        all_values = []
        for team_values in metric_values.values():
            all_values.extend(team_values)
        
        if len(all_values) < 5:  # Minimum data requirement
            raise ValueError(f"Insufficient data for {metric_name}: {len(all_values)} values")
        
        # Calculate comprehensive statistics
        statistics = calculate_metric_statistics(all_values)
        percentiles = calculate_percentiles(all_values)
        
        # Count top performers (above 90th percentile)
        percentile_90 = percentiles.get("90th", 0)
        top_performers = sum(1 for values in metric_values.values() 
                           if max(values) > percentile_90)
        
        baseline = EventBaseline(
            metric_name=metric_name,
            statistics=statistics,
            percentiles=percentiles,
            field_size=len(metric_values),  # Number of teams with data
            top_performers=top_performers
        )
        
        logger.info(f"Calculated baseline for {metric_name}: "
                   f"{baseline.field_size} teams, "
                   f"mean={statistics.mean:.2f}, "
                   f"90th percentile={percentiles.get('90th', 0):.2f}")
        
        return baseline
    
    def calculate_all_baselines(self, metrics: Optional[Set[str]] = None) -> EventPerformanceBaselines:
        """
        Calculate baselines for all metrics or specified subset.
        
        Args:
            metrics: Optional set of specific metrics to analyze.
                    If None, auto-detects all available metrics.
                    
        Returns:
            EventPerformanceBaselines with all calculated baselines
        """
        if metrics is None:
            metrics = self.auto_detect_metrics()
        
        logger.info(f"Calculating baselines for {len(metrics)} metrics...")
        
        baselines = {}
        failed_metrics = []
        
        for metric_name in metrics:
            try:
                baseline = self.calculate_event_baseline(metric_name)
                baselines[metric_name] = baseline
            except ValueError as e:
                logger.warning(f"Failed to calculate baseline for {metric_name}: {e}")
                failed_metrics.append(metric_name)
        
        if failed_metrics:
            logger.info(f"Skipped {len(failed_metrics)} metrics due to insufficient data: {failed_metrics}")
        
        # Calculate event metadata
        total_teams = len(self.teams_data)
        total_matches = sum(
            len(team.get("scouting_data", []))
            for team in self.teams_data.values()
            if isinstance(team, dict)
        )
        avg_matches_per_team = total_matches / total_teams if total_teams > 0 else 0
        
        # Determine event level (heuristic based on team count)
        if total_teams >= 60:
            event_level = "championship"
        elif total_teams >= 40:
            event_level = "regional"
        else:
            event_level = "district"
        
        competitive_context = {
            "total_teams": total_teams,
            "metrics_calculated": len(baselines),
            "avg_matches_per_team": round(avg_matches_per_team, 1),
            "event_level": event_level,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        event_baselines = EventPerformanceBaselines(
            event_key=self.event_key,
            year=self.year,
            baselines=baselines,
            total_teams=total_teams,
            avg_matches_per_team=avg_matches_per_team,
            event_level=event_level,
            competitive_context=competitive_context
        )
        
        logger.info(f"Completed baseline calculation: {len(baselines)} metrics, "
                   f"{total_teams} teams, {event_level} level event")
        
        return event_baselines
    
    def get_team_percentile(self, team_number: str, metric_name: str, baseline: EventBaseline) -> float:
        """
        Calculate a team's percentile rank for a specific metric.
        
        Args:
            team_number: Team to analyze
            metric_name: Metric to evaluate
            baseline: Event baseline for the metric
            
        Returns:
            Percentile rank (0-100)
            
        Raises:
            ValueError: If team or metric data not found
        """
        if team_number not in self.teams_data:
            raise ValueError(f"Team {team_number} not found in dataset")
        
        team_data = self.teams_data[team_number]
        if not isinstance(team_data, dict) or "scouting_data" not in team_data:
            raise ValueError(f"No scouting data for team {team_number}")
        
        # Extract team's values for this metric
        metric_values = self.extract_metric_values(metric_name)
        if team_number not in metric_values:
            raise ValueError(f"No {metric_name} data for team {team_number}")
        
        team_values = metric_values[team_number]
        team_average = statistics.mean(team_values)
        
        # Use baseline to calculate percentile rank
        percentile_rank = baseline.get_percentile_rank(team_average)
        
        return percentile_rank
    
    def export_baselines(self, filepath: str, baselines: EventPerformanceBaselines) -> None:
        """
        Export calculated baselines to JSON file.
        
        Args:
            filepath: Path to save baselines
            baselines: Calculated event baselines
        """
        # Convert to serializable format
        export_data = {
            "event_key": baselines.event_key,
            "year": baselines.year,
            "total_teams": baselines.total_teams,
            "avg_matches_per_team": baselines.avg_matches_per_team,
            "event_level": baselines.event_level,
            "competitive_context": baselines.competitive_context,
            "baselines": {}
        }
        
        for metric_name, baseline in baselines.baselines.items():
            export_data["baselines"][metric_name] = {
                "metric_name": baseline.metric_name,
                "statistics": {
                    "mean": baseline.statistics.mean,
                    "std": baseline.statistics.std,
                    "median": baseline.statistics.median,
                    "min_value": baseline.statistics.min_value,
                    "max_value": baseline.statistics.max_value,
                    "sample_size": baseline.statistics.sample_size,
                    "coefficient_of_variation": baseline.statistics.coefficient_of_variation
                },
                "percentiles": baseline.percentiles,
                "field_size": baseline.field_size,
                "top_performers": baseline.top_performers
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported baselines to {filepath}")