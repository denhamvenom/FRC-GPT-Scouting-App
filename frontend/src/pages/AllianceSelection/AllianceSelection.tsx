/**
 * Alliance Selection Component - Refactored main container
 * 
 * This component orchestrates the alliance selection process using:
 * - Custom hooks for state management and business logic
 * - Focused components for specific UI concerns
 * - Proper TypeScript typing throughout
 * - Error boundaries and loading states
 */

import React, { useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// Custom hooks
import { useAllianceSelection } from './hooks/useAllianceSelection';
import { useTeamActions } from './hooks/useTeamActions';
import { useAllianceState } from './hooks/useAllianceState';
import { usePolling } from './hooks/usePolling';

// Components
import TeamGrid from './components/TeamGrid';
import AllianceBoard from './components/AllianceBoard';
import TeamActionPanel from './components/TeamActionPanel';
import ProgressIndicator from './components/ProgressIndicator';

// Utils and types
import { getTeamColumns, getTeamNickname, getTeamRank, getRoundDisplayName } from './utils';

const AllianceSelection: React.FC = () => {
  const { selectionId } = useParams<{ selectionId?: string }>();
  const navigate = useNavigate();
  
  // Main alliance selection state
  const {
    loading,
    error,
    successMessage,
    picklist,
    selection,
    teamList,
    loadPicklists,
    loadSelectionData,
    createNewSelection,
    clearError,
    clearSuccessMessage,
  } = useAllianceSelection();

  // Team actions state and handlers
  const {
    selectedTeam,
    selectedAlliance,
    action,
    setSelectedTeam,
    setSelectedAlliance,
    setAction,
    performTeamAction,
    handleRemoveTeam,
    clearSelections,
    canBeCaptain,
    isTeamSelectable,
  } = useTeamActions({
    selection,
    onSuccess: (message) => {
      clearSuccessMessage();
      // Show success message and auto-clear it
      setTimeout(() => clearSuccessMessage(), 3000);
    },
    onError: (errorMsg) => {
      clearError();
    },
    onSelectionUpdate: async () => {
      if (selection) {
        await loadSelectionData(selection.id);
      }
    }
  });

  // Alliance state management (advance round, reset)
  const { advanceToNextRound, resetAllianceSelection } = useAllianceState({
    selection,
    onSuccess: (message) => {
      clearSuccessMessage();
      setTimeout(() => clearSuccessMessage(), 3000);
    },
    onError: (errorMsg) => {
      clearError();
    },
    onSelectionUpdate: async () => {
      if (selection) {
        await loadSelectionData(selection.id);
      }
    },
    onClearSelections: clearSelections
  });

  // Polling for real-time updates
  const { isPolling, startPolling, stopPolling } = usePolling({
    onPoll: async () => {
      if (selection && !selection.is_completed) {
        await loadSelectionData(selection.id);
      }
    },
    enabled: !!selection && !selection.is_completed
  });

  // Load initial data
  useEffect(() => {
    if (selectionId) {
      loadSelectionData(parseInt(selectionId));
    } else {
      loadPicklists();
    }
  }, [selectionId, loadSelectionData, loadPicklists]);

  // Start/stop polling based on selection state
  useEffect(() => {
    if (selection && !selection.is_completed) {
      startPolling(10000); // Poll every 10 seconds
    } else {
      stopPolling();
    }

    return () => stopPolling();
  }, [selection, startPolling, stopPolling]);

  // Helper functions for components
  const getTeamNicknameWrapper = useCallback((teamNumber: number) => {
    return getTeamNickname(teamNumber, picklist);
  }, [picklist]);

  const getTeamRankWrapper = useCallback((teamNumber: number, roundNumber?: number) => {
    return getTeamRank(teamNumber, picklist, roundNumber);
  }, [picklist]);

  const handleConfirmAction = useCallback(async () => {
    if (action) {
      await performTeamAction(action);
    }
  }, [action, performTeamAction]);

  // Auto-clear messages after timeout
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => clearSuccessMessage(), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage, clearSuccessMessage]);

  // Render loading state
  if (loading) {
    return <ProgressIndicator loading={loading} error={null} successMessage={null} />;
  }
  
  // Render error state
  if (error) {
    return (
      <div className="max-w-5xl mx-auto p-6">
        <ProgressIndicator loading={false} error={error} successMessage={null} />
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

  // Get team columns for display
  const teamColumns = getTeamColumns(selection, teamList, picklist);
  
  // Render the alliance selection interface
  return (
    <div className="max-w-7xl mx-auto p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">
          Live Alliance Selection
          {isPolling && (
            <span className="text-sm text-gray-500 ml-2">(Auto-updating)</span>
          )}
        </h1>
        
        <div className="flex items-center space-x-3">
          {selection && !selection.is_completed && (
            <>
              <button
                onClick={advanceToNextRound}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                {selection.current_round === 3 ? 'Complete After Backup Selections' : 
                 selection.current_round > 3 ? 'Finalize Alliance Selection' : 
                 `Advance to Round ${selection.current_round + 1}`}
              </button>
              
              <button
                onClick={resetAllianceSelection}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Reset Selection
              </button>
            </>
          )}
          
          <button
            onClick={() => navigate('/picklist')}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100"
          >
            Back to Picklist
          </button>
        </div>
      </div>
      
      {/* Progress indicators */}
      <ProgressIndicator 
        loading={false} 
        error={error} 
        successMessage={successMessage} 
      />
      
      {/* Round information */}
      {selection && (
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold">
                Round {selection.current_round} ({getRoundDisplayName(selection.current_round)})
              </h2>
              <p className="text-gray-600">
                Select teams as they are called during the alliance selection
              </p>
            </div>
            
            <div className="flex space-x-3">
              <span className={`px-3 py-1 rounded-full ${
                selection.is_completed 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-blue-100 text-blue-800'
              }`}>
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
                  ({selection.current_round === 1 ? '1st Pick List' :
                    selection.current_round === 2 ? '2nd Pick List' :
                    selection.current_round === 3 ? '3rd Pick List' :
                    'Backup Picks'})
                </span>
              )}
            </h2>

            <TeamGrid
              teams={teamColumns}
              selectedTeam={selectedTeam}
              onTeamSelect={setSelectedTeam}
              selection={selection}
              picklist={picklist}
              getTeamNickname={getTeamNicknameWrapper}
              getTeamRank={getTeamRankWrapper}
            />
            
            <TeamActionPanel
              selectedTeam={selectedTeam}
              selectedAlliance={selectedAlliance}
              action={action}
              selection={selection}
              picklist={picklist}
              onActionSelect={setAction}
              onAllianceSelect={setSelectedAlliance}
              onConfirmAction={handleConfirmAction}
              getTeamNickname={getTeamNicknameWrapper}
              canBeCaptain={canBeCaptain}
              isTeamSelectable={isTeamSelectable}
            />
          </div>
        </div>
        
        {/* Right Column - Alliance Board */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-4">
            <AllianceBoard
              selection={selection}
              selectedAlliance={selectedAlliance}
              onAllianceSelect={setSelectedAlliance}
              onRemoveTeam={handleRemoveTeam}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AllianceSelection;