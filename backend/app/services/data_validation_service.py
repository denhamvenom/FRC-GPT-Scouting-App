# backend/app/services/data_validation_service.py

import json
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime


def load_unified_dataset(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_event_completeness(unified_dataset_path: str) -> Dict:
    """
    Validate completeness of the unified dataset by checking for missing data.
    This function checks if all expected match/team combinations have scouting data.
    """
    dataset = load_unified_dataset(unified_dataset_path)

    expected_matches = dataset.get("expected_matches", [])
    teams_data = dataset.get("teams", {})

    scouting_records = set()
    superscouted_teams = set()

    # Build scouted records
    for team_number, team_data in teams_data.items():
        team_number_int = None
        try:
            team_number_int = int(team_number)
        except ValueError:
            continue  # Skip if team_number can't be converted to int
            
        for match in team_data.get("scouting_data", []):
            if "qual_number" in match:
                try:
                    qual_number = int(match["qual_number"])
                    scouting_records.add((qual_number, team_number_int))
                except (ValueError, TypeError):
                    # Try with match_number if qual_number is not an integer
                    if "match_number" in match:
                        try:
                            match_number = int(match["match_number"])
                            scouting_records.add((match_number, team_number_int))
                        except (ValueError, TypeError):
                            # Skip if neither qual_number nor match_number are valid integers
                            continue
            elif "match_number" in match:
                try:
                    match_number = int(match["match_number"])
                    scouting_records.add((match_number, team_number_int))
                except (ValueError, TypeError):
                    continue  # Skip if match_number is not a valid integer

        for superscout_entry in team_data.get("superscouting_data", []):
            team_num_raw = superscout_entry.get("team_number")
            if team_num_raw is None:
                continue
            try:
                team_num = int(team_num_raw)
                superscouted_teams.add(team_num)
            except ValueError:
                continue

    # Build expected sets
    expected_match_records = set()
    expected_team_numbers = set()
    
    for entry in expected_matches:
        match_number = entry.get("match_number")
        team_number = entry.get("team_number")
        
        if match_number is not None and team_number is not None:
            try:
                match_number_int = int(match_number)
                team_number_int = int(team_number)
                expected_match_records.add((match_number_int, team_number_int))
                expected_team_numbers.add(team_number_int)
            except (ValueError, TypeError):
                # Skip if either match_number or team_number can't be converted to integers
                continue

    missing_scouting = expected_match_records - scouting_records
    missing_superscouting = expected_team_numbers - superscouted_teams

    status = "complete" if not missing_scouting and not missing_superscouting else "partial"

    return {
        "missing_scouting": [{"match_number": m[0], "team_number": m[1]} for m in sorted(missing_scouting)],
        "missing_superscouting": [{"team_number": team} for team in sorted(missing_superscouting)],
        "status": status,
        "scouting_records_count": len(scouting_records),
        "expected_match_records_count": len(expected_match_records)
    }


def calculate_z_scores(values: List[float]) -> List[float]:
    """Calculate z-scores for a list of values."""
    if len(values) < 2:
        return [0.0] * len(values)  # Not enough data to calculate meaningful z-scores
    
    values_array = np.array(values, dtype=float)
    mean = np.mean(values_array)
    std = np.std(values_array)
    
    if std == 0:
        return [0.0] * len(values)  # Avoid division by zero
    
    return list((values_array - mean) / std)


def calculate_iqr_bounds(values: List[float]) -> Tuple[float, float]:
    """Calculate the IQR bounds for outlier detection."""
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    return lower_bound, upper_bound


def validate_event_with_outliers(unified_dataset_path: str, z_score_threshold: float = 3.0) -> Dict[str, Any]:
    """
    Comprehensive validation of the unified dataset.
    Checks for both missing data and statistical outliers.
    """
    # Get completeness validation results first
    completeness_results = validate_event_completeness(unified_dataset_path)
    
    # Load dataset for outlier detection
    dataset = load_unified_dataset(unified_dataset_path)
    teams_data = dataset.get("teams", {})
    
    # Record of all numeric scouting data for outlier detection
    all_numeric_data = {}
    team_numeric_data = {}
    
    # Collect numeric data for outlier detection
    for team_number, team_data in teams_data.items():
        try:
            team_number_int = int(team_number)
        except ValueError:
            continue  # Skip if team_number can't be converted to int
            
        team_numeric_data[team_number_int] = {}
        
        for match in team_data.get("scouting_data", []):
            match_number = None
            
            # Try to get match_number or qual_number
            if "qual_number" in match:
                try:
                    match_number = int(match["qual_number"])
                except (ValueError, TypeError):
                    pass
                    
            if match_number is None and "match_number" in match:
                try:
                    match_number = int(match["match_number"])
                except (ValueError, TypeError):
                    continue  # Skip if neither qual_number nor match_number are valid integers
            
            if match_number is None:
                continue  # Skip if no valid match number found
                
            # Collect numeric data for outlier detection
            for key, value in match.items():
                if isinstance(value, (int, float)) and key not in ["qual_number", "match_number", "team_number"]:
                    if key not in all_numeric_data:
                        all_numeric_data[key] = []
                    if key not in team_numeric_data[team_number_int]:
                        team_numeric_data[team_number_int][key] = []
                        
                    all_numeric_data[key].append(value)
                    team_numeric_data[team_number_int][key].append((match_number, value))
    
    # Identify outliers
    outliers = {}
    
    # Global outliers (compared to all teams)
    for metric, values in all_numeric_data.items():
        if len(values) < 5:  # Skip metrics with too few data points
            continue
            
        # Z-score method
        z_scores = calculate_z_scores(values)
        for team_number, team_metrics in team_numeric_data.items():
            if metric in team_metrics:
                for match_idx, (match_number, value) in enumerate(team_metrics[metric]):
                    # Find index of this value in all_numeric_data
                    try:
                        # Find the first occurrence of this value
                        indices = [i for i, x in enumerate(all_numeric_data[metric]) if x == value]
                        if indices:
                            value_idx = indices[0]
                            z_score = z_scores[value_idx]
                            
                            if abs(z_score) > z_score_threshold:
                                if team_number not in outliers:
                                    outliers[team_number] = {}
                                if match_number not in outliers[team_number]:
                                    outliers[team_number][match_number] = []
                                    
                                outliers[team_number][match_number].append({
                                    "metric": metric,
                                    "value": value,
                                    "z_score": z_score,
                                    "detection_method": "z_score"
                                })
                    except (ValueError, IndexError) as e:
                        # Skip if value can't be found in all_numeric_data
                        continue
        
        # IQR method
        lower_bound, upper_bound = calculate_iqr_bounds(values)
        for team_number, team_metrics in team_numeric_data.items():
            if metric in team_metrics:
                for match_number, value in team_metrics[metric]:
                    if value < lower_bound or value > upper_bound:
                        if team_number not in outliers:
                            outliers[team_number] = {}
                        if match_number not in outliers[team_number]:
                            outliers[team_number][match_number] = []
                            
                        # Only add if not already added by z-score method
                        if not any(o["metric"] == metric for o in outliers.get(team_number, {}).get(match_number, [])):
                            outliers[team_number][match_number].append({
                                "metric": metric,
                                "value": value,
                                "bounds": [lower_bound, upper_bound],
                                "detection_method": "iqr"
                            })
    
    # Team-specific outliers (compared to team's own performance)
    for team_number, team_metrics in team_numeric_data.items():
        for metric, match_values in team_metrics.items():
            if len(match_values) < 3:  # Skip metrics with too few data points
                continue
                
            values = [v for _, v in match_values]
            team_z_scores = calculate_z_scores(values)
            
            for idx, ((match_number, value), z_score) in enumerate(zip(match_values, team_z_scores)):
                if abs(z_score) > z_score_threshold:
                    if team_number not in outliers:
                        outliers[team_number] = {}
                    if match_number not in outliers[team_number]:
                        outliers[team_number][match_number] = []
                        
                    # Only add if not already added by other methods
                    if not any(o["metric"] == metric for o in outliers.get(team_number, {}).get(match_number, [])):
                        outliers[team_number][match_number].append({
                            "metric": metric,
                            "value": value,
                            "team_z_score": z_score,
                            "detection_method": "team_specific"
                        })
    
    # Format the results
    outliers_list = []
    for team_number, matches in outliers.items():
        for match_number, issues in matches.items():
            outliers_list.append({
                "team_number": team_number,
                "match_number": match_number,
                "issues": issues
            })
    
    # Determine overall status
    missing_scouting = completeness_results["missing_scouting"]
    missing_superscouting = completeness_results["missing_superscouting"]
    has_issues = missing_scouting or missing_superscouting or outliers_list
    status = "complete" if not has_issues else "issues_found"
    
    return {
        "missing_scouting": missing_scouting,
        "missing_superscouting": missing_superscouting,
        "outliers": outliers_list,
        "status": status,
        "summary": {
            "total_missing_matches": len(missing_scouting),
            "total_missing_superscouting": len(missing_superscouting),
            "total_outliers": len(outliers_list),
            "has_issues": has_issues,
            "scouting_records_count": completeness_results.get("scouting_records_count", 0),
            "expected_match_records_count": completeness_results.get("expected_match_records_count", 0)
        }
    }


def get_team_averages(unified_dataset_path: str, team_number: int) -> Dict[str, float]:
    """
    Calculate a team's average metrics for potential replacement of outliers.
    """
    dataset = load_unified_dataset(unified_dataset_path)
    teams_data = dataset.get("teams", {})
    
    if str(team_number) not in teams_data:
        return {}
    
    team_data = teams_data[str(team_number)]
    scouting_data = team_data.get("scouting_data", [])
    
    if not scouting_data:
        return {}
    
    # Collect all numeric metrics
    metrics = {}
    for match in scouting_data:
        for key, value in match.items():
            if isinstance(value, (int, float)) and key not in ["qual_number", "match_number", "team_number"]:
                if key not in metrics:
                    metrics[key] = []
                metrics[key].append(value)
    
    # Calculate averages
    averages = {}
    for key, values in metrics.items():
        averages[key] = np.mean(values)
    
    return averages


def suggest_corrections(unified_dataset_path: str, team_number: int, match_number: int) -> Dict[str, Any]:
    """
    Suggest corrections for outliers based on team averages and common values.
    """
    # Get validation results
    validation_results = validate_event_with_outliers(unified_dataset_path)
    
    # Find outliers for this team and match
    team_match_outliers = None
    for outlier in validation_results.get("outliers", []):
        if outlier["team_number"] == team_number and outlier["match_number"] == match_number:
            team_match_outliers = outlier
            break
    
    if not team_match_outliers:
        return {"status": "no_outliers_found"}
    
    # Calculate team averages
    team_averages = get_team_averages(unified_dataset_path, team_number)
    
    # Prepare suggestions
    suggestions = []
    for issue in team_match_outliers.get("issues", []):
        metric = issue["metric"]
        current_value = issue["value"]
        
        suggestion = {
            "metric": metric,
            "current_value": current_value,
            "suggested_corrections": []
        }
        
        # Suggest team average
        if metric in team_averages:
            avg_value = team_averages[metric]
            suggestion["suggested_corrections"].append({
                "value": round(avg_value, 2) if isinstance(avg_value, float) else avg_value,
                "method": "team_average"
            })
        
        # Suggest reasonable bounds
        if "bounds" in issue:
            lower_bound, upper_bound = issue["bounds"]
            if current_value < lower_bound:
                suggestion["suggested_corrections"].append({
                    "value": round(lower_bound, 2) if isinstance(lower_bound, float) else lower_bound,
                    "method": "minimum_reasonable"
                })
            elif current_value > upper_bound:
                suggestion["suggested_corrections"].append({
                    "value": round(upper_bound, 2) if isinstance(upper_bound, float) else upper_bound,
                    "method": "maximum_reasonable"
                })
        
        # Add 0 as a potential correction for numeric fields
        # (often used when scouters mistake was to record an action that didn't happen)
        if current_value != 0:
            suggestion["suggested_corrections"].append({
                "value": 0,
                "method": "zero"
            })
        
        suggestions.append(suggestion)
    
    return {
        "status": "suggestions_found",
        "team_number": team_number,
        "match_number": match_number,
        "suggestions": suggestions
    }


def apply_correction(unified_dataset_path: str, team_number: int, match_number: int, 
                     corrections: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    """
    Apply corrections to the unified dataset.
    """
    dataset = load_unified_dataset(unified_dataset_path)
    teams_data = dataset.get("teams", {})
    
    if str(team_number) not in teams_data:
        return {"status": "error", "message": "Team not found"}
    
    team_data = teams_data[str(team_number)]
    scouting_data = team_data.get("scouting_data", [])
    
    # Find the match data
    match_idx = None
    for idx, match in enumerate(scouting_data):
        # Check for either qual_number or match_number
        match_num_found = False
        
        if "qual_number" in match:
            try:
                if int(match["qual_number"]) == int(match_number):
                    match_idx = idx
                    match_num_found = True
            except (ValueError, TypeError):
                pass
        
        if not match_num_found and "match_number" in match:
            try:
                if int(match["match_number"]) == int(match_number):
                    match_idx = idx
            except (ValueError, TypeError):
                pass
    
    if match_idx is None:
        return {"status": "error", "message": "Match not found"}
    
    # Apply corrections
    for metric, value in corrections.items():
        if metric in scouting_data[match_idx]:
            # Record the original value for audit purposes
            if "correction_history" not in scouting_data[match_idx]:
                scouting_data[match_idx]["correction_history"] = []
            
            scouting_data[match_idx]["correction_history"].append({
                "metric": metric,
                "original_value": scouting_data[match_idx][metric],
                "corrected_value": value,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            
            # Apply the correction
            scouting_data[match_idx][metric] = value
    
    # Ensure match_number and qual_number are consistent after corrections
    if "match_number" in scouting_data[match_idx] and "qual_number" not in scouting_data[match_idx]:
        scouting_data[match_idx]["qual_number"] = scouting_data[match_idx]["match_number"]
    elif "qual_number" in scouting_data[match_idx] and "match_number" not in scouting_data[match_idx]:
        scouting_data[match_idx]["match_number"] = scouting_data[match_idx]["qual_number"]
    
    # Save the updated dataset
    with open(unified_dataset_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    
    return {
        "status": "success",
        "message": "Corrections applied successfully",
        "team_number": team_number,
        "match_number": match_number
    }