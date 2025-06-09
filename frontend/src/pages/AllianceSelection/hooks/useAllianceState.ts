/**
 * Hook for alliance state management (advance round, reset)
 */

import { useCallback } from 'react';
import { 
  SelectionState, 
  UseAllianceStateReturn,
  ApiResponse
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

interface UseAllianceStateProps {
  selection: SelectionState | null;
  onSuccess: (message: string) => void;
  onError: (error: string) => void;
  onSelectionUpdate: () => Promise<void>;
  onClearSelections: () => void;
}

export const useAllianceState = ({
  selection,
  onSuccess,
  onError,
  onSelectionUpdate,
  onClearSelections
}: UseAllianceStateProps): UseAllianceStateReturn => {

  const advanceToNextRound = useCallback(async () => {
    if (!selection) return;

    try {
      const response = await fetch(`${API_BASE_URL}/alliance/selection/${selection.id}/next-round`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData: ApiResponse = await response.json();
        throw new Error(errorData.detail || 'Failed to advance to next round');
      }

      // Clear selections
      onClearSelections();

      // Reload selection data
      await onSelectionUpdate();

      // Show success message
      const message = selection.current_round >= 3
        ? 'Alliance selection completed after backup selections!'
        : `Advanced to round ${selection.current_round + 1}`;
      
      onSuccess(message);

    } catch (err: any) {
      onError('Error advancing to next round: ' + err.message);
      console.error(err);
    }
  }, [selection, onSuccess, onError, onSelectionUpdate, onClearSelections]);

  const resetAllianceSelection = useCallback(async () => {
    if (!selection) return;

    // Confirm before resetting
    if (!window.confirm('Are you sure you want to reset the entire alliance selection? This will clear all captains and selections and start from the beginning.')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/alliance/selection/${selection.id}/reset`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData: ApiResponse = await response.json();
        throw new Error(errorData.detail || 'Failed to reset alliance selection');
      }

      // Clear selections
      onClearSelections();

      // Reload selection data
      await onSelectionUpdate();

      // Show success message
      onSuccess('Alliance selection has been reset to the beginning');

    } catch (err: any) {
      onError('Error resetting alliance selection: ' + err.message);
      console.error(err);
    }
  }, [selection, onSuccess, onError, onSelectionUpdate, onClearSelections]);

  return {
    advanceToNextRound,
    resetAllianceSelection,
  };
};