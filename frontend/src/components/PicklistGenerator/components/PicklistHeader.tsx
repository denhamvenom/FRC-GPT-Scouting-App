import React from "react";

interface BatchingToggleProps {
  useBatching: boolean;
  isLocked: boolean;
  onToggle: (value: boolean) => void;
}

const BatchingToggle: React.FC<BatchingToggleProps> = ({
  useBatching,
  isLocked,
  onToggle,
}) => {
  if (isLocked) return null;

  return (
    <label className="flex items-center space-x-2 text-sm">
      <input
        type="checkbox"
        checked={useBatching}
        onChange={(e) => {
          const newValue = e.target.checked;
          console.log(
            "Toggling useBatching from",
            useBatching,
            "to",
            newValue,
          );
          onToggle(newValue);
          console.log(
            "useBatching will be saved to localStorage as:",
            newValue,
          );
        }}
        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
      />
      <span>
        Use batch processing (recommended for large datasets)
      </span>
    </label>
  );
};

interface ActionButtonsProps {
  isEditing: boolean;
  isLoading: boolean;
  isLocked: boolean;
  showAnalysis: boolean;
  picklistLength: number;
  onEditClick: () => void;
  onSaveClick: () => void;
  onCancelEdit: () => void;
  onToggleAnalysis: () => void;
  onGenerate: () => void;
  onClear: () => void;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  isEditing,
  isLoading,
  isLocked,
  showAnalysis,
  picklistLength,
  onEditClick,
  onSaveClick,
  onCancelEdit,
  onToggleAnalysis,
  onGenerate,
  onClear,
}) => {
  if (isEditing) {
    return (
      <>
        <button
          onClick={onSaveClick}
          disabled={isLoading}
          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
        >
          Save Changes
        </button>
        <button
          onClick={onCancelEdit}
          className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500"
        >
          Cancel
        </button>
      </>
    );
  }

  return (
    <>
      {!isLocked && (
        <button
          onClick={onEditClick}
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
          onClick={onGenerate}
          disabled={isLoading}
          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
        >
          {isLoading ? "Regenerating..." : "Regenerate Picklist"}
        </button>
      )}
      {!isLocked && picklistLength > 0 && (
        <button
          onClick={onClear}
          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Clear Picklist
        </button>
      )}
    </>
  );
};

interface PicklistHeaderProps {
  pickPosition: "first" | "second" | "third";
  isLocked: boolean;
  isEditing: boolean;
  isLoading: boolean;
  useBatching: boolean;
  showAnalysis: boolean;
  picklistLength: number;
  onToggleBatching: (value: boolean) => void;
  onEditClick: () => void;
  onSaveClick: () => void;
  onCancelEdit: () => void;
  onToggleAnalysis: () => void;
  onGenerate: () => void;
  onClear: () => void;
}

export const PicklistHeader: React.FC<PicklistHeaderProps> = ({
  pickPosition,
  isLocked,
  isEditing,
  isLoading,
  useBatching,
  showAnalysis,
  picklistLength,
  onToggleBatching,
  onEditClick,
  onSaveClick,
  onCancelEdit,
  onToggleAnalysis,
  onGenerate,
  onClear,
}) => {
  return (
    <div className="flex justify-between items-center mb-4">
      <h2 className="text-xl font-bold">
        {pickPosition.charAt(0).toUpperCase() + pickPosition.slice(1)} Pick
        Rankings
      </h2>
      <div className="flex items-center space-x-4">
        <BatchingToggle
          useBatching={useBatching}
          isLocked={isLocked}
          onToggle={onToggleBatching}
        />
        <div className="flex space-x-2">
          <ActionButtons
            isEditing={isEditing}
            isLoading={isLoading}
            isLocked={isLocked}
            showAnalysis={showAnalysis}
            picklistLength={picklistLength}
            onEditClick={onEditClick}
            onSaveClick={onSaveClick}
            onCancelEdit={onCancelEdit}
            onToggleAnalysis={onToggleAnalysis}
            onGenerate={onGenerate}
            onClear={onClear}
          />
        </div>
      </div>
    </div>
  );
};