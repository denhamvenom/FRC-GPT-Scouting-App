"""
Outlier Corrector

Handles correction of statistical outliers with various strategies
and maintains audit trail of all corrections.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime

from ..models import CorrectionSuggestion, CorrectionMethod, AuditEntry
from ..exceptions import InvalidCorrectionError, DataNotFoundError


class OutlierCorrector:
    """Corrects outliers using various strategies."""
    
    def suggest_corrections(self, dataset: Dict, team_number: int, 
                          match_number: int, outlier_metrics: List[str]) -> List[CorrectionSuggestion]:
        """
        Suggest corrections for outliers based on various strategies.
        
        Args:
            dataset: The unified dataset
            team_number: Team number with outliers
            match_number: Match number with outliers
            outlier_metrics: List of metrics that are outliers
            
        Returns:
            List of correction suggestions
        """
        suggestions = []
        teams_data = dataset.get("teams", {})
        
        if str(team_number) not in teams_data:
            raise DataNotFoundError("Team", str(team_number))
        
        team_data = teams_data[str(team_number)]
        
        # Find the match data
        match_data = self._find_match_data(team_data, match_number)
        if not match_data:
            raise DataNotFoundError("Match", f"{team_number}-{match_number}")
        
        # Calculate team averages for each metric
        team_averages = self._calculate_team_averages(team_data, outlier_metrics)
        
        # Generate suggestions for each outlier metric
        for metric in outlier_metrics:
            if metric not in match_data:
                continue
            
            current_value = match_data[metric]
            metric_suggestions = []
            
            # Team average suggestion
            if metric in team_averages:
                avg_value = team_averages[metric]
                metric_suggestions.append(CorrectionSuggestion(
                    metric=metric,
                    current_value=current_value,
                    suggested_value=self._round_appropriately(avg_value, current_value),
                    method=CorrectionMethod.TEAM_AVERAGE,
                    confidence=0.8,
                    reason=f"Based on team's average performance ({avg_value:.2f})"
                ))
            
            # Statistical bounds suggestion
            bounds_suggestion = self._suggest_from_bounds(dataset, metric, current_value)
            if bounds_suggestion:
                metric_suggestions.append(bounds_suggestion)
            
            # Zero suggestion for certain metrics
            if self._should_suggest_zero(metric, current_value):
                metric_suggestions.append(CorrectionSuggestion(
                    metric=metric,
                    current_value=current_value,
                    suggested_value=0,
                    method=CorrectionMethod.ZERO,
                    confidence=0.5,
                    reason="Common correction for false positive recordings"
                ))
            
            suggestions.extend(metric_suggestions)
        
        return suggestions
    
    def apply_correction(self, dataset: Dict, team_number: int, match_number: int,
                        corrections: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
        """
        Apply corrections to the dataset with audit trail.
        
        Args:
            dataset: The unified dataset
            team_number: Team number
            match_number: Match number
            corrections: Dict of metric -> corrected value
            reason: Reason for corrections
            
        Returns:
            Dict with correction results
        """
        teams_data = dataset.get("teams", {})
        
        if str(team_number) not in teams_data:
            raise DataNotFoundError("Team", str(team_number))
        
        team_data = teams_data[str(team_number)]
        scouting_data = team_data.get("scouting_data", [])
        
        # Find the match
        match_idx = self._find_match_index(scouting_data, match_number)
        if match_idx is None:
            raise DataNotFoundError("Match", f"{team_number}-{match_number}")
        
        # Apply corrections and track audit
        audit_entries = []
        for metric, new_value in corrections.items():
            if metric in scouting_data[match_idx]:
                original_value = scouting_data[match_idx][metric]
                
                # Create audit entry
                audit_entry = AuditEntry(
                    metric=metric,
                    original_value=original_value,
                    corrected_value=new_value,
                    reason=reason,
                    timestamp=datetime.now()
                )
                audit_entries.append(audit_entry)
                
                # Initialize correction history if needed
                if "correction_history" not in scouting_data[match_idx]:
                    scouting_data[match_idx]["correction_history"] = []
                
                # Add to history
                scouting_data[match_idx]["correction_history"].append(audit_entry.dict())
                
                # Apply the correction
                scouting_data[match_idx][metric] = new_value
        
        return {
            "status": "success",
            "corrections_applied": len(audit_entries),
            "audit_entries": [entry.dict() for entry in audit_entries]
        }
    
    def _find_match_data(self, team_data: Dict, match_number: int) -> Optional[Dict]:
        """Find match data for a specific match number."""
        for match in team_data.get("scouting_data", []):
            if self._get_match_number(match) == match_number:
                return match
        return None
    
    def _find_match_index(self, scouting_data: List[Dict], match_number: int) -> Optional[int]:
        """Find the index of a match in scouting data."""
        for idx, match in enumerate(scouting_data):
            if self._get_match_number(match) == match_number:
                return idx
        return None
    
    def _calculate_team_averages(self, team_data: Dict, metrics: List[str]) -> Dict[str, float]:
        """Calculate team averages for specified metrics."""
        scouting_data = team_data.get("scouting_data", [])
        if not scouting_data:
            return {}
        
        averages = {}
        for metric in metrics:
            values = []
            for match in scouting_data:
                if metric in match and isinstance(match[metric], (int, float)):
                    values.append(float(match[metric]))
            
            if values:
                averages[metric] = np.mean(values)
        
        return averages
    
    def _suggest_from_bounds(self, dataset: Dict, metric: str, current_value: float) -> Optional[CorrectionSuggestion]:
        """Suggest correction based on statistical bounds."""
        # This would calculate bounds from all data for the metric
        all_values = self._collect_all_values(dataset, metric)
        if len(all_values) < 10:
            return None
        
        q1 = np.percentile(all_values, 25)
        q3 = np.percentile(all_values, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        if current_value < lower_bound:
            return CorrectionSuggestion(
                metric=metric,
                current_value=current_value,
                suggested_value=self._round_appropriately(lower_bound, current_value),
                method=CorrectionMethod.MINIMUM_REASONABLE,
                confidence=0.7,
                reason=f"Adjusted to minimum reasonable value (lower bound: {lower_bound:.2f})"
            )
        elif current_value > upper_bound:
            return CorrectionSuggestion(
                metric=metric,
                current_value=current_value,
                suggested_value=self._round_appropriately(upper_bound, current_value),
                method=CorrectionMethod.MAXIMUM_REASONABLE,
                confidence=0.7,
                reason=f"Adjusted to maximum reasonable value (upper bound: {upper_bound:.2f})"
            )
        
        return None
    
    def _collect_all_values(self, dataset: Dict, metric: str) -> List[float]:
        """Collect all values for a specific metric across all teams."""
        values = []
        teams_data = dataset.get("teams", {})
        
        for team_data in teams_data.values():
            for match in team_data.get("scouting_data", []):
                if metric in match and isinstance(match[metric], (int, float)):
                    values.append(float(match[metric]))
        
        return values
    
    def _should_suggest_zero(self, metric: str, current_value: float) -> bool:
        """Determine if zero should be suggested for a metric."""
        # Don't suggest zero if it's already zero
        if current_value == 0:
            return False
        
        # Metrics where zero is a common correction
        zero_friendly_patterns = ["penalty", "foul", "miss", "drop", "fail"]
        metric_lower = metric.lower()
        
        return any(pattern in metric_lower for pattern in zero_friendly_patterns)
    
    def _round_appropriately(self, value: float, reference: Any) -> float:
        """Round a value appropriately based on the reference type."""
        if isinstance(reference, int):
            return int(round(value))
        else:
            return round(value, 2)
    
    def _get_match_number(self, match: Dict) -> Optional[int]:
        """Extract match number from match data."""
        for field in ["qual_number", "match_number"]:
            if field in match:
                try:
                    return int(match[field])
                except (ValueError, TypeError):
                    pass
        return None