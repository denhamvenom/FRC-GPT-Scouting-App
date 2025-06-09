// frontend/src/pages/PicklistNew/components/PicklistDisplay.tsx

import React from "react";
import { PicklistDisplayProps } from "../types";

export const PicklistDisplay: React.FC<PicklistDisplayProps> = ({
  picklist,
  currentPage,
  teamsPerPage,
  totalPages,
  isEditing,
  isLocked,
  selectedTeams,
  onPositionChange,
  onToggleTeamSelection,
  onExcludeTeam,
}) => {
  // Get current page of teams
  const currentPageTeams = picklist.slice(
    (currentPage - 1) * teamsPerPage,
    currentPage * teamsPerPage
  );

  if (isEditing) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-blue-600 italic mb-2">
          Edit team positions by changing their rank numbers, then click
          "Save Changes" when done.
        </p>

        {currentPageTeams.map((team, pageIndex) => {
          const index = (currentPage - 1) * teamsPerPage + pageIndex;

          return (
            <div
              key={team.team_number}
              className="p-3 bg-white rounded border border-gray-300 shadow-sm flex items-center hover:bg-blue-50 transition-colors duration-150"
            >
              <div className="mr-3 flex items-center">
                <input
                  type="number"
                  min="1"
                  max={picklist.length}
                  value={index + 1}
                  onChange={(e) =>
                    onPositionChange(index, parseInt(e.target.value) || 1)
                  }
                  className="w-12 p-1 border border-gray-300 rounded text-center font-bold text-blue-600"
                />
              </div>
              
              <div className="flex-1">
                <div className="font-medium">
                  Team {team.team_number}: {team.nickname}
                  {team.is_fallback && (
                    <span
                      className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full"
                      title="This team was automatically added to complete the picklist"
                    >
                      Auto-added
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-600">
                  Score: {team.score.toFixed(2)}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                {onExcludeTeam && !isLocked && (
                  <button
                    onClick={() => onExcludeTeam(team.team_number)}
                    className="px-2 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                    title="Exclude team from all picklists"
                  >
                    Exclude
                  </button>
                )}
                <div className="text-gray-400">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {currentPageTeams.map((team, pageIndex) => {
        const index = (currentPage - 1) * teamsPerPage + pageIndex;

        return (
          <div
            key={team.team_number}
            className="p-3 bg-white rounded border flex hover:bg-gray-50"
          >
            <input
              type="checkbox"
              className="mr-3"
              checked={selectedTeams.includes(team.team_number)}
              onChange={() => onToggleTeamSelection(team.team_number)}
              disabled={isLocked}
            />
            
            <div className="mr-3 text-lg font-bold text-gray-500">
              {index + 1}
            </div>
            
            <div className="flex-1">
              <div className="font-medium">
                Team {team.team_number}: {team.nickname}
                {team.is_fallback && (
                  <span
                    className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full"
                    title="This team was automatically added to complete the picklist"
                  >
                    Auto-added
                  </span>
                )}
              </div>
              
              <div className="text-sm text-gray-600">
                Score: {team.score.toFixed(2)}
              </div>
              
              <div
                className={`text-sm mt-1 ${
                  team.is_fallback ? "italic text-yellow-700" : ""
                }`}
              >
                {team.reasoning}
              </div>
              
              {team.is_fallback && (
                <div className="text-xs mt-1 text-red-500">
                  Note: This team was added automatically because it was missing from the GPT response.
                </div>
              )}
            </div>
            
            {onExcludeTeam && !isLocked && (
              <div className="ml-2 flex items-center">
                <button
                  onClick={() => onExcludeTeam(team.team_number)}
                  className="px-2 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  title="Exclude team from all picklists"
                >
                  Exclude
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};