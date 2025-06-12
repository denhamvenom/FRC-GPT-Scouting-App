// frontend/src/pages/PicklistNew/components/PicklistGenerator.tsx

import React, { useEffect } from "react";
import TeamComparisonModal from "../../../components/TeamComparisonModal";
import { usePicklistGeneration } from "../hooks/usePicklistGeneration";
import { usePicklistState } from "../hooks/usePicklistState";
import { usePagination } from "../hooks/usePagination";
import { ProgressIndicator, BatchProgressIndicator } from "./ProgressIndicator";
import { MissingTeamsModal } from "./MissingTeamsModal";
import { PicklistActions } from "./PicklistActions";
import { AnalysisDisplay } from "./AnalysisDisplay";
import { Pagination } from "./Pagination";
import { PicklistDisplay } from "./PicklistDisplay";
import { PicklistGeneratorProps, Team } from "../types";

const PicklistGenerator: React.FC<PicklistGeneratorProps> = ({
  datasetPath,
  yourTeamNumber,
  pickPosition,
  priorities,
  allPriorities,
  excludeTeams = [],
  onPicklistGenerated,
  initialPicklist = [],
  onExcludeTeam,
  isLocked = false,
  onPicklistCleared,
  useBatching = false,
}) => {
  // Custom hooks for state management
  const picklistGeneration = usePicklistGeneration({
    datasetPath,
    yourTeamNumber,
    pickPosition,
    priorities,
    excludeTeams,
    useBatching,
    onPicklistGenerated,
    onPicklistCleared,
    initialPicklist,
  });

  const picklistState = usePicklistState();
  const pagination = usePagination(10);

  // Update pagination when picklist changes
  useEffect(() => {
    pagination.actions.updateTotalPages(picklistGeneration.state.picklist.length);
    pagination.actions.resetToFirstPage();
  }, [picklistGeneration.state.picklist.length]); // Remove pagination.actions from dependencies

  // Handle team position change in edit mode
  const handlePositionChange = (teamIndex: number, newPosition: number) => {
    if (newPosition < 1 || newPosition > picklistGeneration.state.picklist.length) {
      return;
    }

    const newIndex = newPosition - 1;
    const newPicklist = [...picklistGeneration.state.picklist];
    const [teamToMove] = newPicklist.splice(teamIndex, 1);
    newPicklist.splice(newIndex, 0, teamToMove);

    // This would need to be handled by the hook, but for now we'll log it
    console.log("Position change requested:", { teamIndex, newPosition, newPicklist });
  };

  // Handle team comparison results
  const applyComparison = (teams: Team[]) => {
    const indices = picklistState.state.selectedTeams
      .map((num) => picklistGeneration.state.picklist.findIndex((t) => t.team_number === num))
      .filter((i) => i !== -1)
      .sort((a, b) => a - b);
    
    const newList = [...picklistGeneration.state.picklist];
    teams.forEach((team, idx) => {
      const targetIndex = indices[idx];
      if (targetIndex !== undefined) {
        newList[targetIndex] = team;
      }
    });
    
    // This would need to be handled by the hook
    console.log("Comparison applied:", { teams, newList });
    picklistState.actions.clearSelection();
  };

  // Show loading/progress indicators
  if ((picklistGeneration.state.isLoading && !picklistGeneration.state.picklist.length) || 
      picklistGeneration.batchState.batchProcessingActive) {
    
    if (picklistGeneration.batchState.batchProcessingActive && picklistGeneration.batchState.batchProcessingInfo) {
      return (
        <BatchProgressIndicator
          batchInfo={picklistGeneration.batchState.batchProcessingInfo}
          elapsedTime={picklistGeneration.batchState.elapsedTime}
        />
      );
    }

    if (picklistGeneration.state.estimatedTime > 0) {
      return (
        <ProgressIndicator
          estimatedTime={picklistGeneration.state.estimatedTime}
          teamCount={datasetPath ? 75 : 0}
        />
      );
    }

    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-blue-600">Generating picklist...</span>
      </div>
    );
  }

  // Don't show content if batch processing is active
  if (picklistGeneration.batchState.batchProcessingActive) {
    return null;
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow-md p-6">
        {/* Missing Teams Modal */}
        {picklistGeneration.state.showMissingTeamsModal && (
          <MissingTeamsModal
            missingTeamCount={picklistGeneration.state.missingTeamNumbers.length}
            onRankMissingTeams={picklistGeneration.actions.rankMissingTeams}
            onSkip={picklistGeneration.actions.handleSkipMissingTeams}
            isLoading={picklistGeneration.state.isRankingMissingTeams}
          />
        )}

        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">
            {pickPosition.charAt(0).toUpperCase() + pickPosition.slice(1)} Pick Rankings
          </h2>
          <div className="flex items-center space-x-4">
            <PicklistActions
              isEditing={picklistState.state.isEditing}
              isLoading={picklistGeneration.state.isLoading}
              isLocked={isLocked}
              showAnalysis={picklistState.state.showAnalysis}
              hasPicklist={picklistGeneration.state.picklist.length > 0}
              onEdit={() => picklistState.actions.setIsEditing(true)}
              onSave={picklistGeneration.actions.updatePicklist}
              onCancel={() => picklistState.actions.setIsEditing(false)}
              onToggleAnalysis={() => picklistState.actions.setShowAnalysis(!picklistState.state.showAnalysis)}
              onRegenerate={picklistGeneration.actions.generatePicklist}
              onClear={picklistGeneration.actions.clearPicklist}
            />
          </div>
        </div>

        {/* Error and Success Messages */}
        {picklistGeneration.state.error && (
          <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
            {picklistGeneration.state.error}
          </div>
        )}

        {picklistGeneration.state.successMessage && (
          <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
            {picklistGeneration.state.successMessage}
          </div>
        )}

        {/* Analysis Display */}
        <AnalysisDisplay
          analysis={picklistGeneration.state.analysis}
          isVisible={picklistState.state.showAnalysis}
        />

        {/* Pagination Controls */}
        <Pagination
          currentPage={pagination.state.currentPage}
          totalPages={pagination.state.totalPages}
          teamsPerPage={pagination.state.teamsPerPage}
          totalTeams={picklistGeneration.state.picklist.length}
          onPageChange={pagination.actions.setCurrentPage}
          onTeamsPerPageChange={pagination.actions.setTeamsPerPage}
        />

        {/* Team Comparison Button */}
        {picklistState.state.selectedTeams.length > 1 && (
          <div className="my-2">
            <button
              onClick={() => picklistState.actions.setShowComparison(true)}
              className="px-3 py-1 bg-blue-600 text-white rounded"
            >
              Compare & Re-Rank
            </button>
          </div>
        )}

        {/* Picklist Display */}
        <div className="overflow-hidden">
          <PicklistDisplay
            picklist={picklistGeneration.state.picklist}
            currentPage={pagination.state.currentPage}
            teamsPerPage={pagination.state.teamsPerPage}
            totalPages={pagination.state.totalPages}
            isEditing={picklistState.state.isEditing}
            isLocked={isLocked}
            selectedTeams={picklistState.state.selectedTeams}
            onPositionChange={handlePositionChange}
            onToggleTeamSelection={picklistState.actions.toggleTeamSelection}
            onExcludeTeam={onExcludeTeam}
          />
        </div>
      </div>

      {/* Team Comparison Modal */}
      <TeamComparisonModal
        isOpen={picklistState.state.showComparison}
        onClose={() => picklistState.actions.setShowComparison(false)}
        teamNumbers={picklistState.state.selectedTeams}
        datasetPath={datasetPath}
        yourTeamNumber={yourTeamNumber}
        prioritiesMap={
          allPriorities || {
            first: priorities,
            second: priorities,
            third: priorities,
          }
        }
        onApply={applyComparison}
      />
    </>
  );
};

export default PicklistGenerator;