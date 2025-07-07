export interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
  is_fallback?: boolean;
}

export interface MetricPriority {
  id: string;
  weight: number;
  reason?: string;
}

export interface PicklistAnalysis {
  draft_reasoning: string;
  evaluation: string;
  final_recommendations: string;
}

export interface BatchProcessing {
  total_batches: number;
  current_batch: number;
  progress_percentage: number;
  processing_complete: boolean;
}

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

export interface MissingTeamsResult {
  status: string;
  missing_team_rankings: Team[];
  performance?: Performance;
  message?: string;
}

export interface PicklistGeneratorProps {
  datasetPath: string;
  yourTeamNumber: number;
  pickPosition: "first" | "second" | "third";
  priorities: MetricPriority[];
  allPriorities?: {
    first: MetricPriority[];
    second: MetricPriority[];
    third: MetricPriority[];
  };
  excludeTeams?: number[];
  strategyInterpretation?: string;
  onPicklistGenerated?: (result: PicklistResult) => void;
  initialPicklist?: Team[];
  onExcludeTeam?: (teamNumber: number) => void;
  isLocked?: boolean;
  onPicklistCleared?: () => void;
}