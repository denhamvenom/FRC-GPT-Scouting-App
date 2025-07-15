import React, { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { TeamData } from '../hooks/useUnifiedData';
import { useFieldMetadata } from '../hooks/useFieldMetadata';

interface ScoringDistributionProps {
  teams: TeamData[];
  selectedTeams: number[];
  excludeOutliers?: {
    enabled: boolean;
    excludeLowest: number;
    excludeHighest: number;
  };
  height?: number;
}

interface ScoringCategory {
  key: string;
  label: string;
  color: string;
  fields: string[];
}

interface TeamScoringData {
  name: string;
  teamNumber: number;
  categoryTotals: { [key: string]: number };
  total: number;
  matchesPlayed: number;
  efficiency: { [key: string]: number };
}

type SortBy = 'total' | 'teamNumber' | string; // string for dynamic category sorting
type ViewMode = 'absolute' | 'percentage';

// Dynamic color palette for categories
const COLOR_PALETTE = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
  '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43',
  '#C44569', '#778BEB', '#786FA6', '#F8B500', '#3D5A80'
];

const ScoringDistribution: React.FC<ScoringDistributionProps> = ({
  teams,
  selectedTeams,
  excludeOutliers,
  height = 500
}) => {
  const [sortBy, setSortBy] = useState<SortBy>('total');
  const [viewMode, setViewMode] = useState<ViewMode>('absolute');
  const [minMatchesFilter, setMinMatchesFilter] = useState<number>(0);

  const { fieldMetadata, getNumericMetrics, getMetricsByCategory } = useFieldMetadata();

  // Dynamically determine scoring categories based on field metadata
  const scoringCategories = useMemo((): ScoringCategory[] => {
    if (!fieldMetadata) return [];

    const metricsByCategory = getMetricsByCategory();
    const categories: ScoringCategory[] = [];
    let colorIndex = 0;

    // Process each category from field metadata
    Object.entries(metricsByCategory).forEach(([categoryName, metrics]) => {
      // Filter to only include relevant scoring metrics
      const scoringFields = metrics.filter(metric => 
        metric.data_type === 'count' && 
        (metric.usage_context?.includes('scoring') || 
         metric.description?.toLowerCase().includes('scored') ||
         metric.field_name.includes('scored'))
      );

      if (scoringFields.length > 0) {
        categories.push({
          key: categoryName,
          label: categoryName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          color: COLOR_PALETTE[colorIndex % COLOR_PALETTE.length],
          fields: scoringFields.map(f => f.field_name)
        });
        colorIndex++;
      }
    });

    return categories;
  }, [fieldMetadata, getMetricsByCategory]);

  // Process team scoring data using dynamic categories
  const processedData = useMemo(() => {
    if (!fieldMetadata || scoringCategories.length === 0) return [];

    const teamScoringData: TeamScoringData[] = [];

    selectedTeams.forEach(teamNumber => {
      const teamData = teams.find(t => t.team_number === teamNumber);
      if (!teamData || !teamData.scouting_data || teamData.scouting_data.length === 0) {
        return;
      }

      let matchData = [...teamData.scouting_data];

      // Apply outlier exclusion if enabled
      if (excludeOutliers?.enabled) {
        matchData.sort((a, b) => (a.total_points || 0) - (b.total_points || 0));
        const start = excludeOutliers.excludeLowest || 0;
        const end = matchData.length - (excludeOutliers.excludeHighest || 0);
        matchData = matchData.slice(start, end);
      }

      // Filter by minimum matches
      if (matchData.length < minMatchesFilter) {
        return;
      }

      // Initialize category totals
      const categoryTotals: { [key: string]: number } = {};
      const categoryGamePieces: { [key: string]: number } = {};
      
      scoringCategories.forEach(category => {
        categoryTotals[category.key] = 0;
        categoryGamePieces[category.key] = 0;
      });

      // Helper function to safely get numeric value
      const safeNum = (val: any) => {
        const num = Number(val) || 0;
        return isNaN(num) ? 0 : num;
      };

      // Process each match
      matchData.forEach(match => {
        scoringCategories.forEach(category => {
          category.fields.forEach(fieldName => {
            const value = safeNum(match[fieldName]);
            categoryTotals[category.key] += value;
            categoryGamePieces[category.key] += value; // For efficiency calculation
          });
        });
      });

      // Calculate averages and ensure no NaN values
      const matchCount = matchData.length;
      Object.keys(categoryTotals).forEach(key => {
        let avgValue = matchCount > 0 ? categoryTotals[key] / matchCount : 0;
        if (isNaN(avgValue) || !isFinite(avgValue)) {
          console.warn(`Invalid average value for category ${key}: ${avgValue}, setting to 0`);
          avgValue = 0;
        }
        categoryTotals[key] = avgValue;
      });

      // Calculate efficiency (points per game piece)
      const efficiency: { [key: string]: number } = {};
      Object.keys(categoryGamePieces).forEach(key => {
        const totalPieces = categoryGamePieces[key];
        efficiency[key] = totalPieces > 0 
          ? (categoryTotals[key] * matchCount) / totalPieces 
          : 0;
        efficiency[key] = isNaN(efficiency[key]) ? 0 : efficiency[key];
      });

      // Calculate total
      const total = Object.values(categoryTotals).reduce((sum, val) => sum + val, 0);
      const safeTotal = isNaN(total) ? 0 : total;

      teamScoringData.push({
        name: `${teamNumber} - ${teamData.nickname || 'Unknown'}`,
        teamNumber,
        categoryTotals,
        total: safeTotal,
        matchesPlayed: matchCount,
        efficiency
      });
    });

    // Sort data based on selected criteria
    teamScoringData.sort((a, b) => {
      switch (sortBy) {
        case 'total':
          return b.total - a.total;
        case 'teamNumber':
          return a.teamNumber - b.teamNumber;
        default:
          // Check if sorting by a specific category
          if (a.categoryTotals[sortBy] !== undefined && b.categoryTotals[sortBy] !== undefined) {
            return b.categoryTotals[sortBy] - a.categoryTotals[sortBy];
          }
          return 0;
      }
    });

    return teamScoringData;
  }, [teams, selectedTeams, excludeOutliers, sortBy, minMatchesFilter, scoringCategories, fieldMetadata]);

  // Convert data for chart display
  const chartData = useMemo(() => {
    const cleanData = processedData.map(team => {
      const chartTeam: any = {
        name: team.name,
        teamNumber: team.teamNumber,
        total: isNaN(team.total) ? 0 : team.total,
        matchesPlayed: team.matchesPlayed
      };

      // Add category data
      if (viewMode === 'percentage') {
        scoringCategories.forEach(category => {
          const categoryValue = team.categoryTotals[category.key] || 0;
          const totalValue = team.total || 0;
          const value = totalValue > 0 ? (categoryValue / totalValue) * 100 : 0;
          chartTeam[category.key] = isNaN(value) || !isFinite(value) ? 0 : value;
        });
      } else {
        scoringCategories.forEach(category => {
          const value = team.categoryTotals[category.key] || 0;
          chartTeam[category.key] = isNaN(value) || !isFinite(value) ? 0 : value;
        });
      }

      // Final safety check - ensure all numeric values are valid
      Object.keys(chartTeam).forEach(key => {
        if (typeof chartTeam[key] === 'number' && (isNaN(chartTeam[key]) || !isFinite(chartTeam[key]))) {
          console.warn(`Replacing invalid value for ${key}:`, chartTeam[key]);
          chartTeam[key] = 0;
        }
      });

      return chartTeam;
    });

    // Extra safety - deep clean the data
    const superCleanData = cleanData.map(team => {
      const cleaned: any = {};
      Object.entries(team).forEach(([key, value]) => {
        if (typeof value === 'number') {
          cleaned[key] = isNaN(value) || !isFinite(value) ? 0 : value;
        } else {
          cleaned[key] = value;
        }
      });
      return cleaned;
    });

    return superCleanData;
  }, [processedData, viewMode, scoringCategories]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length && processedData.length > 0) {
      const teamData = processedData.find(t => t.name === label);
      if (!teamData) return null;

      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold text-sm mb-2">{label}</p>
          <p className="text-xs text-gray-600 mb-2">
            {teamData.matchesPlayed} matches played
          </p>
          <div className="space-y-1">
            {payload.map((entry: any, index: number) => (
              <div key={index} className="flex justify-between text-xs">
                <span style={{ color: entry.color }}>{entry.name}:</span>
                <span className="ml-2 font-medium">
                  {viewMode === 'percentage' 
                    ? `${entry.value.toFixed(1)}%`
                    : entry.value.toFixed(1)
                  }
                </span>
              </div>
            ))}
          </div>
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="text-xs font-medium">
              Total: {teamData.total.toFixed(1)} points/match
            </p>
            {Object.entries(teamData.efficiency).map(([key, value]) => (
              <p key={key} className="text-xs text-gray-600">
                {scoringCategories.find(c => c.key === key)?.label} Efficiency: {value.toFixed(2)} pts/piece
              </p>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  // Export data to CSV
  const exportToCSV = () => {
    const headers = [
      'Team',
      ...scoringCategories.map(c => c.label),
      'Total',
      ...scoringCategories.map(c => `${c.label} Efficiency`),
      'Matches Played'
    ];

    const rows = processedData.map(team => [
      team.name,
      ...scoringCategories.map(c => team.categoryTotals[c.key].toFixed(2)),
      team.total.toFixed(2),
      ...scoringCategories.map(c => team.efficiency[c.key].toFixed(2)),
      team.matchesPlayed
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scoring_distribution_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // Debug logging
  React.useEffect(() => {
    if (chartData.length > 0) {
      console.log('ScoringDistribution chartData:', JSON.stringify(chartData, null, 2));
      console.log('ScoringDistribution categories:', JSON.stringify(scoringCategories, null, 2));
      
      // Check for NaN values in chartData
      chartData.forEach((team, teamIndex) => {
        console.log(`Team ${teamIndex} data:`, team);
        Object.entries(team).forEach(([key, value]) => {
          if (typeof value === 'number') {
            if (isNaN(value)) {
              console.error(`❌ NaN found in team ${teamIndex} (${team.name}), key: ${key}, value:`, value);
            } else if (!isFinite(value)) {
              console.error(`❌ Infinite value found in team ${teamIndex} (${team.name}), key: ${key}, value:`, value);
            } else {
              console.log(`✅ Valid number for ${key}:`, value);
            }
          }
        });
      });
    }
  }, [chartData, scoringCategories]);

  // Loading state
  if (!fieldMetadata) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium mb-2">Loading Field Metadata...</p>
          <p className="text-sm">Determining scoring categories for this event...</p>
        </div>
      </div>
    );
  }

  // No categories found
  if (scoringCategories.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium mb-2">No Scoring Categories Found</p>
          <p className="text-sm">
            No scoring metrics were found in the field metadata for this event.
          </p>
        </div>
      </div>
    );
  }

  // No data available
  if (processedData.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium mb-2">No Data Available</p>
          <p className="text-sm">
            {selectedTeams.length === 0 
              ? 'Please select teams to display scoring distribution.'
              : minMatchesFilter > 0
              ? `No teams have played at least ${minMatchesFilter} matches.`
              : 'Selected teams have no scoring data available.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Controls */}
      <div className="mb-4 flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="total">Total Score</option>
            <option value="teamNumber">Team Number</option>
            {scoringCategories.map(category => (
              <option key={category.key} value={category.key}>
                {category.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">View:</label>
          <select
            value={viewMode}
            onChange={(e) => setViewMode(e.target.value as ViewMode)}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="absolute">Absolute Points</option>
            <option value="percentage">Percentage</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Min Matches:</label>
          <input
            type="number"
            min="0"
            max="20"
            value={minMatchesFilter}
            onChange={(e) => setMinMatchesFilter(parseInt(e.target.value) || 0)}
            className="w-16 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={exportToCSV}
          className="ml-auto px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Export CSV
        </button>
      </div>

      {/* Chart */}
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={height}>
          <BarChart
            data={chartData}
            layout="horizontal"
            margin={{ top: 20, right: 30, left: 150, bottom: 20 }}
            onError={(error) => {
              console.error('BarChart error:', error);
            }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              type="number" 
              domain={[0, viewMode === 'percentage' ? 100 : (dataMax: number) => {
                if (isNaN(dataMax) || !isFinite(dataMax) || dataMax <= 0) {
                  console.warn('Invalid dataMax, using fallback:', dataMax);
                  return 100;
                }
                return dataMax;
              }]}
              tickFormatter={(value) => {
                if (isNaN(value) || !isFinite(value)) return '0';
                return viewMode === 'percentage' ? `${value}%` : value.toString();
              }}
            />
            <YAxis 
              dataKey="name" 
              type="category" 
              width={140}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '10px' }}
              iconType="rect"
            />
            {scoringCategories.map(category => (
              <Bar 
                key={category.key}
                dataKey={category.key} 
                stackId="a" 
                fill={category.color} 
                name={category.label} 
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend explanation */}
      <div className="mt-4 text-xs text-gray-600">
        <p>• <strong>Categories</strong>: Based on field metadata for this event</p>
        <p>• <strong>Efficiency</strong>: Average points earned per game piece scored</p>
        <p>• Data shows average points per match for each category</p>
        <p>• Categories: {scoringCategories.map(c => c.label).join(', ')}</p>
      </div>
    </div>
  );
};

export default ScoringDistribution;