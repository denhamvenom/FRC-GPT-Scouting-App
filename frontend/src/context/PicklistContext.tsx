import React, { createContext, useContext, useReducer, useEffect, ReactNode, useCallback } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { PicklistService } from '../services/PicklistService';
import { useAppContext } from './AppContext';

// Types for picklist state
export interface PicklistState {
  // Generation state
  isGenerating: boolean;
  generationProgress: number;
  lastGenerationId: string | null;
  
  // Picklist data
  currentPicklist: PicklistTeam[];
  lockedPicklist: PicklistTeam[] | null;
  excludedTeams: string[];
  
  // Generation settings
  generationSettings: GenerationSettings;
  
  // Analysis data
  lastAnalysis: string | null;
  missingTeams: string[];
  
  // UI state
  currentPage: number;
  pageSize: number;
  sortBy: SortField;
  sortDirection: 'asc' | 'desc';
  filterText: string;
  selectedTeams: string[];
  editMode: boolean;
  
  // Error and loading state
  error: string | null;
  isLoading: boolean;
}

export interface PicklistTeam {
  teamNumber: string;
  nickname: string;
  rank: number;
  score: number;
  reasoning: string;
  tier?: string;
  strengths?: string[];
  weaknesses?: string[];
  notes?: string;
}

export interface GenerationSettings {
  yourTeamNumber: string;
  useBatching: boolean;
  strategy: string;
  firstPickPriorities: MetricPriorities;
  secondPickPriorities: MetricPriorities;
  thirdPickPriorities: MetricPriorities;
  customPrompt: string;
  maxTeams: number;
}

export interface MetricPriorities {
  auto: number;
  teleop: number;
  endgame: number;
  defense: number;
  consistency: number;
  speed: number;
}

export type SortField = 'rank' | 'teamNumber' | 'nickname' | 'score' | 'tier';

// Action types for picklist state updates
export type PicklistAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_GENERATING'; payload: { isGenerating: boolean; progress?: number; generationId?: string } }
  | { type: 'SET_CURRENT_PICKLIST'; payload: PicklistTeam[] }
  | { type: 'SET_LOCKED_PICKLIST'; payload: PicklistTeam[] | null }
  | { type: 'SET_EXCLUDED_TEAMS'; payload: string[] }
  | { type: 'UPDATE_GENERATION_SETTINGS'; payload: Partial<GenerationSettings> }
  | { type: 'SET_ANALYSIS'; payload: { analysis: string; missingTeams: string[] } }
  | { type: 'UPDATE_UI_STATE'; payload: Partial<Pick<PicklistState, 'currentPage' | 'pageSize' | 'sortBy' | 'sortDirection' | 'filterText' | 'selectedTeams' | 'editMode'>> }
  | { type: 'TOGGLE_TEAM_SELECTION'; payload: string }
  | { type: 'CLEAR_SELECTION' }
  | { type: 'UPDATE_TEAM'; payload: { teamNumber: string; updates: Partial<PicklistTeam> } }
  | { type: 'MOVE_TEAM'; payload: { teamNumber: string; newRank: number } }
  | { type: 'EXCLUDE_TEAM'; payload: string }
  | { type: 'INCLUDE_TEAM'; payload: string }
  | { type: 'RESET_STATE' };

// Initial state
const initialGenerationSettings: GenerationSettings = {
  yourTeamNumber: '',
  useBatching: false,
  strategy: 'balanced',
  firstPickPriorities: {
    auto: 25,
    teleop: 30,
    endgame: 20,
    defense: 10,
    consistency: 10,
    speed: 5,
  },
  secondPickPriorities: {
    auto: 20,
    teleop: 25,
    endgame: 15,
    defense: 20,
    consistency: 15,
    speed: 5,
  },
  thirdPickPriorities: {
    auto: 15,
    teleop: 20,
    endgame: 10,
    defense: 30,
    consistency: 20,
    speed: 5,
  },
  customPrompt: '',
  maxTeams: 50,
};

const initialState: PicklistState = {
  isGenerating: false,
  generationProgress: 0,
  lastGenerationId: null,
  currentPicklist: [],
  lockedPicklist: null,
  excludedTeams: [],
  generationSettings: initialGenerationSettings,
  lastAnalysis: null,
  missingTeams: [],
  currentPage: 1,
  pageSize: 25,
  sortBy: 'rank',
  sortDirection: 'asc',
  filterText: '',
  selectedTeams: [],
  editMode: false,
  error: null,
  isLoading: false,
};

// Reducer for picklist state management
function picklistReducer(state: PicklistState, action: PicklistAction): PicklistState {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
        error: action.payload ? null : state.error,
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
        isGenerating: false,
      };
    
    case 'SET_GENERATING':
      return {
        ...state,
        isGenerating: action.payload.isGenerating,
        generationProgress: action.payload.progress || 0,
        lastGenerationId: action.payload.generationId || state.lastGenerationId,
        error: action.payload.isGenerating ? null : state.error,
      };
    
    case 'SET_CURRENT_PICKLIST':
      return {
        ...state,
        currentPicklist: action.payload,
        isGenerating: false,
        generationProgress: 0,
      };
    
    case 'SET_LOCKED_PICKLIST':
      return {
        ...state,
        lockedPicklist: action.payload,
      };
    
    case 'SET_EXCLUDED_TEAMS':
      return {
        ...state,
        excludedTeams: action.payload,
      };
    
    case 'UPDATE_GENERATION_SETTINGS':
      return {
        ...state,
        generationSettings: {
          ...state.generationSettings,
          ...action.payload,
        },
      };
    
    case 'SET_ANALYSIS':
      return {
        ...state,
        lastAnalysis: action.payload.analysis,
        missingTeams: action.payload.missingTeams,
      };
    
    case 'UPDATE_UI_STATE':
      return {
        ...state,
        ...action.payload,
      };
    
    case 'TOGGLE_TEAM_SELECTION': {
      const teamNumber = action.payload;
      const isSelected = state.selectedTeams.includes(teamNumber);
      const selectedTeams = isSelected
        ? state.selectedTeams.filter(t => t !== teamNumber)
        : [...state.selectedTeams, teamNumber];
      
      return {
        ...state,
        selectedTeams,
      };
    }
    
    case 'CLEAR_SELECTION':
      return {
        ...state,
        selectedTeams: [],
      };
    
    case 'UPDATE_TEAM': {
      const { teamNumber, updates } = action.payload;
      const updatedPicklist = state.currentPicklist.map(team =>
        team.teamNumber === teamNumber ? { ...team, ...updates } : team
      );
      
      return {
        ...state,
        currentPicklist: updatedPicklist,
      };
    }
    
    case 'MOVE_TEAM': {
      const { teamNumber, newRank } = action.payload;
      const team = state.currentPicklist.find(t => t.teamNumber === teamNumber);
      if (!team) return state;
      
      // Remove team from current position
      const withoutTeam = state.currentPicklist.filter(t => t.teamNumber !== teamNumber);
      
      // Insert at new position and re-rank
      const updatedPicklist = [
        ...withoutTeam.slice(0, newRank - 1),
        { ...team, rank: newRank },
        ...withoutTeam.slice(newRank - 1),
      ].map((team, index) => ({ ...team, rank: index + 1 }));
      
      return {
        ...state,
        currentPicklist: updatedPicklist,
      };
    }
    
    case 'EXCLUDE_TEAM': {
      const teamNumber = action.payload;
      const excludedTeams = state.excludedTeams.includes(teamNumber)
        ? state.excludedTeams
        : [...state.excludedTeams, teamNumber];
      
      return {
        ...state,
        excludedTeams,
      };
    }
    
    case 'INCLUDE_TEAM': {
      const teamNumber = action.payload;
      const excludedTeams = state.excludedTeams.filter(t => t !== teamNumber);
      
      return {
        ...state,
        excludedTeams,
      };
    }
    
    case 'RESET_STATE':
      return {
        ...initialState,
        generationSettings: {
          ...initialState.generationSettings,
          yourTeamNumber: state.generationSettings.yourTeamNumber, // Preserve team number
        },
      };
    
    default:
      return state;
  }
}

// Context creation
export interface PicklistContextType {
  state: PicklistState;
  dispatch: React.Dispatch<PicklistAction>;
  
  // Picklist generation
  generatePicklist: () => Promise<void>;
  checkGenerationStatus: (generationId: string) => Promise<void>;
  cancelGeneration: () => Promise<void>;
  
  // Picklist management
  loadPicklist: () => Promise<void>;
  savePicklist: () => Promise<void>;
  lockPicklist: () => Promise<void>;
  unlockPicklist: () => Promise<void>;
  
  // Team management
  updateTeam: (teamNumber: string, updates: Partial<PicklistTeam>) => void;
  moveTeam: (teamNumber: string, newRank: number) => void;
  excludeTeam: (teamNumber: string) => void;
  includeTeam: (teamNumber: string) => void;
  excludeSelectedTeams: () => void;
  
  // UI helpers
  toggleTeamSelection: (teamNumber: string) => void;
  clearSelection: () => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setSorting: (field: SortField, direction?: 'asc' | 'desc') => void;
  setFilter: (text: string) => void;
  toggleEditMode: () => void;
  
  // Utilities
  getFilteredTeams: () => PicklistTeam[];
  getPaginatedTeams: () => PicklistTeam[];
  getTotalPages: () => number;
  isTeamExcluded: (teamNumber: string) => boolean;
  isTeamSelected: (teamNumber: string) => boolean;
}

const PicklistContext = createContext<PicklistContextType | undefined>(undefined);

// Provider component
export interface PicklistProviderProps {
  children: ReactNode;
}

export function PicklistProvider({ children }: PicklistProviderProps) {
  const [state, dispatch] = useReducer(picklistReducer, initialState);
  const { state: appState, showNotification } = useAppContext();
  
  // Persist generation settings
  const [, setStoredSettings] = useLocalStorage('picklistSettings', state.generationSettings);
  const [, setStoredUIState] = useLocalStorage('picklistUIState', {
    pageSize: state.pageSize,
    sortBy: state.sortBy,
    sortDirection: state.sortDirection,
  });
  
  // Load persisted settings on mount
  const [storedSettings] = useLocalStorage('picklistSettings', initialGenerationSettings);
  const [storedUIState] = useLocalStorage('picklistUIState', {
    pageSize: 25,
    sortBy: 'rank' as SortField,
    sortDirection: 'asc' as const,
  });
  
  useEffect(() => {
    dispatch({ type: 'UPDATE_GENERATION_SETTINGS', payload: storedSettings });
    dispatch({
      type: 'UPDATE_UI_STATE',
      payload: {
        pageSize: storedUIState.pageSize,
        sortBy: storedUIState.sortBy,
        sortDirection: storedUIState.sortDirection,
      },
    });
  }, [storedSettings, storedUIState]);
  
  // Update stored settings when state changes
  useEffect(() => {
    setStoredSettings(state.generationSettings);
  }, [state.generationSettings, setStoredSettings]);
  
  useEffect(() => {
    setStoredUIState({
      pageSize: state.pageSize,
      sortBy: state.sortBy,
      sortDirection: state.sortDirection,
    });
  }, [state.pageSize, state.sortBy, state.sortDirection, setStoredUIState]);
  
  // Picklist generation functions
  const generatePicklist = useCallback(async () => {
    if (!appState.currentEventKey) {
      showNotification({
        type: 'error',
        title: 'No Event Selected',
        message: 'Please select an event before generating a picklist.',
      });
      return;
    }
    
    try {
      dispatch({ type: 'SET_GENERATING', payload: { isGenerating: true, progress: 0 } });
      
      const response = await PicklistService.generatePicklist({
        eventKey: appState.currentEventKey,
        teamNumber: state.generationSettings.yourTeamNumber,
        useBatching: state.generationSettings.useBatching,
        strategy: state.generationSettings.strategy,
        firstPickPriorities: state.generationSettings.firstPickPriorities,
        secondPickPriorities: state.generationSettings.secondPickPriorities,
        thirdPickPriorities: state.generationSettings.thirdPickPriorities,
        customPrompt: state.generationSettings.customPrompt,
        excludedTeams: state.excludedTeams,
        maxTeams: state.generationSettings.maxTeams,
      });
      
      if (response.success && response.generationId) {
        dispatch({
          type: 'SET_GENERATING',
          payload: {
            isGenerating: true,
            progress: 10,
            generationId: response.generationId,
          },
        });
        
        // Start polling for status
        await checkGenerationStatus(response.generationId);
      } else {
        throw new Error(response.error || 'Failed to start picklist generation');
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to generate picklist' });
      showNotification({
        type: 'error',
        title: 'Generation Failed',
        message: error instanceof Error ? error.message : 'Failed to generate picklist',
      });
    }
  }, [appState.currentEventKey, state.generationSettings, state.excludedTeams, showNotification]);
  
  const checkGenerationStatus = useCallback(async (generationId: string) => {
    if (!appState.currentEventKey) return;
    
    try {
      const statusResponse = await PicklistService.getGenerationStatus(generationId);
      
      dispatch({
        type: 'SET_GENERATING',
        payload: {
          isGenerating: !statusResponse.completed,
          progress: statusResponse.progress || 0,
          generationId,
        },
      });
      
      if (statusResponse.completed) {
        if (statusResponse.success && statusResponse.picklist) {
          dispatch({ type: 'SET_CURRENT_PICKLIST', payload: statusResponse.picklist });
          
          if (statusResponse.analysis) {
            dispatch({
              type: 'SET_ANALYSIS',
              payload: {
                analysis: statusResponse.analysis,
                missingTeams: statusResponse.missingTeams || [],
              },
            });
          }
          
          showNotification({
            type: 'success',
            title: 'Picklist Generated',
            message: `Successfully generated picklist with ${statusResponse.picklist.length} teams`,
          });
        } else {
          throw new Error(statusResponse.error || 'Generation completed with errors');
        }
      } else {
        // Continue polling
        setTimeout(() => checkGenerationStatus(generationId), 2000);
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to check generation status' });
      showNotification({
        type: 'error',
        title: 'Status Check Failed',
        message: error instanceof Error ? error.message : 'Failed to check generation status',
      });
    }
  }, [appState.currentEventKey, showNotification]);
  
  const cancelGeneration = useCallback(async () => {
    if (!state.lastGenerationId) return;
    
    try {
      await PicklistService.cancelGeneration(state.lastGenerationId);
      dispatch({ type: 'SET_GENERATING', payload: { isGenerating: false, progress: 0 } });
      
      showNotification({
        type: 'info',
        title: 'Generation Cancelled',
        message: 'Picklist generation has been cancelled',
      });
    } catch (error) {
      showNotification({
        type: 'error',
        title: 'Cancel Failed',
        message: error instanceof Error ? error.message : 'Failed to cancel generation',
      });
    }
  }, [state.lastGenerationId, showNotification]);
  
  // Picklist management functions
  const loadPicklist = useCallback(async () => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await PicklistService.getPicklist(appState.currentEventKey);
      
      if (response.picklist) {
        dispatch({ type: 'SET_CURRENT_PICKLIST', payload: response.picklist });
      }
      
      if (response.locked) {
        dispatch({ type: 'SET_LOCKED_PICKLIST', payload: response.picklist || null });
      }
      
      if (response.excludedTeams) {
        dispatch({ type: 'SET_EXCLUDED_TEAMS', payload: response.excludedTeams });
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to load picklist' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey]);
  
  const savePicklist = useCallback(async () => {
    if (!appState.currentEventKey || state.currentPicklist.length === 0) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await PicklistService.savePicklist({
        eventKey: appState.currentEventKey,
        picklist: state.currentPicklist,
        excludedTeams: state.excludedTeams,
        settings: state.generationSettings,
      });
      
      showNotification({
        type: 'success',
        title: 'Picklist Saved',
        message: 'Picklist has been saved successfully',
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to save picklist' });
      showNotification({
        type: 'error',
        title: 'Save Failed',
        message: error instanceof Error ? error.message : 'Failed to save picklist',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, state.currentPicklist, state.excludedTeams, state.generationSettings, showNotification]);
  
  const lockPicklist = useCallback(async () => {
    if (!appState.currentEventKey || state.currentPicklist.length === 0) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await PicklistService.lockPicklist(appState.currentEventKey);
      dispatch({ type: 'SET_LOCKED_PICKLIST', payload: state.currentPicklist });
      
      showNotification({
        type: 'info',
        title: 'Picklist Locked',
        message: 'Picklist has been locked and cannot be modified',
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to lock picklist' });
      showNotification({
        type: 'error',
        title: 'Lock Failed',
        message: error instanceof Error ? error.message : 'Failed to lock picklist',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, state.currentPicklist, showNotification]);
  
  const unlockPicklist = useCallback(async () => {
    if (!appState.currentEventKey) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await PicklistService.unlockPicklist(appState.currentEventKey);
      dispatch({ type: 'SET_LOCKED_PICKLIST', payload: null });
      
      showNotification({
        type: 'info',
        title: 'Picklist Unlocked',
        message: 'Picklist has been unlocked and can be modified',
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Failed to unlock picklist' });
      showNotification({
        type: 'error',
        title: 'Unlock Failed',
        message: error instanceof Error ? error.message : 'Failed to unlock picklist',
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [appState.currentEventKey, showNotification]);
  
  // Team management functions
  const updateTeam = useCallback((teamNumber: string, updates: Partial<PicklistTeam>) => {
    dispatch({ type: 'UPDATE_TEAM', payload: { teamNumber, updates } });
  }, []);
  
  const moveTeam = useCallback((teamNumber: string, newRank: number) => {
    dispatch({ type: 'MOVE_TEAM', payload: { teamNumber, newRank } });
  }, []);
  
  const excludeTeam = useCallback((teamNumber: string) => {
    dispatch({ type: 'EXCLUDE_TEAM', payload: teamNumber });
  }, []);
  
  const includeTeam = useCallback((teamNumber: string) => {
    dispatch({ type: 'INCLUDE_TEAM', payload: teamNumber });
  }, []);
  
  const excludeSelectedTeams = useCallback(() => {
    state.selectedTeams.forEach(teamNumber => {
      dispatch({ type: 'EXCLUDE_TEAM', payload: teamNumber });
    });
    dispatch({ type: 'CLEAR_SELECTION' });
  }, [state.selectedTeams]);
  
  // UI helper functions
  const toggleTeamSelection = useCallback((teamNumber: string) => {
    dispatch({ type: 'TOGGLE_TEAM_SELECTION', payload: teamNumber });
  }, []);
  
  const clearSelection = useCallback(() => {
    dispatch({ type: 'CLEAR_SELECTION' });
  }, []);
  
  const setPage = useCallback((page: number) => {
    dispatch({ type: 'UPDATE_UI_STATE', payload: { currentPage: page } });
  }, []);
  
  const setPageSize = useCallback((size: number) => {
    dispatch({ type: 'UPDATE_UI_STATE', payload: { pageSize: size, currentPage: 1 } });
  }, []);
  
  const setSorting = useCallback((field: SortField, direction?: 'asc' | 'desc') => {
    const newDirection = direction || (state.sortBy === field && state.sortDirection === 'asc' ? 'desc' : 'asc');
    dispatch({ type: 'UPDATE_UI_STATE', payload: { sortBy: field, sortDirection: newDirection } });
  }, [state.sortBy, state.sortDirection]);
  
  const setFilter = useCallback((text: string) => {
    dispatch({ type: 'UPDATE_UI_STATE', payload: { filterText: text, currentPage: 1 } });
  }, []);
  
  const toggleEditMode = useCallback(() => {
    dispatch({ type: 'UPDATE_UI_STATE', payload: { editMode: !state.editMode } });
  }, [state.editMode]);
  
  // Utility functions
  const getFilteredTeams = useCallback((): PicklistTeam[] => {
    let filtered = [...state.currentPicklist];
    
    // Apply text filter
    if (state.filterText) {
      const searchTerm = state.filterText.toLowerCase();
      filtered = filtered.filter(team =>
        team.teamNumber.toLowerCase().includes(searchTerm) ||
        team.nickname.toLowerCase().includes(searchTerm) ||
        team.reasoning.toLowerCase().includes(searchTerm)
      );
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[state.sortBy];
      const bValue = b[state.sortBy];
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return state.sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();
      
      if (state.sortDirection === 'asc') {
        return aStr.localeCompare(bStr);
      } else {
        return bStr.localeCompare(aStr);
      }
    });
    
    return filtered;
  }, [state.currentPicklist, state.filterText, state.sortBy, state.sortDirection]);
  
  const getPaginatedTeams = useCallback((): PicklistTeam[] => {
    const filtered = getFilteredTeams();
    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = startIndex + state.pageSize;
    return filtered.slice(startIndex, endIndex);
  }, [getFilteredTeams, state.currentPage, state.pageSize]);
  
  const getTotalPages = useCallback((): number => {
    const filtered = getFilteredTeams();
    return Math.ceil(filtered.length / state.pageSize);
  }, [getFilteredTeams, state.pageSize]);
  
  const isTeamExcluded = useCallback((teamNumber: string): boolean => {
    return state.excludedTeams.includes(teamNumber);
  }, [state.excludedTeams]);
  
  const isTeamSelected = useCallback((teamNumber: string): boolean => {
    return state.selectedTeams.includes(teamNumber);
  }, [state.selectedTeams]);
  
  const contextValue: PicklistContextType = {
    state,
    dispatch,
    generatePicklist,
    checkGenerationStatus,
    cancelGeneration,
    loadPicklist,
    savePicklist,
    lockPicklist,
    unlockPicklist,
    updateTeam,
    moveTeam,
    excludeTeam,
    includeTeam,
    excludeSelectedTeams,
    toggleTeamSelection,
    clearSelection,
    setPage,
    setPageSize,
    setSorting,
    setFilter,
    toggleEditMode,
    getFilteredTeams,
    getPaginatedTeams,
    getTotalPages,
    isTeamExcluded,
    isTeamSelected,
  };
  
  return (
    <PicklistContext.Provider value={contextValue}>
      {children}
    </PicklistContext.Provider>
  );
}

// Hook to use the PicklistContext
export function usePicklistContext() {
  const context = useContext(PicklistContext);
  if (context === undefined) {
    throw new Error('usePicklistContext must be used within a PicklistProvider');
  }
  return context;
}

// Additional hooks for specific picklist functionality
export function usePicklistGeneration() {
  const {
    state,
    generatePicklist,
    cancelGeneration,
    checkGenerationStatus,
  } = usePicklistContext();
  
  return {
    isGenerating: state.isGenerating,
    progress: state.generationProgress,
    generatePicklist,
    cancelGeneration,
    checkGenerationStatus,
  };
}

export function usePicklistSettings() {
  const { state, dispatch } = usePicklistContext();
  
  const updateSettings = useCallback((settings: Partial<GenerationSettings>) => {
    dispatch({ type: 'UPDATE_GENERATION_SETTINGS', payload: settings });
  }, [dispatch]);
  
  return {
    settings: state.generationSettings,
    updateSettings,
    excludedTeams: state.excludedTeams,
  };
}

export function usePicklistData() {
  const {
    state,
    getFilteredTeams,
    getPaginatedTeams,
    getTotalPages,
  } = usePicklistContext();
  
  return {
    currentPicklist: state.currentPicklist,
    lockedPicklist: state.lockedPicklist,
    filteredTeams: getFilteredTeams(),
    paginatedTeams: getPaginatedTeams(),
    totalPages: getTotalPages(),
    currentPage: state.currentPage,
    pageSize: state.pageSize,
    isLocked: !!state.lockedPicklist,
  };
}