// frontend/src/pages/Validation/components/CorrectionPanel.tsx

import React from 'react';
import { TeamMatch, ValidationIssue, ActionMode, IgnoreReason, CorrectionSuggestion } from '../types';

interface CorrectionPanelProps {
  selectedIssue: TeamMatch | ValidationIssue | null;
  actionMode: ActionMode;
  ignoreReason: IgnoreReason;
  customReason: string;
  corrections: { [key: string]: number };
  correctionReason: string;
  suggestions: CorrectionSuggestion[];
  virtualScoutPreview: any;
  loading: boolean;
  onActionModeChange: (mode: ActionMode) => void;
  onIgnoreReasonChange: (reason: IgnoreReason) => void;
  onCustomReasonChange: (reason: string) => void;
  onCorrectionChange: (metric: string, value: number) => void;
  onCorrectionReasonChange: (reason: string) => void;
  onSubmitCorrection: () => void;
  onSubmitIgnoreMatch: () => void;
  onSubmitVirtualScout: () => void;
  onCancel: () => void;
}

export const CorrectionPanel: React.FC<CorrectionPanelProps> = ({
  selectedIssue,
  actionMode,
  ignoreReason,
  customReason,
  corrections,
  correctionReason,
  suggestions,
  virtualScoutPreview,
  loading,
  onActionModeChange,
  onIgnoreReasonChange,
  onCustomReasonChange,
  onCorrectionChange,
  onCorrectionReasonChange,
  onSubmitCorrection,
  onSubmitIgnoreMatch,
  onSubmitVirtualScout,
  onCancel,
}) => {
  if (!selectedIssue) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        <div className="text-lg font-medium">No Issue Selected</div>
        <div>Select an issue from the list to view correction options.</div>
      </div>
    );
  }

  const isOutlier = 'issues' in selectedIssue;

  return (
    <div className="bg-white border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">
          Correct Issue: Team {selectedIssue.team_number} - Match {selectedIssue.match_number}
        </h3>
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {/* Issue Details */}
      {isOutlier && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <div className="font-medium text-red-800 mb-2">Detected Issues:</div>
          {selectedIssue.issues.map((issue, index) => (
            <div key={index} className="text-sm text-red-700">
              <span className="font-medium">{issue.metric}:</span> {issue.value}
              {issue.z_score && (
                <span className="text-red-600 ml-2">(z-score: {issue.z_score.toFixed(2)})</span>
              )}
              <div className="text-xs text-red-600 ml-4">
                Detection: {issue.detection_method}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action Mode Selection */}
      <div className="mb-6">
        <div className="text-sm font-medium text-gray-700 mb-3">Choose an action:</div>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="radio"
              value="watch-video"
              checked={actionMode === 'watch-video'}
              onChange={(e) => onActionModeChange(e.target.value as ActionMode)}
              className="mr-2"
            />
            <span>Watch match video and scout manually</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="radio"
              value="virtual-scout"
              checked={actionMode === 'virtual-scout'}
              onChange={(e) => onActionModeChange(e.target.value as ActionMode)}
              className="mr-2"
            />
            <span>Generate virtual scout data using AI</span>
          </label>
          
          {isOutlier && (
            <label className="flex items-center">
              <input
                type="radio"
                value="correct-values"
                checked={actionMode === 'correct-values'}
                onChange={(e) => onActionModeChange('none')}
                className="mr-2"
              />
              <span>Manually correct outlier values</span>
            </label>
          )}
          
          <label className="flex items-center">
            <input
              type="radio"
              value="ignore-match"
              checked={actionMode === 'ignore-match'}
              onChange={(e) => onActionModeChange(e.target.value as ActionMode)}
              className="mr-2"
            />
            <span>Ignore this match (team not operational/present)</span>
          </label>
        </div>
      </div>

      {/* Action-Specific Content */}
      {actionMode === 'ignore-match' && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <div className="text-sm font-medium text-gray-700 mb-3">Reason for ignoring:</div>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                value="not_operational"
                checked={ignoreReason === 'not_operational'}
                onChange={(e) => onIgnoreReasonChange(e.target.value as IgnoreReason)}
                className="mr-2"
              />
              <span>Robot not operational</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="not_present"
                checked={ignoreReason === 'not_present'}
                onChange={(e) => onIgnoreReasonChange(e.target.value as IgnoreReason)}
                className="mr-2"
              />
              <span>Team not present</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="other"
                checked={ignoreReason === 'other'}
                onChange={(e) => onIgnoreReasonChange(e.target.value as IgnoreReason)}
                className="mr-2"
              />
              <span>Other reason</span>
            </label>
          </div>
          
          {ignoreReason === 'other' && (
            <div className="mt-3">
              <input
                type="text"
                value={customReason}
                onChange={(e) => onCustomReasonChange(e.target.value)}
                placeholder="Enter custom reason..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          )}
          
          <button
            onClick={onSubmitIgnoreMatch}
            disabled={loading || (ignoreReason === 'other' && !customReason.trim())}
            className="mt-4 w-full bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 disabled:opacity-50"
          >
            {loading ? 'Ignoring...' : 'Ignore Match'}
          </button>
        </div>
      )}

      {actionMode === 'virtual-scout' && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-2"></div>
              <span>Generating virtual scout data...</span>
            </div>
          ) : virtualScoutPreview ? (
            <div>
              <div className="text-sm font-medium text-gray-700 mb-3">Virtual Scout Preview:</div>
              <div className="bg-white p-3 rounded border text-sm">
                <pre className="whitespace-pre-wrap">{JSON.stringify(virtualScoutPreview, null, 2)}</pre>
              </div>
              <button
                onClick={onSubmitVirtualScout}
                className="mt-4 w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Accept Virtual Scout Data
              </button>
            </div>
          ) : (
            <div className="text-center py-4">
              <button
                onClick={() => onActionModeChange('virtual-scout')}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Generate Virtual Scout Data
              </button>
            </div>
          )}
        </div>
      )}

      {isOutlier && actionMode === 'none' && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded">
          <div className="text-sm font-medium text-gray-700 mb-3">Manual Corrections:</div>
          
          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="mb-4">
              <div className="text-xs font-medium text-gray-600 mb-2">Suggested corrections:</div>
              {suggestions.map((suggestion, index) => (
                <div key={index} className="text-xs text-gray-600 mb-1">
                  <span className="font-medium">{suggestion.metric}:</span>
                  {suggestion.suggested_corrections.map((correction, corrIndex) => (
                    <button
                      key={corrIndex}
                      onClick={() => onCorrectionChange(suggestion.metric, correction.value)}
                      className="ml-2 px-2 py-1 bg-white border border-gray-300 rounded text-xs hover:bg-gray-50"
                    >
                      {correction.value} ({correction.method})
                    </button>
                  ))}
                </div>
              ))}
            </div>
          )}
          
          {/* Manual Corrections */}
          <div className="space-y-3">
            {selectedIssue.issues.map((issue, index) => (
              <div key={index}>
                <label className="block text-xs font-medium text-gray-700">
                  {issue.metric} (current: {issue.value})
                </label>
                <input
                  type="number"
                  value={corrections[issue.metric] || ''}
                  onChange={(e) => onCorrectionChange(issue.metric, Number(e.target.value))}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Enter corrected value"
                />
              </div>
            ))}
          </div>
          
          <div className="mt-4">
            <label className="block text-xs font-medium text-gray-700">
              Reason for correction
            </label>
            <textarea
              value={correctionReason}
              onChange={(e) => onCorrectionReasonChange(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Explain why these corrections are needed..."
              rows={3}
            />
          </div>
          
          <button
            onClick={onSubmitCorrection}
            disabled={loading || Object.keys(corrections).length === 0 || !correctionReason.trim()}
            className="mt-4 w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit Corrections'}
          </button>
        </div>
      )}
    </div>
  );
};