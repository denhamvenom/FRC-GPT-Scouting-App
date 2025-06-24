# API Contracts Documentation

This document contains comprehensive API contract documentation for the original FRC GPT Scouting App backend. This serves as a preservation reference during refactoring to ensure API compatibility.

**Created**: 2025-06-12  
**Source**: Original backend codebase before refactoring  
**Purpose**: Prevent API contract breakage during refactoring efforts

---

## Global Configuration

- **Base URL**: `http://localhost:8000`
- **CORS**: Enabled for `http://localhost:5173` (frontend development server)
- **Authentication**: None (no authentication middleware)
- **Global Error Handler**: Returns 500 with `{"detail": "Internal server error. Check logs for details."}`

---

## API Endpoints

### 1. Health Check API

#### GET `/api/health/`
- **Description**: Basic health check endpoint
- **Parameters**: None
- **Response**:
  ```json
  {"status": "ok"}
  ```
- **Status Codes**: 200

---

### 2. Google Sheets API

#### GET `/api/sheets/headers`
- **Description**: Get headers from specific Google Sheet tab
- **Query Parameters**:
  - `tab` (string, required): Sheet tab name (e.g., "Scouting", "SuperScouting")
  - `optional` (boolean, default: false): Return empty headers instead of error for missing tabs
  - `spreadsheet_id` (string, optional): Spreadsheet ID (uses active config if not provided)
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "tab": "string",
    "headers": ["string"],
    "count": "number",
    "is_empty": "boolean",
    "error": "string" // only if status is "error"
  }
  ```
- **Status Codes**: 200, 500
- **Dependencies**: Google Sheets API

#### GET `/api/sheets/available-tabs`
- **Description**: Get all available tabs in spreadsheet
- **Query Parameters**:
  - `spreadsheet_id` (string, optional): Spreadsheet ID
  - `event_key` (string, optional): Event key to find configuration
  - `year` (number, optional): Year to find configuration
  - `validate` (boolean, default: false): Whether to validate tabs
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "sheets": ["string"]
  }
  ```
- **Dependencies**: Google Sheets API

#### GET `/api/sheets/sheets`
- **Description**: Get sheet names by spreadsheet ID
- **Query Parameters**:
  - `spreadsheet_id` (string, required): Google Sheet ID
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "sheets": ["string"]
  }
  ```

---

### 3. Schema Learning API

#### GET `/api/schema/learn`
- **Description**: Read scouting spreadsheet headers and map them to game tags using GPT
- **Parameters**: None
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "schema_path": "string",
    "mappings": {
      "match": "object",
      "pit": "object",
      "super": "object"
    },
    "critical_fields": {
      "team_number": ["string"],
      "match_number": ["string"]
    }
  }
  ```
- **Dependencies**: OpenAI GPT API, Google Sheets API, Database

#### POST `/api/schema/save`
- **Description**: Save schema mappings to file
- **Request Body**: JSON object with schema mappings
- **Response**:
  ```json
  {"status": "success"}
  ```

#### POST `/api/schema/save-selections`
- **Description**: Save field selection mappings, critical fields, and robot groups
- **Request Schema**:
  ```json
  {
    "field_selections": {"header": "category"},
    "critical_mappings": {
      "team_number": ["string"],
      "match_number": ["string"]
    },
    "robot_groups": {"group": ["headers"]},
    "year": "number",
    "manual_url": "string" // optional
  }
  ```
- **Response Schema**:
  ```json
  {
    "status": "success",
    "files_saved": ["string"],
    "validation": {
      "issues": ["string"],
      "warnings": ["string"],
      "is_valid": "boolean"
    }
  }
  ```

#### GET `/api/schema/field-selections/{year}`
- **Description**: Get current field selection configuration
- **Path Parameters**:
  - `year` (number, default: 2025): Configuration year
- **Response Schema**:
  ```json
  {
    "status": "success" | "not_found",
    "year": "number",
    "field_selections": {"header": "category"},
    "robot_groups": {"group": ["headers"]},
    "critical_mappings": {
      "team_number": ["string"],
      "match_number": ["string"]
    },
    "manual_url": "string"
  }
  ```

---

### 4. Super Scouting Schema API

#### GET `/api/schema/super/learn`
- **Description**: Learn and map superscouting headers
- **Parameters**: None
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "headers": ["string"],
    "mapping": "object",
    "offsets": "object",
    "insights": "object",
    "sample_analyzed": "boolean"
  }
  ```
- **Dependencies**: OpenAI GPT API, Google Sheets API

#### POST `/api/schema/super/save`
- **Description**: Save superscouting schema mappings and offsets
- **Request Schema**:
  ```json
  {
    "mapping": "object",
    "offsets": "object"
  }
  ```
- **Response**:
  ```json
  {"status": "success"}
  ```

---

### 5. Setup API

#### GET `/api/setup/events`
- **Description**: Get FRC events for specific year
- **Query Parameters**:
  - `year` (number, required): FRC season year
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "year": "number",
    "grouped_events": {"event_type": ["event_objects"]},
    "all_events": ["event_objects"]
  }
  ```
- **Dependencies**: The Blue Alliance API

#### GET `/api/setup/event/{event_key}`
- **Description**: Get detailed event information
- **Path Parameters**:
  - `event_key` (string): TBA event key (e.g., "2023caln")
- **Response Schema**:
  ```json
  {
    "status": "success" | "error", 
    "event": "object"
  }
  ```
- **Dependencies**: The Blue Alliance API

#### POST `/api/setup/start`
- **Description**: Start the learning setup process
- **Request Body** (multipart/form-data):
  - `year` (number, required): FRC season year
  - `event_key` (string, optional): TBA event key
  - `manual_file` (file, optional): Uploaded game manual file
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "event_key": "string",
    "message": "string"
  }
  ```

#### GET `/api/setup/info`
- **Description**: Get current setup information
- **Parameters**: None
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "event_key": "string",
    "year": "number",
    "sheet_config": {
      "id": "number",
      "name": "string",
      "spreadsheet_id": "string",
      "match_scouting_sheet": "string",
      "pit_scouting_sheet": "string",
      "super_scouting_sheet": "string",
      "event_key": "string"
    }
  }
  ```
- **Dependencies**: Database

---

### 6. Picklist Generator API

#### POST `/api/picklist/generate`
- **Description**: Generate ranked picklist using GPT
- **Request Schema**:
  ```json
  {
    "unified_dataset_path": "string",
    "your_team_number": "number",
    "pick_position": "first" | "second" | "third",
    "priorities": [{
      "id": "string",
      "weight": "number", // 0.5-3.0
      "reason": "string"
    }],
    "exclude_teams": ["number"], // optional
    "batch_size": "number", // 5-100, default 20
    "reference_teams_count": "number", // 1-10, default 3
    "reference_selection": "even_distribution" | "percentile" | "top_middle_bottom",
    "use_batching": "boolean",
    "cache_key": "string" // optional
  }
  ```
- **Response Schema**:
  ```json
  {
    "status": "success" | "error",
    "cache_key": "string",
    "picklist": ["team_objects"],
    "batch_processing": {
      "total_batches": "number",
      "current_batch": "number",
      "progress_percentage": "number",
      "processing_complete": "boolean"
    }
  }
  ```
- **Dependencies**: OpenAI GPT API

#### POST `/api/picklist/generate/status`
- **Description**: Get picklist generation status
- **Request Schema**:
  ```json
  {
    "cache_key": "string"
  }
  ```
- **Response Schema**:
  ```json
  {
    "status": "success" | "in_progress" | "not_found",
    "batch_processing": {
      "total_batches": "number",
      "current_batch": "number",
      "progress_percentage": "number",
      "processing_complete": "boolean"
    }
  }
  ```

#### POST `/api/picklist/update`
- **Description**: Update picklist based on user rankings
- **Request Schema**:
  ```json
  {
    "unified_dataset_path": "string",
    "original_picklist": ["team_objects"],
    "user_rankings": [{
      "team_number": "number",
      "position": "number",
      "nickname": "string" // optional
    }]
  }
  ```

#### POST `/api/picklist/rank-missing-teams`
- **Description**: Generate rankings for missing teams
- **Request Schema**:
  ```json
  {
    "unified_dataset_path": "string",
    "missing_team_numbers": ["number"],
    "ranked_teams": ["team_objects"],
    "your_team_number": "number",
    "pick_position": "first" | "second" | "third",
    "priorities": ["MetricPriority_objects"]
  }
  ```

#### POST `/api/picklist/clear-cache`
- **Description**: Clear picklist cache
- **Request Schema** (optional):
  ```json
  {
    "cache_keys": ["string"] // optional, clears specific keys
  }
  ```

#### POST `/api/picklist/compare-teams`
- **Description**: Compare specific teams with analysis
- **Request Schema**:
  ```json
  {
    "unified_dataset_path": "string",
    "team_numbers": ["number"],
    "your_team_number": "number",
    "pick_position": "first" | "second" | "third",
    "priorities": ["MetricPriority_objects"],
    "question": "string", // optional
    "chat_history": [{ // optional
      "type": "question" | "answer",
      "content": "string",
      "timestamp": "string"
    }]
  }
  ```
- **Dependencies**: OpenAI GPT API

---

### 7. Alliance Selection API

#### POST `/api/alliance/lock-picklist`
- **Description**: Lock picklist for alliance selection
- **Request Schema**:
  ```json
  {
    "team_number": "number",
    "event_key": "string",
    "year": "number",
    "first_pick_data": {
      "teams": ["team_objects"],
      "analysis": "object", // optional
      "metadata": "object" // optional
    },
    "second_pick_data": "PicklistData",
    "third_pick_data": "PicklistData", // optional
    "excluded_teams": ["number"], // optional
    "strategy_prompts": "object" // optional
  }
  ```
- **Response Schema**:
  ```json
  {
    "id": "number",
    "team_number": "number",
    "event_key": "string",
    "year": "number",
    "created_at": "string"
  }
  ```
- **Dependencies**: Database

#### GET `/api/alliance/picklists`
- **Description**: Get locked picklists
- **Query Parameters**:
  - `team_number` (number, optional): Filter by team number
  - `event_key` (string, optional): Filter by event key
- **Response Schema**:
  ```json
  {
    "status": "success",
    "picklists": [{
      "id": "number",
      "team_number": "number",
      "event_key": "string",
      "year": "number",
      "created_at": "string",
      "updated_at": "string"
    }]
  }
  ```

#### GET `/api/alliance/picklist/{picklist_id}`
- **Description**: Get specific locked picklist
- **Path Parameters**:
  - `picklist_id` (number): Picklist ID
- **Response Schema**:
  ```json
  {
    "status": "success",
    "picklist": {
      "id": "number",
      "team_number": "number",
      "event_key": "string",
      "year": "number",
      "first_pick_data": "object",
      "second_pick_data": "object",
      "third_pick_data": "object",
      "created_at": "string",
      "updated_at": "string"
    }
  }
  ```

#### DELETE `/api/alliance/picklist/{picklist_id}`
- **Description**: Unlock/delete picklist
- **Response**:
  ```json
  {"status": "success", "message": "string"}
  ```

#### POST `/api/alliance/selection/create`
- **Description**: Create new alliance selection process
- **Request Schema**:
  ```json
  {
    "picklist_id": "number", // optional
    "event_key": "string",
    "year": "number",
    "team_list": ["number"]
  }
  ```

#### GET `/api/alliance/selection/{selection_id}`
- **Description**: Get alliance selection state
- **Path Parameters**:
  - `selection_id` (number): Selection ID
- **Response Schema**:
  ```json
  {
    "status": "success",
    "selection": {
      "id": "number",
      "event_key": "string",
      "year": "number",
      "is_completed": "boolean",
      "current_round": "number",
      "picklist_id": "number",
      "alliances": [{
        "alliance_number": "number",
        "captain_team_number": "number",
        "first_pick_team_number": "number",
        "second_pick_team_number": "number",
        "backup_team_number": "number"
      }],
      "team_statuses": [{
        "team_number": "number",
        "is_captain": "boolean",
        "is_picked": "boolean",
        "has_declined": "boolean",
        "round_eliminated": "number"
      }]
    }
  }
  ```

#### POST `/api/alliance/selection/team-action`
- **Description**: Perform team action during selection
- **Request Schema**:
  ```json
  {
    "selection_id": "number",
    "team_number": "number",
    "action": "captain" | "accept" | "decline" | "remove",
    "alliance_number": "number" // required for captain, accept, remove
  }
  ```

#### POST `/api/alliance/selection/{selection_id}/next-round`
- **Description**: Advance to next selection round
- **Path Parameters**:
  - `selection_id` (number): Selection ID

#### POST `/api/alliance/selection/{selection_id}/reset`
- **Description**: Reset alliance selection to beginning

---

### 8. Validation API

#### GET `/api/validate/event`
- **Description**: Legacy completeness validation
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
- **Response**: Validation results object

#### GET `/api/validate/enhanced`
- **Description**: Enhanced validation with outlier detection
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
  - `z_score_threshold` (number, default: 3.0): Outlier detection threshold
- **Response**: Enhanced validation results with outliers

#### GET `/api/validate/suggest-corrections`
- **Description**: Get suggested corrections for outliers
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
  - `team_number` (number, required): Team number
  - `match_number` (number, required): Match number

#### POST `/api/validate/apply-correction`
- **Description**: Apply corrections to dataset
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
- **Request Schema**:
  ```json
  {
    "team_number": "number",
    "match_number": "number",
    "corrections": "object",
    "reason": "string" // optional
  }
  ```

#### POST `/api/validate/ignore-match`
- **Description**: Mark match as intentionally ignored
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
- **Request Schema**:
  ```json
  {
    "team_number": "number",
    "match_number": "number",
    "reason_category": "not_operational" | "not_present" | "other",
    "reason_text": "string" // optional
  }
  ```

#### POST `/api/validate/create-virtual-scout`
- **Description**: Create virtual scout entry for missing match
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
  - `team_number` (number, required): Team number
  - `match_number` (number, required): Match number

#### GET `/api/validate/preview-virtual-scout`
- **Description**: Preview virtual scout entry without saving
- **Query Parameters**: Same as create-virtual-scout

#### POST `/api/validate/add-to-todo`
- **Description**: Add team-match to todo list
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
  - `team_number` (number, required): Team number
  - `match_number` (number, required): Match number

#### GET `/api/validate/todo-list`
- **Description**: Get current todo list
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset

#### POST `/api/validate/update-todo-status`
- **Description**: Update todo item status
- **Query Parameters**:
  - `unified_dataset_path` (string, required): Path to dataset
- **Request Schema**:
  ```json
  {
    "team_number": "number",
    "match_number": "number",
    "status": "pending" | "completed" | "cancelled"
  }
  ```

---

### 9. Unified Dataset API

#### POST `/api/unified/build`
- **Description**: Build unified dataset for event
- **Request Schema**:
  ```json
  {
    "event_key": "string",
    "year": "number",
    "force_rebuild": "boolean" // optional, default false
  }
  ```
- **Response Schema**:
  ```json
  {
    "status": "processing",
    "message": "string",
    "operation_id": "string"
  }
  ```
- **Dependencies**: Google Sheets API, The Blue Alliance API, Statbotics API

#### GET `/api/unified/status`
- **Description**: Check dataset status
- **Query Parameters**:
  - `event_key` (string, required): Event key
  - `year` (number, required): Year
- **Response Schema**:
  ```json
  {
    "status": "exists" | "not_found",
    "path": "string",
    "last_modified": "string"
  }
  ```

#### GET `/api/unified/dataset`
- **Description**: Get unified dataset content
- **Query Parameters**:
  - `path` (string, optional): Full path to dataset
  - `event_key` (string, optional): Event key (preferred method)
- **Response**: JSON dataset content

---

### 10. Progress Tracking API

#### GET `/api/progress/{operation_id}`
- **Description**: Get operation progress
- **Path Parameters**:
  - `operation_id` (string): Operation ID
- **Response Schema**:
  ```json
  {
    "operation_id": "string",
    "status": "string",
    "progress": "number",
    "message": "string"
  }
  ```

#### GET `/api/progress/`
- **Description**: List all active operations
- **Response**: Array of active operations

---

### 11. Archive API

#### POST `/api/archive/create`
- **Description**: Archive current event data
- **Request Schema**:
  ```json
  {
    "name": "string",
    "event_key": "string",
    "year": "number",
    "notes": "string", // optional
    "created_by": "string" // optional
  }
  ```

#### POST `/api/archive/clear`
- **Description**: Clear all data for specific event
- **Request Schema**:
  ```json
  {
    "event_key": "string",
    "year": "number"
  }
  ```

#### GET `/api/archive/list`
- **Description**: Get list of archived events

#### GET `/api/archive/{archive_id}`
- **Description**: Get specific archived event details
- **Path Parameters**:
  - `archive_id` (number): Archive ID

#### POST `/api/archive/restore`
- **Description**: Restore archived event
- **Request Schema**:
  ```json
  {
    "archive_id": "number"
  }
  ```

#### POST `/api/archive/delete`
- **Description**: Delete archived event

#### POST `/api/archive/archive-and-clear`
- **Description**: Archive event then clear data

---

### 12. Sheet Configuration API

#### POST `/api/sheet-config/create`
- **Description**: Create/update sheet configuration
- **Request Schema**:
  ```json
  {
    "name": "string",
    "spreadsheet_id": "string", 
    "match_scouting_sheet": "string",
    "event_key": "string",
    "year": "number",
    "pit_scouting_sheet": "string", // optional
    "super_scouting_sheet": "string", // optional
    "set_active": "boolean" // default true
  }
  ```

#### GET `/api/sheet-config/list`
- **Description**: List sheet configurations
- **Query Parameters**:
  - `event_key` (string, optional): Filter by event
  - `year` (number, optional): Filter by year

#### GET `/api/sheet-config/active`
- **Description**: Get active sheet configuration

#### GET `/api/sheet-config/{config_id}`
- **Description**: Get specific configuration
- **Path Parameters**:
  - `config_id` (number): Configuration ID

#### POST `/api/sheet-config/set-active`
- **Description**: Set configuration as active
- **Request Schema**:
  ```json
  {
    "config_id": "number"
  }
  ```

#### DELETE `/api/sheet-config/{config_id}`
- **Description**: Delete configuration

#### POST `/api/sheet-config/test-connection`
- **Description**: Test Google Sheet connection
- **Request Schema**:
  ```json
  {
    "spreadsheet_id": "string",
    "sheet_name": "string" // optional
  }
  ```

#### GET `/api/sheet-config/available-sheets`
- **Description**: Get available sheets in spreadsheet
- **Query Parameters**:
  - `spreadsheet_id` (string, optional): Spreadsheet ID
  - `event_key` (string, optional): Event key
  - `year` (number, optional): Year
  - `validate` (boolean, default: false): Whether to validate

---

### 13. Picklist Analysis API

#### POST `/api/picklist/analyze`
- **Description**: Analyze dataset for picklist suggestions
- **Request Schema**:
  ```json
  {
    "unified_dataset_path": "string",
    "priorities": ["MetricPriority_objects"], // optional
    "strategy_prompt": "string" // optional
  }
  ```

---

### 14. Debug Logs API

#### GET `/api/debug/logs/picklist`
- **Description**: Get recent picklist generation logs
- **Query Parameters**:
  - `lines` (number, default: 100): Number of log lines to return

---

### 15. Manuals API

#### POST `/api/manuals/process-sections`
- **Description**: Process selected sections from game manual
- **Request Schema**:
  ```json
  {
    "manual_identifier": "string",
    "year": "number",
    "selected_sections": [{
      "title": "string",
      "level": "number",
      "page": "number"
    }]
  }
  ```

#### GET `/api/manuals`
- **Description**: List all uploaded game manuals

#### GET `/api/manuals/{manual_id}`
- **Description**: Get manual details with ToC
- **Path Parameters**:
  - `manual_id` (number): Manual ID

#### DELETE `/api/manuals/{manual_id}`
- **Description**: Delete manual and associated files

---

### 16. Prompt Builder API

#### POST `/api/prompt-builder`
- **Description**: Build prompt from manual and sheet
- **Query Parameters**:
  - `sheet_url` (string, required): Google Sheet URL or ID

#### GET `/api/prompt-builder/variables`
- **Description**: Get suggested scouting variables

---

### 17. Root Endpoint

#### GET `/`
- **Description**: Basic API status
- **Response**:
  ```json
  {"message": "Backend is running!"}
  ```

---

## Common Response Patterns

### Success Response
```json
{
  "status": "success",
  "data": "object or array"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "string",
  "details": "object" // optional
}
```

### Progress Response
```json
{
  "status": "processing",
  "operation_id": "string",
  "progress": "number", // 0-100
  "message": "string"
}
```

---

## Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters, validation errors)
- **404**: Not Found (resource doesn't exist)
- **500**: Internal Server Error (server processing errors)

---

## External API Dependencies

### Google Sheets API
- **Used by**: `/api/sheets/*`, Schema learning, Dataset building
- **Authentication**: Service account JSON file
- **Rate Limits**: Google's standard API limits

### OpenAI GPT API
- **Used by**: Schema learning, Picklist generation, Team comparison
- **Authentication**: API key
- **Models**: GPT-4.1 (primary), GPT-3.5-turbo (fallback)

### The Blue Alliance API
- **Used by**: Event data, Team information, Match results
- **Authentication**: TBA API key
- **Rate Limits**: TBA's standard rate limits

### Statbotics API
- **Used by**: EPA metrics, Team statistics
- **Authentication**: None (public API)
- **Rate Limits**: Statbotics' standard limits

---

## Data Validation Patterns

### Pydantic Models
- Extensive use of Pydantic for request/response validation
- Custom validators for team numbers, pick positions, percentages
- Nested model validation for complex objects

### Common Validations
- `team_number`: Integer, typically 1-9999
- `pick_position`: Enum ["first", "second", "third"]
- `weight`: Float, typically 0.5-3.0
- `event_key`: String format matching TBA event keys
- `year`: Integer, FRC season year

---

## Critical Preservation Requirements

During refactoring, these API contracts MUST be preserved:

1. **All endpoint paths and HTTP methods**
2. **Request parameter names and types**
3. **Response schema structures**
4. **Status code behaviors**
5. **Query parameter formats**
6. **Request body schemas**
7. **Error response formats**

**Breaking any of these contracts will break frontend functionality.**