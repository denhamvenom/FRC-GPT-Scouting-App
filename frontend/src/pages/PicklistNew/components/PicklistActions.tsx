// frontend/src/pages/PicklistNew/components/PicklistActions.tsx

import React from "react";
import { PicklistActionsProps } from "../types";

export const PicklistActions: React.FC<PicklistActionsProps> = ({
  isEditing,
  isLoading,
  isLocked,
  showAnalysis,
  hasPicklist,
  onEdit,
  onSave,
  onCancel,
  onToggleAnalysis,
  onRegenerate,
  onClear,
}) => {
  if (isEditing) {
    return (
      <div className="flex space-x-2">
        <button
          onClick={onSave}
          disabled={isLoading}
          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
        >
          Save Changes
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <div className="flex space-x-2">
      {!isLocked && (
        <button
          onClick={onEdit}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Edit Rankings
        </button>
      )}
      
      <button
        onClick={onToggleAnalysis}
        className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
      >
        {showAnalysis ? "Hide Analysis" : "Show Analysis"}
      </button>
      
      {!isLocked && (
        <button
          onClick={onRegenerate}
          disabled={isLoading}
          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
        >
          {isLoading ? "Regenerating..." : "Regenerate Picklist"}
        </button>
      )}
      
      {!isLocked && hasPicklist && (
        <button
          onClick={onClear}
          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Clear Picklist
        </button>
      )}
    </div>
  );
};