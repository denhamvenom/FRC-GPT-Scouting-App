// TypeScript types for Graphical Analysis components

// Re-export from other modules for convenience
export type { 
  UnifiedDataResponse, 
  TeamData, 
  TeamScoutingData,
  UseUnifiedDataReturn 
} from '../hooks/useUnifiedData';

export type { 
  FieldMetadata, 
  FieldSelection, 
  FieldLabelMapping, 
  ProcessedMetric, 
  MetricsByCategory,
  UseFieldMetadataReturn 
} from '../hooks/useFieldMetadata';

export type { 
  TeamMetrics, 
  RadarChartDataPoint, 
  ChartDataProcessingOptions 
} from '../utils/chartDataProcessing';

// Component state interfaces
export interface GraphicalAnalysisState {
  selectedMetrics: string[];
  selectedTeams: number[];
  normalizationMode: 'none' | 'by_team_max' | 'by_global_max' | 'by_percentile';
  aggregationMode: 'average' | 'total' | 'max' | 'last_match';
  showDataTable: boolean;
  expandedCategories: Set<string>;
  excludeOutliers: {
    enabled: boolean;
    excludeLowest: number;
    excludeHighest: number;
  };
}

// UI Component props
export interface MetricSelectionProps {
  metricsByCategory: MetricsByCategory;
  selectedMetrics: string[];
  onMetricToggle: (metric: string) => void;
  onCategoryToggle: (category: string) => void;
  expandedCategories: Set<string>;
  loading?: boolean;
}

export interface TeamSelectionProps {
  availableTeams: Array<{ team_number: number; nickname: string }>;
  selectedTeams: number[];
  onTeamToggle: (teamNumber: number) => void;
  onClearAll: () => void;
  maxTeams?: number;
  loading?: boolean;
}

export interface ChartControlsProps {
  normalizationMode: GraphicalAnalysisState['normalizationMode'];
  onNormalizationChange: (mode: GraphicalAnalysisState['normalizationMode']) => void;
  aggregationMode: GraphicalAnalysisState['aggregationMode'];
  onAggregationChange: (mode: GraphicalAnalysisState['aggregationMode']) => void;
  showDataTable: boolean;
  onDataTableToggle: (show: boolean) => void;
  onExportChart?: () => void;
  onClearSelections?: () => void;
}

export interface RadarChartVisualizationProps {
  chartData: RadarChartDataPoint[];
  selectedTeams: number[];
  teamNames: { [teamNumber: number]: string };
  loading?: boolean;
  error?: string | null;
  height?: number;
}

export interface DataTableViewProps {
  teamMetrics: TeamMetrics[];
  selectedMetrics: string[];
  statistics: { [teamKey: string]: { avg: number; max: number; min: number; consistency: number } };
  onSortChange?: (metric: string, direction: 'asc' | 'desc') => void;
}

// Chart configuration
export interface ChartConfig {
  colors: string[];
  responsive: boolean;
  animationDuration: number;
  gridOpacity: number;
  labelFontSize: number;
  legendPosition: 'top' | 'bottom' | 'left' | 'right';
}

// Preset metric groups
export interface MetricPreset {
  id: string;
  name: string;
  description: string;
  metrics: string[];
  category?: string;
}

// Analysis results
export interface AnalysisResult {
  teamRankings: Array<{
    team_number: number;
    team_name: string;
    overall_score: number;
    strengths: string[];
    weaknesses: string[];
  }>;
  insights: Array<{
    type: 'strength' | 'weakness' | 'opportunity' | 'balanced';
    message: string;
    team_number?: number;
    metric?: string;
  }>;
  recommendations: Array<{
    category: string;
    suggestion: string;
    priority: 'high' | 'medium' | 'low';
  }>;
}

// Error handling
export interface GraphicalAnalysisError {
  code: string;
  message: string;
  details?: string;
  suggestions?: string[];
}

// Settings and preferences
export interface GraphicalAnalysisSettings {
  defaultNormalizationMode: GraphicalAnalysisState['normalizationMode'];
  defaultAggregationMode: GraphicalAnalysisState['aggregationMode'];
  maxTeamsForComparison: number;
  chartHeight: number;
  autoRefreshInterval: number;
  showTooltips: boolean;
  exportFormat: 'png' | 'svg' | 'pdf';
  colorScheme: 'default' | 'colorblind' | 'high-contrast';
}

// Local storage keys
export const STORAGE_KEYS = {
  SELECTED_METRICS: 'graphical-analysis-selected-metrics',
  SELECTED_TEAMS: 'graphical-analysis-selected-teams',
  NORMALIZATION_MODE: 'graphical-analysis-normalization-mode',
  AGGREGATION_MODE: 'graphical-analysis-aggregation-mode',
  EXPANDED_CATEGORIES: 'graphical-analysis-expanded-categories',
  SETTINGS: 'graphical-analysis-settings'
} as const;

// Default values
export const DEFAULT_SETTINGS: GraphicalAnalysisSettings = {
  defaultNormalizationMode: 'by_global_max',
  defaultAggregationMode: 'average',
  maxTeamsForComparison: 6,
  chartHeight: 400,
  autoRefreshInterval: 0, // 0 = no auto refresh
  showTooltips: true,
  exportFormat: 'png',
  colorScheme: 'default'
};

export const DEFAULT_CHART_CONFIG: ChartConfig = {
  colors: ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#F97316'],
  responsive: true,
  animationDuration: 300,
  gridOpacity: 0.2,
  labelFontSize: 12,
  legendPosition: 'bottom'
};

// Common metric presets
export const METRIC_PRESETS: MetricPreset[] = [
  {
    id: 'scoring-all',
    name: 'All Scoring',
    description: 'All scoring metrics across all game periods',
    metrics: ['Auto Total Points', 'teleop_total_points', 'endgame_total_points']
  },
  {
    id: 'autonomous',
    name: 'Autonomous',
    description: 'Autonomous period performance',
    metrics: ['auto_coral_L1_scored', 'auto_coral_L2_scored', 'auto_coral_L3_scored', 'auto_coral_L4_scored', 'auto_net_score', 'auto_algae_processor_scored']
  },
  {
    id: 'teleop',
    name: 'Teleop',
    description: 'Teleoperated period performance',
    metrics: ['teleop_coral_L1_scored', 'teleop_coral_L2_scored', 'teleop_coral_L3_scored', 'teleop_coral_L4_scored', 'teleop_algae_processor_scored']
  },
  {
    id: 'endgame',
    name: 'Endgame',
    description: 'Endgame period performance',
    metrics: ['endgame_total_points']
  },
  {
    id: 'coral-scoring',
    name: 'Coral Scoring',
    description: 'All coral scoring metrics',
    metrics: ['auto_coral_L1_scored', 'auto_coral_L2_scored', 'auto_coral_L3_scored', 'auto_coral_L4_scored', 'teleop_coral_L1_scored', 'teleop_coral_L2_scored', 'teleop_coral_L3_scored', 'teleop_coral_L4_scored']
  },
  {
    id: 'algae-scoring',
    name: 'Algae Scoring',
    description: 'All algae scoring metrics',
    metrics: ['auto_algae_processor_scored', 'teleop_algae_processor_scored', 'auto_net_score']
  }
];

// Validation functions
export const validateMetricSelection = (selectedMetrics: string[], availableMetrics: string[]): GraphicalAnalysisError | null => {
  if (selectedMetrics.length === 0) {
    return {
      code: 'NO_METRICS_SELECTED',
      message: 'At least one metric must be selected',
      suggestions: ['Select one or more metrics from the available options']
    };
  }
  
  if (selectedMetrics.length > 12) {
    return {
      code: 'TOO_MANY_METRICS',
      message: 'Too many metrics selected for clear visualization',
      suggestions: ['Select fewer metrics (maximum 12 recommended)', 'Use metric presets for common combinations']
    };
  }
  
  const invalidMetrics = selectedMetrics.filter(metric => !availableMetrics.includes(metric));
  if (invalidMetrics.length > 0) {
    return {
      code: 'INVALID_METRICS',
      message: 'Some selected metrics are not available in the current dataset',
      details: `Invalid metrics: ${invalidMetrics.join(', ')}`,
      suggestions: ['Refresh the page to reload available metrics', 'Clear selection and reselect metrics']
    };
  }
  
  return null;
};

export const validateTeamSelection = (selectedTeams: number[], availableTeams: Array<{ team_number: number; nickname: string }>, maxTeams: number = 6): GraphicalAnalysisError | null => {
  if (selectedTeams.length === 0) {
    return {
      code: 'NO_TEAMS_SELECTED',
      message: 'At least one team must be selected',
      suggestions: ['Select one or more teams from the dropdown']
    };
  }
  
  if (selectedTeams.length > maxTeams) {
    return {
      code: 'TOO_MANY_TEAMS',
      message: `Too many teams selected (maximum ${maxTeams})`,
      suggestions: ['Reduce the number of selected teams for better visualization', 'Compare teams in smaller groups']
    };
  }
  
  const availableTeamNumbers = availableTeams.map(team => team.team_number);
  const invalidTeams = selectedTeams.filter(teamNumber => !availableTeamNumbers.includes(teamNumber));
  if (invalidTeams.length > 0) {
    return {
      code: 'INVALID_TEAMS',
      message: 'Some selected teams are not available in the current dataset',
      details: `Invalid teams: ${invalidTeams.join(', ')}`,
      suggestions: ['Refresh the page to reload available teams', 'Clear selection and reselect teams']
    };
  }
  
  return null;
};