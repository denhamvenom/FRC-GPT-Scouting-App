# backend/app/services/team_analysis_service.py

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("team_analysis_service")


class TeamAnalysisService:
    """
    Service for handling team evaluation and ranking algorithms.
    Extracted from monolithic PicklistGeneratorService to improve maintainability.
    """

    def __init__(self, teams_data: Dict[str, Any]):
        """
        Initialize the team analysis service.
        
        Args:
            teams_data: Dictionary of team data from the unified dataset
        """
        self.teams_data = teams_data

    def prepare_team_data_for_analysis(self) -> List[Dict[str, Any]]:
        """
        Prepare team data in a format optimized for analysis and GPT processing.
        
        Returns:
            List of team data formatted for analysis
        """
        formatted_teams = []
        
        for team_number, team_data in self.teams_data.items():
            if isinstance(team_data, dict) and "team_number" in team_data:
                team_info = {
                    "team_number": team_data["team_number"],
                    "nickname": team_data.get("nickname", f"Team {team_data['team_number']}"),
                    "metrics": {},
                    "match_count": 0,
                }

                # Process scouting data if available
                if "scouting_data" in team_data and isinstance(team_data["scouting_data"], list):
                    team_info["metrics"], team_info["match_count"] = self._calculate_average_metrics(
                        team_data["scouting_data"]
                    )

                # Add Statbotics data if available
                if "statbotics" in team_data and isinstance(team_data["statbotics"], dict):
                    for metric, value in team_data["statbotics"].items():
                        if isinstance(value, (int, float)):
                            team_info["metrics"][f"statbotics_{metric}"] = value

                # Add ranking information if available
                if "ranking" in team_data and isinstance(team_data["ranking"], dict):
                    ranking = team_data["ranking"]
                    team_info["rank"] = ranking.get("rank")
                    team_info["record"] = {
                        "wins": ranking.get("wins", 0),
                        "losses": ranking.get("losses", 0),
                        "ties": ranking.get("ties", 0),
                    }

                # Add limited superscouting notes for context
                if "superscouting" in team_data and isinstance(team_data["superscouting"], list):
                    # Include only the first note to manage token usage
                    if team_data["superscouting"]:
                        team_info["superscouting_notes"] = [team_data["superscouting"][0]]

                formatted_teams.append(team_info)

        return formatted_teams

    def _calculate_average_metrics(self, scouting_data: List[Dict[str, Any]]) -> tuple[Dict[str, float], int]:
        """
        Calculate average metrics from scouting data across multiple matches.
        
        Args:
            scouting_data: List of match scouting data
            
        Returns:
            Tuple of (average_metrics, match_count)
        """
        metrics_sum = {}
        metrics_count = {}
        match_count = len(scouting_data)

        for match_data in scouting_data:
            if isinstance(match_data, dict):
                for key, value in match_data.items():
                    # Skip non-numeric fields
                    if key in ["team_number", "match_number", "alliance_color", "notes"]:
                        continue
                        
                    if isinstance(value, (int, float)):
                        if key not in metrics_sum:
                            metrics_sum[key] = 0
                            metrics_count[key] = 0
                        metrics_sum[key] += value
                        metrics_count[key] += 1

        # Calculate averages
        average_metrics = {}
        for metric in metrics_sum:
            if metrics_count[metric] > 0:
                average_metrics[metric] = round(metrics_sum[metric] / metrics_count[metric], 2)

        return average_metrics, match_count

    def calculate_weighted_score(
        self, 
        team_data: Dict[str, Any], 
        priorities: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate weighted score for a team based on metrics and priorities.
        
        Args:
            team_data: Team data with metrics
            priorities: List of priority weights
            
        Returns:
            Weighted score for the team
        """
        if "metrics" not in team_data or not isinstance(team_data["metrics"], dict):
            return 0.0

        metrics = team_data["metrics"]
        total_score = 0.0
        total_weight = 0.0

        for priority in priorities:
            if not isinstance(priority, dict):
                continue
                
            metric_name = priority.get("name", "")
            weight = priority.get("weight", 0.0)
            
            if metric_name in metrics and isinstance(weight, (int, float)) and weight > 0:
                value = metrics[metric_name]
                
                # Simple normalization (assumes higher values are better)
                # In a real implementation, you might want different normalization strategies
                # based on the metric type
                normalized_value = max(0, min(100, value))  # Clamp to 0-100 range
                
                total_score += normalized_value * weight
                total_weight += weight

        if total_weight > 0:
            return round(total_score / total_weight, 2)
        else:
            return 0.0

    def calculate_similarity_score(
        self, 
        team1_metrics: Dict[str, float], 
        team2_metrics: Dict[str, float]
    ) -> float:
        """
        Calculate similarity score between two teams based on their metrics.
        
        Args:
            team1_metrics: Metrics for first team
            team2_metrics: Metrics for second team
            
        Returns:
            Similarity score between 0.0 and 1.0 (higher = more similar)
        """
        if not team1_metrics or not team2_metrics:
            return 0.0

        # Find common metrics
        common_metrics = set(team1_metrics.keys()) & set(team2_metrics.keys())
        
        if not common_metrics:
            return 0.0

        total_similarity = 0.0
        metric_count = 0

        for metric in common_metrics:
            value1 = team1_metrics[metric]
            value2 = team2_metrics[metric]
            
            # Handle zero values
            if value1 == 0 and value2 == 0:
                similarity = 1.0
            else:
                max_val = max(abs(value1), abs(value2))
                if max_val > 0:
                    diff = abs(value1 - value2) / max_val
                    similarity = 1.0 - min(diff, 1.0)
                else:
                    similarity = 1.0

            total_similarity += similarity
            metric_count += 1

        return round(total_similarity / metric_count, 3) if metric_count > 0 else 0.0

    def get_team_by_number(self, team_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve team data by team number.
        
        Args:
            team_number: Team number to search for
            
        Returns:
            Team data dictionary or None if not found
        """
        # Search in the formatted teams data
        for team_key, team_data in self.teams_data.items():
            if isinstance(team_data, dict) and team_data.get("team_number") == team_number:
                return team_data
        
        return None

    def rank_teams_by_score(
        self, 
        teams: List[Dict[str, Any]], 
        priorities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank teams by their weighted scores.
        
        Args:
            teams: List of team data
            priorities: Priority weights for scoring
            
        Returns:
            List of teams ranked by score (highest first)
        """
        ranked_teams = []
        
        for team in teams:
            team_copy = team.copy()
            team_copy["calculated_score"] = self.calculate_weighted_score(team, priorities)
            ranked_teams.append(team_copy)

        # Sort by calculated score (highest first)
        ranked_teams.sort(key=lambda x: x.get("calculated_score", 0.0), reverse=True)
        
        return ranked_teams

    def find_similar_teams(
        self, 
        target_team: Dict[str, Any], 
        candidate_teams: List[Dict[str, Any]], 
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find teams similar to a target team based on metrics.
        
        Args:
            target_team: Team to find similarities for
            candidate_teams: List of teams to compare against
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            max_results: Maximum number of similar teams to return
            
        Returns:
            List of similar teams with similarity scores
        """
        if "metrics" not in target_team:
            return []

        target_metrics = target_team["metrics"]
        similar_teams = []

        for candidate in candidate_teams:
            if candidate.get("team_number") == target_team.get("team_number"):
                continue  # Skip the target team itself
                
            if "metrics" not in candidate:
                continue

            similarity = self.calculate_similarity_score(target_metrics, candidate["metrics"])
            
            if similarity >= similarity_threshold:
                similar_team = candidate.copy()
                similar_team["similarity_score"] = similarity
                similar_teams.append(similar_team)

        # Sort by similarity (highest first) and limit results
        similar_teams.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return similar_teams[:max_results]

    def select_reference_teams(
        self,
        ranked_teams: List[Dict[str, Any]],
        reference_teams_count: int,
        reference_selection: str = "top_middle_bottom"
    ) -> List[Dict[str, Any]]:
        """
        Select reference teams for batch processing score normalization.
        
        Args:
            ranked_teams: List of teams ranked by score
            reference_teams_count: Number of reference teams to select
            reference_selection: Selection strategy
            
        Returns:
            List of selected reference teams
        """
        if not ranked_teams or reference_teams_count <= 0:
            return []

        teams_count = len(ranked_teams)
        reference_teams = []

        if reference_selection == "top_middle_bottom":
            # Always select top team
            reference_teams.append(ranked_teams[0])
            
            if reference_teams_count > 1 and teams_count > 1:
                # Select bottom team
                reference_teams.append(ranked_teams[-1])
                
            if reference_teams_count > 2 and teams_count > 2:
                # Select middle team
                middle_index = teams_count // 2
                reference_teams.append(ranked_teams[middle_index])
                
            # Fill remaining slots with even distribution
            remaining_slots = reference_teams_count - len(reference_teams)
            if remaining_slots > 0 and teams_count > 3:
                step = teams_count / remaining_slots
                for i in range(remaining_slots):
                    index = min(int((i + 1) * step), teams_count - 1)
                    if ranked_teams[index] not in reference_teams:
                        reference_teams.append(ranked_teams[index])

        elif reference_selection == "percentile":
            # Select teams at specific percentiles
            if reference_teams_count > 1:
                percentile_step = 100 / (reference_teams_count - 1)
                for i in range(reference_teams_count):
                    percentile = i * percentile_step
                    index = min(int((teams_count - 1) * (percentile / 100)), teams_count - 1)
                    reference_teams.append(ranked_teams[index])
            else:
                reference_teams.append(ranked_teams[0])

        elif reference_selection == "even_distribution":
            # Evenly distribute across the entire list
            if reference_teams_count > 1:
                step = teams_count / reference_teams_count
                for i in range(reference_teams_count):
                    index = min(int(i * step), teams_count - 1)
                    reference_teams.append(ranked_teams[index])
            else:
                reference_teams.append(ranked_teams[0])

        else:
            # Default: top teams
            for i in range(min(reference_teams_count, teams_count)):
                reference_teams.append(ranked_teams[i])

        return reference_teams

    def normalize_scores_with_reference_teams(
        self,
        teams: List[Dict[str, Any]],
        reference_teams: List[Dict[str, Any]],
        target_reference_scores: Dict[int, float]
    ) -> List[Dict[str, Any]]:
        """
        Normalize team scores using reference teams for consistency.
        
        Args:
            teams: Teams to normalize
            reference_teams: Reference teams in this batch
            target_reference_scores: Target scores for reference teams
            
        Returns:
            List of teams with normalized scores
        """
        if not reference_teams or not target_reference_scores:
            return teams

        # Calculate normalization factor based on reference teams
        total_factor = 0.0
        factor_count = 0

        for ref_team in reference_teams:
            ref_team_num = ref_team.get("team_number")
            current_score = ref_team.get("score", 0.0)
            target_score = target_reference_scores.get(ref_team_num)

            if ref_team_num and target_score and current_score > 0:
                factor = target_score / current_score
                total_factor += factor
                factor_count += 1

        if factor_count == 0:
            return teams  # No normalization possible

        normalization_factor = total_factor / factor_count

        # Apply normalization to all teams
        normalized_teams = []
        for team in teams:
            normalized_team = team.copy()
            original_score = team.get("score", 0.0)
            normalized_score = original_score * normalization_factor
            normalized_team["score"] = round(normalized_score, 2)
            normalized_team["original_score"] = original_score
            normalized_team["normalization_factor"] = round(normalization_factor, 3)
            normalized_teams.append(normalized_team)

        return normalized_teams

    def analyze_team_performance_trends(
        self, 
        team_data: Dict[str, Any],
        metric_names: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze performance trends for a team across matches.
        
        Args:
            team_data: Team data with scouting_data
            metric_names: List of metric names to analyze
            
        Returns:
            Performance trend analysis
        """
        if "scouting_data" not in team_data or not isinstance(team_data["scouting_data"], list):
            return {"error": "No scouting data available"}

        scouting_data = team_data["scouting_data"]
        trends = {}

        for metric in metric_names:
            values = []
            for match in scouting_data:
                if isinstance(match, dict) and metric in match:
                    value = match[metric]
                    if isinstance(value, (int, float)):
                        values.append(value)

            if len(values) >= 2:
                # Calculate basic trend statistics
                avg = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                
                # Simple trend calculation (slope)
                n = len(values)
                sum_x = sum(range(n))
                sum_y = sum(values)
                sum_xy = sum(i * values[i] for i in range(n))
                sum_x2 = sum(i * i for i in range(n))
                
                if n * sum_x2 - sum_x * sum_x != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                else:
                    slope = 0.0

                trends[metric] = {
                    "average": round(avg, 2),
                    "minimum": min_val,
                    "maximum": max_val,
                    "trend_slope": round(slope, 3),
                    "improvement": slope > 0.1,
                    "decline": slope < -0.1,
                    "matches": len(values)
                }

        return trends