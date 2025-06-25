import React from "react";

interface PicklistComparisonControlsProps {
  selectedTeams: number[];
  onCompare: () => void;
}

export const PicklistComparisonControls: React.FC<PicklistComparisonControlsProps> = ({
  selectedTeams,
  onCompare,
}) => {
  if (selectedTeams.length <= 1) return null;

  return (
    <div className="my-2">
      <button
        onClick={onCompare}
        className="px-3 py-1 bg-blue-600 text-white rounded"
      >
        Compare & Re-Rank
      </button>
    </div>
  );
};