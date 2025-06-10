// frontend/src/pages/FieldSelection/types.ts

export interface FieldCategory {
  key: string;
  label: string;
  description: string;
}

export interface CriticalField {
  key: string;
  label: string;
  description: string;
  requiredPattern: RegExp;
}

export interface SheetConfig {
  id: string;
  spreadsheet_id: string;
  event_key: string;
  match_scouting_sheet?: string;
  super_scouting_sheet?: string;
  pit_scouting_sheet?: string;
}

export interface FieldMapping {
  [key: string]: string;
}

export interface CriticalFieldMappings {
  team_number: string[];
  match_number: string[];
}

export interface StatboticsField {
  field_name: string;
  description: string;
  data_type: string;
  category: string;
}

export interface FieldSelectionState {
  // Headers from sheets
  scoutingHeaders: string[];
  superscoutingHeaders: string[];
  pitScoutingHeaders: string[];
  
  // Field mappings
  selectedFields: FieldMapping;
  criticalFieldMappings: CriticalFieldMappings;
  
  // UI state
  activeCategory: string;
  isLoading: boolean;
  error: string | null;
  successMessage: string | null;
  validationWarning: string | null;
  year: number;
  
  // Statbotics integration
  statboticsFields: StatboticsField[];
  selectedStatboticsFields: string[];
  enableStatbotics: boolean;
}

export interface FieldSelectionActions {
  setScoutingHeaders: (headers: string[]) => void;
  setSuperscoutingHeaders: (headers: string[]) => void;
  setPitScoutingHeaders: (headers: string[]) => void;
  setSelectedFields: (fields: FieldMapping) => void;
  setCriticalFieldMappings: (mappings: CriticalFieldMappings) => void;
  setActiveCategory: (category: string) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSuccessMessage: (message: string | null) => void;
  setValidationWarning: (warning: string | null) => void;
  setYear: (year: number) => void;
  setStatboticsFields: (fields: StatboticsField[]) => void;
  setSelectedStatboticsFields: (fields: string[]) => void;
  setEnableStatbotics: (enabled: boolean) => void;
  
  // Actions
  fetchHeaders: () => Promise<void>;
  fetchStatboticsFields: () => Promise<void>;
  saveFieldSelections: () => Promise<void>;
  autoCategorizeFields: () => void;
  validateSelections: () => boolean;
}

// Constants
export const CRITICAL_FIELDS: CriticalField[] = [
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

export const FIELD_CATEGORIES: FieldCategory[] = [
  { key: 'team_info', label: 'Team Information', description: 'Basic team identifiers and match metadata' },
  { key: 'auto', label: 'Autonomous', description: 'Robot actions during the autonomous period' },
  { key: 'teleop', label: 'Teleop', description: 'Robot actions during the teleop period' },
  { key: 'endgame', label: 'Endgame', description: 'Robot actions during the endgame period' },
  { key: 'strategy', label: 'Strategy', description: 'Strategic assessment and qualitative observations' },
  { key: 'other', label: 'Other', description: 'Any additional fields that don\'t fit above categories' },
];

export interface Category {
  id: string;
  label: string;
  description: string;
  icon: string;
}

export const DATA_CATEGORIES: Category[] = [
  { id: 'match', label: 'Match Scouting', description: 'Data collected during matches', icon: '📊' },
  { id: 'pit', label: 'Pit Scouting', description: 'Data collected during pit visits', icon: '🔧' },
  { id: 'super', label: 'Super Scouting', description: 'Qualitative observations from experienced scouts', icon: '🔍' },
  { id: 'critical', label: 'Critical Fields', description: 'Required fields for proper data validation', icon: '⚠️' },
];