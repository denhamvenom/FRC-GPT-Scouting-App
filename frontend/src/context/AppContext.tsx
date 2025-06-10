import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { AppStateService } from '../services/AppStateService';

// Types for global app state
export interface AppState {
  // Event and competition info
  currentEventKey: string | null;
  currentYear: number;
  eventMetadata: EventMetadata | null;
  
  // User preferences
  userTeamNumber: string | null;
  userPreferences: UserPreferences;
  
  // Workflow state
  workflowState: WorkflowState;
  
  // Dataset and validation status
  datasetStatus: DatasetStatus;
  
  // UI state
  uiState: UIState;
}

interface EventMetadata {
  name: string;
  location: string;
  startDate: string;
  endDate: string;
  weekNumber: number;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  compactMode: boolean;
  autoSave: boolean;
  notificationsEnabled: boolean;
  defaultPageSize: number;
}

export interface WorkflowState {
  setupCompleted: boolean;
  fieldSelectionCompleted: boolean;
  datasetBuilt: boolean;
  validationCompleted: boolean;
  canProceedToNextStep: (step: WorkflowStep) => boolean;
}

export interface DatasetStatus {
  hasUnifiedDataset: boolean;
  lastBuiltTimestamp: string | null;
  validationStatus: 'pending' | 'valid' | 'invalid' | 'unknown';
  totalTeams: number;
  totalMatches: number;
}

export interface UIState {
  sidebarCollapsed: boolean;
  activeNotifications: Notification[];
  globalLoading: boolean;
  lastActivity: number;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: number;
  autoClose?: boolean;
}

export type WorkflowStep = 'setup' | 'field-selection' | 'dataset-build' | 'validation' | 'picklist' | 'alliance';

// Action types for state updates
export type AppAction =
  | { type: 'SET_EVENT'; payload: { eventKey: string; year: number; metadata?: EventMetadata } }
  | { type: 'SET_USER_TEAM'; payload: string | null }
  | { type: 'UPDATE_USER_PREFERENCES'; payload: Partial<UserPreferences> }
  | { type: 'UPDATE_WORKFLOW_STATE'; payload: Partial<WorkflowState> }
  | { type: 'UPDATE_DATASET_STATUS'; payload: Partial<DatasetStatus> }
  | { type: 'UPDATE_UI_STATE'; payload: Partial<UIState> }
  | { type: 'ADD_NOTIFICATION'; payload: Omit<Notification, 'timestamp'> & { id?: string } }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_NOTIFICATIONS' }
  | { type: 'RESET_STATE' };

// Initial state
const initialState: AppState = {
  currentEventKey: null,
  currentYear: 2025,
  eventMetadata: null,
  userTeamNumber: null,
  userPreferences: {
    theme: 'system',
    compactMode: false,
    autoSave: true,
    notificationsEnabled: true,
    defaultPageSize: 25,
  },
  workflowState: {
    setupCompleted: false,
    fieldSelectionCompleted: false,
    datasetBuilt: false,
    validationCompleted: false,
    canProceedToNextStep: (step: WorkflowStep) => {
      // Basic workflow validation logic
      switch (step) {
        case 'setup':
          return true;
        case 'field-selection':
          return true; // Always allow field selection
        case 'dataset-build':
          return true; // Field selection not strictly required
        case 'validation':
          return true; // Can validate any dataset
        case 'picklist':
          return true; // Can generate from any dataset
        case 'alliance':
          return true; // Can start alliance selection anytime
        default:
          return false;
      }
    },
  },
  datasetStatus: {
    hasUnifiedDataset: false,
    lastBuiltTimestamp: null,
    validationStatus: 'unknown',
    totalTeams: 0,
    totalMatches: 0,
  },
  uiState: {
    sidebarCollapsed: false,
    activeNotifications: [],
    globalLoading: false,
    lastActivity: Date.now(),
  },
};

// Reducer for state management
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_EVENT':
      return {
        ...state,
        currentEventKey: action.payload.eventKey,
        currentYear: action.payload.year,
        eventMetadata: action.payload.metadata || null,
      };
    
    case 'SET_USER_TEAM':
      return {
        ...state,
        userTeamNumber: action.payload,
      };
    
    case 'UPDATE_USER_PREFERENCES':
      return {
        ...state,
        userPreferences: {
          ...state.userPreferences,
          ...action.payload,
        },
      };
    
    case 'UPDATE_WORKFLOW_STATE':
      return {
        ...state,
        workflowState: {
          ...state.workflowState,
          ...action.payload,
        },
      };
    
    case 'UPDATE_DATASET_STATUS':
      return {
        ...state,
        datasetStatus: {
          ...state.datasetStatus,
          ...action.payload,
        },
      };
    
    case 'UPDATE_UI_STATE':
      return {
        ...state,
        uiState: {
          ...state.uiState,
          ...action.payload,
          lastActivity: Date.now(),
        },
      };
    
    case 'ADD_NOTIFICATION':
      const newNotification: Notification = {
        ...action.payload,
        id: action.payload.id || `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
      };
      return {
        ...state,
        uiState: {
          ...state.uiState,
          activeNotifications: [...state.uiState.activeNotifications, newNotification],
        },
      };
    
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        uiState: {
          ...state.uiState,
          activeNotifications: state.uiState.activeNotifications.filter(
            notification => notification.id !== action.payload
          ),
        },
      };
    
    case 'CLEAR_NOTIFICATIONS':
      return {
        ...state,
        uiState: {
          ...state.uiState,
          activeNotifications: [],
        },
      };
    
    case 'RESET_STATE':
      return {
        ...initialState,
        userPreferences: state.userPreferences, // Preserve user preferences
      };
    
    default:
      return state;
  }
}

// Context creation
export interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  
  // Convenience methods
  setEvent: (eventKey: string, year: number, metadata?: EventMetadata) => void;
  setUserTeam: (teamNumber: string | null) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  updateWorkflowState: (workflowState: Partial<WorkflowState>) => void;
  updateDatasetStatus: (status: Partial<DatasetStatus>) => void;
  showNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  clearNotifications: () => void;
  
  // Utility methods
  isStepCompleted: (step: WorkflowStep) => boolean;
  canProceedToStep: (step: WorkflowStep) => boolean;
  getNextStep: () => WorkflowStep | null;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
export interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  // Sync with localStorage using existing AppStateService
  const [storedEventKey] = useLocalStorage<string | null>('currentEventKey', null);
  const [storedYear] = useLocalStorage<number>('currentYear', 2025);
  const [storedTeamNumber] = useLocalStorage<string | null>('yourTeamNumber', null);
  const [storedPreferences] = useLocalStorage<UserPreferences>('userPreferences', initialState.userPreferences);
  
  // Initialize state from localStorage on mount
  useEffect(() => {
    // Load AppStateService data
    const appState = AppStateService.getState();
    
    // Update state with persisted values
    if (storedEventKey) {
      dispatch({
        type: 'SET_EVENT',
        payload: { eventKey: storedEventKey, year: storedYear || 2025 },
      });
    }
    
    if (storedTeamNumber) {
      dispatch({ type: 'SET_USER_TEAM', payload: storedTeamNumber });
    }
    
    dispatch({ type: 'UPDATE_USER_PREFERENCES', payload: storedPreferences });
    
    // Update workflow state from AppStateService
    dispatch({
      type: 'UPDATE_WORKFLOW_STATE',
      payload: {
        setupCompleted: appState.setupCompleted,
        fieldSelectionCompleted: appState.fieldSelectionCompleted,
        datasetBuilt: appState.datasetBuilt,
        validationCompleted: appState.validationCompleted,
      },
    });
  }, [storedEventKey, storedYear, storedTeamNumber, storedPreferences]);
  
  // Convenience methods
  const setEvent = (eventKey: string, year: number, metadata?: EventMetadata) => {
    dispatch({ type: 'SET_EVENT', payload: { eventKey, year, metadata } });
    AppStateService.resetForNewEvent(eventKey, year);
  };
  
  const setUserTeam = (teamNumber: string | null) => {
    dispatch({ type: 'SET_USER_TEAM', payload: teamNumber });
  };
  
  const updatePreferences = (preferences: Partial<UserPreferences>) => {
    dispatch({ type: 'UPDATE_USER_PREFERENCES', payload: preferences });
  };
  
  const updateWorkflowState = (workflowState: Partial<WorkflowState>) => {
    dispatch({ type: 'UPDATE_WORKFLOW_STATE', payload: workflowState });
    
    // Sync with AppStateService
    if (workflowState.setupCompleted) {
      AppStateService.completeStep('setupCompleted');
    }
    if (workflowState.fieldSelectionCompleted) {
      AppStateService.completeStep('fieldSelectionCompleted');
    }
    if (workflowState.datasetBuilt) {
      AppStateService.completeStep('datasetBuilt');
    }
    if (workflowState.validationCompleted) {
      AppStateService.completeStep('validationCompleted');
    }
  };
  
  const updateDatasetStatus = (status: Partial<DatasetStatus>) => {
    dispatch({ type: 'UPDATE_DATASET_STATUS', payload: status });
  };
  
  const showNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    // Generate ID for auto-removal
    const notificationId = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    dispatch({ type: 'ADD_NOTIFICATION', payload: { ...notification, id: notificationId } });
    
    // Auto-remove notifications after delay if autoClose is true (default)
    if (notification.autoClose !== false) {
      setTimeout(() => {
        dispatch({ type: 'REMOVE_NOTIFICATION', payload: notificationId });
      }, 5000);
    }
  };
  
  const clearNotifications = () => {
    dispatch({ type: 'CLEAR_NOTIFICATIONS' });
  };
  
  // Utility methods
  const isStepCompleted = (step: WorkflowStep): boolean => {
    switch (step) {
      case 'setup':
        return state.workflowState.setupCompleted;
      case 'field-selection':
        return state.workflowState.fieldSelectionCompleted;
      case 'dataset-build':
        return state.workflowState.datasetBuilt;
      case 'validation':
        return state.workflowState.validationCompleted;
      case 'picklist':
      case 'alliance':
        return true; // These are always available
      default:
        return false;
    }
  };
  
  const canProceedToStep = (step: WorkflowStep): boolean => {
    return state.workflowState.canProceedToNextStep(step);
  };
  
  const getNextStep = (): WorkflowStep | null => {
    if (!state.workflowState.setupCompleted) return 'setup';
    if (!state.workflowState.fieldSelectionCompleted) return 'field-selection';
    if (!state.workflowState.datasetBuilt) return 'dataset-build';
    if (!state.workflowState.validationCompleted) return 'validation';
    return 'picklist'; // Default next step after validation
  };
  
  const contextValue: AppContextType = {
    state,
    dispatch,
    setEvent,
    setUserTeam,
    updatePreferences,
    updateWorkflowState,
    updateDatasetStatus,
    showNotification,
    clearNotifications,
    isStepCompleted,
    canProceedToStep,
    getNextStep,
  };
  
  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

// Hook to use the AppContext
export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}

// Additional hooks for specific parts of the state
export function useCurrentEvent() {
  const { state } = useAppContext();
  return {
    eventKey: state.currentEventKey,
    year: state.currentYear,
    metadata: state.eventMetadata,
  };
}

export function useUserPreferences() {
  const { state, updatePreferences } = useAppContext();
  return {
    preferences: state.userPreferences,
    updatePreferences,
  };
}

export function useWorkflow() {
  const { state, updateWorkflowState, isStepCompleted, canProceedToStep, getNextStep } = useAppContext();
  return {
    workflowState: state.workflowState,
    updateWorkflowState,
    isStepCompleted,
    canProceedToStep,
    getNextStep,
  };
}

export function useNotifications() {
  const { state, showNotification, clearNotifications, dispatch } = useAppContext();
  
  const removeNotification = (id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  };
  
  return {
    notifications: state.uiState.activeNotifications,
    showNotification,
    removeNotification,
    clearNotifications,
  };
}

export function useDatasetStatus() {
  const { state, updateDatasetStatus } = useAppContext();
  return {
    datasetStatus: state.datasetStatus,
    updateDatasetStatus,
  };
}