// frontend/src/pages/PicklistNew/hooks/usePicklistState.ts

import { useState, useCallback } from 'react';
import { UsePicklistState, PicklistState } from '../types';

export const usePicklistState = (): UsePicklistState => {
  const [state, setState] = useState<PicklistState>({
    isEditing: false,
    showAnalysis: false,
    selectedTeams: [],
    showComparison: false,
  });

  const setIsEditing = useCallback((editing: boolean) => {
    setState(prev => ({ ...prev, isEditing: editing }));
  }, []);

  const setShowAnalysis = useCallback((show: boolean) => {
    setState(prev => ({ ...prev, showAnalysis: show }));
  }, []);

  const toggleTeamSelection = useCallback((teamNumber: number) => {
    setState(prev => {
      const exists = prev.selectedTeams.includes(teamNumber);
      let newSelectedTeams;
      
      if (exists) {
        newSelectedTeams = prev.selectedTeams.filter(n => n !== teamNumber);
      } else if (prev.selectedTeams.length >= 3) {
        // Limit selection to 3 teams for comparison
        return prev;
      } else {
        newSelectedTeams = [...prev.selectedTeams, teamNumber];
      }
      
      return {
        ...prev,
        selectedTeams: newSelectedTeams,
      };
    });
  }, []);

  const setShowComparison = useCallback((show: boolean) => {
    setState(prev => ({ ...prev, showComparison: show }));
  }, []);

  const clearSelection = useCallback(() => {
    setState(prev => ({
      ...prev,
      selectedTeams: [],
      showComparison: false,
    }));
  }, []);

  return {
    state,
    actions: {
      setIsEditing,
      setShowAnalysis,
      toggleTeamSelection,
      setShowComparison,
      clearSelection,
    },
  };
};