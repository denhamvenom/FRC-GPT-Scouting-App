"""
Statistical Validator

Detects statistical outliers using Z-score and IQR methods.
Performs global outlier detection across all teams.
"""

from typing import Dict, List, Tuple, Any
import numpy as np

from ..models import ValidationIssue, IssueType, IssueSeverity, DetectionMethod, OutlierDetails
from ..exceptions import InsufficientDataError


class StatisticalValidator:
    """Validates data using statistical methods to detect outliers."""
    
    def __init__(self, z_score_threshold: float = 3.0):
        """
        Initialize the statistical validator.
        
        Args:
            z_score_threshold: Threshold for Z-score outlier detection (default: 3.0)
        """
        self.z_score_threshold = z_score_threshold
    
    def validate(self, dataset: Dict) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Perform statistical validation on the dataset.
        
        Args:
            dataset: The unified dataset to validate
            
        Returns:
            Tuple of (issues list, metadata dict)
        """
        issues = []
        teams_data = dataset.get("teams", {})
        
        # Collect all numeric data for analysis
        numeric_data_by_metric = self._collect_numeric_data(teams_data)
        
        # Perform outlier detection for each metric
        outlier_count = 0
        metrics_analyzed = 0
        
        for metric, all_values in numeric_data_by_metric.items():
            if len(all_values) < 5:  # Skip metrics with too few data points
                continue
            
            metrics_analyzed += 1
            
            # Extract just the values for statistical calculations
            values_only = [v["value"] for v in all_values]
            
            # Z-score detection
            z_score_outliers = self._detect_z_score_outliers(all_values, values_only)
            for outlier in z_score_outliers:
                issues.append(self._create_outlier_issue(outlier, metric, DetectionMethod.Z_SCORE))
                outlier_count += 1
            
            # IQR detection
            iqr_outliers = self._detect_iqr_outliers(all_values, values_only)
            for outlier in iqr_outliers:
                # Only add if not already detected by z-score
                if not self._is_duplicate_outlier(outlier, z_score_outliers):
                    issues.append(self._create_outlier_issue(outlier, metric, DetectionMethod.IQR))
                    outlier_count += 1
        
        # Build metadata
        metadata = {
            "metrics_analyzed": metrics_analyzed,
            "total_outliers_detected": outlier_count,
            "z_score_threshold": self.z_score_threshold,
            "detection_methods": ["z_score", "iqr"]
        }
        
        return issues, metadata
    
    def _collect_numeric_data(self, teams_data: Dict) -> Dict[str, List[Dict]]:
        """Collect all numeric data organized by metric."""
        numeric_data = {}
        
        for team_number_str, team_data in teams_data.items():
            try:
                team_number = int(team_number_str)
            except ValueError:
                continue
            
            for match in team_data.get("scouting_data", []):
                match_number = self._get_match_number(match)
                if match_number is None:
                    continue
                
                # Collect numeric metrics
                for key, value in match.items():
                    if self._is_numeric_metric(key, value):
                        if key not in numeric_data:
                            numeric_data[key] = []
                        
                        numeric_data[key].append({
                            "team_number": team_number,
                            "match_number": match_number,
                            "value": float(value)
                        })
        
        return numeric_data
    
    def _detect_z_score_outliers(self, data_points: List[Dict], values: List[float]) -> List[Dict]:
        """Detect outliers using Z-score method."""
        outliers = []
        
        # Calculate Z-scores
        z_scores = self._calculate_z_scores(values)
        
        # Find outliers
        for i, (data_point, z_score) in enumerate(zip(data_points, z_scores)):
            if abs(z_score) > self.z_score_threshold:
                outliers.append({
                    **data_point,
                    "z_score": z_score,
                    "threshold": self.z_score_threshold
                })
        
        return outliers
    
    def _detect_iqr_outliers(self, data_points: List[Dict], values: List[float]) -> List[Dict]:
        """Detect outliers using IQR method."""
        outliers = []
        
        # Calculate IQR bounds
        lower_bound, upper_bound = self._calculate_iqr_bounds(values)
        
        # Find outliers
        for data_point in data_points:
            value = data_point["value"]
            if value < lower_bound or value > upper_bound:
                outliers.append({
                    **data_point,
                    "bounds": [lower_bound, upper_bound]
                })
        
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
    
    def _calculate_iqr_bounds(self, values: List[float]) -> Tuple[float, float]:
        """Calculate the IQR bounds for outlier detection."""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return lower_bound, upper_bound
    
    def _create_outlier_issue(self, outlier_data: Dict, metric: str, method: DetectionMethod) -> ValidationIssue:
        """Create a ValidationIssue for an outlier."""
        details = {
            "metric": metric,
            "value": outlier_data["value"],
            "detection_method": method.value
        }
        
        # Add method-specific details
        if "z_score" in outlier_data:
            details["z_score"] = outlier_data["z_score"]
            details["z_score_threshold"] = outlier_data["threshold"]
            # Determine severity based on z-score
            severity = IssueSeverity.ERROR if abs(outlier_data["z_score"]) > 4 else IssueSeverity.WARNING
        elif "bounds" in outlier_data:
            details["bounds"] = outlier_data["bounds"]
            severity = IssueSeverity.WARNING
        else:
            severity = IssueSeverity.WARNING
        
        return ValidationIssue(
            team_number=outlier_data["team_number"],
            match_number=outlier_data["match_number"],
            issue_type=IssueType.STATISTICAL_OUTLIER,
            severity=severity,
            metric=metric,
            value=outlier_data["value"],
            detection_method=method,
            details=details
        )
    
    def _is_duplicate_outlier(self, outlier: Dict, existing_outliers: List[Dict]) -> bool:
        """Check if an outlier has already been detected."""
        for existing in existing_outliers:
            if (outlier["team_number"] == existing["team_number"] and
                outlier["match_number"] == existing["match_number"]):
                return True
        return False
    
    def _get_match_number(self, match: Dict) -> int:
        """Extract match number from match data."""
        # Try qual_number first, then match_number
        for field in ["qual_number", "match_number"]:
            if field in match:
                try:
                    return int(match[field])
                except (ValueError, TypeError):
                    pass
        return None
    
    def _is_numeric_metric(self, key: str, value: Any) -> bool:
        """Check if a metric should be included in statistical analysis."""
        # Skip non-numeric values
        if not isinstance(value, (int, float)):
            return False
        
        # Skip identifier fields
        skip_fields = ["qual_number", "match_number", "team_number", "alliance_station", "match_id"]
        if key in skip_fields:
            return False
        
        return True