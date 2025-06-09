/**
 * Alliance Selection Module Exports
 * 
 * This module provides a decomposed alliance selection interface with:
 * - Separation of concerns through custom hooks
 * - Focused, single-responsibility components  
 * - Comprehensive TypeScript typing
 * - Error boundaries and loading states
 * - Real-time updates via polling
 */

// Main component with error boundary
export { default as AllianceSelection } from './AllianceSelection';

// Individual components for reuse
export { default as TeamGrid } from './components/TeamGrid';
export { default as AllianceBoard } from './components/AllianceBoard';
export { default as TeamActionPanel } from './components/TeamActionPanel';
export { default as ProgressIndicator } from './components/ProgressIndicator';
export { default as TeamStatusIndicator } from './components/TeamStatusIndicator';
export { default as ErrorBoundary } from './components/ErrorBoundary';

// Custom hooks for business logic
export { useAllianceSelection } from './hooks/useAllianceSelection';
export { useTeamActions } from './hooks/useTeamActions';
export { useAllianceState } from './hooks/useAllianceState';
export { usePolling } from './hooks/usePolling';

// Types and utilities
export * from './types';
export * from './utils';