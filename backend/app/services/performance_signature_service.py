# backend/app/services/performance_signature_service.py

import json
import logging
import os
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from app.types.performance_signature_types import (
    PerformanceSignature, TeamPerformanceProfile, MetricStatistics,
    PerformanceTier, ReliabilityTier, TrendIndicator,
    classify_performance_tier, classify_reliability_tier, analyze_trend,
    calculate_metric_statistics, SIGNATURE_VERSION
)
from app.services.statistical_analysis_service import StatisticalAnalysisService
from app.types.performance_signature_types import EventPerformanceBaselines

logger = logging.getLogger("performance_signature_service")


class PerformanceSignatureService:
    """
    Service for generating performance signatures that replace performance bands.
    
    This service creates game-agnostic performance signatures by:
    1. Using event-wide statistical baselines for percentile calculations
    2. Auto-detecting metrics from unified dataset structure
    3. Generating universal signature format: "value±reliability (context, n=sample, trend)"
    4. Supporting any FRC game without hardcoded metrics/years/events
    
    Thread Safety: Thread-safe for read operations, not thread-safe for cache writes
    Dependencies: StatisticalAnalysisService, unified dataset
    """
    
    def __init__(self, unified_dataset_path: str):
        """
        Initialize performance signature service.
        
        Args:
            unified_dataset_path: Path to unified dataset JSON file
            
        Raises:
            ValueError: If dataset cannot be loaded or is invalid
        """
        self.dataset_path = unified_dataset_path
        self.dataset = self._load_dataset()
        self.event_key = self.dataset.get("event_key", "unknown")
        self.year = self.dataset.get("year", datetime.now().year)
        
        # Initialize statistical analysis service
        self.stats_service = StatisticalAnalysisService(self.dataset)
        
        # Cache for baselines (calculated once per service instance)
        self._event_baselines: Optional[EventPerformanceBaselines] = None
        
        logger.info(f"Initialized performance signature service for {self.event_key} ({self.year})")
    
    def _load_dataset(self) -> Dict[str, Any]:
        """Load and validate unified dataset."""
        if not os.path.exists(self.dataset_path):
            raise ValueError(f"Dataset file not found: {self.dataset_path}")
        
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            if not isinstance(dataset, dict):
                raise ValueError("Dataset must be a JSON object")
            
            logger.info(f"Loaded dataset from {self.dataset_path}")
            return dataset
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in dataset file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading dataset: {e}")
    
    def get_event_baselines(self, refresh: bool = False) -> EventPerformanceBaselines:
        """
        Get or calculate event-wide statistical baselines.
        
        Args:
            refresh: Force recalculation of baselines
            
        Returns:
            EventPerformanceBaselines for the current event
        """
        if self._event_baselines is None or refresh:
            logger.info("Calculating event-wide statistical baselines...")
            self._event_baselines = self.stats_service.calculate_all_baselines()
            logger.info(f"Calculated baselines for {len(self._event_baselines.baselines)} metrics")
        
        return self._event_baselines
    
    def generate_team_signature(
        self, 
        team_number: str, 
        metric_name: str, 
        event_baselines: EventPerformanceBaselines
    ) -> PerformanceSignature:
        """
        Generate performance signature for a team's specific metric.
        
        Args:
            team_number: Team to analyze
            metric_name: Metric to generate signature for
            event_baselines: Event baselines for percentile calculation
            
        Returns:
            PerformanceSignature with complete analysis
            
        Raises:
            ValueError: If team or metric data insufficient
        """
        # Get event baseline for this metric
        baseline = event_baselines.get_baseline(metric_name)
        if baseline is None:
            raise ValueError(f"No baseline available for metric: {metric_name}")
        
        # Extract team's metric values
        metric_values = self.stats_service.extract_metric_values(metric_name)
        if team_number not in metric_values:
            raise ValueError(f"No {metric_name} data for team {team_number}")
        
        team_values = metric_values[team_number]
        if len(team_values) < 2:  # Minimum for meaningful statistics
            raise ValueError(f"Insufficient data for team {team_number} metric {metric_name}: {len(team_values)} values")
        
        # Calculate team statistics
        team_stats = calculate_metric_statistics(team_values)
        
        # Calculate percentile rank
        percentile_rank = baseline.get_percentile_rank(team_stats.mean)
        
        # Analyze trend
        trend = analyze_trend(team_values)
        
        # Classify performance and reliability
        performance_tier = classify_performance_tier(percentile_rank, trend)
        reliability_tier = classify_reliability_tier(team_stats.coefficient_of_variation)
        
        # Generate signature string
        signature_string = PerformanceSignature.create_signature_string(
            team_stats, performance_tier, reliability_tier, trend, percentile_rank
        )
        
        signature = PerformanceSignature(
            metric_name=metric_name,
            team_statistics=team_stats,
            event_baseline=baseline,
            performance_tier=performance_tier,
            reliability_tier=reliability_tier,
            trend_indicator=trend,
            percentile_rank=percentile_rank,
            signature_string=signature_string
        )
        
        logger.debug(f"Generated signature for team {team_number} {metric_name}: {signature_string}")
        return signature
    
    def generate_team_profile(self, team_number: str, metrics: Optional[Set[str]] = None) -> TeamPerformanceProfile:
        """
        Generate complete performance profile for a team.
        
        Args:
            team_number: Team to analyze
            metrics: Optional set of specific metrics. If None, uses all available metrics.
            
        Returns:
            TeamPerformanceProfile with signatures for all metrics
            
        Raises:
            ValueError: If team not found or insufficient data
        """
        if team_number not in self.dataset.get("teams", {}):
            raise ValueError(f"Team {team_number} not found in dataset")
        
        team_data = self.dataset["teams"][team_number]
        nickname = team_data.get("nickname", f"Team {team_number}")
        
        # Get event baselines
        event_baselines = self.get_event_baselines()
        
        # Use specified metrics or auto-detect all
        if metrics is None:
            metrics = set(event_baselines.get_metric_names())
        
        # Generate signatures for each metric
        signatures = {}
        successful_signatures = 0
        failed_metrics = []
        
        for metric_name in metrics:
            try:
                signature = self.generate_team_signature(team_number, metric_name, event_baselines)
                signatures[metric_name] = signature
                successful_signatures += 1
            except ValueError as e:
                logger.debug(f"Skipped {metric_name} for team {team_number}: {e}")
                failed_metrics.append(metric_name)
        
        if successful_signatures == 0:
            raise ValueError(f"No valid signatures generated for team {team_number}")
        
        # Calculate overall percentile (average across all metrics)
        overall_percentile = sum(sig.percentile_rank for sig in signatures.values()) / len(signatures)
        
        # Count matches for this team
        scouting_data = team_data.get("scouting_data", [])
        match_count = len(scouting_data) if isinstance(scouting_data, list) else 0
        
        profile = TeamPerformanceProfile(
            team_number=int(team_number),
            nickname=nickname,
            signatures=signatures,
            match_count=match_count,
            overall_percentile=overall_percentile
        )
        
        logger.info(f"Generated profile for team {team_number}: "
                   f"{successful_signatures} signatures, "
                   f"{overall_percentile:.1f}th percentile overall")
        
        if failed_metrics:
            logger.debug(f"Failed metrics for team {team_number}: {failed_metrics}")
        
        return profile
    
    def generate_all_team_profiles(self, team_numbers: Optional[List[str]] = None) -> Dict[str, TeamPerformanceProfile]:
        """
        Generate performance profiles for all teams or specified subset.
        
        Args:
            team_numbers: Optional list of specific teams. If None, processes all teams.
            
        Returns:
            Dictionary mapping team_number -> TeamPerformanceProfile
        """
        teams_data = self.dataset.get("teams", {})
        
        if team_numbers is None:
            team_numbers = list(teams_data.keys())
        
        logger.info(f"Generating performance profiles for {len(team_numbers)} teams...")
        
        profiles = {}
        successful_profiles = 0
        failed_teams = []
        
        for team_number in team_numbers:
            try:
                profile = self.generate_team_profile(team_number)
                profiles[team_number] = profile
                successful_profiles += 1
            except ValueError as e:
                logger.warning(f"Failed to generate profile for team {team_number}: {e}")
                failed_teams.append(team_number)
        
        logger.info(f"Successfully generated {successful_profiles} team profiles")
        if failed_teams:
            logger.info(f"Failed teams: {failed_teams}")
        
        return profiles
    
    def export_team_profiles(self, profiles: Dict[str, TeamPerformanceProfile], filepath: str) -> None:
        """
        Export team profiles to JSON file.
        
        Args:
            profiles: Team profiles to export
            filepath: Path to save profiles
        """
        export_data = {
            "event_key": self.event_key,
            "year": self.year,
            "signature_version": SIGNATURE_VERSION,
            "generation_timestamp": datetime.now().isoformat(),
            "teams_analyzed": len(profiles),
            "team_profiles": {}
        }
        
        for team_number, profile in profiles.items():
            export_data["team_profiles"][team_number] = {
                "team_number": profile.team_number,
                "nickname": profile.nickname,
                "match_count": profile.match_count,
                "overall_percentile": profile.overall_percentile,
                "strategic_profile": profile.strategic_profile,
                "signatures": {}
            }
            
            for metric_name, signature in profile.signatures.items():
                export_data["team_profiles"][team_number]["signatures"][metric_name] = {
                    "signature_string": signature.signature_string,
                    "performance_tier": signature.performance_tier.value,
                    "reliability_tier": signature.reliability_tier.value,
                    "trend_indicator": signature.trend_indicator.value,
                    "percentile_rank": signature.percentile_rank,
                    "statistics": {
                        "mean": signature.team_statistics.mean,
                        "std": signature.team_statistics.std,
                        "sample_size": signature.team_statistics.sample_size,
                        "coefficient_of_variation": signature.team_statistics.coefficient_of_variation
                    },
                    "strategic_context": signature.strategic_context
                }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(profiles)} team profiles to {filepath}")
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """
        Get summary of available metrics and their characteristics.
        
        Returns:
            Dictionary with metric analysis summary
        """
        event_baselines = self.get_event_baselines()
        
        summary = {
            "event_info": {
                "event_key": self.event_key,
                "year": self.year,
                "total_teams": event_baselines.total_teams,
                "avg_matches_per_team": event_baselines.avg_matches_per_team,
                "event_level": event_baselines.event_level
            },
            "metrics_analyzed": len(event_baselines.baselines),
            "metric_details": {}
        }
        
        for metric_name, baseline in event_baselines.baselines.items():
            summary["metric_details"][metric_name] = {
                "teams_with_data": baseline.field_size,
                "mean": round(baseline.statistics.mean, 2),
                "std": round(baseline.statistics.std, 2),
                "range": [baseline.statistics.min_value, baseline.statistics.max_value],
                "percentiles": {k: round(v, 2) for k, v in baseline.percentiles.items()},
                "top_performers": baseline.top_performers
            }
        
        return summary