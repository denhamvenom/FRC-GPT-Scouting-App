# backend/app/api/picklist_analysis.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.picklist_analysis_service import PicklistAnalysisService

router = APIRouter()


class MetricPriority(BaseModel):
    id: str
    weight: float = 1.0
    reason: Optional[str] = None


class PicklistAnalysisRequest(BaseModel):
    unified_dataset_path: str
    priorities: Optional[List[MetricPriority]] = None
    strategy_prompt: Optional[str] = None


@router.post("/picklist/analyze")
async def analyze_picklist_data(request: PicklistAnalysisRequest):
    """
    Analyze the unified dataset to generate picklist suggestions and metrics.

    Either priorities or strategy_prompt should be provided:
    - priorities: List of metric IDs with weights for direct ranking
    - strategy_prompt: Natural language description of desired strategy
    """
    try:
        # Initialize the analysis service
        analysis_service = PicklistAnalysisService(request.unified_dataset_path)

        # Get game-specific metrics
        game_metrics = analysis_service.identify_game_specific_metrics()

        # Get superscouting metrics - new addition
        superscout_metrics = analysis_service.identify_superscout_metrics()

        # Extract pit scouting metrics
        # For now, we'll filter game metrics that might be from pit scouting
        pit_metrics = [
            m
            for m in game_metrics
            if m.get("category", "").lower() == "pit" or "pit" in m.get("id", "").lower()
        ]

        # Get suggested metrics based on statistical analysis
        suggested_metrics = analysis_service.get_suggested_priorities()

        # If strategy prompt is provided, parse it into priorities using GPT
        parsed_priorities = None
        if request.strategy_prompt:
            parsed_priorities = analysis_service.parse_strategy_prompt(request.strategy_prompt)

        # Generate team rankings if priorities are provided
        team_rankings = None
        if request.priorities:
            team_rankings = analysis_service.rank_teams(request.priorities)

        # Generate statistics for all metrics
        metrics_stats = analysis_service.calculate_metrics_statistics()

        # Get enhanced field selections metadata for API exposure
        enhanced_metadata = analysis_service.get_enhanced_field_metadata()
        field_selections_info = analysis_service.get_field_selections_summary()
        
        return {
            "status": "success",
            "game_metrics": game_metrics,
            "universal_metrics": analysis_service.universal_metrics,
            "superscout_metrics": superscout_metrics,
            "pit_metrics": pit_metrics,  # Add pit scouting metrics to response
            "suggested_metrics": suggested_metrics,
            "metrics_stats": metrics_stats,
            "parsed_priorities": parsed_priorities,
            "team_rankings": team_rankings,
            # Enhanced data structure information
            "enhanced_metadata": enhanced_metadata,
            "field_selections_info": field_selections_info,
            "has_enhanced_data": bool(enhanced_metadata),
            "text_fields_available": any(
                metric.get("data_type") == "text" 
                for metric in game_metrics + superscout_metrics
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing picklist data: {str(e)}")


@router.post("/picklist/validate-enhanced-data")
async def validate_enhanced_data_structure(request: PicklistAnalysisRequest):
    """
    Validate the enhanced data structure integrity for the given dataset.
    
    Checks:
    - Field selections availability and structure
    - Enhanced label mappings completeness
    - Text field support
    - Data type consistency
    - Backward compatibility
    """
    try:
        # Initialize the analysis service
        analysis_service = PicklistAnalysisService(request.unified_dataset_path)
        
        validation_results = {
            "status": "success",
            "data_structure_valid": True,
            "enhanced_features_available": True,
            "validation_details": {},
            "warnings": [],
            "errors": []
        }
        
        # Check field selections availability
        field_selections_info = analysis_service.get_field_selections_summary()
        validation_results["field_selections"] = field_selections_info
        
        if not field_selections_info.get("available", False):
            validation_results["warnings"].append("Enhanced field selections not available - falling back to game labels")
            validation_results["enhanced_features_available"] = False
        
        # Check enhanced metadata availability
        enhanced_metadata = analysis_service.get_enhanced_field_metadata()
        validation_results["enhanced_metadata"] = enhanced_metadata
        
        if not enhanced_metadata:
            validation_results["warnings"].append("Enhanced metadata not available")
            validation_results["enhanced_features_available"] = False
        
        # Check actual vs configured metrics alignment
        try:
            actual_fields = analysis_service.get_actual_scouting_fields()
            validation_results["actual_vs_configured"] = {
                "actual_fields_count": len(actual_fields),
                "actual_fields_sample": list(actual_fields)[:10],  # Show first 10 for debugging
            }
        except Exception as e:
            validation_results["warnings"].append(f"Could not analyze actual vs configured metrics: {str(e)}")
        
        
        # Check text fields support
        text_fields_count = enhanced_metadata.get("text_fields_count", 0)
        validation_results["text_fields_support"] = {
            "available": text_fields_count > 0,
            "count": text_fields_count
        }
        
        if text_fields_count == 0:
            validation_results["warnings"].append("No text fields detected in enhanced structure")
        
        # Validate game metrics structure
        try:
            game_metrics = analysis_service.identify_game_specific_metrics()
            validation_results["game_metrics_validation"] = {
                "total_metrics": len(game_metrics),
                "has_descriptions": sum(1 for m in game_metrics if m.get("description")),
                "has_categories": sum(1 for m in game_metrics if m.get("category")),
                "data_types_found": list(set(m.get("data_type", "unknown") for m in game_metrics))
            }
        except Exception as e:
            validation_results["errors"].append(f"Error validating game metrics: {str(e)}")
            validation_results["data_structure_valid"] = False
        
        # Check label mapping hierarchy
        try:
            # Try to load the enhanced field selections
            if hasattr(analysis_service, 'field_selections') and analysis_service.field_selections:
                enhanced_fields = len(analysis_service.field_selections)
                validation_results["label_mapping_hierarchy"] = {
                    "enhanced_fields_available": enhanced_fields,
                    "hierarchy_working": enhanced_fields > 0
                }
            else:
                validation_results["warnings"].append("Enhanced field selections not loaded properly")
                validation_results["label_mapping_hierarchy"] = {
                    "enhanced_fields_available": 0,
                    "hierarchy_working": False
                }
        except Exception as e:
            validation_results["errors"].append(f"Error checking label mapping hierarchy: {str(e)}")
            validation_results["data_structure_valid"] = False
        
        # Overall validation status
        if validation_results["errors"]:
            validation_results["status"] = "error"
            validation_results["data_structure_valid"] = False
        elif validation_results["warnings"]:
            validation_results["status"] = "warning"
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating enhanced data structure: {str(e)}")
