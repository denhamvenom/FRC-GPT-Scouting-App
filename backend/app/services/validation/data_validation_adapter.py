"""
Data Validation Adapter

Provides backward compatibility layer for the old data_validation_service API.
Maps old function signatures to the new service-oriented architecture.
"""

from typing import Dict, Any, List, Tuple, Optional

from .validation_service import ValidationService
from .exceptions import ValidationError, DataNotFoundError


# Global service instance for backward compatibility
_validation_service = ValidationService()


def load_unified_dataset(path: str) -> Dict:
    """Legacy function for loading dataset."""
    return _validation_service._load_dataset(path)


def validate_event_completeness(unified_dataset_path: str) -> Dict:
    """
    Legacy function for completeness validation.
    
    Args:
        unified_dataset_path: Path to unified dataset
        
    Returns:
        Dict with completeness validation results
    """
    result = _validation_service.validate_dataset(
        unified_dataset_path,
        include_outliers=False,
        include_team_specific=False,
        include_quality=False
    )
    
    # Convert to legacy format
    return {
        "missing_scouting": result.missing_scouting,
        "missing_superscouting": result.missing_superscouting,
        "ignored_matches": result.ignored_matches,
        "status": "complete" if result.status == "complete" else "partial",
        "scouting_records_count": result.summary.scouting_records_count,
        "expected_match_records_count": result.summary.expected_match_records_count,
    }


def validate_event_with_outliers(
    unified_dataset_path: str, 
    z_score_threshold: float = 3.0
) -> Dict[str, Any]:
    """
    Legacy function for comprehensive validation with outliers.
    
    Args:
        unified_dataset_path: Path to unified dataset
        z_score_threshold: Threshold for outlier detection
        
    Returns:
        Dict with validation results including outliers
    """
    # Create service with specified threshold
    service = ValidationService(z_score_threshold=z_score_threshold)
    
    result = service.validate_dataset(
        unified_dataset_path,
        include_outliers=True,
        include_team_specific=True,
        include_quality=True
    )
    
    # Convert to legacy format
    return {
        "missing_scouting": result.missing_scouting,
        "missing_superscouting": result.missing_superscouting,
        "ignored_matches": result.ignored_matches,
        "outliers": result.outliers,
        "status": result.status,
        "summary": result.summary.dict(),
    }


def get_team_averages(unified_dataset_path: str, team_number: int) -> Dict[str, float]:
    """
    Legacy function for getting team averages.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        
    Returns:
        Dict of metric averages
    """
    return _validation_service.get_team_averages(unified_dataset_path, team_number)


def suggest_corrections(
    unified_dataset_path: str, 
    team_number: int, 
    match_number: int
) -> Dict[str, Any]:
    """
    Legacy function for suggesting corrections.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        match_number: Match number
        
    Returns:
        Dict with correction suggestions
    """
    try:
        suggestions = _validation_service.suggest_corrections(
            unified_dataset_path, team_number, match_number
        )
        
        # Convert to legacy format
        legacy_suggestions = []
        for suggestion in suggestions:
            legacy_suggestions.append({
                "metric": suggestion.metric,
                "current_value": suggestion.current_value,
                "suggested_corrections": [{
                    "value": suggestion.suggested_value,
                    "method": suggestion.method.value,
                }]
            })
        
        return {
            "status": "suggestions_found" if legacy_suggestions else "no_outliers_found",
            "team_number": team_number,
            "match_number": match_number,
            "suggestions": legacy_suggestions,
        }
    except DataNotFoundError:
        return {"status": "no_outliers_found"}


def apply_correction(
    unified_dataset_path: str,
    team_number: int,
    match_number: int,
    corrections: Dict[str, Any],
    reason: str = "",
) -> Dict[str, Any]:
    """
    Legacy function for applying corrections.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        match_number: Match number
        corrections: Dict of corrections to apply
        reason: Reason for corrections
        
    Returns:
        Dict with operation result
    """
    try:
        result = _validation_service.apply_correction(
            unified_dataset_path, team_number, match_number, corrections, reason
        )
        
        return {
            "status": result.get("status", "error"),
            "message": "Corrections applied successfully" if result.get("status") == "success" else "Error applying corrections",
            "team_number": team_number,
            "match_number": match_number,
        }
    except (DataNotFoundError, ValidationError) as e:
        return {
            "status": "error",
            "message": str(e),
        }


def ignore_match(
    unified_dataset_path: str,
    team_number: int,
    match_number: int,
    reason_category: str,
    reason_text: str = "",
) -> Dict[str, Any]:
    """
    Legacy function for ignoring a match.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        match_number: Match number
        reason_category: Category of ignore reason
        reason_text: Optional detailed reason
        
    Returns:
        Dict with operation result
    """
    try:
        result = _validation_service.ignore_match(
            unified_dataset_path, team_number, match_number, reason_category, reason_text
        )
        
        return {
            "status": result.get("status", "error"),
            "message": "Match ignored successfully",
            "team_number": team_number,
            "match_number": match_number,
        }
    except ValidationError as e:
        return {
            "status": "error",
            "message": str(e),
        }


def create_virtual_scout(
    unified_dataset_path: str,
    team_number: int,
    match_number: int
) -> Dict[str, Any]:
    """
    Legacy function for creating virtual scout.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        match_number: Match number
        
    Returns:
        Dict with virtual scout data
    """
    try:
        virtual_scout = _validation_service.create_virtual_scout(
            unified_dataset_path, team_number, match_number, preview_only=False
        )
        
        # Convert to legacy format
        virtual_data = virtual_scout.data.copy()
        virtual_data.update({
            "team_number": virtual_scout.team_number,
            "match_number": virtual_scout.match_number,
            "qual_number": virtual_scout.qual_number,
            "alliance_color": virtual_scout.alliance_color,
            "is_virtual_scout": virtual_scout.is_virtual_scout,
            "virtual_scout_timestamp": virtual_scout.virtual_scout_timestamp.isoformat(),
        })
        
        return {
            "status": "success",
            "message": "Virtual scout created successfully",
            "team_number": team_number,
            "match_number": match_number,
            "virtual_scout": virtual_data,
        }
    except (DataNotFoundError, ValidationError) as e:
        return {
            "status": "error",
            "message": str(e),
        }


def preview_virtual_scout(
    unified_dataset_path: str,
    team_number: int,
    match_number: int
) -> Dict[str, Any]:
    """
    Legacy function for previewing virtual scout.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        match_number: Match number
        
    Returns:
        Dict with virtual scout preview
    """
    try:
        virtual_scout = _validation_service.create_virtual_scout(
            unified_dataset_path, team_number, match_number, preview_only=True
        )
        
        # Convert to legacy format
        virtual_data = virtual_scout.data.copy()
        virtual_data.update({
            "team_number": virtual_scout.team_number,
            "match_number": virtual_scout.match_number,
            "qual_number": virtual_scout.qual_number,
            "alliance_color": virtual_scout.alliance_color,
            "is_virtual_scout": virtual_scout.is_virtual_scout,
        })
        
        return {
            "status": "success",
            "message": "Virtual scout preview generated",
            "virtual_scout_preview": virtual_data,
            "adjustment_info": virtual_scout.adjustment_info or {
                "has_tba_match_data": False,
                "tba_match_score": None,
                "average_alliance_score": None,
                "adjustment_ratio": None,
            },
        }
    except (DataNotFoundError, ValidationError) as e:
        return {
            "status": "error",
            "message": str(e),
        }


def add_to_todo_list(
    unified_dataset_path: str,
    team_number: int,
    match_number: int
) -> Dict[str, Any]:
    """
    Legacy function for adding to todo list.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        match_number: Match number
        
    Returns:
        Dict with operation result
    """
    try:
        todo_item = _validation_service.manage_todo(
            unified_dataset_path,
            "add",
            team_number=team_number,
            match_number=match_number
        )
        
        return {
            "status": "success",
            "message": "Added to to-do list successfully",
            "team_number": team_number,
            "match_number": match_number,
        }
    except ValidationError as e:
        return {
            "status": "error",
            "message": str(e),
        }


def get_todo_list(unified_dataset_path: str) -> Dict[str, Any]:
    """
    Legacy function for getting todo list.
    
    Args:
        unified_dataset_path: Path to unified dataset
        
    Returns:
        Dict with todo list
    """
    try:
        todo_items = _validation_service.manage_todo(unified_dataset_path, "get")
        
        # Convert to legacy format
        legacy_items = []
        for item in todo_items:
            legacy_items.append({
                "team_number": item.team_number,
                "match_number": item.match_number,
                "added_timestamp": item.added_timestamp.isoformat(),
                "status": item.status.value,
            })
        
        return {
            "status": "success",
            "todo_list": legacy_items,
        }
    except Exception:
        return {
            "status": "success",
            "todo_list": [],
        }


def update_todo_status(
    unified_dataset_path: str,
    team_number: int,
    match_number: int,
    new_status: str
) -> Dict[str, Any]:
    """
    Legacy function for updating todo status.
    
    Args:
        unified_dataset_path: Path to unified dataset
        team_number: Team number
        match_number: Match number
        new_status: New status
        
    Returns:
        Dict with operation result
    """
    try:
        todo_item = _validation_service.manage_todo(
            unified_dataset_path,
            "update",
            team_number=team_number,
            match_number=match_number,
            status=new_status
        )
        
        return {
            "status": "success",
            "message": "To-do list entry updated successfully",
            "team_number": team_number,
            "match_number": match_number,
            "new_status": new_status,
        }
    except ValidationError as e:
        return {
            "status": "error",
            "message": str(e),
        }


# Additional helper functions for legacy compatibility

def calculate_z_scores(values: List[float]) -> List[float]:
    """Legacy z-score calculation function."""
    import numpy as np
    
    if len(values) < 2:
        return [0.0] * len(values)
    
    values_array = np.array(values, dtype=float)
    mean = np.mean(values_array)
    std = np.std(values_array)
    
    if std == 0:
        return [0.0] * len(values)
    
    return list((values_array - mean) / std)


def calculate_iqr_bounds(values: List[float]) -> Tuple[float, float]:
    """Legacy IQR bounds calculation function."""
    import numpy as np
    
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    return lower_bound, upper_bound