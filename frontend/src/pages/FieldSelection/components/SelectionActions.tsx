// frontend/src/pages/FieldSelection/components/SelectionActions.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';

interface SelectionActionsProps {
  isLoading: boolean;
  hasValidSelections: boolean;
  onSave: () => void;
  onSaveAndContinue: () => Promise<boolean>;
  onAutoCategorize: () => void;
  onValidate: () => boolean;
}

export const SelectionActions: React.FC<SelectionActionsProps> = ({
  isLoading,
  hasValidSelections,
  onSave,
  onSaveAndContinue,
  onAutoCategorize,
  onValidate,
}) => {
  const navigate = useNavigate();

  const handleSaveAndContinue = async () => {
    if (onValidate()) {
      const success = await onSaveAndContinue();
      if (success) {
        // Navigate to validation after successful save and dataset build
        navigate('/validation');
      }
    }
  };

  return (
    <div className="bg-white border-t border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex space-x-3">
          <button
            onClick={onAutoCategorize}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            🤖 Auto-Categorize
          </button>
          
          <button
            onClick={() => onValidate()}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            ✅ Validate
          </button>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={() => navigate('/schema-mapping')}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          >
            ← Back
          </button>
          
          <button
            onClick={onSave}
            disabled={isLoading || !hasValidSelections}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : 'Save'}
          </button>
          
          <button
            onClick={handleSaveAndContinue}
            disabled={isLoading || !hasValidSelections}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : 'Save & Continue →'}
          </button>
        </div>
      </div>

      {/* Help Text */}
      <div className="mt-4 text-sm text-gray-600">
        <div className="flex items-start space-x-2">
          <span className="text-blue-500">💡</span>
          <div>
            <div className="font-medium">Tips:</div>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Use "Auto-Categorize" to automatically categorize fields based on their names</li>
              <li>Ensure at least one team number and match number field are selected</li>
              <li>Review the preview to verify your field categorizations</li>
              <li>Enable Statbotics integration for advanced EPA metrics</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};