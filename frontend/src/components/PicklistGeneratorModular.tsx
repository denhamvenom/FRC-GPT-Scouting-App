// frontend/src/components/PicklistGeneratorModular.tsx
// Backward compatibility wrapper for the refactored PicklistGenerator

import { default as ModularPicklistGenerator } from '../pages/PicklistNew/components/PicklistGenerator';

// Re-export the modular component with the same interface
export default ModularPicklistGenerator;

// Also export types for backward compatibility
export type {
  Team,
  MetricPriority,
  PicklistAnalysis,
  BatchProcessing,
  Performance,
  PicklistResult,
  MissingTeamsResult,
  PicklistGeneratorProps,
  AllPriorities,
  PickPosition
} from '../pages/PicklistNew/types';