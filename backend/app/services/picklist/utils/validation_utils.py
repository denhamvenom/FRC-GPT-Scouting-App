"""
Validation utilities for picklist operations.

Provides comprehensive validation for picklist requests, team data,
batch parameters, and response structures.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from ..exceptions import PicklistValidationError

logger = logging.getLogger(__name__)


class PicklistValidator:
    """
    Comprehensive validator for picklist operations.
    """
    
    # FRC team number constraints
    MIN_TEAM_NUMBER = 1
    MAX_TEAM_NUMBER = 99999
    
    # Batch processing constraints
    MIN_BATCH_SIZE = 5
    MAX_BATCH_SIZE = 100
    MIN_REFERENCE_TEAMS = 0
    MAX_REFERENCE_TEAMS = 20
    
    # Score constraints
    MIN_SCORE = 0.0
    MAX_SCORE = 100.0
    
    def __init__(self):
        """Initialize picklist validator."""
        pass
    
    def validate_picklist_request(self, request_data: Dict[str, Any]) -> List[str]:
        """
        Validate a complete picklist generation request.
        
        Args:
            request_data: Request data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate required fields
        required_fields = ["your_team_number", "priorities"]
        for field in required_fields:
            if field not in request_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate team number
        your_team = request_data.get("your_team_number")
        if your_team is not None:
            team_errors = self.validate_team_number(your_team)
            errors.extend(team_errors)
        
        # Validate priorities
        priorities = request_data.get("priorities", [])
        priority_errors = self.validate_priorities(priorities)
        errors.extend(priority_errors)
        
        # Validate exclude teams
        exclude_teams = request_data.get("exclude_teams", [])
        exclude_errors = self.validate_team_numbers(exclude_teams)
        errors.extend([f"exclude_teams: {err}" for err in exclude_errors])
        
        # Validate batch parameters
        if request_data.get("use_batching", False):
            batch_errors = self.validate_batch_parameters(
                request_data.get("batch_size", 50),
                request_data.get("reference_teams_count", 3)
            )
            errors.extend(batch_errors)
        
        return errors
    
    def validate_team_number(self, team_number: Any) -> List[str]:
        """
        Validate a single team number.
        
        Args:
            team_number: Team number to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check type
        if not isinstance(team_number, int):
            try:
                team_number = int(team_number)
            except (ValueError, TypeError):
                errors.append(f"Team number must be an integer, got {type(team_number)}")
                return errors
        
        # Check range
        if team_number < self.MIN_TEAM_NUMBER:
            errors.append(f"Team number {team_number} is below minimum {self.MIN_TEAM_NUMBER}")
        elif team_number > self.MAX_TEAM_NUMBER:
            errors.append(f"Team number {team_number} exceeds maximum {self.MAX_TEAM_NUMBER}")
        
        return errors
    
    def validate_team_numbers(self, team_numbers: List[Any]) -> List[str]:
        """
        Validate a list of team numbers.
        
        Args:
            team_numbers: List of team numbers to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        seen_teams = set()
        
        if not isinstance(team_numbers, list):
            errors.append(f"Team numbers must be a list, got {type(team_numbers)}")
            return errors
        
        for idx, team_number in enumerate(team_numbers):
            # Validate individual team number
            team_errors = self.validate_team_number(team_number)
            for error in team_errors:
                errors.append(f"Team {idx}: {error}")
            
            # Check for duplicates
            if isinstance(team_number, int) and team_number in seen_teams:
                errors.append(f"Duplicate team number: {team_number}")
            else:
                seen_teams.add(team_number)
        
        return errors
    
    def validate_priorities(self, priorities: List[Dict[str, Any]]) -> List[str]:
        """
        Validate priority metrics.
        
        Args:
            priorities: List of priority dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(priorities, list):
            errors.append(f"Priorities must be a list, got {type(priorities)}")
            return errors
        
        if not priorities:
            errors.append("At least one priority metric is required")
            return errors
        
        seen_ids = set()
        total_weight = 0.0
        
        for idx, priority in enumerate(priorities):
            if not isinstance(priority, dict):
                errors.append(f"Priority {idx} must be a dictionary")
                continue
            
            # Validate required fields
            required_fields = ["id", "name", "weight"]
            for field in required_fields:
                if field not in priority:
                    errors.append(f"Priority {idx}: missing required field '{field}'")
            
            # Validate ID uniqueness
            priority_id = priority.get("id")
            if priority_id in seen_ids:
                errors.append(f"Priority {idx}: duplicate ID '{priority_id}'")
            else:
                seen_ids.add(priority_id)
            
            # Validate weight
            weight = priority.get("weight")
            if weight is not None:
                try:
                    weight = float(weight)
                    if weight < 0:
                        errors.append(f"Priority {idx}: weight must be non-negative")
                    elif weight > 1:
                        errors.append(f"Priority {idx}: weight should not exceed 1.0")
                    total_weight += weight
                except (ValueError, TypeError):
                    errors.append(f"Priority {idx}: weight must be numeric")
        
        # Check total weight
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Priority weights should sum to 1.0, got {total_weight}")
        
        return errors
    
    def validate_batch_parameters(
        self, 
        batch_size: int, 
        reference_teams_count: int
    ) -> List[str]:
        """
        Validate batch processing parameters.
        
        Args:
            batch_size: Teams per batch
            reference_teams_count: Reference teams between batches
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate batch size
        if not isinstance(batch_size, int):
            errors.append(f"Batch size must be an integer, got {type(batch_size)}")
        elif batch_size < self.MIN_BATCH_SIZE:
            errors.append(f"Batch size must be at least {self.MIN_BATCH_SIZE}")
        elif batch_size > self.MAX_BATCH_SIZE:
            errors.append(f"Batch size cannot exceed {self.MAX_BATCH_SIZE}")
        
        # Validate reference teams count
        if not isinstance(reference_teams_count, int):
            errors.append(f"Reference teams count must be an integer, got {type(reference_teams_count)}")
        elif reference_teams_count < self.MIN_REFERENCE_TEAMS:
            errors.append(f"Reference teams count must be at least {self.MIN_REFERENCE_TEAMS}")
        elif reference_teams_count > self.MAX_REFERENCE_TEAMS:
            errors.append(f"Reference teams count cannot exceed {self.MAX_REFERENCE_TEAMS}")
        
        # Validate relationship between batch size and reference teams
        if isinstance(batch_size, int) and isinstance(reference_teams_count, int):
            if reference_teams_count > batch_size // 2:
                errors.append(
                    f"Reference teams count ({reference_teams_count}) cannot exceed "
                    f"half of batch size ({batch_size // 2})"
                )
        
        return errors
    
    def validate_team_data(self, teams_data: List[Dict[str, Any]]) -> List[str]:
        """
        Validate team data structure.
        
        Args:
            teams_data: List of team data dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(teams_data, list):
            errors.append(f"Teams data must be a list, got {type(teams_data)}")
            return errors
        
        if not teams_data:
            errors.append("Teams data cannot be empty")
            return errors
        
        seen_teams = set()
        
        for idx, team_data in enumerate(teams_data):
            if not isinstance(team_data, dict):
                errors.append(f"Team {idx} must be a dictionary")
                continue
            
            # Validate team number
            team_number = team_data.get("team_number")
            if team_number is None:
                errors.append(f"Team {idx}: missing team_number")
            else:
                team_errors = self.validate_team_number(team_number)
                for error in team_errors:
                    errors.append(f"Team {idx}: {error}")
                
                # Check for duplicates
                if team_number in seen_teams:
                    errors.append(f"Team {idx}: duplicate team number {team_number}")
                else:
                    seen_teams.add(team_number)
            
            # Validate optional nickname
            nickname = team_data.get("nickname")
            if nickname is not None and not isinstance(nickname, str):
                errors.append(f"Team {idx}: nickname must be a string")
            
            # Validate metrics if present
            metrics = team_data.get("metrics")
            if metrics is not None:
                if not isinstance(metrics, dict):
                    errors.append(f"Team {idx}: metrics must be a dictionary")
                else:
                    # Validate metric values
                    for metric_name, value in metrics.items():
                        if not isinstance(value, (int, float)):
                            errors.append(
                                f"Team {idx}: metric '{metric_name}' must be numeric"
                            )
        
        return errors
    
    def validate_ranked_teams(self, ranked_teams: List[Dict[str, Any]]) -> List[str]:
        """
        Validate ranked teams structure.
        
        Args:
            ranked_teams: List of ranked team dictionaries
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(ranked_teams, list):
            errors.append(f"Ranked teams must be a list, got {type(ranked_teams)}")
            return errors
        
        seen_teams = set()
        
        for idx, team in enumerate(ranked_teams):
            if not isinstance(team, dict):
                errors.append(f"Ranked team {idx} must be a dictionary")
                continue
            
            # Validate team number
            team_number = team.get("team_number")
            if team_number is None:
                errors.append(f"Ranked team {idx}: missing team_number")
            else:
                team_errors = self.validate_team_number(team_number)
                for error in team_errors:
                    errors.append(f"Ranked team {idx}: {error}")
                
                # Check for duplicates
                if team_number in seen_teams:
                    errors.append(f"Ranked team {idx}: duplicate team number {team_number}")
                else:
                    seen_teams.add(team_number)
            
            # Validate score
            score = team.get("score")
            if score is None:
                errors.append(f"Ranked team {idx}: missing score")
            else:
                try:
                    score = float(score)
                    if score < self.MIN_SCORE or score > self.MAX_SCORE:
                        errors.append(
                            f"Ranked team {idx}: score {score} outside valid range "
                            f"[{self.MIN_SCORE}, {self.MAX_SCORE}]"
                        )
                except (ValueError, TypeError):
                    errors.append(f"Ranked team {idx}: score must be numeric")
            
            # Validate reasoning
            reasoning = team.get("reasoning")
            if reasoning is not None and not isinstance(reasoning, str):
                errors.append(f"Ranked team {idx}: reasoning must be a string")
        
        return errors


# Convenience functions
def validate_picklist_request(request_data: Dict[str, Any]) -> None:
    """
    Validate picklist request and raise exception if invalid.
    
    Args:
        request_data: Request data to validate
        
    Raises:
        PicklistValidationError: If validation fails
    """
    validator = PicklistValidator()
    errors = validator.validate_picklist_request(request_data)
    
    if errors:
        raise PicklistValidationError(f"Validation failed: {'; '.join(errors)}")


def validate_team_numbers(team_numbers: List[Any]) -> None:
    """
    Validate team numbers and raise exception if invalid.
    
    Args:
        team_numbers: List of team numbers to validate
        
    Raises:
        PicklistValidationError: If validation fails
    """
    validator = PicklistValidator()
    errors = validator.validate_team_numbers(team_numbers)
    
    if errors:
        raise PicklistValidationError(f"Team number validation failed: {'; '.join(errors)}")


def validate_batch_parameters(batch_size: int, reference_teams_count: int) -> None:
    """
    Validate batch parameters and raise exception if invalid.
    
    Args:
        batch_size: Teams per batch
        reference_teams_count: Reference teams between batches
        
    Raises:
        PicklistValidationError: If validation fails
    """
    validator = PicklistValidator()
    errors = validator.validate_batch_parameters(batch_size, reference_teams_count)
    
    if errors:
        raise PicklistValidationError(f"Batch parameter validation failed: {'; '.join(errors)}")


def validate_team_data(teams_data: List[Dict[str, Any]]) -> None:
    """
    Validate team data structure and raise exception if invalid.
    
    Args:
        teams_data: List of team data dictionaries
        
    Raises:
        PicklistValidationError: If validation fails
    """
    validator = PicklistValidator()
    errors = validator.validate_team_data(teams_data)
    
    if errors:
        raise PicklistValidationError(f"Team data validation failed: {'; '.join(errors)}")


def is_valid_team_number(team_number: Any) -> bool:
    """
    Check if a team number is valid without raising exceptions.
    
    Args:
        team_number: Team number to check
        
    Returns:
        True if valid, False otherwise
    """
    validator = PicklistValidator()
    errors = validator.validate_team_number(team_number)
    return len(errors) == 0


def sanitize_team_numbers(team_numbers: List[Any]) -> List[int]:
    """
    Sanitize and filter valid team numbers from a list.
    
    Args:
        team_numbers: List that may contain invalid team numbers
        
    Returns:
        List of valid team numbers as integers
    """
    valid_teams = []
    
    for team_number in team_numbers:
        try:
            team_int = int(team_number)
            if is_valid_team_number(team_int):
                valid_teams.append(team_int)
            else:
                logger.warning(f"Filtered out invalid team number: {team_number}")
        except (ValueError, TypeError):
            logger.warning(f"Filtered out non-numeric team number: {team_number}")
    
    return valid_teams