// frontend/src/pages/Validation/components/ValidationResults.tsx

import React from 'react';
import { ValidationResult, TabType } from '../types';

interface ValidationResultsProps {
  validationResult: ValidationResult | null;
  loading: boolean;
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export const ValidationResults: React.FC<ValidationResultsProps> = ({
  validationResult,
  loading,
  activeTab,
  onTabChange,
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading validation results...</span>
      </div>
    );
  }

  if (!validationResult) {
    return null;
  }

  const { summary } = validationResult;

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Data Validation Results</h2>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-600 text-sm font-medium">Missing Matches</div>
          <div className="text-2xl font-bold text-red-700">{summary.total_missing_matches}</div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="text-yellow-600 text-sm font-medium">Missing Super</div>
          <div className="text-2xl font-bold text-yellow-700">{summary.total_missing_superscouting}</div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="text-orange-600 text-sm font-medium">Outliers</div>
          <div className="text-2xl font-bold text-orange-700">{summary.total_outliers}</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-gray-600 text-sm font-medium">Ignored</div>
          <div className="text-2xl font-bold text-gray-700">{summary.total_ignored_matches}</div>
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        {summary.has_issues ? (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
            ⚠️ Issues Found
          </span>
        ) : (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            ✅ No Issues Found
          </span>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => onTabChange('missing')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'missing'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Missing Data ({summary.total_missing_matches + summary.total_missing_superscouting})
          </button>
          <button
            onClick={() => onTabChange('outliers')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'outliers'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Outliers ({summary.total_outliers})
          </button>
          <button
            onClick={() => onTabChange('todo')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'todo'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            To-Do List
          </button>
        </nav>
      </div>
    </div>
  );
};