# backend/app/services/performance_optimization_service.py

import hashlib
import logging
import time
import statistics
from typing import Any, Dict, List, Optional

logger = logging.getLogger("performance_optimization_service")


class PerformanceOptimizationService:
    """
    Service for optimizing team data and token usage.
    Restored from original system algorithms.
    """
    
    def __init__(self, cache_instance=None):
        """Initialize with cache reference for result storage."""
        self._cache = cache_instance or {}
        
    def condense_team_data_for_gpt(self, teams_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ORIGINAL TEAM DATA CONDENSATION - EXACT RESTORATION"""
        
        condensed_teams = []
        
        for team_data in teams_data:
            condensed_team = {
                "team_number": team_data["team_number"],
                "nickname": team_data.get("nickname", f"Team {team_data['team_number']}")
            }
            
            # ORIGINAL METRICS CONDENSATION
            if "scouting_data" in team_data and team_data["scouting_data"]:
                condensed_team["metrics"] = self._condense_metrics(team_data["scouting_data"])
            elif "metrics" in team_data:
                # Already condensed metrics
                condensed_team["metrics"] = team_data["metrics"]
            
            # ORIGINAL STATBOTICS INTEGRATION
            if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
                for key, value in team_data["statbotics"].items():
                    condensed_team[f"statbotics_{key}"] = value
            
            # ORIGINAL SUPERSCOUTING LIMITATION (1 note max)
            if "superscouting" in team_data and team_data["superscouting"]:
                notes = team_data["superscouting"]
                if isinstance(notes, list) and notes:
                    condensed_team["superscouting"] = notes[0][:100]  # Take only first note, limit to 100 chars
                elif isinstance(notes, str):
                    condensed_team["superscouting"] = notes[:100]  # Limit to 100 chars
            
            condensed_teams.append(condensed_team)
        
        logger.debug(f"Condensed {len(teams_data)} teams for GPT processing")
        return condensed_teams

    def _condense_metrics(self, scouting_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """ORIGINAL METRICS AVERAGING - EXACT RESTORATION"""
        
        if not scouting_data:
            return {}
        
        # ORIGINAL ESSENTIAL FIELDS ONLY
        essential_fields = [
            "auto_points", "teleop_points", "endgame_points",
            "auto_mobility", "auto_docking", "teleop_scoring_rate",
            "defense_rating", "driver_skill", "consistency_rating",
            "auto_gamepieces", "teleop_gamepieces", "endgame_climb",
            "penalty_count", "foul_count", "tech_foul_count"
        ]
        
        metrics = {}
        for field in essential_fields:
            values = []
            for match in scouting_data:
                if isinstance(match.get(field), (int, float)):
                    values.append(match[field])
            
            if values:
                # Use median for more robust average with outliers
                if len(values) >= 3:
                    metrics[field] = round(statistics.median(values), 2)
                else:
                    metrics[field] = round(sum(values) / len(values), 2)
        
        return metrics

    def calculate_weighted_score(self, team_data: Dict[str, Any], priorities: List[Dict[str, Any]]) -> float:
        """ORIGINAL WEIGHTED SCORING - EXACT RESTORATION"""
        
        if not priorities:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for priority in priorities:
            field_name = priority.get("id", "")
            weight = priority.get("weight", 1.0)
            
            # ORIGINAL FIELD MAPPING
            field_value = self._extract_field_value(team_data, field_name)
            
            if field_value is not None:
                total_score += field_value * weight
                total_weight += weight
        
        return round(total_score / total_weight if total_weight > 0 else 0.0, 2)

    def _extract_field_value(self, team_data: Dict[str, Any], field_name: str) -> Optional[float]:
        """ORIGINAL FIELD EXTRACTION LOGIC - EXACT RESTORATION"""
        
        # Try metrics first (most common location)
        if "metrics" in team_data and isinstance(team_data["metrics"], dict):
            if field_name in team_data["metrics"]:
                try:
                    return float(team_data["metrics"][field_name])
                except (ValueError, TypeError):
                    pass
        
        # Try statbotics fields
        if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
            if field_name in team_data["statbotics"]:
                try:
                    return float(team_data["statbotics"][field_name])
                except (ValueError, TypeError):
                    pass
        
        # Try statbotics with prefix
        statbotics_field = f"statbotics_{field_name}"
        if statbotics_field in team_data:
            try:
                return float(team_data[statbotics_field])
            except (ValueError, TypeError):
                pass
        
        # Try direct field access
        if field_name in team_data:
            try:
                return float(team_data[field_name])
            except (ValueError, TypeError):
                pass
        
        # Handle common field mappings
        field_mappings = {
            "auto": "auto_points",
            "teleop": "teleop_points", 
            "endgame": "endgame_points",
            "defense": "defense_rating",
            "consistency": "consistency_rating"
        }
        
        if field_name in field_mappings:
            return self._extract_field_value(team_data, field_mappings[field_name])
        
        return None

    def estimate_token_usage(
        self, 
        teams_count: int, 
        priorities_count: int, 
        use_ultra_compact: bool = True,
        has_game_context: bool = False
    ) -> Dict[str, int]:
        """ORIGINAL TOKEN ESTIMATION - EXACT RESTORATION"""
        
        # ORIGINAL TOKEN ESTIMATION FORMULAS
        base_system_tokens = 200 if use_ultra_compact else 400
        base_user_tokens = 150
        
        # ORIGINAL PER-TEAM TOKEN COSTS
        tokens_per_team = 25 if use_ultra_compact else 45
        tokens_per_priority = 15
        
        # Game context adds tokens
        game_context_tokens = 100 if has_game_context else 0
        
        estimated_input = (
            base_system_tokens + 
            base_user_tokens + 
            (teams_count * tokens_per_team) + 
            (priorities_count * tokens_per_priority) +
            game_context_tokens
        )
        
        # ORIGINAL OUTPUT ESTIMATION
        estimated_output = teams_count * (8 if use_ultra_compact else 15)
        
        total_tokens = estimated_input + estimated_output
        
        # Add safety margin
        total_with_margin = int(total_tokens * 1.1)
        
        return {
            "input_tokens": estimated_input,
            "output_tokens": estimated_output,
            "total_tokens": total_tokens,
            "total_with_margin": total_with_margin,
            "optimization_used": "ultra_compact" if use_ultra_compact else "standard",
            "within_limits": total_with_margin < 100000
        }

    def should_use_batching(self, teams_count: int, priorities_count: int) -> bool:
        """ORIGINAL BATCHING DECISION LOGIC"""
        
        # Estimate token usage
        estimation = self.estimate_token_usage(teams_count, priorities_count, use_ultra_compact=True)
        
        # ORIGINAL DECISION FACTORS
        # 1. Team count threshold (primary)
        if teams_count > 20:
            return True
        
        # 2. Token limit threshold (secondary) 
        if estimation["total_with_margin"] > 80000:  # 80% of limit
            return True
        
        # 3. Priority complexity (tertiary)
        if priorities_count > 6:
            return True
        
        return False

    def get_optimal_processing_strategy(
        self, 
        teams_count: int, 
        priorities_count: int,
        user_preference: Optional[bool] = None
    ) -> Dict[str, Any]:
        """COMPREHENSIVE PROCESSING STRATEGY RECOMMENDATION"""
        
        # Calculate recommendations
        auto_batch_recommended = self.should_use_batching(teams_count, priorities_count)
        token_estimation = self.estimate_token_usage(teams_count, priorities_count)
        
        # Determine final strategy
        if user_preference is not None:
            use_batching = user_preference
            strategy_source = "user_specified"
        else:
            use_batching = auto_batch_recommended
            strategy_source = "auto_determined"
        
        # Calculate batch parameters if batching
        batch_size = 20
        if use_batching:
            # Adjust batch size based on priorities
            if priorities_count > 5:
                batch_size = 18
            elif priorities_count > 3:
                batch_size = 19
            else:
                batch_size = 20
        
        return {
            "use_batching": use_batching,
            "strategy_source": strategy_source,
            "batch_size": batch_size,
            "estimated_batches": (teams_count // batch_size) + (1 if teams_count % batch_size else 0) if use_batching else 1,
            "token_estimation": token_estimation,
            "recommendations": {
                "auto_batch_recommended": auto_batch_recommended,
                "reason": self._get_strategy_reason(teams_count, priorities_count, auto_batch_recommended)
            }
        }

    def _get_strategy_reason(self, teams_count: int, priorities_count: int, recommended_batching: bool) -> str:
        """Explain why a strategy was recommended"""
        
        if recommended_batching:
            reasons = []
            if teams_count > 20:
                reasons.append(f"team count ({teams_count}) exceeds threshold (20)")
            
            estimation = self.estimate_token_usage(teams_count, priorities_count)
            if estimation["total_with_margin"] > 80000:
                reasons.append(f"token usage ({estimation['total_with_margin']}) near limit")
            
            if priorities_count > 6:
                reasons.append(f"high priority complexity ({priorities_count})")
            
            return f"Batching recommended: {', '.join(reasons)}"
        else:
            return f"Single processing optimal: {teams_count} teams with {priorities_count} priorities fits comfortably"

    def generate_cache_key(
        self,
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        exclude_teams: Optional[List[int]] = None,
        team_count: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate deterministic cache key."""
        import json
        sorted_params = json.dumps({
            "team": your_team_number,
            "position": pick_position,
            "priorities": priorities,
            "exclude": exclude_teams or [],
            "count": team_count
        }, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()[:16]

    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result"""
        if self._cache is not None and cache_key in self._cache:
            logger.debug(f"Retrieved cached result for key: {cache_key}")
            return self._cache[cache_key]
        return None

    def store_cached_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Store result in performance cache"""
        if self._cache is not None:
            self._cache[cache_key] = result
            logger.debug(f"Cached result for key: {cache_key}")

    def mark_cache_processing(self, cache_key: str) -> None:
        """Mark a cache key as currently being processed."""
        if self._cache is not None:
            self._cache[cache_key] = time.time()
            logger.debug(f"Marked cache key as processing: {cache_key}")