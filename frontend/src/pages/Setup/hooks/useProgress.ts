import { useState, useCallback } from 'react';
import type { TocItemType, ProcessedSectionsResult } from '../types';

interface ProgressState {
  selectedTocItems: Map<string, TocItemType>;
  processedSectionsResult: ProcessedSectionsResult | null;
  isProcessingSections: boolean;
  processSectionsError: string | null;
}

export const useProgress = () => {
  const [progressState, setProgressState] = useState<ProgressState>({
    selectedTocItems: new Map(),
    processedSectionsResult: null,
    isProcessingSections: false,
    processSectionsError: null,
  });

  const updateSelectedTocItems = useCallback((items: Map<string, TocItemType>) => {
    setProgressState(prev => ({ ...prev, selectedTocItems: items }));
  }, []);

  const setProcessingStart = useCallback(() => {
    setProgressState(prev => ({
      ...prev,
      isProcessingSections: true,
      processSectionsError: null,
      processedSectionsResult: null
    }));
  }, []);

  const setProcessingError = useCallback((error: string) => {
    setProgressState(prev => ({
      ...prev,
      processSectionsError: error
    }));
  }, []);

  const setProcessingResult = useCallback((result: ProcessedSectionsResult) => {
    setProgressState(prev => ({
      ...prev,
      processedSectionsResult: result
    }));
  }, []);

  const setProcessingEnd = useCallback(() => {
    setProgressState(prev => ({
      ...prev,
      isProcessingSections: false
    }));
  }, []);

  const resetProgress = useCallback(() => {
    setProgressState({
      selectedTocItems: new Map(),
      processedSectionsResult: null,
      isProcessingSections: false,
      processSectionsError: null,
    });
  }, []);

  return {
    ...progressState,
    updateSelectedTocItems,
    setProcessingStart,
    setProcessingError,
    setProcessingResult,
    setProcessingEnd,
    resetProgress
  };
};