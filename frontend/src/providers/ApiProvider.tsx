import React, { createContext, useContext, ReactNode, useMemo, useEffect } from 'react';
import { ApiClient } from '../services/ApiClient';
import { AllianceService } from '../services/AllianceService';
import { PicklistService } from '../services/PicklistService';
import { TeamService } from '../services/TeamService';
import { EventService } from '../services/EventService';
import { ValidationService } from '../services/ValidationService';
import { DatasetService } from '../services/DatasetService';
import { useErrorContext } from '../context/ErrorContext';
import { useAppContext } from '../context/AppContext';

// Types for API provider
export interface ApiContextType {
  // API client instance
  apiClient: ApiClient;
  
  // Service instances
  allianceService: AllianceService;
  picklistService: PicklistService;
  teamService: TeamService;
  eventService: EventService;
  validationService: ValidationService;
  datasetService: DatasetService;
  
  // Configuration
  baseURL: string;
  timeout: number;
  
  // Status
  isHealthy: boolean;
  lastHealthCheck: number | null;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

// Provider component
export interface ApiProviderProps {
  children: ReactNode;
  baseURL?: string;
  timeout?: number;
  apiClient?: ApiClient; // For testing
}

export function ApiProvider({ 
  children, 
  baseURL = '/api', 
  timeout = 30000,
  apiClient: providedApiClient 
}: ApiProviderProps) {
  const { reportNetworkError, reportApiError } = useErrorContext();
  const { showNotification } = useAppContext();
  
  // Create API client with error handling
  const apiClient = useMemo(() => {
    if (providedApiClient) {
      return providedApiClient;
    }
    
    const client = new ApiClient({
      baseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add request interceptor for logging
    client.addRequestInterceptor(
      (config) => {
        console.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );
    
    // Add response interceptor for error handling
    client.addResponseInterceptor(
      (response) => {
        console.debug(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error);
        
        // Report network errors
        if (error.code === 'ECONNABORTED' || error.code === 'NETWORK_ERROR') {
          reportNetworkError({
            url: error.config?.url || 'unknown',
            method: error.config?.method || 'unknown',
            status: 0,
            statusText: 'Network Error',
            retryCount: 0,
            maxRetries: 3,
          });
        }
        
        // Report API errors
        if (error.response) {
          const { status, data } = error.response;
          const isUserError = status >= 400 && status < 500;
          const isServerError = status >= 500;
          
          reportApiError({
            endpoint: error.config?.url || 'unknown',
            method: error.config?.method || 'unknown',
            requestData: error.config?.data,
            responseData: data,
            statusCode: status,
            errorCode: data?.error_code || data?.code,
            userMessage: data?.message || data?.error || `Request failed with status ${status}`,
            technicalMessage: data?.details || error.message,
            recoverable: isUserError,
          });
          
          // Show notification for server errors
          if (isServerError) {
            showNotification({
              type: 'error',
              title: 'Server Error',
              message: data?.message || 'A server error occurred. Please try again.',
            });
          }
        }
        
        return Promise.reject(error);
      }
    );
    
    return client;
  }, [baseURL, timeout, providedApiClient, reportNetworkError, reportApiError, showNotification]);
  
  // Create service instances
  const services = useMemo(() => {
    return {
      allianceService: new AllianceService(apiClient),
      picklistService: new PicklistService(apiClient),
      teamService: new TeamService(apiClient),
      eventService: new EventService(apiClient),
      validationService: new ValidationService(apiClient),
      datasetService: new DatasetService(apiClient),
    };
  }, [apiClient]);
  
  // Health check state
  const [isHealthy, setIsHealthy] = React.useState(true);
  const [lastHealthCheck, setLastHealthCheck] = React.useState<number | null>(null);
  
  // Perform health check
  const performHealthCheck = React.useCallback(async () => {
    try {
      await apiClient.get('/health');
      setIsHealthy(true);
      setLastHealthCheck(Date.now());
    } catch (error) {
      setIsHealthy(false);
      setLastHealthCheck(Date.now());
      
      // Only show notification if we were previously healthy
      if (isHealthy) {
        showNotification({
          type: 'warning',
          title: 'API Connection Lost',
          message: 'Unable to connect to the server. Some features may not work properly.',
        });
      }
    }
  }, [apiClient, isHealthy, showNotification]);
  
  // Initial health check and periodic monitoring
  useEffect(() => {
    performHealthCheck();
    
    // Check health every 5 minutes
    const interval = setInterval(performHealthCheck, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [performHealthCheck]);
  
  const contextValue: ApiContextType = {
    apiClient,
    ...services,
    baseURL,
    timeout,
    isHealthy,
    lastHealthCheck,
  };
  
  return (
    <ApiContext.Provider value={contextValue}>
      {children}
    </ApiContext.Provider>
  );
}

// Hook to use the ApiContext
export function useApiContext() {
  const context = useContext(ApiContext);
  if (context === undefined) {
    throw new Error('useApiContext must be used within an ApiProvider');
  }
  return context;
}

// Convenience hooks for specific services
export function useAllianceService() {
  const { allianceService } = useApiContext();
  return allianceService;
}

export function usePicklistService() {
  const { picklistService } = useApiContext();
  return picklistService;
}

export function useTeamService() {
  const { teamService } = useApiContext();
  return teamService;
}

export function useEventService() {
  const { eventService } = useApiContext();
  return eventService;
}

export function useValidationService() {
  const { validationService } = useApiContext();
  return validationService;
}

export function useDatasetService() {
  const { datasetService } = useApiContext();
  return datasetService;
}

// Hook for API health monitoring
export function useApiHealth() {
  const { isHealthy, lastHealthCheck, apiClient } = useApiContext();
  
  const checkHealth = React.useCallback(async () => {
    try {
      await apiClient.get('/health');
      return true;
    } catch (error) {
      return false;
    }
  }, [apiClient]);
  
  return {
    isHealthy,
    lastHealthCheck,
    checkHealth,
  };
}