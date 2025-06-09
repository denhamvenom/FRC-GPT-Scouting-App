// frontend/src/pages/PicklistNew/hooks/usePagination.ts

import { useState, useCallback } from 'react';
import { UsePagination, PaginationState } from '../types';

export const usePagination = (initialTeamsPerPage: number = 10): UsePagination => {
  const [state, setState] = useState<PaginationState>({
    currentPage: 1,
    teamsPerPage: initialTeamsPerPage,
    totalPages: 1,
  });

  const setCurrentPage = useCallback((page: number) => {
    setState(prev => ({
      ...prev,
      currentPage: Math.max(1, Math.min(page, prev.totalPages)),
    }));
  }, []);

  const setTeamsPerPage = useCallback((teamsPerPage: number) => {
    setState(prev => {
      // Calculate new current page to maintain visible content
      const firstTeamOnCurrentPage = (prev.currentPage - 1) * prev.teamsPerPage + 1;
      const newPage = Math.ceil(firstTeamOnCurrentPage / teamsPerPage);
      const newTotalPages = Math.ceil((prev.totalPages * prev.teamsPerPage) / teamsPerPage);
      
      return {
        ...prev,
        teamsPerPage,
        currentPage: Math.max(1, Math.min(newPage, newTotalPages)),
        totalPages: newTotalPages,
      };
    });
  }, []);

  const updateTotalPages = useCallback((totalTeams: number) => {
    setState(prev => {
      const newTotalPages = Math.ceil(totalTeams / prev.teamsPerPage);
      return {
        ...prev,
        totalPages: Math.max(1, newTotalPages),
        currentPage: Math.min(prev.currentPage, newTotalPages),
      };
    });
  }, []);

  const resetToFirstPage = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentPage: 1,
    }));
  }, []);

  return {
    state,
    actions: {
      setCurrentPage,
      setTeamsPerPage,
      updateTotalPages,
      resetToFirstPage,
    },
  };
};