/**
 * Legacy Alliance Selection Component - Now wraps the refactored version
 * 
 * This file maintains compatibility with existing imports while delegating 
 * to the new decomposed AllianceSelection component with error boundary.
 */

import React from 'react';
import { AllianceSelection as RefactoredAllianceSelection, ErrorBoundary } from './AllianceSelection/index';

const AllianceSelection: React.FC = () => {
  return (
    <ErrorBoundary>
      <RefactoredAllianceSelection />
    </ErrorBoundary>
  );
};

export default AllianceSelection;