"""
Data Quality Validator

Performs various data quality checks including:
- Range validation for known metrics
- Data type consistency
- Business rule validation
- Duplicate detection
"""

from typing import Dict, List, Tuple, Any, Set

from ..models import ValidationIssue, IssueType, IssueSeverity, DetectionMethod


class DataQualityValidator:
    """Validates data quality and business rules."""
    
    def __init__(self, game_year: int = 2025):
        """
        Initialize the data quality validator.
        
        Args:
            game_year: The game year for rule validation
        """
        self.game_year = game_year
        self._init_metric_rules()
    
    def _init_metric_rules(self):
        """Initialize metric validation rules based on game year."""
        # Define reasonable ranges for common metrics
        # These would be customized per game year
        self.metric_ranges = {
            # Scoring metrics (examples)
            "auto_high_goals": (0, 10),
            "teleop_high_goals": (0, 30),
            "auto_low_goals": (0, 10),
            "teleop_low_goals": (0, 30),
            
            # Movement metrics
            "auto_mobility": (0, 1),  # Boolean
            "endgame_climb": (0, 3),  # None, Low, Mid, High
            
            # Defense metrics
            "defense_rating": (0, 5),
            "driver_rating": (0, 5),
            
            # Generic ranges for unknown numeric fields
            "_default_count": (0, 100),  # For counting metrics
            "_default_rating": (0, 10),   # For rating metrics
            "_default_boolean": (0, 1),   # For boolean metrics
        }
    
    def validate(self, dataset: Dict) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Perform data quality validation.
        
        Args:
            dataset: The unified dataset to validate
            
        Returns:
            Tuple of (issues list, metadata dict)
        """
        issues = []
        teams_data = dataset.get("teams", {})
        
        # Track validation statistics
        total_values_checked = 0
        range_violations = 0
        duplicate_entries = 0
        
        # Check for duplicate entries
        duplicate_issues, duplicates_found = self._check_duplicates(teams_data)
        issues.extend(duplicate_issues)
        duplicate_entries = duplicates_found
        
        # Validate data ranges and quality
        for team_number_str, team_data in teams_data.items():
            try:
                team_number = int(team_number_str)
            except ValueError:
                continue
            
            for match in team_data.get("scouting_data", []):
                match_number = self._get_match_number(match)
                if match_number is None:
                    continue
                
                # Check each field in the match data
                for key, value in match.items():
                    if key in ["qual_number", "match_number", "team_number"]:
                        continue
                    
                    total_values_checked += 1
                    
                    # Check range violations
                    range_issue = self._check_range_violation(
                        team_number, match_number, key, value
                    )
                    if range_issue:
                        issues.append(range_issue)
                        range_violations += 1
                    
                    # Check data consistency
                    consistency_issue = self._check_data_consistency(
                        team_number, match_number, key, value
                    )
                    if consistency_issue:
                        issues.append(consistency_issue)
        
        # Build metadata
        metadata = {
            "total_values_checked": total_values_checked,
            "range_violations": range_violations,
            "duplicate_entries": duplicate_entries,
            "validation_rules_count": len(self.metric_ranges)
        }
        
        return issues, metadata
    
    def _check_duplicates(self, teams_data: Dict) -> Tuple[List[ValidationIssue], int]:
        """Check for duplicate scouting entries."""
        issues = []
        seen_entries = {}
        duplicate_count = 0
        
        for team_number_str, team_data in teams_data.items():
            try:
                team_number = int(team_number_str)
            except ValueError:
                continue
            
            for match in team_data.get("scouting_data", []):
                match_number = self._get_match_number(match)
                if match_number is None:
                    continue
                
                entry_key = (team_number, match_number)
                
                if entry_key in seen_entries:
                    # Found a duplicate
                    duplicate_count += 1
                    issues.append(ValidationIssue(
                        team_number=team_number,
                        match_number=match_number,
                        issue_type=IssueType.DATA_QUALITY,
                        severity=IssueSeverity.WARNING,
                        details={
                            "issue": "duplicate_entry",
                            "description": f"Duplicate scouting entry for team {team_number} in match {match_number}",
                            "first_occurrence": seen_entries[entry_key]
                        }
                    ))
                else:
                    seen_entries[entry_key] = {
                        "team_number": team_number,
                        "match_number": match_number
                    }
        
        return issues, duplicate_count
    
    def _check_range_violation(self, team_number: int, match_number: int, 
                             metric: str, value: Any) -> ValidationIssue:
        """Check if a value violates expected ranges."""
        if not isinstance(value, (int, float)):
            return None
        
        # Get expected range for this metric
        expected_range = self._get_metric_range(metric)
        if expected_range is None:
            return None
        
        min_val, max_val = expected_range
        
        if value < min_val or value > max_val:
            severity = IssueSeverity.ERROR if value < 0 else IssueSeverity.WARNING
            
            return ValidationIssue(
                team_number=team_number,
                match_number=match_number,
                issue_type=IssueType.DATA_QUALITY,
                severity=severity,
                metric=metric,
                value=value,
                detection_method=DetectionMethod.BUSINESS_RULE,
                details={
                    "issue": "range_violation",
                    "expected_range": [min_val, max_val],
                    "actual_value": value,
                    "description": f"Value {value} is outside expected range [{min_val}, {max_val}]"
                }
            )
        
        return None
    
    def _check_data_consistency(self, team_number: int, match_number: int,
                               metric: str, value: Any) -> ValidationIssue:
        """Check for data type and consistency issues."""
        # Check for None or empty values in critical fields
        if value is None or value == "":
            if self._is_critical_field(metric):
                return ValidationIssue(
                    team_number=team_number,
                    match_number=match_number,
                    issue_type=IssueType.DATA_QUALITY,
                    severity=IssueSeverity.ERROR,
                    metric=metric,
                    details={
                        "issue": "missing_critical_data",
                        "description": f"Critical field '{metric}' is empty or null"
                    }
                )
        
        return None
    
    def _get_metric_range(self, metric: str) -> Tuple[float, float]:
        """Get the expected range for a metric."""
        # Check for exact match
        if metric in self.metric_ranges:
            return self.metric_ranges[metric]
        
        # Check for pattern-based ranges
        metric_lower = metric.lower()
        if "count" in metric_lower or "total" in metric_lower:
            return self.metric_ranges["_default_count"]
        elif "rating" in metric_lower or "score" in metric_lower:
            return self.metric_ranges["_default_rating"]
        elif "bool" in metric_lower or metric_lower.startswith("is_") or metric_lower.startswith("has_"):
            return self.metric_ranges["_default_boolean"]
        
        return None
    
    def _is_critical_field(self, metric: str) -> bool:
        """Determine if a field is critical and should not be empty."""
        critical_patterns = ["goals", "score", "climb", "mobility"]
        metric_lower = metric.lower()
        
        return any(pattern in metric_lower for pattern in critical_patterns)
    
    def _get_match_number(self, match: Dict) -> int:
        """Extract match number from match data."""
        for field in ["qual_number", "match_number"]:
            if field in match:
                try:
                    return int(match[field])
                except (ValueError, TypeError):
                    pass
        return None