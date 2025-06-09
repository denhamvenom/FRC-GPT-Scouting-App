/**
 * Team Grid Component - Displays teams organized in columns for selection
 */

import React from 'react';
import { TeamGridProps } from '../types';
import { getColumnPriorityName } from '../utils';
import TeamStatusIndicator from './TeamStatusIndicator';

const TeamGrid: React.FC<TeamGridProps> = ({
  teams,
  selectedTeam,
  onTeamSelect,
  selection,
  picklist,
  getTeamNickname,
  getTeamRank
}) => {
  if (!teams || teams.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No teams available for selection
      </div>
    );
  }

  return (
    <div className="grid grid-cols-8 gap-2">
      {teams.map((column, columnIndex) => (
        <div key={columnIndex} className="space-y-2">
          <div className="text-center text-xs font-bold bg-gray-100 p-1 rounded">
            {getColumnPriorityName(columnIndex)}
          </div>
          {column.map(teamNumber => {
            const isSelected = selectedTeam === teamNumber;
            const teamStatus = selection?.team_statuses.find(ts => ts.team_number === teamNumber);
            
            // Determine if the team should be clickable
            const isClickable = (
              (!teamStatus) || // No status yet
              // Not already a captain/picked and not eliminated in previous round
              (!teamStatus.is_captain && !teamStatus.is_picked && 
              (!teamStatus.round_eliminated || teamStatus.round_eliminated >= (selection?.current_round || 1))) ||
              // Specifically allow declined teams to be clickable (for becoming captains)
              (teamStatus.has_declined)
            );

            // Determine if button should be disabled
            const isDisabled = teamStatus && 
              // Already a captain or already picked
              (teamStatus.is_captain || teamStatus.is_picked ||
               // Eliminated in a previous round
               (teamStatus.round_eliminated && teamStatus.round_eliminated < (selection?.current_round || 1)));
            
            return (
              <TeamStatusIndicator
                key={teamNumber}
                teamNumber={teamNumber}
                teamStatus={teamStatus}
                isSelected={isSelected}
                picklist={picklist}
                currentRound={selection?.current_round || 1}
                getTeamRank={getTeamRank}
                getTeamNickname={getTeamNickname}
                isClickable={isClickable}
                isDisabled={isDisabled}
                onClick={() => onTeamSelect(isSelected ? null : teamNumber)}
              />
            );
          })}
        </div>
      ))}
    </div>
  );
};

export default TeamGrid;