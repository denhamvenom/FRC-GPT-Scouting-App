/**
 * API Request type definitions
 */

// Alliance Selection Requests
export interface CreateAllianceSelectionRequest {
  event_key: string;
  captain_meetings?: boolean;
}

export interface TeamActionRequest {
  action: 'captain' | 'accept' | 'decline' | 'remove';
  team_number: number;
  alliance_number?: number;
  pick_number?: number;
  backup_team?: number;
}

// Picklist Generation Requests
export interface GeneratePicklistRequest {
  event_key: string;
  unified_dataset_path: string;
  team_position: 'overall' | 'pick1' | 'pick2' | 'dnp';
  excluded_teams?: number[];
  strategy_prompt?: string;
  use_batching?: boolean;
}

export interface CompareTeamsRequest {
  event_key: string;
  unified_dataset_path: string;
  teams: number[];
  comparison_prompt: string;
}

export interface LockPicklistRequest {
  event_key: string;
  picklist: Array<{
    team_number: number;
    nickname: string;
    score: number;
    reasoning: string;
  }>;
  excluded_teams?: number[];
  strategy_prompt?: string;
}

// Validation Requests
export interface ValidationRequest {
  unified_dataset_path: string;
  event_key: string;
}

export interface CorrectValidationRequest {
  unified_dataset_path: string;
  corrections: Array<{
    teamNumber: number;
    field: string;
    correctedValue: any;
    correctionType: string;
  }>;
}

export interface VirtualScoutRequest {
  unified_dataset_path: string;
  todos: Array<{
    teamNumber: number;
    field: string;
    value: any;
  }>;
}

// Dataset Building Requests
export interface BuildDatasetRequest {
  event_key: string;
  fields: Record<string, any>;
  sheet_config?: {
    tab_name?: string;
    has_headers?: boolean;
    headers?: string[];
  };
  force_refresh?: boolean;
}

export interface DatasetStatusRequest {
  event_key: string;
}

// Event Management Requests
export interface UpdateEventRequest {
  name?: string;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
}

export interface ArchiveEventRequest {
  event_key: string;
  archive_picklists?: boolean;
  archive_alliance_selection?: boolean;
  archive_sheet_config?: boolean;
}

// Schema Learning Requests
export interface LearnSchemaRequest {
  data: Record<string, any>[];
  year?: number;
}

export interface SaveSchemaMappingRequest {
  event_key: string;
  mapping: Record<string, string>;
}

// Sheet Configuration Requests
export interface SaveSheetConfigRequest {
  event_key: string;
  tab_name: string;
  has_headers: boolean;
  headers?: string[];
}

export interface GetSheetsRequest {
  force_refresh?: boolean;
}

// Team Requests
export interface GetTeamRequest {
  team_number: number;
  event_key?: string;
}

export interface GetTeamHistoryRequest {
  team_number: number;
  limit?: number;
}

// Progress Tracking Requests
export interface GetProgressRequest {
  operation_id: string;
}

// Field Selection Requests
export interface GetFieldsRequest {
  event_key: string;
  year?: number;
}

export interface SaveFieldSelectionRequest {
  event_key: string;
  fields: Record<string, any>;
}

// Manual Processing Requests
export interface ProcessManualRequest {
  year: number;
  sections?: string[];
}

// Debug Requests
export interface GetDebugLogsRequest {
  log_type: 'picklist' | 'validation' | 'dataset';
  lines?: number;
}