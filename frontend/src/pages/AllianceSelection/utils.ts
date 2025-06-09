/**
 * Utility functions for Alliance Selection
 */

import { Team, LockedPicklist, SelectionState, TeamStatus } from './types';

/**
 * Get the team ranking based on picklist data
 *
 * This function returns a numeric ranking for a team:
 * - If the team is in the first pick list: rank = index (0-999)
 * - If the team is in the second pick list: rank = 1000 + index
 * - If the team is in the third pick list: rank = 2000 + index
 * - If the team isn't found in any picklist: rank = 3000 + (teamNumber/10000)
 *
 * This ensures teams are displayed in order of their picklist ranking.
 *
 * The fallback logic (for teams not in picklist) uses the team number as a rough
 * proxy for quality, assuming historically strong teams (254, 1114, etc.) have lower
 * numbers than newer teams. This is not perfect but provides reasonable sorting
 * when no picklist data is available.
 *
 * @param teamNumber - The team number to look up
 * @param picklist - The locked picklist data
 * @param roundNumber - Optional round number to prioritize that specific picklist (1, 2, or 3)
 * @returns A numeric rank value (lower is better)
 */
export const getTeamRank = (
  teamNumber: number, 
  picklist: LockedPicklist | null, 
  roundNumber?: number
): number => {
  // If we have a picklist, use it for ranking
  if (picklist) {
    // If a specific round is requested, prioritize that picklist for ranking
    if (roundNumber) {
      // Check requested picklist first
      if (roundNumber === 1 && picklist.first_pick_data?.teams) {
        const teamIndex = picklist.first_pick_data.teams.findIndex(t => t.team_number === teamNumber);
        if (teamIndex !== -1) {
          return teamIndex;
        }
      } else if (roundNumber === 2 && picklist.second_pick_data?.teams) {
        const teamIndex = picklist.second_pick_data.teams.findIndex(t => t.team_number === teamNumber);
        if (teamIndex !== -1) {
          return 1000 + teamIndex;
        }
      } else if (roundNumber === 3 && picklist.third_pick_data?.teams) {
        const teamIndex = picklist.third_pick_data.teams.findIndex(t => t.team_number === teamNumber);
        if (teamIndex !== -1) {
          return 2000 + teamIndex;
        }
      }
    }

    // If no specific round or team wasn't found in the specified round's picklist,
    // follow the standard approach of checking all picklists

    // Check first pick list
    if (picklist.first_pick_data?.teams) {
      const firstPickIndex = picklist.first_pick_data.teams.findIndex(t => t.team_number === teamNumber);
      if (firstPickIndex !== -1) {
        return firstPickIndex;
      }
    }

    // Check second pick list
    if (picklist.second_pick_data?.teams) {
      const secondPickIndex = picklist.second_pick_data.teams.findIndex(t => t.team_number === teamNumber);
      if (secondPickIndex !== -1) {
        return 1000 + secondPickIndex;
      }
    }

    // Check third pick list
    if (picklist.third_pick_data?.teams) {
      const thirdPickIndex = picklist.third_pick_data.teams.findIndex(t => t.team_number === teamNumber);
      if (thirdPickIndex !== -1) {
        return 2000 + thirdPickIndex;
      }
    }
  }

  // If we don't have a picklist or the team wasn't found in the picklist,
  // use the team number itself as a fallback - higher numbers will be ranked lower
  // Scale the team number to be between 3000-4000 to ensure it's after all picklist ranks
  return 3000 + (teamNumber / 10000);
};

/**
 * Get team nickname from picklist data
 */
export const getTeamNickname = (teamNumber: number, picklist: LockedPicklist | null): string => {
  if (!picklist) return `Team ${teamNumber}`;
  
  try {
    // Check first pick list
    if (picklist.first_pick_data?.teams) {
      const firstPickTeam = picklist.first_pick_data.teams.find(t => t.team_number === teamNumber);
      if (firstPickTeam?.nickname) return firstPickTeam.nickname;
    }
    
    // Check second pick list
    if (picklist.second_pick_data?.teams) {
      const secondPickTeam = picklist.second_pick_data.teams.find(t => t.team_number === teamNumber);
      if (secondPickTeam?.nickname) return secondPickTeam.nickname;
    }
    
    // Check third pick list if available
    if (picklist.third_pick_data?.teams) {
      const thirdPickTeam = picklist.third_pick_data.teams.find(t => t.team_number === teamNumber);
      if (thirdPickTeam?.nickname) return thirdPickTeam.nickname;
    }
  } catch (err) {
    console.error('Error getting team nickname:', err);
  }
  
  return `Team ${teamNumber}`;
};

/**
 * Check if a team is selectable in the current round
 */
export const isTeamSelectable = (teamNumber: number, selection: SelectionState | null): boolean => {
  if (!selection?.team_statuses) return true;
  
  const status = selection.team_statuses.find(ts => ts.team_number === teamNumber);
  
  if (!status) return false;
  
  // Teams that are captains or already picked are not selectable
  if (status.is_captain || status.is_picked) return false;
  
  // Teams that have declined are not selectable as normal picks
  if (status.has_declined) return false;
  
  // If team was eliminated in a previous round, it's not selectable
  if (status.round_eliminated && status.round_eliminated < selection.current_round) return false;
  
  return true;
};

/**
 * Check if a team can be a captain in the current round
 */
export const canBeCaptain = (teamNumber: number, selection: SelectionState | null): boolean => {
  if (!selection?.team_statuses) return true;
  
  const status = selection.team_statuses.find(ts => ts.team_number === teamNumber);
  
  if (!status) return false;
  
  // Teams that are already captains or picked are not eligible
  if (status.is_captain || status.is_picked) return false;
  
  // Teams that declined can still be captains
  return true;
};

/**
 * Organize teams into 8 columns based on picklist order
 */
export const getTeamColumns = (
  selection: SelectionState | null,
  teamList: number[],
  picklist: LockedPicklist | null
): number[][] => {
  let teamsToUse: number[] = [];

  // Get all the available teams
  if (selection?.team_statuses?.length > 0) {
    // Filter teams based on selection status - only include teams that:
    // 1. Are not captains
    // 2. Are not already picked
    // 3. Have not been eliminated in a previous round
    teamsToUse = selection.team_statuses
      .filter(ts => {
        // Skip teams that are captains or already picked
        if (ts.is_captain || ts.is_picked) return false;

        // Skip teams eliminated in a previous round (but allow teams eliminated in the current round)
        if (ts.round_eliminated && ts.round_eliminated < selection.current_round) return false;

        return true;
      })
      .map(ts => ts.team_number);
  } else if (teamList.length > 0) {
    teamsToUse = [...teamList];
  } else {
    // Fallback to default list of teams for testing
    teamsToUse = [254, 1114, 1678, 2056, 2767, 3310, 4414, 5254, 6329, 7769, 8044,
                  1619, 3538, 4613, 6328, 7429, 8033, 3407, 4290, 6443];
  }

  // Create paired list of team numbers with their ranking
  const allTeamsWithRank: { team_number: number; rank: number }[] = [];

  teamsToUse.forEach(teamNumber => {
    // Use the appropriate picklist based on the current round
    let rank = 9999; // Default high rank (low priority)

    if (picklist) {
      if (selection?.current_round === 1) {
        // For round 1, use the first pick picklist rankings
        rank = getTeamRank(teamNumber, picklist, 1);
      } else if (selection?.current_round === 2) {
        // For round 2, use the second pick picklist rankings
        rank = getTeamRank(teamNumber, picklist, 2);
      } else if (selection?.current_round && selection.current_round >= 3) {
        // For round 3+, use the third pick picklist rankings if available, otherwise second pick
        rank = picklist.third_pick_data 
          ? getTeamRank(teamNumber, picklist, 3) 
          : getTeamRank(teamNumber, picklist, 2);
      } else {
        // Fallback to first pick rankings
        rank = getTeamRank(teamNumber, picklist, 1);
      }
    } else {
      // No picklist available - use team number as fallback
      rank = 3000 + (teamNumber / 10000);
    }

    allTeamsWithRank.push({
      team_number: teamNumber,
      rank: rank
    });
  });

  // Sort the teams by rank (first pick first, lower ranks first)
  allTeamsWithRank.sort((a, b) => a.rank - b.rank);

  // Extract just the team numbers in the sorted order
  const sortedTeamNumbers = allTeamsWithRank.map(team => team.team_number);

  // Split into 8 columns for display
  const columns: number[][] = [[], [], [], [], [], [], [], []];
  const teamsPerColumn = Math.ceil(sortedTeamNumbers.length / 8);

  for (let i = 0; i < sortedTeamNumbers.length; i++) {
    const columnIndex = Math.floor(i / teamsPerColumn);
    if (columnIndex < 8) {
      columns[columnIndex].push(sortedTeamNumbers[i]);
    }
  }

  return columns;
};

/**
 * Get team list from picklist
 */
export const getTeamListFromPicklist = (picklist: LockedPicklist): number[] => {
  const teams = new Set<number>();
  
  picklist.first_pick_data.teams.forEach((team: Team) => teams.add(team.team_number));
  picklist.second_pick_data.teams.forEach((team: Team) => teams.add(team.team_number));
  if (picklist.third_pick_data) {
    picklist.third_pick_data.teams.forEach((team: Team) => teams.add(team.team_number));
  }
  
  return Array.from(teams);
};

/**
 * Get round display name
 */
export const getRoundDisplayName = (round: number): string => {
  switch (round) {
    case 1: return 'First Picks';
    case 2: return 'Second Picks';
    case 3: return 'Backup Robots';
    default: return `Round ${round}`;
  }
};

/**
 * Get column priority display name
 */
export const getColumnPriorityName = (columnIndex: number): string => {
  const priorities = [
    'Highest Picks',
    'High Priority',
    'Priority',
    'Medium Priority',
    'Medium',
    'Medium-Low',
    'Low Priority',
    'Lowest Priority'
  ];
  
  return priorities[columnIndex] || 'Unknown Priority';
};

/**
 * Determine if alliance is valid for a specific action
 */
export const isAllianceValidForAction = (
  alliance: { 
    alliance_number: number;
    captain_team_number: number;
    first_pick_team_number: number;
    second_pick_team_number: number;
    backup_team_number?: number;
  },
  action: 'captain' | 'accept',
  currentRound: number
): boolean => {
  if (action === 'captain') {
    // Alliance is valid for a captain if it doesn't have one yet
    return alliance.captain_team_number === 0;
  } else if (action === 'accept') {
    // Alliance is valid for accept if it has a captain and doesn't have the current round's pick yet
    let isValid = alliance.captain_team_number !== 0;
    
    if (currentRound === 1) {
      isValid = isValid && alliance.first_pick_team_number === 0;
    } else if (currentRound === 2) {
      isValid = isValid && alliance.second_pick_team_number === 0;
    } else if (currentRound === 3) {
      // Allow backup picks if the backup slot is empty (0, null, or undefined)
      isValid = isValid && (!alliance.backup_team_number || alliance.backup_team_number === 0);
    }
    
    return isValid;
  }
  
  return false;
};