import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { persist, createJSONStorage } from 'zustand/middleware';
import { AppStateService } from '../services/AppStateService';

// Types for app store state
export interface AppStoreState {
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
  
  // UI state (not persisted)
  uiState: UIState;
  
  // Loading states
  isLoading: Record<string, boolean>;
  
  // Cache for API responses
  cache: Record<string, CacheEntry>;
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
  language: string;
  timezone: string;
}

export interface WorkflowState {
  setupCompleted: boolean;
  fieldSelectionCompleted: boolean;
  datasetBuilt: boolean;
  validationCompleted: boolean;
  lastCompletedStep: string | null;
  stepProgress: Record<string, number>;
}

export interface DatasetStatus {
  hasUnifiedDataset: boolean;
  lastBuiltTimestamp: string | null;
  validationStatus: 'pending' | 'valid' | 'invalid' | 'unknown';
  totalTeams: number;
  totalMatches: number;
  schemaVersion: string | null;
}

export interface UIState {
  sidebarCollapsed: boolean;
  activeNotifications: Notification[];
  globalLoading: boolean;
  lastActivity: number;
  activeModals: string[];
  focusedElement: string | null;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: number;
  autoClose?: boolean;
  persistent?: boolean;
}

interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number;
  key: string;
}

// Actions interface
export interface AppStoreActions {
  // Event management
  setEvent: (eventKey: string, year: number, metadata?: EventMetadata) => void;
  clearEvent: () => void;
  
  // User preferences
  setUserTeam: (teamNumber: string | null) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  resetPreferences: () => void;
  
  // Workflow management
  updateWorkflowState: (updates: Partial<WorkflowState>) => void;
  markStepCompleted: (step: string, progress?: number) => void;
  resetWorkflow: () => void;
  
  // Dataset management
  updateDatasetStatus: (status: Partial<DatasetStatus>) => void;
  clearDatasetStatus: () => void;
  
  // UI state management
  updateUIState: (updates: Partial<UIState>) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
  setFocus: (elementId: string | null) => void;
  
  // Loading state management
  setLoading: (key: string, loading: boolean) => void;
  clearLoading: () => void;
  
  // Cache management
  setCache: (key: string, data: any, ttl?: number) => void;
  getCache: (key: string) => any | null;
  clearCache: (key?: string) => void;
  
  // Utility actions
  reset: () => void;
  sync: () => Promise<void>;
}

// Combined store type
export type AppStore = AppStoreState & AppStoreActions;

// Initial state
const initialState: AppStoreState = {
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
    language: 'en',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  },
  workflowState: {
    setupCompleted: false,
    fieldSelectionCompleted: false,
    datasetBuilt: false,
    validationCompleted: false,
    lastCompletedStep: null,
    stepProgress: {},
  },
  datasetStatus: {
    hasUnifiedDataset: false,
    lastBuiltTimestamp: null,
    validationStatus: 'unknown',
    totalTeams: 0,
    totalMatches: 0,
    schemaVersion: null,
  },
  uiState: {
    sidebarCollapsed: false,
    activeNotifications: [],
    globalLoading: false,
    lastActivity: Date.now(),
    activeModals: [],
    focusedElement: null,
  },
  isLoading: {},
  cache: {},
};

// Create the store with persistence
export const useAppStore = create<AppStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        ...initialState,
        
        // Event management
        setEvent: (eventKey, year, metadata) => {
          set({
            currentEventKey: eventKey,
            currentYear: year,
            eventMetadata: metadata || null,
          });
          
          // Sync with AppStateService
          AppStateService.setCurrentEvent(eventKey, year);
        },
        
        clearEvent: () => {
          set({
            currentEventKey: null,
            currentYear: 2025,
            eventMetadata: null,
          });
        },
        
        // User preferences
        setUserTeam: (teamNumber) => {
          set({ userTeamNumber: teamNumber });
        },
        
        updatePreferences: (preferences) => {
          set((state) => ({
            userPreferences: {
              ...state.userPreferences,
              ...preferences,
            },
          }));
        },
        
        resetPreferences: () => {
          set({ userPreferences: initialState.userPreferences });
        },
        
        // Workflow management
        updateWorkflowState: (updates) => {
          set((state) => ({
            workflowState: {
              ...state.workflowState,
              ...updates,
            },
          }));
          
          // Sync with AppStateService
          const { workflowState } = get();
          if (updates.setupCompleted !== undefined) {
            AppStateService.markSetupCompleted(updates.setupCompleted);
          }
          if (updates.fieldSelectionCompleted !== undefined) {
            AppStateService.markFieldSelectionCompleted(updates.fieldSelectionCompleted);
          }
          if (updates.datasetBuilt !== undefined) {
            AppStateService.markDatasetBuilt(updates.datasetBuilt);
          }
          if (updates.validationCompleted !== undefined) {
            AppStateService.markValidationCompleted(updates.validationCompleted);
          }
        },
        
        markStepCompleted: (step, progress = 100) => {
          set((state) => ({
            workflowState: {
              ...state.workflowState,
              lastCompletedStep: step,
              stepProgress: {
                ...state.workflowState.stepProgress,
                [step]: progress,
              },
              // Update specific step completion flags
              ...(step === 'setup' && { setupCompleted: true }),
              ...(step === 'field-selection' && { fieldSelectionCompleted: true }),
              ...(step === 'dataset-build' && { datasetBuilt: true }),
              ...(step === 'validation' && { validationCompleted: true }),
            },
          }));
        },
        
        resetWorkflow: () => {
          set({ workflowState: initialState.workflowState });
        },
        
        // Dataset management
        updateDatasetStatus: (status) => {
          set((state) => ({
            datasetStatus: {
              ...state.datasetStatus,
              ...status,
            },
          }));
        },
        
        clearDatasetStatus: () => {
          set({ datasetStatus: initialState.datasetStatus });
        },
        
        // UI state management
        updateUIState: (updates) => {
          set((state) => ({
            uiState: {
              ...state.uiState,
              ...updates,
              lastActivity: Date.now(),
            },
          }));
        },
        
        addNotification: (notification) => {
          const newNotification: Notification = {
            ...notification,
            id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: Date.now(),
          };
          
          set((state) => ({
            uiState: {
              ...state.uiState,
              activeNotifications: [...state.uiState.activeNotifications, newNotification],
            },
          }));
          
          // Auto-remove notifications after delay if autoClose is true (default)
          if (notification.autoClose !== false && !notification.persistent) {
            setTimeout(() => {
              get().removeNotification(newNotification.id);
            }, 5000);
          }
        },
        
        removeNotification: (id) => {
          set((state) => ({
            uiState: {
              ...state.uiState,
              activeNotifications: state.uiState.activeNotifications.filter(
                notification => notification.id !== id
              ),
            },
          }));
        },
        
        clearNotifications: () => {
          set((state) => ({
            uiState: {
              ...state.uiState,
              activeNotifications: [],
            },
          }));
        },
        
        openModal: (modalId) => {
          set((state) => ({
            uiState: {
              ...state.uiState,
              activeModals: [...state.uiState.activeModals, modalId],
            },
          }));
        },
        
        closeModal: (modalId) => {
          set((state) => ({
            uiState: {
              ...state.uiState,
              activeModals: state.uiState.activeModals.filter(id => id !== modalId),
            },
          }));
        },
        
        setFocus: (elementId) => {
          set((state) => ({
            uiState: {
              ...state.uiState,
              focusedElement: elementId,
            },
          }));
        },
        
        // Loading state management
        setLoading: (key, loading) => {
          set((state) => ({
            isLoading: {
              ...state.isLoading,
              [key]: loading,
            },
          }));
        },
        
        clearLoading: () => {
          set({ isLoading: {} });
        },
        
        // Cache management
        setCache: (key, data, ttl = 5 * 60 * 1000) => { // Default 5 minutes
          const entry: CacheEntry = {
            data,
            timestamp: Date.now(),
            ttl,
            key,
          };
          
          set((state) => ({
            cache: {
              ...state.cache,
              [key]: entry,
            },
          }));
        },
        
        getCache: (key) => {
          const entry = get().cache[key];
          if (!entry) return null;
          
          const now = Date.now();
          if (now - entry.timestamp > entry.ttl) {
            // Entry expired, remove it
            get().clearCache(key);
            return null;
          }
          
          return entry.data;
        },
        
        clearCache: (key) => {
          if (key) {
            set((state) => {
              const { [key]: removed, ...rest } = state.cache;
              return { cache: rest };
            });
          } else {
            set({ cache: {} });
          }
        },
        
        // Utility actions
        reset: () => {
          set({
            ...initialState,
            userPreferences: get().userPreferences, // Preserve preferences
          });
        },
        
        sync: async () => {
          try {
            // Sync with AppStateService
            const appState = AppStateService.getAppState();
            
            set((state) => ({
              workflowState: {
                ...state.workflowState,
                setupCompleted: appState.setupCompleted,
                fieldSelectionCompleted: appState.fieldSelectionCompleted,
                datasetBuilt: appState.datasetBuilt,
                validationCompleted: appState.validationCompleted,
              },
            }));
          } catch (error) {
            console.error('Failed to sync app state:', error);
          }
        },
      }),
      {
        name: 'app-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          // Only persist certain parts of the state
          currentEventKey: state.currentEventKey,
          currentYear: state.currentYear,
          userTeamNumber: state.userTeamNumber,
          userPreferences: state.userPreferences,
          workflowState: state.workflowState,
          datasetStatus: state.datasetStatus,
        }),
        version: 1,
        migrate: (persistedState: any, version: number) => {
          // Handle state migrations if needed
          if (version === 0) {
            // Migration from version 0 to 1
            return {
              ...persistedState,
              userPreferences: {
                ...initialState.userPreferences,
                ...persistedState.userPreferences,
              },
            };
          }
          return persistedState;
        },
      }
    )
  )
);

// Selector hooks for specific parts of the state
export const useCurrentEvent = () => useAppStore((state) => ({
  eventKey: state.currentEventKey,
  year: state.currentYear,
  metadata: state.eventMetadata,
}));

export const useUserPreferences = () => useAppStore((state) => ({
  preferences: state.userPreferences,
  updatePreferences: state.updatePreferences,
  resetPreferences: state.resetPreferences,
}));

export const useWorkflowState = () => useAppStore((state) => ({
  workflowState: state.workflowState,
  updateWorkflowState: state.updateWorkflowState,
  markStepCompleted: state.markStepCompleted,
  resetWorkflow: state.resetWorkflow,
}));

export const useDatasetStatus = () => useAppStore((state) => ({
  datasetStatus: state.datasetStatus,
  updateDatasetStatus: state.updateDatasetStatus,
  clearDatasetStatus: state.clearDatasetStatus,
}));

export const useNotifications = () => useAppStore((state) => ({
  notifications: state.uiState.activeNotifications,
  addNotification: state.addNotification,
  removeNotification: state.removeNotification,
  clearNotifications: state.clearNotifications,
}));

export const useLoadingState = () => useAppStore((state) => ({
  isLoading: state.isLoading,
  setLoading: state.setLoading,
  clearLoading: state.clearLoading,
}));

export const useCache = () => useAppStore((state) => ({
  cache: state.cache,
  setCache: state.setCache,
  getCache: state.getCache,
  clearCache: state.clearCache,
}));

// Computed selectors
export const useIsStepCompleted = (step: string) => {
  return useAppStore((state) => {
    switch (step) {
      case 'setup':
        return state.workflowState.setupCompleted;
      case 'field-selection':
        return state.workflowState.fieldSelectionCompleted;
      case 'dataset-build':
        return state.workflowState.datasetBuilt;
      case 'validation':
        return state.workflowState.validationCompleted;
      default:
        return false;
    }
  });
};

export const useCanProceedToStep = (step: string) => {
  return useAppStore((state) => {
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
  });
};

export const useNextStep = () => {
  return useAppStore((state) => {
    if (!state.workflowState.setupCompleted) return 'setup';
    if (!state.workflowState.fieldSelectionCompleted) return 'field-selection';
    if (!state.workflowState.datasetBuilt) return 'dataset-build';
    if (!state.workflowState.validationCompleted) return 'validation';
    return 'picklist'; // Default next step after validation
  });
};

// Subscribe to specific state changes
export const subscribeToEvent = (callback: (event: { eventKey: string | null; year: number }) => void) => {
  return useAppStore.subscribe(
    (state) => ({ eventKey: state.currentEventKey, year: state.currentYear }),
    callback,
    { equalityFn: (a, b) => a.eventKey === b.eventKey && a.year === b.year }
  );
};

export const subscribeToWorkflow = (callback: (workflowState: WorkflowState) => void) => {
  return useAppStore.subscribe(
    (state) => state.workflowState,
    callback
  );
};