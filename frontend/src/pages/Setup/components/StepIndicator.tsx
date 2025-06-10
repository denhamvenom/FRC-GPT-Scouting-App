import React from 'react';
import { SETUP_STEPS } from '../types';

interface StepIndicatorProps {
  currentStep: number;
  completedSteps: Set<number>;
  onStepClick: (step: number) => void;
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  completedSteps,
  onStepClick
}) => {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {SETUP_STEPS.map((step, index) => (
          <React.Fragment key={step.number}>
            <div
              className={`flex flex-col items-center cursor-pointer ${
                step.number === currentStep ? 'text-blue-600' : 
                completedSteps.has(step.number) ? 'text-green-600' : 'text-gray-400'
              }`}
              onClick={() => onStepClick(step.number)}
            >
              <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg border-2 ${
                step.number === currentStep ? 'bg-blue-600 text-white border-blue-600' :
                completedSteps.has(step.number) ? 'bg-green-600 text-white border-green-600' :
                'bg-white text-gray-400 border-gray-300'
              }`}>
                {completedSteps.has(step.number) ? '✓' : step.number}
              </div>
              <div className="mt-2 text-center">
                <div className="font-semibold">{step.title}</div>
                <div className="text-sm text-gray-500">{step.description}</div>
              </div>
            </div>
            {index < SETUP_STEPS.length - 1 && (
              <div className={`flex-1 h-1 mx-4 ${
                completedSteps.has(step.number) ? 'bg-green-600' : 'bg-gray-300'
              }`} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};