"""
Picklist API Schemas

This module contains schemas specific to picklist generation and management endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

from .common import BatchRequest


class MetricPriority(BaseModel):
    """Priority configuration for a specific metric"""
    id: str = Field(..., description="Metric identifier from the schema")
    weight: float = Field(1.0, ge=0.5, le=3.0, description="Weight multiplier for this metric")
    reason: Optional[str] = Field(None, description="Explanation for this priority")

    class Config:
        schema_extra = {
            "example": {
                "id": "total_teleop_points",
                "weight": 2.5,
                "reason": "Critical for scoring in elimination matches"
            }
        }


class UserRanking(BaseModel):
    """User-defined ranking for a team"""
    team_number: int = Field(..., gt=0, description="Team number")
    position: int = Field(..., gt=0, description="Ranking position (1-based)")
    nickname: Optional[str] = Field(None, description="Team nickname")

    class Config:
        schema_extra = {
            "example": {
                "team_number": 254,
                "position": 1,
                "nickname": "The Cheesy Poofs"
            }
        }


class TeamRanking(BaseModel):
    """Complete team ranking information"""
    team_number: int = Field(..., description="Team number")
    nickname: Optional[str] = Field(None, description="Team nickname")
    score: float = Field(..., description="Overall ranking score")
    reasoning: str = Field(..., description="Reasoning for this ranking")
    
    # Optional fields for backward compatibility
    rank: Optional[int] = Field(None, description="Overall rank")
    tier: Optional[str] = Field(None, description="Performance tier")
    strengths: Optional[List[str]] = Field(None, description="Key strengths")
    weaknesses: Optional[List[str]] = Field(None, description="Key weaknesses")
    strategy_fit: Optional[str] = Field(None, description="How well team fits strategy")
    recommendation: Optional[str] = Field(None, description="Pick recommendation")
    stats: Optional[Dict[str, Any]] = Field(None, description="Relevant statistics")

    class Config:
        schema_extra = {
            "example": {
                "team_number": 254,
                "nickname": "The Cheesy Poofs",
                "score": 95.5,
                "reasoning": "Strong scorer, reliable performer",
                "rank": 1,
                "tier": "Elite",
                "strengths": ["High scoring", "Consistent auto"],
                "weaknesses": ["Limited endgame"],
                "strategy_fit": "Excellent complement to our capabilities",
                "recommendation": "Strong first pick",
                "stats": {
                    "avg_total_points": 125.5,
                    "auto_success_rate": 0.95
                }
            }
        }


class BatchProcessingStatus(BaseModel):
    """Status information for batch processing"""
    total_batches: int = Field(..., description="Total number of batches")
    current_batch: int = Field(..., description="Current batch being processed")
    completed_batches: int = Field(..., description="Number of completed batches")
    progress_percentage: float = Field(..., ge=0, le=100, description="Overall progress percentage")
    processing_complete: bool = Field(..., description="Whether all processing is complete")
    estimated_time_remaining: Optional[float] = Field(None, description="Estimated seconds remaining")

    class Config:
        schema_extra = {
            "example": {
                "total_batches": 10,
                "current_batch": 4,
                "completed_batches": 3,
                "progress_percentage": 35.0,
                "processing_complete": False,
                "estimated_time_remaining": 120.5
            }
        }


class PicklistGenerateRequest(BaseModel):
    """Request for generating a new picklist"""
    unified_dataset_path: str = Field(..., description="Path to the unified dataset file")
    your_team_number: int = Field(..., gt=0, description="Your team number")
    pick_position: Literal["first", "second", "third"] = Field(..., description="Pick position strategy")
    priorities: List[MetricPriority] = Field(..., min_items=1, description="Metric priorities")
    exclude_teams: Optional[List[int]] = Field(None, description="Teams to exclude from picklist")

    # Batch processing options
    use_batching: bool = Field(False, description="Whether to use batch processing")
    batch_size: int = Field(20, ge=5, le=100, description="Number of teams per batch")
    reference_teams_count: int = Field(3, ge=1, le=10, description="Number of reference teams")
    reference_selection: Literal["even_distribution", "percentile", "top_middle_bottom"] = Field(
        "top_middle_bottom",
        description="Strategy for selecting reference teams"
    )

    # Optional cache key for tracking
    cache_key: Optional[str] = Field(None, description="Optional cache key for progress tracking")

    @validator('priorities')
    def validate_priorities(cls, v):
        """Ensure priorities have unique metric IDs"""
        metric_ids = [p.id for p in v]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("Duplicate metric IDs in priorities")
        return v

    class Config:
        schema_extra = {
            "example": {
                "unified_dataset_path": "/data/events/2025arc_unified.json",
                "your_team_number": 1234,
                "pick_position": "first",
                "priorities": [
                    {"id": "total_teleop_points", "weight": 2.5},
                    {"id": "auto_points", "weight": 1.8}
                ],
                "exclude_teams": [5678, 9012],
                "use_batching": True,
                "batch_size": 20,
                "reference_teams_count": 3,
                "reference_selection": "top_middle_bottom"
            }
        }


class PicklistGenerateResponse(BaseModel):
    """Response from picklist generation"""
    status: str = Field(..., description="Operation status")
    picklist: Optional[List[Dict[str, Any]]] = Field(None, description="Generated picklist")
    cache_key: Optional[str] = Field(None, description="Cache key for status polling")
    batch_processing: Optional[BatchProcessingStatus] = Field(None, description="Batch processing status")
    generation_time: Optional[float] = Field(None, description="Total generation time in seconds")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Generation analysis")
    missing_team_numbers: Optional[List[int]] = Field(None, description="Teams missing from dataset")
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    error_message: Optional[str] = Field(None, description="Error details if status is error")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "picklist": [
                    {
                        "team_number": 254,
                        "rank": 1,
                        "tier": "Elite",
                        "strengths": ["High scoring"],
                        "weaknesses": ["Limited endgame"],
                        "strategy_fit": "Excellent",
                        "recommendation": "Strong first pick",
                        "stats": {"avg_total_points": 125.5}
                    }
                ],
                "cache_key": "abc123",
                "generation_time": 45.2,
                "tokens_used": 15000
            }
        }


class PicklistUpdateRequest(BaseModel):
    """Request for updating an existing picklist"""
    unified_dataset_path: str = Field(..., description="Path to the unified dataset file")
    original_picklist: List[Dict[str, Any]] = Field(..., description="Original picklist to update")
    user_rankings: List[UserRanking] = Field(..., min_items=1, description="User-defined rankings")

    class Config:
        schema_extra = {
            "example": {
                "unified_dataset_path": "/data/events/2025arc_unified.json",
                "original_picklist": [{"team_number": 254, "rank": 1}],
                "user_rankings": [
                    {"team_number": 1234, "position": 1},
                    {"team_number": 254, "position": 2}
                ]
            }
        }


class PicklistUpdateResponse(BaseModel):
    """Response from picklist update"""
    status: Literal["success"] = Field(default="success", description="Always 'success' for successful responses")
    picklist: List[Dict[str, Any]] = Field(..., description="Updated picklist")
    changes_made: int = Field(..., description="Number of position changes")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "picklist": [{"team_number": 1234, "rank": 1}],
                "changes_made": 2
            }
        }


class RankMissingTeamsRequest(BaseModel):
    """Request for ranking teams not in original picklist"""
    unified_dataset_path: str = Field(..., description="Path to the unified dataset file")
    missing_team_numbers: List[int] = Field(..., min_items=1, description="Teams to rank")
    ranked_teams: List[Dict[str, Any]] = Field(..., description="Already ranked teams for context")
    your_team_number: int = Field(..., gt=0, description="Your team number")
    pick_position: Literal["first", "second", "third"] = Field(..., description="Pick position strategy")
    priorities: List[MetricPriority] = Field(..., min_items=1, description="Metric priorities")

    class Config:
        schema_extra = {
            "example": {
                "unified_dataset_path": "/data/events/2025arc_unified.json",
                "missing_team_numbers": [1111, 2222],
                "ranked_teams": [{"team_number": 254, "rank": 1}],
                "your_team_number": 1234,
                "pick_position": "first",
                "priorities": [{"id": "total_teleop_points", "weight": 2.5}]
            }
        }


class RankMissingTeamsResponse(BaseModel):
    """Response from ranking missing teams"""
    status: str = Field(..., description="Operation status")
    picklist: Optional[List[Dict[str, Any]]] = Field(None, description="Rankings for missing teams")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Generation analysis")
    missing_team_numbers: Optional[List[int]] = Field(None, description="Teams missing from dataset")
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    error_message: Optional[str] = Field(None, description="Error details if status is error")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "rankings": [
                    {
                        "team_number": 1111,
                        "rank": 5,
                        "tier": "Strong",
                        "strengths": ["Good auto"],
                        "weaknesses": ["Inconsistent"],
                        "strategy_fit": "Good",
                        "recommendation": "Consider for second pick",
                        "stats": {"avg_total_points": 95.0}
                    }
                ],
                "suggested_positions": {
                    "1111": 5,
                    "2222": 8
                }
            }
        }


class ClearCacheRequest(BaseModel):
    """Request for clearing picklist cache"""
    cache_keys: Optional[List[str]] = Field(None, description="Specific cache keys to clear")
    pick_position: Optional[str] = Field(None, description="Clear all entries for this position")

    class Config:
        schema_extra = {
            "example": {
                "cache_keys": ["abc123", "def456"]
            }
        }
