/**
 * Team Status Indicator Component - Individual team button with status visualization
 */

import React from 'react';
import { TeamStatus, LockedPicklist } from '../types';

interface TeamStatusIndicatorProps {
  teamNumber: number;
  teamStatus?: TeamStatus;
  isSelected: boolean;
  picklist: LockedPicklist | null;
  currentRound: number;
  getTeamRank: (teamNumber: number, roundNumber?: number) => number;
  getTeamNickname: (teamNumber: number) => string;
  isClickable: boolean;
  isDisabled: boolean;
  onClick: () => void;
}

const TeamStatusIndicator: React.FC<TeamStatusIndicatorProps> = ({
  teamNumber,
  teamStatus,
  isSelected,
  picklist,
  currentRound,
  getTeamRank,
  getTeamNickname,
  isClickable,
  isDisabled,
  onClick
}) => {
  // Determine team status styles
  let statusClass = "";
  let statusText = "";
  
  if (teamStatus) {
    if (teamStatus.is_captain) {
      statusClass = "bg-blue-600 text-white";
      statusText = "Captain";
    } else if (teamStatus.is_picked) {
      statusClass = "bg-green-600 text-white";
      statusText = "Picked";
    } else if (teamStatus.has_declined) {
      statusClass = "bg-red-600 text-white";
      statusText = "Declined";
    } else if (teamStatus.round_eliminated) {
      statusClass = "bg-gray-400 text-white";
      statusText = `Round ${teamStatus.round_eliminated}`;
    } else {
      statusClass = isSelected ? "bg-purple-600 text-white" : "bg-gray-100 hover:bg-gray-200";
      statusText = "";
    }
  } else {
    statusClass = isSelected ? "bg-purple-600 text-white" : "bg-gray-100 hover:bg-gray-200";
  }

  const nickname = getTeamNickname(teamNumber);
  const truncatedNickname = nickname.length > 12 ? nickname.substring(0, 12) + '...' : nickname;
  
  // Determine pick list ranking display
  const teamRank = getTeamRank(teamNumber);
  const pickListInfo = picklist && teamRank < 9999 ? {
    list: teamRank < 1000 ? '1st' : teamRank < 2000 ? '2nd' : '3rd',
    position: (teamRank % 1000) + 1
  } : null;

  // Check if team is in current round's pick list
  const isCurrentRoundPick = picklist && (
    (currentRound === 1 && getTeamRank(teamNumber, 1) < 1000) ||
    (currentRound === 2 && getTeamRank(teamNumber, 2) < 2000 && getTeamRank(teamNumber, 2) >= 1000) ||
    (currentRound === 3 && getTeamRank(teamNumber, 3) < 3000 && getTeamRank(teamNumber, 3) >= 2000 && picklist.third_pick_data)
  );

  return (
    <button
      onClick={onClick}
      className={`w-full p-2 rounded text-center ${statusClass} ${
        isClickable ? "cursor-pointer" : "cursor-default"
      }`}
      disabled={isDisabled}
      title={`${teamNumber} - ${nickname}`}
    >
      <div className="font-medium">{teamNumber}</div>
      <div className="text-xs truncate max-w-full" title={nickname}>
        {truncatedNickname}
      </div>
      
      {pickListInfo && (
        <div className="text-xs font-bold" title="Rank in your picklist">
          {pickListInfo.list} Pick #{pickListInfo.position}
        </div>
      )}
      
      {isCurrentRoundPick && (
        <div className="text-xs">
          <span className="text-green-600">Current Round Pick</span>
        </div>
      )}
      
      {statusText && (
        <div className="text-xs mt-1 font-semibold">{statusText}</div>
      )}
    </button>
  );
};

export default TeamStatusIndicator;