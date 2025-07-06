# backend/app/api/v1/endpoints/game_labels.py

import datetime
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from app.services.game_label_extractor_service import GameLabelExtractorService

logger = logging.getLogger("game_labels_api")

router = APIRouter(prefix="/game-labels", tags=["Game Labels"])

# Initialize the service with proper data directory
# Get the backend directory: go up from endpoints -> v1 -> api -> app -> backend
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
data_dir = os.path.join(backend_dir, "app", "data")
label_extractor_service = GameLabelExtractorService(data_dir=data_dir)


class GameLabel(BaseModel):
    """Model for a scouting data field label."""
    label: str = Field(..., description="Scouting field name (e.g., auto_coral_L1_scored, teleop_defense_rating)")
    category: str = Field(..., description="Category: autonomous|teleop|endgame|defense|reliability|strategic")
    description: str = Field(..., description="What this metric measures about robot performance")
    data_type: str = Field(..., description="Data type: count|rating|boolean|time|text")
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


class GenerateDescriptionRequest(BaseModel):
    """Request model for AI description generation."""
    label_name: str = Field(..., description="Name of the label to generate description for")
    category: str = Field(..., description="Category of the label")
    data_type: str = Field(..., description="Data type of the label")
    context: Optional[str] = Field(None, description="Additional context about the field")


class GenerateDescriptionResponse(BaseModel):
    """Response model for AI description generation."""
    success: bool = Field(..., description="Whether generation was successful")
    suggested_label: Optional[str] = Field(None, description="AI-suggested label name")
    description: Optional[str] = Field(None, description="Generated description")
    typical_range: Optional[str] = Field(None, description="Generated typical range")
    usage_context: Optional[str] = Field(None, description="Generated usage context")
    message: Optional[str] = Field(None, description="Response message")


class AddLabelRequest(BaseModel):
    """Request model for adding a new label."""
    label: GameLabel = Field(..., description="Label to add")
    year: int = Field(..., description="Year to add the label to")


class UpdateLabelRequest(BaseModel):
    """Request model for updating an existing label."""
    original_label: str = Field(..., description="Original label name to find and update")
    updated_label: GameLabel = Field(..., description="Updated label data")
    year: int = Field(..., description="Year to update the label in")


@router.post("/generate-description", response_model=GenerateDescriptionResponse)
async def generate_label_description(request: GenerateDescriptionRequest = Body(...)):
    """
    Generate AI-powered description for a new scouting label.
    
    This endpoint uses GPT to generate appropriate description, typical range,
    and usage context for a custom scouting label based on the provided information.
    """
    try:
        logger.info(f"Generating description for label: {request.label_name}")
        
        # Create a prompt for GPT to generate the description
        prompt = f"""
        You are an FRC (FIRST Robotics Competition) scouting expert. Generate a concise description for a custom scouting metric.
        
        Label Name: {request.label_name}
        Category: {request.category}
        Data Type: {request.data_type}
        Additional Context: {request.context or 'None provided'}
        
        Please provide:
        1. A brief, clear description of what this metric measures (1 sentence max)
        2. A typical range for the values (appropriate for the data type)
        3. Usage context (when/how this would be tracked during a match)
        4. If needed, suggest a better label name following FRC scouting conventions
        
        Format your response as JSON with these keys:
        - suggested_label: (string, improved label name if needed, or same as input)
        - description: (string, brief description of what this measures - 1 sentence only)
        - typical_range: (string, appropriate range for the data type)
        - usage_context: (string, when/how this is tracked)
        
        Keep descriptions brief and consistent with existing scouting metrics. Match the style of existing labels like "Number of CORAL scored in the REEF trough (L1) during autonomous".
        """
        
        # Use the existing GPT service
        result = await label_extractor_service.call_gpt_for_description(prompt)
        
        if result.get('success'):
            return GenerateDescriptionResponse(
                success=True,
                suggested_label=result.get('suggested_label'),
                description=result.get('description'),
                typical_range=result.get('typical_range'),
                usage_context=result.get('usage_context'),
                message="Description generated successfully"
            )
        else:
            return GenerateDescriptionResponse(
                success=False,
                message=result.get('error', 'Failed to generate description')
            )
        
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        return GenerateDescriptionResponse(
            success=False,
            message=f"Failed to generate description: {str(e)}"
        )


@router.post("/add", response_model=GameLabelResponse)
async def add_new_label(request: AddLabelRequest = Body(...)):
    """
    Add a new custom label to the existing labels for a year.
    
    This endpoint appends a new label to the existing labels file,
    allowing users to add custom scouting metrics on-the-fly.
    """
    try:
        logger.info(f"Adding new label: {request.label.label} for year {request.year}")
        
        if request.year < 2000 or request.year > 2030:
            raise HTTPException(
                status_code=400,
                detail="Year must be between 2000 and 2030"
            )
        
        # Get existing labels
        existing_labels = label_extractor_service.get_labels_by_year(request.year) or []
        
        # Check if label already exists
        if any(label.get('label') == request.label.label for label in existing_labels):
            raise HTTPException(
                status_code=400,
                detail=f"Label '{request.label.label}' already exists for year {request.year}"
            )
        
        # Add the new label
        new_label_dict = request.label.model_dump()
        # Add metadata
        import datetime
        new_label_dict.update({
            'extraction_version': '1.0',
            'extraction_date': datetime.datetime.now().isoformat(),
            'game_year': request.year,
            'custom_added': True
        })
        
        existing_labels.append(new_label_dict)
        
        # Save updated labels
        success = label_extractor_service.save_labels(request.year, existing_labels)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save new label for year {request.year}"
            )
        
        return GameLabelResponse(
            success=True,
            message=f"Successfully added label '{request.label.label}' for year {request.year}",
            labels_count=len(existing_labels),
            labels=[GameLabel(**label) for label in existing_labels]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding new label: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add new label: {str(e)}"
        )


@router.post("/update", response_model=GameLabelResponse)
async def update_existing_label(request: UpdateLabelRequest = Body(...)):
    """
    Update an existing label in the labels collection.
    
    This endpoint finds a label by its original name and updates it with new information,
    allowing users to edit descriptions, ranges, and other properties.
    """
    try:
        logger.info(f"Updating label: {request.original_label} for year {request.year}")
        
        if request.year < 2000 or request.year > 2030:
            raise HTTPException(
                status_code=400,
                detail="Year must be between 2000 and 2030"
            )
        
        # Get existing labels
        existing_labels = label_extractor_service.get_labels_by_year(request.year) or []
        
        # Find the label to update
        label_index = -1
        for i, label in enumerate(existing_labels):
            if label.get('label') == request.original_label:
                label_index = i
                break
        
        if label_index == -1:
            raise HTTPException(
                status_code=404,
                detail=f"Label '{request.original_label}' not found for year {request.year}"
            )
        
        # Check if the new label name already exists (if it changed)
        if (request.updated_label.label != request.original_label and 
            any(label.get('label') == request.updated_label.label for label in existing_labels)):
            raise HTTPException(
                status_code=400,
                detail=f"Label '{request.updated_label.label}' already exists for year {request.year}"
            )
        
        # Update the label
        updated_label_dict = request.updated_label.model_dump()
        # Preserve original metadata but update modification info
        original_label = existing_labels[label_index]
        updated_label_dict.update({
            'extraction_version': original_label.get('extraction_version', '1.0'),
            'extraction_date': original_label.get('extraction_date'),
            'game_year': request.year,
            'custom_added': original_label.get('custom_added', False),
            'last_modified': datetime.datetime.now().isoformat(),
            'modified_by_user': True
        })
        
        existing_labels[label_index] = updated_label_dict
        
        # Save updated labels
        success = label_extractor_service.save_labels(request.year, existing_labels)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update label for year {request.year}"
            )
        
        return GameLabelResponse(
            success=True,
            message=f"Successfully updated label '{request.original_label}' to '{request.updated_label.label}' for year {request.year}",
            labels_count=len(existing_labels),
            labels=[GameLabel(**label) for label in existing_labels]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating label: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update label: {str(e)}"
        )


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