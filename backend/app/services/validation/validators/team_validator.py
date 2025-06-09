"""
Team Validator

Performs team-specific validation by comparing each team's performance
against their own historical data to detect match-specific anomalies.
"""

from typing import Dict, List, Tuple, Any
import numpy as np

from ..models import ValidationIssue, IssueType, IssueSeverity, DetectionMethod


class TeamValidator:
    """Validates team-specific performance patterns."""
    
    def __init__(self, z_score_threshold: float = 3.0):
        """
        Initialize the team validator.
        
        Args:
            z_score_threshold: Threshold for team-specific outlier detection
        """
        self.z_score_threshold = z_score_threshold
    
    def validate(self, dataset: Dict) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Perform team-specific validation.
        
        Args:
            dataset: The unified dataset to validate
            
        Returns:
            Tuple of (issues list, metadata dict)
        """
        issues = []
        teams_data = dataset.get("teams", {})
        
        teams_analyzed = 0
        total_team_outliers = 0
        
        # Analyze each team individually
        for team_number_str, team_data in teams_data.items():
            try:
                team_number = int(team_number_str)
            except ValueError:
                continue
            
            # Get team's scouting data
            scouting_data = team_data.get("scouting_data", [])
            if len(scouting_data) < 3:  # Need at least 3 matches for meaningful analysis
                continue
            
            teams_analyzed += 1
            
            # Collect team's numeric data by metric
            team_metrics = self._collect_team_metrics(scouting_data)
            
            # Analyze each metric for this team
            for metric, match_values in team_metrics.items():
                if len(match_values) < 3:
                    continue
                
                # Detect outliers in team's own performance
                outliers = self._detect_team_outliers(match_values, team_number, metric)
                for outlier in outliers:
                    issues.append(outlier)
                    total_team_outliers += 1
        
        # Build metadata
        metadata = {
            "teams_analyzed": teams_analyzed,
            "total_team_outliers": total_team_outliers,
            "min_matches_required": 3,
            "z_score_threshold": self.z_score_threshold
        }
        
        return issues, metadata
    
    def _collect_team_metrics(self, scouting_data: List[Dict]) -> Dict[str, List[Tuple[int, float]]]:
        """Collect a team's metrics organized by metric name."""
        team_metrics = {}
        
        for match in scouting_data:
            match_number = self._get_match_number(match)
            if match_number is None:
                continue
            
            for key, value in match.items():
                if self._is_numeric_metric(key, value):
                    if key not in team_metrics:
                        team_metrics[key] = []
                    team_metrics[key].append((match_number, float(value)))
        
        return team_metrics
    
    def _detect_team_outliers(self, match_values: List[Tuple[int, float]], 
                            team_number: int, metric: str) -> List[ValidationIssue]:
        """Detect outliers in a team's performance for a specific metric."""
        outliers = []
        
        # Extract just the values
        values = [v for _, v in match_values]
        
        # Calculate z-scores for team's performance
        z_scores = self._calculate_z_scores(values)
        
        # Find outliers
        for (match_number, value), z_score in zip(match_values, z_scores):
            if abs(z_score) > self.z_score_threshold:
                # Determine severity based on deviation
                if abs(z_score) > 4:
                    severity = IssueSeverity.ERROR
                elif abs(z_score) > 3.5:
                    severity = IssueSeverity.WARNING
                else:
                    severity = IssueSeverity.INFO
                
                issue = ValidationIssue(
                    team_number=team_number,
                    match_number=match_number,
                    issue_type=IssueType.TEAM_OUTLIER,
                    severity=severity,
                    metric=metric,
                    value=value,
                    detection_method=DetectionMethod.TEAM_SPECIFIC,
                    details={
                        "metric": metric,
                        "value": value,
                        "team_z_score": z_score,
                        "team_mean": np.mean(values),
                        "team_std": np.std(values),
                        "matches_analyzed": len(values),
                        "detection_method": "team_specific",
                        "description": f"Value deviates {abs(z_score):.2f} standard deviations from team's average"
                    }
                )
                outliers.append(issue)
        
        return outliers
    
    def _calculate_z_scores(self, values: List[float]) -> List[float]:
        """Calculate Z-scores for a list of values."""
        if len(values) < 2:
            return [0.0] * len(values)
        
        values_array = np.array(values, dtype=float)
        mean = np.mean(values_array)
        std = np.std(values_array)
        
        if std == 0:
            return [0.0] * len(values)
        
        return list((values_array - mean) / std)
    
    def _get_match_number(self, match: Dict) -> int:
        """Extract match number from match data."""
        for field in ["qual_number", "match_number"]:
            if field in match:
                try:
                    return int(match[field])
                except (ValueError, TypeError):
                    pass
        return None
    
    def _is_numeric_metric(self, key: str, value: Any) -> bool:
        """Check if a metric should be included in analysis."""
        # Skip non-numeric values
        if not isinstance(value, (int, float)):
            return False
        
        # Skip identifier fields
        skip_fields = ["qual_number", "match_number", "team_number", "alliance_station", "match_id"]
        if key in skip_fields:
            return False
        
        return True