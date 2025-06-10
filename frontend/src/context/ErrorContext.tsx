import React, { createContext, useContext, useReducer, useCallback, ReactNode, useEffect } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';

// Types for error handling state
export interface ErrorState {
  // Global error tracking
  globalError: GlobalError | null;
  recentErrors: ErrorEntry[];
  
  // Error boundaries
  boundaryErrors: BoundaryError[];
  
  // Network and API errors
  networkErrors: NetworkError[];
  apiErrors: ApiError[];
  
  // User preferences for error handling
  errorPreferences: ErrorPreferences;
  
  // Recovery state
  recoveryAttempts: Record<string, number>;
  lastRecoveryTime: Record<string, number>;
}

export interface GlobalError {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  details?: string;
  stackTrace?: string;
  timestamp: number;
  source: 'component' | 'api' | 'network' | 'validation' | 'unknown';
  recoverable: boolean;
  retryable: boolean;
}

export interface ErrorEntry {
  id: string;
  error: Error;
  context: string;
  timestamp: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  handled: boolean;
  reportedToUser: boolean;
}

export interface BoundaryError {
  id: string;
  componentStack: string;
  errorBoundary: string;
  error: Error;
  timestamp: number;
  recovered: boolean;
}

export interface NetworkError {
  id: string;
  url: string;
  method: string;
  status: number;
  statusText: string;
  timestamp: number;
  retryCount: number;
  maxRetries: number;
}

export interface ApiError {
  id: string;
  endpoint: string;
  method: string;
  requestData?: any;
  responseData?: any;
  statusCode: number;
  errorCode?: string;
  userMessage: string;
  technicalMessage: string;
  timestamp: number;
  recoverable: boolean;
}

export interface ErrorPreferences {
  showTechnicalDetails: boolean;
  autoRetryFailedRequests: boolean;
  maxRetryAttempts: number;
  retryDelay: number;
  persistErrorLogs: boolean;
  reportCriticalErrors: boolean;
  showErrorNotifications: boolean;
}

// Action types for error state updates
export type ErrorAction =
  | { type: 'SET_GLOBAL_ERROR'; payload: GlobalError | null }
  | { type: 'ADD_ERROR'; payload: Omit<ErrorEntry, 'id' | 'timestamp'> }
  | { type: 'MARK_ERROR_HANDLED'; payload: string }
  | { type: 'ADD_BOUNDARY_ERROR'; payload: Omit<BoundaryError, 'id' | 'timestamp'> }
  | { type: 'MARK_BOUNDARY_RECOVERED'; payload: string }
  | { type: 'ADD_NETWORK_ERROR'; payload: Omit<NetworkError, 'id' | 'timestamp'> }
  | { type: 'ADD_API_ERROR'; payload: Omit<ApiError, 'id' | 'timestamp'> }
  | { type: 'UPDATE_PREFERENCES'; payload: Partial<ErrorPreferences> }
  | { type: 'INCREMENT_RECOVERY_ATTEMPT'; payload: { key: string; timestamp: number } }
  | { type: 'CLEAR_ERRORS'; payload?: 'all' | 'recent' | 'boundary' | 'network' | 'api' }
  | { type: 'CLEAR_OLD_ERRORS'; payload: number }; // Clear errors older than timestamp

// Initial state
const initialErrorPreferences: ErrorPreferences = {
  showTechnicalDetails: false,
  autoRetryFailedRequests: true,
  maxRetryAttempts: 3,
  retryDelay: 1000,
  persistErrorLogs: true,
  reportCriticalErrors: true,
  showErrorNotifications: true,
};

const initialState: ErrorState = {
  globalError: null,
  recentErrors: [],
  boundaryErrors: [],
  networkErrors: [],
  apiErrors: [],
  errorPreferences: initialErrorPreferences,
  recoveryAttempts: {},
  lastRecoveryTime: {},
};

// Helper function to generate unique IDs
const generateId = () => `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Reducer for error state management
function errorReducer(state: ErrorState, action: ErrorAction): ErrorState {
  switch (action.type) {
    case 'SET_GLOBAL_ERROR':
      return {
        ...state,
        globalError: action.payload,
      };
    
    case 'ADD_ERROR': {
      const newError: ErrorEntry = {
        ...action.payload,
        id: generateId(),
        timestamp: Date.now(),
      };
      
      // Keep only last 50 errors to prevent memory issues
      const recentErrors = [newError, ...state.recentErrors].slice(0, 50);
      
      return {
        ...state,
        recentErrors,
      };
    }
    
    case 'MARK_ERROR_HANDLED': {
      const recentErrors = state.recentErrors.map(error =>
        error.id === action.payload ? { ...error, handled: true } : error
      );
      
      return {
        ...state,
        recentErrors,
      };
    }
    
    case 'ADD_BOUNDARY_ERROR': {
      const newBoundaryError: BoundaryError = {
        ...action.payload,
        id: generateId(),
        timestamp: Date.now(),
      };
      
      // Keep only last 20 boundary errors
      const boundaryErrors = [newBoundaryError, ...state.boundaryErrors].slice(0, 20);
      
      return {
        ...state,
        boundaryErrors,
      };
    }
    
    case 'MARK_BOUNDARY_RECOVERED': {
      const boundaryErrors = state.boundaryErrors.map(error =>
        error.id === action.payload ? { ...error, recovered: true } : error
      );
      
      return {
        ...state,
        boundaryErrors,
      };
    }
    
    case 'ADD_NETWORK_ERROR': {
      const newNetworkError: NetworkError = {
        ...action.payload,
        id: generateId(),
        timestamp: Date.now(),
      };
      
      // Keep only last 30 network errors
      const networkErrors = [newNetworkError, ...state.networkErrors].slice(0, 30);
      
      return {
        ...state,
        networkErrors,
      };
    }
    
    case 'ADD_API_ERROR': {
      const newApiError: ApiError = {
        ...action.payload,
        id: generateId(),
        timestamp: Date.now(),
      };
      
      // Keep only last 30 API errors
      const apiErrors = [newApiError, ...state.apiErrors].slice(0, 30);
      
      return {
        ...state,
        apiErrors,
      };
    }
    
    case 'UPDATE_PREFERENCES':
      return {
        ...state,
        errorPreferences: {
          ...state.errorPreferences,
          ...action.payload,
        },
      };
    
    case 'INCREMENT_RECOVERY_ATTEMPT': {
      const { key, timestamp } = action.payload;
      const currentAttempts = state.recoveryAttempts[key] || 0;
      
      return {
        ...state,
        recoveryAttempts: {
          ...state.recoveryAttempts,
          [key]: currentAttempts + 1,
        },
        lastRecoveryTime: {
          ...state.lastRecoveryTime,
          [key]: timestamp,
        },
      };
    }
    
    case 'CLEAR_ERRORS': {
      const clearType = action.payload || 'all';
      
      if (clearType === 'all') {
        return {
          ...state,
          globalError: null,
          recentErrors: [],
          boundaryErrors: [],
          networkErrors: [],
          apiErrors: [],
          recoveryAttempts: {},
          lastRecoveryTime: {},
        };
      }
      
      const updates: Partial<ErrorState> = {};
      
      if (clearType === 'recent') {
        updates.recentErrors = [];
      } else if (clearType === 'boundary') {
        updates.boundaryErrors = [];
      } else if (clearType === 'network') {
        updates.networkErrors = [];
      } else if (clearType === 'api') {
        updates.apiErrors = [];
      }
      
      return {
        ...state,
        ...updates,
      };
    }
    
    case 'CLEAR_OLD_ERRORS': {
      const cutoffTime = action.payload;
      
      return {
        ...state,
        recentErrors: state.recentErrors.filter(error => error.timestamp > cutoffTime),
        boundaryErrors: state.boundaryErrors.filter(error => error.timestamp > cutoffTime),
        networkErrors: state.networkErrors.filter(error => error.timestamp > cutoffTime),
        apiErrors: state.apiErrors.filter(error => error.timestamp > cutoffTime),
      };
    }
    
    default:
      return state;
  }
}

// Context creation
export interface ErrorContextType {
  state: ErrorState;
  dispatch: React.Dispatch<ErrorAction>;
  
  // Error reporting
  reportError: (error: Error, context: string, severity?: ErrorEntry['severity']) => void;
  reportGlobalError: (error: Omit<GlobalError, 'id' | 'timestamp'>) => void;
  reportBoundaryError: (error: Error, componentStack: string, errorBoundary: string) => void;
  reportNetworkError: (error: Omit<NetworkError, 'id' | 'timestamp'>) => void;
  reportApiError: (error: Omit<ApiError, 'id' | 'timestamp'>) => void;
  
  // Error handling
  clearGlobalError: () => void;
  clearErrors: (type?: 'all' | 'recent' | 'boundary' | 'network' | 'api') => void;
  markErrorHandled: (errorId: string) => void;
  markBoundaryRecovered: (boundaryId: string) => void;
  
  // Recovery utilities
  attemptRecovery: (key: string) => boolean;
  canRetry: (key: string) => boolean;
  getRetryDelay: (key: string) => number;
  
  // Preferences
  updatePreferences: (preferences: Partial<ErrorPreferences>) => void;
  
  // Utilities
  getErrorSummary: () => {
    total: number;
    critical: number;
    unhandled: number;
    recent: number;
  };
  exportErrorLogs: () => string;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

// Provider component
export interface ErrorProviderProps {
  children: ReactNode;
}

export function ErrorProvider({ children }: ErrorProviderProps) {
  const [state, dispatch] = useReducer(errorReducer, initialState);
  
  // Persist error preferences
  const [, setStoredPreferences] = useLocalStorage('errorPreferences', state.errorPreferences);
  
  // Load persisted preferences on mount
  const [storedPreferences] = useLocalStorage('errorPreferences', initialErrorPreferences);
  
  useEffect(() => {
    dispatch({ type: 'UPDATE_PREFERENCES', payload: storedPreferences });
  }, [storedPreferences]);
  
  // Update stored preferences when state changes
  useEffect(() => {
    setStoredPreferences(state.errorPreferences);
  }, [state.errorPreferences, setStoredPreferences]);
  
  // Clean up old errors periodically (keep last 24 hours)
  useEffect(() => {
    const cleanup = () => {
      const cutoffTime = Date.now() - (24 * 60 * 60 * 1000); // 24 hours ago
      dispatch({ type: 'CLEAR_OLD_ERRORS', payload: cutoffTime });
    };
    
    // Clean up on mount and then every hour
    cleanup();
    const interval = setInterval(cleanup, 60 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  // Error reporting functions
  const reportError = useCallback((error: Error, context: string, severity: ErrorEntry['severity'] = 'medium') => {
    dispatch({
      type: 'ADD_ERROR',
      payload: {
        error,
        context,
        severity,
        handled: false,
        reportedToUser: false,
      },
    });
    
    // Auto-promote to global error if critical
    if (severity === 'critical') {
      reportGlobalError({
        type: 'critical',
        title: 'Critical Error',
        message: error.message,
        details: `Context: ${context}`,
        stackTrace: error.stack,
        source: 'component',
        recoverable: false,
        retryable: false,
      });
    }
  }, []);
  
  const reportGlobalError = useCallback((error: Omit<GlobalError, 'id' | 'timestamp'>) => {
    const globalError: GlobalError = {
      ...error,
      id: generateId(),
      timestamp: Date.now(),
    };
    
    dispatch({ type: 'SET_GLOBAL_ERROR', payload: globalError });
  }, []);
  
  const reportBoundaryError = useCallback((error: Error, componentStack: string, errorBoundary: string) => {
    dispatch({
      type: 'ADD_BOUNDARY_ERROR',
      payload: {
        error,
        componentStack,
        errorBoundary,
        recovered: false,
      },
    });
    
    // Also report as global error
    reportGlobalError({
      type: 'critical',
      title: 'Component Error',
      message: error.message,
      details: `Component: ${errorBoundary}\nStack: ${componentStack}`,
      stackTrace: error.stack,
      source: 'component',
      recoverable: true,
      retryable: false,
    });
  }, [reportGlobalError]);
  
  const reportNetworkError = useCallback((error: Omit<NetworkError, 'id' | 'timestamp'>) => {
    dispatch({ type: 'ADD_NETWORK_ERROR', payload: error });
    
    // Report as global error if not retryable
    if (error.retryCount >= error.maxRetries) {
      reportGlobalError({
        type: 'warning',
        title: 'Network Error',
        message: `Failed to connect to ${error.url}`,
        details: `Status: ${error.status} ${error.statusText}\nRetries: ${error.retryCount}/${error.maxRetries}`,
        source: 'network',
        recoverable: true,
        retryable: true,
      });
    }
  }, [reportGlobalError]);
  
  const reportApiError = useCallback((error: Omit<ApiError, 'id' | 'timestamp'>) => {
    dispatch({ type: 'ADD_API_ERROR', payload: error });
    
    // Report as global error if not recoverable
    if (!error.recoverable) {
      reportGlobalError({
        type: error.statusCode >= 500 ? 'critical' : 'warning',
        title: 'API Error',
        message: error.userMessage,
        details: `Endpoint: ${error.endpoint}\nStatus: ${error.statusCode}\nTechnical: ${error.technicalMessage}`,
        source: 'api',
        recoverable: error.recoverable,
        retryable: error.statusCode >= 500,
      });
    }
  }, [reportGlobalError]);
  
  // Error handling functions
  const clearGlobalError = useCallback(() => {
    dispatch({ type: 'SET_GLOBAL_ERROR', payload: null });
  }, []);
  
  const clearErrors = useCallback((type?: 'all' | 'recent' | 'boundary' | 'network' | 'api') => {
    dispatch({ type: 'CLEAR_ERRORS', payload: type });
  }, []);
  
  const markErrorHandled = useCallback((errorId: string) => {
    dispatch({ type: 'MARK_ERROR_HANDLED', payload: errorId });
  }, []);
  
  const markBoundaryRecovered = useCallback((boundaryId: string) => {
    dispatch({ type: 'MARK_BOUNDARY_RECOVERED', payload: boundaryId });
  }, []);
  
  // Recovery utilities
  const attemptRecovery = useCallback((key: string): boolean => {
    const attempts = state.recoveryAttempts[key] || 0;
    const maxAttempts = state.errorPreferences.maxRetryAttempts;
    
    if (attempts >= maxAttempts) {
      return false;
    }
    
    dispatch({
      type: 'INCREMENT_RECOVERY_ATTEMPT',
      payload: { key, timestamp: Date.now() },
    });
    
    return true;
  }, [state.recoveryAttempts, state.errorPreferences.maxRetryAttempts]);
  
  const canRetry = useCallback((key: string): boolean => {
    const attempts = state.recoveryAttempts[key] || 0;
    const maxAttempts = state.errorPreferences.maxRetryAttempts;
    const lastAttempt = state.lastRecoveryTime[key] || 0;
    const retryDelay = state.errorPreferences.retryDelay;
    
    return (
      attempts < maxAttempts &&
      Date.now() - lastAttempt >= retryDelay
    );
  }, [state.recoveryAttempts, state.lastRecoveryTime, state.errorPreferences]);
  
  const getRetryDelay = useCallback((key: string): number => {
    const attempts = state.recoveryAttempts[key] || 0;
    const baseDelay = state.errorPreferences.retryDelay;
    
    // Exponential backoff: delay * 2^attempts
    return baseDelay * Math.pow(2, attempts);
  }, [state.recoveryAttempts, state.errorPreferences.retryDelay]);
  
  // Preferences
  const updatePreferences = useCallback((preferences: Partial<ErrorPreferences>) => {
    dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences });
  }, []);
  
  // Utilities
  const getErrorSummary = useCallback(() => {
    const total = state.recentErrors.length + state.boundaryErrors.length + state.networkErrors.length + state.apiErrors.length;
    const critical = [
      ...state.recentErrors.filter(e => e.severity === 'critical'),
      ...state.boundaryErrors,
    ].length;
    const unhandled = state.recentErrors.filter(e => !e.handled).length;
    const recent = state.recentErrors.filter(e => Date.now() - e.timestamp < 60000).length; // Last minute
    
    return { total, critical, unhandled, recent };
  }, [state.recentErrors, state.boundaryErrors, state.networkErrors, state.apiErrors]);
  
  const exportErrorLogs = useCallback((): string => {
    const logs = {
      timestamp: new Date().toISOString(),
      globalError: state.globalError,
      recentErrors: state.recentErrors.map(e => ({
        ...e,
        error: {
          name: e.error.name,
          message: e.error.message,
          stack: e.error.stack,
        },
      })),
      boundaryErrors: state.boundaryErrors.map(e => ({
        ...e,
        error: {
          name: e.error.name,
          message: e.error.message,
          stack: e.error.stack,
        },
      })),
      networkErrors: state.networkErrors,
      apiErrors: state.apiErrors,
      recoveryAttempts: state.recoveryAttempts,
      lastRecoveryTime: state.lastRecoveryTime,
    };
    
    return JSON.stringify(logs, null, 2);
  }, [state]);
  
  const contextValue: ErrorContextType = {
    state,
    dispatch,
    reportError,
    reportGlobalError,
    reportBoundaryError,
    reportNetworkError,
    reportApiError,
    clearGlobalError,
    clearErrors,
    markErrorHandled,
    markBoundaryRecovered,
    attemptRecovery,
    canRetry,
    getRetryDelay,
    updatePreferences,
    getErrorSummary,
    exportErrorLogs,
  };
  
  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
    </ErrorContext.Provider>
  );
}

// Hook to use the ErrorContext
export function useErrorContext() {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useErrorContext must be used within an ErrorProvider');
  }
  return context;
}

// Additional hooks for specific error functionality
export function useErrorReporting() {
  const {
    reportError,
    reportGlobalError,
    reportBoundaryError,
    reportNetworkError,
    reportApiError,
  } = useErrorContext();
  
  return {
    reportError,
    reportGlobalError,
    reportBoundaryError,
    reportNetworkError,
    reportApiError,
  };
}

export function useErrorRecovery() {
  const {
    attemptRecovery,
    canRetry,
    getRetryDelay,
    state,
  } = useErrorContext();
  
  return {
    attemptRecovery,
    canRetry,
    getRetryDelay,
    autoRetryEnabled: state.errorPreferences.autoRetryFailedRequests,
    maxRetries: state.errorPreferences.maxRetryAttempts,
  };
}

export function useGlobalError() {
  const { state, clearGlobalError } = useErrorContext();
  
  return {
    globalError: state.globalError,
    clearGlobalError,
    hasError: !!state.globalError,
  };
}

export function useErrorPreferences() {
  const { state, updatePreferences } = useErrorContext();
  
  return {
    preferences: state.errorPreferences,
    updatePreferences,
  };
}