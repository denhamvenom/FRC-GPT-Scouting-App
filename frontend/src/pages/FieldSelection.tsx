// frontend/src/pages/FieldSelection.tsx

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CategoryTabs, { Category } from '../components/CategoryTabs';
import { apiUrl, fetchWithNgrokHeaders } from '../config';
import { useGameLabels, GameLabel } from '../hooks/useGameLabels';
import { AddLabelModal } from '../components/AddLabelModal';

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
  { key: 'strategy', label: 'Strategy/Notes', description: 'Strategic assessment, text notes, and qualitative observations' },
  { key: 'other', label: 'Other', description: 'Any additional fields that don\'t fit above categories' },
];

// Define UI categories for the tabs
const DATA_CATEGORIES: Category[] = [
  { id: 'match', label: 'Match Scouting', description: 'Data collected during matches', icon: '📊' },
  { id: 'pit', label: 'Pit Scouting', description: 'Data collected during pit visits', icon: '🔧' },
  { id: 'super', label: 'Super Scouting', description: 'Qualitative observations from experienced scouts', icon: '🔍' },
  { id: 'critical', label: 'Critical Fields', description: 'Required fields for proper data validation', icon: '⚠️' },
];

// Fuzzy matching algorithm to find best matching label
const calculateStringSimilarity = (str1: string, str2: string): number => {
  // Convert to lowercase for case-insensitive comparison
  const s1 = str1.toLowerCase();
  const s2 = str2.toLowerCase();
  
  // Exact match
  if (s1 === s2) return 1.0;
  
  // Calculate Levenshtein distance
  const matrix = [];
  for (let i = 0; i <= s2.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= s1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= s2.length; i++) {
    for (let j = 1; j <= s1.length; j++) {
      if (s2.charAt(i - 1) === s1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  const distance = matrix[s2.length][s1.length];
  const maxLength = Math.max(s1.length, s2.length);
  return (maxLength - distance) / maxLength;
};

// Find best matching label for a field header
const findBestLabelMatch = (header: string, labels: GameLabel[]): { label: GameLabel; score: number } | null => {
  if (!labels || labels.length === 0) return null;
  
  let bestMatch: { label: GameLabel; score: number } | null = null;
  const headerLower = header.toLowerCase();
  
  for (const label of labels) {
    // Extract key parts from label name (remove common prefixes/suffixes)
    const labelName = label.label.toLowerCase();
    const labelWords = labelName.split('_');
    
    // Check for exact substring matches first
    if (headerLower.includes(labelName) || labelName.includes(headerLower)) {
      const score = 0.9;
      if (!bestMatch || score > bestMatch.score) {
        bestMatch = { label, score };
      }
      continue;
    }
    
    // Check for word matches
    const headerWords = headerLower.split(/[\s_\-]+/);
    let wordMatches = 0;
    let totalWords = Math.max(labelWords.length, headerWords.length);
    
    for (const labelWord of labelWords) {
      if (headerWords.some(hw => hw.includes(labelWord) || labelWord.includes(hw))) {
        wordMatches++;
      }
    }
    
    if (wordMatches > 0) {
      const score = wordMatches / totalWords;
      if (!bestMatch || score > bestMatch.score) {
        bestMatch = { label, score };
      }
    }
    
    // Fallback to string similarity
    const similarity = calculateStringSimilarity(header, labelName);
    if (similarity > 0.3) {
      const score = similarity * 0.7; // Lower weight for pure similarity
      if (!bestMatch || score > bestMatch.score) {
        bestMatch = { label, score };
      }
    }
  }
  
  // Only return matches with reasonable confidence
  return bestMatch && bestMatch.score > 0.3 ? bestMatch : null;
};

// Build dynamic patterns from loaded labels (memoized for performance)
const buildPatternsFromLabels = (labels: GameLabel[]): Map<string, RegExp> => {
  const patterns = new Map<string, RegExp>();
  
  const categories = ['autonomous', 'teleop', 'endgame', 'defense', 'reliability', 'strategic', 'qualitative', 'subjective', 'notes'];
  
  categories.forEach(category => {
    const categoryLabels = labels.filter(l => l.category === category);
    if (categoryLabels.length === 0) return;
    
    // Extract unique keywords from label names
    const keywords = new Set<string>();
    categoryLabels.forEach(label => {
      // Split by underscore and extract meaningful parts
      const parts = label.label.toLowerCase().split('_');
      parts.forEach(part => {
        if (part.length > 2 && !['the', 'and', 'or', 'in', 'on', 'at', 'to', 'for'].includes(part)) {
          keywords.add(part);
        }
      });
    });
    
    if (keywords.size > 0) {
      const pattern = Array.from(keywords).join('|');
      patterns.set(category, new RegExp(pattern, 'i'));
    }
  });
  
  return patterns;
};

// Helper function to get available labels for a field (excluding already assigned labels)
const getAvailableLabelsForField = (
  allLabels: GameLabel[], 
  labelMappings: { [fieldHeader: string]: GameLabel },
  currentFieldHeader: string
): GameLabel[] => {
  // Get set of already assigned label names, excluding the current field
  const assignedLabelNames = new Set(
    Object.entries(labelMappings)
      .filter(([fieldHeader, _]) => fieldHeader !== currentFieldHeader)
      .map(([_, label]) => label.label)
  );
  
  // Return labels that are not already assigned
  return allLabels.filter(label => !assignedLabelNames.has(label.label));
};

// Helper function to check if a label is assigned to another field
const isLabelAssignedElsewhere = (
  label: GameLabel,
  labelMappings: { [fieldHeader: string]: GameLabel },
  currentFieldHeader: string
): string | null => {
  for (const [fieldHeader, assignedLabel] of Object.entries(labelMappings)) {
    if (fieldHeader !== currentFieldHeader && assignedLabel.label === label.label) {
      return fieldHeader;
    }
  }
  return null;
};

// Cache for label patterns to avoid rebuilding on every call
let labelPatternsCache: Map<string, RegExp> | null = null;
let labelsCacheKey: string | null = null;

// Enhanced utility function to auto-categorize fields based on patterns and label matching
const autoCategorizeField = (header: string, labels: GameLabel[] = []): { category: string; matchedLabel?: GameLabel; confidence?: number } => {
  // Convert to lowercase for case-insensitive matching
  const headerLower = header.toLowerCase();
  
  // Build patterns cache if needed
  const labelsKey = labels.map(l => l.label).join(',');
  if (labels.length > 0 && (labelPatternsCache === null || labelsCacheKey !== labelsKey)) {
    labelPatternsCache = buildPatternsFromLabels(labels);
    labelsCacheKey = labelsKey;
  }
  
  // Special handling for robot team numbers in SuperScouting
  if (/robot\s*\d+\s*number/i.test(header)) {
    return { category: 'team_number' };
  }
  
  // Check for team number or match number patterns (general)
  if ((/team|^t\d+$|^frc\d+$/i.test(headerLower)) && /number/i.test(headerLower)) {
    return { category: 'team_number' };
  }
  
  // Handle match/qual number fields
  if (/qual\s*number/i.test(headerLower)) {
    return { category: 'match_number' };
  }
  
  if (/match|qualification|^q\d+$/i.test(headerLower)) {
    return { category: 'match_number' };
  }
  
  // Try to find a matching label first, but only for very high confidence matches
  const labelMatch = findBestLabelMatch(header, labels);
  if (labelMatch && labelMatch.score > 0.85) {  // Only use label matching for very high confidence
    // Map label categories to field categories
    const categoryMap: { [key: string]: string } = {
      'autonomous': 'auto',
      'teleop': 'teleop',
      'endgame': 'endgame',
      'defense': 'strategy',
      'reliability': 'strategy',
      'strategic': 'strategy',
      'qualitative': 'strategy',
      'subjective': 'strategy',
      'notes': 'strategy',
      'team_info': 'team_info',
      'match_info': 'team_info'
    };
    
    const mappedCategory = categoryMap[labelMatch.label.category] || 'other';
    return { 
      category: mappedCategory, 
      matchedLabel: labelMatch.label, 
      confidence: labelMatch.score 
    };
  }
  
  // Fallback to pattern matching - use dynamic patterns from labels if available
  if (labelPatternsCache && labelPatternsCache.size > 0) {
    // Try dynamic patterns based on loaded labels
    const autoPattern = labelPatternsCache.get('autonomous');
    if (autoPattern && autoPattern.test(headerLower)) {
      return { category: 'auto' };
    }
    
    const teleopPattern = labelPatternsCache.get('teleop');
    if (teleopPattern && teleopPattern.test(headerLower)) {
      return { category: 'teleop' };
    }
    
    const endgamePattern = labelPatternsCache.get('endgame');
    if (endgamePattern && endgamePattern.test(headerLower)) {
      return { category: 'endgame' };
    }
    
    // For strategy, check multiple related categories
    const strategyCategories = ['defense', 'reliability', 'strategic', 'qualitative', 'subjective', 'notes'];
    for (const cat of strategyCategories) {
      const pattern = labelPatternsCache.get(cat);
      if (pattern && pattern.test(headerLower)) {
        return { category: 'strategy' };
      }
    }
  }
  
  // Generic fallback patterns if no labels are loaded or no dynamic patterns matched
  // Check for autonomous/auto patterns
  if (/auto|autonomous|^a_|^a\.|auton|initial|opening|^pre_/i.test(headerLower)) {
    return { category: 'auto' };
  }
  
  // Check for teleop patterns
  if (/tele|teleop|teleoperated|driver|^t_|^t\.|manual|operated/i.test(headerLower)) {
    return { category: 'teleop' };
  }
  
  // Check for endgame patterns
  if (/end|endgame|final|climb|hanging|finish|last|conclude/i.test(headerLower)) {
    return { category: 'endgame' };
  }
  
  // Check for strategy/subjective patterns
  if (/strat|comment|note|subjective|rating|skill|defense|speed|observ|text|description|details|remarks|feedback|evaluation|qualitative|narrative|analysis|summary|report|scout|assess|judge|opinion|review/i.test(headerLower)) {
    return { category: 'strategy' };
  }
  
  // Check for team info patterns
  if (/alliance|color|station|position|start|timestamp|time|date|match|team|robot|event/i.test(headerLower)) {
    return { category: 'team_info' };
  }
  
  // Check for scoring/game piece patterns (generic)
  if (/score|point|goal|piece/i.test(headerLower)) {
    return { category: 'teleop' }; // Default scoring to teleop
  }
  
  // Check for movement/mobility patterns
  if (/move|mobility|drive|cross|leave|exit|path|route/i.test(headerLower)) {
    return { category: 'auto' }; // Movement often relates to auto
  }
  
  // Check for reliability/performance patterns
  if (/broke|fail|dead|disable|penalty|foul|technical|malfunction|issue|problem|reliable/i.test(headerLower)) {
    return { category: 'strategy' };
  }
  
  // Default to 'other' if no patterns match
  return { category: 'other' };
};


interface FieldSelectionProps {
  embedded?: boolean;
  onComplete?: () => void;
}

function FieldSelection({ embedded = false, onComplete }: FieldSelectionProps = {}) {
  const navigate = useNavigate();
  const { labels, loadLabels, isLoading: labelsLoading } = useGameLabels();
  
  // Headers from different scouting spreadsheets
  const [scoutingHeaders, setScoutingHeaders] = useState<string[]>([]);
  const [superscoutingHeaders, setSuperscoutingHeaders] = useState<string[]>([]);
  const [pitScoutingHeaders, setPitScoutingHeaders] = useState<string[]>([]);

  // Field categorization
  const [selectedFields, setSelectedFields] = useState<{ [key: string]: string }>({});
  
  // Label mappings for enhanced field names
  const [labelMappings, setLabelMappings] = useState<{ [fieldHeader: string]: GameLabel }>({});

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


  // UI state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isBuildingDataset, setIsBuildingDataset] = useState<boolean>(false);
  const [buildProgress, setBuildProgress] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);
  const [year, setYear] = useState<number>(2025);
  const [eventKey, setEventKey] = useState<string | null>(null);
  
  // Add Label Modal state
  const [isAddLabelModalOpen, setIsAddLabelModalOpen] = useState(false);
  const [currentFieldForLabel, setCurrentFieldForLabel] = useState<string | null>(null);
  const [editingLabel, setEditingLabel] = useState<GameLabel | null>(null);

  useEffect(() => {
    // Load game labels on component mount
    console.log('Loading game labels...');
    loadLabels();
  }, [loadLabels]);

  // Load saved field selections when headers are available
  useEffect(() => {
    // Only load saved selections after headers are loaded
    if (scoutingHeaders.length === 0 && superscoutingHeaders.length === 0 && pitScoutingHeaders.length === 0) {
      return;
    }

    const loadSavedSelections = async () => {
      try {
        console.log('Attempting to load saved field selections...');
        // Use event_key if available, otherwise fall back to year
        const storageKey = eventKey || year.toString();
        console.log(`Loading field selections with storage key: ${storageKey}`);
        const response = await fetchWithNgrokHeaders(apiUrl(`/api/schema/load-selections/${storageKey}`));
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            console.log('Loading saved field selections:', data);
            
            // Load field selections, but only for headers that exist
            if (data.field_selections) {
              const validSelections: { [key: string]: string } = {};
              const allHeaders = [...scoutingHeaders, ...superscoutingHeaders, ...pitScoutingHeaders];
              
              Object.entries(data.field_selections).forEach(([header, category]) => {
                if (allHeaders.includes(header)) {
                  validSelections[header] = category as string;
                }
              });
              
              if (Object.keys(validSelections).length > 0) {
                setSelectedFields(validSelections);
                console.log(`✅ Restored ${Object.keys(validSelections).length} field selections`);
              }
            }
            
            // Load critical mappings
            if (data.critical_mappings) {
              setCriticalFieldMappings(data.critical_mappings);
              console.log('✅ Restored critical field mappings');
            }
            
            // Load robot groups (for superscout fields)
            if (data.robot_groups) {
              console.log('Robot groups loaded:', data.robot_groups);
            }
            
            // Load label mappings
            if (data.label_mappings) {
              setLabelMappings(data.label_mappings);
              console.log(`✅ Restored ${Object.keys(data.label_mappings).length} label mappings`);
            }
          }
        } else {
          // No saved selections found, which is normal for first-time setup
          console.log('No saved field selections found, starting fresh');
        }
      } catch (error) {
        console.error('Error loading saved field selections:', error);
        // Don't show error to user, as this is optional functionality
      }
    };

    loadSavedSelections();
  }, [year, eventKey, scoutingHeaders, superscoutingHeaders, pitScoutingHeaders]);

  // Note: Automatic auto-categorization removed to preserve saved field selections
  // Auto-categorization now only happens when user clicks "Auto-match Labels" button

  useEffect(() => {
    // Fetch headers from Google Sheets
    const fetchHeaders = async () => {
      setIsLoading(true);
      try {
        // First, get the active sheet configuration from setup
        const setupResponse = await fetchWithNgrokHeaders(apiUrl('/api/setup/info'));
        let sheetConfig = null;

        console.log("Setup response status:", setupResponse.status);

        if (setupResponse.ok) {
          const setupData = await setupResponse.json();
          console.log("Setup data:", setupData);

          if (setupData.status === 'success' && setupData.sheet_config) {
            sheetConfig = setupData.sheet_config;
            console.log("Using sheet configuration from setup:", sheetConfig);

            // Get year and event_key if available
            if (setupData.year) {
              setYear(setupData.year);
            }
            if (setupData.event_key) {
              setEventKey(setupData.event_key);
              console.log("Set event key for field selections:", setupData.event_key);
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
          const configResponse = await fetchWithNgrokHeaders(apiUrl(`/api/sheet-config/${sheetConfig.id}`));

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
          const setupData = await fetchWithNgrokHeaders(apiUrl('/api/setup/info')).then(res => res.json());
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
              url: apiUrl(`/api/sheets/sheets?spreadsheet_id=${encodeURIComponent(spreadsheetId)}`),
              name: "Direct sheets API"
            },
            // Primary endpoint - most reliable but more complex
            {
              url: buildUrl(apiUrl('/api/sheet-config/available-sheets')),
              name: "sheet-config API"
            },
            // Fallback endpoint - for backward compatibility
            {
              url: buildUrl(apiUrl('/api/sheets/available-tabs')),
              name: "sheets API"
            }
          ];

          // Try each endpoint in sequence until one succeeds
          for (const endpoint of endpoints) {
            try {
              console.log(`Fetching available tabs from ${endpoint.name}:`, endpoint.url);
              const response = await fetchWithNgrokHeaders(endpoint.url);

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

          // If we have no available tabs, we'll try to fetch headers anyway using fallback logic
          if (!availableTabs || availableTabs.length === 0) {
            console.warn("Could not fetch sheet tabs list, but will attempt to fetch headers using configured tab names");
            // Don't return here - continue with the header fetching logic
          }
        } catch (error) {
          console.error("Exception in tab search process:", error);
          setError("Error fetching sheet tabs. Please try again or go back to Setup page to set up a proper sheet configuration.");
          setIsLoading(false);
          return;
        }

        // Check if our configured tabs exist in the available tabs (if we got the tab list)
        const hasMatchTab = availableTabs.length === 0 || availableTabs.includes(matchScoutingTab);
        const hasSuperTab = availableTabs.length === 0 || availableTabs.includes(superScoutingTab);
        const hasPitTab = availableTabs.length === 0 || availableTabs.includes(pitScoutingTab);

        // Show warning if we can't find the match scouting tab and we have a valid tab list
        if (!hasMatchTab && availableTabs.length > 0) {
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
          fetchPromises.push(fetchWithNgrokHeaders(apiUrl(`/api/sheets/headers?tab=${matchScoutingTab}${spreadsheetIdParam}`)));
          tabTypes.push('scout');
        } else {
          console.log(`Match scouting tab '${matchScoutingTab}' not found in Google Sheet`);
          // Try fallback to "Scouting" if the configured tab doesn't exist
          if (matchScoutingTab !== 'Scouting' && (availableTabs.length === 0 || availableTabs.includes('Scouting'))) {
            console.log("Trying fallback to 'Scouting' tab");
            fetchPromises.push(fetchWithNgrokHeaders(apiUrl(`/api/sheets/headers?tab=Scouting${spreadsheetIdParam}`)));
            tabTypes.push('scout');
          }
        }

        // Only fetch SuperScouting if the tab exists or we're using fallback
        if (hasSuperTab || availableTabs.length === 0) {
          fetchPromises.push(fetchWithNgrokHeaders(apiUrl(`/api/sheets/headers?tab=${superScoutingTab}&optional=true${spreadsheetIdParam}`)));
          tabTypes.push('super');
        } else {
          console.log(`Super scouting tab '${superScoutingTab}' not found in Google Sheet`);
        }

        // Only fetch PitScouting if the tab exists or we're using fallback
        if (hasPitTab || availableTabs.length === 0) {
          fetchPromises.push(fetchWithNgrokHeaders(apiUrl(`/api/sheets/headers?tab=${pitScoutingTab}&optional=true${spreadsheetIdParam}`)));
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

        // Clear any previous errors if we successfully got headers
        const totalHeaders = (scoutData.headers || []).length + (superData.headers || []).length + (pitData.headers || []).length;
        if (totalHeaders > 0) {
          setError(null);
        }

        // Initialize all headers with default 'ignore' category (auto-categorization removed)
        // This prevents overriding saved field selections when page loads
        const initialFields: { [key: string]: string } = {};
        
        [
          ...(scoutData.headers || []),
          ...(superData.headers || []),
          ...(pitData.headers || [])
        ].forEach(header => {
          // Set all fields to 'ignore' by default - saved selections will override this
          initialFields[header] = 'ignore';
        });

        // Set selected fields with defaults (saved selections will override these)
        setSelectedFields(initialFields);
        setLabelMappings({});

        // Update critical field mappings
        const newCriticalMappings = {
          team_number: [] as string[],
          match_number: [] as string[]
        };

        Object.entries(initialFields).forEach(([header, category]) => {
          if (category === 'team_number') {
            newCriticalMappings.team_number.push(header);
          } else if (category === 'match_number') {
            newCriticalMappings.match_number.push(header);
          }
        });
        setCriticalFieldMappings(newCriticalMappings);

        // Show information about available labels and instructions
        if (labels.length > 0) {
          setSuccessMessage(`Headers loaded successfully! ${labels.length} scouting labels available. Use "Auto-match Labels" button to automatically categorize fields, or set categories manually.`);
        } else {
          setSuccessMessage(`Headers loaded successfully! Set field categories manually or use "Auto-match Labels" once labels are loaded.`);
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
    
    // Set states before the async operation
    console.log('handleSaveSchema called - setting states...');
    setIsBuildingDataset(true);
    setBuildProgress('Saving field selections...');
    // Don't set isLoading here as it conflicts with overlay display
    
    // Force a re-render to ensure overlay appears
    await new Promise(resolve => setTimeout(resolve, 100));
    console.log('States should now be updated, isBuildingDataset:', true);
    
    try {
      
      // Save the schema including label mappings
      const schema = {
        field_selections: selectedFields,
        year: year,
        event_key: eventKey,
        critical_mappings: criticalFieldMappings,
        label_mappings: labelMappings
      };
      
      const response = await fetchWithNgrokHeaders(apiUrl('/api/schema/save-selections'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schema)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save schema');
      }
      
      // Show initial success message
      setBuildProgress('Field selections saved! Learning schema mappings...');
      
      // Trigger schema mapping for regular scouting
      try {
        // Learn regular scouting schema
        await fetchWithNgrokHeaders(apiUrl('/api/schema/learn'));
        
        // Show building dataset message with more detail
        setBuildProgress('Schema mappings learned! Starting dataset build...');

        // Trigger dataset build
        try {
          // Get current event key from setup API
          const setupResponse = await fetchWithNgrokHeaders(apiUrl("/api/setup/info"));
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
            setIsBuildingDataset(false);
            setIsLoading(false);
            return;
          }

          console.log('Building dataset for event:', eventKey, 'year:', yearValue);
          setBuildProgress('Sending dataset build request...');

          // Build the dataset with progress tracking
          const buildUrl = apiUrl("/api/unified/build");
          console.log('API URL:', buildUrl);
          
          const buildResponse = await fetchWithNgrokHeaders(buildUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              event_key: eventKey,
              year: yearValue,
              force_rebuild: true
            })
          });

          console.log('Build response status:', buildResponse.status);

          if (buildResponse.ok) {
            const buildData = await buildResponse.json();
            console.log('Build response data:', buildData);
            
            if (buildData.operation_id) {
              // Track progress
              setBuildProgress('Building unified dataset... This may take a moment.');
              
              // Poll for progress
              const checkProgress = async () => {
                try {
                  const progressResponse = await fetchWithNgrokHeaders(
                    apiUrl(`/api/progress/${buildData.operation_id}`)
                  );
                  
                  if (progressResponse.ok) {
                    const progressData = await progressResponse.json();
                    
                    if (progressData.status === 'completed') {
                      setBuildProgress('Dataset built successfully!');
                      setSuccessMessage('Dataset built successfully!');
                      setIsBuildingDataset(false);
                      setIsLoading(false);
                      
                      if (embedded && onComplete) {
                        // In embedded mode, wait a bit to show success before completing
                        setTimeout(() => {
                          onComplete();
                        }, 1500);
                      } else {
                        setBuildProgress('Dataset built successfully! Setup complete!');
                        setTimeout(() => {
                          navigate('/setup?step=6');
                        }, 1500);
                      }
                    } else if (progressData.status === 'failed') {
                      throw new Error(progressData.message || 'Dataset build failed');
                    } else {
                      // Still in progress, update message and check again
                      setBuildProgress(`Building dataset... ${progressData.progress}% - ${progressData.message || 'Processing'}`);
                      setTimeout(checkProgress, 1000);
                    }
                  } else {
                    // If progress check fails, wait and continue
                    setTimeout(checkProgress, 1000);
                  }
                } catch (err) {
                  console.error('Error checking progress:', err);
                  setError('Error tracking dataset build progress');
                  setIsLoading(false);
                  setIsBuildingDataset(false);
                }
              };
              
              // Start checking progress after a short delay
              setTimeout(checkProgress, 500);
            } else {
              // Fallback if no operation ID (shouldn't happen)
              setBuildProgress('Dataset build started...');
              setTimeout(() => {
                setIsBuildingDataset(false);
                setIsLoading(false);
                if (embedded && onComplete) {
                  onComplete();
                } else {
                  navigate('/setup?step=6');
                }
              }, 2000);
            }
          } else {
            const errorData = await buildResponse.json().catch(() => ({ error: 'Unknown error' }));
            console.error('Dataset build failed:', errorData);
            
            setIsBuildingDataset(false);
            setIsLoading(false);
            
            if (embedded && onComplete) {
              setError(`Dataset build failed: ${errorData.error || 'Unknown error'}. Please try again.`);
              // Don't complete if build failed
              return;
            } else {
              // Go to setup complete even if build fails
              setSuccessMessage('Field selections saved, but dataset build had issues. Setup marked as complete.');
              setTimeout(() => {
                navigate('/setup-complete');
              }, 2000);
            }
          }
        } catch (buildErr) {
          console.error('Error building dataset:', buildErr);
          setIsBuildingDataset(false);
          setIsLoading(false);
          
          if (embedded && onComplete) {
            setSuccessMessage('Field selections saved, but dataset build had issues.');
            onComplete();
          } else {
            // Go to setup complete even if build fails
            setSuccessMessage('Field selections saved, but dataset build had issues. Setup marked as complete.');
            setTimeout(() => {
              navigate('/setup-complete');
            }, 2000);
          }
        }
      } catch (schemaErr) {
        console.error('Error learning schema mappings:', schemaErr);
        setIsBuildingDataset(false);
        setIsLoading(false);
        
        if (embedded && onComplete) {
          setSuccessMessage('Field selections saved, but schema learning had issues.');
          onComplete();
        } else {
          // Still continue to setup complete even if schema learning fails
          setSuccessMessage('Field selections saved, but schema learning had issues. Setup marked as complete.');
          setTimeout(() => {
            navigate('/setup-complete');
          }, 2000);
        }
      }
    } catch (err) {
      console.error('Error saving schema:', err);
      setError('Error saving field selections');
      setIsLoading(false);
      setIsBuildingDataset(false);
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

  // Handler for when a new label is successfully added
  const handleLabelAdded = (newLabel: GameLabel) => {
    // Reload labels to get the updated list
    loadLabels();
    
    // If we were adding a label for a specific field, apply it automatically
    if (currentFieldForLabel) {
      setLabelMappings(prev => ({
        ...prev,
        [currentFieldForLabel]: newLabel
      }));
    }
    
    setSuccessMessage(`✅ Added new label "${newLabel.label}" successfully!`);
    setCurrentFieldForLabel(null);
  };

  // Handler for when a label is successfully updated
  const handleLabelUpdated = (updatedLabel: GameLabel) => {
    // Reload labels to get the updated list
    loadLabels();
    
    // Update any field mappings that were using the old label
    setLabelMappings(prev => {
      const newMappings = { ...prev };
      Object.entries(newMappings).forEach(([fieldName, label]) => {
        if (editingLabel && label.label === editingLabel.label) {
          newMappings[fieldName] = updatedLabel;
        }
      });
      return newMappings;
    });
    
    setSuccessMessage(`✅ Updated label "${updatedLabel.label}" successfully!`);
    setEditingLabel(null);
  };

  // Handler to start editing a label
  const handleEditLabel = (label: GameLabel) => {
    setEditingLabel(label);
    setCurrentFieldForLabel(null);
    setIsAddLabelModalOpen(true);
  };

  // Only show generic loading if we're not building dataset (which has its own overlay)
  if ((isLoading || labelsLoading) && !isBuildingDataset) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      <span className="ml-3">Loading field data and scouting labels...</span>
    </div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-6 relative">
      {/* Loading overlay */}
      {isBuildingDataset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
             style={{display: 'flex'}}  /* Force display */>
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full">
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <h3 className="text-lg font-semibold mb-2">Building Dataset</h3>
              <p className="text-gray-600 text-center">
                {buildProgress || 'Processing field selections and building unified dataset...'}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Please wait while we process your field selections...
              </p>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Field Selection</h1>
        
        <div className="flex items-center space-x-4">
          {labelsLoading && (
            <div className="flex items-center text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-blue-500 mr-2"></div>
              Loading labels...
            </div>
          )}
          
          {labels.length > 0 && (
            <div className="text-green-600 text-sm">
              ✅ {labels.length} scouting labels loaded
            </div>
          )}
          
          <button
            onClick={() => {
              console.log('Triggering manual re-categorization');
              // Re-run auto-categorization manually
              const updatedFields: { [key: string]: string } = {};
              const updatedLabelMappings: { [fieldHeader: string]: GameLabel } = {};
              
              [
                ...scoutingHeaders,
                ...superscoutingHeaders,
                ...pitScoutingHeaders
              ].forEach(header => {
                // Only consider labels that haven't been assigned yet
                const availableLabels = getAvailableLabelsForField(labels, updatedLabelMappings, header);
                const categorization = autoCategorizeField(header, availableLabels);
                updatedFields[header] = categorization.category;
                
                if (categorization.matchedLabel) {
                  updatedLabelMappings[header] = categorization.matchedLabel;
                }
              });
              
              setSelectedFields(updatedFields);
              setLabelMappings(updatedLabelMappings);
              
              const labelMatchCount = Object.keys(updatedLabelMappings).length;
              const duplicatePrevention = labelMatchCount < labels.length ? " (duplicate prevention applied)" : "";
              setSuccessMessage(`✨ Auto-matched ${labelMatchCount} labels with field headers from ${labels.length} available labels${duplicatePrevention}.`);
            }}
            className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
            disabled={labelsLoading}
          >
            ✨ Auto-match Labels
          </button>
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
            <span className="block mt-1">Note: You can select multiple team number and match number fields if needed.</span>
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
                  <th className="border px-4 py-2 text-left">Label Match</th>
                  <th className="border px-4 py-2 text-left">Category</th>
                </tr>
              </thead>
              <tbody>
                {scoutingHeaders.map((header, index) => {
                  const criticalType = getCriticalFieldType(header);
                  const matchedLabel = labelMappings[header];

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
                        <div className="space-y-2">
                          <select
                            value={matchedLabel ? matchedLabel.label : ''}
                            onChange={(e) => {
                              const selectedLabelName = e.target.value;
                              if (selectedLabelName === '___ADD_NEW___') {
                                setCurrentFieldForLabel(header);
                                setIsAddLabelModalOpen(true);
                              } else if (selectedLabelName) {
                                const selectedLabel = labels.find(l => l.label === selectedLabelName);
                                if (selectedLabel) {
                                  setLabelMappings(prev => ({
                                    ...prev,
                                    [header]: selectedLabel
                                  }));
                                }
                              } else {
                                setLabelMappings(prev => {
                                  const newMappings = { ...prev };
                                  delete newMappings[header];
                                  return newMappings;
                                });
                              }
                            }}
                            className="w-full p-1 border rounded text-xs"
                          >
                            <option value="">No label selected</option>
                            {getAvailableLabelsForField(labels, labelMappings, header).map(label => (
                              <option key={label.label} value={label.label}>
                                {label.label} ({label.category})
                              </option>
                            ))}
                            {/* Show currently assigned label even if it would normally be filtered out */}
                            {matchedLabel && !getAvailableLabelsForField(labels, labelMappings, header).find(l => l.label === matchedLabel.label) && (
                              <option key={matchedLabel.label} value={matchedLabel.label}>
                                {matchedLabel.label} ({matchedLabel.category}) - Currently assigned
                              </option>
                            )}
                            <option value="___ADD_NEW___" className="text-blue-600 font-medium">
                              ➕ Add New Label for "{header}"
                            </option>
                          </select>
                          
                          {matchedLabel && (
                            <div className="space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full mr-2">
                                  ✓ Selected
                                </span>
                                <button
                                  onClick={() => handleEditLabel(matchedLabel)}
                                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                                  title="Edit this label"
                                >
                                  ✏️ Edit
                                </button>
                              </div>
                              <div className="text-xs text-gray-600">
                                {matchedLabel.description}
                              </div>
                              <div className="text-xs text-gray-500">
                                Type: {matchedLabel.data_type} | Range: {matchedLabel.typical_range}
                              </div>
                            </div>
                          )}
                        </div>
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
                      <th className="border px-4 py-2 text-left">Label Match</th>
                      <th className="border px-4 py-2 text-left">Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pitScoutingHeaders.map((header, index) => {
                      const criticalType = getCriticalFieldType(header);
                      const matchedLabel = labelMappings[header];

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
                            <div className="space-y-2">
                              <select
                                value={matchedLabel ? matchedLabel.label : ''}
                                onChange={(e) => {
                                  const selectedLabelName = e.target.value;
                                  if (selectedLabelName === '___ADD_NEW___') {
                                    setCurrentFieldForLabel(header);
                                    setIsAddLabelModalOpen(true);
                                  } else if (selectedLabelName) {
                                    const selectedLabel = labels.find(l => l.label === selectedLabelName);
                                    if (selectedLabel) {
                                      setLabelMappings(prev => ({
                                        ...prev,
                                        [header]: selectedLabel
                                      }));
                                    }
                                  } else {
                                    setLabelMappings(prev => {
                                      const newMappings = { ...prev };
                                      delete newMappings[header];
                                      return newMappings;
                                    });
                                  }
                                }}
                                className="w-full p-1 border rounded text-xs"
                              >
                                <option value="">No label selected</option>
                                {getAvailableLabelsForField(labels, labelMappings, header).map(label => (
                                  <option key={label.label} value={label.label}>
                                    {label.label} ({label.category})
                                  </option>
                                ))}
                                {/* Show currently assigned label even if it would normally be filtered out */}
                                {matchedLabel && !getAvailableLabelsForField(labels, labelMappings, header).find(l => l.label === matchedLabel.label) && (
                                  <option key={matchedLabel.label} value={matchedLabel.label}>
                                    {matchedLabel.label} ({matchedLabel.category}) - Currently assigned
                                  </option>
                                )}
                                <option value="___ADD_NEW___" className="text-blue-600 font-medium">
                                  ➕ Add New Label for "{header}"
                                </option>
                              </select>
                              
                              {matchedLabel && (
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between">
                                    <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full mr-2">
                                      ✓ Selected
                                    </span>
                                    <button
                                      onClick={() => handleEditLabel(matchedLabel)}
                                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                                      title="Edit this label"
                                    >
                                      ✏️ Edit
                                    </button>
                                  </div>
                                  <div className="text-xs text-gray-600">
                                    {matchedLabel.description}
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    Type: {matchedLabel.data_type} | Range: {matchedLabel.typical_range}
                                  </div>
                                </div>
                              )}
                            </div>
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
              <p className="mb-4 text-gray-600">
                Select which fields to include in analysis and categorize them.
                These fields come from the "SuperScouting" tab in your spreadsheet.
                <span className="block mt-2 p-3 bg-blue-50 rounded border-l-4 border-blue-400 text-blue-800">
                  <strong>Note:</strong> All superscouting fields will automatically be applied to all three robots in each match.
                  No manual robot assignment is needed.
                </span>
              </p>

              <div className="mb-6">
                <table className="min-w-full border">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-4 py-2 text-left">Header</th>
                      <th className="border px-4 py-2 text-left">Label Match</th>
                      <th className="border px-4 py-2 text-left">Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {superscoutingHeaders.map((header, index) => {
                      const criticalType = getCriticalFieldType(header);
                      const matchedLabel = labelMappings[header];

                      return (
                        <tr
                          key={`super-${index}`}
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
                            <div className="space-y-2">
                              <select
                                value={matchedLabel ? matchedLabel.label : ''}
                                onChange={(e) => {
                                  const selectedLabelName = e.target.value;
                                  if (selectedLabelName === '___ADD_NEW___') {
                                    setCurrentFieldForLabel(header);
                                    setIsAddLabelModalOpen(true);
                                  } else if (selectedLabelName) {
                                    const selectedLabel = labels.find(l => l.label === selectedLabelName);
                                    if (selectedLabel) {
                                      setLabelMappings(prev => ({
                                        ...prev,
                                        [header]: selectedLabel
                                      }));
                                    }
                                  } else {
                                    setLabelMappings(prev => {
                                      const newMappings = { ...prev };
                                      delete newMappings[header];
                                      return newMappings;
                                    });
                                  }
                                }}
                                className="w-full p-1 border rounded text-xs"
                              >
                                <option value="">No label selected</option>
                                {getAvailableLabelsForField(labels, labelMappings, header).map(label => (
                                  <option key={label.label} value={label.label}>
                                    {label.label} ({label.category})
                                  </option>
                                ))}
                                {/* Show currently assigned label even if it would normally be filtered out */}
                                {matchedLabel && !getAvailableLabelsForField(labels, labelMappings, header).find(l => l.label === matchedLabel.label) && (
                                  <option key={matchedLabel.label} value={matchedLabel.label}>
                                    {matchedLabel.label} ({matchedLabel.category}) - Currently assigned
                                  </option>
                                )}
                                <option value="___ADD_NEW___" className="text-blue-600 font-medium">
                                  ➕ Add New Label for "{header}"
                                </option>
                              </select>
                              
                              {matchedLabel && (
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between">
                                    <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full mr-2">
                                      ✓ Selected
                                    </span>
                                    <button
                                      onClick={() => handleEditLabel(matchedLabel)}
                                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                                      title="Edit this label"
                                    >
                                      ✏️ Edit
                                    </button>
                                  </div>
                                  <div className="text-xs text-gray-600">
                                    {matchedLabel.description}
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    Type: {matchedLabel.data_type} | Range: {matchedLabel.typical_range}
                                  </div>
                                </div>
                              )}
                            </div>
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
          disabled={isBuildingDataset}
          className={`px-4 py-2 rounded ${
            isBuildingDataset 
              ? 'bg-gray-400 text-gray-200 cursor-not-allowed' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isBuildingDataset ? 'Processing...' : 'Save Field Selections'}
        </button>
      </div>
      
      {/* Add/Edit Label Modal */}
      <AddLabelModal
        isOpen={isAddLabelModalOpen}
        onClose={() => {
          setIsAddLabelModalOpen(false);
          setCurrentFieldForLabel(null);
          setEditingLabel(null);
        }}
        onLabelAdded={handleLabelAdded}
        onLabelUpdated={handleLabelUpdated}
        fieldHeader={currentFieldForLabel || undefined}
        editingLabel={editingLabel || undefined}
      />
    </div>
  );
}

export default FieldSelection;