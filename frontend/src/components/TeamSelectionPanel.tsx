import React from 'react';

interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
}

interface TeamSelectionPanelProps {
  teamNumbers: number[];
  pickPosition: "first" | "second" | "third";
  onPickPositionChange: (position: "first" | "second" | "third") => void;
  result: Team[] | null;
  hasInitialAnalysis: boolean;
  isLoading: boolean;
  onStartAnalysis: () => void;
  onApply: () => void;
  onReset: () => void;
  onClearChat: () => void;
  chatHistoryLength: number;
}

const TeamSelectionPanel: React.FC<TeamSelectionPanelProps> = ({
  teamNumbers,
  pickPosition,
  onPickPositionChange,
  result,
  hasInitialAnalysis,
  isLoading,
  onStartAnalysis,
  onApply,
  onReset,
  onClearChat,
  chatHistoryLength
}) => {
  return (
    <div className="w-1/4 border-r border-gray-200 p-4 flex flex-col">
      <div className="space-y-4">
        {/* Selected Teams */}
        <div>
          <h4 className="font-medium text-gray-900 mb-2">Selected Teams</h4>
          <div className="space-y-2">
            {teamNumbers.map((teamNum, index) => (
              <div
                key={teamNum}
                className="bg-blue-50 border border-blue-200 rounded p-2 flex items-center justify-between"
              >
                <span className="font-medium">Team {teamNum}</span>
                {result && (
                  <span className="text-sm text-gray-600">
                    #{result.findIndex(t => t.team_number === teamNum) + 1}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Pick Strategy */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pick Strategy
          </label>
          <select
            value={pickPosition}
            onChange={(e) => onPickPositionChange(e.target.value as "first" | "second" | "third")}
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="first">1st Pick Strategy</option>
            <option value="second">2nd Pick Strategy</option>
            <option value="third">3rd Pick Strategy</option>
          </select>
        </div>

        {/* Initial Analysis Button */}
        {!hasInitialAnalysis && (
          <button
            onClick={onStartAnalysis}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "Analyzing..." : "Start Analysis"}
          </button>
        )}

        {/* Re-Ranking Results */}
        {result && (
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium text-gray-900 mb-2">Suggested Ranking</h4>
            <ol className="space-y-1">
              {result.map((team, index) => (
                <li
                  key={team.team_number}
                  className="flex items-center justify-between bg-gray-50 rounded p-2"
                >
                  <span className="font-medium">
                    {index + 1}. Team {team.team_number}
                  </span>
                  {team.nickname && (
                    <span className="text-sm text-gray-600 truncate ml-2">
                      {team.nickname}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Apply Button */}
        {result && (
          <div className="border-t border-gray-200 pt-4 mt-auto space-y-2">
            <button
              onClick={onApply}
              className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 font-medium"
            >
              Apply New Ranking
            </button>
            <button
              onClick={onReset}
              className="w-full bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
            >
              Reset Analysis
            </button>
            {chatHistoryLength > 1 && (
              <button
                onClick={onClearChat}
                className="w-full bg-yellow-500 text-white py-1 px-4 rounded hover:bg-yellow-600 text-sm"
              >
                Clear Chat (Keep Initial Analysis)
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamSelectionPanel;