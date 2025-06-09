/**
 * Type definitions for Alliance Selection components
 */

export interface Team {
  team_number: number;
  nickname: string;
  score?: number;
  reasoning?: string;
}

export interface Alliance {
  alliance_number: number;
  captain_team_number: number;
  first_pick_team_number: number;
  second_pick_team_number: number;
  backup_team_number?: number;
}

export interface TeamStatus {
  team_number: number;
  is_captain: boolean;
  is_picked: boolean;
  has_declined: boolean;
  round_eliminated?: number;
}

export interface SelectionState {
  id: number;
  event_key: string;
  year: number;
  is_completed: boolean;
  current_round: number;
  picklist_id?: number;
  alliances: Alliance[];
  team_statuses: TeamStatus[];
}

export interface LockedPicklist {
  id: number;
  team_number: number;
  event_key: string;
  year: number;
  first_pick_data: { teams: Team[] };
  second_pick_data: { teams: Team[] };
  third_pick_data?: { teams: Team[] };
  created_at?: string;
}

export interface TeamRankInfo {
  team_number: number;
  rank: number;
}

export type TeamAction = 'captain' | 'accept' | 'decline' | 'remove';

export interface TeamActionRequest {
  selection_id: number;
  team_number: number;
  action: TeamAction;
  alliance_number?: number;
}

export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  message?: string;
  detail?: string;
  [key: string]: any;
}

export interface PicklistsResponse extends ApiResponse {
  picklists: LockedPicklist[];
}

export interface SelectionResponse extends ApiResponse {
  selection: SelectionState;
}

export interface PicklistResponse extends ApiResponse {
  picklist: LockedPicklist;
}

export interface CreateSelectionRequest {
  picklist_id?: number | null;
  event_key: string;
  year: number;
  team_list: number[];
}

export interface CreateSelectionResponse extends ApiResponse {
  id: number;
}

// Component prop types
export interface AllianceSelectionProps {
  selectionId?: string;
}

export interface TeamGridProps {
  teams: number[][];
  selectedTeam: number | null;
  onTeamSelect: (teamNumber: number | null) => void;
  selection: SelectionState | null;
  picklist: LockedPicklist | null;
  getTeamNickname: (teamNumber: number) => string;
  getTeamRank: (teamNumber: number, roundNumber?: number) => number;
}

export interface AllianceBoardProps {
  selection: SelectionState | null;
  selectedAlliance: number | null;
  onAllianceSelect: (allianceNumber: number | null) => void;
  onRemoveTeam: (teamNumber: number, allianceNumber: number) => void;
}

export interface TeamActionPanelProps {
  selectedTeam: number | null;
  selectedAlliance: number | null;
  action: TeamAction | null;
  selection: SelectionState | null;
  picklist: LockedPicklist | null;
  onActionSelect: (action: TeamAction | null) => void;
  onAllianceSelect: (allianceNumber: number | null) => void;
  onConfirmAction: () => void;
  getTeamNickname: (teamNumber: number) => string;
  canBeCaptain: (teamNumber: number) => boolean;
  isTeamSelectable: (teamNumber: number) => boolean;
}

export interface ProgressIndicatorProps {
  loading: boolean;
  error: string | null;
  successMessage: string | null;
}

export interface TeamStatusIndicatorProps {
  teamNumber: number;
  teamStatus?: TeamStatus;
  isSelected: boolean;
  picklist: LockedPicklist | null;
  currentRound: number;
  getTeamRank: (teamNumber: number, roundNumber?: number) => number;
}

// Hook types
export interface UseAllianceSelectionReturn {
  // State
  loading: boolean;
  error: string | null;
  successMessage: string | null;
  picklist: LockedPicklist | null;
  selection: SelectionState | null;
  teamList: number[];
  
  // Actions
  loadPicklists: () => Promise<void>;
  loadSelectionData: (id: number) => Promise<void>;
  createNewSelection: () => Promise<void>;
  clearError: () => void;
  clearSuccessMessage: () => void;
}

export interface UseTeamActionsReturn {
  // State
  selectedTeam: number | null;
  selectedAlliance: number | null;
  action: TeamAction | null;
  
  // Actions
  setSelectedTeam: (teamNumber: number | null) => void;
  setSelectedAlliance: (allianceNumber: number | null) => void;
  setAction: (action: TeamAction | null) => void;
  performTeamAction: (action: TeamAction) => Promise<void>;
  handleRemoveTeam: (teamNumber: number, allianceNumber: number) => Promise<void>;
  clearSelections: () => void;
  
  // Validation
  canBeCaptain: (teamNumber: number) => boolean;
  isTeamSelectable: (teamNumber: number) => boolean;
}

export interface UseAllianceStateReturn {
  advanceToNextRound: () => Promise<void>;
  resetAllianceSelection: () => Promise<void>;
}

export interface UsePollingReturn {
  isPolling: boolean;
  startPolling: (interval?: number) => void;
  stopPolling: () => void;
}