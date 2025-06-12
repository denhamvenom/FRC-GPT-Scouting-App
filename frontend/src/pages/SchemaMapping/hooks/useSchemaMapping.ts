import { useState, useEffect, useCallback } from 'react';
import { useApiContext } from '../../../providers/ApiProvider';
import type { SchemaMappingState, CriticalFieldsConfig, SchemaResponse, VariablesResponse } from '../types';
import { DEFAULT_CRITICAL_MAPPINGS } from '../types';

const initialState: SchemaMappingState = {
  headers: [],
  mapping: {},
  suggestedVariables: [],
  criticalMappings: DEFAULT_CRITICAL_MAPPINGS,
  loading: true,
  error: null,
  validationMessage: null,
};

export const useSchemaMapping = () => {
  const [state, setState] = useState<SchemaMappingState>(initialState);
  
  // Get API services from context
  const { apiClient } = useApiContext();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // First, fetch schema headers
      const schemaData: SchemaResponse = await apiClient.get('/schema/learn');
      
      if (schemaData.status === "success") {
        setState(prev => ({
          ...prev,
          headers: schemaData.headers,
          mapping: schemaData.mapping
        }));
        
        // Check for critical field mappings
        const newCriticalMappings: CriticalFieldsConfig = { ...DEFAULT_CRITICAL_MAPPINGS };
        
        // Find team_number mapping
        for (const [header, value] of Object.entries(schemaData.mapping)) {
          if (value === "team_number") {
            newCriticalMappings.team_number = header;
          }
          // Find match_number or qual_number mapping
          if (value === "match_number" || value === "qual_number") {
            newCriticalMappings.match_number = header;
          }
        }
        
        setState(prev => ({
          ...prev,
          criticalMappings: newCriticalMappings
        }));
      } else {
        setState(prev => ({
          ...prev,
          error: "Failed to load schema headers"
        }));
      }
      
      // Then fetch variable suggestions from the prompt builder
      try {
        const promptData: VariablesResponse = await apiClient.get('/prompt-builder/variables');
        
        if (promptData.status === "success") {
          setState(prev => ({
            ...prev,
            suggestedVariables: promptData.suggested_variables || []
          }));
        }
      } catch (promptErr) {
        console.log("No suggested variables available yet");
      }
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: "Error connecting to server"
      }));
      console.error(err);
    } finally {
      setState(prev => ({
        ...prev,
        loading: false
      }));
    }
  };

  // Handle critical field mapping changes
  const handleCriticalFieldChange = useCallback((fieldType: string, header: string, value: string) => {
    // Update the main mapping
    setState(prev => ({
      ...prev,
      mapping: {
        ...prev.mapping,
        [header]: value
      }
    }));
    
    // Update the critical mappings tracker
    if (fieldType === "team_number") {
      setState(prev => ({
        ...prev,
        criticalMappings: {
          ...prev.criticalMappings,
          team_number: header
        }
      }));
    } else if (fieldType === "match_number") {
      setState(prev => ({
        ...prev,
        criticalMappings: {
          ...prev.criticalMappings,
          match_number: header
        }
      }));
    }
  }, []);

  const handleChange = useCallback((header: string, value: string) => {
    setState(prev => {
      const newMapping = {
        ...prev.mapping,
        [header]: value
      };

      const newCriticalMappings = { ...prev.criticalMappings };

      // If this is setting a critical field, update our tracker
      if (value === "team_number") {
        newCriticalMappings.team_number = header;
      } else if (value === "match_number" || value === "qual_number") {
        newCriticalMappings.match_number = header;
      }
      
      // If this field was previously set as a critical field, but now is changing
      if (header === prev.criticalMappings.team_number && value !== "team_number") {
        newCriticalMappings.team_number = null;
      } else if (header === prev.criticalMappings.match_number && 
                value !== "match_number" && value !== "qual_number") {
        newCriticalMappings.match_number = null;
      }

      return {
        ...prev,
        mapping: newMapping,
        criticalMappings: newCriticalMappings
      };
    });
  }, []);

  const validateCriticalFields = useCallback(() => {
    const missingFields = [];
    
    if (!state.criticalMappings.team_number) {
      missingFields.push("Team Number");
    }
    
    if (!state.criticalMappings.match_number) {
      missingFields.push("Match Number/Qual Number");
    }
    
    if (missingFields.length > 0) {
      setState(prev => ({
        ...prev,
        validationMessage: `Warning: Missing required fields: ${missingFields.join(", ")}`
      }));
      return false;
    }
    
    setState(prev => ({
      ...prev,
      validationMessage: null
    }));
    return true;
  }, [state.criticalMappings]);

  const handleSave = async () => {
    if (!validateCriticalFields()) {
      const proceed = window.confirm("Missing critical field mappings may cause data validation issues. Do you want to proceed anyway?");
      if (!proceed) return;
    }
    
    try {
      await apiClient.post('/schema/save', state.mapping);
      alert("Schema saved successfully.");
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: "Error connecting to server"
      }));
      console.error(err);
    }
  };

  const clearCriticalMapping = useCallback((fieldType: string) => {
    setState(prev => ({
      ...prev,
      criticalMappings: {
        ...prev.criticalMappings,
        [fieldType]: null
      }
    }));
  }, []);

  return {
    state,
    actions: {
      handleCriticalFieldChange,
      handleChange,
      handleSave,
      clearCriticalMapping,
      validateCriticalFields
    }
  };
};