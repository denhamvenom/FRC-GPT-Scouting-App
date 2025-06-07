// Alliance-related Types for FRC GPT Scouting App

import { APIResponse } from './api';
import { Team, TeamSelectionStatus } from './team';

// Core Alliance Interface
export interface Alliance {
  alliance_number: number;
  captain_team_number: number;
  first_pick_team_number: number;
  second_pick_team_number: number;
  backup_team_number?: number;
  is_complete: boolean;
  is_eliminated?: boolean;
  elimination_round?: number;
}

// Alliance Selection Event
export interface AllianceSelection {
  id: number;
  picklist_id?: number;
  event_key: string;
  year: number;
  is_completed: boolean;
  current_round: number;
  created_at: string;
  updated_at?: string;
  alliances: Alliance[];
  team_statuses: TeamSelectionStatus[];
  available_teams?: number[];
  eliminated_teams?: number[];
}

// Alliance Selection Configuration
export interface AllianceSelectionConfig {
  max_alliances: number;
  teams_per_alliance: number;
  allows_backup: boolean;
  allows_decline: boolean;
  selection_rounds: number;
  time_limit_per_pick?: number; // seconds
}

// Alliance Draft Rules
export interface AllianceDraftRules {
  can_pick_same_team_twice: boolean;
  can_decline_invitation: boolean;
  can_remove_team: boolean;
  backup_selection_allowed: boolean;
  captain_selection_automatic: boolean;
  pick_order_alternates: boolean;
}

// Alliance Selection State
export interface AllianceSelectionState {
  current_alliance: number;
  current_pick: "captain" | "first" | "second" | "backup";
  current_round: number;
  selection_phase: "captain_selection" | "first_picks" | "second_picks" | "backup_picks" | "completed";
  next_picking_alliance?: number;
  time_remaining?: number;
  is_paused: boolean;
}

// Alliance Performance
export interface AlliancePerformance {
  alliance_number: number;
  teams: Team[];
  combined_metrics: Record<string, number>;
  synergy_score: number;
  predicted_performance: number;
  strengths: string[];
  weaknesses: string[];
  strategy_recommendations: string[];
  complementarity_analysis: AllianceComplementarity;
}

// Alliance Complementarity Analysis
export interface AllianceComplementarity {
  alliance_number: number;
  captain_role: string;
  first_pick_role: string;
  second_pick_role: string;
  overlap_areas: string[];
  gap_areas: string[];
  overall_balance_score: number;
  risk_factors: string[];
}

// Alliance Selection Action Types
export type AllianceActionType = "captain" | "accept" | "decline" | "remove" | "backup";

export interface AllianceAction {
  action_type: AllianceActionType;
  team_number: number;
  alliance_number?: number;
  timestamp: string;
  performed_by?: string;
  notes?: string;
}

// Alliance Selection History
export interface AllianceSelectionHistory {
  selection_id: number;
  actions: AllianceAction[];
  snapshots: AllianceSelectionSnapshot[];
  timeline: AllianceTimelineEvent[];
}

export interface AllianceSelectionSnapshot {
  timestamp: string;
  alliances: Alliance[];
  team_statuses: TeamSelectionStatus[];
  current_state: AllianceSelectionState;
}

export interface AllianceTimelineEvent {
  timestamp: string;
  event_type: "team_selected" | "team_declined" | "team_removed" | "round_completed" | "selection_completed";
  description: string;
  team_number?: number;
  alliance_number?: number;
  metadata?: Record<string, any>;
}

// API Request Types
export interface CreateAllianceSelectionRequest {
  picklist_id?: number;
  event_key: string;
  year: number;
  team_list: number[];
  config?: Partial<AllianceSelectionConfig>;
}

export interface UpdateAllianceSelectionRequest {
  selection_id: number;
  alliances?: Alliance[];
  team_statuses?: TeamSelectionStatus[];
  current_round?: number;
  is_completed?: boolean;
}

export interface AllianceActionRequest {
  selection_id: number;
  team_number: number;
  action: AllianceActionType;
  alliance_number?: number;
  notes?: string;
}

export interface SimulateAllianceSelectionRequest {
  picklist_id: number;
  team_list: number[];
  strategy?: "optimal" | "conservative" | "aggressive";
  iterations?: number;
}

// API Response Types
export type AllianceSelectionResponse = APIResponse<AllianceSelection>;
export type AllianceSelectionListResponse = APIResponse<AllianceSelection[]>;
export type AlliancePerformanceResponse = APIResponse<AlliancePerformance[]>;
export type AllianceActionResponse = APIResponse<{ success: boolean; updated_selection: AllianceSelection }>;
export type AllianceSimulationResponse = APIResponse<{
  simulations: AllianceSimulationResult[];
  best_strategy: string;
  confidence_score: number;
}>;

// Alliance Simulation Results
export interface AllianceSimulationResult {
  iteration: number;
  final_alliances: Alliance[];
  your_team_alliance?: number;
  predicted_ranking: number;
  success_probability: number;
  strategy_used: string;
}

// Alliance Statistics
export interface AllianceStatistics {
  alliance_number: number;
  total_matches: number;
  wins: number;
  losses: number;
  win_percentage: number;
  average_score: number;
  average_margin: number;
  elimination_performance?: {
    rounds_advanced: number;
    final_placement: string;
    matches_played: number;
    matches_won: number;
  };
}

// Alliance Strategy
export interface AllianceStrategy {
  alliance_number: number;
  primary_strategy: string;
  backup_strategies: string[];
  role_assignments: {
    captain_role: string;
    first_pick_role: string;
    second_pick_role: string;
  };
  game_plan: {
    auto_strategy: string;
    teleop_strategy: string;
    endgame_strategy: string;
  };
  contingency_plans: string[];
}

// Alliance Draft Prediction
export interface AllianceDraftPrediction {
  predicted_picks: Array<{
    alliance_number: number;
    pick_type: "captain" | "first" | "second";
    team_number: number;
    confidence: number;
    reasoning: string;
  }>;
  your_team_scenarios: Array<{
    scenario: string;
    probability: number;
    expected_alliance: number;
    expected_pick_position: "captain" | "first" | "second";
  }>;
  recommendations: string[];
}