# backend/app/api/performance_signatures.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import logging

from app.services.data_aggregation_service import DataAggregationService

router = APIRouter(prefix="/api/performance-signatures", tags=["Performance Signatures"])
logger = logging.getLogger("performance_signatures_api")


class PerformanceSignatureRequest(BaseModel):
    unified_dataset_path: str
    output_filepath: Optional[str] = None


class PerformanceSignatureResponse(BaseModel):
    success: bool
    message: str
    teams_analyzed: Optional[int] = None
    metrics_processed: Optional[int] = None
    signatures_filepath: Optional[str] = None
    baselines_filepath: Optional[str] = None
    strategic_intelligence_filepath: Optional[str] = None
    strategic_teams_analyzed: Optional[int] = None
    processing_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/generate", response_model=PerformanceSignatureResponse)
async def generate_performance_signatures(request: PerformanceSignatureRequest):
    """
    Generate performance signatures for all teams in a unified dataset.
    
    This endpoint triggers the performance signature generation process
    after data validation is complete.
    """
    try:
        logger.info(f"Starting performance signature generation for: {request.unified_dataset_path}")
        
        # Validate dataset file exists
        if not os.path.exists(request.unified_dataset_path):
            raise HTTPException(
                status_code=404,
                detail=f"Unified dataset file not found: {request.unified_dataset_path}"
            )
        
        # Initialize data aggregation service
        data_service = DataAggregationService(request.unified_dataset_path)
        
        # Generate performance signatures
        result = data_service.generate_performance_signatures(request.output_filepath)
        
        if result["success"]:
            logger.info(f"Performance signatures generated successfully: {result['teams_analyzed']} teams")
            
            # Generate strategic intelligence after performance signatures
            strategic_result = await data_service.generate_strategic_intelligence_file()
            
            # Prepare response with both signature and strategic intelligence results
            response_data = {
                "success": True,
                "message": result["message"],
                "teams_analyzed": result["teams_analyzed"],
                "metrics_processed": result["metrics_processed"],
                "signatures_filepath": result["signatures_filepath"],
                "baselines_filepath": result["baselines_filepath"],
                "processing_summary": result["processing_summary"]
            }
            
            # Add strategic intelligence results if successful
            if strategic_result and strategic_result.get("success"):
                response_data["strategic_intelligence_filepath"] = strategic_result["filepath"]
                response_data["strategic_teams_analyzed"] = strategic_result["teams_analyzed"]
                response_data["message"] = f"{result['message']} + strategic intelligence for {strategic_result['teams_analyzed']} teams"
                logger.info(f"Strategic intelligence generated: {strategic_result['teams_analyzed']} teams")
            else:
                # Log strategic analysis failure but don't fail the entire operation
                logger.warning(f"Strategic intelligence generation failed: {strategic_result.get('error', 'Unknown error') if strategic_result else 'Service unavailable'}")
                response_data["message"] = f"{result['message']} (strategic intelligence generation failed)"
            
            return PerformanceSignatureResponse(**response_data)
        else:
            logger.error(f"Performance signature generation failed: {result.get('error')}")
            
            return PerformanceSignatureResponse(
                success=False,
                message=result.get("message", "Performance signature generation failed"),
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"Error in performance signature generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during signature generation: {str(e)}"
        )


@router.get("/status/{event_key}")
async def get_signature_status(event_key: str):
    """
    Check if performance signatures exist for a given event.
    
    Args:
        event_key: Event key to check (e.g., "2025lake")
        
    Returns:
        Status information about existing signature files
    """
    try:
        # Look for signature files in the data directory
        data_dir = "/app/data"  # Default data directory
        
        # Try different possible locations
        possible_dirs = [
            "/app/data",
            "/app/app/data", 
            "backend/app/data",
            "app/data"
        ]
        
        signatures_file = None
        baselines_file = None
        
        for base_dir in possible_dirs:
            if os.path.exists(base_dir):
                sig_path = os.path.join(base_dir, f"performance_signatures_{event_key}.json")
                base_path = os.path.join(base_dir, f"performance_signatures_{event_key}_baselines.json")
                
                if os.path.exists(sig_path):
                    signatures_file = sig_path
                if os.path.exists(base_path):
                    baselines_file = base_path
                
                if signatures_file:
                    break
        
        exists = signatures_file is not None
        
        return {
            "event_key": event_key,
            "signatures_exist": exists,
            "signatures_filepath": signatures_file,
            "baselines_filepath": baselines_file,
            "status": "available" if exists else "not_generated"
        }
        
    except Exception as e:
        logger.error(f"Error checking signature status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking signature status: {str(e)}"
        )


@router.delete("/clear/{event_key}")
async def clear_signatures(event_key: str):
    """
    Clear/delete performance signature files for an event.
    
    Args:
        event_key: Event key to clear signatures for
        
    Returns:
        Status of the clearing operation
    """
    try:
        data_dir = "/app/data"
        
        # Try different possible locations
        possible_dirs = [
            "/app/data",
            "/app/app/data", 
            "backend/app/data",
            "app/data"
        ]
        
        files_deleted = []
        
        for base_dir in possible_dirs:
            if os.path.exists(base_dir):
                sig_path = os.path.join(base_dir, f"performance_signatures_{event_key}.json")
                base_path = os.path.join(base_dir, f"performance_signatures_{event_key}_baselines.json")
                
                for file_path in [sig_path, base_path]:
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            files_deleted.append(os.path.basename(file_path))
                            logger.info(f"Deleted signature file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path}: {e}")
        
        return {
            "event_key": event_key,
            "files_deleted": files_deleted,
            "success": len(files_deleted) > 0,
            "message": f"Deleted {len(files_deleted)} signature files" if files_deleted else "No signature files found to delete"
        }
        
    except Exception as e:
        logger.error(f"Error clearing signatures: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing signatures: {str(e)}"
        )