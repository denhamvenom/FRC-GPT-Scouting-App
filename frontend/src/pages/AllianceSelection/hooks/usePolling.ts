/**
 * Hook for polling mechanism to keep alliance selection up to date
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { UsePollingReturn } from '../types';

interface UsePollingProps {
  onPoll: () => Promise<void>;
  enabled?: boolean;
}

export const usePolling = ({ 
  onPoll, 
  enabled = true 
}: UsePollingProps): UsePollingReturn => {
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startPolling = useCallback((interval: number = 5000) => {
    if (!enabled || isPolling) return;

    setIsPolling(true);
    
    intervalRef.current = setInterval(async () => {
      try {
        await onPoll();
      } catch (error) {
        console.error('Polling error:', error);
        // Continue polling even if there's an error
      }
    }, interval);
  }, [enabled, isPolling, onPoll]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Auto-stop polling if disabled
  useEffect(() => {
    if (!enabled && isPolling) {
      stopPolling();
    }
  }, [enabled, isPolling, stopPolling]);

  return {
    isPolling,
    startPolling,
    stopPolling,
  };
};