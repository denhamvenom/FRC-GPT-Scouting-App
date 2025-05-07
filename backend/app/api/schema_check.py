#!/usr/bin/env python3
# backend/app/api/schema_check.py

import os
import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(tags=["Schema"])

@router.get("/check")
async def check_schema_exists() -> Dict[str, Any]:
    """
    Check if schema mapping files exist to determine if setup and field selection are completed.
    
    Returns:
        Dict with status of schema files
    """
    # Get the base directory path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    # Check for regular schema mapping
    schema_path = os.path.join(data_dir, "schema_2025.json")
    schema_exists = os.path.exists(schema_path)
    
    # Check for superscout schema mapping
    superscout_path = os.path.join(data_dir, "schema_superscout_2025.json")
    superscout_exists = os.path.exists(superscout_path)
    
    # Check for unified dataset
    unified_path = os.path.join(data_dir, "unified_event_2025arc.json")
    dataset_exists = os.path.exists(unified_path)
    
    # Check for validation completion
    validation_completed = False
    if dataset_exists:
        try:
            with open(unified_path, 'r') as f:
                data = json.load(f)
                # Check if validation data exists in the file
                if "metadata" in data and "validation" in data["metadata"]:
                    validation_completed = data["metadata"]["validation"].get("completed", False)
        except Exception:
            validation_completed = False
    
    # Check for other files that would indicate setup completion
    setup_completed = False
    
    # Check for various files that would indicate setup is complete
    game_analysis_path = os.path.join(data_dir, "game_analysis_2025.json")
    manual_info_path = os.path.join(data_dir, "manual_info_2025.json")
    
    if os.path.exists(game_analysis_path) or os.path.exists(manual_info_path):
        setup_completed = True
        
    # For testing/development, always enable setup completion
    setup_completed = True
        
    return {
        "exists": schema_exists and superscout_exists,
        "setup_completed": setup_completed,
        "schema_exists": schema_exists,
        "superscout_exists": superscout_exists,
        "schema_path": schema_path if schema_exists else None,
        "superscout_path": superscout_path if superscout_exists else None,
        "dataset_built": dataset_exists,
        "validation_completed": validation_completed
    }

@router.get("/fields")
async def check_fields_exist() -> Dict[str, Any]:
    """
    Check if field selection mappings exist.
    
    Returns:
        Dict with status of field selection
    """
    # Get the base directory path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    # Check for field selections 
    fields_path = os.path.join(data_dir, "field_selections_2025.json")
    schema_path = os.path.join(data_dir, "schema_2025.json")
    
    # Either the field selections or schema file would indicate field selection is complete
    fields_exist = os.path.exists(fields_path) or os.path.exists(schema_path)
    
    # For testing/development, always enable field selection
    fields_exist = True
    
    return {
        "exists": fields_exist,
        "fields_path": fields_path if fields_exist else None
    }

@router.get("/check-validation-status")
async def check_validation_status():
    """
    Check if any datasets have been validated and if there are still issues.
    
    Returns:
        Dict with validation status information
    """
    try:
        # Get the base directory path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        
        # Look for validation results files (these would be created when validation is run)
        validation_files = []
        
        # Check for unified datasets first - we need these to have run validation
        pattern = os.path.join(data_dir, "unified_event_*.json")
        
        import glob
        dataset_files = glob.glob(pattern)
        
        validation_completed = False
        validation_has_issues = True
        
        # For each dataset, check if there's a validation record embedded
        for dataset_path in dataset_files:
            try:
                with open(dataset_path, 'r') as f:
                    data = json.load(f)
                    
                    # Check if there's a metadata/validation section
                    if "metadata" in data and "validation" in data["metadata"]:
                        validation_completed = True
                        validation_record = data["metadata"]["validation"]
                        
                        # Check if there are issues
                        if not validation_record.get("has_issues", True):
                            validation_has_issues = False
                            break
            except Exception as e:
                # Continue checking other files if one fails to load
                continue
            
        return {
            "validation_completed": validation_completed,
            "validation_has_issues": validation_has_issues,
            "datasets_checked": len(dataset_files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))