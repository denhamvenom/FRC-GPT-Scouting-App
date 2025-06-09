"""
Schema API Schemas

This module contains schemas specific to the schema learning and mapping API endpoints.
Includes models for schema discovery, field mapping, and configuration.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

from .common import SuccessResponse


class FieldType(str, Enum):
    """Supported field data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    ARRAY = "array"
    UNKNOWN = "unknown"


class FieldCategory(str, Enum):
    """Categories for organizing fields"""
    TEAM_INFO = "team_info"
    MATCH_INFO = "match_info"
    AUTONOMOUS = "autonomous"
    TELEOP = "teleop"
    ENDGAME = "endgame"
    FOULS = "fouls"
    STRATEGY = "strategy"
    METADATA = "metadata"
    CUSTOM = "custom"


class SchemaField(BaseModel):
    """Represents a field in the schema"""
    name: str = Field(..., description="Field name")
    display_name: str = Field(..., description="Human-readable name")
    type: FieldType = Field(..., description="Data type")
    category: FieldCategory = Field(FieldCategory.CUSTOM, description="Field category")
    description: Optional[str] = Field(None, description="Field description")
    source: str = Field("sheets", description="Data source")
    required: bool = Field(False, description="Whether field is required")
    nullable: bool = Field(True, description="Whether field can be null")
    unique: bool = Field(False, description="Whether values must be unique")
    default_value: Optional[Any] = Field(None, description="Default value if missing")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    mapping: Optional[str] = Field(None, description="Mapping to standard field")
    examples: Optional[List[Any]] = Field(None, description="Example values")

    class Config:
        schema_extra = {
            "example": {
                "name": "teleop_speaker_scores",
                "display_name": "Teleop Speaker Scores",
                "type": "integer",
                "category": "teleop",
                "description": "Number of notes scored in speaker during teleop",
                "source": "sheets",
                "required": False,
                "nullable": True,
                "default_value": 0,
                "validation_rules": {
                    "min": 0,
                    "max": 20
                },
                "examples": [0, 3, 5, 8]
            }
        }


class FieldMapping(BaseModel):
    """Mapping between source field and standard field"""
    source_field: str = Field(..., description="Original field name")
    target_field: str = Field(..., description="Standard field name")
    transform: Optional[str] = Field(None, description="Transformation to apply")
    confidence: float = Field(1.0, ge=0, le=1, description="Mapping confidence")
    auto_mapped: bool = Field(False, description="Whether mapping was automatic")

    class Config:
        schema_extra = {
            "example": {
                "source_field": "Speaker Notes (Teleop)",
                "target_field": "teleop_speaker_scores",
                "transform": None,
                "confidence": 0.95,
                "auto_mapped": True
            }
        }


class SchemaValidationIssue(BaseModel):
    """Issue found during schema validation"""
    field: str = Field(..., description="Field with issue")
    issue_type: str = Field(..., description="Type of issue")
    severity: Literal["error", "warning", "info"] = Field(..., description="Severity")
    message: str = Field(..., description="Issue description")
    suggestion: Optional[str] = Field(None, description="Suggested fix")

    class Config:
        schema_extra = {
            "example": {
                "field": "team_number",
                "issue_type": "missing_required",
                "severity": "error",
                "message": "Required field 'team_number' not found in schema",
                "suggestion": "Map one of your fields to 'team_number'"
            }
        }


class SchemaTemplate(BaseModel):
    """Pre-defined schema template"""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    year: int = Field(..., description="Game year")
    description: str = Field(..., description="Template description")
    fields: List[SchemaField] = Field(..., description="Template fields")
    version: str = Field(..., description="Template version")

    class Config:
        schema_extra = {
            "example": {
                "id": "frc2025_standard",
                "name": "FRC 2025 Standard Schema",
                "year": 2025,
                "description": "Standard scouting schema for 2025 game",
                "fields": [],
                "version": "1.0.0"
            }
        }


# Request Models

class LearnSchemaRequest(BaseModel):
    """Request to learn schema from data source"""
    source: Literal["sheets", "csv", "json"] = Field("sheets", description="Data source type")
    sheet_id: Optional[str] = Field(None, description="Google Sheet ID")
    sheet_name: Optional[str] = Field(None, description="Sheet tab name")
    sample_data: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Sample data for schema inference"
    )
    auto_map: bool = Field(True, description="Automatically map to standard fields")
    include_stats: bool = Field(True, description="Include field statistics")

    @validator('sheet_id')
    def validate_sheet_source(cls, v, values):
        """Validate sheet_id is provided when source is sheets"""
        if values.get('source') == 'sheets' and not v:
            raise ValueError("sheet_id is required when source is 'sheets'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "source": "sheets",
                "sheet_id": "1234567890abcdef",
                "sheet_name": "Scouting Data",
                "auto_map": True,
                "include_stats": True
            }
        }


class UpdateSchemaRequest(BaseModel):
    """Request to update schema configuration"""
    fields: List[SchemaField] = Field(..., description="Updated field definitions")
    mappings: Optional[List[FieldMapping]] = Field(None, description="Field mappings")
    validate_schema: bool = Field(True, description="Validate schema before saving")

    class Config:
        schema_extra = {
            "example": {
                "fields": [],
                "mappings": [],
                "validate": True
            }
        }


class MapFieldsRequest(BaseModel):
    """Request to map fields"""
    mappings: List[FieldMapping] = Field(..., description="Field mappings to apply")
    validate_mappings: bool = Field(True, description="Validate mappings")
    preserve_existing: bool = Field(True, description="Keep existing mappings")

    class Config:
        schema_extra = {
            "example": {
                "mappings": [
                    {
                        "source_field": "Team #",
                        "target_field": "team_number",
                        "confidence": 1.0
                    }
                ],
                "validate_mappings": True,
                "preserve_existing": True
            }
        }


class ValidateSchemaRequest(BaseModel):
    """Request to validate schema"""
    schema_fields: Optional[List[SchemaField]] = Field(
        None,
        description="Schema to validate (None = use current)"
    )
    strict: bool = Field(False, description="Use strict validation")
    check_data: bool = Field(False, description="Validate against actual data")

    class Config:
        schema_extra = {
            "example": {
                "strict": False,
                "check_data": True
            }
        }


# Response Models

class LearnSchemaResponse(SuccessResponse):
    """Response from schema learning"""
    fields_discovered: int = Field(..., description="Number of fields discovered")
    fields: List[SchemaField] = Field(..., description="Discovered fields")
    mappings: List[FieldMapping] = Field(..., description="Automatic field mappings")
    mapping_confidence: float = Field(..., ge=0, le=1, description="Overall mapping confidence")
    warnings: List[str] = Field(default_factory=list, description="Learning warnings")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Field statistics")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "fields_discovered": 25,
                "fields": [],
                "mappings": [],
                "mapping_confidence": 0.85,
                "warnings": ["Could not determine type for field 'notes'"],
                "statistics": {
                    "total_rows_analyzed": 100,
                    "completeness": 0.92
                }
            }
        }


class SchemaResponse(SuccessResponse):
    """Response containing current schema"""
    event_key: Optional[str] = Field(None, description="Associated event")
    fields: List[SchemaField] = Field(..., description="Schema fields")
    mappings: List[FieldMapping] = Field(..., description="Field mappings")
    total_fields: int = Field(..., description="Total number of fields")
    mapped_fields: int = Field(..., description="Number of mapped fields")
    required_fields_missing: List[str] = Field(
        default_factory=list,
        description="Required fields that are missing"
    )
    last_updated: Optional[str] = Field(None, description="Last update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "event_key": "2025arc",
                "fields": [],
                "mappings": [],
                "total_fields": 25,
                "mapped_fields": 20,
                "required_fields_missing": [],
                "last_updated": "2025-01-01T12:00:00Z"
            }
        }


class ValidateSchemaResponse(SuccessResponse):
    """Response from schema validation"""
    valid: bool = Field(..., description="Whether schema is valid")
    issues: List[SchemaValidationIssue] = Field(..., description="Validation issues")
    error_count: int = Field(..., description="Number of errors")
    warning_count: int = Field(..., description="Number of warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "valid": False,
                "issues": [
                    {
                        "field": "team_number",
                        "issue_type": "missing_required",
                        "severity": "error",
                        "message": "Required field not found"
                    }
                ],
                "error_count": 1,
                "warning_count": 2,
                "suggestions": [
                    "Consider adding descriptions to fields",
                    "Map remaining unmapped fields"
                ]
            }
        }


class SchemaTemplatesResponse(SuccessResponse):
    """Response containing available schema templates"""
    templates: List[SchemaTemplate] = Field(..., description="Available templates")
    current_year: int = Field(..., description="Current competition year")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "templates": [],
                "current_year": 2025
            }
        }


class SchemaExportResponse(SuccessResponse):
    """Response for schema export"""
    format: str = Field(..., description="Export format")
    content: Dict[str, Any] = Field(..., description="Exported schema content")
    filename: str = Field(..., description="Suggested filename")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "format": "json",
                "content": {
                    "version": "1.0",
                    "fields": []
                },
                "filename": "schema_2025arc_20250101.json"
            }
        }