import { UnifiedDataResponse, TeamData, TeamScoutingData } from '../hooks/useUnifiedData';
import { HeatmapData, HeatmapCell } from '../types/graphicalAnalysis';

// Sort function for teams by average score
const sortTeamsByAverageScore = (
  teams: Array<{ teamNumber: number; nickname: string; avgScore: number }>
): Array<{ teamNumber: number; nickname: string; avgScore: number }> => {
  return [...teams].sort((a, b) => b.avgScore - a.avgScore);
};

// Extract unique match numbers from selected teams' scouting data
const extractMatchNumbers = (unifiedData: UnifiedDataResponse, selectedTeams: number[]): number[] => {
  const matchNumbers = new Set<number>();
  
  selectedTeams.forEach(teamNumber => {
    const team = unifiedData.teams[teamNumber.toString()];
    if (team && team.scouting_data) {
      team.scouting_data.forEach(match => {
        if (typeof match.match_number === 'number') {
          matchNumbers.add(match.match_number);
        }
      });
    }
  });
  
  return Array.from(matchNumbers).sort((a, b) => a - b);
};

// Calculate metric value based on show mode
const calculateMetricValue = (
  matchData: TeamScoutingData,
  selectedMetric: string,
  showMode: 'auto' | 'teleop' | 'total'
): number => {
  // First, try to get the metric directly as it might already include the prefix
  const directValue = matchData[selectedMetric];
  if (typeof directValue === 'number') {
    return directValue;
  }
  
  if (showMode === 'total') {
    // For total mode, check if this is a metric that can be summed
    const metricBase = selectedMetric.replace(/^(auto_|teleop_)/, '');
    
    // Try to find and sum auto and teleop versions
    const autoKey = `auto_${metricBase}`;
    const teleopKey = `teleop_${metricBase}`;
    
    const autoValue = matchData[autoKey];
    const teleopValue = matchData[teleopKey];
    
    if (typeof autoValue === 'number' || typeof teleopValue === 'number') {
      return (typeof autoValue === 'number' ? autoValue : 0) + 
             (typeof teleopValue === 'number' ? teleopValue : 0);
    }
    
    // If no auto/teleop versions exist, return 0
    return 0;
  }
  
  // For auto or teleop mode, get the prefixed metric
  const prefixedMetric = `${showMode}_${selectedMetric}`;
  const value = matchData[prefixedMetric];
  
  return typeof value === 'number' ? value : 0;
};

// Process unified data into heatmap format with sequential team matches
export const processDataForHeatmap = (
  unifiedData: UnifiedDataResponse,
  selectedTeams: number[],
  selectedMetric: string,
  showMode: 'auto' | 'teleop' | 'total',
  normalizationMode: 'match' | 'global'
): HeatmapData => {
  const cells: HeatmapCell[] = [];
  const teamAverages: { [teamNumber: number]: { total: number; count: number } } = {};
  
  // Initialize value tracking
  let globalMin = Infinity;
  let globalMax = -Infinity;
  let maxTeamMatches = 0;
  
  // First pass: collect all team data and find max match count
  const teamMatchSequences: { [teamNumber: number]: { matchNumber: number; data: TeamScoutingData }[] } = {};
  
  selectedTeams.forEach(teamNumber => {
    const teamData = unifiedData.teams[teamNumber.toString()];
    if (!teamData) {
      console.warn(`Team ${teamNumber} not found in unified data`);
      // Still initialize the average data for this team
      teamAverages[teamNumber] = { total: 0, count: 0 };
      return;
    }
    
    teamAverages[teamNumber] = { total: 0, count: 0 };
    
    // Get all matches for this team, sorted chronologically
    const teamMatches = teamData.scouting_data
      .filter(match => typeof match.match_number === 'number')
      .map(match => ({ matchNumber: match.match_number as number, data: match }))
      .sort((a, b) => a.matchNumber - b.matchNumber);
    
    teamMatchSequences[teamNumber] = teamMatches;
    maxTeamMatches = Math.max(maxTeamMatches, teamMatches.length);
    
    console.log(`Team ${teamNumber}: ${teamMatches.length} matches found`);
    
    // Process each match for this team
    teamMatches.forEach((match, sequenceIndex) => {
      const value = calculateMetricValue(match.data, selectedMetric, showMode);
      
      // Debug log for teams with no metric data
      if (value === 0 && sequenceIndex === 0) {
        console.log(`Team ${teamNumber} match ${match.matchNumber} - metric value: ${value}, available keys:`, 
          Object.keys(match.data).filter(k => typeof match.data[k] === 'number').slice(0, 20));
      }
      
      // Debug log for first team and match
      if (teamNumber === selectedTeams[0] && sequenceIndex === 0) {
        console.log('Sample metric calculation:', {
          teamNumber,
          matchNumber: match.matchNumber,
          sequenceIndex,
          selectedMetric,
          value,
          matchDataKeys: Object.keys(match.data).filter(k => typeof match.data[k] === 'number')
        });
      }
      
      // Track values for normalization
      globalMin = Math.min(globalMin, value);
      globalMax = Math.max(globalMax, value);
      
      // Track for team average
      teamAverages[teamNumber].total += value;
      teamAverages[teamNumber].count += 1;
      
      // Debug for team 8044
      if (teamNumber === 8044 && sequenceIndex < 3) {
        console.log(`Team 8044 match ${match.matchNumber}: value=${value}, running total=${teamAverages[teamNumber].total}`);
      }
      
      // Create cell with sequence index as position
      cells.push({
        teamNumber,
        matchNumber: match.matchNumber,
        value,
        isValid: true,
        matchType: match.data.match_type,
        allianceColor: match.data.alliance_color as 'red' | 'blue' | undefined
      });
    });
  });
  
  console.log('Processing heatmap data:', {
    selectedMetric,
    showMode,
    maxTeamMatches,
    teamCount: selectedTeams.length,
    teamMatchCounts: Object.entries(teamMatchSequences).map(([team, matches]) => 
      ({ team, matchCount: matches.length }))
  });
  
  // Calculate team averages and prepare sorted team list
  const teamsWithAverages = selectedTeams.map(teamNumber => {
    const teamData = unifiedData.teams[teamNumber.toString()];
    const avgData = teamAverages[teamNumber];
    const avgScore = avgData && avgData.count > 0 ? avgData.total / avgData.count : 0;
    
    // Debug missing teams
    if (!avgData) {
      console.warn(`Team ${teamNumber} has no average data in teamAverages`);
    }
    
    return {
      teamNumber,
      nickname: teamData?.nickname || `Team ${teamNumber}`,
      avgScore
    };
  });
  
  console.log('Teams before sorting:', teamsWithAverages.map(t => ({ 
    team: t.teamNumber, 
    avgScore: t.avgScore.toFixed(2) 
  })));
  
  // Sort teams by average score (highest first)
  const sortedTeams = sortTeamsByAverageScore(teamsWithAverages);
  
  console.log('Teams after sorting:', sortedTeams.map(t => ({ 
    team: t.teamNumber, 
    avgScore: t.avgScore.toFixed(2) 
  })));
  
  // Create sequential match positions (1st match, 2nd match, etc.)
  const matches = Array.from({ length: maxTeamMatches }, (_, index) => ({
    matchNumber: index + 1, // Use position number instead of actual match number
    displayName: `Match ${index + 1}`
  }));
  
  // Ensure we have valid min/max values
  if (globalMin === Infinity) globalMin = 0;
  if (globalMax === -Infinity) globalMax = 100;
  
  return {
    cells,
    teams: sortedTeams,
    matches,
    valueRange: { 
      min: globalMin,
      max: globalMax
    },
    colorScale: 'greenToRed'
  };
};

// Get color for a cell value based on the scale
export const getHeatmapCellColor = (
  value: number,
  min: number,
  max: number,
  isValid: boolean,
  colorScale: 'greenToRed' | 'blueToRed' | 'sequential' = 'greenToRed'
): string => {
  if (!isValid) {
    return '#e5e7eb'; // Gray for missing data
  }
  
  // Normalize value to 0-1 range
  const range = max - min;
  const normalized = range > 0 ? (value - min) / range : 0.5;
  
  if (colorScale === 'greenToRed') {
    // Green (good) to Red (bad) - inverted so high values are green
    const hue = normalized * 120; // 0 (red) to 120 (green)
    const saturation = 70 + normalized * 20; // 70-90%
    const lightness = 45 + (1 - normalized) * 15; // 45-60%
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  } else if (colorScale === 'blueToRed') {
    // Blue (low) to Red (high)
    const r = Math.round(255 * normalized);
    const b = Math.round(255 * (1 - normalized));
    const g = 0;
    return `rgb(${r}, ${g}, ${b})`;
  } else {
    // Sequential scale (light to dark blue)
    const lightness = 90 - normalized * 50; // 90% to 40%
    return `hsl(210, 70%, ${lightness}%)`;
  }
};

// Format value for display
export const formatHeatmapValue = (value: number, isValid: boolean): string => {
  if (!isValid) return '-';
  
  // Round to 1 decimal place if needed
  if (value % 1 !== 0) {
    return value.toFixed(1);
  }
  
  return value.toString();
};

// Calculate statistics for a specific metric across all teams
export const calculateHeatmapStatistics = (
  cells: HeatmapCell[]
): {
  mean: number;
  median: number;
  stdDev: number;
  percentiles: { p25: number; p50: number; p75: number; p95: number };
} => {
  const validValues = cells
    .filter(cell => cell.isValid)
    .map(cell => cell.value)
    .sort((a, b) => a - b);
  
  if (validValues.length === 0) {
    return {
      mean: 0,
      median: 0,
      stdDev: 0,
      percentiles: { p25: 0, p50: 0, p75: 0, p95: 0 }
    };
  }
  
  // Calculate mean
  const mean = validValues.reduce((sum, val) => sum + val, 0) / validValues.length;
  
  // Calculate median
  const midIndex = Math.floor(validValues.length / 2);
  const median = validValues.length % 2 === 0
    ? (validValues[midIndex - 1] + validValues[midIndex]) / 2
    : validValues[midIndex];
  
  // Calculate standard deviation
  const variance = validValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / validValues.length;
  const stdDev = Math.sqrt(variance);
  
  // Calculate percentiles
  const getPercentile = (p: number) => {
    const index = Math.ceil(validValues.length * p) - 1;
    return validValues[Math.max(0, Math.min(index, validValues.length - 1))];
  };
  
  return {
    mean,
    median,
    stdDev,
    percentiles: {
      p25: getPercentile(0.25),
      p50: median,
      p75: getPercentile(0.75),
      p95: getPercentile(0.95)
    }
  };
};