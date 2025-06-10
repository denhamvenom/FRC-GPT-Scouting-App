import React from 'react';

interface SetupActionsProps {
  currentStep: number;
  canProceedToNextStep: boolean;
  onPreviousStep: () => void;
  onNextStep: () => void;
}

export const SetupActions: React.FC<SetupActionsProps> = ({
  currentStep,
  canProceedToNextStep,
  onPreviousStep,
  onNextStep
}) => {
  return (
    <div className="mt-8 flex justify-between">
      <button
        onClick={onPreviousStep}
        disabled={currentStep === 1}
        className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
      >
        Previous
      </button>
      
      {currentStep < 4 && (
        <button
          onClick={onNextStep}
          disabled={!canProceedToNextStep}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
        >
          {currentStep === 3 ? "Review Setup" : "Next"}
        </button>
      )}
    </div>
  );
};