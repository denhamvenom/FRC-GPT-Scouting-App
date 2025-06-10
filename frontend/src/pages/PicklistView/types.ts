// frontend/src/pages/PicklistView/types.ts

export interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
}

export interface MetricPriority {
  id: string;
  weight: number;
  reason?: string;
}

export interface Metric {
  id: string;
  label: string;
  category: string;
}

export interface LockedPicklist {
  id: number;
  position: string;
  team_number: number | null;
  excluded_teams: number[];
  strategy_prompt: string;
  priority_metrics: MetricPriority[];
  created_at: string;
  picklist: Team[];
}

export interface AllianceSelection {
  id: number;
  event_key: string;
  current_round: number;
  current_pick: number;
  is_active: boolean;
}

export type PickPosition = 'first' | 'second' | 'third';

export interface PicklistViewState {
  // Dataset
  datasetPath: string;
  yourTeamNumber: number;
  
  // UI state
  activeTab: PickPosition;
  isLoading: boolean;
  error: string | null;
  successMessage: string | null;
  isLocking: boolean;
  
  // Metrics
  universalMetrics: Metric[];
  gameMetrics: Metric[];
  
  // Priorities for each position
  firstPickPriorities: MetricPriority[];
  secondPickPriorities: MetricPriority[];
  thirdPickPriorities: MetricPriority[];
  
  // Generated picklists
  firstPicklist: Team[];
  secondPicklist: Team[];
  thirdPicklist: Team[];
  
  // Excluded teams
  excludedTeams: number[];
  
  // Existing data
  picklists: LockedPicklist[];
  hasLockedPicklist: boolean;
  activeAllianceSelection: number | null;
}

export interface PicklistViewActions {
  setDatasetPath: (path: string) => void;
  setYourTeamNumber: (teamNumber: number) => void;
  setActiveTab: (tab: PickPosition) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSuccessMessage: (message: string | null) => void;
  setIsLocking: (locking: boolean) => void;
  
  setUniversalMetrics: (metrics: Metric[]) => void;
  setGameMetrics: (metrics: Metric[]) => void;
  
  setFirstPickPriorities: (priorities: MetricPriority[]) => void;
  setSecondPickPriorities: (priorities: MetricPriority[]) => void;
  setThirdPickPriorities: (priorities: MetricPriority[]) => void;
  
  setFirstPicklist: (teams: Team[]) => void;
  setSecondPicklist: (teams: Team[]) => void;
  setThirdPicklist: (teams: Team[]) => void;
  
  setExcludedTeams: (teams: number[]) => void;
  setPicklists: (picklists: LockedPicklist[]) => void;
  setHasLockedPicklist: (hasLocked: boolean) => void;
  setActiveAllianceSelection: (selection: number | null) => void;
  
  // Actions
  checkDatasetStatus: () => Promise<void>;
  fetchMetrics: (path: string) => Promise<void>;
  fetchLockedPicklists: () => Promise<void>;
  handleAddMetric: (metric: Metric) => void;
  handleRemovePriority: (metricId: string) => void;
  handleWeightChange: (metricId: string, weight: number) => void;
  generatePicklist: () => Promise<void>;
  lockPicklist: () => Promise<void>;
  unlockPicklist: () => Promise<void>;
}