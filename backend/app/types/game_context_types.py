# backend/app/types/game_context_types.py

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class StrategicValue(Enum):
    """Enumeration for strategic value levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Importance(Enum):
    """Enumeration for importance levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ScoringPhase:
    """Represents scoring information for a game phase."""
    duration_seconds: int
    key_objectives: List[str]
    point_values: Dict[str, Union[int, float]]
    strategic_notes: str


@dataclass
class StrategicElement:
    """Represents a strategic element in the game."""
    name: str
    description: str
    strategic_value: StrategicValue
    alliance_impact: str


@dataclass
class KeyMetric:
    """Represents a key metric for team evaluation."""
    metric_name: str
    description: str
    importance: Importance
    calculation_hint: str


@dataclass
class GamePiece:
    """Represents a game piece and its scoring opportunities."""
    name: str
    scoring_locations: List[str]
    point_values: Dict[str, Union[int, float]]
    strategic_notes: str


@dataclass
class ScoringSummary:
    """Complete scoring summary for all game phases."""
    autonomous: ScoringPhase
    teleop: ScoringPhase
    endgame: ScoringPhase


@dataclass
class ExtractedGameContext:
    """
    Complete extracted game context structure.
    
    This represents the optimized, essential information extracted
    from the full game manual for use in picklist generation.
    """
    game_year: int
    game_name: str
    extraction_version: str
    extraction_date: str
    scoring_summary: ScoringSummary
    strategic_elements: List[StrategicElement]
    alliance_considerations: List[str]
    key_metrics: List[KeyMetric]
    game_pieces: List[GamePiece]
    original_manual_hash: str


class ExtractionConfig:
    """Configuration for extraction parameters."""
    
    def __init__(
        self,
        max_strategic_elements: int = 10,
        max_alliance_considerations: int = 8,
        max_key_metrics: int = 12,
        max_game_pieces: int = 6,
        extraction_temperature: float = 0.1,
        max_extraction_tokens: int = 4000,
        cache_ttl_hours: int = 168,  # 1 week
        validation_threshold: float = 0.8
    ):
        """
        Initialize extraction configuration.
        
        Args:
            max_strategic_elements: Maximum number of strategic elements to extract
            max_alliance_considerations: Maximum alliance considerations
            max_key_metrics: Maximum key metrics to extract
            max_game_pieces: Maximum game pieces to track
            extraction_temperature: Temperature for GPT extraction (lower = more consistent)
            max_extraction_tokens: Maximum tokens for extraction response
            cache_ttl_hours: Time to live for cached extractions in hours
            validation_threshold: Minimum validation score to accept extraction
        """
        self.max_strategic_elements = max_strategic_elements
        self.max_alliance_considerations = max_alliance_considerations
        self.max_key_metrics = max_key_metrics
        self.max_game_pieces = max_game_pieces
        self.extraction_temperature = extraction_temperature
        self.max_extraction_tokens = max_extraction_tokens
        self.cache_ttl_hours = cache_ttl_hours
        self.validation_threshold = validation_threshold


# Type aliases for common usage
GameContextDict = Dict[str, Any]
ManualData = Dict[str, Any]
TokenUsage = Dict[str, int]
ValidationIssues = List[str]
CacheInfo = Dict[str, Any]


def validate_extracted_context_schema(data: Dict[str, Any]) -> List[str]:
    """
    Validate that extracted context matches the expected schema.
    
    Args:
        data: Dictionary to validate against schema
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required top-level fields
    required_fields = [
        'game_year', 'game_name', 'extraction_version', 'extraction_date',
        'scoring_summary', 'strategic_elements', 'alliance_considerations',
        'key_metrics', 'game_pieces'
    ]
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            errors.append(f"Field cannot be null: {field}")
    
    # Validate game_year
    if 'game_year' in data:
        if not isinstance(data['game_year'], int) or data['game_year'] < 1992:
            errors.append("game_year must be a valid integer >= 1992")
    
    # Validate scoring_summary structure
    if 'scoring_summary' in data and isinstance(data['scoring_summary'], dict):
        required_phases = ['autonomous', 'teleop', 'endgame']
        for phase in required_phases:
            if phase not in data['scoring_summary']:
                errors.append(f"Missing scoring phase: {phase}")
            elif isinstance(data['scoring_summary'][phase], dict):
                phase_data = data['scoring_summary'][phase]
                required_phase_fields = ['duration_seconds', 'key_objectives', 'point_values', 'strategic_notes']
                for field in required_phase_fields:
                    if field not in phase_data:
                        errors.append(f"Missing field in {phase}: {field}")
    
    # Validate strategic_elements
    if 'strategic_elements' in data:
        if not isinstance(data['strategic_elements'], list):
            errors.append("strategic_elements must be a list")
        else:
            for i, element in enumerate(data['strategic_elements']):
                if not isinstance(element, dict):
                    errors.append(f"strategic_elements[{i}] must be a dictionary")
                else:
                    required_element_fields = ['name', 'description', 'strategic_value', 'alliance_impact']
                    for field in required_element_fields:
                        if field not in element:
                            errors.append(f"Missing field in strategic_elements[{i}]: {field}")
                    
                    # Validate strategic_value enum
                    if 'strategic_value' in element:
                        valid_values = ['high', 'medium', 'low']
                        if element['strategic_value'] not in valid_values:
                            errors.append(f"Invalid strategic_value in element[{i}]: must be one of {valid_values}")
    
    # Validate key_metrics
    if 'key_metrics' in data:
        if not isinstance(data['key_metrics'], list):
            errors.append("key_metrics must be a list")
        else:
            for i, metric in enumerate(data['key_metrics']):
                if not isinstance(metric, dict):
                    errors.append(f"key_metrics[{i}] must be a dictionary")
                else:
                    required_metric_fields = ['metric_name', 'description', 'importance', 'calculation_hint']
                    for field in required_metric_fields:
                        if field not in metric:
                            errors.append(f"Missing field in key_metrics[{i}]: {field}")
                    
                    # Validate importance enum
                    if 'importance' in metric:
                        valid_importance = ['high', 'medium', 'low']
                        if metric['importance'] not in valid_importance:
                            errors.append(f"Invalid importance in metric[{i}]: must be one of {valid_importance}")
    
    # Validate game_pieces
    if 'game_pieces' in data:
        if not isinstance(data['game_pieces'], list):
            errors.append("game_pieces must be a list")
        else:
            for i, piece in enumerate(data['game_pieces']):
                if not isinstance(piece, dict):
                    errors.append(f"game_pieces[{i}] must be a dictionary")
                else:
                    required_piece_fields = ['name', 'scoring_locations', 'point_values', 'strategic_notes']
                    for field in required_piece_fields:
                        if field not in piece:
                            errors.append(f"Missing field in game_pieces[{i}]: {field}")
    
    return errors


def create_sample_extracted_context() -> ExtractedGameContext:
    """
    Create a sample extracted context for testing and documentation.
    
    Returns:
        Sample ExtractedGameContext with realistic data
    """
    return ExtractedGameContext(
        game_year=2025,
        game_name="REEFSCAPE",
        extraction_version="1.0",
        extraction_date="2025-06-26T10:30:00",
        scoring_summary=ScoringSummary(
            autonomous=ScoringPhase(
                duration_seconds=15,
                key_objectives=["Score algae in processor", "Navigate to reef zones"],
                point_values={"algae_processor": 4, "coral_placement": 3},
                strategic_notes="Focus on consistent algae scoring for auto bonus"
            ),
            teleop=ScoringPhase(
                duration_seconds=135,
                key_objectives=["Coral placement", "Algae processing", "Defensive play"],
                point_values={"coral_L1": 2, "coral_L2": 4, "coral_L3": 6, "algae_net": 1},
                strategic_notes="Coral scoring scales exponentially, prioritize higher levels"
            ),
            endgame=ScoringPhase(
                duration_seconds=30,
                key_objectives=["Shallow climb", "Deep climb", "Barge support"],
                point_values={"shallow_climb": 3, "deep_climb": 12, "barge_support": 2},
                strategic_notes="Deep climb provides significant points but requires capability"
            )
        ),
        strategic_elements=[
            StrategicElement(
                name="Coral Placement Capability",
                description="Ability to score coral at different levels",
                strategic_value=StrategicValue.HIGH,
                alliance_impact="High-level coral scoring teams are essential for competitive alliances"
            )
        ],
        alliance_considerations=[
            "Balance coral placement and algae processing capabilities",
            "Ensure at least one deep climb capable robot per alliance"
        ],
        key_metrics=[
            KeyMetric(
                metric_name="Average Coral per Match",
                description="Average number of coral scored per match",
                importance=Importance.HIGH,
                calculation_hint="Sum coral from all levels divided by matches played"
            )
        ],
        game_pieces=[
            GamePiece(
                name="Coral",
                scoring_locations=["L1 Branch", "L2 Branch", "L3 Branch", "Processor"],
                point_values={"L1": 2, "L2": 4, "L3": 6, "Processor": 3},
                strategic_notes="Higher levels provide exponentially more points"
            )
        ],
        original_manual_hash="abc123def456"
    )


# Constants for validation and limits
MAX_EXTRACTION_SIZE_KB = 50  # Maximum size for extracted context
MIN_STRATEGIC_ELEMENTS = 3   # Minimum strategic elements required
MIN_KEY_METRICS = 5          # Minimum key metrics required
SUPPORTED_GAME_YEARS = list(range(2020, 2030))  # Supported game years