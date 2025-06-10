/**
 * API call hook with caching and advanced features
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { ApiClientError } from '../services';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  key: string;
}

interface UseApiCallOptions {
  cacheKey?: string;
  cacheDuration?: number; // in milliseconds
  refetchInterval?: number; // in milliseconds
  onSuccess?: (data: any) => void;
  onError?: (error: ApiClientError) => void;
  enabled?: boolean;
  retry?: number;
  retryDelay?: number;
}

interface UseApiCallReturn<T> {
  data: T | null;
  loading: boolean;
  error: ApiClientError | null;
  refetch: (...args: any[]) => Promise<T | null>;
  invalidateCache: () => void;
  isValidating: boolean;
  isCached: boolean;
}

// Simple in-memory cache
const cache = new Map<string, CacheEntry<any>>();

export function useApiCall<T = any>(
  apiFunction: (...args: any[]) => Promise<T>,
  args: any[] = [],
  options: UseApiCallOptions = {}
): UseApiCallReturn<T> {
  const {
    cacheKey,
    cacheDuration = 5 * 60 * 1000, // 5 minutes default
    refetchInterval,
    onSuccess,
    onError,
    enabled = true,
    retry = 0,
    retryDelay = 1000,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiClientError | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isCached, setIsCached] = useState(false);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const retryCountRef = useRef(0);

  // Generate cache key
  const getCacheKey = useCallback(() => {
    if (cacheKey) return cacheKey;
    return `${apiFunction.name || 'api'}-${JSON.stringify(args)}`;
  }, [apiFunction, args, cacheKey]);

  // Check cache
  const checkCache = useCallback(() => {
    const key = getCacheKey();
    const cached = cache.get(key);
    
    if (cached && Date.now() - cached.timestamp < cacheDuration) {
      setData(cached.data);
      setIsCached(true);
      return cached.data;
    }
    
    setIsCached(false);
    return null;
  }, [getCacheKey, cacheDuration]);

  // Update cache
  const updateCache = useCallback((newData: T) => {
    const key = getCacheKey();
    cache.set(key, {
      data: newData,
      timestamp: Date.now(),
      key,
    });
  }, [getCacheKey]);

  // Execute API call
  const execute = useCallback(
    async (...callArgs: any[]): Promise<T | null> => {
      if (!mountedRef.current) return null;

      // Use provided args or fall back to hook args
      const finalArgs = callArgs.length > 0 ? callArgs : args;

      // Check cache first
      const cachedData = checkCache();
      if (cachedData && !isValidating) {
        return cachedData;
      }

      setLoading(!isCached);
      setIsValidating(true);
      setError(null);
      retryCountRef.current = 0;

      const attemptCall = async (): Promise<T | null> => {
        try {
          const result = await apiFunction(...finalArgs);
          
          if (!mountedRef.current) return null;
          
          setData(result);
          updateCache(result);
          setIsCached(false);
          
          if (onSuccess) {
            onSuccess(result);
          }
          
          return result;
        } catch (err) {
          if (!mountedRef.current) return null;

          const apiError = err instanceof ApiClientError 
            ? err 
            : new ApiClientError({
                message: err instanceof Error ? err.message : 'Unknown error',
              });

          // Retry logic
          if (retryCountRef.current < retry) {
            retryCountRef.current++;
            await new Promise(resolve => setTimeout(resolve, retryDelay));
            return attemptCall();
          }

          setError(apiError);
          
          if (onError) {
            onError(apiError);
          }
          
          return null;
        } finally {
          if (mountedRef.current) {
            setLoading(false);
            setIsValidating(false);
          }
        }
      };

      return attemptCall();
    },
    [apiFunction, args, checkCache, updateCache, onSuccess, onError, retry, retryDelay, isCached, isValidating]
  );

  // Invalidate cache
  const invalidateCache = useCallback(() => {
    const key = getCacheKey();
    cache.delete(key);
    setIsCached(false);
  }, [getCacheKey]);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      execute();
    }
  }, [enabled, ...args]); // Re-run when args change

  // Set up refetch interval
  useEffect(() => {
    if (refetchInterval && enabled) {
      intervalRef.current = setInterval(() => {
        execute();
      }, refetchInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [refetchInterval, enabled, execute]);

  // Cleanup
  useEffect(() => {
    mountedRef.current = true;
    
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    refetch: execute,
    invalidateCache,
    isValidating,
    isCached,
  };
}

/**
 * Clear all cached data
 */
export function clearApiCache() {
  cache.clear();
}

/**
 * Clear specific cache entries by pattern
 */
export function clearApiCacheByPattern(pattern: string | RegExp) {
  const keys = Array.from(cache.keys());
  keys.forEach(key => {
    if (typeof pattern === 'string' ? key.includes(pattern) : pattern.test(key)) {
      cache.delete(key);
    }
  });
}