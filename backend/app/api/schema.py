"""
Schema API Router

This module handles schema learning, field mapping, and configuration
for scouting data structure management.
"""

import json
import os
import traceback
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    LearnSchemaRequest,
    LearnSchemaResponse,
    MapFieldsRequest,
    SchemaResponse,
    SuccessResponse,
    ValidateSchemaRequest,
    ValidateSchemaResponse,
)
from app.api.utils.response_formatters import format_error_response
from app.database.db import get_db
from app.services.global_cache import cache
from app.services.schema_service import extract_game_tags_from_manual, map_headers_to_tags
from app.services.sheets_service import get_sheet_headers, get_sheet_values

router = APIRouter(prefix="/api/schema", tags=["schema"])


@router.post("/learn", response_model=LearnSchemaResponse)
async def learn_schema(
    request: LearnSchemaRequest,
    db: Session = Depends(get_db),
) -> LearnSchemaResponse:
    """
    Learn schema from spreadsheet headers using AI mapping.
    
    Analyzes spreadsheet column headers and intelligently maps them
    to standardized scouting fields using GPT-4. Supports multiple
    scouting types (match, pit, super).
    """
    try:
        # Load field selections for the current year
        year = cache.get("manual_year", 2025)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        selections_path = os.path.join(data_dir, f"field_selections_{year}.json")
        
        if not os.path.exists(selections_path):
            raise HTTPException(
                status_code=404,
                detail="Field selections not found. Please configure fields first."
            )
        
        with open(selections_path, "r", encoding="utf-8") as f:
            selections = json.load(f)
        
        field_selections = selections.get("field_selections", {})
        if not field_selections:
            raise HTTPException(
                status_code=400,
                detail="No field selections found in saved data."
            )
        
        # Get critical mappings and robot groups
        critical_mappings = selections.get(
            "critical_mappings", {"team_number": [], "match_number": []}
        )
        robot_groups = selections.get("robot_groups", {})
        
        # Fetch headers based on source
        if request.source == "sheets":
            if not request.sheet_id:
                # Use default sheets
                match_headers = get_sheet_headers("Scouting")
                pit_headers = get_sheet_headers("PitScouting", log_errors=False) or []
                super_headers = get_sheet_headers("SuperScouting", log_errors=False) or []
            else:
                # Use specific sheet
                match_headers = get_sheet_headers(request.sheet_name or "Scouting")
                pit_headers = []
                super_headers = []
        else:
            # Extract headers from sample data if provided
            match_headers = []
            if request.sample_data:
                match_headers = list(request.sample_data[0].keys())
        
        # Get game analysis from cache
        game_analysis = cache.get("game_analysis", {})
        scouting_vars = []
        
        if game_analysis and "scouting_variables" in game_analysis:
            for category_vars in game_analysis.get("scouting_variables", {}).values():
                scouting_vars.extend(category_vars)
        
        # Fallback to standard variables
        if not scouting_vars:
            scouting_vars = [
                "team_number", "match_number", "alliance_color",
                "auto_score", "teleop_score", "endgame_score",
                "total_score", "comments", "starting_position",
                "driver_skill", "defense_rating",
            ]
        
        # Process mappings
        all_mappings = {}
        discovered_fields = []
        field_mappings = []
        warnings = []
        
        # Map match scouting headers
        if match_headers:
            relevant_headers = [
                h for h in match_headers 
                if h in field_selections and field_selections[h] != "ignore"
            ]
            
            if relevant_headers and request.auto_map:
                match_mapping = await map_headers_to_tags(relevant_headers, scouting_vars)
                all_mappings["match"] = match_mapping
                
                # Convert to field mappings
                for header, tag in match_mapping.items():
                    field_mappings.append({
                        "source_field": header,
                        "target_field": tag,
                        "confidence": 0.9,
                        "auto_mapped": True,
                    })
        
        # Create field definitions
        for header in match_headers:
            if header in field_selections and field_selections[header] != "ignore":
                field_type = "string"  # Default type
                category = field_selections.get(header, "custom")
                
                discovered_fields.append({
                    "name": header,
                    "display_name": header,
                    "type": field_type,
                    "category": category,
                    "source": "sheets",
                    "required": header in critical_mappings.get("team_number", []) or 
                              header in critical_mappings.get("match_number", []),
                    "nullable": True,
                })
        
        # Calculate statistics if requested
        statistics = None
        if request.include_stats and request.sample_data:
            total_rows = len(request.sample_data)
            completeness = sum(
                1 for row in request.sample_data 
                if all(row.get(h) for h in match_headers)
            ) / total_rows if total_rows > 0 else 0
            
            statistics = {
                "total_rows_analyzed": total_rows,
                "completeness": completeness,
            }
        
        # Save schema
        schema_path = os.path.join(data_dir, f"schema_{year}.json")
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mappings": all_mappings,
                    "critical_fields": critical_mappings,
                    "robot_groups": robot_groups,
                    "year": year,
                    "fields": discovered_fields,
                },
                f,
                indent=2,
            )
        
        # Calculate mapping confidence
        total_fields = len(discovered_fields)
        mapped_fields = len(field_mappings)
        mapping_confidence = mapped_fields / total_fields if total_fields > 0 else 0
        
        return LearnSchemaResponse(
            status="success",
            fields_discovered=len(discovered_fields),
            fields=discovered_fields,
            mappings=field_mappings,
            mapping_confidence=mapping_confidence,
            warnings=warnings,
            statistics=statistics,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in learn_schema: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current", response_model=SchemaResponse)
async def get_current_schema(
    event_key: Optional[str] = None,
) -> SchemaResponse:
    """
    Get the current schema configuration.
    
    Returns the complete schema including field definitions,
    mappings, and critical fields.
    """
    try:
        year = cache.get("manual_year", 2025)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        schema_path = os.path.join(data_dir, f"schema_{year}.json")
        
        if not os.path.exists(schema_path):
            raise HTTPException(
                status_code=404,
                detail="Schema not found. Please run schema learning first."
            )
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
        
        # Extract data
        fields = schema_data.get("fields", [])
        mappings = []
        
        # Convert mappings to field mapping format
        for sheet_type, sheet_mappings in schema_data.get("mappings", {}).items():
            if isinstance(sheet_mappings, dict):
                for source, target in sheet_mappings.items():
                    mappings.append({
                        "source_field": source,
                        "target_field": target,
                        "confidence": 1.0,
                        "auto_mapped": True,
                    })
        
        # Check for required fields
        critical_fields = schema_data.get("critical_fields", {})
        required_fields_missing = []
        
        # Check if critical fields are mapped
        mapped_targets = {m.get("target_field") for m in mappings}
        if "team_number" not in mapped_targets:
            required_fields_missing.append("team_number")
        if "match_number" not in mapped_targets:
            required_fields_missing.append("match_number")
        
        return SchemaResponse(
            status="success",
            event_key=event_key or cache.get("active_event_key"),
            fields=fields,
            mappings=mappings,
            total_fields=len(fields),
            mapped_fields=len(mappings),
            required_fields_missing=required_fields_missing,
            last_updated=None,  # TODO: Add timestamp tracking
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/map-fields", response_model=SuccessResponse)
async def map_fields(request: MapFieldsRequest) -> SuccessResponse:
    """
    Manually map fields or update existing mappings.
    
    Allows manual override of automatic field mappings for
    precise control over data structure.
    """
    try:
        year = cache.get("manual_year", 2025)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        schema_path = os.path.join(data_dir, f"schema_{year}.json")
        
        # Load existing schema
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
        else:
            schema_data = {"mappings": {}, "fields": []}
        
        # Update mappings
        current_mappings = schema_data.get("mappings", {})
        
        # Apply new mappings
        for mapping in request.mappings:
            # Find which sheet type this mapping belongs to
            sheet_type = "match"  # Default
            
            # Update the mapping
            if sheet_type not in current_mappings:
                current_mappings[sheet_type] = {}
            
            if not request.preserve_existing or mapping.source_field not in current_mappings[sheet_type]:
                current_mappings[sheet_type][mapping.source_field] = mapping.target_field
        
        # Validate mappings if requested
        if request.validate_mappings:
            # Check for duplicate targets
            all_targets = []
            for sheet_mappings in current_mappings.values():
                if isinstance(sheet_mappings, dict):
                    all_targets.extend(sheet_mappings.values())
            
            duplicates = [t for t in all_targets if all_targets.count(t) > 1]
            if duplicates:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate target fields found: {', '.join(set(duplicates))}"
                )
        
        # Save updated schema
        schema_data["mappings"] = current_mappings
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, indent=2)
        
        return SuccessResponse(
            status="success",
            message=f"Successfully updated {len(request.mappings)} field mappings",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidateSchemaResponse)
async def validate_schema(request: ValidateSchemaRequest) -> ValidateSchemaResponse:
    """
    Validate schema configuration.
    
    Checks for missing required fields, invalid mappings,
    and other potential issues.
    """
    try:
        year = cache.get("manual_year", 2025)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        schema_path = os.path.join(data_dir, f"schema_{year}.json")
        
        issues = []
        
        # Load schema to validate
        if request.schema_fields:
            # Validate provided schema
            fields = request.schema_fields
        else:
            # Validate current schema
            if not os.path.exists(schema_path):
                issues.append({
                    "field": "schema",
                    "issue_type": "missing_schema",
                    "severity": "error",
                    "message": "No schema found. Please run schema learning first.",
                })
                
                return ValidateSchemaResponse(
                    status="success",
                    valid=False,
                    issues=issues,
                    error_count=1,
                    warning_count=0,
                    suggestions=[],
                )
            
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            
            fields = schema_data.get("fields", [])
        
        # Check for required fields
        field_names = {f.get("name") for f in fields}
        mappings = []
        
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
                
                # Extract all mappings
                for sheet_mappings in schema_data.get("mappings", {}).values():
                    if isinstance(sheet_mappings, dict):
                        for source, target in sheet_mappings.items():
                            mappings.append((source, target))
        
        mapped_targets = {m[1] for m in mappings}
        
        # Check for critical fields
        if "team_number" not in mapped_targets:
            issues.append({
                "field": "team_number",
                "issue_type": "missing_required",
                "severity": "error",
                "message": "Required field 'team_number' not mapped",
                "suggestion": "Map a spreadsheet column to 'team_number'",
            })
        
        if "match_number" not in mapped_targets:
            issues.append({
                "field": "match_number",
                "issue_type": "missing_required",
                "severity": "error",
                "message": "Required field 'match_number' not mapped",
                "suggestion": "Map a spreadsheet column to 'match_number'",
            })
        
        # Check for unmapped fields
        unmapped_count = len(field_names) - len(mappings)
        if unmapped_count > 0:
            issues.append({
                "field": "mappings",
                "issue_type": "unmapped_fields",
                "severity": "warning",
                "message": f"{unmapped_count} fields are not mapped to standard fields",
                "suggestion": "Review and map remaining fields or mark them as ignored",
            })
        
        # Generate suggestions
        suggestions = []
        if not fields:
            suggestions.append("Run schema learning to discover spreadsheet structure")
        if len(issues) > 0:
            suggestions.append("Address all errors before proceeding with data import")
        if unmapped_count > 5:
            suggestions.append("Consider using automatic mapping for unmapped fields")
        
        # Count issues by severity
        error_count = sum(1 for i in issues if i["severity"] == "error")
        warning_count = sum(1 for i in issues if i["severity"] == "warning")
        
        return ValidateSchemaResponse(
            status="success",
            valid=error_count == 0,
            issues=issues,
            error_count=error_count,
            warning_count=warning_count,
            suggestions=suggestions,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))