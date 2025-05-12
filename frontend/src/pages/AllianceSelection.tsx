// frontend/src/pages/AllianceSelection.tsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// TypeScript interfaces
interface Team {
  team_number: number;
  nickname: string;
  score?: number;
  reasoning?: string;
}

interface Alliance {
  alliance_number: number;
  captain_team_number: number;
  first_pick_team_number: number;
  second_pick_team_number: number;
  backup_team_number?: number;
}

interface TeamStatus {
  team_number: number;
  is_captain: boolean;
  is_picked: boolean;
  has_declined: boolean;
  round_eliminated?: number;
}

interface SelectionState {
  id: number;
  event_key: string;
  year: number;
  is_completed: boolean;
  current_round: number;
  alliances: Alliance[];
  team_statuses: TeamStatus[];
}

interface LockedPicklist {
  id: number;
  team_number: number;
  event_key: string;
  year: number;
  first_pick_data: { teams: Team[] };
  second_pick_data: { teams: Team[] };
  third_pick_data?: { teams: Team[] };
}

const AllianceSelection: React.FC = () => {
  const { selectionId } = useParams<{ selectionId?: string }>();
  const navigate = useNavigate();
  
  // State
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const [picklist, setPicklist] = useState<LockedPicklist | null>(null);
  const [selection, setSelection] = useState<SelectionState | null>(null);
  const [teamList, setTeamList] = useState<number[]>([]);
  
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const [selectedAlliance, setSelectedAlliance] = useState<number | null>(null);
  const [action, setAction] = useState<'captain' | 'accept' | 'decline' | null>(null);
  
  // Load selection state and picklist data
  useEffect(() => {
    if (selectionId) {
      loadSelectionData(parseInt(selectionId));
    } else {
      loadPicklists();
    }
  }, [selectionId]);
  
  const loadPicklists = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('http://localhost:8000/api/alliance/picklists');
      const data = await response.json();
      
      if (data.status === 'success' && data.picklists && data.picklists.length > 0) {
        // Find the most recent picklist
        const latestPicklist = data.picklists.sort((a: any, b: any) => {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        })[0];
        
        // Check if there's an active selection for this picklist
        const selectionResponse = await fetch(`http://localhost:8000/api/alliance/selection/${latestPicklist.id}`);
        
        if (selectionResponse.ok) {
          const selectionData = await selectionResponse.json();
          
          if (selectionData.status === 'success' && selectionData.selection) {
            // Redirect to existing selection
            navigate(`/alliance-selection/${selectionData.selection.id}`);
            return;
          }
        }
        
        // If no selection exists, load the picklist details
        const picklist = await fetchPicklistDetails(latestPicklist.id);
        setPicklist(picklist);
        
        // Get team list from picklist
        const teams = new Set<number>();
        picklist.first_pick_data.teams.forEach((team: Team) => teams.add(team.team_number));
        picklist.second_pick_data.teams.forEach((team: Team) => teams.add(team.team_number));
        if (picklist.third_pick_data) {
          picklist.third_pick_data.teams.forEach((team: Team) => teams.add(team.team_number));
        }
        
        setTeamList(Array.from(teams));
      } else {
        setError('No locked picklists found. Please lock a picklist before proceeding.');
      }
    } catch (err: any) {
      setError('Error loading picklists: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchPicklistDetails = async (picklistId: number): Promise<LockedPicklist> => {
    const response = await fetch(`http://localhost:8000/api/alliance/picklist/${picklistId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch picklist details');
    }
    
    const data = await response.json();
    
    if (data.status !== 'success' || !data.picklist) {
      throw new Error('Invalid picklist data');
    }
    
    return data.picklist;
  };
  
  const loadSelectionData = async (id: number) => {
    try {
      setLoading(true);
      
      const response = await fetch(`http://localhost:8000/api/alliance/selection/${id}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch alliance selection data');
      }
      
      const data = await response.json();
      console.log("Alliance selection data:", data);
      
      if (data.status === 'success' && data.selection) {
        setSelection(data.selection);
        
        // Also fetch the picklist data if picklist_id is defined
        if (data.selection.picklist_id) {
          console.log("Found picklist_id in selection:", data.selection.picklist_id);
          try {
            const picklist = await fetchPicklistDetails(data.selection.picklist_id);
            console.log("Fetched picklist details:", picklist);
            setPicklist(picklist);
          } catch (picklistErr) {
            console.error('Error fetching picklist details:', picklistErr);
            // Continue without picklist data - we can still use the alliance selection
          }
        } else {
          console.warn('Alliance selection has no picklist_id, proceeding without picklist data');
          
          // Fallback: Let's try to find the picklist from the list (if a picklist with this event_key exists)
          try {
            console.log("Attempting to fallback to finding picklist by event_key");
            const picklistsResponse = await fetch('http://localhost:8000/api/alliance/picklists');
            const picklistsData = await picklistsResponse.json();
            
            if (picklistsData.status === 'success' && picklistsData.picklists && picklistsData.picklists.length > 0) {
              // Find a picklist for the same event
              const matchingPicklist = picklistsData.picklists.find((p: any) => 
                p.event_key === data.selection.event_key
              );
              
              if (matchingPicklist) {
                console.log("Found matching picklist by event_key:", matchingPicklist.id);
                
                // Fetch the picklist details
                const picklist = await fetchPicklistDetails(matchingPicklist.id);
                console.log("Fetched fallback picklist details:", picklist);
                setPicklist(picklist);
              } else {
                console.warn("No matching picklist found by event_key");
              }
            }
          } catch (fallbackErr) {
            console.error('Error in picklist fallback attempt:', fallbackErr);
          }
        }
      } else {
        setError('Alliance selection not found');
      }
    } catch (err: any) {
      setError('Error loading alliance selection: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const createNewSelection = async () => {
    try {
      setLoading(true);
      
      // Use picklist data if available, otherwise use default values
      const event_key = picklist?.event_key || '2025arc';
      const year = picklist?.year || 2025;
      let picklist_id = picklist?.id || null;  // Changed to 'let' so we can modify it
      
      console.log("Creating new alliance selection with picklist_id:", picklist_id);
      console.log("Picklist data available:", !!picklist);
      
      // If we don't have a picklist ID but have a team number and event key, try to find a matching picklist
      if (!picklist_id) {
        try {
          console.log("No picklist ID, looking for matching picklist");
          const picklistsResponse = await fetch('http://localhost:8000/api/alliance/picklists');
          const picklistsData = await picklistsResponse.json();
          
          if (picklistsData.status === 'success' && picklistsData.picklists && picklistsData.picklists.length > 0) {
            // Find the latest picklist for the same event
            const matchingPicklists = picklistsData.picklists.filter((p: any) => 
              p.event_key === event_key
            );
            
            if (matchingPicklists.length > 0) {
              // Sort by creation date (newest first)
              const latestPicklist = matchingPicklists.sort((a: any, b: any) => {
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
              })[0];
              
              console.log("Found matching picklist:", latestPicklist.id);
              
              // Fetch the picklist details to use for sorting teams
              const picklistDetails = await fetchPicklistDetails(latestPicklist.id);
              setPicklist(picklistDetails);
              
              // Update our picklist_id for the new alliance selection
              picklist_id = latestPicklist.id;
            }
          }
        } catch (err) {
          console.error("Error looking for matching picklist:", err);
        }
      }
      
      const response = await fetch('http://localhost:8000/api/alliance/selection/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          picklist_id: picklist_id, // Might be null, which is okay
          event_key: event_key,
          year: year,
          team_list: teamList
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create alliance selection');
      }
      
      const data = await response.json();
      console.log("Created new alliance selection:", data);
      
      // Navigate to the new selection
      navigate(`/alliance-selection/${data.id}`);
      
    } catch (err: any) {
      setError('Error creating alliance selection: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const performTeamAction = async (action: 'captain' | 'accept' | 'decline') => {
    if (!selection || !selectedTeam) return;
    
    try {
      setLoading(true);
      
      const requestBody: any = {
        selection_id: selection.id,
        team_number: selectedTeam,
        action: action
      };
      
      // Add alliance number for captain and accept actions
      if (action === 'captain' || action === 'accept') {
        if (!selectedAlliance) {
          setError('Please select an alliance');
          setLoading(false);
          return;
        }
        requestBody.alliance_number = selectedAlliance;
      }
      
      const response = await fetch('http://localhost:8000/api/alliance/selection/team-action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to perform team action');
      }
      
      // Success! Reload selection data
      await loadSelectionData(selection.id);
      
      // Clear selections
      setSelectedTeam(null);
      setSelectedAlliance(null);
      setAction(null);
      
      // Show success message
      setSuccessMessage(`Team ${selectedTeam} ${
        action === 'captain' ? 'is now alliance captain' :
        action === 'accept' ? 'accepted the selection' :
        'declined the selection'
      }`);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
      
    } catch (err: any) {
      setError('Error performing team action: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleRemoveTeam = async (teamNumber: number, allianceNumber: number) => {
    if (!selection) return;

    // Confirm before removing
    if (!window.confirm(`Are you sure you want to remove team ${teamNumber} from alliance ${allianceNumber}?`)) {
      return;
    }

    try {
      setLoading(true);

      const response = await fetch('http://localhost:8000/api/alliance/selection/team-action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          selection_id: selection.id,
          team_number: teamNumber,
          action: 'remove',
          alliance_number: allianceNumber
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to remove team from alliance');
      }

      // Success! Reload selection data
      await loadSelectionData(selection.id);

      // Show success message
      setSuccessMessage(`Team ${teamNumber} has been removed from alliance ${allianceNumber}`);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err: any) {
      setError('Error removing team: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const advanceToNextRound = async () => {
    if (!selection) return;

    try {
      setLoading(true);

      const response = await fetch(`http://localhost:8000/api/alliance/selection/${selection.id}/next-round`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to advance to next round');
      }

      // Reset the selected team and action
      setSelectedTeam(null);
      setSelectedAlliance(null);
      setAction(null);

      // Reload selection data
      await loadSelectionData(selection.id);

      // Show success message
      setSuccessMessage(
        selection.current_round >= 3
          ? 'Alliance selection completed after backup selections!'
          : `Advanced to round ${selection.current_round + 1}`
      );

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err: any) {
      setError('Error advancing to next round: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  // Check if a team is selectable in the current round
  const isTeamSelectable = (teamNumber: number): boolean => {
    if (!selection || !selection.team_statuses) return true;
    
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
  
  // Check if a team can be a captain in the current round
  const canBeCaptain = (teamNumber: number): boolean => {
    if (!selection || !selection.team_statuses) return true;
    
    const status = selection.team_statuses.find(ts => ts.team_number === teamNumber);
    
    if (!status) return false;
    
    // Teams that are already captains or picked are not eligible
    if (status.is_captain || status.is_picked) return false;
    
    // Teams that declined can still be captains
    return true;
  };
  
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
   * @param roundNumber - Optional round number to prioritize that specific picklist (1, 2, or 3)
   * @returns A numeric rank value (lower is better)
   */
  const getTeamRank = (teamNumber: number, roundNumber?: number): number => {
    // If we have a picklist, use it for ranking
    if (picklist) {
      console.log("Using picklist for ranking with ID:", picklist.id);

      // If a specific round is requested, prioritize that picklist for ranking
      if (roundNumber) {
        let foundInSpecifiedRound = false;
        let rank = 0;

        // Check requested picklist first
        if (roundNumber === 1 && picklist.first_pick_data && picklist.first_pick_data.teams) {
          const teamIndex = picklist.first_pick_data.teams.findIndex(t => t.team_number === teamNumber);
          if (teamIndex !== -1) {
            // Team is in the 1st pick list - use its position
            return teamIndex;
          }
        } else if (roundNumber === 2 && picklist.second_pick_data && picklist.second_pick_data.teams) {
          const teamIndex = picklist.second_pick_data.teams.findIndex(t => t.team_number === teamNumber);
          if (teamIndex !== -1) {
            // Team is in the 2nd pick list - use its position + 1000
            return 1000 + teamIndex;
          }
        } else if (roundNumber === 3 && picklist.third_pick_data && picklist.third_pick_data.teams) {
          const teamIndex = picklist.third_pick_data.teams.findIndex(t => t.team_number === teamNumber);
          if (teamIndex !== -1) {
            // Team is in the 3rd pick list - use its position + 2000
            return 2000 + teamIndex;
          }
        }
      }

      // If no specific round or team wasn't found in the specified round's picklist,
      // follow the standard approach of checking all picklists

      // Create array of all teams in their ranked order combining all pick positions
      const allRankedTeams: {team_number: number, rank: number}[] = [];

      // Add teams from first pick list
      if (picklist.first_pick_data && picklist.first_pick_data.teams) {
        picklist.first_pick_data.teams.forEach((team, index) => {
          allRankedTeams.push({
            team_number: team.team_number,
            rank: index // Lower index = higher rank
          });
        });
      }

      // Add teams from second pick list
      if (picklist.second_pick_data && picklist.second_pick_data.teams) {
        picklist.second_pick_data.teams.forEach((team, index) => {
          // Only add if not already in the list
          if (!allRankedTeams.some(t => t.team_number === team.team_number)) {
            allRankedTeams.push({
              team_number: team.team_number,
              rank: 1000 + index // Second pick teams come after first pick teams
            });
          }
        });
      }

      // Add teams from third pick list
      if (picklist.third_pick_data && picklist.third_pick_data.teams) {
        picklist.third_pick_data.teams.forEach((team, index) => {
          // Only add if not already in the list
          if (!allRankedTeams.some(t => t.team_number === team.team_number)) {
            allRankedTeams.push({
              team_number: team.team_number,
              rank: 2000 + index // Third pick teams come after second pick teams
            });
          }
        });
      }

      // Find the team's rank
      const teamRankObj = allRankedTeams.find(t => t.team_number === teamNumber);
      if (teamRankObj) {
        return teamRankObj.rank;
      }
    }

    // If we don't have a picklist or the team wasn't found in the picklist,
    // use the team number itself as a fallback - higher numbers will be ranked lower
    // This means teams like 254, 1114, etc. will be ranked higher than teams with high numbers,
    // which is generally a decent fallback since historically successful teams tend to have lower numbers

    // Scale the team number to be between 3000-4000 to ensure it's after all picklist ranks
    return 3000 + (teamNumber / 10000);
  };

  // Organize teams into 8 columns based on picklist order
  const getTeamColumns = (): number[][] => {
    const allTeamsWithRank: {team_number: number, rank: number}[] = [];
    let teamsToUse: number[] = [];

    // Get all the available teams
    if (selection && selection.team_statuses && selection.team_statuses.length > 0) {
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

      console.log(`Using team statuses from selection (filtered for round ${selection.current_round}):`, teamsToUse.length, "teams");
    } else if (teamList.length > 0) {
      teamsToUse = [...teamList];
      console.log("Using team list:", teamsToUse.length, "teams");
    } else {
      // Fallback to default list of teams for testing
      teamsToUse = [254, 1114, 1678, 2056, 2767, 3310, 4414, 5254, 6329, 7769, 8044,
                    1619, 3538, 4613, 6328, 7429, 8033, 3407, 4290, 6443];
      console.log("Using fallback team list:", teamsToUse.length, "teams");
    }

    // Log picklist status
    console.log("Picklist available:", picklist !== null);
    if (picklist) {
      console.log("First pick teams:", picklist.first_pick_data?.teams?.length || 0);
      console.log("Second pick teams:", picklist.second_pick_data?.teams?.length || 0);
      console.log("Third pick teams:", picklist.third_pick_data?.teams?.length || 0);
      console.log("Current round:", selection?.current_round || 1);
    }

    // Create paired list of team numbers with their ranking
    teamsToUse.forEach(teamNumber => {
      // Use the appropriate picklist based on the current round
      let rank = 9999; // Default high rank (low priority)

      if (picklist) {
        if (selection?.current_round === 1) {
          // For round 1, use the first pick picklist rankings
          rank = getTeamRank(teamNumber, 1);
        } else if (selection?.current_round === 2) {
          // For round 2, use the second pick picklist rankings
          rank = getTeamRank(teamNumber, 2);
        } else if (selection?.current_round >= 3) {
          // For round 3+, use the third pick picklist rankings if available, otherwise second pick
          rank = picklist.third_pick_data ? getTeamRank(teamNumber, 3) : getTeamRank(teamNumber, 2);
        } else {
          // Fallback to first pick rankings
          rank = getTeamRank(teamNumber, 1);
        }
      } else {
        // No picklist available - use team number as fallback
        rank = 3000 + (teamNumber / 10000);
      }

      allTeamsWithRank.push({
        team_number: teamNumber,
        rank: rank
      });

      // Log a few team ranks for debugging
      if (teamNumber === teamsToUse[0] || teamNumber === teamsToUse[1] ||
          teamNumber === teamsToUse[2] || teamNumber === teamsToUse[3]) {
        console.log(`Team ${teamNumber} rank: ${rank}`);
      }
    });

    // Sort the teams by rank (first pick first, lower ranks first)
    allTeamsWithRank.sort((a, b) => a.rank - b.rank);

    // Extract just the team numbers in the sorted order
    const sortedTeamNumbers = allTeamsWithRank.map(team => team.team_number);

    // Log first few sorted teams for debugging
    console.log("First few sorted teams:", sortedTeamNumbers.slice(0, 5));

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
  
  // Get team nickname from picklist data
  const getTeamNickname = (teamNumber: number): string => {
    if (!picklist) return `Team ${teamNumber}`;
    
    try {
      // Check first pick list
      if (picklist.first_pick_data && picklist.first_pick_data.teams) {
        const firstPickTeam = picklist.first_pick_data.teams.find(t => t.team_number === teamNumber);
        if (firstPickTeam && firstPickTeam.nickname) return firstPickTeam.nickname;
      }
      
      // Check second pick list
      if (picklist.second_pick_data && picklist.second_pick_data.teams) {
        const secondPickTeam = picklist.second_pick_data.teams.find(t => t.team_number === teamNumber);
        if (secondPickTeam && secondPickTeam.nickname) return secondPickTeam.nickname;
      }
      
      // Check third pick list if available
      if (picklist.third_pick_data && picklist.third_pick_data.teams) {
        const thirdPickTeam = picklist.third_pick_data.teams.find(t => t.team_number === teamNumber);
        if (thirdPickTeam && thirdPickTeam.nickname) return thirdPickTeam.nickname;
      }
    } catch (err) {
      console.error('Error getting team nickname:', err);
    }
    
    return `Team ${teamNumber}`;
  };
  
  // Rendering the loading state
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className="max-w-5xl mx-auto p-6">
        <div className="bg-red-100 text-red-700 p-4 rounded mb-6">
          {error}
        </div>
        <button
          onClick={() => navigate('/picklist')}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Return to Picklist
        </button>
      </div>
    );
  }
  
  // Render new selection screen
  if (!selection && picklist) {
    return (
      <div className="max-w-5xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Start Alliance Selection</h1>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Picklist Information</h2>
          <p className="mb-2"><span className="font-semibold">Team:</span> {picklist.team_number}</p>
          <p className="mb-2"><span className="font-semibold">Event:</span> {picklist.event_key}</p>
          <p className="mb-4"><span className="font-semibold">Year:</span> {picklist.year}</p>
          
          <div className="flex space-x-4">
            <button
              onClick={createNewSelection}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Start Alliance Selection
            </button>
            
            <button
              onClick={() => navigate('/picklist')}
              className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100"
            >
              Back to Picklist
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  // Render the alliance selection interface
  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Live Alliance Selection</h1>
        
        <div className="flex items-center space-x-3">
          {selection && !selection.is_completed && (
            <button
              onClick={advanceToNextRound}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {selection.current_round === 3 ? 'Complete After Backup Selections' : 
               selection.current_round > 3 ? 'Finalize Alliance Selection' : 
               `Advance to Round ${selection.current_round + 1}`}
            </button>
          )}
          
          <button
            onClick={() => navigate('/picklist')}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100"
          >
            Back to Picklist
          </button>
        </div>
      </div>
      
      {successMessage && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {successMessage}
        </div>
      )}
      
      {/* Round information */}
      {selection && (
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold">
                Round {selection.current_round}
                {selection.current_round === 1 ? ' (First Picks)' : 
                 selection.current_round === 2 ? ' (Second Picks)' : 
                 ' (Backup Robots)'}
              </h2>
              <p className="text-gray-600">
                Select teams as they are called during the alliance selection
              </p>
            </div>
            
            <div className="flex space-x-3">
              <span className={`px-3 py-1 rounded-full ${selection.is_completed ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`}>
                {selection.is_completed ? 'Completed' : 'In Progress'}
              </span>
            </div>
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Team Grid */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-4">
            <h2 className="text-xl font-bold mb-4">
              Team Selection
              {selection && (
                <span className="text-blue-600 ml-2">
                  {selection.current_round === 1 ? '(1st Pick List)' :
                   selection.current_round === 2 ? '(2nd Pick List)' :
                   selection.current_round === 3 ? '(3rd Pick List)' :
                   '(Backup Picks)'}
                </span>
              )}
            </h2>

            {/* Team selection grid */}
            <div className="grid grid-cols-8 gap-2">
              {getTeamColumns().map((column, columnIndex) => (
                <div key={columnIndex} className="space-y-2">
                  <div className="text-center text-xs font-bold bg-gray-100 p-1 rounded">
                    {columnIndex === 0 ? 'Highest Picks' :
                     columnIndex === 1 ? 'High Priority' :
                     columnIndex === 2 ? 'Priority' :
                     columnIndex === 3 ? 'Medium Priority' :
                     columnIndex === 4 ? 'Medium' :
                     columnIndex === 5 ? 'Medium-Low' :
                     columnIndex === 6 ? 'Low Priority' :
                     'Lowest Priority'}
                  </div>
                  {column.map(teamNumber => {
                    const isSelected = selectedTeam === teamNumber;
                    const teamStatus = selection?.team_statuses.find(ts => ts.team_number === teamNumber);
                    
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
                    
                    return (
                      <button
                        key={teamNumber}
                        onClick={() => setSelectedTeam(isSelected ? null : teamNumber)}
                        className={`w-full p-2 rounded text-center ${statusClass} ${
                          // Check if the team should be clickable
                          (
                            (!teamStatus) || // No status yet
                            // Not already a captain/picked and not eliminated in previous round
                            (!teamStatus.is_captain && !teamStatus.is_picked && 
                            (!teamStatus.round_eliminated || teamStatus.round_eliminated >= (selection?.current_round || 1))) ||
                            // Specifically allow declined teams to be clickable (for becoming captains)
                            (teamStatus.has_declined)
                          )
                            ? "cursor-pointer"
                            : "cursor-default"
                        }`}
                        // Only disable the button for these specific cases:
                        disabled={teamStatus && 
                          // Already a captain or already picked
                          (teamStatus.is_captain || teamStatus.is_picked ||
                           // Eliminated in a previous round
                           (teamStatus.round_eliminated && teamStatus.round_eliminated < (selection?.current_round || 1)))
                        }
                      >
                        <div className="font-medium">{teamNumber}</div>
                        <div className="text-xs truncate max-w-full" title={getTeamNickname(teamNumber)}>
                          {getTeamNickname(teamNumber).substring(0, 12)}
                          {getTeamNickname(teamNumber).length > 12 ? '...' : ''}
                        </div>
                        {picklist && getTeamRank(teamNumber) < 9999 && (
                          <div className="text-xs font-bold" title="Rank in your picklist">
                            {getTeamRank(teamNumber) < 1000 ? '1st' :
                             getTeamRank(teamNumber) < 2000 ? '2nd' : '3rd'} Pick #{getTeamRank(teamNumber) % 1000 + 1}
                          </div>
                        )}
                        {selection && selection.current_round && picklist && (
                          <div className="text-xs">
                            {selection.current_round === 1 && getTeamRank(teamNumber, 1) < 1000 && (
                              <span className="text-green-600">Current Round Pick</span>
                            )}
                            {selection.current_round === 2 && getTeamRank(teamNumber, 2) < 2000 && getTeamRank(teamNumber, 2) >= 1000 && (
                              <span className="text-green-600">Current Round Pick</span>
                            )}
                            {selection.current_round === 3 && getTeamRank(teamNumber, 3) < 3000 && getTeamRank(teamNumber, 3) >= 2000 && picklist.third_pick_data && (
                              <span className="text-green-600">Current Round Pick</span>
                            )}
                          </div>
                        )}
                        {statusText && <div className="text-xs mt-1 font-semibold">{statusText}</div>}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
            
            {/* Team actions */}
            {selectedTeam && selection && !selection.is_completed && (
              <div className="mt-6 p-4 border border-blue-200 bg-blue-50 rounded">
                <h3 className="font-bold text-lg mb-2">
                  Selected: {selectedTeam} - {getTeamNickname(selectedTeam)}
                </h3>
                
                <div className="flex flex-wrap gap-3 mt-4">
                  {canBeCaptain(selectedTeam) && (
                    <button
                      onClick={() => setAction('captain')}
                      className={`px-4 py-2 rounded ${
                        action === 'captain' ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                      }`}
                    >
                      Alliance Captain
                    </button>
                  )}
                  
                  {isTeamSelectable(selectedTeam) && (
                    <>
                      <button
                        onClick={() => setAction('accept')}
                        className={`px-4 py-2 rounded ${
                          action === 'accept' ? 'bg-green-600 text-white' : 'bg-green-100 text-green-800 hover:bg-green-200'
                        }`}
                      >
                        Accept Selection
                      </button>
                      
                      <button
                        onClick={() => setAction('decline')}
                        className={`px-4 py-2 rounded ${
                          action === 'decline' ? 'bg-red-600 text-white' : 'bg-red-100 text-red-800 hover:bg-red-200'
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
                        let isValid = false;
                        
                        if (action === 'captain') {
                          // Alliance is valid for a captain if it doesn't have one yet
                          isValid = alliance.captain_team_number === 0;
                        } else if (action === 'accept') {
                          // Alliance is valid for accept if it has a captain and doesn't have the current round's pick yet
                          isValid = alliance.captain_team_number !== 0;
                          
                          if (selection.current_round === 1) {
                            isValid = isValid && alliance.first_pick_team_number === 0;
                          } else if (selection.current_round === 2) {
                            isValid = isValid && alliance.second_pick_team_number === 0;
                          } else if (selection.current_round === 3) {
                            // Allow backup picks if the backup slot is empty (0, null, or undefined)
                            isValid = isValid && (!alliance.backup_team_number || alliance.backup_team_number === 0);
                          }
                        }
                        
                        return (
                          <button
                            key={alliance.alliance_number}
                            onClick={() => setSelectedAlliance(alliance.alliance_number)}
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
                      onClick={() => performTeamAction(action)}
                      disabled={(action === 'captain' || action === 'accept') && !selectedAlliance}
                      className={`px-6 py-2 rounded font-medium ${
                        (action === 'captain' || action === 'accept') && !selectedAlliance
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-purple-600 text-white hover:bg-purple-700'
                      }`}
                    >
                      Confirm {action === 'captain' ? 'Captain' : action === 'accept' ? 'Accept' : 'Decline'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        
        {/* Right Column - Alliance Board */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-4">
            <h2 className="text-xl font-bold mb-4">Alliance Board</h2>
            
            {selection && (
              <div className="space-y-3">
                {selection.alliances.map(alliance => (
                  <div 
                    key={alliance.alliance_number}
                    className={`p-3 rounded-lg border ${
                      selectedAlliance === alliance.alliance_number
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200'
                    }`}
                  >
                    <div className="font-bold text-lg">Alliance #{alliance.alliance_number}</div>
                    
                    <div className="grid grid-cols-2 gap-2 mt-2">
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
                            onClick={() => handleRemoveTeam(alliance.first_pick_team_number, alliance.alliance_number)}
                            className="absolute top-0 right-0 bg-red-500 text-white text-xs w-4 h-4 flex items-center justify-center rounded-full -mt-1 -mr-1"
                            title="Remove team"
                          >
                            ×
                          </button>
                        )}
                      </div>

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
                            onClick={() => handleRemoveTeam(alliance.second_pick_team_number, alliance.alliance_number)}
                            className="absolute top-0 right-0 bg-red-500 text-white text-xs w-4 h-4 flex items-center justify-center rounded-full -mt-1 -mr-1"
                            title="Remove team"
                          >
                            ×
                          </button>
                        )}
                      </div>

                      {/* Always show backup slot after round 3 starts */}
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
                              onClick={() => handleRemoveTeam(alliance.backup_team_number, alliance.alliance_number)}
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
            )}
            
            {/* Print button */}
            {selection && (
              <div className="mt-6">
                <button
                  onClick={() => window.print()}
                  className="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center justify-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clipRule="evenodd" />
                  </svg>
                  Print Alliance Selection
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AllianceSelection;