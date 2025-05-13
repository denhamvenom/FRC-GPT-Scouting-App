// frontend/src/pages/FieldSelection.tsx

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CategoryTabs, { Category } from '../components/CategoryTabs';

interface FieldCategory {
  key: string;
  label: string;
  description: string;
}

interface CriticalField {
  key: string;
  label: string;
  description: string;
  requiredPattern: RegExp;
}

const CRITICAL_FIELDS: CriticalField[] = [
  { 
    key: 'team_number', 
    label: 'Team Number', 
    description: 'Identifies which team the data belongs to', 
    requiredPattern: /team|number|^\d+$/i
  },
  { 
    key: 'match_number', 
    label: 'Match Number', 
    description: 'Identifies which match the data belongs to',
    requiredPattern: /match|qual/i
  }
];

const FIELD_CATEGORIES: FieldCategory[] = [
  { key: 'team_info', label: 'Team Information', description: 'Basic team identifiers and match metadata' },
  { key: 'auto', label: 'Autonomous', description: 'Robot actions during the autonomous period' },
  { key: 'teleop', label: 'Teleop', description: 'Robot actions during the teleop period' },
  { key: 'endgame', label: 'Endgame', description: 'Robot actions during the endgame period' },
  { key: 'strategy', label: 'Strategy', description: 'Strategic assessment and qualitative observations' },
  { key: 'other', label: 'Other', description: 'Any additional fields that don\'t fit above categories' },
];

// Define UI categories for the tabs
const DATA_CATEGORIES: Category[] = [
  { id: 'match', label: 'Match Scouting', description: 'Data collected during matches', icon: '📊' },
  { id: 'pit', label: 'Pit Scouting', description: 'Data collected during pit visits', icon: '🔧' },
  { id: 'super', label: 'Super Scouting', description: 'Qualitative observations from experienced scouts', icon: '🔍' },
  { id: 'critical', label: 'Critical Fields', description: 'Required fields for proper data validation', icon: '⚠️' },
];

// Enhanced utility function to auto-categorize fields based on patterns
const autoCategorizeField = (header: string): string => {
  // Convert to lowercase for case-insensitive matching
  const headerLower = header.toLowerCase();
  
  // Special handling for robot team numbers in SuperScouting
  if (/robot\s*\d+\s*number/i.test(header)) {
    return 'team_number'; // Identify "Robot X Number" as team number fields
  }
  
  // Check for team number or match number patterns (general)
  if ((/team|^t\d+$|^frc\d+$/i.test(headerLower)) && /number/i.test(headerLower)) {
    return 'team_number';
  }
  
  // Handle match/qual number fields
  if (/qual\s*number/i.test(headerLower)) {
    return 'match_number';
  }
  
  if (/match|qualification|^q\d+$/i.test(headerLower)) {
    return 'match_number';
  }
  
  // Check for autonomous/auto patterns
  if (/auto|autonomous|^a_|^a\.|auton/i.test(headerLower)) {
    return 'auto';
  }
  
  // Check for teleop patterns
  if (/tele|teleop|teleoperated|driver|^t_|^t\./i.test(headerLower)) {
    return 'teleop';
  }
  
  // Check for endgame patterns
  if (/end|endgame|final|climb|parking|docking|hanging/i.test(headerLower)) {
    return 'endgame';
  }
  
  // Check for strategy/subjective patterns
  if (/strat|comment|note|subjective|rating|skill|defense|speed|observ/i.test(headerLower)) {
    return 'strategy';
  }
  
  // Check for team info patterns
  if (/alliance|color|station|position|start/i.test(headerLower)) {
    return 'team_info';
  }
  
  // Default to 'other' if no patterns match
  return 'other';
};

// Helper function to ensure robot group team numbers and match numbers are correctly handled
const processRobotGroups = (groups: { [key: string]: string[] }, selectedFields: { [key: string]: string }) => {
  // Check all fields for potential match numbers
  Object.entries(selectedFields).forEach(([header, _]) => {
    if (/qual\s*number/i.test(header)) {
      selectedFields[header] = 'match_number';
    }
  });
  
  Object.entries(groups).forEach(([_, headers]) => {
    // Find team number field in this robot group
    const teamNumberField = headers.find(header => 
      /robot\s*\d+\s*number/i.test(header)
    );
    
    // If found, make sure it's mapped as team_number
    if (teamNumberField) {
      selectedFields[teamNumberField] = 'team_number';
    }
    
    // Also map match related fields if they exist in groups
    headers.forEach(header => {
      if (/qual\s*number/i.test(header)) {
        selectedFields[header] = 'match_number';
      }
    });
  });
  
  return selectedFields;
};

function FieldSelection() {
  const navigate = useNavigate();
  // Headers from different scouting spreadsheets
  const [scoutingHeaders, setScoutingHeaders] = useState<string[]>([]);
  const [superscoutingHeaders, setSuperscoutingHeaders] = useState<string[]>([]);
  const [pitScoutingHeaders, setPitScoutingHeaders] = useState<string[]>([]);

  // Field categorization
  const [selectedFields, setSelectedFields] = useState<{ [key: string]: string }>({});

  // UI Category tabs state
  const [activeCategory, setActiveCategory] = useState<string>('match');

  // Updated to support multiple fields per critical category
  const [criticalFieldMappings, setCriticalFieldMappings] = useState<{
    team_number: string[],
    match_number: string[]
  }>({
    team_number: [],
    match_number: []
  });

  // Robot grouping for superscouting
  const [robotGroups, setRobotGroups] = useState<{ [key: string]: string[] }>({
    robot_1: [],
    robot_2: [],
    robot_3: []
  });

  // Current robot group being edited
  const [activeRobotGroup, setActiveRobotGroup] = useState<string>('robot_1');

  // Headers that are already assigned to a robot group
  const [assignedHeaders, setAssignedHeaders] = useState<Set<string>>(new Set());

  // UI state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);
  const [gameManualUrl, setGameManualUrl] = useState<string>('');
  const [year, setYear] = useState<number>(2025);

  useEffect(() => {
    // Fetch headers from Google Sheets
    const fetchHeaders = async () => {
      setIsLoading(true);
      try {
        // First, get the active sheet configuration from setup
        const setupResponse = await fetch('http://localhost:8000/api/setup/info');
        let sheetConfig = null;

        console.log("Setup response status:", setupResponse.status);

        if (setupResponse.ok) {
          const setupData = await setupResponse.json();
          console.log("Setup data:", setupData);

          if (setupData.status === 'success' && setupData.sheet_config) {
            sheetConfig = setupData.sheet_config;
            console.log("Using sheet configuration from setup:", sheetConfig);

            // Also get year if available
            if (setupData.year) {
              setYear(setupData.year);
            }
          } else {
            console.warn("No sheet_config found in setup data:", setupData);
          }
        } else {
          console.error("Error fetching setup info:", setupResponse.statusText);
        }

        // Next, get the detailed configuration including tab names
        let matchScoutingTab = 'Scouting';
        let superScoutingTab = 'SuperScouting';
        let pitScoutingTab = 'PitScouting';

        if (sheetConfig && sheetConfig.id) {
          const configResponse = await fetch(`http://localhost:8000/api/sheet-config/${sheetConfig.id}`);

          if (configResponse.ok) {
            const configData = await configResponse.json();
            if (configData.status === 'success' && configData.configuration) {
              const config = configData.configuration;
              // Get the configured tab names
              matchScoutingTab = config.match_scouting_sheet || 'Scouting';
              superScoutingTab = config.super_scouting_sheet || 'SuperScouting';
              pitScoutingTab = config.pit_scouting_sheet || 'PitScouting';

              console.log("Using configured tabs:", {
                match: matchScoutingTab,
                super: superScoutingTab,
                pit: pitScoutingTab
              });
            }
          }
        }

        // Now check what tabs are actually available in the Google Sheet
        // Use the sheetConfig.spreadsheet_id to ensure we're getting tabs from the right spreadsheet
        let spreadsheetId = "";
        if (sheetConfig && sheetConfig.spreadsheet_id) {
          spreadsheetId = sheetConfig.spreadsheet_id;
          console.log("Using spreadsheet ID from config:", spreadsheetId);

          // Add debug log for sheet tab names
          console.log("Sheet tab names from config:", {
            match: sheetConfig.match_scouting_sheet || "not configured",
            pit: sheetConfig.pit_scouting_sheet || "not configured",
            super: sheetConfig.super_scouting_sheet || "not configured"
          });
        } else {
          console.warn("No spreadsheet ID found in configuration");
          setError("No valid sheet configuration found. Please return to Setup page and configure your sheets.");
          setIsLoading(false);
          return;
        }

        let availableTabs: string[] = [];

        // Try multiple endpoints to get available sheets, with fallbacks
        const tryEndpoints = async () => {
          // Build up the URL with query parameters
          const setupData = await fetch('http://localhost:8000/api/setup/info').then(res => res.json());
          // Use event_key from setupData if available, otherwise try to get it from sheetConfig
          let eventKey = null;
          if (setupData.status === 'success' && setupData.event_key) {
            eventKey = setupData.event_key;
          } else if (sheetConfig && sheetConfig.event_key) {
            // If no event_key in cache, use the one from the sheet configuration
            eventKey = sheetConfig.event_key;
            console.log("Using event_key from sheet config instead of cache:", eventKey);
          }
          const yearValue = setupData.status === 'success' ? setupData.year : null;

          // Use the spreadsheet ID from the configuration if available
          if (sheetConfig && sheetConfig.spreadsheet_id) {
            console.log("Using spreadsheet ID from configuration:", sheetConfig.spreadsheet_id);
          } else if (!spreadsheetId) {
            console.warn("No spreadsheet ID available in configuration or directly provided");
            setError("No active sheet configuration found. Please go back to Setup page and set up a sheet configuration.");
            setIsLoading(false);
            return [];
          }

          // Create URLs with all available parameters
          const buildUrl = (base, addSpreadsheetId = true) => {
            const params = new URLSearchParams();

            if (addSpreadsheetId && spreadsheetId) {
              params.append('spreadsheet_id', spreadsheetId);
            }

            if (eventKey) {
              params.append('event_key', eventKey);
            }

            if (yearValue) {
              params.append('year', yearValue.toString());
            }

            const queryString = params.toString();
            return `${base}${queryString ? '?' + queryString : ''}`;
          };

          // List of endpoints to try in order
          const endpoints = [
            // Direct access endpoint - simplest, just uses spreadsheet ID directly
            {
              url: `http://localhost:8000/api/sheets/sheets?spreadsheet_id=${encodeURIComponent(spreadsheetId)}`,
              name: "Direct sheets API"
            },
            // Primary endpoint - most reliable but more complex
            {
              url: buildUrl('http://localhost:8000/api/sheet-config/available-sheets'),
              name: "sheet-config API"
            },
            // Fallback endpoint - for backward compatibility
            {
              url: buildUrl('http://localhost:8000/api/sheets/available-tabs'),
              name: "sheets API"
            }
          ];

          // Try each endpoint in sequence until one succeeds
          for (const endpoint of endpoints) {
            try {
              console.log(`Fetching available tabs from ${endpoint.name}:`, endpoint.url);
              const response = await fetch(endpoint.url);

              if (response.ok) {
                const data = await response.json();
                if (data.status === 'success') {
                  // Handle both response formats
                  if (data.sheet_names) {
                    console.log(`${endpoint.name} returned sheet_names:`, data.sheet_names);
                    return data.sheet_names;
                  } else if (data.sheets) {
                    console.log(`${endpoint.name} returned sheets:`, data.sheets);
                    return data.sheets;
                  }
                  console.warn(`${endpoint.name} returned success but no sheet names found`);
                } else {
                  console.error(`Error from ${endpoint.name}:`, data.message || "Unknown error");
                }
              } else {
                // Attempt to parse error response
                try {
                  const errorData = await response.json();
                  console.error(`Failed to fetch from ${endpoint.name}:`, response.status, errorData);
                } catch {
                  console.error(`Failed to fetch from ${endpoint.name}:`, response.status, response.statusText);
                }
              }
            } catch (error) {
              console.error(`Exception fetching from ${endpoint.name}:`, error);
            }
          }

          // If we get here, all endpoints failed
          console.warn("All endpoints failed to get sheet tabs, using defaults");
          return [];
        };

        // Try all endpoints and get the result
        try {
          availableTabs = await tryEndpoints();

          // If we have no available tabs, it's likely because we couldn't find the configuration
          if (!availableTabs || availableTabs.length === 0) {
            setError("Could not fetch sheet tabs. Please make sure you have set up a valid sheet configuration in the Setup page and that you have selected an event.");
            setIsLoading(false);
            return;
          }
        } catch (error) {
          console.error("Exception in tab search process:", error);
          setError("Error fetching sheet tabs. Please try again or go back to Setup page to set up a proper sheet configuration.");
          setIsLoading(false);
          return;
        }

        // Check if our configured tabs exist in the available tabs
        const hasMatchTab = availableTabs.includes(matchScoutingTab);
        const hasSuperTab = availableTabs.includes(superScoutingTab);
        const hasPitTab = availableTabs.includes(pitScoutingTab);

        // Show warning if we can't find the match scouting tab
        if (!hasMatchTab) {
          setError(`Could not find the configured match scouting tab "${matchScoutingTab}" in the spreadsheet. Available tabs are: ${availableTabs.join(", ")}`);
        }

        // Display search status in console
        console.log("Tab search results:", {
          matchScoutingTab,
          hasMatchTab,
          superScoutingTab,
          hasSuperTab,
          pitScoutingTab,
          hasPitTab,
          availableTabs
        });

        // Prepare fetch requests for tabs that exist
        const fetchPromises = [];
        const tabTypes = [];

        // Add spreadsheet_id to the API calls - this is required now
        if (!spreadsheetId) {
          console.error("No spreadsheet ID available for API calls");
          setError("Missing spreadsheet ID. Please go back to Setup and configure your sheets.");
          setIsLoading(false);
          return;
        }
        const spreadsheetIdParam = `&spreadsheet_id=${encodeURIComponent(spreadsheetId)}`;
        console.log("Using spreadsheet ID param:", spreadsheetIdParam);

        // Always try to fetch Match Scouting data (main tab)
        if (hasMatchTab) {
          fetchPromises.push(fetch(`http://localhost:8000/api/sheets/headers?tab=${matchScoutingTab}${spreadsheetIdParam}`));
          tabTypes.push('scout');
        } else {
          console.log(`Match scouting tab '${matchScoutingTab}' not found in Google Sheet`);
          // Try fallback to "Scouting" if the configured tab doesn't exist
          if (matchScoutingTab !== 'Scouting' && (availableTabs.length === 0 || availableTabs.includes('Scouting'))) {
            console.log("Trying fallback to 'Scouting' tab");
            fetchPromises.push(fetch(`http://localhost:8000/api/sheets/headers?tab=Scouting${spreadsheetIdParam}`));
            tabTypes.push('scout');
          }
        }

        // Only fetch SuperScouting if the tab exists or we're using fallback
        if (hasSuperTab || availableTabs.length === 0) {
          fetchPromises.push(fetch(`http://localhost:8000/api/sheets/headers?tab=${superScoutingTab}&optional=true${spreadsheetIdParam}`));
          tabTypes.push('super');
        } else {
          console.log(`Super scouting tab '${superScoutingTab}' not found in Google Sheet`);
        }

        // Only fetch PitScouting if the tab exists or we're using fallback
        if (hasPitTab || availableTabs.length === 0) {
          fetchPromises.push(fetch(`http://localhost:8000/api/sheets/headers?tab=${pitScoutingTab}&optional=true${spreadsheetIdParam}`));
          tabTypes.push('pit');
        } else {
          console.log(`Pit scouting tab '${pitScoutingTab}' not found in Google Sheet`);
        }

        // Execute all fetch requests in parallel
        const responses = await Promise.all(fetchPromises);

        // Process the responses
        let scoutData = { headers: [] };
        let superData = { headers: [] };
        let pitData = { headers: [] };

        for (let i = 0; i < responses.length; i++) {
          const response = responses[i];
          const tabType = tabTypes[i];

          if (response.ok) {
            const data = await response.json();

            if (tabType === 'scout') {
              scoutData = data;
            } else if (tabType === 'super') {
              superData = data;
            } else if (tabType === 'pit') {
              pitData = data;
            }
          } else if (tabType === 'scout') {
            // Only throw an error if the main Scouting tab fails
            throw new Error('Failed to fetch match scouting headers');
          }
        }

        // Set headers - check if they exist and aren't empty
        setScoutingHeaders(scoutData.headers || []);
        setSuperscoutingHeaders(superData.headers || []);
        setPitScoutingHeaders(pitData.headers || []);

        // Initialize all headers with auto-categorization
        const initialFields: { [key: string]: string } = {};
        [
          ...(scoutData.headers || []),
          ...(superData.headers || []),
          ...(pitData.headers || [])
        ].forEach(header => {
          initialFields[header] = autoCategorizeField(header);
        });

        // Try to auto-detect robot groupings in superscouting headers
        const superHeaders = superData.headers || [];
        const newRobotGroups = { ...robotGroups };
        const newAssignedHeaders = new Set<string>();

        // Try to detect patterns like "Robot 1 X", "Robot 2 X", "Robot 3 X"
        // or "R1 X", "R2 X", "R3 X"
        const robotPatterns = [
          [/robot\s*1|r1\b/i, /robot\s*2|r2\b/i, /robot\s*3|r3\b/i],
          [/\b1\s*-/, /\b2\s*-/, /\b3\s*-/],
          [/_1_/, /_2_/, /_3_/]
        ];

        for (const patternSet of robotPatterns) {
          const r1Headers = superHeaders.filter((h: string) => patternSet[0].test(h));
          const r2Headers = superHeaders.filter((h: string) => patternSet[1].test(h));
          const r3Headers = superHeaders.filter((h: string) => patternSet[2].test(h));

          // If we found substantial matches for all robots, use them
          if (r1Headers.length > 1 && r2Headers.length > 1 && r3Headers.length > 1) {
            newRobotGroups.robot_1 = r1Headers;
            newRobotGroups.robot_2 = r2Headers;
            newRobotGroups.robot_3 = r3Headers;

            // Mark these headers as assigned
            [...r1Headers, ...r2Headers, ...r3Headers].forEach((h: string) => {
              newAssignedHeaders.add(h);
            });

            break;
          }
        }

        // Set up robot groups first
        setRobotGroups(newRobotGroups);
        setAssignedHeaders(newAssignedHeaders);

        // Process fields after robot groups are established
        const processedFields = processRobotGroups(newRobotGroups, initialFields);
        setSelectedFields(processedFields);

        // Update critical field mappings after processing
        const newCriticalMappings = {
          team_number: [] as string[],
          match_number: [] as string[]
        };

        Object.entries(processedFields).forEach(([header, category]) => {
          if (category === 'team_number') {
            newCriticalMappings.team_number.push(header);
          } else if (category === 'match_number') {
            newCriticalMappings.match_number.push(header);
          }
        });
        setCriticalFieldMappings(newCriticalMappings);

        // Add feedback about automated categorization
        const autoMappedCount = Object.values(processedFields).filter(v => v !== 'ignore' && v !== 'other').length;
        if (autoMappedCount > 0) {
          setSuccessMessage(`Auto-categorized ${autoMappedCount} fields based on naming patterns. Please review and adjust as needed.`);
        }
      } catch (err) {
        console.error('Error fetching headers:', err);
        setError('Error fetching headers from Google Sheets');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHeaders();
  }, []);

  useEffect(() => {
    // Validate critical fields whenever selected fields change
    validateCriticalFields();
  }, [selectedFields]);

  const validateCriticalFields = () => {
    // Find all team_number and match_number mappings
    const teamNumberFields: string[] = [];
    const matchNumberFields: string[] = [];
    
    Object.entries(selectedFields).forEach(([header, category]) => {
      if (category === 'team_number') {
        teamNumberFields.push(header);
      } else if (category === 'match_number') {
        matchNumberFields.push(header);
      }
    });
    
    // Update state with the mappings
    setCriticalFieldMappings({
      team_number: teamNumberFields,
      match_number: matchNumberFields
    });
    
    // Check if we have at least one of each critical field type
    const missingFields = [];
    
    if (teamNumberFields.length === 0) {
      missingFields.push('Team Number');
    }
    
    if (matchNumberFields.length === 0) {
      missingFields.push('Match Number');
    }
    
    if (missingFields.length > 0) {
      setValidationWarning(`Warning: Missing required fields: ${missingFields.join(', ')}`);
    } else {
      setValidationWarning(null);
    }
  };

  // Modified to allow multiple critical field mappings
  const handleCategoryChange = (header: string, category: string) => {
    // Update the field mapping
    setSelectedFields(prev => ({
      ...prev,
      [header]: category
    }));
    
    // Validation will run automatically via useEffect
  };

  const handleAddToRobotGroup = (header: string) => {
    // Remove from any existing robot group
    const updatedGroups = { ...robotGroups };
    
    // Remove header from all groups
    Object.keys(updatedGroups).forEach(group => {
      updatedGroups[group] = updatedGroups[group].filter(h => h !== header);
    });
    
    // Add to current active group
    updatedGroups[activeRobotGroup] = [...updatedGroups[activeRobotGroup], header];
    
    // Update state
    setRobotGroups(updatedGroups);
    
    // Update assigned headers
    const newAssignedHeaders = new Set(assignedHeaders);
    newAssignedHeaders.add(header);
    setAssignedHeaders(newAssignedHeaders);
  };

  const handleRemoveFromRobotGroup = (header: string, group: string) => {
    const updatedGroups = { ...robotGroups };
    updatedGroups[group] = updatedGroups[group].filter(h => h !== header);
    setRobotGroups(updatedGroups);
    
    // Only remove from assigned headers if it's not in any group
    const isAssigned = Object.values(updatedGroups).some(headers => headers.includes(header));
    if (!isAssigned) {
      const newAssignedHeaders = new Set(assignedHeaders);
      newAssignedHeaders.delete(header);
      setAssignedHeaders(newAssignedHeaders);
    }
  };

  const handleRobotGroupChange = (robot: string) => {
    setActiveRobotGroup(robot);
  };

  // Handle changing the UI category tab
  const handleTabChange = (categoryId: string) => {
    setActiveCategory(categoryId);
  };

  // Calculate counts per category for progress tracking
  const getFieldCountsByCategory = () => {
    const categoryCounts: Record<string, number> = {
      match: 0,
      pit: 0,
      super: 0,
      critical: criticalFieldMappings.team_number.length + criticalFieldMappings.match_number.length
    };

    // Count categorized fields by data source
    scoutingHeaders.forEach(header => {
      if (selectedFields[header] && selectedFields[header] !== 'ignore') {
        categoryCounts.match++;
      }
    });

    pitScoutingHeaders.forEach(header => {
      if (selectedFields[header] && selectedFields[header] !== 'ignore') {
        categoryCounts.pit++;
      }
    });

    superscoutingHeaders.forEach(header => {
      if (selectedFields[header] && selectedFields[header] !== 'ignore') {
        categoryCounts.super++;
      }
    });

    return categoryCounts;
  };

  const handleSaveSchema = async () => {
    // Validate critical fields before saving
    const missingFields = [];
    
    if (criticalFieldMappings.team_number.length === 0) {
      missingFields.push('Team Number');
    }
    
    if (criticalFieldMappings.match_number.length === 0) {
      missingFields.push('Match Number');
    }
    
    if (missingFields.length > 0) {
      const proceed = window.confirm(
        `Warning: The following critical fields are not mapped: ${missingFields.join(', ')}. ` +
        `This will prevent proper data validation and match tracking. Do you want to proceed anyway?`
      );
      
      if (!proceed) {
        return;
      }
    }
    
    try {
      setIsLoading(true);
      
      // Save the schema
      const schema = {
        field_selections: selectedFields,
        manual_url: gameManualUrl,
        year: year,
        critical_mappings: criticalFieldMappings,
        robot_groups: robotGroups
      };
      
      const response = await fetch('http://localhost:8000/api/schema/save-selections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schema)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save schema');
      }
      
      // Show initial success message
      setSuccessMessage('Field selections saved successfully! Now learning schema mappings...');
      
      // Trigger schema mapping for both regular scouting and superscout
      try {
        // Learn regular scouting schema
        await fetch('http://localhost:8000/api/schema/learn');
        
        // Learn superscouting schema with data analysis
        const superResponse = await fetch('http://localhost:8000/api/schema/super/learn');
        const superData = await superResponse.json();
        
        if (superResponse.ok && superData.status === 'success') {
          setSuccessMessage('Field selections and schema mappings saved successfully! Analyzing data content...');
        }
        
        // Show building dataset message
        setSuccessMessage('Field selections and schema mappings saved successfully! Building dataset...');

        // Trigger dataset build
        try {
          // Get current event key from setup API
          const setupResponse = await fetch("http://localhost:8000/api/setup/info");
          let eventKey = null;
          let yearValue = 2025; // Default

          if (setupResponse.ok) {
            const setupData = await setupResponse.json();

            if (setupData.status === "success" && setupData.event_key) {
              eventKey = setupData.event_key;
              if (setupData.year) {
                yearValue = setupData.year;
              }
            }
          }

          // Check if we have a valid event key
          if (!eventKey) {
            setError('No event selected. Please go to Setup page and select an event first.');
            return;
          }

          // Build the dataset
          const buildResponse = await fetch("http://localhost:8000/api/unified/build", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              event_key: eventKey,
              year: yearValue,
              force_rebuild: true
            })
          });

          if (buildResponse.ok) {
            setSuccessMessage('Dataset built successfully! Proceeding to validation...');
            // Navigate to validation page after dataset is built
            setTimeout(() => {
              navigate('/validation');
            }, 1500);
          } else {
            // Still go to validation even if build fails - they can build from there
            setSuccessMessage('Field selections saved, but dataset build had issues. Proceeding to validation...');
            setTimeout(() => {
              navigate('/validation');
            }, 2000);
          }
        } catch (buildErr) {
          console.error('Error building dataset:', buildErr);
          // Still go to validation even if build fails - they can build from there
          setSuccessMessage('Field selections saved, but dataset build had issues. Proceeding to validation...');
          setTimeout(() => {
            navigate('/validation');
          }, 2000);
        }
      } catch (schemaErr) {
        console.error('Error learning schema mappings:', schemaErr);
        // Still continue to workflow even if schema learning fails
        // The user can manually trigger schema learning later
        setSuccessMessage('Field selections saved, but schema learning had issues. Continuing to workflow.');
        setTimeout(() => {
          navigate('/workflow');
        }, 2000);
      }
    } catch (err) {
      console.error('Error saving schema:', err);
      setError('Error saving field selections');
      setIsLoading(false);
    }
  };

  // Find suggested headers for critical fields
  const findCriticalFieldCandidates = (field: CriticalField): string[] => {
    // Include both scouting and superscouting headers for better suggestions
    const allHeaders = [...scoutingHeaders, ...superscoutingHeaders];
    return allHeaders.filter(header => field.requiredPattern.test(header));
  };

 
  // Helper to get the critical field type
  const getCriticalFieldType = (header: string): string | null => {
    if (criticalFieldMappings.team_number.includes(header)) {
      return 'team_number';
    }
    if (criticalFieldMappings.match_number.includes(header)) {
      return 'match_number';
    }
    return null;
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Field Selection</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-bold mb-4">Game Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-2">Year</label>
            <select
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="w-full p-2 border rounded"
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
            </select>
          </div>
          <div>
            <label className="block font-medium mb-2">Game Manual URL (Optional)</label>
            <input
              type="url"
              value={gameManualUrl}
              onChange={(e) => setGameManualUrl(e.target.value)}
              placeholder="https://example.com/game-manual.pdf"
              className="w-full p-2 border rounded"
            />
            <p className="text-sm text-gray-500 mt-1">
              Used for picklist generation and strategy insights.
            </p>
          </div>
        </div>
      </div>
      
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {successMessage}
        </div>
      )}

      {validationWarning && (
        <div className="p-3 mb-4 bg-yellow-100 text-yellow-700 rounded">
          {validationWarning}
        </div>
      )}

      {/* Category Tabs */}
      <CategoryTabs
        categories={DATA_CATEGORIES}
        activeCategory={activeCategory}
        onCategoryChange={handleTabChange}
        countsPerCategory={getFieldCountsByCategory()}
        totalCount={scoutingHeaders.length + superscoutingHeaders.length + pitScoutingHeaders.length}
      />

      {/* Critical Fields Section */}
      {activeCategory === 'critical' && (
        <div className="bg-blue-50 p-6 rounded-lg shadow-md mb-6 border-l-4 border-blue-500">
          <h2 className="text-xl font-bold text-blue-800 mb-2">Critical Fields</h2>
          <p className="mb-4 text-blue-700">
            These fields are required for proper data validation and match tracking.
            They must be mapped correctly for the system to function properly.
            <span className="block mt-1">Note: You can select multiple team number and match number fields for superscouting robot groups.</span>
          </p>

          <div className="grid grid-cols-1 gap-4">
            {CRITICAL_FIELDS.map(field => {
              const candidates = findCriticalFieldCandidates(field);
              const currentMappings = criticalFieldMappings[field.key as keyof typeof criticalFieldMappings];

              return (
                <div key={field.key} className="bg-white p-4 rounded border">
                  <h3 className="font-bold mb-1">{field.label}s</h3>
                  <p className="text-sm mb-3 text-gray-600">{field.description}</p>

                  {/* Display currently mapped fields */}
                  {currentMappings.length > 0 ? (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold mb-2">Currently Mapped Fields:</h4>
                      <div className="flex flex-wrap gap-2">
                        {currentMappings.map(header => (
                          <div key={header} className="flex items-center bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                            <span>{header}</span>
                            <button
                              onClick={() => handleCategoryChange(header, 'ignore')}
                              className="ml-2 text-blue-800 hover:text-blue-600"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="mb-4 bg-red-100 text-red-700 p-2 rounded">
                      No {field.label} fields mapped yet.
                    </div>
                  )}

                  {/* Field Suggestions */}
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Add A {field.label} Field:</h4>
                    <select
                      value=""
                      onChange={(e) => {
                        const header = e.target.value;
                        if (header) {
                          handleCategoryChange(header, field.key);
                        }
                      }}
                      className="w-full p-2 border rounded"
                    >
                      <option value="">-- Select {field.label} Field --</option>

                      {/* Show likely candidates first */}
                      {candidates.length > 0 && (
                        <optgroup label="Suggested Fields">
                          {candidates
                            .filter(header => !currentMappings.includes(header))
                            .map(header => (
                              <option key={`suggested-${header}`} value={header}>
                                {header}
                              </option>
                            ))}
                        </optgroup>
                      )}

                      {/* Show fields grouped by section */}
                      <optgroup label="Match Scouting Fields">
                        {scoutingHeaders
                          .filter(header => !currentMappings.includes(header) && selectedFields[header] !== field.key)
                          .map(header => (
                            <option key={header} value={header}>
                              {header}
                            </option>
                          ))}
                      </optgroup>

                      {pitScoutingHeaders.length > 0 && (
                        <optgroup label="Pit Scouting Fields">
                          {pitScoutingHeaders
                            .filter(header => !currentMappings.includes(header) && selectedFields[header] !== field.key)
                            .map(header => (
                              <option key={`pit-${header}`} value={header}>
                                {header}
                              </option>
                            ))}
                        </optgroup>
                      )}

                      {superscoutingHeaders.length > 0 && (
                        <optgroup label="SuperScouting Fields">
                          {superscoutingHeaders
                            .filter(header => !currentMappings.includes(header) && selectedFields[header] !== field.key)
                            .map(header => (
                              <option key={`super-${header}`} value={header}>
                                {header}
                              </option>
                            ))}
                        </optgroup>
                      )}
                    </select>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Match Scouting Fields */}
      {activeCategory === 'match' && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-bold mb-4">Match Scouting Fields</h2>
          <p className="mb-4 text-gray-600">
            Select which fields to include in analysis and categorize them.
            These fields come from the "Scouting" tab in your spreadsheet.
          </p>

          <div className="mb-6">
            <table className="min-w-full border">
              <thead className="bg-gray-100">
                <tr>
                  <th className="border px-4 py-2 text-left">Header</th>
                  <th className="border px-4 py-2 text-left">Category</th>
                </tr>
              </thead>
              <tbody>
                {scoutingHeaders.map((header, index) => {
                  const criticalType = getCriticalFieldType(header);

                  return (
                    <tr
                      key={`scout-${index}`}
                      className={`${criticalType ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                    >
                      <td className="border px-4 py-2">
                        {criticalType && (
                          <span className="inline-block mr-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                            {criticalType === 'team_number' ? 'Team Number' : 'Match Number'}
                          </span>
                        )}
                        {header}
                      </td>
                      <td className="border px-4 py-2">
                        <select
                          value={selectedFields[header] || 'ignore'}
                          onChange={(e) => handleCategoryChange(header, e.target.value)}
                          className={`w-full p-1 border rounded ${criticalType ? 'bg-blue-50 font-medium' : ''}`}
                        >
                          <option value="ignore">Ignore</option>
                          <option value="team_number">Team Number</option>
                          <option value="match_number">Match Number</option>
                          {FIELD_CATEGORIES.map(category => (
                            <option key={category.key} value={category.key}>
                              {category.label}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pit Scouting Fields */}
      {activeCategory === 'pit' && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-bold mb-4">Pit Scouting Fields</h2>

          {pitScoutingHeaders.length > 0 ? (
            <>
              <p className="mb-4 text-gray-600">
                Select which fields to include in analysis and categorize them.
                These fields come from the "PitScouting" tab in your spreadsheet.
              </p>

              <div className="mb-6">
                <table className="min-w-full border">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-4 py-2 text-left">Header</th>
                      <th className="border px-4 py-2 text-left">Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pitScoutingHeaders.map((header, index) => {
                      const criticalType = getCriticalFieldType(header);

                      return (
                        <tr
                          key={`pit-${index}`}
                          className={`${criticalType ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                        >
                          <td className="border px-4 py-2">
                            {criticalType && (
                              <span className="inline-block mr-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                                {criticalType === 'team_number' ? 'Team Number' : 'Match Number'}
                              </span>
                            )}
                            {header}
                          </td>
                          <td className="border px-4 py-2">
                            <select
                              value={selectedFields[header] || 'ignore'}
                              onChange={(e) => handleCategoryChange(header, e.target.value)}
                              className={`w-full p-1 border rounded ${criticalType ? 'bg-blue-50 font-medium' : ''}`}
                            >
                              <option value="ignore">Ignore</option>
                              <option value="team_number">Team Number</option>
                              {FIELD_CATEGORIES.map(category => (
                                <option key={category.key} value={category.key}>
                                  {category.label}
                                </option>
                              ))}
                            </select>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-300 mb-6">
              <h3 className="text-lg font-bold text-yellow-800 mb-2">Pit Scouting Data Not Found</h3>
              <p className="text-yellow-700 mb-2">
                No Pit Scouting headers were detected in your spreadsheet. This may indicate:
              </p>
              <ul className="list-disc list-inside text-yellow-700 mb-2">
                <li>You don't have a "PitScouting" tab in your Google Sheet</li>
                <li>The "PitScouting" tab exists but is empty or formatted incorrectly</li>
                <li>You haven't configured a Pit Scouting sheet in your sheet configuration</li>
              </ul>
              <p className="text-yellow-700">
                Pit Scouting data is optional but helpful for collecting technical and physical robot specifications.
                You can still proceed without Pit Scouting data.
              </p>
            </div>
          )}
        </div>
      )}

      {/* SuperScouting Section */}
      {activeCategory === 'super' && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-bold mb-4">Super Scouting Fields</h2>

          {superscoutingHeaders.length > 0 ? (
            <>
              <h3 className="text-lg font-bold mb-4">Robot Groups</h3>
              <p className="mb-4 text-gray-600">
                Group superscouting headers by robot to create separate records for each robot in a match.
                <span className="block mt-1 font-semibold text-blue-700">
                  You can mark multiple team number fields - one for each robot group.
                </span>
              </p>

              {/* Robot Group Selection Tabs */}
              <div className="flex border-b mb-4">
                {Object.keys(robotGroups).map((robot) => (
                  <button
                    key={robot}
                    onClick={() => handleRobotGroupChange(robot)}
                    className={`py-2 px-4 font-medium ${
                      activeRobotGroup === robot
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {robot.replace('_', ' ').toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Robot Group Members Display */}
              <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(robotGroups).map(([robot, headers]) => (
                  <div
                    key={robot}
                    className={`border rounded-lg p-4 ${
                      activeRobotGroup === robot ? 'border-blue-500 bg-blue-50' : ''
                    }`}
                  >
                    <h3 className="font-bold mb-2">{robot.replace('_', ' ').toUpperCase()}</h3>
                    {headers.length === 0 ? (
                      <p className="text-gray-500 text-sm italic">No fields assigned</p>
                    ) : (
                      <ul className="space-y-1">
                        {headers.map(header => {
                          const criticalType = getCriticalFieldType(header);
                          return (
                            <li key={header} className="flex justify-between items-center text-sm">
                              <span>
                                {header}
                                {criticalType && (
                                  <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                                    {criticalType === 'team_number' ? 'Team #' : 'Match #'}
                                  </span>
                                )}
                              </span>
                              <button
                                onClick={() => handleRemoveFromRobotGroup(header, robot)}
                                className="text-red-500 hover:text-red-700"
                              >
                                ×
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                ))}
              </div>

              <h3 className="text-lg font-bold mb-4">Available SuperScouting Fields</h3>
              <p className="mb-4 text-gray-600">
                Add fields to the currently selected robot group above.
              </p>

              <div>
                <table className="min-w-full border">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-4 py-2 text-left">Header</th>
                      <th className="border px-4 py-2 text-left">Category</th>
                      <th className="border px-4 py-2 text-center w-24">Robot Group</th>
                    </tr>
                  </thead>
                  <tbody>
                    {superscoutingHeaders.map((header, index) => {
                      const isAssigned = assignedHeaders.has(header);
                      const assignedGroup = Object.entries(robotGroups)
                        .find(([_, headers]) => headers.includes(header))?.[0];
                      const criticalType = getCriticalFieldType(header);

                      return (
                        <tr
                          key={`super-${index}`}
                          className={`${isAssigned ? 'bg-gray-100' : 'hover:bg-gray-50'} ${
                            criticalType ? 'bg-blue-50' : ''
                          }`}
                        >
                          <td className="border px-4 py-2">
                            {header}
                            {assignedGroup && (
                              <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                                {assignedGroup.replace('_', ' ').toUpperCase()}
                              </span>
                            )}
                            {criticalType && (
                              <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                                {criticalType === 'team_number' ? 'Team #' : 'Match #'}
                              </span>
                            )}
                          </td>
                          <td className="border px-4 py-2">
                            <select
                              value={selectedFields[header] || 'ignore'}
                              onChange={(e) => handleCategoryChange(header, e.target.value)}
                              className="w-full p-1 border rounded"
                            >
                              <option value="ignore">Ignore</option>
                              <option value="team_number">Team Number</option>
                              <option value="match_number">Match Number</option>
                              {FIELD_CATEGORIES.map(category => (
                                <option key={category.key} value={category.key}>
                                  {category.label}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="border px-4 py-2 text-center">
                            {assignedGroup ? (
                              <button
                                onClick={() => handleRemoveFromRobotGroup(header, assignedGroup)}
                                className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs hover:bg-red-200"
                              >
                                Remove
                              </button>
                            ) : (
                              <button
                                onClick={() => handleAddToRobotGroup(header)}
                                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                              >
                                {`Add to ${activeRobotGroup.replace('_', ' ').toUpperCase()}`}
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-300 mb-6">
              <h3 className="text-lg font-bold text-yellow-800 mb-2">SuperScouting Data Not Found</h3>
              <p className="text-yellow-700 mb-2">
                No SuperScouting headers were detected in your spreadsheet. This may indicate:
              </p>
              <ul className="list-disc list-inside text-yellow-700 mb-2">
                <li>You don't have a "SuperScouting" tab in your Google Sheet</li>
                <li>The "SuperScouting" tab exists but is empty or formatted incorrectly</li>
                <li>There might be an API connection issue with the Google Sheets service</li>
              </ul>
              <p className="text-yellow-700">
                SuperScouting data is optional but helpful for qualitative robot assessments and strategy notes.
                You can still proceed without SuperScouting data.
              </p>
            </div>
          )}
        </div>
      )}
      
      <div className="flex justify-end">
        <button
          onClick={handleSaveSchema}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Save Field Selections
        </button>
      </div>
    </div>
  );
}

export default FieldSelection;