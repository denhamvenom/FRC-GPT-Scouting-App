"""
Data models for the picklist service.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PickPosition(str, Enum):
    """Valid pick positions for alliance selection."""

    FIRST = "first"
    SECOND = "second"
    THIRD = "third"


class ReferenceSelectionStrategy(str, Enum):
    """Strategies for selecting reference teams in batch processing."""

    EVEN_DISTRIBUTION = "even_distribution"
    PERCENTILE = "percentile"
    TOP_MIDDLE_BOTTOM = "top_middle_bottom"


@dataclass
class TeamMetrics:
    """Team performance metrics."""

    team_number: int
    nickname: str
    metrics: Dict[str, float] = field(default_factory=dict)
    match_count: int = 0
    rank: Optional[int] = None
    record: Optional[Dict[str, int]] = None
    superscouting_notes: List[str] = field(default_factory=list)


@dataclass
class PriorityMetric:
    """A metric priority for ranking teams."""

    id: str
    name: str
    weight: float = 1.0
    description: Optional[str] = None


@dataclass
class RankedTeam:
    """A team with its ranking information."""

    team_number: int
    nickname: str
    score: float
    reasoning: str
    rank: Optional[int] = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class PicklistGenerationRequest:
    """Request parameters for picklist generation."""

    your_team_number: int
    pick_position: PickPosition
    priorities: List[PriorityMetric]
    exclude_teams: List[int] = field(default_factory=list)
    request_id: Optional[int] = None
    cache_key: Optional[str] = None
    batch_size: int = 20
    reference_teams_count: int = 3
    reference_selection: ReferenceSelectionStrategy = ReferenceSelectionStrategy.TOP_MIDDLE_BOTTOM
    use_batching: bool = False
    final_rerank: bool = True


@dataclass
class PicklistGenerationResult:
    """Result of picklist generation."""

    status: str
    picklist: List[RankedTeam]
    analysis: Dict[str, str] = field(default_factory=dict)
    missing_team_numbers: List[int] = field(default_factory=list)
    performance: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class BatchProcessingStatus:
    """Status of batch processing operation."""

    total_batches: int
    current_batch: int
    progress_percentage: int
    processing_complete: bool
    error: Optional[str] = None


@dataclass
class GPTPrompt:
    """A prompt for GPT with system and user messages."""

    system_message: str
    user_message: str
    max_tokens: int = 4000
    temperature: float = 0.1


@dataclass
class TeamBatch:
    """A batch of teams for processing."""

    batch_index: int
    teams: List[TeamMetrics]
    reference_teams: List[RankedTeam] = field(default_factory=list)