import React from "react";
import TeamComparisonModal from "./TeamComparisonModal";
import { PicklistGeneratorProps } from "./PicklistGenerator/types";
import { usePicklistState } from "./PicklistGenerator/hooks/usePicklistState";
import { usePicklistPagination } from "./PicklistGenerator/hooks/usePicklistPagination";
import { usePicklistGeneration } from "./PicklistGenerator/hooks/usePicklistGeneration";

import { ProgressIndicator, BatchProgressIndicator, LoadingSpinner } from "./PicklistGenerator/components/PicklistProgressIndicators";
import { MissingTeamsModal } from "./PicklistGenerator/components/PicklistModals";
import { PicklistHeader } from "./PicklistGenerator/components/PicklistHeader";
import { PicklistMessageBanners } from "./PicklistGenerator/components/PicklistMessageBanners";
import { PicklistAnalysisPanel } from "./PicklistGenerator/components/PicklistAnalysisPanel";
import { PicklistPagination } from "./PicklistGenerator/components/PicklistPagination";
import { PicklistComparisonControls } from "./PicklistGenerator/components/PicklistComparisonControls";
import { TeamListDisplay } from "./PicklistGenerator/components/TeamListDisplay";

const PicklistGenerator: React.FC<PicklistGeneratorProps> = (props) => {
  const {
    datasetPath,
    yourTeamNumber,
    allPriorities,
    priorities,
    isLocked = false,
  } = props;

  const picklistState = usePicklistState(props);
  const pagination = usePicklistPagination(picklistState.picklist);
  
  const generation = usePicklistGeneration(props, picklistState, {
    setCurrentPage: pagination.setCurrentPage,
    setTotalPages: (pages: number) => {}, // This is handled internally in pagination hook
    teamsPerPage: pagination.teamsPerPage,
  });

  const {
    picklist,
    analysis,
    isLoading,
    estimatedTime,
    error,
    isEditing,
    showAnalysis,
    successMessage,
    selectedTeams,
    showComparison,
    missingTeamNumbers,
    showMissingTeamsModal,
    isRankingMissingTeams,
    useBatching,
    setIsEditing,
    setShowAnalysis,
    setShowComparison,
    setUseBatching,
  } = picklistState;

  const {
    currentPage,
    teamsPerPage,
    totalPages,
    setCurrentPage,
    setTeamsPerPage,
  } = pagination;

  const {
    batchProcessing,
    shouldShowProgress,
    clearPicklist,
    generatePicklist,
    updatePicklist,
    rankMissingTeams,
    handleSkipMissingTeams,
    handlePositionChange,
    toggleTeamSelection,
    applyComparison,
  } = generation;

  const {
    batchProcessingActive,
    batchProcessingInfo,
    elapsedTime,
  } = batchProcessing;

  // Decide which loading/progress indicator to show
  if (shouldShowProgress) {
    if (batchProcessingActive && batchProcessingInfo) {
      return (
        <BatchProgressIndicator
          batchInfo={batchProcessingInfo}
          elapsedTime={elapsedTime}
        />
      );
    }

    if (estimatedTime > 0) {
      return (
        <ProgressIndicator
          estimatedTime={estimatedTime}
          teamCount={datasetPath ? 75 : 0}
        />
      );
    }

    return <LoadingSpinner />;
  }

  // Don't show the picklist if batch processing is active
  if (batchProcessingActive) {
    return null;
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow-md p-6">
        {showMissingTeamsModal && (
          <MissingTeamsModal
            missingTeamCount={missingTeamNumbers.length}
            onRankMissingTeams={rankMissingTeams}
            onSkip={handleSkipMissingTeams}
            isLoading={isRankingMissingTeams}
          />
        )}
        
        <PicklistHeader
          pickPosition={props.pickPosition}
          isLocked={isLocked}
          isEditing={isEditing}
          isLoading={isLoading}
          useBatching={useBatching}
          showAnalysis={showAnalysis}
          picklistLength={picklist.length}
          onToggleBatching={setUseBatching}
          onEditClick={() => setIsEditing(true)}
          onSaveClick={() => {
            updatePicklist();
            setIsEditing(false);
          }}
          onCancelEdit={() => setIsEditing(false)}
          onToggleAnalysis={() => setShowAnalysis(!showAnalysis)}
          onGenerate={generatePicklist}
          onClear={clearPicklist}
        />

        <PicklistMessageBanners
          error={error}
          successMessage={successMessage}
        />

        <PicklistAnalysisPanel
          analysis={analysis}
          showAnalysis={showAnalysis}
        />

        <PicklistPagination
          position="top"
          currentPage={currentPage}
          totalPages={totalPages}
          teamsPerPage={teamsPerPage}
          totalTeams={picklist.length}
          onPageChange={setCurrentPage}
          onTeamsPerPageChange={setTeamsPerPage}
        />

        <PicklistComparisonControls
          selectedTeams={selectedTeams}
          onCompare={() => setShowComparison(true)}
        />

        <TeamListDisplay
          teams={picklist}
          currentPage={currentPage}
          teamsPerPage={teamsPerPage}
          isEditing={isEditing}
          isLocked={isLocked}
          selectedTeams={selectedTeams}
          onPositionChange={handlePositionChange}
          onTeamSelect={toggleTeamSelection}
          onExcludeTeam={props.onExcludeTeam}
        />

        <PicklistPagination
          position="bottom"
          currentPage={currentPage}
          totalPages={totalPages}
          teamsPerPage={teamsPerPage}
          totalTeams={picklist.length}
          onPageChange={setCurrentPage}
          onTeamsPerPageChange={setTeamsPerPage}
        />
      </div>
      
      <TeamComparisonModal
        isOpen={showComparison}
        onClose={() => setShowComparison(false)}
        teamNumbers={selectedTeams}
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