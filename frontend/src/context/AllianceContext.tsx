import React, { createContext, useContext, useReducer, useEffect, ReactNode, useCallback } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { AllianceService } from '../services/AllianceService';
import { useAppContext } from './AppContext';

// Types for alliance selection state
export interface AllianceState {
  // Current selection state
  currentRound: number;
  currentAlliance: number;
  currentPick: number;
  selectionActive: boolean;
  
  // Alliance data
  alliances: Alliance[];
  availableTeams: Team[];
  selectedTeams: SelectedTeam[];
  
  // UI state
  selectedTeamNumber: string | null;
  actionMode: ActionMode;
  isLoading: boolean;
  error: string | null;
  
  // Settings
  autoAdvance: boolean;
  showTeamDetails: boolean;
  compactView: boolean;
}

export interface Alliance {
  id: number;
  captain: Team | null;
  firstPick: Team | null;
  secondPick: Team | null;
  isComplete: boolean;
}

export interface Team {
  number: string;
  nickname: string;
  location: string;
  rookieYear: number;
  epa?: number;
  rank?: number;
}

export interface SelectedTeam {
  teamNumber: string;
  allianceId: number;
  pickOrder: number;
  status: 'captain' | 'picked' | 'declined';
  timestamp: string;
}

export type ActionMode = 'select' | 'captain' | 'accept' | 'decline' | 'remove' | null;

// Action types for alliance state updates
export type AllianceAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SELECTION_STATE'; payload: { round: number; alliance: number; pick: number; active: boolean } }
  | { type: 'SET_ALLIANCES'; payload: Alliance[] }
  | { type: 'SET_AVAILABLE_TEAMS'; payload: Team[] }
  | { type: 'SET_SELECTED_TEAMS'; payload: SelectedTeam[] }
  | { type: 'SELECT_TEAM'; payload: string | null }
  | { type: 'SET_ACTION_MODE'; payload: ActionMode }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<{ autoAdvance: boolean; showTeamDetails: boolean; compactView: boolean }> }
  | { type: 'TEAM_ACTION_SUCCESS'; payload: { teamNumber: string; action: string; allianceId?: number } }
  | { type: 'ADVANCE_SELECTION' }
  | { type: 'RESET_SELECTION' }
  | { type: 'RESET_STATE' };

// Initial state
const initialState: AllianceState = {
  currentRound: 1,
  currentAlliance: 1,
  currentPick: 1,
  selectionActive: false,
  alliances: Array.from({ length: 8 }, (_, i) => ({
    id: i + 1,
    captain: null,
    firstPick: null,
    secondPick: null,
    isComplete: false,
  })),
  availableTeams: [],
  selectedTeams: [],
  selectedTeamNumber: null,
  actionMode: null,
  isLoading: false,
  error: null,
  autoAdvance: true,
  showTeamDetails: true,
  compactView: false,
};

// Reducer for alliance state management
function allianceReducer(state: AllianceState, action: AllianceAction): AllianceState {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
        error: action.payload ? null : state.error, // Clear error when starting loading
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
    
    case 'SET_SELECTION_STATE':
      return {
        ...state,
        currentRound: action.payload.round,
        currentAlliance: action.payload.alliance,
        currentPick: action.payload.pick,
        selectionActive: action.payload.active,
      };
    
    case 'SET_ALLIANCES':
      return {
        ...state,
        alliances: action.payload,
      };
    
    case 'SET_AVAILABLE_TEAMS':
      return {
        ...state,
        availableTeams: action.payload,
      };
    
    case 'SET_SELECTED_TEAMS':
      return {
        ...state,
        selectedTeams: action.payload,
      };
    
    case 'SELECT_TEAM':
      return {
        ...state,
        selectedTeamNumber: action.payload,
        actionMode: action.payload ? 'select' : null,
      };
    
    case 'SET_ACTION_MODE':
      return {
        ...state,
        actionMode: action.payload,
      };
    
    case 'UPDATE_SETTINGS':
      return {
        ...state,
        ...action.payload,
      };
    
    case 'TEAM_ACTION_SUCCESS': {
      const { teamNumber, action: actionType, allianceId } = action.payload;
      
      // Update selected teams list
      let updatedSelectedTeams = [...state.selectedTeams];
      
      if (actionType === 'captain' || actionType === 'accept') {
        const existingIndex = updatedSelectedTeams.findIndex(t => t.teamNumber === teamNumber);
        const newTeam: SelectedTeam = {
          teamNumber,
          allianceId: allianceId || state.currentAlliance,
          pickOrder: actionType === 'captain' ? 0 : state.currentPick,
          status: actionType === 'captain' ? 'captain' : 'picked',
          timestamp: new Date().toISOString(),
        };
        
        if (existingIndex >= 0) {
          updatedSelectedTeams[existingIndex] = newTeam;
        } else {
          updatedSelectedTeams.push(newTeam);
        }
      } else if (actionType === 'remove') {
        updatedSelectedTeams = updatedSelectedTeams.filter(t => t.teamNumber !== teamNumber);
      }
      
      // Remove from available teams if selected
      const updatedAvailableTeams = state.availableTeams.filter(t => t.number !== teamNumber);
      
      return {
        ...state,
        selectedTeams: updatedSelectedTeams,
        availableTeams: actionType === 'decline' ? state.availableTeams : updatedAvailableTeams,
        selectedTeamNumber: null,
        actionMode: null,
      };
    }
    
    case 'ADVANCE_SELECTION': {
      let { currentRound, currentAlliance, currentPick } = state;
      
      // Alliance selection advancement logic
      if (currentRound === 1) {
        // Round 1: Captain selection (1-8)
        if (currentAlliance < 8) {
          currentAlliance++;
        } else {
          currentRound = 2;
          currentAlliance = 8; // Start from alliance 8 in round 2
          currentPick = 1;
        }
      } else if (currentRound === 2) {
        // Round 2: First picks (8-1)
        if (currentAlliance > 1) {
          currentAlliance--;
        } else {
          currentRound = 3;
          currentAlliance = 1; // Start from alliance 1 in round 3
          currentPick = 2;
        }
      } else if (currentRound === 3) {
        // Round 3: Second picks (1-8)
        if (currentAlliance < 8) {
          currentAlliance++;
        } else {
          // Selection complete
          return {
            ...state,
            selectionActive: false,
          };
        }
      }
      
      return {
        ...state,
        currentRound,
        currentAlliance,
        currentPick,
      };
    }
    
    case 'RESET_SELECTION':
      return {
        ...state,
        currentRound: 1,
        currentAlliance: 1,
        currentPick: 1,
        selectionActive: false,
        selectedTeams: [],
        alliances: initialState.alliances,
        selectedTeamNumber: null,
        actionMode: null,
      };
    
    case 'RESET_STATE':
      return {
        ...initialState,
        autoAdvance: state.autoAdvance,
        showTeamDetails: state.showTeamDetails,
        compactView: state.compactView,
      };
    
    default:
      return state;
  }
}

// Context creation
export interface AllianceContextType {
  state: AllianceState;
  dispatch: React.Dispatch<AllianceAction>;
  
  // Alliance management
  startSelection: () => Promise<void>;
  resetSelection: () => Promise<void>;
  loadSelectionState: () => Promise<void>;
  
  // Team actions
  selectTeam: (teamNumber: string) => void;
  makeTeamCaptain: (teamNumber: string, allianceId: number) => Promise<void>;
  acceptTeam: (teamNumber: string) => Promise<void>;
  declineTeam: (teamNumber: string, reason?: string) => Promise<void>;
  removeTeam: (teamNumber: string) => Promise<void>;
  
  // Navigation
  advanceSelection: () => void;
  goToRound: (round: number, alliance: number) => void;
  
  // Utilities
  getCurrentAlliance: () => Alliance | null;
  getTeamStatus: (teamNumber: string) => 'available' | 'selected' | 'captain' | 'declined' | null;
  canPerformAction: (action: ActionMode, teamNumber?: string) => boolean;
  isSelectionComplete: () => boolean;
}

const AllianceContext = createContext<AllianceContextType | undefined>(undefined);

// Provider component
export interface AllianceProviderProps {
  children: ReactNode;
}

export function AllianceProvider({ children }: AllianceProviderProps) {
  const [state, dispatch] = useReducer(allianceReducer, initialState);
  const { state: appState, showNotification } = useAppContext();
  
  // Persist alliance settings
  const [, setStoredSettings] = useLocalStorage('allianceSettings', {
    autoAdvance: state.autoAdvance,
    showTeamDetails: state.showTeamDetails,
    compactView: state.compactView,
  });
  
  // Load persisted settings on mount
  const [storedSettings] = useLocalStorage('allianceSettings', {
    autoAdvance: true,
    showTeamDetails: true,
    compactView: false,
  });
  
  useEffect(() => {
    dispatch({ type: 'UPDATE_SETTINGS', payload: storedSettings });
  }, [storedSettings]);
  
  // Update stored settings when state changes
  useEffect(() => {
    setStoredSettings({
      autoAdvance: state.autoAdvance,
      showTeamDetails: state.showTeamDetails,
      compactView: state.compactView,
    });
  }, [state.autoAdvance, state.showTeamDetails, state.compactView, setStoredSettings]);
  
  // Alliance management functions
  const startSelection = useCallback(async () => {
    if (!appState.currentEventKey) {
      showNotification({
        type: 'error',
        title: 'No Event Selected',
        message: 'Please select an event before starting alliance selection.',
      });
      return;
    }
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await AllianceService.startSelection(appState.currentEventKey);
      
      dispatch({
        type: 'SET_SELECTION_STATE',
        payload: {
          round: 1,
          alliance: 1,
          pick: 1,
          active: true,
        },
      });
      
      // Load available teams
      await loadSelectionState();
      
      showNotification({
        type: 'success',
        title: 'Alliance Selection Started',
        message: 'Alliance selection has begun. Select team captains first.',
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to start selection' });
      showNotification({
        type: 'error',
        title: 'Selection Start Failed',
        message: error instanceof Error ? error.message : 'Failed to start alliance selection',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, showNotification]);
  
  const resetSelection = useCallback(async () => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await AllianceService.resetSelection(appState.currentEventKey);
      dispatch({ type: 'RESET_SELECTION' });
      
      showNotification({
        type: 'info',
        title: 'Selection Reset',
        message: 'Alliance selection has been reset.',
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to reset selection' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, showNotification]);
  
  const loadSelectionState = useCallback(async () => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const [statusResponse, teamsResponse] = await Promise.all([
        AllianceService.getSelectionStatus(appState.currentEventKey),
        AllianceService.getAvailableTeams(appState.currentEventKey),
      ]);
      
      dispatch({ type: 'SET_ALLIANCES', payload: statusResponse.alliances || [] });
      dispatch({ type: 'SET_SELECTED_TEAMS', payload: statusResponse.selectedTeams || [] });
      dispatch({ type: 'SET_AVAILABLE_TEAMS', payload: teamsResponse.teams || [] });
      
      if (statusResponse.currentState) {
        dispatch({
          type: 'SET_SELECTION_STATE',
          payload: {
            round: statusResponse.currentState.round || 1,
            alliance: statusResponse.currentState.alliance || 1,
            pick: statusResponse.currentState.pick || 1,
            active: statusResponse.currentState.active || false,
          },
        });
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to load selection state' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey]);
  
  // Team action functions
  const selectTeam = useCallback((teamNumber: string) => {
    dispatch({ type: 'SELECT_TEAM', payload: teamNumber });
  }, []);
  
  const makeTeamCaptain = useCallback(async (teamNumber: string, allianceId: number) => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await AllianceService.performTeamAction(appState.currentEventKey, {
        teamNumber,
        action: 'captain',
        allianceId,
      });
      
      dispatch({
        type: 'TEAM_ACTION_SUCCESS',
        payload: { teamNumber, action: 'captain', allianceId },
      });
      
      if (state.autoAdvance) {
        dispatch({ type: 'ADVANCE_SELECTION' });
      }
      
      showNotification({
        type: 'success',
        title: 'Captain Selected',
        message: `Team ${teamNumber} is now captain of Alliance ${allianceId}`,
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to make team captain' });
      showNotification({
        type: 'error',
        title: 'Captain Selection Failed',
        message: error instanceof Error ? error.message : 'Failed to make team captain',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, state.autoAdvance, showNotification]);
  
  const acceptTeam = useCallback(async (teamNumber: string) => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await AllianceService.performTeamAction(appState.currentEventKey, {
        teamNumber,
        action: 'accept',
      });
      
      dispatch({
        type: 'TEAM_ACTION_SUCCESS',
        payload: { teamNumber, action: 'accept' },
      });
      
      if (state.autoAdvance) {
        dispatch({ type: 'ADVANCE_SELECTION' });
      }
      
      showNotification({
        type: 'success',
        title: 'Team Accepted',
        message: `Team ${teamNumber} has been added to the alliance`,
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to accept team' });
      showNotification({
        type: 'error',
        title: 'Team Accept Failed',
        message: error instanceof Error ? error.message : 'Failed to accept team',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, state.autoAdvance, showNotification]);
  
  const declineTeam = useCallback(async (teamNumber: string, reason?: string) => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await AllianceService.performTeamAction(appState.currentEventKey, {
        teamNumber,
        action: 'decline',
        reason,
      });
      
      dispatch({
        type: 'TEAM_ACTION_SUCCESS',
        payload: { teamNumber, action: 'decline' },
      });
      
      if (state.autoAdvance) {
        dispatch({ type: 'ADVANCE_SELECTION' });
      }
      
      showNotification({
        type: 'info',
        title: 'Team Declined',
        message: `Team ${teamNumber} has declined the invitation`,
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to decline team' });
      showNotification({
        type: 'error',
        title: 'Team Decline Failed',
        message: error instanceof Error ? error.message : 'Failed to decline team',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, state.autoAdvance, showNotification]);
  
  const removeTeam = useCallback(async (teamNumber: string) => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await AllianceService.performTeamAction(appState.currentEventKey, {
        teamNumber,
        action: 'remove',
      });
      
      dispatch({
        type: 'TEAM_ACTION_SUCCESS',
        payload: { teamNumber, action: 'remove' },
      });
      
      showNotification({
        type: 'info',
        title: 'Team Removed',
        message: `Team ${teamNumber} has been removed from the alliance`,
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to remove team' });
      showNotification({
        type: 'error',
        title: 'Team Remove Failed',
        message: error instanceof Error ? error.message : 'Failed to remove team',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, showNotification]);
  
  // Navigation functions
  const advanceSelection = useCallback(() => {
    dispatch({ type: 'ADVANCE_SELECTION' });
  }, []);
  
  const goToRound = useCallback((round: number, alliance: number) => {
    dispatch({
      type: 'SET_SELECTION_STATE',
      payload: {
        round,
        alliance,
        pick: round === 1 ? 1 : round - 1,
        active: state.selectionActive,
      },
    });
  }, [state.selectionActive]);
  
  // Utility functions
  const getCurrentAlliance = useCallback((): Alliance | null => {
    return state.alliances.find(a => a.id === state.currentAlliance) || null;
  }, [state.alliances, state.currentAlliance]);
  
  const getTeamStatus = useCallback((teamNumber: string): 'available' | 'selected' | 'captain' | 'declined' | null => {
    const selectedTeam = state.selectedTeams.find(t => t.teamNumber === teamNumber);
    if (selectedTeam) {
      return selectedTeam.status;
    }
    
    const isAvailable = state.availableTeams.some(t => t.number === teamNumber);
    return isAvailable ? 'available' : null;
  }, [state.selectedTeams, state.availableTeams]);
  
  const canPerformAction = useCallback((action: ActionMode, teamNumber?: string): boolean => {
    if (!state.selectionActive || state.isLoading) return false;
    
    switch (action) {
      case 'captain':
        return state.currentRound === 1 && teamNumber ? getTeamStatus(teamNumber) === 'available' : false;
      case 'accept':
        return state.currentRound > 1 && teamNumber ? getTeamStatus(teamNumber) === 'available' : false;
      case 'decline':
        return teamNumber ? getTeamStatus(teamNumber) === 'available' : false;
      case 'remove':
        return teamNumber ? ['selected', 'captain'].includes(getTeamStatus(teamNumber) || '') : false;
      default:
        return false;
    }
  }, [state.selectionActive, state.isLoading, state.currentRound, getTeamStatus]);
  
  const isSelectionComplete = useCallback((): boolean => {
    return state.alliances.every(alliance => alliance.isComplete);
  }, [state.alliances]);
  
  const contextValue: AllianceContextType = {
    state,
    dispatch,
    startSelection,
    resetSelection,
    loadSelectionState,
    selectTeam,
    makeTeamCaptain,
    acceptTeam,
    declineTeam,
    removeTeam,
    advanceSelection,
    goToRound,
    getCurrentAlliance,
    getTeamStatus,
    canPerformAction,
    isSelectionComplete,
  };
  
  return (
    <AllianceContext.Provider value={contextValue}>
      {children}
    </AllianceContext.Provider>
  );
}

// Hook to use the AllianceContext
export function useAllianceContext() {
  const context = useContext(AllianceContext);
  if (context === undefined) {
    throw new Error('useAllianceContext must be used within an AllianceProvider');
  }
  return context;
}

// Additional hooks for specific alliance functionality
export function useCurrentSelection() {
  const { state, getCurrentAlliance } = useAllianceContext();
  return {
    currentRound: state.currentRound,
    currentAlliance: state.currentAlliance,
    currentPick: state.currentPick,
    alliance: getCurrentAlliance(),
    isActive: state.selectionActive,
  };
}

export function useTeamActions() {
  const {
    selectTeam,
    makeTeamCaptain,
    acceptTeam,
    declineTeam,
    removeTeam,
    canPerformAction,
    getTeamStatus,
  } = useAllianceContext();
  
  return {
    selectTeam,
    makeTeamCaptain,
    acceptTeam,
    declineTeam,
    removeTeam,
    canPerformAction,
    getTeamStatus,
  };
}

export function useAllianceSettings() {
  const { state, dispatch } = useAllianceContext();
  
  const updateSettings = useCallback((settings: Partial<{ autoAdvance: boolean; showTeamDetails: boolean; compactView: boolean }>) => {
    dispatch({ type: 'UPDATE_SETTINGS', payload: settings });
  }, [dispatch]);
  
  return {
    autoAdvance: state.autoAdvance,
    showTeamDetails: state.showTeamDetails,
    compactView: state.compactView,
    updateSettings,
  };
}