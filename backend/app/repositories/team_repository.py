# backend/app/repositories/team_repository.py
"""
Team Repository

Specialized repository for team-related operations with caching and
domain-specific queries for team management.
"""

from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, text, or_, Integer
import logging
from datetime import datetime, timedelta

from app.database.models import TeamSelectionStatus, LockedPicklist, Alliance
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TeamRepository(BaseRepository[TeamSelectionStatus]):
    """Repository for team operations with specialized queries and caching."""

    def __init__(self, db: Session):
        super().__init__(TeamSelectionStatus, db)
        self._team_cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes

    def get_domain_specific_methods(self) -> Dict[str, Any]:
        """Return domain-specific methods for team operations."""
        return {
            'get_team_history': self.get_team_history,
            'get_team_performance_summary': self.get_team_performance_summary,
            'get_teams_by_status': self.get_teams_by_status,
            'get_team_alliance_history': self.get_team_alliance_history,
            'get_team_picklist_appearances': self.get_team_picklist_appearances,
            'get_popular_teams': self.get_popular_teams,
            'get_team_ranking_trends': self.get_team_ranking_trends,
            'search_teams_by_performance': self.search_teams_by_performance,
            'get_team_competition_stats': self.get_team_competition_stats,
            'get_team_selection_patterns': self.get_team_selection_patterns,
            'clear_team_cache': self.clear_team_cache,
            'get_cached_team_data': self.get_cached_team_data,
        }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    def _cache_team_data(self, cache_key: str, data: Any) -> None:
        """Cache team data with expiry."""
        self._team_cache[cache_key] = data
        self._cache_expiry[cache_key] = datetime.now() + self._cache_duration

    def get_team_history(self, team_number: int, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive history for a team.
        
        Args:
            team_number: Team number
            year: Optional year filter
            
        Returns:
            Dictionary with team history data
        """
        cache_key = f"team_history_{team_number}_{year}"
        
        if self._is_cache_valid(cache_key):
            return self._team_cache[cache_key]
        
        try:
            # Get selection status history
            status_query = self.db.query(TeamSelectionStatus).filter(
                TeamSelectionStatus.team_number == team_number
            )
            
            if year:
                # Join with AllianceSelection to filter by year
                from app.database.models import AllianceSelection
                status_query = status_query.join(AllianceSelection).filter(
                    AllianceSelection.year == year
                )
            
            statuses = status_query.all()
            
            # Get picklist appearances
            picklist_query = self.db.query(LockedPicklist).filter(
                LockedPicklist.team_number == team_number
            )
            
            if year:
                picklist_query = picklist_query.filter(LockedPicklist.year == year)
            
            picklists = picklist_query.all()
            
            # Get alliance memberships
            alliance_query = self.db.query(Alliance).filter(
                or_(
                    Alliance.captain_team_number == team_number,
                    Alliance.first_pick_team_number == team_number,
                    Alliance.second_pick_team_number == team_number,
                    Alliance.backup_team_number == team_number
                )
            )
            
            if year:
                from app.database.models import AllianceSelection
                alliance_query = alliance_query.join(AllianceSelection).filter(
                    AllianceSelection.year == year
                )
            
            alliances = alliance_query.all()
            
            # Compile history
            history = {
                'team_number': team_number,
                'year_filter': year,
                'selection_history': [
                    {
                        'selection_id': status.selection_id,
                        'is_captain': status.is_captain,
                        'is_picked': status.is_picked,
                        'has_declined': status.has_declined,
                        'round_eliminated': status.round_eliminated,
                        'created_at': status.created_at,
                    } for status in statuses
                ],
                'picklist_history': [
                    {
                        'id': picklist.id,
                        'event_key': picklist.event_key,
                        'year': picklist.year,
                        'created_at': picklist.created_at,
                    } for picklist in picklists
                ],
                'alliance_history': [
                    {
                        'alliance_number': alliance.alliance_number,
                        'role': self._get_team_role_in_alliance(alliance, team_number),
                        'selection_id': alliance.selection_id,
                        'created_at': alliance.created_at,
                    } for alliance in alliances
                ],
                'summary': {
                    'total_selections': len(statuses),
                    'times_captain': sum(1 for s in statuses if s.is_captain),
                    'times_picked': sum(1 for s in statuses if s.is_picked),
                    'times_declined': sum(1 for s in statuses if s.has_declined),
                    'picklists_created': len(picklists),
                    'alliances_joined': len(alliances),
                }
            }
            
            self._cache_team_data(cache_key, history)
            return history
            
        except Exception as e:
            logger.error(f"Error getting team history for {team_number}: {e}")
            raise

    def _get_team_role_in_alliance(self, alliance: Alliance, team_number: int) -> str:
        """Determine team's role in an alliance."""
        if alliance.captain_team_number == team_number:
            return "captain"
        elif alliance.first_pick_team_number == team_number:
            return "first_pick"
        elif alliance.second_pick_team_number == team_number:
            return "second_pick"
        elif alliance.backup_team_number == team_number:
            return "backup"
        return "unknown"

    def get_team_performance_summary(self, team_number: int, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get performance summary for a team.
        
        Args:
            team_number: Team number
            year: Optional year filter
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            history = self.get_team_history(team_number, year)
            
            # Calculate performance metrics
            total_selections = history['summary']['total_selections']
            captain_rate = history['summary']['times_captain'] / max(total_selections, 1)
            pick_rate = history['summary']['times_picked'] / max(total_selections, 1)
            decline_rate = history['summary']['times_declined'] / max(total_selections, 1)
            
            # Calculate success metrics
            successful_selections = history['summary']['times_captain'] + history['summary']['times_picked']
            success_rate = successful_selections / max(total_selections, 1)
            
            return {
                'team_number': team_number,
                'year_filter': year,
                'performance_metrics': {
                    'total_selections': total_selections,
                    'captain_rate': round(captain_rate, 3),
                    'pick_rate': round(pick_rate, 3),
                    'decline_rate': round(decline_rate, 3),
                    'success_rate': round(success_rate, 3),
                    'alliance_participation': history['summary']['alliances_joined'],
                    'picklists_generated': history['summary']['picklists_created'],
                },
                'ratings': {
                    'desirability': min(1.0, captain_rate * 2 + pick_rate),  # How often picked
                    'reliability': 1.0 - decline_rate,  # How often accepts
                    'leadership': captain_rate,  # How often is captain
                    'overall': round((success_rate + (1.0 - decline_rate)) / 2, 3),
                }
            }
        except Exception as e:
            logger.error(f"Error getting performance summary for team {team_number}: {e}")
            raise

    def get_teams_by_status(
        self,
        selection_id: int,
        is_captain: Optional[bool] = None,
        is_picked: Optional[bool] = None,
        has_declined: Optional[bool] = None
    ) -> List[TeamSelectionStatus]:
        """
        Get teams filtered by their selection status.
        
        Args:
            selection_id: Alliance selection ID
            is_captain: Filter by captain status
            is_picked: Filter by picked status
            has_declined: Filter by declined status
            
        Returns:
            List of TeamSelectionStatus instances
        """
        try:
            query = self.db.query(TeamSelectionStatus).filter(
                TeamSelectionStatus.selection_id == selection_id
            )
            
            if is_captain is not None:
                query = query.filter(TeamSelectionStatus.is_captain == is_captain)
            if is_picked is not None:
                query = query.filter(TeamSelectionStatus.is_picked == is_picked)
            if has_declined is not None:
                query = query.filter(TeamSelectionStatus.has_declined == has_declined)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting teams by status for selection {selection_id}: {e}")
            raise

    def get_team_alliance_history(self, team_number: int, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get detailed alliance history for a team.
        
        Args:
            team_number: Team number
            year: Optional year filter
            
        Returns:
            List of alliance participation records
        """
        try:
            query = self.db.query(Alliance).filter(
                or_(
                    Alliance.captain_team_number == team_number,
                    Alliance.first_pick_team_number == team_number,
                    Alliance.second_pick_team_number == team_number,
                    Alliance.backup_team_number == team_number
                )
            )
            
            if year:
                from app.database.models import AllianceSelection
                query = query.join(AllianceSelection).filter(
                    AllianceSelection.year == year
                )
            
            alliances = query.all()
            
            alliance_history = []
            for alliance in alliances:
                # Get alliance selection details
                from app.database.models import AllianceSelection
                selection = self.db.query(AllianceSelection).filter(
                    AllianceSelection.id == alliance.selection_id
                ).first()
                
                alliance_history.append({
                    'alliance_number': alliance.alliance_number,
                    'role': self._get_team_role_in_alliance(alliance, team_number),
                    'event_key': selection.event_key if selection else None,
                    'year': selection.year if selection else None,
                    'selection_completed': selection.is_completed if selection else False,
                    'alliance_members': {
                        'captain': alliance.captain_team_number if alliance.captain_team_number != 0 else None,
                        'first_pick': alliance.first_pick_team_number if alliance.first_pick_team_number != 0 else None,
                        'second_pick': alliance.second_pick_team_number if alliance.second_pick_team_number != 0 else None,
                        'backup': alliance.backup_team_number if alliance.backup_team_number != 0 else None,
                    },
                    'created_at': alliance.created_at,
                })
            
            return sorted(alliance_history, key=lambda x: x['created_at'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting alliance history for team {team_number}: {e}")
            raise

    def get_team_picklist_appearances(self, team_number: int, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get picklist appearances for a team.
        
        Args:
            team_number: Team number
            year: Optional year filter
            
        Returns:
            List of picklist appearance records
        """
        try:
            # This is complex because team_number in LockedPicklist is the team that CREATED the picklist
            # We need to search in the JSON data for appearances of the team
            
            query = self.db.query(LockedPicklist)
            
            if year:
                query = query.filter(LockedPicklist.year == year)
            
            all_picklists = query.all()
            appearances = []
            
            for picklist in all_picklists:
                # Search in JSON fields for the team number
                found_in = []
                
                # Check each pick position
                for pick_type, pick_data in [
                    ('first_pick', picklist.first_pick_data),
                    ('second_pick', picklist.second_pick_data),
                    ('third_pick', picklist.third_pick_data)
                ]:
                    if pick_data and isinstance(pick_data, list):
                        for i, team_entry in enumerate(pick_data):
                            if isinstance(team_entry, dict) and team_entry.get('team_number') == team_number:
                                found_in.append({
                                    'pick_type': pick_type,
                                    'rank': i + 1,
                                    'score': team_entry.get('score'),
                                    'reasoning': team_entry.get('reasoning', '')
                                })
                
                if found_in:
                    appearances.append({
                        'picklist_id': picklist.id,
                        'created_by_team': picklist.team_number,
                        'event_key': picklist.event_key,
                        'year': picklist.year,
                        'appearances': found_in,
                        'created_at': picklist.created_at,
                    })
            
            return sorted(appearances, key=lambda x: x['created_at'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting picklist appearances for team {team_number}: {e}")
            raise

    def get_popular_teams(self, year: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get most popular teams based on selection frequency.
        
        Args:
            year: Optional year filter
            limit: Maximum number of teams to return
            
        Returns:
            List of popular team records
        """
        try:
            query = self.db.query(
                TeamSelectionStatus.team_number,
                func.count(TeamSelectionStatus.id).label('total_selections'),
                func.sum(func.cast(TeamSelectionStatus.is_captain, Integer)).label('captain_count'),
                func.sum(func.cast(TeamSelectionStatus.is_picked, Integer)).label('picked_count')
            ).group_by(TeamSelectionStatus.team_number)
            
            if year:
                from app.database.models import AllianceSelection
                query = query.join(AllianceSelection).filter(
                    AllianceSelection.year == year
                )
            
            popular_teams = query.order_by(
                desc('total_selections')
            ).limit(limit).all()
            
            return [
                {
                    'team_number': team.team_number,
                    'total_selections': team.total_selections,
                    'captain_count': team.captain_count or 0,
                    'picked_count': team.picked_count or 0,
                    'success_rate': (team.captain_count or 0 + team.picked_count or 0) / team.total_selections,
                }
                for team in popular_teams
            ]
        except Exception as e:
            logger.error(f"Error getting popular teams: {e}")
            raise

    def get_team_ranking_trends(self, team_number: int, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get ranking trends for a team across picklists.
        
        Args:
            team_number: Team number
            year: Optional year filter
            
        Returns:
            Dictionary with ranking trend data
        """
        try:
            appearances = self.get_team_picklist_appearances(team_number, year)
            
            if not appearances:
                return {
                    'team_number': team_number,
                    'year_filter': year,
                    'trends': {},
                    'summary': {
                        'total_appearances': 0,
                        'average_rank': None,
                        'best_rank': None,
                        'worst_rank': None,
                    }
                }
            
            # Extract ranking data
            all_ranks = []
            pick_type_trends = {}
            
            for appearance in appearances:
                for entry in appearance['appearances']:
                    pick_type = entry['pick_type']
                    rank = entry['rank']
                    
                    all_ranks.append(rank)
                    
                    if pick_type not in pick_type_trends:
                        pick_type_trends[pick_type] = []
                    pick_type_trends[pick_type].append({
                        'rank': rank,
                        'score': entry.get('score'),
                        'event_key': appearance['event_key'],
                        'created_at': appearance['created_at'],
                    })
            
            # Calculate statistics
            avg_rank = sum(all_ranks) / len(all_ranks) if all_ranks else None
            best_rank = min(all_ranks) if all_ranks else None
            worst_rank = max(all_ranks) if all_ranks else None
            
            return {
                'team_number': team_number,
                'year_filter': year,
                'trends': {
                    'by_pick_type': pick_type_trends,
                    'chronological': sorted([
                        {
                            'rank': entry['rank'],
                            'pick_type': entry['pick_type'],
                            'event_key': appearance['event_key'],
                            'created_at': appearance['created_at'],
                        }
                        for appearance in appearances
                        for entry in appearance['appearances']
                    ], key=lambda x: x['created_at'])
                },
                'summary': {
                    'total_appearances': len(all_ranks),
                    'average_rank': round(avg_rank, 2) if avg_rank else None,
                    'best_rank': best_rank,
                    'worst_rank': worst_rank,
                    'pick_type_distribution': {
                        pick_type: len(ranks) for pick_type, ranks in pick_type_trends.items()
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting ranking trends for team {team_number}: {e}")
            raise

    def search_teams_by_performance(
        self,
        min_success_rate: float = 0.0,
        min_selections: int = 1,
        year: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search teams by performance criteria.
        
        Args:
            min_success_rate: Minimum success rate (0.0-1.0)
            min_selections: Minimum number of selections
            year: Optional year filter
            limit: Maximum number of teams to return
            
        Returns:
            List of teams matching criteria
        """
        try:
            # Get team performance data
            query = self.db.query(
                TeamSelectionStatus.team_number,
                func.count(TeamSelectionStatus.id).label('total_selections'),
                func.sum(func.cast(TeamSelectionStatus.is_captain, Integer)).label('captain_count'),
                func.sum(func.cast(TeamSelectionStatus.is_picked, Integer)).label('picked_count'),
                func.sum(func.cast(TeamSelectionStatus.has_declined, Integer)).label('declined_count')
            ).group_by(TeamSelectionStatus.team_number)
            
            if year:
                from app.database.models import AllianceSelection
                query = query.join(AllianceSelection).filter(
                    AllianceSelection.year == year
                )
            
            # Apply minimum selections filter
            query = query.having(func.count(TeamSelectionStatus.id) >= min_selections)
            
            teams = query.all()
            
            # Filter by success rate
            qualifying_teams = []
            for team in teams:
                total = team.total_selections
                successful = (team.captain_count or 0) + (team.picked_count or 0)
                success_rate = successful / total if total > 0 else 0.0
                
                if success_rate >= min_success_rate:
                    qualifying_teams.append({
                        'team_number': team.team_number,
                        'total_selections': total,
                        'captain_count': team.captain_count or 0,
                        'picked_count': team.picked_count or 0,
                        'declined_count': team.declined_count or 0,
                        'success_rate': round(success_rate, 3),
                        'decline_rate': round((team.declined_count or 0) / total, 3),
                    })
            
            # Sort by success rate descending
            qualifying_teams.sort(key=lambda x: x['success_rate'], reverse=True)
            
            return qualifying_teams[:limit]
        except Exception as e:
            logger.error(f"Error searching teams by performance: {e}")
            raise

    def get_team_competition_stats(self, year: int) -> Dict[str, Any]:
        """
        Get overall competition statistics for teams.
        
        Args:
            year: Competition year
            
        Returns:
            Dictionary with competition statistics
        """
        try:
            from app.database.models import AllianceSelection
            
            # Get team counts
            total_teams = self.db.query(TeamSelectionStatus.team_number).join(
                AllianceSelection
            ).filter(AllianceSelection.year == year).distinct().count()
            
            total_selections = self.db.query(TeamSelectionStatus).join(
                AllianceSelection
            ).filter(AllianceSelection.year == year).count()
            
            captains = self.db.query(TeamSelectionStatus).join(
                AllianceSelection
            ).filter(
                and_(
                    AllianceSelection.year == year,
                    TeamSelectionStatus.is_captain == True
                )
            ).count()
            
            picked = self.db.query(TeamSelectionStatus).join(
                AllianceSelection
            ).filter(
                and_(
                    AllianceSelection.year == year,
                    TeamSelectionStatus.is_picked == True
                )
            ).count()
            
            declined = self.db.query(TeamSelectionStatus).join(
                AllianceSelection
            ).filter(
                and_(
                    AllianceSelection.year == year,
                    TeamSelectionStatus.has_declined == True
                )
            ).count()
            
            return {
                'year': year,
                'team_statistics': {
                    'total_unique_teams': total_teams,
                    'total_selection_events': total_selections,
                    'average_selections_per_team': round(total_selections / max(total_teams, 1), 2),
                    'captain_selections': captains,
                    'picked_selections': picked,
                    'declined_selections': declined,
                    'success_rate': round((captains + picked) / max(total_selections, 1), 3),
                    'decline_rate': round(declined / max(total_selections, 1), 3),
                }
            }
        except Exception as e:
            logger.error(f"Error getting competition stats for year {year}: {e}")
            raise

    def get_team_selection_patterns(self, team_number: int, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze selection patterns for a team.
        
        Args:
            team_number: Team number
            year: Optional year filter
            
        Returns:
            Dictionary with selection pattern analysis
        """
        try:
            history = self.get_team_history(team_number, year)
            
            if not history['selection_history']:
                return {
                    'team_number': team_number,
                    'year_filter': year,
                    'patterns': {},
                    'insights': []
                }
            
            # Analyze patterns
            selections = history['selection_history']
            
            # Time-based patterns
            selection_dates = [s['created_at'] for s in selections]
            
            # Success patterns
            captain_pattern = [s['is_captain'] for s in selections]
            picked_pattern = [s['is_picked'] for s in selections]
            declined_pattern = [s['has_declined'] for s in selections]
            
            # Generate insights
            insights = []
            
            total = len(selections)
            captain_rate = sum(captain_pattern) / total
            picked_rate = sum(picked_pattern) / total
            decline_rate = sum(declined_pattern) / total
            
            if captain_rate > 0.5:
                insights.append(f"Frequently selected as captain ({captain_rate:.1%} of selections)")
            if picked_rate > 0.3:
                insights.append(f"Often picked by other teams ({picked_rate:.1%} of selections)")
            if decline_rate > 0.2:
                insights.append(f"Sometimes declines invitations ({decline_rate:.1%} of selections)")
            if captain_rate + picked_rate > 0.8:
                insights.append("Highly desirable team with strong selection success")
            
            return {
                'team_number': team_number,
                'year_filter': year,
                'patterns': {
                    'selection_frequency': {
                        'total_selections': total,
                        'captain_rate': round(captain_rate, 3),
                        'picked_rate': round(picked_rate, 3),
                        'decline_rate': round(decline_rate, 3),
                        'success_rate': round(captain_rate + picked_rate, 3),
                    },
                    'temporal_distribution': {
                        'first_selection': min(selection_dates) if selection_dates else None,
                        'last_selection': max(selection_dates) if selection_dates else None,
                        'selection_span_days': (max(selection_dates) - min(selection_dates)).days if len(selection_dates) > 1 else 0,
                    }
                },
                'insights': insights
            }
        except Exception as e:
            logger.error(f"Error analyzing selection patterns for team {team_number}: {e}")
            raise

    def clear_team_cache(self) -> None:
        """Clear the team data cache."""
        self._team_cache.clear()
        self._cache_expiry.clear()
        logger.info("Team cache cleared")

    def get_cached_team_data(self, cache_key: str) -> Optional[Any]:
        """
        Get cached team data if available and valid.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None
        """
        if self._is_cache_valid(cache_key):
            return self._team_cache.get(cache_key)
        return None