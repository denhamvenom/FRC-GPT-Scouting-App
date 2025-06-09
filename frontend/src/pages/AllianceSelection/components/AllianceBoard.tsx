/**
 * Alliance Board Component - Displays current alliance formations
 */

import React from 'react';
import { AllianceBoardProps } from '../types';

const AllianceBoard: React.FC<AllianceBoardProps> = ({
  selection,
  selectedAlliance,
  onAllianceSelect,
  onRemoveTeam
}) => {
  if (!selection) {
    return (
      <div className="text-center text-gray-500 py-8">
        No alliance selection in progress
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold mb-4">Alliance Board</h2>
      
      <div className="space-y-3">
        {selection.alliances.map(alliance => (
          <div 
            key={alliance.alliance_number}
            className={`p-3 rounded-lg border ${
              selectedAlliance === alliance.alliance_number
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-200'
            }`}
            onClick={() => onAllianceSelect(
              selectedAlliance === alliance.alliance_number ? null : alliance.alliance_number
            )}
          >
            <div className="font-bold text-lg">Alliance #{alliance.alliance_number}</div>
            
            <div className="grid grid-cols-2 gap-2 mt-2">
              {/* Captain */}
              <div className={`p-2 rounded ${
                alliance.captain_team_number !== 0
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                <div className="text-xs">Captain</div>
                <div className="font-bold">
                  {alliance.captain_team_number !== 0
                    ? `${alliance.captain_team_number}`
                    : '-'}
                </div>
              </div>

              {/* First Pick */}
              <div className={`p-2 rounded relative ${
                alliance.first_pick_team_number !== 0
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                <div className="text-xs">First Pick</div>
                <div className="font-bold">
                  {alliance.first_pick_team_number !== 0
                    ? `${alliance.first_pick_team_number}`
                    : '-'}
                </div>
                {alliance.first_pick_team_number !== 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveTeam(alliance.first_pick_team_number, alliance.alliance_number);
                    }}
                    className="absolute top-0 right-0 bg-red-500 text-white text-xs w-4 h-4 flex items-center justify-center rounded-full -mt-1 -mr-1"
                    title="Remove team"
                  >
                    ×
                  </button>
                )}
              </div>

              {/* Second Pick */}
              <div className={`p-2 rounded relative ${
                alliance.second_pick_team_number !== 0
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                <div className="text-xs">Second Pick</div>
                <div className="font-bold">
                  {alliance.second_pick_team_number !== 0
                    ? `${alliance.second_pick_team_number}`
                    : '-'}
                </div>
                {alliance.second_pick_team_number !== 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveTeam(alliance.second_pick_team_number, alliance.alliance_number);
                    }}
                    className="absolute top-0 right-0 bg-red-500 text-white text-xs w-4 h-4 flex items-center justify-center rounded-full -mt-1 -mr-1"
                    title="Remove team"
                  >
                    ×
                  </button>
                )}
              </div>

              {/* Backup - only show after round 3 starts */}
              {selection.current_round >= 3 && (
                <div className={`p-2 rounded relative ${
                  alliance.backup_team_number && alliance.backup_team_number !== 0
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  <div className="text-xs">Backup</div>
                  <div className="font-bold">
                    {alliance.backup_team_number && alliance.backup_team_number !== 0
                      ? `${alliance.backup_team_number}`
                      : '-'}
                  </div>
                  {alliance.backup_team_number && alliance.backup_team_number !== 0 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveTeam(alliance.backup_team_number!, alliance.alliance_number);
                      }}
                      className="absolute top-0 right-0 bg-red-500 text-white text-xs w-4 h-4 flex items-center justify-center rounded-full -mt-1 -mr-1"
                      title="Remove team"
                    >
                      ×
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* Print button */}
      <div className="mt-6">
        <button
          onClick={handlePrint}
          className="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center justify-center"
        >
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clipRule="evenodd" />
          </svg>
          Print Alliance Selection
        </button>
      </div>
    </div>
  );
};

export default AllianceBoard;