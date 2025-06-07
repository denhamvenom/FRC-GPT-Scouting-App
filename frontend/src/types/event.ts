// Event-related Types for FRC GPT Scouting App

import { APIResponse } from './api';
import { Team } from './team';

// Core FRC Event
export interface FRCEvent {
  key: string;
  name: string;
  code: string;
  location: string;
  dates: string;
  type: "regional" | "district" | "championship" | "offseason" | "preseason";
  week?: number;
  year: number;
  country?: string;
  state?: string;
  city?: string;
  timezone?: string;
  website?: string;
  live_stream_url?: string;
  webcasts?: Array<{
    type: string;
    channel: string;
    url: string;
  }>;
}

// Event Configuration
export interface EventConfiguration {
  event_key: string;
  year: number;
  is_active: boolean;
  sheet_config_id?: number;
  field_selection_complete: boolean;
  validation_rules: ValidationRules;
  custom_settings: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

// Validation Rules for Event
export interface ValidationRules {
  enable_outlier_detection: boolean;
  z_score_threshold: number;
  iqr_multiplier: number;
  min_matches_for_validation: number;
  enable_completeness_check: boolean;
  enable_consistency_check: boolean;
  custom_validation_rules: CustomValidationRule[];
}

export interface CustomValidationRule {
  id: string;
  name: string;
  field: string;
  condition: "greater_than" | "less_than" | "equals" | "not_equals" | "in_range" | "not_in_range";
  value: any;
  severity: "error" | "warning" | "info";
  enabled: boolean;
}

// Event Setup Information
export interface EventSetupInfo {
  status: "success" | "error" | "incomplete";
  event_key?: string;
  year: number;
  event_name?: string;
  sheet_config?: SheetConfiguration;
  field_selection_status?: "not_started" | "in_progress" | "completed";
  validation_status?: "not_started" | "in_progress" | "completed";
  dataset_status?: "not_available" | "building" | "available" | "outdated";
  setup_progress?: {
    steps_completed: number;
    total_steps: number;
    current_step: string;
    next_step?: string;
  };
}

// Sheet Configuration
export interface SheetConfiguration {
  id: number;
  name: string;
  spreadsheet_id: string;
  match_scouting_sheet: string;
  pit_scouting_sheet?: string;
  super_scouting_sheet?: string;
  event_key: string;
  year: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  match_scouting_headers?: string[];
  pit_scouting_headers?: string[];
  super_scouting_headers?: string[];
  formatted_date: string;
  last_sync?: string;
  row_count?: {
    match_scouting: number;
    pit_scouting?: number;
    super_scouting?: number;
  };
}

// Event Data Statistics
export interface EventDataStatistics {
  event_key: string;
  year: number;
  total_teams: number;
  total_matches: number;
  scouting_coverage: {
    match_scouting_percentage: number;
    pit_scouting_percentage: number;
    super_scouting_percentage?: number;
  };
  data_quality: {
    completeness_score: number;
    consistency_score: number;
    outlier_count: number;
    missing_data_count: number;
  };
  last_updated: string;
}

// Archived Event
export interface ArchivedEvent {
  id: number;
  name: string;
  event_key: string;
  year: number;
  archive_metadata: ArchiveMetadata;
  is_active: boolean;
  created_at: string;
  created_by?: string;
  notes?: string;
  formatted_date: string;
  file_size?: number;
  download_url?: string;
}

export interface ArchiveMetadata {
  teams_count: number;
  matches_count: number;
  scouting_entries: number;
  pit_entries: number;
  super_entries?: number;
  picklists_count: number;
  alliances_count: number;
  data_sources: string[];
  compression_ratio?: number;
  archive_version: string;
}

// Event Match
export interface EventMatch {
  match_number: number;
  match_type: "qualification" | "playoff" | "practice";
  red_alliance: EventAlliance;
  blue_alliance: EventAlliance;
  red_score?: number;
  blue_score?: number;
  winning_alliance?: "red" | "blue" | "tie";
  scheduled_time?: string;
  actual_time?: string;
  status: "scheduled" | "in_progress" | "completed" | "cancelled";
  video_url?: string;
}

export interface EventAlliance {
  teams: number[];
  score?: number;
  ranking_points?: number;
  fouls?: number;
  tech_fouls?: number;
  auto_points?: number;
  teleop_points?: number;
  endgame_points?: number;
}

// Event Rankings
export interface EventRankings {
  event_key: string;
  year: number;
  rankings: Array<{
    rank: number;
    team_number: number;
    ranking_points: number;
    avg_points: number;
    record: {
      wins: number;
      losses: number;
      ties: number;
    };
    matches_played: number;
    sort_orders: number[];
  }>;
  sort_order_info: Array<{
    name: string;
    precision: number;
  }>;
  last_updated: string;
}

// API Request Types
export interface CreateSheetConfigRequest {
  name: string;
  spreadsheet_id: string;
  match_scouting_sheet: string;
  event_key: string;
  year: number;
  pit_scouting_sheet?: string;
  super_scouting_sheet?: string;
  set_active?: boolean;
}

export interface UpdateSheetConfigRequest {
  config_id: number;
  name?: string;
  spreadsheet_id?: string;
  match_scouting_sheet?: string;
  pit_scouting_sheet?: string;
  super_scouting_sheet?: string;
  is_active?: boolean;
}

export interface TestConnectionRequest {
  spreadsheet_id: string;
  sheet_name?: string;
}

export interface CreateArchiveRequest {
  event_key: string;
  year: number;
  name: string;
  include_scouting_data: boolean;
  include_picklists: boolean;
  include_alliances: boolean;
  notes?: string;
}

export interface RestoreArchiveRequest {
  archive_id: number;
  target_event_key?: string;
  overwrite_existing?: boolean;
}

// API Response Types
export type FRCEventResponse = APIResponse<FRCEvent>;
export type FRCEventListResponse = APIResponse<FRCEvent[]>;
export type EventSetupInfoResponse = APIResponse<EventSetupInfo>;
export type SheetConfigurationResponse = APIResponse<SheetConfiguration>;
export type SheetConfigurationListResponse = APIResponse<SheetConfiguration[]>;
export type EventDataStatisticsResponse = APIResponse<EventDataStatistics>;
export type ArchivedEventResponse = APIResponse<ArchivedEvent>;
export type ArchivedEventListResponse = APIResponse<ArchivedEvent[]>;
export type EventMatchResponse = APIResponse<EventMatch[]>;
export type EventRankingsResponse = APIResponse<EventRankings>;
export type TestConnectionResponse = APIResponse<{
  success: boolean;
  sheet_info?: {
    title: string;
    sheet_count: number;
    last_modified: string;
  };
  error_message?: string;
}>;

// Event Search and Filter Types
export interface EventSearchParams {
  year?: number;
  type?: "regional" | "district" | "championship" | "offseason";
  country?: string;
  state?: string;
  week?: number;
  search_query?: string;
}

export interface EventFilterOptions {
  sort_by?: "name" | "date" | "location" | "type";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
  include_past?: boolean;
  include_future?: boolean;
}

// Event Status Types
export type EventStatus = 
  | "upcoming" 
  | "in_progress" 
  | "completed" 
  | "cancelled" 
  | "postponed";

export type EventPhase = 
  | "registration" 
  | "qualification" 
  | "alliance_selection" 
  | "playoffs" 
  | "awards" 
  | "concluded";

// Event Workflow
export interface EventWorkflow {
  event_key: string;
  current_phase: EventPhase;
  phases: Array<{
    phase: EventPhase;
    status: "not_started" | "in_progress" | "completed" | "skipped";
    start_time?: string;
    end_time?: string;
    progress_percentage?: number;
  }>;
  next_phase?: EventPhase;
  estimated_completion?: string;
}

// Event Performance Summary
export interface EventPerformanceSummary {
  event_key: string;
  year: number;
  team_count: number;
  match_count: number;
  average_score: number;
  highest_score: number;
  top_performers: Team[];
  award_winners: Array<{
    award_name: string;
    team_number: number;
    recipient_name?: string;
  }>;
  statistics: {
    total_points_scored: number;
    average_margin: number;
    closest_match_margin: number;
    penalty_rate: number;
  };
}