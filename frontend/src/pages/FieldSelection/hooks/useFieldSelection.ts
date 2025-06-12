// frontend/src/pages/FieldSelection/hooks/useFieldSelection.ts

import { useState, useEffect } from 'react';
import { 
  FieldMapping, 
  CriticalFieldMappings, 
  StatboticsField,
  SheetConfig,
  CRITICAL_FIELDS,
  FIELD_CATEGORIES
} from '../types';
import { autoCategorizeField } from '../utils';
import { datasetService } from '../../../services/DatasetService';

export const useFieldSelection = () => {
  // Headers from different scouting spreadsheets
  const [scoutingHeaders, setScoutingHeaders] = useState<string[]>([]);
  const [superscoutingHeaders, setSuperscoutingHeaders] = useState<string[]>([]);
  const [pitScoutingHeaders, setPitScoutingHeaders] = useState<string[]>([]);

  // Field categorization
  const [selectedFields, setSelectedFields] = useState<FieldMapping>({});

  // Updated to support multiple fields per critical category
  const [criticalFieldMappings, setCriticalFieldMappings] = useState<CriticalFieldMappings>({
    team_number: [],
    match_number: []
  });

  // UI Category tabs state
  const [activeCategory, setActiveCategory] = useState<string>('match');

  // UI state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);
  const [year, setYear] = useState<number>(2025);
  const [currentEventKey, setCurrentEventKey] = useState<string | null>(null);

  // Statbotics integration
  const [statboticsFields, setStatboticsFields] = useState<StatboticsField[]>([]);
  const [selectedStatboticsFields, setSelectedStatboticsFields] = useState<string[]>([]);
  const [enableStatbotics, setEnableStatbotics] = useState<boolean>(true);

  // Fetch headers from Google Sheets
  const fetchHeaders = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // First, get the active sheet configuration from setup
      const setupResponse = await fetch('/api/setup/info');
      let sheetConfig: SheetConfig | null = null;

      if (setupResponse.ok) {
        const setupData = await setupResponse.json();

        if (setupData.status === 'success' && setupData.sheet_config) {
          sheetConfig = setupData.sheet_config;

          // Also get year and event key if available
          if (setupData.year) {
            setYear(setupData.year);
          }
          if (setupData.event_key) {
            setCurrentEventKey(setupData.event_key);
          }
        }
      }

      if (!sheetConfig?.spreadsheet_id) {
        setError("No valid sheet configuration found. Please return to Setup page and configure your sheets.");
        setIsLoading(false);
        return;
      }

      // Get the detailed configuration including tab names
      let matchScoutingTab = 'Scouting';
      let superScoutingTab = 'SuperScouting';
      let pitScoutingTab = 'PitScouting';

      if (sheetConfig.id) {
        const configResponse = await fetch(`/api/sheet-config/${sheetConfig.id}`);

        if (configResponse.ok) {
          const configData = await configResponse.json();
          if (configData.status === 'success' && configData.configuration) {
            const config = configData.configuration;
            matchScoutingTab = config.match_scouting_sheet || 'Scouting';
            superScoutingTab = config.super_scouting_sheet || 'SuperScouting';
            pitScoutingTab = config.pit_scouting_sheet || 'PitScouting';
          }
        }
      }

      // Get available tabs from the sheet
      const availableTabs = await getAvailableTabs(sheetConfig);

      // Fetch headers for each available tab
      const headerPromises = [];

      if (availableTabs.includes(matchScoutingTab)) {
        headerPromises.push(
          fetchSheetHeaders(sheetConfig.spreadsheet_id, matchScoutingTab).then(headers => {
            setScoutingHeaders(headers);
          })
        );
      }

      if (availableTabs.includes(superScoutingTab)) {
        headerPromises.push(
          fetchSheetHeaders(sheetConfig.spreadsheet_id, superScoutingTab).then(headers => {
            setSuperscoutingHeaders(headers);
          })
        );
      }

      if (availableTabs.includes(pitScoutingTab)) {
        headerPromises.push(
          fetchSheetHeaders(sheetConfig.spreadsheet_id, pitScoutingTab).then(headers => {
            setPitScoutingHeaders(headers);
          })
        );
      }

      await Promise.all(headerPromises);

    } catch (err) {
      console.error('Error fetching headers:', err);
      setError('Error loading sheet headers');
    } finally {
      setIsLoading(false);
    }
  };

  // Get available tabs from the sheet
  const getAvailableTabs = async (sheetConfig: SheetConfig): Promise<string[]> => {
    const endpoints = [
      `/api/sheets/sheets?spreadsheet_id=${encodeURIComponent(sheetConfig.spreadsheet_id)}`,
      `/api/sheet-config/available-sheets?spreadsheet_id=${sheetConfig.spreadsheet_id}`,
      `/api/sheets/available-tabs?spreadsheet_id=${sheetConfig.spreadsheet_id}`
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(endpoint);
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            return data.sheet_names || data.sheets || [];
          }
        }
      } catch (err) {
        console.error(`Error fetching from ${endpoint}:`, err);
      }
    }

    return [];
  };

  // Fetch headers for a specific sheet
  const fetchSheetHeaders = async (spreadsheetId: string, sheetName: string): Promise<string[]> => {
    try {
      const response = await fetch(
        `/api/sheets/headers?spreadsheet_id=${encodeURIComponent(spreadsheetId)}&sheet_name=${encodeURIComponent(sheetName)}`
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          return data.headers || [];
        }
      }
    } catch (err) {
      console.error(`Error fetching headers for ${sheetName}:`, err);
    }
    
    return [];
  };

  // Fetch Statbotics fields
  const fetchStatboticsFields = async () => {
    try {
      const response = await fetch(`/api/field-selection/statbotics-fields?year=${year}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setStatboticsFields(data.fields || []);
        }
      }
    } catch (err) {
      console.error('Error fetching Statbotics fields:', err);
    }
  };

  // Auto-categorize all fields
  const autoCategorizeFields = () => {
    const newSelectedFields: FieldMapping = {};
    const newCriticalMappings: CriticalFieldMappings = {
      team_number: [],
      match_number: []
    };

    // Process all headers
    const allHeaders = [
      ...scoutingHeaders,
      ...superscoutingHeaders,
      ...pitScoutingHeaders
    ];

    allHeaders.forEach(header => {
      const category = autoCategorizeField(header);
      newSelectedFields[header] = category;

      // Check for critical field mappings
      CRITICAL_FIELDS.forEach(criticalField => {
        if (criticalField.requiredPattern.test(header)) {
          if (criticalField.key === 'team_number') {
            newCriticalMappings.team_number.push(header);
          } else if (criticalField.key === 'match_number') {
            newCriticalMappings.match_number.push(header);
          }
        }
      });
    });

    setSelectedFields(newSelectedFields);
    setCriticalFieldMappings(newCriticalMappings);
    setSuccessMessage('Fields automatically categorized!');
  };

  // Validate field selections
  const validateSelections = (): boolean => {
    const warnings: string[] = [];

    // Check critical fields
    if (!criticalFieldMappings?.team_number || criticalFieldMappings.team_number.length === 0) {
      warnings.push('No team number field selected');
    }
    if (!criticalFieldMappings?.match_number || criticalFieldMappings.match_number.length === 0) {
      warnings.push('No match number field selected');
    }

    // Check if any fields are categorized
    const categorizedFields = Object.values(selectedFields).filter(cat => cat !== 'other');
    if (categorizedFields.length === 0) {
      warnings.push('No fields have been categorized');
    }

    if (warnings.length > 0) {
      setValidationWarning(warnings.join(', '));
      return false;
    }

    setValidationWarning(null);
    return true;
  };

  // Save field selections
  const saveFieldSelections = async () => {
    if (!validateSelections()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/field-selection/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          year: year,
          field_selections: selectedFields,
          critical_mappings: criticalFieldMappings,
          statbotics_fields: enableStatbotics ? selectedStatboticsFields : [],
          enable_statbotics: enableStatbotics
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setSuccessMessage('Field selections saved successfully!');
        } else {
          setError(data.message || 'Error saving field selections');
        }
      } else {
        setError('Failed to save field selections');
      }
    } catch (err) {
      console.error('Error saving field selections:', err);
      setError('Error saving field selections');
    } finally {
      setIsLoading(false);
    }
  };

  // Save field selections and trigger dataset building for validation workflow
  const saveFieldSelectionsAndBuildDataset = async () => {
    if (!validateSelections()) {
      return false;
    }

    if (!currentEventKey) {
      setError('No event key found. Please ensure Setup is completed first.');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      // First save the field selections
      const saveResponse = await fetch('/api/field-selection/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          year: year,
          field_selections: selectedFields,
          critical_mappings: criticalFieldMappings,
          statbotics_fields: enableStatbotics ? selectedStatboticsFields : [],
          enable_statbotics: enableStatbotics
        }),
      });

      if (!saveResponse.ok) {
        setError('Failed to save field selections');
        return false;
      }

      const saveData = await saveResponse.json();
      if (saveData.status !== 'success') {
        setError(saveData.message || 'Error saving field selections');
        return false;
      }

      // Then trigger dataset building with the field mappings
      const buildResponse = await datasetService.buildDataset({
        event_key: currentEventKey,
        force_rebuild: true,
        field_mappings: selectedFields
      });

      if (buildResponse.status === 'pending' || buildResponse.status === 'in_progress') {
        setSuccessMessage('Field selections saved and dataset building started!');
        return true;
      } else {
        setError('Field selections saved but dataset building failed');
        return false;
      }
    } catch (err) {
      console.error('Error saving field selections and building dataset:', err);
      setError('Error saving field selections and building dataset');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Load existing field selections
  const loadFieldSelections = async () => {
    try {
      const response = await fetch(`/api/field-selection/load?year=${year}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          // The backend returns field_selections directly as the field mappings
          if (data.field_selections) {
            setSelectedFields(data.field_selections);
          }
          // Critical mappings are returned as critical_mappings
          if (data.critical_mappings) {
            // Ensure critical_mappings has the correct structure
            setCriticalFieldMappings({
              team_number: data.critical_mappings?.team_number || [],
              match_number: data.critical_mappings?.match_number || []
            });
          }
          // Note: Statbotics fields are not currently saved/loaded by the backend
          // They would need to be stored and returned separately
        }
      }
    } catch (err) {
      console.error('Error loading field selections:', err);
    }
  };

  // Initialize
  useEffect(() => {
    fetchHeaders();
    fetchStatboticsFields();
    loadFieldSelections();
  }, [year]);

  return {
    // State
    scoutingHeaders,
    superscoutingHeaders,
    pitScoutingHeaders,
    selectedFields,
    criticalFieldMappings,
    activeCategory,
    isLoading,
    error,
    successMessage,
    validationWarning,
    year,
    statboticsFields,
    selectedStatboticsFields,
    enableStatbotics,

    // Actions
    setScoutingHeaders,
    setSuperscoutingHeaders,
    setPitScoutingHeaders,
    setSelectedFields,
    setCriticalFieldMappings,
    setActiveCategory,
    setIsLoading,
    setError,
    setSuccessMessage,
    setValidationWarning,
    setYear,
    setStatboticsFields,
    setSelectedStatboticsFields,
    setEnableStatbotics,
    fetchHeaders,
    fetchStatboticsFields,
    saveFieldSelections,
    saveFieldSelectionsAndBuildDataset,
    autoCategorizeFields,
    validateSelections,
    loadFieldSelections,
  };
};