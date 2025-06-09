// frontend/src/pages/PicklistNew/types.ts

// Core team interface used throughout picklist components
export interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
  is_fallback?: boolean;
  stats?: Record<string, number>;
  metrics_contribution?: Array<{
    id: string;
    value: number;
    weighted_value: number;
    metrics_used?: string[];
  }>;
  match_count?: number;
}

// Metric priority interface for ranking teams
export interface MetricPriority {
  id: string;
  weight: number;
  reason?: string;
}

// Analysis provided by GPT for picklist generation
export interface PicklistAnalysis {
  draft_reasoning: string;
  evaluation: string;
  final_recommendations: string;
}

// Batch processing information for large team datasets
export interface BatchProcessing {
  total_batches: number;
  current_batch: number;
  progress_percentage: number;
  processing_complete: boolean;
}

// Performance metrics for picklist generation
export interface Performance {
  total_time: number;
  team_count: number;
  avg_time_per_team: number;
  missing_teams?: number;
  duplicate_teams?: number;
  batch_count?: number;
  batch_size?: number;
  reference_teams_count?: number;
  reference_selection?: string;
}

// Complete result from picklist generation API
export interface PicklistResult {
  status: string;
  picklist: Team[];
  analysis: PicklistAnalysis;
  missing_team_numbers?: number[];
  performance?: Performance;
  message?: string;
  batched?: boolean;
  batch_processing?: BatchProcessing;
  cache_key?: string;
}

// Result from ranking missing teams specifically
export interface MissingTeamsResult {
  status: string;
  missing_team_rankings: Team[];
  performance?: Performance;
  message?: string;
}

// Available metric definitions
export interface Metric {
  id: string;
  label: string;
  category: string;
  importance_score?: number;
  win_correlation?: number;
  variability?: number;
}

// Weight assignment for metrics
export interface MetricWeight {
  id: string;
  weight: number;
  reason?: string;
}

// Parsed strategy from natural language input
export interface ParsedStrategy {
  interpretation: string;
  parsed_metrics: MetricWeight[];
}

// Pick position type
export type PickPosition = "first" | "second" | "third";

// Priority collections for all pick positions
export interface AllPriorities {
  first: MetricPriority[];
  second: MetricPriority[];
  third: MetricPriority[];
}

// Props for PicklistGenerator component
export interface PicklistGeneratorProps {
  datasetPath: string;
  yourTeamNumber: number;
  pickPosition: PickPosition;
  priorities: MetricPriority[];
  allPriorities?: AllPriorities;
  excludeTeams?: number[];
  onPicklistGenerated?: (result: PicklistResult) => void;
  initialPicklist?: Team[];
  onExcludeTeam?: (teamNumber: number) => void;
  isLocked?: boolean;
  onPicklistCleared?: () => void;
  useBatching?: boolean;
}

// Props for progress indicators
export interface ProgressIndicatorProps {
  estimatedTime: number;
  teamCount: number;
}

export interface BatchProgressIndicatorProps {
  batchInfo: BatchProcessing;
  elapsedTime: number;
}

// Props for missing teams modal
export interface MissingTeamsModalProps {
  missingTeamCount: number;
  onRankMissingTeams: () => void;
  onSkip: () => void;
  isLoading: boolean;
}

// Props for team comparison functionality
export interface TeamComparisonProps {
  selectedTeams: number[];
  datasetPath: string;
  yourTeamNumber: number;
  prioritiesMap: AllPriorities;
  onApply: (teams: Team[]) => void;
  onClose: () => void;
}

// Props for picklist display component
export interface PicklistDisplayProps {
  picklist: Team[];
  currentPage: number;
  teamsPerPage: number;
  totalPages: number;
  isEditing: boolean;
  isLocked: boolean;
  selectedTeams: number[];
  onPositionChange: (teamIndex: number, newPosition: number) => void;
  onToggleTeamSelection: (teamNumber: number) => void;
  onExcludeTeam?: (teamNumber: number) => void;
}

// Props for pagination component
export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  teamsPerPage: number;
  totalTeams: number;
  onPageChange: (page: number) => void;
  onTeamsPerPageChange: (teamsPerPage: number) => void;
}

// Props for picklist actions component
export interface PicklistActionsProps {
  isEditing: boolean;
  isLoading: boolean;
  isLocked: boolean;
  showAnalysis: boolean;
  hasPicklist: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onToggleAnalysis: () => void;
  onRegenerate: () => void;
  onClear: () => void;
}

// Props for analysis display component
export interface AnalysisDisplayProps {
  analysis: PicklistAnalysis;
  isVisible: boolean;
}

// State interfaces for hooks
export interface PicklistGenerationState {
  picklist: Team[];
  analysis: PicklistAnalysis | null;
  isLoading: boolean;
  estimatedTime: number;
  error: string | null;
  successMessage: string | null;
  missingTeamNumbers: number[];
  showMissingTeamsModal: boolean;
  isRankingMissingTeams: boolean;
}

export interface BatchProcessingState {
  batchProcessingActive: boolean;
  batchProcessingInfo: BatchProcessing | null;
  pollingCacheKey: string | null;
  elapsedTime: number;
}

export interface PaginationState {
  currentPage: number;
  teamsPerPage: number;
  totalPages: number;
}

export interface PicklistState {
  isEditing: boolean;
  showAnalysis: boolean;
  selectedTeams: number[];
  showComparison: boolean;
}

// Hook return types
export interface UsePicklistGeneration {
  state: PicklistGenerationState;
  batchState: BatchProcessingState;
  actions: {
    generatePicklist: () => Promise<void>;
    updatePicklist: () => Promise<void>;
    clearPicklist: () => Promise<void>;
    rankMissingTeams: () => Promise<void>;
    handleSkipMissingTeams: () => void;
  };
}

export interface UsePicklistState {
  state: PicklistState;
  actions: {
    setIsEditing: (editing: boolean) => void;
    setShowAnalysis: (show: boolean) => void;
    toggleTeamSelection: (teamNumber: number) => void;
    setShowComparison: (show: boolean) => void;
    clearSelection: () => void;
  };
}

export interface UsePagination {
  state: PaginationState;
  actions: {
    setCurrentPage: (page: number) => void;
    setTeamsPerPage: (teamsPerPage: number) => void;
    updateTotalPages: (totalTeams: number) => void;
    resetToFirstPage: () => void;
  };
}