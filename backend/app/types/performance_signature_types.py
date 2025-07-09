# backend/app/types/performance_signature_types.py

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import statistics
import math


class PerformanceTier(Enum):
    """Game-agnostic performance level classifications."""
    DOMINANT = "dominant"      # 90th+ percentile
    STRONG = "strong"          # 75th+ percentile  
    SOLID = "solid"            # 50th+ percentile
    DEVELOPING = "developing"  # Improving trend
    STRUGGLING = "struggling"  # Below median


class ReliabilityTier(Enum):
    """Game-agnostic reliability classifications based on coefficient of variation."""
    MACHINE_LIKE = "machine_like"      # CV < 15%
    CONSISTENT = "consistent"          # CV 15-25%
    RELIABLE = "reliable"              # CV 25-40%
    VOLATILE = "volatile"              # CV 40-60%
    UNPREDICTABLE = "unpredictable"    # CV > 60%


class TrendIndicator(Enum):
    """Trend analysis indicators."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    LIMITED_DATA = "limited_data"


@dataclass
class MetricStatistics:
    """Core statistical measures for a metric."""
    mean: float
    std: float
    median: float
    min_value: float
    max_value: float
    sample_size: int
    coefficient_of_variation: float
    
    def __post_init__(self):
        """Calculate derived statistics."""
        if self.mean != 0:
            self.coefficient_of_variation = self.std / abs(self.mean)
        else:
            self.coefficient_of_variation = float('inf')


@dataclass
class EventBaseline:
    """Statistical baseline for a metric across the entire event."""
    metric_name: str
    statistics: MetricStatistics
    percentiles: Dict[str, float]  # {"10th": 0.5, "25th": 1.2, "50th": 2.1, "75th": 3.8, "90th": 5.2}
    field_size: int
    top_performers: int  # Number of teams above 90th percentile
    
    def get_percentile_rank(self, value: float) -> float:
        """Calculate percentile rank for a given value."""
        percentile_values = sorted(self.percentiles.values())
        percentile_keys = sorted([int(k.replace('th', '')) for k in self.percentiles.keys()])
        
        if value <= percentile_values[0]:
            return percentile_keys[0]
        elif value >= percentile_values[-1]:
            return percentile_keys[-1]
        else:
            # Linear interpolation between percentiles
            for i in range(len(percentile_values) - 1):
                if percentile_values[i] <= value <= percentile_values[i + 1]:
                    ratio = (value - percentile_values[i]) / (percentile_values[i + 1] - percentile_values[i])
                    return percentile_keys[i] + ratio * (percentile_keys[i + 1] - percentile_keys[i])
        return 50.0  # Default to median


@dataclass  
class PerformanceSignature:
    """Complete performance signature for a metric."""
    metric_name: str
    team_statistics: MetricStatistics
    event_baseline: EventBaseline
    performance_tier: PerformanceTier
    reliability_tier: ReliabilityTier
    trend_indicator: TrendIndicator
    percentile_rank: float
    signature_string: str
    strategic_context: Optional[str] = None
    
    @classmethod
    def create_signature_string(
        cls,
        stats: MetricStatistics,
        performance_tier: PerformanceTier,
        reliability_tier: ReliabilityTier,
        trend_indicator: TrendIndicator,
        percentile_rank: float,
        strategic_context: Optional[str] = None
    ) -> str:
        """Create the formatted signature string."""
        base = f"{stats.mean:.1f}±{stats.std:.1f} ({performance_tier.value}_{reliability_tier.value}, n={stats.sample_size}, {trend_indicator.value})"
        
        if strategic_context:
            return f"{base}, {strategic_context}"
        return base


@dataclass
class TeamPerformanceProfile:
    """Complete performance profile for a team across all metrics."""
    team_number: int
    nickname: str
    signatures: Dict[str, PerformanceSignature]
    match_count: int
    overall_percentile: float
    strategic_profile: Optional[str] = None
    
    def get_signature(self, metric_name: str) -> Optional[PerformanceSignature]:
        """Get performance signature for a specific metric."""
        return self.signatures.get(metric_name)
    
    def get_top_metrics(self, min_percentile: float = 75.0) -> List[PerformanceSignature]:
        """Get metrics where team performs above given percentile."""
        return [sig for sig in self.signatures.values() if sig.percentile_rank >= min_percentile]


@dataclass
class EventPerformanceBaselines:
    """Complete statistical baselines for an entire event."""
    event_key: str
    year: int
    baselines: Dict[str, EventBaseline]
    total_teams: int
    avg_matches_per_team: float
    event_level: str  # "regional", "district", "championship"
    competitive_context: Dict[str, Any]
    
    def get_baseline(self, metric_name: str) -> Optional[EventBaseline]:
        """Get baseline for a specific metric."""
        return self.baselines.get(metric_name)
    
    def get_metric_names(self) -> List[str]:
        """Get all available metric names."""
        return list(self.baselines.keys())


def classify_performance_tier(percentile_rank: float, trend: TrendIndicator) -> PerformanceTier:
    """Classify performance tier based on percentile and trend."""
    if percentile_rank >= 90:
        return PerformanceTier.DOMINANT
    elif percentile_rank >= 75:
        return PerformanceTier.STRONG
    elif percentile_rank >= 50:
        return PerformanceTier.SOLID
    elif trend == TrendIndicator.IMPROVING:
        return PerformanceTier.DEVELOPING
    else:
        return PerformanceTier.STRUGGLING


def classify_reliability_tier(coefficient_of_variation: float) -> ReliabilityTier:
    """Classify reliability tier based on coefficient of variation."""
    if coefficient_of_variation < 0.15:
        return ReliabilityTier.MACHINE_LIKE
    elif coefficient_of_variation < 0.25:
        return ReliabilityTier.CONSISTENT
    elif coefficient_of_variation < 0.40:
        return ReliabilityTier.RELIABLE
    elif coefficient_of_variation < 0.60:
        return ReliabilityTier.VOLATILE
    else:
        return ReliabilityTier.UNPREDICTABLE


def analyze_trend(values: List[Union[int, float]], min_samples: int = 3) -> TrendIndicator:
    """Analyze trend in performance values using simple linear regression."""
    if len(values) < min_samples:
        return TrendIndicator.LIMITED_DATA
    
    try:
        n = len(values)
        x_values = list(range(n))
        
        # Calculate means
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        # Calculate slope using least squares
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return TrendIndicator.STABLE
        
        slope = numerator / denominator
        
        # Determine significance threshold based on data variance
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        threshold = std_dev * 0.1  # 10% of standard deviation
        
        if slope > threshold:
            return TrendIndicator.IMPROVING
        elif slope < -threshold:
            return TrendIndicator.DECLINING
        else:
            return TrendIndicator.STABLE
            
    except Exception:
        return TrendIndicator.LIMITED_DATA


def calculate_metric_statistics(values: List[Union[int, float]]) -> MetricStatistics:
    """Calculate comprehensive statistics for a list of metric values."""
    if not values:
        raise ValueError("Cannot calculate statistics for empty values list")
    
    float_values = [float(v) for v in values]
    
    mean_val = statistics.mean(float_values)
    std_val = statistics.stdev(float_values) if len(float_values) > 1 else 0.0
    median_val = statistics.median(float_values)
    
    return MetricStatistics(
        mean=mean_val,
        std=std_val,
        median=median_val,
        min_value=min(float_values),
        max_value=max(float_values),
        sample_size=len(values),
        coefficient_of_variation=0.0  # Will be calculated in __post_init__
    )


def calculate_percentiles(values: List[Union[int, float]]) -> Dict[str, float]:
    """Calculate standard percentiles for a dataset."""
    if not values:
        return {}
    
    sorted_values = sorted([float(v) for v in values])
    n = len(sorted_values)
    percentile_points = [10, 25, 50, 75, 90]
    
    percentiles = {}
    for p in percentile_points:
        # Calculate percentile using linear interpolation
        if p == 50:
            percentiles[f"{p}th"] = statistics.median(sorted_values)
        else:
            index = (p / 100) * (n - 1)
            lower_index = int(index)
            upper_index = min(lower_index + 1, n - 1)
            
            if lower_index == upper_index:
                percentiles[f"{p}th"] = sorted_values[lower_index]
            else:
                # Linear interpolation
                fraction = index - lower_index
                percentiles[f"{p}th"] = (
                    sorted_values[lower_index] * (1 - fraction) +
                    sorted_values[upper_index] * fraction
                )
    
    return percentiles


# Constants for signature generation
DEFAULT_MIN_SAMPLE_SIZE = 3
DEFAULT_MAX_SAMPLE_SIZE = 15
SIGNATURE_VERSION = "1.0"

# Performance tier thresholds
PERFORMANCE_PERCENTILE_THRESHOLDS = {
    PerformanceTier.DOMINANT: 90.0,
    PerformanceTier.STRONG: 75.0,
    PerformanceTier.SOLID: 50.0,
    PerformanceTier.DEVELOPING: 25.0,
    PerformanceTier.STRUGGLING: 0.0
}

# Reliability tier thresholds
RELIABILITY_CV_THRESHOLDS = {
    ReliabilityTier.MACHINE_LIKE: 0.15,
    ReliabilityTier.CONSISTENT: 0.25,
    ReliabilityTier.RELIABLE: 0.40,
    ReliabilityTier.VOLATILE: 0.60,
    ReliabilityTier.UNPREDICTABLE: float('inf')
}