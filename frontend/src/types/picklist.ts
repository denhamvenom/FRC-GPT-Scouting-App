// Picklist-related Types for FRC GPT Scouting App

import { APIResponse, BatchProcessingStatus } from './api';
import { Team, MetricPriority, UserRanking } from './team';

// Core Picklist Data
export interface PicklistData {
  teams: Team[];
  analysis?: Record<string, string>;
  metadata?: PicklistMetadata;
  generation_timestamp?: string;
  cache_key?: string;
}

// Picklist Metadata
export interface PicklistMetadata {
  total_teams: number;
  generation_method: "gpt" | "statistical" | "manual" | "hybrid";
  generation_time_ms: number;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  confidence_score?: number;
  data_source: string;
  filters_applied?: string[];
  exclusions_applied?: number[];
}

// Locked Picklist (Database Entity)
export interface LockedPicklist {
  id: number;
  team_number: number;
  event_key: string;
  year: number;
  first_pick_data: PicklistData;
  second_pick_data: PicklistData;
  third_pick_data?: PicklistData;
  excluded_teams?: number[];
  strategy_prompts?: Record<string, string>;
  created_at: string;
  updated_at?: string;
  is_locked: boolean;
  notes?: string;
}

// Picklist Generation Request
export interface PicklistRequest {
  unified_dataset_path: string;
  your_team_number: number;
  pick_position: "first" | "second" | "third";
  priorities: MetricPriority[];
  exclude_teams?: number[];
  batch_size?: number; // 5-100, default 20
  reference_teams_count?: number; // 1-10, default 3
  reference_selection?: "even_distribution" | "percentile" | "top_middle_bottom";
  use_batching: boolean;
  cache_key?: string;
  force_regenerate?: boolean;
  strategy_prompts?: Record<string, string>;
}

// Picklist Generation Status
export interface PicklistGenerationStatus {
  status: "in_progress" | "success" | "not_found" | "error";
  batch_processing: BatchProcessingStatus;
  picklist?: Team[];
  cache_key?: string;
  error_message?: string;
  estimated_completion_time?: string;
  current_batch_teams?: number[];
}

// Picklist Update Request
export interface UpdatePicklistRequest {
  unified_dataset_path: string;
  original_picklist: Team[];
  user_rankings: UserRanking[];
  preserve_analysis?: boolean;
  regenerate_missing_analysis?: boolean;
}

// Rank Missing Teams Request
export interface RankMissingTeamsRequest {
  unified_dataset_path: string;
  missing_team_numbers: number[];
  ranked_teams: Team[];
  your_team_number: number;
  pick_position: "first" | "second" | "third";
  priorities: MetricPriority[];
  context_teams?: number[]; // Teams to provide context for ranking
}

// Lock Picklist Request
export interface LockPicklistRequest {
  team_number: number;
  event_key: string;
  year: number;
  first_pick_data: PicklistData;
  second_pick_data: PicklistData;
  third_pick_data?: PicklistData;
  excluded_teams?: number[];
  strategy_prompts?: Record<string, string>;
  notes?: string;
}

// Picklist Analysis Response
export interface PicklistAnalysisResponse {
  status: "success" | "error";
  game_metrics: GameMetric[];
  universal_metrics: GameMetric[];
  superscout_metrics: GameMetric[];
  pit_metrics: GameMetric[];
  suggested_metrics: MetricPriority[];
  metrics_stats: Record<string, any>;
  parsed_priorities?: MetricPriority[];
  team_rankings?: Team[];
  analysis_metadata?: AnalysisMetadata;
}

// Game Metric Definition
export interface GameMetric {
  id: string;
  name: string;
  category: "auto" | "teleop" | "endgame" | "strategy" | "universal" | "pit";
  description: string;
  data_type: "numeric" | "boolean" | "categorical";
  unit?: string;
  range?: {
    min: number;
    max: number;
  };
  statistics?: {
    mean?: number;
    median?: number;
    std_dev?: number;
    min?: number;
    max?: number;
    distribution?: Record<string, number>;
  };
  importance_score?: number;
  correlation_with_success?: number;
}

// Analysis Metadata
export interface AnalysisMetadata {
  analysis_timestamp: string;
  dataset_size: number;
  metrics_analyzed: number;
  teams_analyzed: number;
  confidence_level: number;
  data_quality_score: number;
  outliers_detected: number;
  missing_data_percentage: number;
}

// Picklist Configuration
export interface PicklistConfiguration {
  default_batch_size: number;
  max_batch_size: number;
  default_reference_teams: number;
  max_reference_teams: number;
  cache_duration_hours: number;
  enable_token_optimization: boolean;
  enable_similarity_grouping: boolean;
  priority_weight_limits: {
    min: number;
    max: number;
  };
}

// Picklist Export Options
export interface PicklistExportOptions {
  format: "json" | "csv" | "pdf" | "excel";
  include_analysis: boolean;
  include_metadata: boolean;
  include_rankings: boolean;
  team_details_level: "basic" | "detailed" | "full";
  sort_by?: "rank" | "team_number" | "performance";
}

// Picklist Comparison
export interface PicklistComparison {
  baseline_picklist: PicklistData;
  comparison_picklist: PicklistData;
  differences: {
    rank_changes: Array<{
      team_number: number;
      old_rank: number;
      new_rank: number;
      rank_change: number;
    }>;
    new_teams: number[];
    removed_teams: number[];
    significant_changes: Array<{
      team_number: number;
      change_type: "major_improvement" | "major_decline" | "new_entry" | "dropped_out";
      description: string;
    }>;
  };
  similarity_score: number;
  recommendation: string;
}

// Picklist History
export interface PicklistHistory {
  picklist_id: number;
  versions: Array<{
    version: number;
    timestamp: string;
    generated_by: "system" | "user";
    change_summary: string;
    data: PicklistData;
  }>;
  generation_log: Array<{
    timestamp: string;
    action: "generated" | "updated" | "locked" | "exported";
    details: string;
    user?: string;
  }>;
}

// API Response Types
export type PicklistResponse = APIResponse<PicklistData>;
export type PicklistAnalysisApiResponse = APIResponse<PicklistAnalysisResponse>;
export type PicklistGenerationStatusResponse = APIResponse<PicklistGenerationStatus>;
export type LockedPicklistResponse = APIResponse<LockedPicklist>;
export type LockedPicklistListResponse = APIResponse<LockedPicklist[]>;
export type PicklistComparisonResponse = APIResponse<PicklistComparison>;
export type PicklistHistoryResponse = APIResponse<PicklistHistory>;

// Picklist Search and Filter
export interface PicklistSearchParams {
  team_number?: number;
  event_key?: string;
  year?: number;
  is_locked?: boolean;
  created_after?: string;
  created_before?: string;
}

export interface PicklistFilterOptions {
  sort_by?: "created_at" | "updated_at" | "team_number" | "event_key";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
  include_data?: boolean;
}

// Picklist Validation
export interface PicklistValidationResult {
  is_valid: boolean;
  errors: PicklistValidationError[];
  warnings: PicklistValidationWarning[];
  team_count: number;
  duplicate_teams: number[];
  missing_required_fields: string[];
  data_quality_score: number;
}

export interface PicklistValidationError {
  type: "duplicate_team" | "invalid_team_number" | "missing_data" | "invalid_rank";
  message: string;
  team_number?: number;
  field?: string;
}

export interface PicklistValidationWarning {
  type: "unusual_ranking" | "missing_analysis" | "low_confidence" | "data_age";
  message: string;
  team_number?: number;
  severity: "low" | "medium" | "high";
}

// Picklist Optimization
export interface PicklistOptimizationRequest {
  current_picklist: PicklistData;
  optimization_goals: Array<"maximize_synergy" | "minimize_risk" | "balance_roles" | "maximize_ceiling">;
  constraints?: {
    must_include_teams?: number[];
    must_exclude_teams?: number[];
    max_rank_change?: number;
    preserve_top_n?: number;
  };
}

export interface PicklistOptimizationResult {
  optimized_picklist: PicklistData;
  optimization_score: number;
  changes_made: Array<{
    team_number: number;
    old_rank: number;
    new_rank: number;
    reason: string;
  }>;
  recommendations: string[];
  trade_offs: string[];
}