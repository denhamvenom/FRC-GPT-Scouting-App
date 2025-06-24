// frontend/src/services/AppStateService.ts

interface AppState {
  setupCompleted: boolean;
  fieldSelectionCompleted: boolean;
  datasetBuilt: boolean;
  validationCompleted: boolean;
  currentEventKey: string;
  currentYear: number;
  archivedEvents: string[];
}

// Initial state with nothing completed
const initialState: AppState = {
  setupCompleted: false,
  fieldSelectionCompleted: false,
  datasetBuilt: false,
  validationCompleted: false,
  currentEventKey: '',
  currentYear: new Date().getFullYear(),
  archivedEvents: []
};

// Keys for localStorage
const STATE_KEY = 'frc_scouting_app_state';
const ARCHIVES_KEY = 'frc_scouting_archived_events';

/**
 * Service for managing application state and workflow progression
 */
export const AppStateService = {
  /**
   * Get the current application state
   */
  getState: (): AppState => {
    try {
      const storedState = localStorage.getItem(STATE_KEY);
      if (storedState) {
        return JSON.parse(storedState);
      }
    } catch (error) {
      console.error('Error retrieving app state:', error);
    }
    return initialState;
  },

  /**
   * Save the current application state
   */
  saveState: (state: AppState): void => {
    try {
      localStorage.setItem(STATE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error('Error saving app state:', error);
    }
  },

  /**
   * Update a specific part of the state
   */
  updateState: (updates: Partial<AppState>): AppState => {
    const currentState = AppStateService.getState();
    const newState = { ...currentState, ...updates };
    AppStateService.saveState(newState);
    return newState;
  },

  /**
   * Mark a step as completed
   */
  completeStep: (step: keyof AppState): AppState => {
    const updates = { [step]: true } as Partial<AppState>;
    return AppStateService.updateState(updates);
  },

  /**
   * Reset the application state for a new event
   */
  resetForNewEvent: (eventKey: string, year: number): AppState => {
    // Archive current event first if it exists
    const currentState = AppStateService.getState();
    if (currentState.currentEventKey) {
      AppStateService.archiveEvent(currentState.currentEventKey, currentState.currentYear);
    }

    // Create new state with event info but steps reset
    const newState: AppState = {
      ...initialState,
      currentEventKey: eventKey,
      currentYear: year,
      archivedEvents: currentState.archivedEvents
    };
    
    AppStateService.saveState(newState);
    return newState;
  },

  /**
   * Check if all prerequisites for a step are completed
   */
  canAccessStep: (step: string): boolean => {
    const state = AppStateService.getState();
    
    // TEMPORARY: Enable all steps for testing purposes
    const TESTING_MODE = true;
    if (TESTING_MODE) {
      return true;
    }
    
    switch (step) {
      case 'setup':
        return true; // Setup is always accessible
      
      case 'field-selection':
        return state.setupCompleted;
      
      case 'build-dataset':
        return state.setupCompleted && state.fieldSelectionCompleted;
      
      case 'validation':
        return state.setupCompleted && state.fieldSelectionCompleted && state.datasetBuilt;
      
      case 'picklist':
        return state.setupCompleted && state.fieldSelectionCompleted && 
               state.datasetBuilt && state.validationCompleted;
      
      default:
        return false;
    }
  },

  /**
   * Archive the current event
   */
  archiveEvent: (eventKey: string, year: number): void => {
    try {
      // Get current archives
      let archives = [];
      const storedArchives = localStorage.getItem(ARCHIVES_KEY);
      if (storedArchives) {
        archives = JSON.parse(storedArchives);
      }
      
      // Add current event if not already archived
      const eventId = `${year}_${eventKey}`;
      if (!archives.includes(eventId)) {
        archives.push(eventId);
      }
      
      // Save updated archives
      localStorage.setItem(ARCHIVES_KEY, JSON.stringify(archives));
      
      // Update current state
      const currentState = AppStateService.getState();
      AppStateService.updateState({
        archivedEvents: archives
      });
      
    } catch (error) {
      console.error('Error archiving event:', error);
    }
  },

  /**
   * Get list of archived events
   */
  getArchivedEvents: (): string[] => {
    try {
      const storedArchives = localStorage.getItem(ARCHIVES_KEY);
      if (storedArchives) {
        return JSON.parse(storedArchives);
      }
    } catch (error) {
      console.error('Error retrieving archived events:', error);
    }
    return [];
  },

  /**
   * Verify completion status by checking server-side state
   * This makes sure localStorage state matches actual data by checking for actual file existence
   */
  async verifyCompletionStatus(): Promise<AppState> {
    try {
      // Start with the current state
      const currentState = AppStateService.getState();
      let verifiedState: Partial<AppState> = { ...currentState };
      
      // Check if setup is completed by querying schema existence
      try {
        const schemaResponse = await fetch('http://localhost:8000/api/schema/check');
        if (schemaResponse.ok) {
          const schemaData = await schemaResponse.json();
          verifiedState.setupCompleted = schemaData.setup_completed;
        }
      } catch (error) {
        console.error('Error checking schema status:', error);
      }
      
      // Check for field selection completion 
      try {
        const fieldSelectionResponse = await fetch('http://localhost:8000/api/schema/fields');
        if (fieldSelectionResponse.ok) {
          const fieldData = await fieldSelectionResponse.json();
          verifiedState.fieldSelectionCompleted = fieldData.exists;
        }
      } catch (error) {
        console.error('Error checking field selection status:', error);
      }
      
      // Check if dataset exists - two approaches:
      // 1. If we have a current event key, check for that specific dataset
      // 2. Otherwise, check if any datasets exist at all
      try {
        if (currentState.currentEventKey && currentState.currentYear) {
          const datasetResponse = await fetch(
            `http://localhost:8000/api/unified/status?event_key=${currentState.currentEventKey}&year=${currentState.currentYear}`
          );
          if (datasetResponse.ok) {
            const datasetData = await datasetResponse.json();
            verifiedState.datasetBuilt = datasetData.dataset_built === true;
          }
        } else {
          // Check if any datasets exist
          const allDatasetsResponse = await fetch('http://localhost:8000/api/unified/check-all');
          if (allDatasetsResponse.ok) {
            const allDatasetsData = await allDatasetsResponse.json();
            verifiedState.datasetBuilt = allDatasetsData.datasets_exist === true;
            
            // If datasets exist but we don't have current event info, get it from the first dataset
            if (allDatasetsData.datasets_exist && allDatasetsData.datasets.length > 0 && 
                (!currentState.currentEventKey || !currentState.currentYear)) {
              const firstDataset = allDatasetsData.datasets[0];
              verifiedState.currentEventKey = firstDataset.event_key;
              // Extract year from metadata if available, otherwise use current year
              verifiedState.currentYear = currentState.currentYear || new Date().getFullYear();
            }
          }
        }
      } catch (error) {
        console.error('Error checking dataset status:', error);
      }
      
      // Check validation status
      try {
        if (verifiedState.datasetBuilt) {
          const validationResponse = await fetch('http://localhost:8000/api/validate/check-validation-status');
          if (validationResponse.ok) {
            const validationData = await validationResponse.json();
            verifiedState.validationCompleted = validationData.validation_completed === true && 
                                               !validationData.validation_has_issues;
          }
        }
      } catch (error) {
        console.error('Error checking validation status:', error);
      }
      
      // Update and return the verified state
      return AppStateService.updateState(verifiedState);
      
    } catch (error) {
      console.error('Error verifying completion status:', error);
      return AppStateService.getState();
    }
  }
};

export default AppStateService;