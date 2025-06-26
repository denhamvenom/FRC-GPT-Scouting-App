# backend/app/api/v1/endpoints/extraction.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from app.services.data_aggregation_service import DataAggregationService
from app.services.game_context_extractor_service import GameContextExtractorService
from app.config.extraction_config import get_extraction_config, get_config_manager

logger = logging.getLogger("extraction_api")

router = APIRouter()


def get_data_service() -> DataAggregationService:
    """
    Dependency to get DataAggregationService instance.
    
    Note: In production, this should be injected via dependency injection.
    For now, we'll create a basic instance.
    """
    # This would normally be configured via dependency injection
    # For testing, we'll use a default dataset path
    dataset_path = "backend/app/data/unified_dataset.json"
    return DataAggregationService(dataset_path, use_extracted_context=True)


@router.get("/status", response_model=Dict[str, Any])
async def get_extraction_status(
    data_service: DataAggregationService = Depends(get_data_service)
) -> Dict[str, Any]:
    """
    Get the current status of game context extraction.
    
    Returns information about extraction availability, cache status,
    and configuration settings.
    """
    try:
        status = data_service.get_extraction_status()
        config = get_extraction_config()
        
        return {
            "status": "success",
            "extraction_status": status,
            "config": {
                "max_strategic_elements": config.max_strategic_elements,
                "max_key_metrics": config.max_key_metrics,
                "validation_threshold": config.validation_threshold,
                "extraction_temperature": config.extraction_temperature
            }
        }
    except Exception as e:
        logger.error(f"Error getting extraction status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=Dict[str, Any])
async def force_extract_context(
    data_service: DataAggregationService = Depends(get_data_service)
) -> Dict[str, Any]:
    """
    Force extraction of game context, bypassing cache.
    
    This will re-process the game manual and create a new extracted context.
    Use this when the manual has been updated or extraction parameters changed.
    """
    try:
        result = data_service.force_extract_game_context()
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Game context extracted successfully",
                "extraction_result": {
                    "processing_time": result["processing_time"],
                    "validation_score": result["validation_score"],
                    "token_usage": result.get("token_usage", {}),
                },
                "extracted_context": result["extraction_result"]
            }
        else:
            return {
                "status": "error",
                "message": result["message"],
                "error": result["error"]
            }
            
    except Exception as e:
        logger.error(f"Error during forced extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mode", response_model=Dict[str, Any])
async def set_extraction_mode(
    use_extracted_context: bool,
    data_service: DataAggregationService = Depends(get_data_service)
) -> Dict[str, Any]:
    """
    Enable or disable extracted context mode.
    
    Args:
        use_extracted_context: True to enable extraction, False for full manual
    """
    try:
        result = data_service.set_extraction_mode(use_extracted_context)
        
        return {
            "status": "success" if result["success"] else "error",
            "message": result["message"],
            "previous_mode": result.get("previous_mode"),
            "current_mode": result.get("current_mode"),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error setting extraction mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache", response_model=Dict[str, Any])
async def get_cache_info(
    data_service: DataAggregationService = Depends(get_data_service)
) -> Dict[str, Any]:
    """
    Get information about the extraction cache.
    
    Returns cache statistics, file information, and storage details.
    """
    try:
        if not data_service.extractor_service:
            return {
                "status": "error",
                "message": "Extraction service not available",
                "cache_info": {}
            }
        
        cache_info = data_service.extractor_service.get_cache_info()
        
        return {
            "status": "success",
            "cache_info": cache_info
        }
        
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache", response_model=Dict[str, Any])
async def clear_cache(
    extraction_version: Optional[str] = None,
    data_service: DataAggregationService = Depends(get_data_service)
) -> Dict[str, Any]:
    """
    Clear the extraction cache.
    
    Args:
        extraction_version: Optional version filter. If provided, only clear this version.
    """
    try:
        if not data_service.extractor_service:
            return {
                "status": "error",
                "message": "Extraction service not available"
            }
        
        result = data_service.extractor_service.clear_cache(extraction_version)
        
        return {
            "status": "success",
            "message": f"Cleared {result['cleared_files']} cache files",
            "cleared_files": result["cleared_files"],
            "version_filter": result.get("version_filter")
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=Dict[str, Any])
async def get_extraction_config_endpoint() -> Dict[str, Any]:
    """
    Get current extraction configuration settings.
    """
    try:
        config_manager = get_config_manager()
        config_dict = config_manager.get_config_dict()
        validation = config_manager.validate_config()
        
        return {
            "status": "success",
            "config": config_dict,
            "validation": validation
        }
        
    except Exception as e:
        logger.error(f"Error getting extraction config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config", response_model=Dict[str, Any])
async def update_extraction_config(
    max_strategic_elements: Optional[int] = None,
    max_alliance_considerations: Optional[int] = None,
    max_key_metrics: Optional[int] = None,
    max_game_pieces: Optional[int] = None,
    extraction_temperature: Optional[float] = None,
    max_extraction_tokens: Optional[int] = None,
    cache_ttl_hours: Optional[int] = None,
    validation_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update extraction configuration settings.
    
    Only provided parameters will be updated. Others remain unchanged.
    """
    try:
        config_manager = get_config_manager()
        
        # Build update dict with only provided values
        updates = {}
        if max_strategic_elements is not None:
            updates["max_strategic_elements"] = max_strategic_elements
        if max_alliance_considerations is not None:
            updates["max_alliance_considerations"] = max_alliance_considerations
        if max_key_metrics is not None:
            updates["max_key_metrics"] = max_key_metrics
        if max_game_pieces is not None:
            updates["max_game_pieces"] = max_game_pieces
        if extraction_temperature is not None:
            updates["extraction_temperature"] = extraction_temperature
        if max_extraction_tokens is not None:
            updates["max_extraction_tokens"] = max_extraction_tokens
        if cache_ttl_hours is not None:
            updates["cache_ttl_hours"] = cache_ttl_hours
        if validation_threshold is not None:
            updates["validation_threshold"] = validation_threshold
        
        if not updates:
            return {
                "status": "error",
                "message": "No configuration parameters provided to update"
            }
        
        # Update configuration
        config_manager.update_config(**updates)
        
        # Validate new configuration
        validation = config_manager.validate_config()
        
        return {
            "status": "success",
            "message": f"Updated {len(updates)} configuration parameters",
            "updated_fields": list(updates.keys()),
            "new_config": config_manager.get_config_dict(),
            "validation": validation
        }
        
    except Exception as e:
        logger.error(f"Error updating extraction config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare", response_model=Dict[str, Any])
async def compare_context_sizes(
    data_service: DataAggregationService = Depends(get_data_service)
) -> Dict[str, Any]:
    """
    Compare the sizes of full manual vs extracted context.
    
    Returns token counts and size comparisons for analysis.
    """
    try:
        # Get manual data
        manual_data = data_service._load_manual_data()
        if not manual_data:
            return {
                "status": "error",
                "message": "Manual data not available"
            }
        
        # Get full context
        full_context = data_service._get_full_manual_context(manual_data)
        full_size = len(full_context)
        
        # Get extracted context if available
        extracted_context = None
        extracted_size = 0
        
        if data_service.extractor_service:
            try:
                # Temporarily enable extraction mode to get extracted context
                original_mode = data_service.use_extracted_context
                data_service.use_extracted_context = True
                
                extracted_context = data_service._get_extracted_context(manual_data)
                if extracted_context:
                    extracted_size = len(extracted_context)
                
                # Restore original mode
                data_service.use_extracted_context = original_mode
                
            except Exception as e:
                logger.warning(f"Could not get extracted context for comparison: {e}")
        
        # Calculate savings
        savings_percentage = 0.0
        if full_size > 0 and extracted_size > 0:
            savings_percentage = 100 * (1 - extracted_size / full_size)
        
        # Estimate token counts (rough approximation)
        full_tokens = full_size // 4  # Rough estimate: 4 chars per token
        extracted_tokens = extracted_size // 4
        token_savings = full_tokens - extracted_tokens
        
        return {
            "status": "success",
            "comparison": {
                "full_manual": {
                    "character_count": full_size,
                    "estimated_tokens": full_tokens
                },
                "extracted_context": {
                    "character_count": extracted_size,
                    "estimated_tokens": extracted_tokens,
                    "available": extracted_context is not None
                },
                "savings": {
                    "character_reduction": full_size - extracted_size,
                    "percentage_reduction": round(savings_percentage, 1),
                    "estimated_token_savings": token_savings
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error comparing context sizes: {e}")
        raise HTTPException(status_code=500, detail=str(e))