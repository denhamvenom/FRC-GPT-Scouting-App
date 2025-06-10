"""
Factory functions for generating test data for picklist services.
"""

import random
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.services.picklist.models import (
    PicklistGenerationRequest,
    PickPosition,
    PriorityMetric,
    RankedTeam,
    PicklistGenerationResult,
)


class TeamDataFactory:
    """Factory for generating team data."""
    
    TEAM_NICKNAMES = [
        "The Cheesy Poofs", "Robonauts", "MadTown Robotics", "Team Voltage",
        "The Thunderbolts", "Cyber Eagles", "Iron Patriots", "RoboLancers",
        "Mechanical Mayhem", "Titanium Tigers", "Steel Storm", "Gear Heads",
        "Circuit Breakers", "Bot Builders", "Robo Warriors", "Tech Tigers",
        "Metal Moose", "Cyber Crusaders", "Robo Rams", "Lightning Robotics"
    ]
    
    CITIES = [
        "San Francisco", "New York", "Austin", "Seattle", "Boston", "Denver",
        "Chicago", "Los Angeles", "Portland", "Minneapolis", "Detroit", "Phoenix",
        "Atlanta", "Miami", "Dallas", "Houston", "Philadelphia", "San Diego"
    ]
    
    STATES = [
        "CA", "NY", "TX", "WA", "MA", "CO", "IL", "OR", "MN", "MI",
        "AZ", "GA", "FL", "PA", "NC", "OH", "VA", "NJ", "MD", "WI"
    ]
    
    @classmethod
    def create_team(
        cls,
        team_number: int,
        nickname: Optional[str] = None,
        performance_tier: str = "average",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a team with specified performance characteristics.
        
        Args:
            team_number: Team number
            nickname: Team nickname (random if None)
            performance_tier: "elite", "good", "average", "poor"
            **kwargs: Additional overrides
        """
        if nickname is None:
            nickname = random.choice(cls.TEAM_NICKNAMES)
        
        # Performance profiles based on tier
        if performance_tier == "elite":
            auto_base, teleop_base, epa_base = 20, 35, 25
            variance = 3
        elif performance_tier == "good":
            auto_base, teleop_base, epa_base = 15, 28, 20
            variance = 4
        elif performance_tier == "average":
            auto_base, teleop_base, epa_base = 12, 22, 16
            variance = 5
        else:  # poor
            auto_base, teleop_base, epa_base = 8, 15, 12
            variance = 6
        
        # Generate match data with variance
        auto_data = [
            max(0, auto_base + random.randint(-variance, variance))
            for _ in range(random.randint(5, 10))
        ]
        teleop_data = [
            max(0, teleop_base + random.randint(-variance * 2, variance * 2))
            for _ in range(len(auto_data))
        ]
        endgame_data = [
            max(0, 8 + random.randint(-3, 5))
            for _ in range(len(auto_data))
        ]
        
        default_team = {
            "team_number": team_number,
            "nickname": nickname,
            "city": random.choice(cls.CITIES),
            "state_prov": random.choice(cls.STATES),
            "country": "USA",
            "rookie_year": random.randint(2000, 2023),
            "scouting_data": {
                "auto_points": auto_data,
                "teleop_points": teleop_data,
                "endgame_points": endgame_data,
                "defense_rating": [random.randint(1, 5) for _ in range(len(auto_data))],
                "reliability": [random.randint(3, 5) for _ in range(len(auto_data))],
                "fouls": [random.randint(0, 3) for _ in range(len(auto_data))],
                "tech_fouls": [random.randint(0, 1) for _ in range(len(auto_data))]
            },
            "statbotics_data": {
                "epa": epa_base + random.uniform(-3, 3),
                "auto_epa": (auto_base / 3) + random.uniform(-2, 2),
                "teleop_epa": (teleop_base / 2.5) + random.uniform(-3, 3),
                "endgame_epa": 4 + random.uniform(-2, 3),
                "rp1_epa": random.uniform(0.3, 0.9),
                "rp2_epa": random.uniform(0.2, 0.8),
                "winrate": random.uniform(0.2, 0.9)
            },
            "tba_data": {
                "wins": random.randint(0, 15),
                "losses": random.randint(0, 15),
                "ties": random.randint(0, 2),
                "rank": random.randint(1, 50),
                "ranking_score": random.uniform(1.0, 3.0),
                "played": random.randint(8, 15),
                "dq": random.randint(0, 2)
            }
        }
        
        # Update with any provided overrides
        cls._deep_update(default_team, kwargs)
        return default_team
    
    @classmethod
    def create_teams_by_tier(
        cls,
        count_per_tier: int = 10,
        start_number: int = 1000
    ) -> List[Dict[str, Any]]:
        """Create teams distributed across performance tiers."""
        teams = []
        current_number = start_number
        
        for tier in ["elite", "good", "average", "poor"]:
            for _ in range(count_per_tier):
                team = cls.create_team(
                    team_number=current_number,
                    performance_tier=tier
                )
                teams.append(team)
                current_number += 1
        
        return teams
    
    @classmethod
    def create_regional_teams(
        cls,
        count: int = 50,
        start_number: int = 1000,
        region: str = "midwest"
    ) -> List[Dict[str, Any]]:
        """Create teams from a specific region."""
        region_configs = {
            "midwest": {
                "states": ["IL", "IN", "IA", "MI", "MN", "OH", "WI"],
                "cities": ["Chicago", "Detroit", "Minneapolis", "Columbus", "Milwaukee"]
            },
            "west": {
                "states": ["CA", "WA", "OR", "NV", "AZ"],
                "cities": ["San Francisco", "Seattle", "Portland", "Los Angeles", "Phoenix"]
            },
            "east": {
                "states": ["NY", "MA", "CT", "NJ", "PA"],
                "cities": ["New York", "Boston", "Philadelphia", "Hartford", "Newark"]
            }
        }
        
        config = region_configs.get(region, region_configs["midwest"])
        teams = []
        
        for i in range(count):
            team = cls.create_team(
                team_number=start_number + i,
                city=random.choice(config["cities"]),
                state_prov=random.choice(config["states"])
            )
            teams.append(team)
        
        return teams
    
    @staticmethod
    def _deep_update(base_dict: Dict, update_dict: Dict) -> None:
        """Deep update base_dict with update_dict."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict:
                TeamDataFactory._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value


class DatasetFactory:
    """Factory for generating complete datasets."""
    
    @classmethod
    def create_dataset(
        cls,
        team_count: int = 50,
        event_key: str = "2025test",
        event_name: str = "Test Event",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a complete unified dataset."""
        teams = TeamDataFactory.create_teams_by_tier(
            count_per_tier=team_count // 4,
            start_number=kwargs.get("start_number", 1000)
        )
        
        # Convert to team dictionary
        teams_dict = {str(team["team_number"]): team for team in teams}
        
        dataset = {
            "event_info": {
                "key": event_key,
                "name": event_name,
                "year": int(event_key[:4]) if event_key[:4].isdigit() else 2025,
                "start_date": "2025-03-15",
                "end_date": "2025-03-17",
                "location": "Test Venue, Test City, TS",
                "district": kwargs.get("district"),
                "week": kwargs.get("week", 1)
            },
            "teams": teams_dict,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_teams": len(teams),
                "data_sources": ["scouting", "statbotics", "tba"],
                "scouting_matches": kwargs.get("scouting_matches", 7),
                "last_updated": (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z",
                "version": "1.0",
                "generator": "test_factory"
            }
        }
        
        # Add any additional metadata
        dataset["metadata"].update(kwargs.get("metadata", {}))
        
        return dataset
    
    @classmethod
    def create_championship_dataset(cls) -> Dict[str, Any]:
        """Create a large championship-style dataset."""
        teams = []
        
        # Create teams from multiple divisions
        for division in range(4):  # 4 divisions
            division_teams = TeamDataFactory.create_teams_by_tier(
                count_per_tier=20,  # 20 teams per tier per division
                start_number=1000 + (division * 100)
            )
            teams.extend(division_teams)
        
        teams_dict = {str(team["team_number"]): team for team in teams}
        
        return {
            "event_info": {
                "key": "2025champ",
                "name": "FIRST Championship 2025",
                "year": 2025,
                "location": "Houston, TX",
                "divisions": ["Newton", "Galileo", "Hopper", "Carson"]
            },
            "teams": teams_dict,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_teams": len(teams),
                "data_sources": ["scouting", "statbotics", "tba"],
                "event_type": "championship"
            }
        }


class PicklistRequestFactory:
    """Factory for generating picklist requests."""
    
    COMMON_METRICS = [
        ("auto_points", "Autonomous Points", 2.0),
        ("teleop_points", "Teleoperated Points", 1.5),
        ("endgame_points", "Endgame Points", 1.2),
        ("epa", "Expected Points Added", 1.8),
        ("defense_rating", "Defense Rating", 1.0),
        ("reliability", "Reliability", 1.3),
        ("auto_epa", "Auto EPA", 1.6),
        ("teleop_epa", "Teleop EPA", 1.4)
    ]
    
    @classmethod
    def create_request(
        cls,
        your_team_number: int = 1001,
        pick_position: PickPosition = PickPosition.FIRST,
        strategy_type: str = "balanced",
        **kwargs
    ) -> PicklistGenerationRequest:
        """Create a picklist generation request."""
        
        # Strategy-based priority selection
        if strategy_type == "auto_focused":
            priorities = [
                PriorityMetric(id="auto_points", name="Auto Points", weight=3.0),
                PriorityMetric(id="auto_epa", name="Auto EPA", weight=2.5),
                PriorityMetric(id="teleop_points", name="Teleop Points", weight=1.0)
            ]
        elif strategy_type == "teleop_focused":
            priorities = [
                PriorityMetric(id="teleop_points", name="Teleop Points", weight=3.0),
                PriorityMetric(id="teleop_epa", name="Teleop EPA", weight=2.5),
                PriorityMetric(id="endgame_points", name="Endgame Points", weight=2.0)
            ]
        elif strategy_type == "defensive":
            priorities = [
                PriorityMetric(id="defense_rating", name="Defense", weight=3.0),
                PriorityMetric(id="reliability", name="Reliability", weight=2.5),
                PriorityMetric(id="epa", name="EPA", weight=1.5)
            ]
        else:  # balanced
            priorities = [
                PriorityMetric(id="epa", name="EPA", weight=2.0),
                PriorityMetric(id="auto_points", name="Auto Points", weight=1.8),
                PriorityMetric(id="teleop_points", name="Teleop Points", weight=1.6),
                PriorityMetric(id="reliability", name="Reliability", weight=1.4)
            ]
        
        defaults = {
            "priorities": priorities,
            "exclude_teams": [],
            "use_batching": False,
            "batch_size": 10,
            "custom_strategy": "",
            "cache_key": None
        }
        
        defaults.update(kwargs)
        
        return PicklistGenerationRequest(
            your_team_number=your_team_number,
            pick_position=pick_position,
            **defaults
        )
    
    @classmethod
    def create_batch_request(
        cls,
        your_team_number: int = 1001,
        batch_size: int = 5,
        **kwargs
    ) -> PicklistGenerationRequest:
        """Create a batch processing request."""
        return cls.create_request(
            your_team_number=your_team_number,
            use_batching=True,
            batch_size=batch_size,
            **kwargs
        )
    
    @classmethod
    def create_custom_priorities_request(
        cls,
        metric_weights: List[tuple],
        **kwargs
    ) -> PicklistGenerationRequest:
        """Create request with custom priority metrics."""
        priorities = [
            PriorityMetric(id=metric_id, name=name, weight=weight)
            for metric_id, name, weight in metric_weights
        ]
        
        return cls.create_request(priorities=priorities, **kwargs)


class MockResponseFactory:
    """Factory for generating mock API responses."""
    
    @classmethod
    def create_gpt_response(
        cls,
        team_numbers: List[int],
        format_type: str = "ultra_compact"
    ) -> str:
        """Create mock GPT response in specified format."""
        
        if format_type == "ultra_compact":
            # Ultra-compact format: {"p": [[team, score, reasoning], ...]}
            rankings = []
            for i, team_num in enumerate(team_numbers):
                score = 95.0 - (i * 2.5)
                reasoning = cls._generate_reasoning(team_num, score)
                rankings.append([team_num, score, reasoning])
            
            response = {"p": rankings}
            
        elif format_type == "standard":
            # Standard format
            rankings = []
            for i, team_num in enumerate(team_numbers):
                score = 95.0 - (i * 2.5)
                rankings.append({
                    "team_number": team_num,
                    "score": score,
                    "reasoning": cls._generate_reasoning(team_num, score)
                })
            
            response = {"picklist": rankings}
            
        else:  # markdown_wrapped
            # Wrapped in markdown code block
            rankings = []
            for i, team_num in enumerate(team_numbers):
                score = 95.0 - (i * 2.5)
                rankings.append([team_num, score, cls._generate_reasoning(team_num, score)])
            
            response_json = json.dumps({"p": rankings})
            return f"```json\n{response_json}\n```"
        
        return json.dumps(response)
    
    @classmethod
    def create_ranked_teams(
        cls,
        team_numbers: List[int],
        include_tiers: bool = True
    ) -> List[RankedTeam]:
        """Create list of ranked teams."""
        ranked_teams = []
        
        for i, team_num in enumerate(team_numbers):
            score = 95.0 - (i * 2.5)
            
            # Determine tier based on score
            if score >= 90:
                tier = "S"
            elif score >= 80:
                tier = "A"
            elif score >= 70:
                tier = "B"
            else:
                tier = "C"
            
            ranked_team = RankedTeam(
                team_number=team_num,
                nickname=f"Team {team_num}",
                score=score,
                reasoning=cls._generate_reasoning(team_num, score),
                rank=i + 1,
                tier=tier if include_tiers else None,
                strengths=cls._generate_strengths(score),
                weaknesses=cls._generate_weaknesses(score),
                pick_probability=max(0.1, 1.0 - (i * 0.1))
            )
            
            ranked_teams.append(ranked_team)
        
        return ranked_teams
    
    @classmethod
    def create_picklist_result(
        cls,
        team_numbers: List[int],
        status: str = "success",
        **kwargs
    ) -> PicklistGenerationResult:
        """Create complete picklist generation result."""
        ranked_teams = cls.create_ranked_teams(team_numbers)
        
        return PicklistGenerationResult(
            status=status,
            picklist=ranked_teams,
            analysis=kwargs.get("analysis", {
                "total_teams_evaluated": len(team_numbers),
                "strategy_effectiveness": 0.85,
                "confidence_score": 0.78
            }),
            missing_team_numbers=kwargs.get("missing_team_numbers", []),
            performance=kwargs.get("performance", {
                "generation_time": 12.5,
                "token_usage": 2500,
                "api_calls": 1
            }),
            error_message=kwargs.get("error_message")
        )
    
    @staticmethod
    def _generate_reasoning(team_number: int, score: float) -> str:
        """Generate realistic reasoning for a team ranking."""
        if score >= 90:
            templates = [
                f"Team {team_number} demonstrates exceptional performance across all game phases with consistent high scoring and reliable autonomous routines.",
                f"Elite team {team_number} shows outstanding strategic gameplay and clutch performance in elimination matches.",
                f"Team {team_number} combines strong technical execution with excellent game strategy and alliance coordination."
            ]
        elif score >= 80:
            templates = [
                f"Team {team_number} shows strong performance with good consistency in key scoring areas and solid defensive capabilities.",
                f"Reliable team {team_number} with above-average scoring and good strategic awareness in match play.",
                f"Team {team_number} demonstrates solid fundamentals with particular strength in autonomous and endgame phases."
            ]
        elif score >= 70:
            templates = [
                f"Team {team_number} shows decent performance with room for improvement in consistency and strategic execution.",
                f"Average team {team_number} with adequate scoring ability but some reliability concerns in high-pressure situations.",
                f"Team {team_number} has potential but needs more consistent execution across all game phases."
            ]
        else:
            templates = [
                f"Team {team_number} shows developing skills but struggles with consistency and strategic execution.",
                f"Lower-tier team {team_number} with limited scoring ability and reliability issues in competitive matches.",
                f"Team {team_number} needs significant improvement in fundamental game mechanics and strategic awareness."
            ]
        
        return random.choice(templates)
    
    @staticmethod
    def _generate_strengths(score: float) -> List[str]:
        """Generate strengths based on score."""
        all_strengths = [
            "Autonomous", "Teleop Scoring", "Endgame", "Defense", "Reliability",
            "Strategy", "Speed", "Accuracy", "Consistency", "Clutch Performance",
            "Alliance Coordination", "Adaptability"
        ]
        
        if score >= 90:
            return random.sample(all_strengths, 4)
        elif score >= 80:
            return random.sample(all_strengths, 3)
        elif score >= 70:
            return random.sample(all_strengths, 2)
        else:
            return random.sample(all_strengths, 1)
    
    @staticmethod
    def _generate_weaknesses(score: float) -> List[str]:
        """Generate weaknesses based on score."""
        all_weaknesses = [
            "Autonomous Consistency", "Teleop Speed", "Endgame Reliability",
            "Defensive Positioning", "Strategy Adaptation", "Pressure Performance",
            "Mechanical Reliability", "Driver Skill", "Communication"
        ]
        
        if score >= 90:
            return random.sample(all_weaknesses, 1)
        elif score >= 80:
            return random.sample(all_weaknesses, 2)
        elif score >= 70:
            return random.sample(all_weaknesses, 3)
        else:
            return random.sample(all_weaknesses, 4)


def create_test_scenario(
    scenario_type: str,
    **kwargs
) -> Dict[str, Any]:
    """Create complete test scenario with dataset, request, and expected results."""
    
    scenarios = {
        "small_regional": {
            "dataset": DatasetFactory.create_dataset(
                team_count=20,
                event_key="2025small",
                event_name="Small Regional"
            ),
            "request": PicklistRequestFactory.create_request(
                your_team_number=1005,
                strategy_type="balanced"
            ),
            "expected_teams": 10
        },
        
        "large_regional": {
            "dataset": DatasetFactory.create_dataset(
                team_count=60,
                event_key="2025large",
                event_name="Large Regional"
            ),
            "request": PicklistRequestFactory.create_batch_request(
                your_team_number=1030,
                batch_size=8
            ),
            "expected_teams": 30
        },
        
        "championship": {
            "dataset": DatasetFactory.create_championship_dataset(),
            "request": PicklistRequestFactory.create_request(
                your_team_number=1150,
                strategy_type="auto_focused",
                use_batching=True,
                batch_size=12
            ),
            "expected_teams": 50
        },
        
        "defensive_strategy": {
            "dataset": DatasetFactory.create_dataset(
                team_count=40,
                event_key="2025defense",
                event_name="Defense-Focused Event"
            ),
            "request": PicklistRequestFactory.create_request(
                your_team_number=1020,
                strategy_type="defensive"
            ),
            "expected_teams": 20
        }
    }
    
    scenario = scenarios.get(scenario_type, scenarios["small_regional"])
    scenario.update(kwargs)
    
    return scenario