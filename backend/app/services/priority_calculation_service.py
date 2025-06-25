# backend/app/services/priority_calculation_service.py

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("priority_calculation_service")


class PriorityCalculationService:
    """
    Service for handling multi-criteria scoring and preference management.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    """

    def __init__(self):
        """Initialize the priority calculation service."""
        pass

    def normalize_priorities(self, priorities: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Normalize priority weights and convert to standard format.
        
        Args:
            priorities: Dictionary of priority names to weights
            
        Returns:
            List of normalized priority dictionaries
        """
        if not priorities:
            return []

        total_weight = sum(priorities.values())
        if total_weight <= 0:
            logger.warning("Total priority weight is zero or negative")
            return []

        normalized_priorities = []
        for name, weight in priorities.items():
            if weight > 0:
                normalized_weight = weight / total_weight
                normalized_priorities.append({
                    "name": name,
                    "weight": normalized_weight,
                    "original_weight": weight,
                    "description": self._get_priority_description(name)
                })

        # Sort by weight (highest first)
        normalized_priorities.sort(key=lambda x: x["weight"], reverse=True)
        
        return normalized_priorities

    def _get_priority_description(self, priority_name: str) -> str:
        """
        Get description for common priority names.
        
        Args:
            priority_name: Name of the priority
            
        Returns:
            Description of the priority
        """
        descriptions = {
            "autonomous": "Performance during autonomous period",
            "teleop": "Performance during teleoperated period",
            "endgame": "Performance during endgame period",
            "defense": "Defensive capabilities and strategy",
            "reliability": "Consistency and reliability of performance",
            "speed": "Speed and efficiency of actions",
            "accuracy": "Precision and accuracy of scoring",
            "versatility": "Ability to perform multiple roles",
            "climbing": "Climbing and endgame positioning",
            "cooperation": "Teamwork and alliance cooperation",
            "innovation": "Unique strategies and innovations",
            "experience": "Team experience and track record"
        }
        
        return descriptions.get(priority_name.lower(), f"Priority for {priority_name}")

    def calculate_multi_criteria_score(
        self,
        team_metrics: Dict[str, float],
        priorities: List[Dict[str, Any]],
        scoring_method: str = "weighted_sum"
    ) -> Dict[str, Any]:
        """
        Calculate multi-criteria score for a team based on metrics and priorities.
        
        Args:
            team_metrics: Dictionary of team performance metrics
            priorities: List of priority weights
            scoring_method: Method to use for scoring calculation
            
        Returns:
            Dictionary with score and detailed breakdown
        """
        if not team_metrics or not priorities:
            return {
                "total_score": 0.0,
                "breakdown": {},
                "method": scoring_method,
                "metrics_used": 0,
                "coverage": 0.0
            }

        if scoring_method == "weighted_sum":
            return self._calculate_weighted_sum_score(team_metrics, priorities)
        elif scoring_method == "topsis":
            return self._calculate_topsis_score(team_metrics, priorities)
        elif scoring_method == "normalized_weighted":
            return self._calculate_normalized_weighted_score(team_metrics, priorities)
        else:
            logger.warning(f"Unknown scoring method: {scoring_method}, using weighted_sum")
            return self._calculate_weighted_sum_score(team_metrics, priorities)

    def _calculate_weighted_sum_score(
        self,
        team_metrics: Dict[str, float],
        priorities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate score using weighted sum method.
        
        Args:
            team_metrics: Team performance metrics
            priorities: Priority weights
            
        Returns:
            Score calculation result
        """
        total_score = 0.0
        total_weight = 0.0
        breakdown = {}
        metrics_used = 0

        for priority in priorities:
            metric_name = priority.get("name", "")
            weight = priority.get("weight", 0.0)
            
            if metric_name in team_metrics and weight > 0:
                value = team_metrics[metric_name]
                
                # Normalize value (assume 0-100 scale for most metrics)
                normalized_value = self._normalize_metric_value(metric_name, value)
                
                contribution = normalized_value * weight
                total_score += contribution
                total_weight += weight
                metrics_used += 1
                
                breakdown[metric_name] = {
                    "raw_value": value,
                    "normalized_value": normalized_value,
                    "weight": weight,
                    "contribution": round(contribution, 2)
                }

        # Calculate final score
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.0

        # Calculate coverage (percentage of priorities that had matching metrics)
        coverage = metrics_used / len(priorities) if priorities else 0.0

        return {
            "total_score": round(final_score, 2),
            "breakdown": breakdown,
            "method": "weighted_sum",
            "metrics_used": metrics_used,
            "total_priorities": len(priorities),
            "coverage": round(coverage, 2),
            "total_weight_used": round(total_weight, 3)
        }

    def _calculate_normalized_weighted_score(
        self,
        team_metrics: Dict[str, float],
        priorities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate score using normalized weighted method with z-score normalization.
        
        Args:
            team_metrics: Team performance metrics
            priorities: Priority weights
            
        Returns:
            Score calculation result
        """
        # This would typically require population statistics for z-score normalization
        # For now, use simple min-max normalization
        return self._calculate_weighted_sum_score(team_metrics, priorities)

    def _calculate_topsis_score(
        self,
        team_metrics: Dict[str, float],
        priorities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate score using TOPSIS (Technique for Order Preference by Similarity to Ideal Solution).
        
        Args:
            team_metrics: Team performance metrics
            priorities: Priority weights
            
        Returns:
            Score calculation result
        """
        # Simplified TOPSIS implementation
        # In a full implementation, this would require the full set of alternatives
        return self._calculate_weighted_sum_score(team_metrics, priorities)

    def _normalize_metric_value(self, metric_name: str, value: float) -> float:
        """
        Normalize a metric value based on its type and expected range.
        
        Args:
            metric_name: Name of the metric
            value: Raw metric value
            
        Returns:
            Normalized value (0-100 scale)
        """
        # Define metric-specific normalization rules
        metric_ranges = {
            # Standard FRC metrics (0-100 range)
            "autonomous": (0, 100),
            "teleop": (0, 100), 
            "endgame": (0, 100),
            "defense": (0, 100),
            "reliability": (0, 100),
            "speed": (0, 100),
            "accuracy": (0, 100),
            
            # Percentage-based metrics (0-1 range, convert to 0-100)
            "climb_success_rate": (0, 1),
            "accuracy_rate": (0, 1),
            
            # Time-based metrics (lower is better)
            "cycle_time": (0, 60),  # seconds
            
            # Count-based metrics
            "auto_points": (0, 50),
            "teleop_points": (0, 200),
            "ranking_points": (0, 4),
        }
        
        if metric_name in metric_ranges:
            min_val, max_val = metric_ranges[metric_name]
            
            # Check if this is a "lower is better" metric
            lower_is_better = metric_name in ["cycle_time", "penalty_count"]
            
            if lower_is_better:
                # Invert the scale for "lower is better" metrics
                if value <= min_val:
                    return 100.0
                elif value >= max_val:
                    return 0.0
                else:
                    return 100.0 * (max_val - value) / (max_val - min_val)
            else:
                # Standard "higher is better" normalization
                if value <= min_val:
                    return 0.0
                elif value >= max_val:
                    return 100.0
                else:
                    return 100.0 * (value - min_val) / (max_val - min_val)
        else:
            # Default normalization - clamp to 0-100 range
            return max(0.0, min(100.0, value))

    def calculate_priority_impact(
        self,
        base_scores: List[Dict[str, Any]],
        modified_priorities: Dict[str, float],
        original_priorities: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate the impact of changing priorities on team rankings.
        
        Args:
            base_scores: List of teams with base scores
            modified_priorities: New priority weights
            original_priorities: Original priority weights
            
        Returns:
            Analysis of priority change impact
        """
        impact_analysis = {
            "priority_changes": {},
            "ranking_changes": {},
            "score_changes": {},
            "top_movers": [],
            "stability_score": 0.0
        }

        # Compare priority changes
        all_priorities = set(original_priorities.keys()) | set(modified_priorities.keys())
        for priority in all_priorities:
            orig_weight = original_priorities.get(priority, 0.0)
            new_weight = modified_priorities.get(priority, 0.0)
            change = new_weight - orig_weight
            
            impact_analysis["priority_changes"][priority] = {
                "original": orig_weight,
                "new": new_weight,
                "change": round(change, 3),
                "percent_change": round((change / orig_weight * 100) if orig_weight > 0 else 0, 1)
            }

        return impact_analysis

    def optimize_priorities(
        self,
        team_performances: List[Dict[str, Any]],
        target_rankings: List[int],
        optimization_method: str = "least_squares"
    ) -> Dict[str, float]:
        """
        Optimize priority weights to best match target rankings.
        
        Args:
            team_performances: List of team performance data
            target_rankings: Desired ranking order (team numbers)
            optimization_method: Method to use for optimization
            
        Returns:
            Optimized priority weights
        """
        # This is a placeholder for a complex optimization algorithm
        # In practice, this would use techniques like:
        # - Least squares optimization
        # - Genetic algorithms
        # - Gradient descent
        # - Linear programming
        
        logger.info(f"Priority optimization requested for {len(team_performances)} teams")
        
        # Return equal weights as a simple baseline
        if team_performances:
            first_team = team_performances[0]
            if "metrics" in first_team:
                metrics = first_team["metrics"].keys()
                weight = 1.0 / len(metrics) if metrics else 0.0
                return {metric: weight for metric in metrics}
        
        return {}

    def create_priority_recommendation(
        self,
        pick_position: str,
        game_strategy: str = "balanced"
    ) -> Dict[str, float]:
        """
        Create recommended priority weights based on pick position and strategy.
        
        Args:
            pick_position: Pick position ("first", "second", "third")
            game_strategy: Overall strategy ("offensive", "defensive", "balanced")
            
        Returns:
            Recommended priority weights
        """
        base_priorities = {
            "autonomous": 0.20,
            "teleop": 0.35,
            "endgame": 0.20,
            "defense": 0.10,
            "reliability": 0.15
        }

        # Adjust based on pick position
        if pick_position == "first":
            # First pick should prioritize high scorers
            base_priorities["teleop"] = 0.40
            base_priorities["autonomous"] = 0.25
            base_priorities["endgame"] = 0.20
            base_priorities["defense"] = 0.05
            base_priorities["reliability"] = 0.10
            
        elif pick_position == "second":
            # Second pick should complement first pick
            base_priorities["defense"] = 0.15
            base_priorities["reliability"] = 0.20
            base_priorities["endgame"] = 0.25
            
        elif pick_position == "third":
            # Third pick should fill gaps and provide defense
            base_priorities["defense"] = 0.25
            base_priorities["reliability"] = 0.25
            base_priorities["endgame"] = 0.15
            base_priorities["teleop"] = 0.25
            base_priorities["autonomous"] = 0.10

        # Adjust based on game strategy
        if game_strategy == "offensive":
            base_priorities["teleop"] *= 1.3
            base_priorities["autonomous"] *= 1.2
            base_priorities["defense"] *= 0.7
            
        elif game_strategy == "defensive":
            base_priorities["defense"] *= 1.5
            base_priorities["reliability"] *= 1.2
            base_priorities["teleop"] *= 0.8
            
        # Normalize to sum to 1.0
        total = sum(base_priorities.values())
        if total > 0:
            for key in base_priorities:
                base_priorities[key] = base_priorities[key] / total

        return base_priorities

    def validate_priorities(self, priorities: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate priority weights for correctness and consistency.
        
        Args:
            priorities: Priority weights to validate
            
        Returns:
            Validation result with any issues found
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }

        if not priorities:
            validation_result["valid"] = False
            validation_result["errors"].append("No priorities provided")
            return validation_result

        # Check for negative weights
        negative_weights = [name for name, weight in priorities.items() if weight < 0]
        if negative_weights:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Negative weights found: {negative_weights}")

        # Check for zero total weight
        total_weight = sum(priorities.values())
        if total_weight <= 0:
            validation_result["valid"] = False
            validation_result["errors"].append("Total weight is zero or negative")

        # Warn about extreme weights
        if total_weight > 0:
            for name, weight in priorities.items():
                percentage = (weight / total_weight) * 100
                if percentage > 70:
                    validation_result["warnings"].append(
                        f"Priority '{name}' has very high weight ({percentage:.1f}%)"
                    )
                elif percentage < 5 and weight > 0:
                    validation_result["warnings"].append(
                        f"Priority '{name}' has very low weight ({percentage:.1f}%)"
                    )

        # Suggest common priorities if missing
        common_priorities = {"autonomous", "teleop", "endgame", "defense", "reliability"}
        missing_common = common_priorities - set(priorities.keys())
        if missing_common:
            validation_result["suggestions"].append(
                f"Consider adding common priorities: {missing_common}"
            )

        return validation_result