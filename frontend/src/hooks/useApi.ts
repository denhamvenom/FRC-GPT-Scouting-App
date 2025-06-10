/**
 * Generic API hook with error handling and loading states
 */

import { useState, useCallback } from 'react';
import { ApiClientError } from '../services';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: ApiClientError) => void;
  showErrorToast?: boolean;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: ApiClientError | null;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T = any>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiClientError | null>(null);

  const { onSuccess, onError, showErrorToast = true } = options;

  const execute = useCallback(
    async (...args: any[]): Promise<T | null> => {
      setLoading(true);
      setError(null);

      try {
        const result = await apiFunction(...args);
        setData(result);
        
        if (onSuccess) {
          onSuccess(result);
        }
        
        return result;
      } catch (err) {
        const apiError = err instanceof ApiClientError 
          ? err 
          : new ApiClientError({
              message: err instanceof Error ? err.message : 'Unknown error',
            });
        
        setError(apiError);
        
        if (onError) {
          onError(apiError);
        }
        
        if (showErrorToast && typeof window !== 'undefined') {
          // You can integrate with your toast notification system here
          console.error('API Error:', apiError.message);
        }
        
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, onSuccess, onError, showErrorToast]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

/**
 * Hook for API calls that should be executed immediately
 */
export function useApiCall<T = any>(
  apiFunction: (...args: any[]) => Promise<T>,
  deps: any[] = [],
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const api = useApi(apiFunction, options);
  
  // Execute on mount and when dependencies change
  React.useEffect(() => {
    api.execute();
  }, deps);
  
  return api;
}

// Import React for useEffect
import React from 'react';