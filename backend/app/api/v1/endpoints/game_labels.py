# backend/app/api/v1/endpoints/game_labels.py

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from app.services.game_label_extractor_service import GameLabelExtractorService

logger = logging.getLogger("game_labels_api")

router = APIRouter(prefix="/game-labels", tags=["Game Labels"])

# Initialize the service
label_extractor_service = GameLabelExtractorService()


class GameLabel(BaseModel):
    """Model for a scouting data field label."""
    label: str = Field(..., description="Scouting field name (e.g., auto_coral_L1_scored, teleop_defense_rating)")
    category: str = Field(..., description="Category: autonomous|teleop|endgame|defense|reliability|strategic")
    description: str = Field(..., description="What this metric measures about robot performance")
    data_type: str = Field(..., description="Data type: count|rating|boolean|time")
    typical_range: str = Field(..., description="Expected range like 0-10, 1-5, true/false")
    usage_context: str = Field(..., description="When this would be tracked during a match")


class GameLabelExtractionRequest(BaseModel):
    """Request model for label extraction."""
    manual_data: Dict[str, Any] = Field(..., description="Manual data containing game information")
    year: int = Field(..., description="Game year", ge=2000, le=2030)
    force_refresh: bool = Field(False, description="Force re-extraction even if labels exist")


class GameLabelExtractionResponse(BaseModel):
    """Response model for label extraction."""
    success: bool = Field(..., description="Whether extraction was successful")
    labels: List[GameLabel] = Field(default_factory=list, description="Extracted labels")
    labels_count: int = Field(..., description="Number of labels extracted")
    processing_time: float = Field(..., description="Time taken for extraction in seconds")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")


class GameLabelUpdateRequest(BaseModel):
    """Request model for updating labels."""
    labels: List[GameLabel] = Field(..., description="Labels to save")


class GameLabelResponse(BaseModel):
    """Response model for label operations."""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Response message")
    labels_count: int = Field(..., description="Number of labels")
    labels: List[GameLabel] = Field(default_factory=list, description="Labels data")


class ServiceInfoResponse(BaseModel):
    """Response model for service information."""
    data_directory: str = Field(..., description="Directory where labels are stored")
    extraction_version: str = Field(..., description="Current extraction version")
    available_years: List[int] = Field(..., description="Years with available labels")
    total_label_files: int = Field(..., description="Total number of label files")
    model_used: str = Field(..., description="GPT model used for extraction")


@router.post("/extract", response_model=GameLabelExtractionResponse)
async def extract_game_labels(request: GameLabelExtractionRequest = Body(...)):
    """
    Extract scouting data field labels from manual data.
    
    This endpoint uses GPT to analyze game manual content and extract
    specific scouting metrics that teams would track about robot performance,
    such as scoring counts, effectiveness ratings, and success/failure indicators.
    """
    try:
        logger.info(f"Starting label extraction for year {request.year}")
        
        # Perform extraction
        result = await label_extractor_service.extract_game_labels(
            manual_data=request.manual_data,
            year=request.year,
            force_refresh=request.force_refresh
        )
        
        # Convert to response model
        labels = [GameLabel(**label) for label in result.extracted_labels]
        
        return GameLabelExtractionResponse(
            success=result.success,
            labels=labels,
            labels_count=result.labels_count,
            processing_time=result.processing_time,
            error=result.error,
            token_usage=result.token_usage
        )
        
    except Exception as e:
        logger.error(f"Error in extract_game_labels: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Label extraction failed: {str(e)}"
        )


@router.get("/{year}", response_model=GameLabelResponse)
async def get_game_labels_by_year(year: int):
    """
    Get stored game labels for a specific year.
    
    Args:
        year: Game year (e.g., 2025)
        
    Returns:
        Labels for the specified year
    """
    try:
        if year < 2000 or year > 2030:
            raise HTTPException(
                status_code=400,
                detail="Year must be between 2000 and 2030"
            )
        
        labels_data = label_extractor_service.get_labels_by_year(year)
        
        if not labels_data:
            return GameLabelResponse(
                success=True,
                message=f"No labels found for year {year}",
                labels_count=0,
                labels=[]
            )
        
        # Convert to response model
        labels = [GameLabel(**label) for label in labels_data]
        
        return GameLabelResponse(
            success=True,
            message=f"Found {len(labels)} labels for year {year}",
            labels_count=len(labels),
            labels=labels
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting labels for year {year}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve labels for year {year}: {str(e)}"
        )


@router.post("/{year}", response_model=GameLabelResponse)
async def save_game_labels(year: int, request: GameLabelUpdateRequest = Body(...)):
    """
    Save or update game labels for a specific year.
    
    Args:
        year: Game year
        request: Labels to save
        
    Returns:
        Success confirmation
    """
    try:
        if year < 2000 or year > 2030:
            raise HTTPException(
                status_code=400,
                detail="Year must be between 2000 and 2030"
            )
        
        # Convert to dictionary format
        labels_data = [label.model_dump() for label in request.labels]
        
        # Save labels
        success = label_extractor_service.save_labels(year, labels_data)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save labels for year {year}"
            )
        
        return GameLabelResponse(
            success=True,
            message=f"Successfully saved {len(labels_data)} labels for year {year}",
            labels_count=len(labels_data),
            labels=request.labels
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving labels for year {year}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save labels for year {year}: {str(e)}"
        )


@router.get("/service/info", response_model=ServiceInfoResponse)
async def get_service_info():
    """
    Get information about the game label extraction service.
    
    Returns:
        Service configuration and statistics
    """
    try:
        info = label_extractor_service.get_service_info()
        
        if 'error' in info:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get service info: {info['error']}"
            )
        
        return ServiceInfoResponse(**info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service info: {str(e)}"
        )


@router.delete("/{year}")
async def delete_game_labels(year: int):
    """
    Delete stored game labels for a specific year.
    
    Args:
        year: Game year
        
    Returns:
        Deletion confirmation
    """
    try:
        if year < 2000 or year > 2030:
            raise HTTPException(
                status_code=400,
                detail="Year must be between 2000 and 2030"
            )
        
        import os
        labels_file = os.path.join(label_extractor_service.data_dir, f"game_labels_{year}.json")
        
        if not os.path.exists(labels_file):
            raise HTTPException(
                status_code=404,
                detail=f"No labels found for year {year}"
            )
        
        os.remove(labels_file)
        logger.info(f"Deleted labels file for year {year}")
        
        return {
            "success": True,
            "message": f"Successfully deleted labels for year {year}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting labels for year {year}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete labels for year {year}: {str(e)}"
        )