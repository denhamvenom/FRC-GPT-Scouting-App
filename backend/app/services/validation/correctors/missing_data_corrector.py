"""
Missing Data Corrector

Handles missing data through various strategies including:
- Virtual scouting based on team averages and match context
- Todo list management for manual data collection
- Match ignoring with categorized reasons
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import (
    VirtualScoutData, TodoItem, IgnoredMatch, 
    TodoStatus, IgnoreReason
)
from ..exceptions import (
    DataNotFoundError, TodoItemExistsError, 
    TodoItemNotFoundError, InvalidCorrectionError
)


class MissingDataCorrector:
    """Handles missing data through various correction strategies."""
    
    def create_virtual_scout(self, dataset: Dict, team_number: int, 
                           match_number: int) -> VirtualScoutData:
        """
        Create virtual scout data based on team averages and match context.
        
        Args:
            dataset: The unified dataset
            team_number: Team number
            match_number: Match number
            
        Returns:
            VirtualScoutData object
        """
        teams_data = dataset.get("teams", {})
        
        # Validate team exists
        if str(team_number) not in teams_data:
            raise DataNotFoundError("Team", str(team_number))
        
        team_data = teams_data[str(team_number)]
        scouting_data = team_data.get("scouting_data", [])
        
        # Check if match already exists
        if self._match_exists(scouting_data, match_number):
            raise InvalidCorrectionError(f"Match {match_number} already exists for team {team_number}")
        
        # Calculate team averages
        team_averages = self._calculate_team_averages(scouting_data)
        if not team_averages:
            raise InvalidCorrectionError("Insufficient data to calculate team averages")
        
        # Get match context (alliance color, etc.)
        match_context = self._get_match_context(dataset, team_number, match_number)
        
        # Create base virtual scout entry
        virtual_data = {
            "team_number": team_number,
            "match_number": match_number,
            "qual_number": match_number,
            "alliance_color": match_context.get("alliance_color", "unknown"),
            **team_averages
        }
        
        # Adjust based on match performance if available
        adjustment_info = None
        if match_context.get("alliance_score") is not None:
            virtual_data, adjustment_info = self._adjust_for_match_performance(
                virtual_data, team_averages, match_context, dataset
            )
        
        # Create VirtualScoutData object
        virtual_scout = VirtualScoutData(
            team_number=team_number,
            match_number=match_number,
            qual_number=match_number,
            alliance_color=match_context.get("alliance_color", "unknown"),
            data=virtual_data,
            adjustment_info=adjustment_info
        )
        
        # Add to scouting data
        virtual_data["is_virtual_scout"] = True
        virtual_data["virtual_scout_timestamp"] = datetime.now().isoformat()
        scouting_data.append(virtual_data)
        
        return virtual_scout
    
    def preview_virtual_scout(self, dataset: Dict, team_number: int, 
                            match_number: int) -> VirtualScoutData:
        """
        Preview virtual scout data without saving.
        
        Args:
            dataset: The unified dataset
            team_number: Team number
            match_number: Match number
            
        Returns:
            VirtualScoutData preview
        """
        # Create a copy of the dataset to avoid modifying original
        import copy
        dataset_copy = copy.deepcopy(dataset)
        
        # Generate virtual scout on the copy
        return self.create_virtual_scout(dataset_copy, team_number, match_number)
    
    def ignore_match(self, dataset: Dict, team_number: int, match_number: int,
                    reason_category: str, reason_text: str = "") -> IgnoredMatch:
        """
        Mark a match as ignored with a categorized reason.
        
        Args:
            dataset: The unified dataset
            team_number: Team number
            match_number: Match number
            reason_category: Category of ignore reason
            reason_text: Optional detailed explanation
            
        Returns:
            IgnoredMatch object
        """
        # Validate reason category
        try:
            reason_enum = IgnoreReason(reason_category)
        except ValueError:
            raise InvalidCorrectionError(f"Invalid reason category: {reason_category}")
        
        if reason_enum == IgnoreReason.OTHER and not reason_text:
            raise InvalidCorrectionError("Reason text required when category is 'other'")
        
        teams_data = dataset.get("teams", {})
        
        # Validate team exists
        if str(team_number) not in teams_data:
            raise DataNotFoundError("Team", str(team_number))
        
        team_data = teams_data[str(team_number)]
        
        # Initialize ignored_matches if needed
        if "ignored_matches" not in team_data:
            team_data["ignored_matches"] = []
        
        # Check if already ignored
        for ignored in team_data["ignored_matches"]:
            if ignored.get("match_number") == match_number:
                raise InvalidCorrectionError(f"Match {match_number} already ignored")
        
        # Create ignored match record
        ignored_match = IgnoredMatch(
            team_number=team_number,
            match_number=match_number,
            reason_category=reason_enum,
            reason=reason_text
        )
        
        # Add to dataset
        team_data["ignored_matches"].append(ignored_match.dict())
        
        return ignored_match
    
    def add_to_todo(self, dataset: Dict, team_number: int, match_number: int,
                   priority: int = 3, description: Optional[str] = None) -> TodoItem:
        """
        Add a match to the todo list for manual scouting.
        
        Args:
            dataset: The unified dataset
            team_number: Team number
            match_number: Match number
            priority: Priority level (1-5)
            description: Optional description
            
        Returns:
            TodoItem object
        """
        # Initialize todo list if needed
        if "todo_list" not in dataset:
            dataset["todo_list"] = []
        
        # Check if already exists
        for item in dataset["todo_list"]:
            if (item.get("team_number") == team_number and 
                item.get("match_number") == match_number):
                raise TodoItemExistsError(team_number, match_number)
        
        # Create todo item
        todo_item = TodoItem(
            team_number=team_number,
            match_number=match_number,
            priority=priority,
            description=description
        )
        
        # Add to dataset
        dataset["todo_list"].append(todo_item.dict())
        
        return todo_item
    
    def get_todo_list(self, dataset: Dict) -> List[TodoItem]:
        """Get all todo items from the dataset."""
        todo_data = dataset.get("todo_list", [])
        return [TodoItem(**item) for item in todo_data]
    
    def update_todo_status(self, dataset: Dict, team_number: int, match_number: int,
                          new_status: str, assigned_to: Optional[str] = None,
                          notes: Optional[str] = None) -> TodoItem:
        """
        Update the status of a todo item.
        
        Args:
            dataset: The unified dataset
            team_number: Team number
            match_number: Match number
            new_status: New status
            assigned_to: Optional assignee
            notes: Optional notes
            
        Returns:
            Updated TodoItem
        """
        # Validate status
        try:
            status_enum = TodoStatus(new_status)
        except ValueError:
            raise InvalidCorrectionError(f"Invalid status: {new_status}")
        
        # Find todo item
        todo_list = dataset.get("todo_list", [])
        for item in todo_list:
            if (item.get("team_number") == team_number and 
                item.get("match_number") == match_number):
                # Update fields
                item["status"] = status_enum.value
                item["updated_timestamp"] = datetime.now().isoformat()
                if assigned_to is not None:
                    item["assigned_to"] = assigned_to
                if notes is not None:
                    item["notes"] = notes
                
                return TodoItem(**item)
        
        raise TodoItemNotFoundError(team_number, match_number)
    
    def _match_exists(self, scouting_data: List[Dict], match_number: int) -> bool:
        """Check if a match already exists in scouting data."""
        for match in scouting_data:
            if self._get_match_number(match) == match_number:
                return True
        return False
    
    def _calculate_team_averages(self, scouting_data: List[Dict]) -> Dict[str, float]:
        """Calculate team averages for all numeric metrics."""
        if not scouting_data:
            return {}
        
        # Collect all numeric metrics
        metrics = {}
        for match in scouting_data:
            for key, value in match.items():
                if isinstance(value, (int, float)) and key not in [
                    "qual_number", "match_number", "team_number"
                ]:
                    if key not in metrics:
                        metrics[key] = []
                    metrics[key].append(float(value))
        
        # Calculate averages
        averages = {}
        for key, values in metrics.items():
            if values:
                averages[key] = sum(values) / len(values)
        
        return averages
    
    def _get_match_context(self, dataset: Dict, team_number: int, 
                          match_number: int) -> Dict[str, Any]:
        """Get context information for a match."""
        expected_matches = dataset.get("expected_matches", [])
        
        for entry in expected_matches:
            if (entry.get("match_number") == match_number and 
                entry.get("team_number") == team_number):
                return {
                    "alliance_color": entry.get("alliance_color"),
                    "alliance_score": self._get_alliance_score(dataset, match_number, 
                                                              entry.get("alliance_color"))
                }
        
        return {}
    
    def _get_alliance_score(self, dataset: Dict, match_number: int, 
                           alliance_color: str) -> Optional[int]:
        """Get the alliance score for a specific match."""
        tba_matches = dataset.get("tba_matches", [])
        
        for match in tba_matches:
            if match.get("match_number") == match_number:
                alliances = match.get("alliances", {})
                alliance_data = alliances.get(alliance_color, {})
                return alliance_data.get("score")
        
        return None
    
    def _adjust_for_match_performance(self, virtual_data: Dict, team_averages: Dict,
                                    match_context: Dict, dataset: Dict) -> tuple:
        """Adjust virtual scout data based on match performance."""
        alliance_score = match_context.get("alliance_score")
        alliance_color = match_context.get("alliance_color")
        
        if alliance_score is None or alliance_color is None:
            return virtual_data, None
        
        # Calculate average alliance score for this team
        avg_alliance_score = self._calculate_avg_alliance_score(
            dataset, virtual_data["team_number"], alliance_color
        )
        
        if avg_alliance_score is None or avg_alliance_score == 0:
            return virtual_data, None
        
        # Calculate adjustment ratio
        score_ratio = alliance_score / avg_alliance_score
        
        # Apply adjustment to numeric metrics
        adjusted_data = virtual_data.copy()
        for metric, value in virtual_data.items():
            if isinstance(value, (int, float)) and metric not in [
                "team_number", "match_number", "qual_number"
            ]:
                adjusted_value = value * score_ratio
                # Round appropriately
                if isinstance(value, int):
                    adjusted_data[metric] = int(round(adjusted_value))
                else:
                    adjusted_data[metric] = round(adjusted_value, 2)
        
        adjustment_info = {
            "alliance_score": alliance_score,
            "avg_alliance_score": avg_alliance_score,
            "score_ratio": score_ratio,
            "adjusted": True
        }
        
        return adjusted_data, adjustment_info
    
    def _calculate_avg_alliance_score(self, dataset: Dict, team_number: int, 
                                    alliance_color: str) -> Optional[float]:
        """Calculate average alliance score for a team."""
        teams_data = dataset.get("teams", {})
        tba_matches = dataset.get("tba_matches", [])
        
        if str(team_number) not in teams_data:
            return None
        
        team_data = teams_data[str(team_number)]
        alliance_scores = []
        
        for match in team_data.get("scouting_data", []):
            if match.get("alliance_color") == alliance_color:
                match_num = self._get_match_number(match)
                if match_num:
                    # Find TBA score for this match
                    for tba_match in tba_matches:
                        if tba_match.get("match_number") == match_num:
                            score = (tba_match.get("alliances", {})
                                   .get(alliance_color, {})
                                   .get("score"))
                            if score is not None:
                                alliance_scores.append(score)
                            break
        
        return sum(alliance_scores) / len(alliance_scores) if alliance_scores else None
    
    def _get_match_number(self, match: Dict) -> Optional[int]:
        """Extract match number from match data."""
        for field in ["qual_number", "match_number"]:
            if field in match:
                try:
                    return int(match[field])
                except (ValueError, TypeError):
                    pass
        return None