// frontend/src/pages/Validation/hooks/useValidation.ts

import { useState, useEffect, useCallback } from 'react';
import { useApiContext } from '../../../providers/ApiProvider';
import { 
  ValidationState, 
  ValidationResult, 
  TodoItem, 
  TeamMatch, 
  ValidationIssue,
  ActionMode,
  TabType,
  IgnoreReason,
  CorrectionSuggestion
} from '../types';

export const useValidation = () => {
  // Get API services from context
  const { validationService, datasetService, apiClient } = useApiContext();
  
  // State
  const [datasetPath, setDatasetPath] = useState<string>('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<TabType>('missing');
  const [selectedIssue, setSelectedIssue] = useState<TeamMatch | ValidationIssue | null>(null);
  const [suggestions, setSuggestions] = useState<CorrectionSuggestion[]>([]);
  const [corrections, setCorrections] = useState<{ [key: string]: number }>({});
  const [correctionReason, setCorrectionReason] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [todoList, setTodoList] = useState<TodoItem[]>([]);
  const [virtualScoutPreview, setVirtualScoutPreview] = useState<any>(null);
  const [actionMode, setActionMode] = useState<ActionMode>('none');
  const [ignoreReason, setIgnoreReason] = useState<IgnoreReason>('not_operational');
  const [customReason, setCustomReason] = useState<string>('');

  // Define callback functions BEFORE useEffect that uses them
  const fetchValidationData = useCallback(async (eventKey: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Use POST for enhanced validation with proper request body
      const data = await apiClient.post('/validate/enhanced', {
        event_key: eventKey,
        confidence_threshold: 0.8 // Default confidence threshold
      });
      setValidationResult(data);
    } catch (err) {
      console.error('Error fetching validation data:', err);
      setError('Error loading validation data');
    } finally {
      setLoading(false);
    }
  }, [apiClient]);
  
  const fetchTodoList = useCallback(async (eventKey: string) => {
    try {
      // Use event_key parameter instead of unified_dataset_path
      const data = await apiClient.get('/validate/todo', { 
        params: { event_key: eventKey } 
      });
      if (data.status === 'success') {
        setTodoList(data.todos || []);
      }
    } catch (err) {
      console.error('Error fetching to-do list:', err);
    }
  }, [apiClient]);
  
  const fetchVirtualScoutPreview = useCallback(async () => {
    if (!selectedIssue) return;
    
    setLoading(true);
    try {
      const data = await apiClient.get('/validate/preview-virtual-scout', { 
        params: { 
          event_key: datasetPath, // datasetPath is now the event key
          team_number: selectedIssue.team_number,
          match_key: `${datasetPath}_qm${selectedIssue.match_number}` // Convert match_number to match_key format
        } 
      });
      
      if (data.status === 'success') {
        setVirtualScoutPreview(data.virtual_scout_preview);
      } else {
        setError(data.message || 'Error generating virtual scout preview');
      }
    } catch (err) {
      console.error('Error fetching virtual scout preview:', err);
      setError('Error generating virtual scout preview');
    } finally {
      setLoading(false);
    }
  }, [selectedIssue, datasetPath, apiClient]);

  const handleActionModeChange = (mode: ActionMode) => {
    setActionMode(mode);
    
    // Clear any previous preview
    setVirtualScoutPreview(null);
    
    // If virtual scout is selected, fetch the preview
    if (mode === 'virtual-scout') {
      fetchVirtualScoutPreview();
    }
  };

  const submitCorrection = useCallback(async () => {
    if (!selectedIssue || !datasetPath) return;

    setLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.post('/validate/apply-correction', {
        event_key: datasetPath, // datasetPath is now the event key
        team_number: selectedIssue.team_number,
        match_number: selectedIssue.match_number,
        corrections: corrections,
        reason: correctionReason
      });
      
      if (data.status === 'success') {
        setSuccessMessage('Correction submitted successfully');
        setSelectedIssue(null);
        setCorrections({});
        setCorrectionReason('');
        
        // Refresh validation data
        fetchValidationData(datasetPath);
      } else {
        setError(data.message || 'Error submitting correction');
      }
    } catch (err) {
      console.error('Error submitting correction:', err);
      setError('Error submitting correction');
    } finally {
      setLoading(false);
    }
  }, [selectedIssue, datasetPath, corrections, correctionReason, apiClient, fetchValidationData]);

  const submitIgnoreMatch = useCallback(async () => {
    if (!selectedIssue || !datasetPath) return;

    setLoading(true);
    setError(null);
    
    try {
      const reasonText = ignoreReason === 'other' ? customReason : ignoreReason;
      
      const data = await apiClient.post('/validate/ignore-match', {
        event_key: datasetPath, // datasetPath is now the event key
        team_number: selectedIssue.team_number,
        match_number: selectedIssue.match_number,
        reason_category: ignoreReason,
        reason: reasonText
      });
      
      if (data.status === 'success') {
        setSuccessMessage('Match ignored successfully');
        setSelectedIssue(null);
        setActionMode('none');
        setCustomReason('');
        
        // Refresh validation data
        fetchValidationData(datasetPath);
        fetchTodoList(datasetPath);
      } else {
        setError(data.message || 'Error ignoring match');
      }
    } catch (err) {
      console.error('Error ignoring match:', err);
      setError('Error ignoring match');
    } finally {
      setLoading(false);
    }
  }, [selectedIssue, datasetPath, ignoreReason, customReason, apiClient, fetchValidationData, fetchTodoList]);

  const submitVirtualScout = useCallback(async () => {
    if (!selectedIssue || !datasetPath || !virtualScoutPreview) return;

    setLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.post('/validate/virtual-scout', {
        event_key: datasetPath, // datasetPath is now the event key
        team_number: selectedIssue.team_number,
        match_key: `${datasetPath}_qm${selectedIssue.match_number}`, // Convert match_number to match_key format
        virtual_scout_data: virtualScoutPreview
      });
      
      if (data.status === 'success') {
        setSuccessMessage('Virtual scout data submitted successfully');
        setSelectedIssue(null);
        setVirtualScoutPreview(null);
        setActionMode('none');
        
        // Refresh validation data
        fetchValidationData(datasetPath);
        fetchTodoList(datasetPath);
      } else {
        setError(data.message || 'Error submitting virtual scout');
      }
    } catch (err) {
      console.error('Error submitting virtual scout:', err);
      setError('Error submitting virtual scout');
    } finally {
      setLoading(false);
    }
  }, [selectedIssue, datasetPath, virtualScoutPreview, apiClient, fetchValidationData, fetchTodoList]);

  // Initial data loading when component mounts
  useEffect(() => {
    const fetchEventInfoAndCheckDatasets = async () => {
      try {
        // First, get current event info from setup
        let eventKey = "";
        let yearValue = 2025; // Default

        try {
          const setupData = await apiClient.get('/setup/info');

          if (setupData.status === "success" && setupData.event_key) {
            eventKey = setupData.event_key;
            if (setupData.year) {
              yearValue = setupData.year;
            }
          }
        } catch (setupErr) {
          // Handle setup error gracefully
          console.warn("Error getting setup info:", setupErr);
        }

        // If we couldn't get event info from setup, show an error message
        if (!eventKey) {
          console.warn("Could not retrieve event info from setup");
          setError("No event selected. Please go to Setup page and select an event first.");
          return;
        }

        // Now check for datasets with this event key  
        const data = await datasetService.getDatasetStatus(eventKey);

        if (data.status === 'success' && data.exists) {
          // Store the event key for validation - let backend handle path construction
          setDatasetPath(eventKey);
          fetchValidationData(eventKey);
          fetchTodoList(eventKey);
        } else {
          setError(`No dataset found for event ${eventKey}. Please build the dataset first.`);
        }
      } catch (err) {
        console.error('Error checking datasets:', err);
        setError('Error checking for datasets');
      }
    };

    fetchEventInfoAndCheckDatasets();
  }, [apiClient, datasetService, fetchValidationData, fetchTodoList]);

  return {
    // State
    datasetPath,
    validationResult,
    loading,
    activeTab,
    selectedIssue,
    suggestions,
    corrections,
    correctionReason,
    error,
    successMessage,
    todoList,
    virtualScoutPreview,
    actionMode,
    ignoreReason,
    customReason,
    
    // Actions
    setDatasetPath,
    setValidationResult,
    setLoading,
    setActiveTab,
    setSelectedIssue,
    setSuggestions,
    setCorrections,
    setCorrectionReason,
    setError,
    setSuccessMessage,
    setTodoList,
    setVirtualScoutPreview,
    setActionMode,
    setIgnoreReason,
    setCustomReason,
    fetchValidationData,
    fetchTodoList,
    fetchVirtualScoutPreview,
    handleActionModeChange,
    submitCorrection,
    submitIgnoreMatch,
    submitVirtualScout,
  };
};