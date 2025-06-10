// frontend/src/pages/Validation/types.ts

export interface TeamMatch {
  team_number: number;
  match_number: number;
}

export interface ValidationIssue {
  team_number: number;
  match_number: number;
  issues: Array<{
    metric: string;
    value: number;
    detection_method: string;
    z_score?: number;
    bounds?: [number, number];
    team_z_score?: number;
  }>;
}

export interface IgnoredMatch {
  team_number: number;
  match_number: number;
  reason_category: string;
  reason: string;
  timestamp: string;
}

export interface TodoItem {
  team_number: number;
  match_number: number;
  added_timestamp: string;
  updated_timestamp?: string;
  status: 'pending' | 'completed' | 'cancelled';
}

export interface ValidationResult {
  missing_scouting: TeamMatch[];
  missing_superscouting: { team_number: number }[];
  ignored_matches: IgnoredMatch[];
  outliers: ValidationIssue[];
  status: string;
  summary: {
    total_missing_matches: number;
    total_missing_superscouting: number;
    total_outliers: number;
    total_ignored_matches: number;
    has_issues: boolean;
  };
}

export interface CorrectionSuggestion {
  metric: string;
  current_value: number;
  suggested_corrections: Array<{
    value: number;
    method: string;
  }>;
}

export type TabType = 'missing' | 'outliers' | 'todo';

export type ActionMode = 'none' | 'watch-video' | 'virtual-scout' | 'ignore-match';

export type IgnoreReason = 'not_operational' | 'not_present' | 'other';

export interface ValidationState {
  datasetPath: string;
  validationResult: ValidationResult | null;
  loading: boolean;
  activeTab: TabType;
  selectedIssue: TeamMatch | ValidationIssue | null;
  suggestions: CorrectionSuggestion[];
  corrections: { [key: string]: number };
  correctionReason: string;
  error: string | null;
  successMessage: string | null;
  todoList: TodoItem[];
  virtualScoutPreview: any;
  actionMode: ActionMode;
  ignoreReason: IgnoreReason;
  customReason: string;
}

export interface ValidationActions {
  setDatasetPath: (path: string) => void;
  setValidationResult: (result: ValidationResult | null) => void;
  setLoading: (loading: boolean) => void;
  setActiveTab: (tab: TabType) => void;
  setSelectedIssue: (issue: TeamMatch | ValidationIssue | null) => void;
  setSuggestions: (suggestions: CorrectionSuggestion[]) => void;
  setCorrections: (corrections: { [key: string]: number }) => void;
  setCorrectionReason: (reason: string) => void;
  setError: (error: string | null) => void;
  setSuccessMessage: (message: string | null) => void;
  setTodoList: (list: TodoItem[]) => void;
  setVirtualScoutPreview: (preview: any) => void;
  setActionMode: (mode: ActionMode) => void;
  setIgnoreReason: (reason: IgnoreReason) => void;
  setCustomReason: (reason: string) => void;
  fetchValidationData: (path: string) => Promise<void>;
  fetchTodoList: (path: string) => Promise<void>;
  fetchVirtualScoutPreview: () => Promise<void>;
  handleActionModeChange: (mode: ActionMode) => void;
  submitCorrection: () => Promise<void>;
  submitIgnoreMatch: () => Promise<void>;
  submitVirtualScout: () => Promise<void>;
}