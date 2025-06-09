/**
 * Team Action Panel Component - Handles team actions (captain, accept, decline)
 */

import React from 'react';
import { TeamActionPanelProps, TeamAction } from '../types';
import { isAllianceValidForAction } from '../utils';

const TeamActionPanel: React.FC<TeamActionPanelProps> = ({
  selectedTeam,
  selectedAlliance,
  action,
  selection,
  picklist,
  onActionSelect,
  onAllianceSelect,
  onConfirmAction,
  getTeamNickname,
  canBeCaptain,
  isTeamSelectable
}) => {
  if (!selectedTeam || !selection || selection.is_completed) {
    return null;
  }

  const handleActionClick = (actionType: TeamAction) => {
    onActionSelect(action === actionType ? null : actionType);
  };

  const handleAllianceClick = (allianceNumber: number) => {
    onAllianceSelect(selectedAlliance === allianceNumber ? null : allianceNumber);
  };

  const canConfirm = action && (
    action === 'decline' || 
    ((action === 'captain' || action === 'accept') && selectedAlliance)
  );

  const getActionDisplayName = (actionType: TeamAction): string => {
    const names = {
      captain: 'Captain',
      accept: 'Accept',
      decline: 'Decline',
      remove: 'Remove'
    };
    return names[actionType] || actionType;
  };

  return (
    <div className="mt-6 p-4 border border-blue-200 bg-blue-50 rounded">
      <h3 className="font-bold text-lg mb-2">
        Selected: {selectedTeam} - {getTeamNickname(selectedTeam)}
      </h3>
      
      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 mt-4">
        {canBeCaptain(selectedTeam) && (
          <button
            onClick={() => handleActionClick('captain')}
            className={`px-4 py-2 rounded ${
              action === 'captain' 
                ? 'bg-blue-600 text-white' 
                : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
            }`}
          >
            Alliance Captain
          </button>
        )}
        
        {isTeamSelectable(selectedTeam) && (
          <>
            <button
              onClick={() => handleActionClick('accept')}
              className={`px-4 py-2 rounded ${
                action === 'accept' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-green-100 text-green-800 hover:bg-green-200'
              }`}
            >
              Accept Selection
            </button>
            
            <button
              onClick={() => handleActionClick('decline')}
              className={`px-4 py-2 rounded ${
                action === 'decline' 
                  ? 'bg-red-600 text-white' 
                  : 'bg-red-100 text-red-800 hover:bg-red-200'
              }`}
            >
              Decline Selection
            </button>
          </>
        )}
      </div>
      
      {/* Alliance selection for captain or accept */}
      {(action === 'captain' || action === 'accept') && (
        <div className="mt-4">
          <h4 className="font-medium mb-2">Select Alliance:</h4>
          <div className="grid grid-cols-8 gap-2">
            {selection.alliances.map(alliance => {
              // Determine if this alliance is valid for the current action
              const isValid = isAllianceValidForAction(
                alliance, 
                action, 
                selection.current_round
              );
              
              return (
                <button
                  key={alliance.alliance_number}
                  onClick={() => handleAllianceClick(alliance.alliance_number)}
                  disabled={!isValid}
                  className={`p-2 rounded text-center ${
                    selectedAlliance === alliance.alliance_number
                      ? 'bg-purple-600 text-white'
                      : isValid
                        ? 'bg-gray-100 hover:bg-gray-200'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  #{alliance.alliance_number}
                </button>
              );
            })}
          </div>
        </div>
      )}
      
      {/* Confirm button */}
      {action && (
        <div className="mt-6 flex justify-end">
          <button
            onClick={onConfirmAction}
            disabled={!canConfirm}
            className={`px-6 py-2 rounded font-medium ${
              !canConfirm
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            Confirm {getActionDisplayName(action)}
          </button>
        </div>
      )}
    </div>
  );
};

export default TeamActionPanel;