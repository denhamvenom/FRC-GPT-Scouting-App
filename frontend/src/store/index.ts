// Main store exports
export {
  useAppStore,
  useCurrentEvent,
  useUserPreferences,
  useWorkflowState,
  useDatasetStatus,
  useNotifications,
  useLoadingState,
  useCache,
  useIsStepCompleted,
  useCanProceedToStep,
  useNextStep,
  subscribeToEvent,
  subscribeToWorkflow,
} from './useAppStore';

// Store types
export type {
  AppStore,
  AppStoreState,
  AppStoreActions,
  UserPreferences,
  WorkflowState,
  DatasetStatus,
  UIState,
} from './useAppStore';

// Slice exports
export { createEventSlice } from './slices/eventSlice';
export type { EventSlice, EventMetadata, RecentEvent } from './slices/eventSlice';

// Re-export commonly used store functions
export const {
  setEvent,
  clearEvent,
  setUserTeam,
  updatePreferences,
  updateWorkflowState,
  markStepCompleted,
  updateDatasetStatus,
  addNotification,
  removeNotification,
  clearNotifications,
  setLoading,
  setCache,
  getCache,
  clearCache,
  reset,
  sync,
} = useAppStore.getState();

// Store utilities
export const getAppStore = () => useAppStore.getState();
export const subscribeToStore = useAppStore.subscribe;