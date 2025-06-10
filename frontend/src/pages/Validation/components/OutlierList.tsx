// frontend/src/pages/Validation/components/OutlierList.tsx

import React from 'react';
import { ValidationIssue, TeamMatch } from '../types';
import { useOutliers } from '../hooks/useOutliers';

interface OutlierListProps {
  outliers: ValidationIssue[];
  onSelectIssue: (issue: ValidationIssue) => void;
  selectedIssue: TeamMatch | ValidationIssue | null;
}

export const OutlierList: React.FC<OutlierListProps> = ({
  outliers,
  onSelectIssue,
  selectedIssue,
}) => {
  const {
    filteredOutliers,
    uniqueTeams,
    uniqueMetrics,
    selectedTeam,
    selectedMetric,
    sortBy,
    sortOrder,
    setSelectedTeam,
    setSelectedMetric,
    toggleSort,
    clearFilters,
    getSeverityLevel,
    getSeverityColor,
  } = useOutliers(outliers);

  const isSelected = (outlier: ValidationIssue) => {
    return selectedIssue && 
           selectedIssue.team_number === outlier.team_number && 
           selectedIssue.match_number === outlier.match_number;
  };

  if (outliers.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">✨</div>
        <div className="text-lg font-medium">No outliers found!</div>
        <div>Your data looks clean and consistent.</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Team
            </label>
            <select
              value={selectedTeam || ''}
              onChange={(e) => setSelectedTeam(e.target.value ? Number(e.target.value) : null)}
              className="block w-32 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">All Teams</option>
              {uniqueTeams.map(team => (
                <option key={team} value={team}>Team {team}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by Metric
            </label>
            <select
              value={selectedMetric || ''}
              onChange={(e) => setSelectedMetric(e.target.value || null)}
              className="block w-48 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              <option value="">All Metrics</option>
              {uniqueMetrics.map(metric => (
                <option key={metric} value={metric}>{metric}</option>
              ))}
            </select>
          </div>
          
          {(selectedTeam || selectedMetric) && (
            <button
              onClick={clearFilters}
              className="mt-6 px-3 py-1 text-sm text-blue-600 hover:text-blue-800"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex space-x-2 text-sm">
        <span className="text-gray-500">Sort by:</span>
        {['team', 'match', 'severity', 'metric'].map((option) => (
          <button
            key={option}
            onClick={() => toggleSort(option as any)}
            className={`px-2 py-1 rounded ${
              sortBy === option 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {option.charAt(0).toUpperCase() + option.slice(1)}
            {sortBy === option && (
              <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
            )}
          </button>
        ))}
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        Showing {filteredOutliers.length} of {outliers.length} outliers
      </div>

      {/* Outlier List */}
      <div className="space-y-2">
        {filteredOutliers.map((outlier) => (
          <div
            key={`${outlier.team_number}-${outlier.match_number}`}
            onClick={() => onSelectIssue(outlier)}
            className={`border rounded-lg p-4 cursor-pointer transition-colors ${
              isSelected(outlier)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="font-medium">
                  Team {outlier.team_number} - Match {outlier.match_number}
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(outlier)}`}>
                  {getSeverityLevel(outlier).toUpperCase()}
                </span>
              </div>
              <div className="text-sm text-gray-500">
                {outlier.issues.length} issue{outlier.issues.length > 1 ? 's' : ''}
              </div>
            </div>
            
            <div className="mt-2 space-y-1">
              {outlier.issues.slice(0, 3).map((issue, index) => (
                <div key={index} className="text-sm text-gray-600">
                  <span className="font-medium">{issue.metric}:</span> {issue.value}
                  {issue.z_score && (
                    <span className="text-gray-500 ml-2">(z-score: {issue.z_score.toFixed(2)})</span>
                  )}
                </div>
              ))}
              {outlier.issues.length > 3 && (
                <div className="text-sm text-gray-500">
                  ... and {outlier.issues.length - 3} more
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredOutliers.length === 0 && (selectedTeam || selectedMetric) && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-lg font-medium">No outliers match your filters</div>
          <div>Try adjusting the filters above.</div>
        </div>
      )}
    </div>
  );
};