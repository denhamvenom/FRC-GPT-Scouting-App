import React from "react";

interface MissingTeamsModalProps {
  missingTeamCount: number;
  onRankMissingTeams: () => void;
  onSkip: () => void;
  isLoading: boolean;
}

export const MissingTeamsModal: React.FC<MissingTeamsModalProps> = ({
  missingTeamCount,
  onRankMissingTeams,
  onSkip,
  isLoading,
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
        <h3 className="text-xl font-bold mb-4">Auto-Added Teams Detected</h3>
        <p className="mb-6">
          {missingTeamCount} teams have been automatically added with estimated
          scores. Would you like to get more accurate rankings for these teams?
        </p>
        <div className="flex justify-end space-x-3">
          <button
            onClick={onSkip}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 disabled:opacity-50"
          >
            Skip
          </button>
          <button
            onClick={onRankMissingTeams}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                Ranking...
              </>
            ) : (
              "Get Accurate Rankings"
            )}
          </button>
        </div>
      </div>
    </div>
  );
};