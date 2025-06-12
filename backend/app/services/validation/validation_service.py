"""
Validation Service

Main orchestrator for data validation operations.
Coordinates validators and correctors to provide comprehensive validation functionality.
"""

import json
from typing import Dict, List, Any, Optional, Tuple

from .validators import (
    CompletenessValidator,
    StatisticalValidator,
    TeamValidator,
    DataQualityValidator
)
from .correctors import (
    OutlierCorrector,
    MissingDataCorrector,
    AuditManager
)
from .models import (
    ValidationResult, ValidationSummary, ValidationIssue,
    CorrectionSuggestion, VirtualScoutData, TodoItem
)
from .exceptions import FileOperationError


class ValidationService:
    """Main service for data validation operations."""
    
    def __init__(self, z_score_threshold: float = 3.0, game_year: int = 2025):
        """
        Initialize the validation service.
        
        Args:
            z_score_threshold: Threshold for outlier detection
            game_year: Game year for rule validation
        """
        # Initialize validators
        self.completeness_validator = CompletenessValidator()
        self.statistical_validator = StatisticalValidator(z_score_threshold)
        self.team_validator = TeamValidator(z_score_threshold)
        self.data_quality_validator = DataQualityValidator(game_year)
        
        # Initialize correctors
        self.outlier_corrector = OutlierCorrector()
        self.missing_data_corrector = MissingDataCorrector()
        self.audit_manager = AuditManager()
        
        self.z_score_threshold = z_score_threshold
    
    def validate_dataset(self, dataset_path: str, 
                        include_outliers: bool = True,
                        include_team_specific: bool = True,
                        include_quality: bool = True) -> ValidationResult:
        """
        Perform comprehensive validation on a dataset.
        
        Args:
            dataset_path: Path to the unified dataset
            include_outliers: Include statistical outlier detection
            include_team_specific: Include team-specific validation
            include_quality: Include data quality checks
            
        Returns:
            ValidationResult with all issues found
        """
        # Load dataset
        dataset = self._load_dataset(dataset_path)
        
        all_issues = []
        metadata = {}
        
        # Always run completeness validation
        completeness_issues, completeness_meta = self.completeness_validator.validate(dataset)
        all_issues.extend(completeness_issues)
        metadata["completeness"] = completeness_meta
        
        # Optional validations
        if include_outliers:
            outlier_issues, outlier_meta = self.statistical_validator.validate(dataset)
            all_issues.extend(outlier_issues)
            metadata["statistical"] = outlier_meta
        
        if include_team_specific:
            team_issues, team_meta = self.team_validator.validate(dataset)
            all_issues.extend(team_issues)
            metadata["team_specific"] = team_meta
        
        if include_quality:
            quality_issues, quality_meta = self.data_quality_validator.validate(dataset)
            all_issues.extend(quality_issues)
            metadata["data_quality"] = quality_meta
        
        # Build result
        result = self._build_validation_result(dataset, all_issues, metadata)
        
        return result
    
    def suggest_corrections(self, dataset_path: str, team_number: int, 
                          match_number: int) -> List[CorrectionSuggestion]:
        """
        Suggest corrections for issues in a specific match.
        
        Args:
            dataset_path: Path to the unified dataset
            team_number: Team number
            match_number: Match number
            
        Returns:
            List of correction suggestions
        """
        dataset = self._load_dataset(dataset_path)
        
        # Find outliers for this team/match
        validation_result = self.validate_dataset(dataset_path)
        outlier_metrics = []
        
        for issue in validation_result.issues:
            if (issue.team_number == team_number and 
                issue.match_number == match_number and
                issue.metric):
                outlier_metrics.append(issue.metric)
        
        if not outlier_metrics:
            return []
        
        # Get suggestions
        return self.outlier_corrector.suggest_corrections(
            dataset, team_number, match_number, outlier_metrics
        )
    
    def apply_correction(self, dataset_path: str, team_number: int,
                        match_number: int, corrections: Dict[str, Any],
                        reason: str = "") -> Dict[str, Any]:
        """
        Apply corrections to a dataset.
        
        Args:
            dataset_path: Path to the unified dataset
            team_number: Team number
            match_number: Match number
            corrections: Dict of metric -> corrected value
            reason: Reason for corrections
            
        Returns:
            Result of correction operation
        """
        dataset = self._load_dataset(dataset_path)
        
        # Apply corrections
        result = self.outlier_corrector.apply_correction(
            dataset, team_number, match_number, corrections, reason
        )
        
        # Save dataset if successful
        if result.get("status") == "success":
            self._save_dataset(dataset_path, dataset)
        
        return result
    
    def create_virtual_scout(self, dataset_path: str, team_number: int,
                           match_number: int, preview_only: bool = False) -> VirtualScoutData:
        """
        Create or preview virtual scout data.
        
        Args:
            dataset_path: Path to the unified dataset
            team_number: Team number
            match_number: Match number
            preview_only: If True, don't save changes
            
        Returns:
            VirtualScoutData object
        """
        dataset = self._load_dataset(dataset_path)
        
        if preview_only:
            return self.missing_data_corrector.preview_virtual_scout(
                dataset, team_number, match_number
            )
        else:
            result = self.missing_data_corrector.create_virtual_scout(
                dataset, team_number, match_number
            )
            self._save_dataset(dataset_path, dataset)
            return result
    
    def ignore_match(self, dataset_path: str, team_number: int, match_number: int,
                    reason_category: str, reason_text: str = "") -> Dict[str, Any]:
        """
        Mark a match as ignored.
        
        Args:
            dataset_path: Path to the unified dataset
            team_number: Team number
            match_number: Match number
            reason_category: Category of ignore reason
            reason_text: Optional detailed explanation
            
        Returns:
            Result of ignore operation
        """
        dataset = self._load_dataset(dataset_path)
        
        ignored_match = self.missing_data_corrector.ignore_match(
            dataset, team_number, match_number, reason_category, reason_text
        )
        
        self._save_dataset(dataset_path, dataset)
        
        return {
            "status": "success",
            "ignored_match": ignored_match.dict()
        }
    
    def manage_todo(self, dataset_path: str, action: str, **kwargs) -> Any:
        """
        Manage todo list operations.
        
        Args:
            dataset_path: Path to the unified dataset
            action: Action to perform (add, get, update)
            **kwargs: Action-specific arguments
            
        Returns:
            Action-specific result
        """
        dataset = self._load_dataset(dataset_path)
        
        if action == "add":
            todo_item = self.missing_data_corrector.add_to_todo(
                dataset, 
                kwargs["team_number"],
                kwargs["match_number"],
                kwargs.get("priority", 3),
                kwargs.get("description")
            )
            self._save_dataset(dataset_path, dataset)
            return todo_item
        
        elif action == "get":
            return self.missing_data_corrector.get_todo_list(dataset)
        
        elif action == "update":
            todo_item = self.missing_data_corrector.update_todo_status(
                dataset,
                kwargs["team_number"],
                kwargs["match_number"],
                kwargs["status"],
                kwargs.get("assigned_to"),
                kwargs.get("notes")
            )
            self._save_dataset(dataset_path, dataset)
            return todo_item
        
        else:
            raise ValueError(f"Unknown todo action: {action}")
    
    def get_team_averages(self, dataset_path: str, team_number: int) -> Dict[str, float]:
        """
        Get team averages for all metrics.
        
        Args:
            dataset_path: Path to the unified dataset
            team_number: Team number
            
        Returns:
            Dict of metric -> average value
        """
        dataset = self._load_dataset(dataset_path)
        teams_data = dataset.get("teams", {})
        
        if str(team_number) not in teams_data:
            return {}
        
        team_data = teams_data[str(team_number)]
        return self._calculate_team_averages(team_data.get("scouting_data", []))
    
    def _load_dataset(self, path: str) -> Dict:
        """Load dataset from file."""
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        logger.debug(f"Attempting to load dataset from: {path}")
        logger.debug(f"Path exists: {os.path.exists(path)}")
        logger.debug(f"Absolute path: {os.path.abspath(path)}")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Dataset file not found: {path}")
            logger.error(f"Current working directory: {os.getcwd()}")
            
            # Try to provide helpful debugging information
            parent_dir = os.path.dirname(path)
            if os.path.exists(parent_dir):
                files = os.listdir(parent_dir)
                logger.error(f"Files in {parent_dir}: {files[:10]}")  # Show first 10 files
            else:
                logger.error(f"Parent directory does not exist: {parent_dir}")
            
            # Check common alternative locations
            alternatives = [
                os.path.join("app", "data", os.path.basename(path)),
                os.path.join("/app", "app", "data", os.path.basename(path)),
                os.path.join(os.getcwd(), "app", "data", os.path.basename(path)),
            ]
            
            for alt_path in alternatives:
                if os.path.exists(alt_path):
                    logger.error(f"Found file at alternative location: {alt_path}")
                    logger.error("Consider updating the path or configuration")
                    break
            
            raise FileOperationError("read", path, f"File not found. Please ensure the dataset has been built for this event.")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in dataset file {path}: {str(e)}")
            raise FileOperationError("read", path, f"Invalid JSON format: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading dataset from {path}: {str(e)}")
            raise FileOperationError("read", path, str(e))
    
    def _save_dataset(self, path: str, dataset: Dict) -> None:
        """Save dataset to file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, indent=2)
        except Exception as e:
            raise FileOperationError("write", path, str(e))
    
    def _build_validation_result(self, dataset: Dict, issues: List[ValidationIssue],
                               metadata: Dict[str, Any]) -> ValidationResult:
        """Build a comprehensive validation result."""
        # Organize issues by type
        missing_scouting = []
        missing_superscouting = []
        outliers_dict = {}  # Group outliers by (team_number, match_number)
        ignored_matches = []
        
        for issue in issues:
            if issue.issue_type.value == "missing_scouting":
                missing_scouting.append({
                    "team_number": issue.team_number,
                    "match_number": issue.match_number
                })
            elif issue.issue_type.value == "missing_superscouting":
                missing_superscouting.append({
                    "team_number": issue.team_number
                })
            elif issue.issue_type.value in ["statistical_outlier", "team_outlier"]:
                # Group outliers by team and match
                key = (issue.team_number, issue.match_number)
                if key not in outliers_dict:
                    outliers_dict[key] = {
                        "team_number": issue.team_number,
                        "match_number": issue.match_number,
                        "issues": []
                    }
                
                # Add this issue to the group
                outliers_dict[key]["issues"].append({
                    "metric": issue.metric,
                    "value": issue.value,
                    **issue.details
                })
            elif issue.issue_type.value == "ignored_match":
                ignored_matches.append({
                    "team_number": issue.team_number,
                    "match_number": issue.match_number,
                    **issue.details
                })
        
        # Convert outliers dict to list
        outliers = list(outliers_dict.values())
        
        # Build summary
        summary = ValidationSummary(
            total_missing_matches=len(missing_scouting),
            total_missing_superscouting=len(missing_superscouting),
            total_outliers=len(outliers),
            total_ignored_matches=len(ignored_matches),
            has_issues=bool(issues),
            scouting_records_count=metadata.get("completeness", {}).get("scouting_records_count", 0),
            expected_match_records_count=metadata.get("completeness", {}).get("expected_match_records_count", 0)
        )
        
        # Determine status
        status = "complete" if not summary.has_issues else "issues_found"
        
        return ValidationResult(
            status=status,
            missing_scouting=missing_scouting,
            missing_superscouting=missing_superscouting,
            outliers=outliers,
            ignored_matches=ignored_matches,
            summary=summary,
            issues=issues
        )
    
    def _calculate_team_averages(self, scouting_data: List[Dict]) -> Dict[str, float]:
        """Calculate team averages for all numeric metrics."""
        if not scouting_data:
            return {}
        
        metrics = {}
        for match in scouting_data:
            for key, value in match.items():
                if isinstance(value, (int, float)) and key not in [
                    "qual_number", "match_number", "team_number"
                ]:
                    if key not in metrics:
                        metrics[key] = []
                    metrics[key].append(float(value))
        
        averages = {}
        for key, values in metrics.items():
            if values:
                averages[key] = sum(values) / len(values)
        
        return averages