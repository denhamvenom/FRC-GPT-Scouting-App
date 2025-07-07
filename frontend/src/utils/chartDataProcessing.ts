import { UnifiedDataResponse, TeamData, TeamScoutingData } from '../hooks/useUnifiedData';
import { ProcessedMetric } from '../hooks/useFieldMetadata';

// TypeScript interfaces for chart data
export interface TeamMetrics {
  team_number: number;
  team_name: string;
  metrics: { [metricName: string]: number };
  averages: { [metricName: string]: number };
  totals: { [metricName: string]: number };
  match_count: number;
}

export interface RadarChartDataPoint {
  metric: string;
  [teamKey: string]: number | string; // Dynamic team keys like 'team_1234'
}

export interface ChartDataProcessingOptions {
  normalizationMode: 'none' | 'by_team_max' | 'by_global_max' | 'by_percentile';
  selectedMetrics: string[];
  selectedTeams: number[];
  aggregationMode: 'average' | 'total' | 'max' | 'last_match';
  excludeOutliers?: {
    enabled: boolean;
    excludeLowest: number;
    excludeHighest: number;
  };
}

// Extract numeric metrics from team scouting data with outlier exclusion
export const extractTeamMetrics = (
  teamData: TeamData, 
  selectedMetrics: string[], 
  excludeOutliers?: ChartDataProcessingOptions['excludeOutliers'],
  aggregationMode: ChartDataProcessingOptions['aggregationMode'] = 'average'
): TeamMetrics => {
  const metrics: { [metricName: string]: number[] } = {};
  const averages: { [metricName: string]: number } = {};
  const totals: { [metricName: string]: number } = {};
  
  // Initialize metric arrays
  selectedMetrics.forEach(metric => {
    metrics[metric] = [];
  });

  // Extract data from all matches
  teamData.scouting_data.forEach(matchData => {
    selectedMetrics.forEach(metric => {
      const value = matchData[metric];
      if (typeof value === 'number') {
        metrics[metric].push(value);
      }
    });
  });

  // Apply outlier exclusion if enabled
  if (excludeOutliers?.enabled) {
    selectedMetrics.forEach(metric => {
      const values = metrics[metric];
      if (values.length > 0) {
        const originalLength = values.length;
        // Sort values to identify outliers
        const sortedValues = [...values].sort((a, b) => a - b);
        
        // Calculate how many values to exclude
        const excludeFromStart = Math.min(excludeOutliers.excludeLowest, Math.floor(sortedValues.length / 3));
        const excludeFromEnd = Math.min(excludeOutliers.excludeHighest, Math.floor(sortedValues.length / 3));
        
        // Only exclude if we have enough data points
        if (sortedValues.length > (excludeFromStart + excludeFromEnd + 1)) {
          const filteredValues = sortedValues.slice(excludeFromStart, sortedValues.length - excludeFromEnd);
          metrics[metric] = filteredValues;
          
          console.log(`Outlier exclusion for ${metric} on team ${teamData.team_number}:`, {
            originalCount: originalLength,
            filteredCount: filteredValues.length,
            excludedLowest: excludeFromStart,
            excludedHighest: excludeFromEnd,
            originalRange: `[${sortedValues[0].toFixed(1)} - ${sortedValues[sortedValues.length - 1].toFixed(1)}]`,
            filteredRange: `[${filteredValues[0].toFixed(1)} - ${filteredValues[filteredValues.length - 1].toFixed(1)}]`
          });
        }
        // If not enough data points, keep all values
      }
    });
  }

  // Calculate values based on aggregation mode
  selectedMetrics.forEach(metric => {
    const values = metrics[metric];
    if (values.length > 0) {
      let aggregatedValue = 0;
      
      switch (aggregationMode) {
        case 'average':
          aggregatedValue = values.reduce((sum, val) => sum + val, 0) / values.length;
          break;
        case 'total':
          aggregatedValue = values.reduce((sum, val) => sum + val, 0);
          break;
        case 'max':
          aggregatedValue = Math.max(...values);
          break;
        case 'last_match':
          // Get the most recent match (last in the array)
          aggregatedValue = values[values.length - 1];
          break;
        default:
          aggregatedValue = values.reduce((sum, val) => sum + val, 0) / values.length;
      }
      
      // Store the aggregated value in averages (this is what gets used for chart display)
      averages[metric] = aggregatedValue;
      // Still calculate totals for reference
      totals[metric] = values.reduce((sum, val) => sum + val, 0);
    } else {
      averages[metric] = 0;
      totals[metric] = 0;
    }
  });

  return {
    team_number: teamData.team_number,
    team_name: teamData.nickname,
    metrics,
    averages,
    totals,
    match_count: teamData.scouting_data.length
  };
};

// Get all available numeric metrics from unified data
export const getAvailableMetrics = (unifiedData: UnifiedDataResponse): string[] => {
  const allMetrics = new Set<string>();
  
  // Sample from first team's first match to get available fields
  const firstTeam = Object.values(unifiedData.teams)[0];
  if (firstTeam && firstTeam.scouting_data.length > 0) {
    const sampleMatch = firstTeam.scouting_data[0];
    
    Object.entries(sampleMatch).forEach(([key, value]) => {
      // Include only numeric fields, excluding identifiers
      if (typeof value === 'number' && 
          key !== 'match_number' && 
          key !== 'qual_number' && 
          key !== 'team_number') {
        allMetrics.add(key);
      }
    });
  }

  return Array.from(allMetrics);
};

// Normalize metric values for radar chart (0-100 scale)
export const normalizeMetricValues = (
  teamMetrics: TeamMetrics[],
  selectedMetrics: string[],
  mode: ChartDataProcessingOptions['normalizationMode']
): { [teamKey: string]: { [metric: string]: number } } => {
  const normalized: { [teamKey: string]: { [metric: string]: number } } = {};
  
  // Calculate normalization factors for each metric
  const normalizationFactors: { [metric: string]: number } = {};
  
  selectedMetrics.forEach(metric => {
    let maxValue = 0;
    
    if (mode === 'by_global_max') {
      // Find global maximum across all teams
      teamMetrics.forEach(team => {
        const value = team.averages[metric] || 0;
        maxValue = Math.max(maxValue, value);
      });
    } else if (mode === 'by_percentile') {
      // Use 95th percentile as max (more stable than absolute max)
      const allValues = teamMetrics.map(team => team.averages[metric] || 0).sort((a, b) => b - a);
      const percentile95Index = Math.floor(allValues.length * 0.05);
      maxValue = allValues[percentile95Index] || 1;
    }
    
    // Ensure we don't divide by zero
    normalizationFactors[metric] = maxValue > 0 ? maxValue : 1;
  });

  console.log('Normalization factors:', {
    mode,
    factors: normalizationFactors
  });

  // Normalize each team's metrics
  teamMetrics.forEach(team => {
    const teamKey = `team_${team.team_number}`;
    normalized[teamKey] = {};
    
    selectedMetrics.forEach(metric => {
      const rawValue = team.averages[metric] || 0;
      
      if (mode === 'by_team_max') {
        // Normalize by the team's own maximum across all metrics
        const teamMax = Math.max(...selectedMetrics.map(m => team.averages[m] || 0));
        normalized[teamKey][metric] = teamMax > 0 ? (rawValue / teamMax) * 100 : 0;
      } else if (mode === 'by_global_max' || mode === 'by_percentile') {
        // Normalize by global maximum or percentile
        normalized[teamKey][metric] = (rawValue / normalizationFactors[metric]) * 100;
      } else {
        // No normalization - use raw values
        normalized[teamKey][metric] = rawValue;
      }
    });
  });
  
  // Log sample normalized values for verification
  if (teamMetrics.length > 0 && selectedMetrics.length > 0) {
    const sampleTeam = teamMetrics[0];
    const sampleMetric = selectedMetrics[0];
    console.log(`Normalization example - Team ${sampleTeam.team_number}, ${sampleMetric}:`, {
      rawValue: sampleTeam.averages[sampleMetric],
      normalizedValue: normalized[`team_${sampleTeam.team_number}`][sampleMetric],
      normalizationMode: mode
    });
  }

  return normalized;
};

// Convert team metrics to radar chart format
export const convertToRadarChartData = (
  teamMetrics: TeamMetrics[],
  selectedMetrics: string[],
  options: ChartDataProcessingOptions
): RadarChartDataPoint[] => {
  const normalizedData = normalizeMetricValues(teamMetrics, selectedMetrics, options.normalizationMode);
  
  return selectedMetrics.map(metric => {
    const dataPoint: RadarChartDataPoint = {
      metric: metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    };
    
    // Add each team's normalized value for this metric
    teamMetrics.forEach(team => {
      const teamKey = `team_${team.team_number}`;
      dataPoint[teamKey] = normalizedData[teamKey][metric] || 0;
    });
    
    return dataPoint;
  });
};

// Calculate team statistics for display
export const calculateTeamStatistics = (
  teamMetrics: TeamMetrics[],
  selectedMetrics: string[]
): { [teamKey: string]: { avg: number; max: number; min: number; consistency: number } } => {
  const stats: { [teamKey: string]: { avg: number; max: number; min: number; consistency: number } } = {};
  
  teamMetrics.forEach(team => {
    const teamKey = `team_${team.team_number}`;
    const values = selectedMetrics.map(metric => team.averages[metric] || 0);
    
    if (values.length > 0) {
      const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
      const max = Math.max(...values);
      const min = Math.min(...values);
      
      // Calculate consistency (1 - coefficient of variation)
      const stdDev = Math.sqrt(values.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / values.length);
      const consistency = avg > 0 ? Math.max(0, 1 - (stdDev / avg)) : 0;
      
      stats[teamKey] = {
        avg: Math.round(avg * 100) / 100,
        max: Math.round(max * 100) / 100,
        min: Math.round(min * 100) / 100,
        consistency: Math.round(consistency * 100) / 100
      };
    }
  });
  
  return stats;
};

// Process unified data for radar chart visualization
export const processUnifiedDataForChart = (
  unifiedData: UnifiedDataResponse,
  options: ChartDataProcessingOptions
): {
  chartData: RadarChartDataPoint[];
  teamMetrics: TeamMetrics[];
  statistics: { [teamKey: string]: { avg: number; max: number; min: number; consistency: number } };
  availableMetrics: string[];
} => {
  // Extract team metrics for selected teams
  const teamMetrics: TeamMetrics[] = [];
  
  options.selectedTeams.forEach(teamNumber => {
    const teamData = unifiedData.teams[teamNumber.toString()];
    if (teamData && teamData.scouting_data.length > 0) {
      teamMetrics.push(extractTeamMetrics(teamData, options.selectedMetrics, options.excludeOutliers, options.aggregationMode));
    }
  });

  // Convert to radar chart format
  const chartData = convertToRadarChartData(teamMetrics, options.selectedMetrics, options);
  
  // Calculate statistics
  const statistics = calculateTeamStatistics(teamMetrics, options.selectedMetrics);
  
  // Get all available metrics
  const availableMetrics = getAvailableMetrics(unifiedData);

  return {
    chartData,
    teamMetrics,
    statistics,
    availableMetrics
  };
};

// Helper function to get team colors for charts
export const getTeamColors = (teamCount: number): string[] => {
  const colors = [
    '#3B82F6', // Blue
    '#EF4444', // Red
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#8B5CF6', // Purple
    '#F97316', // Orange
    '#EC4899', // Pink
    '#6B7280', // Gray
  ];
  
  return colors.slice(0, teamCount);
};

// Helper function to format metric names for display
export const formatMetricName = (metricName: string): string => {
  return metricName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .replace(/([A-Z])/g, ' $1')
    .trim();
};

// Helper function to validate chart data
export const validateChartData = (
  chartData: RadarChartDataPoint[],
  selectedMetrics: string[],
  selectedTeams: number[]
): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  
  if (selectedMetrics.length === 0) {
    errors.push('At least one metric must be selected');
  }
  
  if (selectedTeams.length === 0) {
    errors.push('At least one team must be selected');
  }
  
  if (selectedTeams.length > 6) {
    errors.push('Maximum of 6 teams can be compared at once');
  }
  
  if (chartData.length === 0) {
    errors.push('No data available for the selected metrics and teams');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};