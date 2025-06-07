// Team-related Types for FRC GPT Scouting App

import { APIResponse } from './api';

// Core Team Interface
export interface Team {
  team_number: number;
  nickname?: string;
  rank?: number;
  metrics?: Record<string, number>;
  analysis?: string;
  reason?: string;
  location?: string;
  rookie_year?: number;
  website?: string;
  [key: string]: any;
}

// Team Selection Status for Alliance Selection
export interface TeamSelectionStatus {
  team_number: number;
  is_captain: boolean;
  is_picked: boolean;
  has_declined: boolean;
  round_eliminated?: number;
  alliance_number?: number;
  pick_order?: number;
}

// User Ranking for Picklist Updates
export interface UserRanking {
  team_number: number;
  position: number;
  nickname?: string;
  custom_rank?: number;
}

// Team Action Request for Alliance Selection
export interface TeamActionRequest {
  selection_id: number;
  team_number: number;
  action: "captain" | "accept" | "decline" | "remove";
  alliance_number?: number;
}

// Team Comparison Types
export interface CompareTeamsRequest {
  unified_dataset_path: string;
  team_numbers: number[];
  your_team_number: number;
  pick_position: "first" | "second" | "third";
  priorities: MetricPriority[];
  question?: string;
  chat_history?: ChatMessage[];
}

export interface TeamComparisonResponse {
  status: "success" | "error";
  comparison?: string;
  rankings?: Record<number, number>;
  analysis?: Record<string, any>;
  team_summaries?: Record<number, TeamSummary>;
}

export interface TeamSummary {
  team_number: number;
  nickname?: string;
  key_strengths: string[];
  key_weaknesses: string[];
  overall_rating: number;
  compatibility_score?: number;
  risk_factors?: string[];
}

// Metric Priority for Team Analysis
export interface MetricPriority {
  id: string;
  weight: number; // 0.5 to 3.0
  reason?: string;
  category?: "auto" | "teleop" | "endgame" | "strategy" | "universal" | "pit";
}

// Chat Message for Team Comparison
export interface ChatMessage {
  type: "question" | "answer";
  content: string;
  timestamp: string;
  team_numbers?: number[];
}

// Team Statistics
export interface TeamStatistics {
  team_number: number;
  matches_played: number;
  wins: number;
  losses: number;
  ties: number;
  win_percentage: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  ranking_points: number;
  qual_rank?: number;
  record?: {
    wins: number;
    losses: number;
    ties: number;
  };
}

// Team Performance Metrics
export interface TeamPerformanceMetrics {
  team_number: number;
  auto_metrics: Record<string, number>;
  teleop_metrics: Record<string, number>;
  endgame_metrics: Record<string, number>;
  overall_metrics: Record<string, number>;
  consistency_score: number;
  reliability_score: number;
  improvement_trend: "improving" | "declining" | "stable";
}

// Team Match Data
export interface TeamMatchData {
  team_number: number;
  match_number: number;
  alliance_color: "red" | "blue";
  alliance_position: 1 | 2 | 3;
  score: number;
  ranking_points: number;
  auto_data: Record<string, any>;
  teleop_data: Record<string, any>;
  endgame_data: Record<string, any>;
  fouls: number;
  tech_fouls: number;
  yellow_cards: number;
  red_cards: number;
  disqualified: boolean;
}

// Team Availability Status
export interface TeamAvailabilityStatus {
  team_number: number;
  is_available: boolean;
  is_eliminated: boolean;
  elimination_round?: number;
  status: "available" | "picked" | "declined" | "eliminated" | "unavailable";
  notes?: string;
}

// API Response Types for Team-related endpoints
export type TeamListResponse = APIResponse<Team[]>;
export type TeamResponse = APIResponse<Team>;
export type TeamComparisonApiResponse = APIResponse<TeamComparisonResponse>;
export type TeamStatisticsResponse = APIResponse<TeamStatistics>;
export type TeamPerformanceResponse = APIResponse<TeamPerformanceMetrics>;
export type TeamActionResponse = APIResponse<{ success: boolean; message?: string }>;

// Team Search and Filter Types
export interface TeamSearchParams {
  team_numbers?: number[];
  region?: string;
  rookie_year_min?: number;
  rookie_year_max?: number;
  has_nickname?: boolean;
  search_query?: string;
}

export interface TeamFilterOptions {
  sort_by?: "team_number" | "nickname" | "rank" | "performance";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
  include_inactive?: boolean;
}

// Team Event Participation
export interface TeamEventParticipation {
  team_number: number;
  event_key: string;
  year: number;
  rank?: number;
  record?: {
    wins: number;
    losses: number;
    ties: number;
  };
  alliance_selection_status?: "captain" | "picked" | "available" | "backup";
  elimination_result?: "winner" | "finalist" | "semifinalist" | "quarterfinalist" | "eliminated";
}