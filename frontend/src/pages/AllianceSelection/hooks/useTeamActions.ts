/**
 * Hook for team action management (captain, accept, decline, remove)
 */

import { useState, useCallback } from 'react';
import { 
  TeamAction, 
  TeamActionRequest, 
  SelectionState, 
  UseTeamActionsReturn,
  ApiResponse
} from '../types';
import { isTeamSelectable, canBeCaptain } from '../utils';

// Removed hardcoded API_BASE_URL - now using centralized API client

interface UseTeamActionsProps {
  selection: SelectionState | null;
  onSuccess: (message: string) => void;
  onError: (error: string) => void;
  onSelectionUpdate: () => Promise<void>;
}

export const useTeamActions = ({
  selection,
  onSuccess,
  onError,
  onSelectionUpdate
}: UseTeamActionsProps): UseTeamActionsReturn => {
  // State
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const [selectedAlliance, setSelectedAlliance] = useState<number | null>(null);
  const [action, setAction] = useState<TeamAction | null>(null);

  const clearSelections = useCallback(() => {
    setSelectedTeam(null);
    setSelectedAlliance(null);
    setAction(null);
  }, []);

  const performTeamAction = useCallback(async (actionType: TeamAction) => {
    if (!selection || !selectedTeam) return;
    
    try {
      const requestBody: TeamActionRequest = {
        selection_id: selection.id,
        team_number: selectedTeam,
        action: actionType
      };
      
      // Add alliance number for captain and accept actions
      if (actionType === 'captain' || actionType === 'accept') {
        if (!selectedAlliance) {
          onError('Please select an alliance');
          return;
        }
        requestBody.alliance_number = selectedAlliance;
      }
      
      const response = await fetch(`${API_BASE_URL}/alliance/selection/team-action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorData: ApiResponse = await response.json();
        throw new Error(errorData.detail || 'Failed to perform team action');
      }
      
      // Success! Reload selection data
      await onSelectionUpdate();
      
      // Clear selections
      clearSelections();
      
      // Show success message
      const actionMessages = {
        captain: 'is now alliance captain',
        accept: 'accepted the selection',
        decline: 'declined the selection',
        remove: 'has been removed'
      };
      
      onSuccess(`Team ${selectedTeam} ${actionMessages[actionType]}`);
      
    } catch (err: any) {
      onError('Error performing team action: ' + err.message);
      console.error(err);
    }
  }, [selection, selectedTeam, selectedAlliance, onSuccess, onError, onSelectionUpdate, clearSelections]);

  const handleRemoveTeam = useCallback(async (teamNumber: number, allianceNumber: number) => {
    if (!selection) return;

    // Confirm before removing
    if (!window.confirm(`Are you sure you want to remove team ${teamNumber} from alliance ${allianceNumber}?`)) {
      return;
    }

    try {
      const requestBody: TeamActionRequest = {
        selection_id: selection.id,
        team_number: teamNumber,
        action: 'remove',
        alliance_number: allianceNumber
      };

      const response = await fetch(`${API_BASE_URL}/alliance/selection/team-action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData: ApiResponse = await response.json();
        throw new Error(errorData.detail || 'Failed to remove team from alliance');
      }

      // Success! Reload selection data
      await onSelectionUpdate();

      // Show success message
      onSuccess(`Team ${teamNumber} has been removed from alliance ${allianceNumber}`);

    } catch (err: any) {
      onError('Error removing team: ' + err.message);
      console.error(err);
    }
  }, [selection, onSuccess, onError, onSelectionUpdate]);

  // Validation functions
  const isTeamSelectableFunc = useCallback((teamNumber: number): boolean => {
    return isTeamSelectable(teamNumber, selection);
  }, [selection]);

  const canBeCaptainFunc = useCallback((teamNumber: number): boolean => {
    return canBeCaptain(teamNumber, selection);
  }, [selection]);

  return {
    // State
    selectedTeam,
    selectedAlliance,
    action,
    
    // Actions
    setSelectedTeam,
    setSelectedAlliance,
    setAction,
    performTeamAction,
    handleRemoveTeam,
    clearSelections,
    
    // Validation
    canBeCaptain: canBeCaptainFunc,
    isTeamSelectable: isTeamSelectableFunc,
  };
};