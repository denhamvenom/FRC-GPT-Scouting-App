import { useState, useCallback } from 'react';
import { apiUrl, fetchWithNgrokHeaders } from '../config';

export interface GameLabel {
  label: string;
  category: string;
  description: string;
  data_type: string;
  typical_range: string;
  usage_context: string;
}

interface GameLabelResponse {
  success: boolean;
  message: string;
  labels_count: number;
  labels: GameLabel[];
}

export function useGameLabels() {
  const [labels, setLabels] = useState<GameLabel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const currentYear = new Date().getFullYear();
  
  const loadLabels = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetchWithNgrokHeaders(
        apiUrl(`/api/v1/game-labels/${currentYear}`)
      );
      
      if (!response.ok) {
        // If no labels found (404), that's OK - just start with empty array
        if (response.status === 404) {
          setLabels([]);
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data: GameLabelResponse = await response.json();
      
      if (data.success) {
        setLabels(data.labels || []);
      } else {
        setError(data.message || 'Failed to load labels');
      }
    } catch (err) {
      console.error('Error loading game labels:', err);
      setError(`Failed to load labels: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  }, [currentYear]);
  
  const saveLabels = useCallback(async (labelsToSave: GameLabel[]): Promise<boolean> => {
    setError(null);
    
    try {
      const response = await fetchWithNgrokHeaders(
        apiUrl(`/api/v1/game-labels/${currentYear}`),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ labels: labelsToSave })
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data: GameLabelResponse = await response.json();
      
      if (data.success) {
        setLabels(data.labels || []);
        return true;
      } else {
        setError(data.message || 'Failed to save labels');
        return false;
      }
    } catch (err) {
      console.error('Error saving game labels:', err);
      setError(`Failed to save labels: ${err instanceof Error ? err.message : 'Unknown error'}`);
      return false;
    }
  }, [currentYear]);
  
  const extractLabels = useCallback(async (manualData: any, forceRefresh: boolean = false): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetchWithNgrokHeaders(
        apiUrl('/api/v1/game-labels/extract'),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            manual_data: manualData,
            year: currentYear,
            force_refresh: forceRefresh
          })
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setLabels(data.labels || []);
        return true;
      } else {
        setError(data.error || 'Failed to extract labels');
        return false;
      }
    } catch (err) {
      console.error('Error extracting game labels:', err);
      setError(`Failed to extract labels: ${err instanceof Error ? err.message : 'Unknown error'}`);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [currentYear]);
  
  return {
    labels,
    isLoading,
    error,
    loadLabels,
    saveLabels,
    extractLabels
  };
}