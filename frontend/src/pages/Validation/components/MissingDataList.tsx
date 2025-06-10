// frontend/src/pages/Validation/components/MissingDataList.tsx

import React from 'react';
import { TeamMatch } from '../types';

interface MissingDataListProps {
  missingMatches: TeamMatch[];
  missingSuperscouting: { team_number: number }[];
  onSelectMissing: (item: TeamMatch | { team_number: number; match_number?: number }) => void;
  selectedIssue: TeamMatch | any | null;
}

export const MissingDataList: React.FC<MissingDataListProps> = ({
  missingMatches,
  missingSuperscouting,
  onSelectMissing,
  selectedIssue,
}) => {
  const isSelected = (item: any) => {
    return selectedIssue && 
           selectedIssue.team_number === item.team_number && 
           selectedIssue.match_number === item.match_number;
  };

  const isSelectedSuper = (item: { team_number: number }) => {
    return selectedIssue && 
           selectedIssue.team_number === item.team_number && 
           !selectedIssue.match_number;
  };

  if (missingMatches.length === 0 && missingSuperscouting.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">✅</div>
        <div className="text-lg font-medium">No missing data!</div>
        <div>All expected scouting data has been collected.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Missing Match Scouting */}
      {missingMatches.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-red-700">
            Missing Match Scouting ({missingMatches.length})
          </h3>
          <div className="space-y-2">
            {missingMatches.map((missing, index) => (
              <div
                key={`${missing.team_number}-${missing.match_number}-${index}`}
                onClick={() => onSelectMissing(missing)}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  isSelected(missing)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-red-200 bg-red-50 hover:border-red-300 hover:bg-red-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium">
                    Team {missing.team_number} - Match {missing.match_number}
                  </div>
                  <div className="text-sm text-red-600 font-medium">
                    Missing Match Data
                  </div>
                </div>
                <div className="mt-1 text-sm text-red-600">
                  No scouting data found for this team's match performance
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing Superscouting */}
      {missingSuperscouting.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-yellow-700">
            Missing Superscouting ({missingSuperscouting.length})
          </h3>
          <div className="space-y-2">
            {missingSuperscouting.map((missing, index) => (
              <div
                key={`${missing.team_number}-super-${index}`}
                onClick={() => onSelectMissing({ ...missing, match_number: undefined })}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  isSelectedSuper(missing)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-yellow-200 bg-yellow-50 hover:border-yellow-300 hover:bg-yellow-100'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium">
                    Team {missing.team_number}
                  </div>
                  <div className="text-sm text-yellow-600 font-medium">
                    Missing Superscouting
                  </div>
                </div>
                <div className="mt-1 text-sm text-yellow-600">
                  No superscouting data found for this team
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selection Hint */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <div className="text-blue-600 text-xl">💡</div>
          </div>
          <div className="ml-3">
            <div className="text-sm font-medium text-blue-800">
              Select an item to see correction options
            </div>
            <div className="text-sm text-blue-700 mt-1">
              You can watch match videos, generate virtual scout data, or mark matches as ignored.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};