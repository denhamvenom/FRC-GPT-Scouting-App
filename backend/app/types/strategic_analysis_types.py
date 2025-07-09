# backend/app/types/strategic_analysis_types.py

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class StrategicRole(Enum):
    """Strategic roles for team classification."""
    OFFENSIVE_POWERHOUSE = "offensive_powerhouse"
    DEFENSIVE_SPECIALIST = "defensive_specialist"
    BALANCED_CONTRIBUTOR = "balanced_contributor"
    AUTO_SPECIALIST = "auto_specialist"
    ENDGAME_CLUTCH = "endgame_clutch"
    DEVELOPING_TEAM = "developing_team"
    VERSATILE_PERFORMER = "versatile_performer"
    SPECIALIZED_SCORER = "specialized_scorer"


class StrategicTier(Enum):
    """Performance-based strategic tiers."""
    DOMINANT = "dominant"          # 90th+ percentile performers
    STRONG = "strong"              # 75th+ percentile performers
    SOLID = "solid"                # 50th+ percentile performers
    DEVELOPING = "developing"      # Improving teams with potential
    STRUGGLING = "struggling"      # Below median performers


@dataclass
class StrategicSignature:
    """Enhanced performance signature with strategic context."""
    metric_name: str
    base_signature: str  # e.g., "4.2±0.3 (consistent, n=5, stable)"
    strategic_qualifier: str  # e.g., "dominant_consistent_scorer"
    percentile_rank: float
    field_context: str  # e.g., "field_mean_2.1"


@dataclass
class TeamStrategicProfile:
    """Complete strategic profile for a team."""
    team_number: int
    nickname: str
    strategic_signatures: Dict[str, StrategicSignature]
    strategic_role: StrategicRole
    strategic_tier: StrategicTier
    overall_percentile: float
    key_strengths: List[str]
    development_areas: List[str]
    alliance_value: str
    batch_number: Optional[int] = None


@dataclass
class BatchInfo:
    """Information about batch processing."""
    batch_number: int
    total_batches: int
    teams_in_batch: int
    teams_processed: int
    missing_teams: List[int]
    processing_status: str


@dataclass
class BatchInsights:
    """Strategic insights from batch analysis."""
    standout_performers: List[int]  # Team indices
    developing_teams: List[int]     # Team indices
    specialist_roles: Dict[str, List[int]]  # Role -> team indices
    competitive_notes: List[str]


@dataclass
class StrategicAnalysisResult:
    """Complete result from strategic analysis processing."""
    status: str
    strategic_signatures: Dict[int, TeamStrategicProfile]  # team_number -> profile
    event_baselines: Dict[str, Any]
    processing_summary: Dict[str, Any]
    batch_insights: List[BatchInsights]
    generation_timestamp: float
    error_details: Optional[str] = None


@dataclass
class EventCompetitiveContext:
    """Competitive context for the event."""
    total_teams: int
    avg_matches_per_team: float
    event_level: str  # "regional", "district", "championship"
    metrics_available: int
    data_quality: str  # "good", "limited", "poor"
    score_inflation: str  # "low", "moderate", "high"
    competitive_balance: str  # "tight", "spread", "dominated"


@dataclass
class StrategicIntelligence:
    """Complete strategic intelligence package."""
    event_key: str
    analysis_timestamp: float
    team_profiles: Dict[int, TeamStrategicProfile]
    competitive_context: EventCompetitiveContext
    strategic_trends: Dict[str, Any]
    alliance_recommendations: List[str]
    processing_metadata: Dict[str, Any]


# Type aliases for common patterns
StrategicSignatureDict = Dict[str, StrategicSignature]
TeamProfileDict = Dict[int, TeamStrategicProfile]
BatchResultDict = Dict[str, Any]
EventBaselinesDict = Dict[str, Any]


def create_strategic_signature(
    metric_name: str,
    value: float,
    std: float,
    sample_size: int,
    percentile_rank: float,
    strategic_qualifier: str,
    field_mean: float
) -> StrategicSignature:
    """
    Create a strategic signature from components.
    
    Args:
        metric_name: Name of the metric
        value: Team's average value
        std: Standard deviation
        sample_size: Number of samples
        percentile_rank: Team's percentile rank in field
        strategic_qualifier: Strategic qualifier (e.g., "dominant_consistent")
        field_mean: Event field mean for context
        
    Returns:
        Complete StrategicSignature object
    """
    base_signature = f"{value:.1f}±{std:.1f} ({strategic_qualifier}, n={sample_size})"
    field_context = f"field_mean_{field_mean:.1f}"
    
    return StrategicSignature(
        metric_name=metric_name,
        base_signature=base_signature,
        strategic_qualifier=strategic_qualifier,
        percentile_rank=percentile_rank,
        field_context=field_context
    )


def classify_strategic_tier(percentile_rank: float, trend: str = "stable") -> StrategicTier:
    """
    Classify team into strategic tier based on performance.
    
    Args:
        percentile_rank: Team's percentile rank (0-100)
        trend: Performance trend ("improving", "stable", "declining")
        
    Returns:
        StrategicTier classification
    """
    if percentile_rank >= 90:
        return StrategicTier.DOMINANT
    elif percentile_rank >= 75:
        return StrategicTier.STRONG
    elif percentile_rank >= 50:
        return StrategicTier.SOLID
    elif trend == "improving" or percentile_rank >= 25:
        return StrategicTier.DEVELOPING
    else:
        return StrategicTier.STRUGGLING


def determine_strategic_role(
    signatures: Dict[str, StrategicSignature],
    overall_percentile: float
) -> StrategicRole:
    """
    Determine primary strategic role based on performance signatures.
    
    Args:
        signatures: Dictionary of strategic signatures
        overall_percentile: Team's overall percentile rank
        
    Returns:
        Primary StrategicRole for the team
    """
    # Count strong performance areas (75th+ percentile)
    strong_areas = [
        sig for sig in signatures.values() 
        if sig.percentile_rank >= 75
    ]
    
    # Analyze signature qualifiers for specialization patterns
    qualifiers = [sig.strategic_qualifier for sig in signatures.values()]
    
    # Check for specific specializations
    if any("auto" in q for q in qualifiers) and len(strong_areas) <= 2:
        return StrategicRole.AUTO_SPECIALIST
    
    if any("endgame" in q or "climb" in q for q in qualifiers) and len(strong_areas) <= 2:
        return StrategicRole.ENDGAME_CLUTCH
    
    if any("defense" in q for q in qualifiers):
        return StrategicRole.DEFENSIVE_SPECIALIST
    
    # General role classification based on overall performance
    if overall_percentile >= 85 and len(strong_areas) >= 4:
        return StrategicRole.VERSATILE_PERFORMER
    elif overall_percentile >= 85 and len(strong_areas) >= 3:
        return StrategicRole.OFFENSIVE_POWERHOUSE
    elif overall_percentile >= 50:
        return StrategicRole.BALANCED_CONTRIBUTOR
    elif len(strong_areas) >= 1:
        return StrategicRole.SPECIALIZED_SCORER
    else:
        return StrategicRole.DEVELOPING_TEAM


def extract_key_strengths(signatures: Dict[str, StrategicSignature]) -> List[str]:
    """
    Extract key strengths from strategic signatures.
    
    Args:
        signatures: Dictionary of strategic signatures
        
    Returns:
        List of key strength descriptions
    """
    strengths = []
    
    for metric_name, sig in signatures.items():
        if sig.percentile_rank >= 75:  # Strong performance
            qualifier = sig.strategic_qualifier
            if "dominant" in qualifier:
                strengths.append(f"Dominant {metric_name.lower().replace('_', ' ')}")
            elif "strong" in qualifier:
                strengths.append(f"Strong {metric_name.lower().replace('_', ' ')}")
            elif "consistent" in qualifier:
                strengths.append(f"Consistent {metric_name.lower().replace('_', ' ')}")
    
    return strengths[:5]  # Limit to top 5 strengths


def identify_development_areas(signatures: Dict[str, StrategicSignature]) -> List[str]:
    """
    Identify areas needing development from strategic signatures.
    
    Args:
        signatures: Dictionary of strategic signatures
        
    Returns:
        List of development area descriptions
    """
    development_areas = []
    
    for metric_name, sig in signatures.items():
        if sig.percentile_rank <= 25:  # Weak performance
            qualifier = sig.strategic_qualifier
            if "struggling" in qualifier:
                development_areas.append(f"Needs improvement in {metric_name.lower().replace('_', ' ')}")
            elif "volatile" in qualifier or "unpredictable" in qualifier:
                development_areas.append(f"Inconsistent {metric_name.lower().replace('_', ' ')}")
    
    return development_areas[:3]  # Limit to top 3 areas


# Constants for strategic analysis
DEFAULT_BATCH_SIZE = 20
MIN_TEAMS_FOR_ANALYSIS = 5
MAX_TEAMS_PER_BATCH = 25
STRATEGIC_PERCENTILE_THRESHOLDS = {
    "dominant": 90.0,
    "strong": 75.0,
    "solid": 50.0,
    "developing": 25.0,
    "struggling": 0.0
}

# GPT prompt constants
STRATEGIC_ANALYSIS_TEMPERATURE = 0.1
STRATEGIC_ANALYSIS_MAX_TOKENS = 4000
STRATEGIC_ANALYSIS_TIMEOUT = 30.0