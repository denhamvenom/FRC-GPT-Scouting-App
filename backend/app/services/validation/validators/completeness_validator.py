"""
Completeness Validator

Validates that all expected data is present in the dataset.
Checks for missing scouting records, superscouting data, and tracks ignored matches.
"""

from typing import Dict, List, Set, Tuple

from ..models import ValidationIssue, IssueType, IssueSeverity


class CompletenessValidator:
    """Validates data completeness for an event."""
    
    def validate(self, dataset: Dict) -> Tuple[List[ValidationIssue], Dict[str, any]]:
        """
        Validate completeness of the dataset.
        
        Args:
            dataset: The unified dataset to validate
            
        Returns:
            Tuple of (issues list, metadata dict)
        """
        issues = []
        
        # Extract data structures
        expected_matches = dataset.get("expected_matches", [])
        teams_data = dataset.get("teams", {})
        direct_scouting = dataset.get("scouting", [])
        
        # Process scouting records
        scouting_records = self._collect_scouting_records(teams_data, direct_scouting)
        superscouted_teams = self._collect_superscouted_teams(teams_data)
        
        # Build expected sets
        expected_match_records, expected_team_numbers = self._build_expected_sets(expected_matches)
        
        # Find missing data
        missing_scouting = expected_match_records - scouting_records
        missing_superscouting = expected_team_numbers - superscouted_teams
        
        # Create issues for missing scouting
        for match_number, team_number in missing_scouting:
            issues.append(ValidationIssue(
                team_number=team_number,
                match_number=match_number,
                issue_type=IssueType.MISSING_SCOUTING,
                severity=IssueSeverity.WARNING,
                details={
                    "expected": True,
                    "found": False,
                    "data_type": "scouting"
                }
            ))
        
        # Create issues for missing superscouting
        for team_number in missing_superscouting:
            issues.append(ValidationIssue(
                team_number=team_number,
                match_number=0,  # No specific match for superscouting
                issue_type=IssueType.MISSING_SUPERSCOUTING,
                severity=IssueSeverity.INFO,
                details={
                    "expected": True,
                    "found": False,
                    "data_type": "superscouting"
                }
            ))
        
        # Process ignored matches
        ignored_matches = self._collect_ignored_matches(teams_data)
        for ignored in ignored_matches:
            issues.append(ValidationIssue(
                team_number=ignored["team_number"],
                match_number=ignored["match_number"],
                issue_type=IssueType.IGNORED_MATCH,
                severity=IssueSeverity.INFO,
                details={
                    "reason": ignored.get("reason"),
                    "reason_category": ignored.get("reason_category"),
                    "timestamp": ignored.get("timestamp")
                }
            ))
        
        # Build metadata
        metadata = {
            "scouting_records_count": len(scouting_records),
            "expected_match_records_count": len(expected_match_records),
            "superscouted_teams_count": len(superscouted_teams),
            "expected_teams_count": len(expected_team_numbers),
            "ignored_matches_count": len(ignored_matches),
            "missing_scouting_count": len(missing_scouting),
            "missing_superscouting_count": len(missing_superscouting)
        }
        
        return issues, metadata
    
    def _collect_scouting_records(self, teams_data: Dict, direct_scouting: List) -> Set[Tuple[int, int]]:
        """Collect all scouting records from various sources."""
        scouting_records = set()
        
        # Process direct scouting records
        if direct_scouting:
            for match in direct_scouting:
                team_number = self._safe_int_conversion(match.get("team_number"))
                if team_number is None:
                    continue
                
                match_number = (
                    self._safe_int_conversion(match.get("qual_number")) or
                    self._safe_int_conversion(match.get("match_number"))
                )
                
                if match_number is not None:
                    scouting_records.add((match_number, team_number))
        
        # Process per-team scouting data
        for team_number_str, team_data in teams_data.items():
            team_number = self._safe_int_conversion(team_number_str)
            if team_number is None:
                continue
            
            for match in team_data.get("scouting_data", []):
                match_number = (
                    self._safe_int_conversion(match.get("qual_number")) or
                    self._safe_int_conversion(match.get("match_number"))
                )
                
                if match_number is not None:
                    scouting_records.add((match_number, team_number))
        
        return scouting_records
    
    def _collect_superscouted_teams(self, teams_data: Dict) -> Set[int]:
        """Collect teams that have superscouting data."""
        superscouted_teams = set()
        
        for team_number_str, team_data in teams_data.items():
            for superscout_entry in team_data.get("superscouting_data", []):
                team_number = self._safe_int_conversion(superscout_entry.get("team_number"))
                if team_number is not None:
                    superscouted_teams.add(team_number)
        
        return superscouted_teams
    
    def _build_expected_sets(self, expected_matches: List) -> Tuple[Set[Tuple[int, int]], Set[int]]:
        """Build sets of expected match records and team numbers."""
        expected_match_records = set()
        expected_team_numbers = set()
        
        for entry in expected_matches:
            match_number = self._safe_int_conversion(entry.get("match_number"))
            team_number = self._safe_int_conversion(entry.get("team_number"))
            
            if match_number is not None and team_number is not None:
                expected_match_records.add((match_number, team_number))
                expected_team_numbers.add(team_number)
        
        return expected_match_records, expected_team_numbers
    
    def _collect_ignored_matches(self, teams_data: Dict) -> List[Dict]:
        """Collect all ignored matches."""
        ignored_matches = []
        
        for team_number_str, team_data in teams_data.items():
            team_number = self._safe_int_conversion(team_number_str)
            if team_number is None:
                continue
            
            for match in team_data.get("ignored_matches", []):
                ignored_matches.append({
                    "team_number": team_number,
                    "match_number": match.get("match_number"),
                    "reason": match.get("reason"),
                    "reason_category": match.get("reason_category"),
                    "timestamp": match.get("timestamp"),
                })
        
        return ignored_matches
    
    def _safe_int_conversion(self, value: any) -> int:
        """Safely convert a value to integer, returning None if not possible."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None