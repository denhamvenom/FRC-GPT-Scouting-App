/**
 * API Response type definitions
 */

// Common Response Types
export interface SuccessResponse {
  success: boolean;
  message?: string;
}

export interface ErrorResponse {
  detail: string;
  status_code?: number;
  headers?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// Alliance Selection Responses
export interface AllianceSelectionResponse {
  event_key: string;
  alliances: Alliance[];
  available_teams: TeamStatus[];
  current_round: number;
  current_alliance: number;
  is_complete: boolean;
  created_at: string;
  updated_at: string;
}

export interface Alliance {
  number: number;
  captain?: TeamStatus;
  pick1?: TeamStatus;
  pick2?: TeamStatus;
  backup?: TeamStatus;
}

export interface TeamStatus {
  team_number: number;
  team_name: string;
  status: 'available' | 'captain' | 'picked' | 'declined';
  alliance_number?: number;
  declined_alliances?: number[];
}

// Picklist Generation Responses
export interface PicklistGenerateResponse {
  operation_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  picklist?: Array<{
    team_number: number;
    nickname: string;
    score: number;
    reasoning: string;
    rank?: number;
    tier?: string;
    strengths?: string[];
    concerns?: string[];
  }>;
  analysis?: string;
  missing_team_numbers?: number[];
  performance?: {
    tokens_used: number;
    processing_time: number;
  };
  error_message?: string;
}

export interface PicklistStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  result?: PicklistGenerateResponse;
}

export interface TeamComparisonResponse {
  comparison: string;
  teams: Array<{
    team_number: number;
    nickname: string;
    strengths: string[];
    weaknesses: string[];
    recommendation: string;
  }>;
  recommendation: string;
}

export interface LockedPicklistResponse {
  id: number;
  event_key: string;
  picklist: any[];
  excluded_teams: number[];
  strategy_prompt?: string;
  created_at: string;
}

// Validation Responses
export interface ValidationResponse {
  outliers: Array<{
    teamNumber: number;
    field: string;
    value: any;
    zScore?: number;
    iqrScore?: number;
    reason: string;
    severity: 'low' | 'medium' | 'high';
  }>;
  todos: Array<{
    teamNumber: number;
    field: string;
    reason: string;
    priority: 'low' | 'medium' | 'high';
  }>;
  summary: {
    totalOutliers: number;
    totalTodos: number;
    affectedTeams: number;
    dataQuality: number;
  };
}

export interface ValidationPreviewResponse {
  preview: Array<{
    teamNumber: number;
    teamName: string;
    fields: Record<string, any>;
    virtualScoutingData: Record<string, any>;
  }>;
}

// Dataset Building Responses
export interface DatasetBuildResponse {
  success: boolean;
  message: string;
  file_path?: string;
  cache_used?: boolean;
}

export interface DatasetStatusResponse {
  exists: boolean;
  file_path?: string;
  created_at?: string;
  size?: number;
  team_count?: number;
  field_count?: number;
}

// Event Management Responses
export interface EventResponse {
  key: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  team_count?: number;
  match_count?: number;
}

export interface ArchivedEventResponse {
  id: number;
  event_key: string;
  event_name: string;
  archived_at: string;
  data_types: string[];
  file_size: number;
}

// Schema Learning Responses
export interface SchemaLearnResponse {
  detected_fields: Array<{
    original_name: string;
    suggested_mapping: string;
    confidence: number;
    data_type: string;
    sample_values: any[];
  }>;
  unmapped_fields: string[];
  statistics: {
    total_fields: number;
    mapped_fields: number;
    confidence_average: number;
  };
}

export interface SchemaMappingResponse {
  event_key: string;
  mapping: Record<string, string>;
  created_at: string;
  updated_at: string;
}

// Sheet Configuration Responses
export interface SheetConfigResponse {
  event_key: string;
  tab_name: string;
  has_headers: boolean;
  headers?: string[];
  created_at: string;
  updated_at: string;
}

export interface SheetsListResponse {
  sheets: Array<{
    name: string;
    index: number;
    row_count: number;
    column_count: number;
  }>;
}

// Team Responses
export interface TeamResponse {
  team_number: number;
  nickname: string;
  name: string;
  city?: string;
  state_prov?: string;
  country?: string;
  rookie_year?: number;
  events?: EventResponse[];
  stats?: Record<string, any>;
}

// Progress Tracking Responses
export interface ProgressResponse {
  operation_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  started_at: string;
  updated_at: string;
  estimated_completion?: string;
  result?: any;
  error?: string;
}

// Field Selection Responses
export interface FieldsResponse {
  tba_fields: Array<{
    key: string;
    name: string;
    description?: string;
    data_type: string;
  }>;
  statbotics_fields: Array<{
    key: string;
    name: string;
    description?: string;
    data_type: string;
  }>;
  sheets_fields: Array<{
    key: string;
    name: string;
    description?: string;
    data_type: string;
  }>;
  selected_fields?: Record<string, any>;
}

// Setup Responses
export interface SetupInfoResponse {
  current_event?: EventResponse;
  has_sheet_config: boolean;
  has_field_selection: boolean;
  has_unified_dataset: boolean;
  has_schema_mapping: boolean;
  is_ready: boolean;
  missing_steps: string[];
}

// Manual Processing Responses
export interface ManualProcessResponse {
  success: boolean;
  sections_processed: string[];
  output_file?: string;
  message: string;
}

// Debug Responses
export interface DebugLogsResponse {
  logs: string[];
  total_lines: number;
  file_path: string;
}