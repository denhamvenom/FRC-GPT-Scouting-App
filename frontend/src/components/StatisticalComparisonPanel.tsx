import React from 'react';
import { getStatColor } from '../utils/colorUtils';
import { formatMetricName } from '../utils/formatUtils';

interface ComparisonData {
  teams: Array<{
    team_number: number;
    nickname: string;
    stats: Record<string, number>;
  }>;
  metrics: string[];
}

interface StatisticalComparisonPanelProps {
  comparisonData: ComparisonData | null;
}

const StatisticalComparisonPanel: React.FC<StatisticalComparisonPanelProps> = ({
  comparisonData
}) => {
  return (
    <div className="w-1/3 flex flex-col">
      {/* Stats Header */}
      <div className="border-b border-gray-200 p-3">
        <h4 className="font-medium text-gray-900">Statistical Comparison</h4>
        <p className="text-sm text-gray-600">
          {comparisonData?.metrics?.length > 0 
            ? "GPT-selected key metrics for comparison" 
            : "Direct comparison of key metrics"}
        </p>
      </div>

      {/* Stats Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!comparisonData ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="bg-gray-50 rounded-lg p-6 border">
              <p className="font-medium">No Comparison Data</p>
              <p className="text-sm mt-2">
                Run analysis to see statistical comparison
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {comparisonData.metrics.length === 0 ? (
              <div className="text-center text-gray-500">
                <p>No comparable metrics found</p>
              </div>
            ) : (
              <div className="space-y-3">
                {comparisonData.metrics.map((metric) => {
                  const teams = comparisonData.teams.filter(team => 
                    team.stats[metric] !== undefined && team.stats[metric] !== null
                  );
                  
                  if (teams.length === 0) return null;
                  
                  const values = teams.map(team => team.stats[metric]);
                  
                  return (
                    <div key={metric} className="bg-white border rounded-lg p-3">
                      <h5 className="font-medium text-sm text-gray-800 mb-2">
                        {formatMetricName(metric)}
                      </h5>
                      <div className="space-y-1">
                        {teams.map((team) => {
                          const value = team.stats[metric];
                          const colorClass = getStatColor(value, values);
                          
                          return (
                            <div
                              key={team.team_number}
                              className={`flex justify-between items-center p-2 rounded text-sm ${colorClass}`}
                            >
                              <span className="font-medium">
                                Team {team.team_number}
                              </span>
                              <span className="font-mono">
                                {typeof value === 'number' ? value.toFixed(2) : value}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
                
                {comparisonData.metrics.length > 0 && (
                  <div className="text-center text-sm text-gray-500 italic mt-4">
                    Showing {comparisonData.metrics.length} GPT-recommended metrics
                  </div>
                )}
                
                {/* Legend */}
                <div className="mt-4 p-3 bg-gray-50 rounded-lg border">
                  <p className="text-xs font-medium text-gray-700 mb-2">Legend:</p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-green-100 rounded"></div>
                      <span>Highest</span>
                    </div>
                    {comparisonData.teams.length === 3 && (
                      <div className="flex items-center space-x-1">
                        <div className="w-3 h-3 bg-yellow-100 rounded"></div>
                        <span>Middle</span>
                      </div>
                    )}
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-red-100 rounded"></div>
                      <span>Lowest</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatisticalComparisonPanel;