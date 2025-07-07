import React, { useMemo, useState } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip
} from 'recharts';
import { RadarChartDataPoint } from '../utils/chartDataProcessing';
import { DEFAULT_CHART_CONFIG } from '../types/graphicalAnalysis';

interface RadarChartVisualizationProps {
  chartData: RadarChartDataPoint[];
  selectedTeams: number[];
  teamNames: { [teamNumber: number]: string };
  teamMetrics?: Array<{ team_number: number; averages: { [metric: string]: number } }>;
  selectedMetrics?: string[];
  loading?: boolean;
  error?: string | null;
  height?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number;
    fill: string;
    name: string;
  }>;
  label?: string;
  teamMetrics?: Array<{ team_number: number; averages: { [metric: string]: number } }>;
  selectedMetrics?: string[];
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, teamMetrics, selectedMetrics }) => {
  if (active && payload && payload.length) {
    // Find the original metric field name by matching the formatted display label
    const originalMetric = selectedMetrics?.find(metric => {
      const formatted = metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      return formatted === label;
    });
    
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-medium text-gray-800 mb-2">{label}</p>
        {payload.map((entry, index) => {
          const teamNumber = parseInt(entry.dataKey.replace('team_', ''));
          const teamName = entry.name || `Team ${teamNumber}`;
          
          // Find the raw value for this team and metric
          const teamData = teamMetrics?.find(tm => tm.team_number === teamNumber);
          const rawValue = originalMetric ? teamData?.averages[originalMetric] : undefined;
          
          return (
            <div key={index} className="text-sm" style={{ color: entry.fill }}>
              <p className="font-medium">{teamName}:</p>
              <p className="ml-2">
                <span className="text-gray-600">Normalized:</span> {entry.value.toFixed(1)}%
              </p>
              {rawValue !== undefined && (
                <p className="ml-2">
                  <span className="text-gray-600">Actual:</span> {rawValue.toFixed(2)}
                </p>
              )}
            </div>
          );
        })}
      </div>
    );
  }
  return null;
};

const RadarChartVisualization: React.FC<RadarChartVisualizationProps> = ({
  chartData,
  selectedTeams,
  teamNames,
  teamMetrics,
  selectedMetrics,
  loading = false,
  error = null,
  height = 400
}) => {
  const [hiddenTeams, setHiddenTeams] = useState<Set<number>>(new Set());

  // Generate team colors and radar components
  const teamRadars = useMemo(() => {
    return selectedTeams.map((teamNumber, index) => {
      const teamKey = `team_${teamNumber}`;
      const color = DEFAULT_CHART_CONFIG.colors[index % DEFAULT_CHART_CONFIG.colors.length];
      const isHidden = hiddenTeams.has(teamNumber);
      
      return {
        teamNumber,
        teamKey,
        color,
        isHidden,
        name: teamNames[teamNumber] || `Team ${teamNumber}`
      };
    });
  }, [selectedTeams, teamNames, hiddenTeams]);

  // Handle legend click to toggle team visibility
  const handleLegendClick = (teamNumber: number) => {
    setHiddenTeams(prev => {
      const newSet = new Set(prev);
      if (newSet.has(teamNumber)) {
        newSet.delete(teamNumber);
      } else {
        newSet.add(teamNumber);
      }
      return newSet;
    });
  };

  // Format legend payload for Recharts
  const legendPayload = useMemo(() => {
    return teamRadars.map((team) => ({
      value: team.name,
      type: 'line' as const,
      color: team.isHidden ? '#d1d5db' : team.color,
      dataKey: team.teamKey
    }));
  }, [teamRadars]);

  if (loading) {
    return (
      <div className="flex justify-center items-center" style={{ height }}>
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading chart...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center" style={{ height }}>
        <div className="text-center">
          <div className="text-red-500 mb-2">
            <svg className="mx-auto h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="flex justify-center items-center" style={{ height }}>
        <div className="text-center">
          <div className="text-gray-400 mb-2">
            <svg className="mx-auto h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-sm text-gray-600">No data available for selected metrics and teams</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart 
          data={chartData} 
          margin={{ 
            top: 20, 
            right: 20, 
            bottom: 60, 
            left: 20 
          }}
        >
          <PolarGrid 
            stroke="#e5e7eb" 
            strokeWidth={1}
            strokeOpacity={DEFAULT_CHART_CONFIG.gridOpacity}
          />
          <PolarAngleAxis 
            dataKey="metric" 
            tick={{ 
              fontSize: DEFAULT_CHART_CONFIG.labelFontSize, 
              fill: '#374151' 
            }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]}
            tick={{ 
              fontSize: DEFAULT_CHART_CONFIG.labelFontSize - 2, 
              fill: '#6b7280' 
            }}
            strokeOpacity={0.3}
          />
          
          {/* Render radar for each team */}
          {teamRadars.map((team) => (
            <Radar
              key={team.teamKey}
              name={team.name}
              dataKey={team.teamKey}
              stroke={team.color}
              fill={team.color}
              fillOpacity={team.isHidden ? 0 : 0.1}
              strokeOpacity={team.isHidden ? 0.2 : 1}
              strokeWidth={team.isHidden ? 1 : 2}
              dot={!team.isHidden}
              connectNulls={false}
            />
          ))}
          
          <Tooltip content={<CustomTooltip teamMetrics={teamMetrics} selectedMetrics={selectedMetrics} />} />
          
          <Legend 
            payload={legendPayload}
            onClick={(data) => {
              const teamNumber = parseInt(data.dataKey.replace('team_', ''));
              handleLegendClick(teamNumber);
            }}
            wrapperStyle={{ 
              paddingTop: '20px', 
              cursor: 'pointer' 
            }}
          />
        </RadarChart>
      </ResponsiveContainer>

      {/* Legend Instructions */}
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          Click on team names in the legend to show/hide individual teams
        </p>
      </div>

      {/* Chart Info */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-gray-600">
        <div className="text-center p-2 bg-gray-50 rounded">
          <p className="font-medium">Scale: 0-100</p>
          <p>Normalized values</p>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <p className="font-medium">Metrics: {chartData.length}</p>
          <p>Selected for comparison</p>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded">
          <p className="font-medium">Teams: {selectedTeams.length}</p>
          <p>Currently displayed</p>
        </div>
      </div>
    </div>
  );
};

export default RadarChartVisualization;