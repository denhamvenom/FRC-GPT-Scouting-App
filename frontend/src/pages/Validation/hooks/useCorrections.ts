// frontend/src/pages/Validation/hooks/useCorrections.ts

import { useState } from 'react';
import { CorrectionSuggestion, TeamMatch, ValidationIssue } from '../types';

export const useCorrections = () => {
  const [suggestions, setSuggestions] = useState<CorrectionSuggestion[]>([]);
  const [corrections, setCorrections] = useState<{ [key: string]: number }>({});
  const [correctionReason, setCorrectionReason] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = async (
    datasetPath: string, 
    issue: TeamMatch | ValidationIssue
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/validate/suggestions?unified_dataset_path=${encodeURIComponent(datasetPath)}&team_number=${issue.team_number}&match_number=${issue.match_number}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch correction suggestions');
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuggestions(data.suggestions || []);
      } else {
        setError(data.message || 'Error fetching suggestions');
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
      setError('Error fetching correction suggestions');
    } finally {
      setLoading(false);
    }
  };

  const applySuggestion = (metric: string, value: number) => {
    setCorrections(prev => ({
      ...prev,
      [metric]: value
    }));
  };

  const updateCorrection = (metric: string, value: number) => {
    setCorrections(prev => ({
      ...prev,
      [metric]: value
    }));
  };

  const removeCorrection = (metric: string) => {
    setCorrections(prev => {
      const updated = { ...prev };
      delete updated[metric];
      return updated;
    });
  };

  const clearCorrections = () => {
    setCorrections({});
    setCorrectionReason('');
    setSuggestions([]);
    setError(null);
  };

  const hasCorrections = Object.keys(corrections).length > 0;

  return {
    suggestions,
    corrections,
    correctionReason,
    loading,
    error,
    hasCorrections,
    setSuggestions,
    setCorrections,
    setCorrectionReason,
    setError,
    fetchSuggestions,
    applySuggestion,
    updateCorrection,
    removeCorrection,
    clearCorrections,
  };
};