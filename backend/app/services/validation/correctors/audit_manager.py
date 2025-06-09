"""
Audit Manager

Manages audit trails for all data corrections and modifications.
Provides history tracking and rollback capabilities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models import AuditEntry


class AuditManager:
    """Manages audit trails for data corrections."""
    
    def __init__(self):
        """Initialize the audit manager."""
        self.audit_key = "correction_history"
    
    def add_audit_entry(self, data_record: Dict, audit_entry: AuditEntry) -> None:
        """
        Add an audit entry to a data record.
        
        Args:
            data_record: The data record to add audit to
            audit_entry: The audit entry to add
        """
        if self.audit_key not in data_record:
            data_record[self.audit_key] = []
        
        data_record[self.audit_key].append(audit_entry.dict())
    
    def get_audit_history(self, data_record: Dict) -> List[AuditEntry]:
        """
        Get the audit history for a data record.
        
        Args:
            data_record: The data record to get history from
            
        Returns:
            List of AuditEntry objects
        """
        history = data_record.get(self.audit_key, [])
        return [AuditEntry(**entry) for entry in history]
    
    def get_original_value(self, data_record: Dict, metric: str) -> Optional[Any]:
        """
        Get the original value for a metric before any corrections.
        
        Args:
            data_record: The data record
            metric: The metric name
            
        Returns:
            Original value if found, None otherwise
        """
        history = self.get_audit_history(data_record)
        
        # Find the first correction for this metric
        for entry in history:
            if entry.metric == metric:
                return entry.original_value
        
        # If no corrections found, current value is original
        return data_record.get(metric)
    
    def get_correction_count(self, data_record: Dict, metric: Optional[str] = None) -> int:
        """
        Get the number of corrections applied.
        
        Args:
            data_record: The data record
            metric: Optional specific metric to count
            
        Returns:
            Number of corrections
        """
        history = self.get_audit_history(data_record)
        
        if metric:
            return sum(1 for entry in history if entry.metric == metric)
        else:
            return len(history)
    
    def can_rollback(self, data_record: Dict, metric: str) -> bool:
        """
        Check if a metric can be rolled back.
        
        Args:
            data_record: The data record
            metric: The metric name
            
        Returns:
            True if rollback is possible
        """
        history = self.get_audit_history(data_record)
        return any(entry.metric == metric for entry in history)
    
    def rollback_correction(self, data_record: Dict, metric: str) -> Dict[str, Any]:
        """
        Rollback the last correction for a metric.
        
        Args:
            data_record: The data record
            metric: The metric name
            
        Returns:
            Dict with rollback information
        """
        if not self.can_rollback(data_record, metric):
            return {
                "success": False,
                "reason": f"No corrections found for metric '{metric}'"
            }
        
        history = self.get_audit_history(data_record)
        
        # Find all corrections for this metric
        metric_corrections = [
            (i, entry) for i, entry in enumerate(history) 
            if entry.metric == metric
        ]
        
        if not metric_corrections:
            return {
                "success": False,
                "reason": f"No corrections found for metric '{metric}'"
            }
        
        # Get the last correction
        last_idx, last_correction = metric_corrections[-1]
        
        # Determine the value to restore
        if len(metric_corrections) > 1:
            # Restore to previous correction value
            prev_correction = metric_corrections[-2][1]
            restore_value = prev_correction.corrected_value
        else:
            # Restore to original value
            restore_value = last_correction.original_value
        
        # Apply the rollback
        old_value = data_record.get(metric)
        data_record[metric] = restore_value
        
        # Add rollback audit entry
        rollback_entry = AuditEntry(
            metric=metric,
            original_value=old_value,
            corrected_value=restore_value,
            reason=f"Rollback of correction from {last_correction.timestamp}",
            timestamp=datetime.now(),
            correction_method=None
        )
        
        # Remove the last correction from history
        data_record[self.audit_key].pop(last_idx)
        
        # Add rollback entry
        self.add_audit_entry(data_record, rollback_entry)
        
        return {
            "success": True,
            "metric": metric,
            "rolled_back_from": old_value,
            "rolled_back_to": restore_value,
            "rollback_entry": rollback_entry.dict()
        }
    
    def get_audit_summary(self, dataset: Dict) -> Dict[str, Any]:
        """
        Get a summary of all corrections in the dataset.
        
        Args:
            dataset: The full dataset
            
        Returns:
            Summary statistics
        """
        total_corrections = 0
        corrected_teams = set()
        corrected_matches = set()
        metrics_corrected = {}
        
        teams_data = dataset.get("teams", {})
        
        for team_number_str, team_data in teams_data.items():
            for match in team_data.get("scouting_data", []):
                history = match.get(self.audit_key, [])
                if history:
                    match_number = self._get_match_number(match)
                    corrected_teams.add(team_number_str)
                    if match_number:
                        corrected_matches.add((team_number_str, match_number))
                    
                    for entry_data in history:
                        total_corrections += 1
                        metric = entry_data.get("metric")
                        if metric:
                            metrics_corrected[metric] = metrics_corrected.get(metric, 0) + 1
        
        return {
            "total_corrections": total_corrections,
            "teams_with_corrections": len(corrected_teams),
            "matches_with_corrections": len(corrected_matches),
            "metrics_corrected": metrics_corrected,
            "most_corrected_metric": (
                max(metrics_corrected.items(), key=lambda x: x[1])[0] 
                if metrics_corrected else None
            )
        }
    
    def _get_match_number(self, match: Dict) -> Optional[int]:
        """Extract match number from match data."""
        for field in ["qual_number", "match_number"]:
            if field in match:
                try:
                    return int(match[field])
                except (ValueError, TypeError):
                    pass
        return None