// frontend/src/pages/Validation/Validation.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiContext } from '../../providers/ApiProvider';
import { useValidation } from './hooks/useValidation';
import { useCorrections } from './hooks/useCorrections';
import {
  ValidationResults,
  OutlierList,
  CorrectionPanel,
  TodoList,
  MissingDataList,
} from './components';
import { TeamMatch, ValidationIssue, TodoItem } from './types';

const Validation: React.FC = () => {
  // Get navigation hook
  const navigate = useNavigate();
  
  // Get API services from context
  const { apiClient } = useApiContext();
  
  const validationHook = useValidation();
  
  const {
    datasetPath,
    validationResult,
    loading,
    activeTab,
    selectedIssue,
    suggestions,
    corrections,
    correctionReason,
    error,
    successMessage,
    todoList,
    virtualScoutPreview,
    actionMode,
    ignoreReason,
    customReason,
    setActiveTab,
    setSelectedIssue,
    setSuggestions,
    setCorrections,
    setCorrectionReason,
    setError,
    setSuccessMessage,
    setTodoList,
    setActionMode,
    setIgnoreReason,
    setCustomReason,
    fetchValidationData,
    fetchTodoList,
    handleActionModeChange,
    submitCorrection,
    submitIgnoreMatch,
    submitVirtualScout,
  } = validationHook;

  const {
    fetchSuggestions,
  } = useCorrections();

  // Handle selecting an issue
  const handleSelectIssue = async (issue: TeamMatch | ValidationIssue) => {
    setSelectedIssue(issue);
    setActionMode('none');
    
    // Fetch suggestions for outliers
    if ('issues' in issue && datasetPath) {
      await fetchSuggestions(datasetPath, issue);
    }
  };

  // Handle canceling selection
  const handleCancel = () => {
    setSelectedIssue(null);
    setActionMode('none');
    setCorrections({});
    setCorrectionReason('');
    setSuggestions([]);
  };

  // Handle updating todo status
  const handleUpdateTodoStatus = async (item: TodoItem, status: 'completed' | 'cancelled') => {
    try {
      await apiClient.post('/validate/todo-update', {
        unified_dataset_path: datasetPath,
        team_number: item.team_number,
        match_number: item.match_number,
        status: status,
      });

      // Refresh the todo list
      await fetchTodoList(datasetPath);
      setSuccessMessage(`Todo item marked as ${status}`);
    } catch (err: any) {
      console.error('Error updating todo status:', err);
      setError(err.message || 'Error updating todo item');
    }
  };

  // Clear messages after a delay
  React.useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage, setSuccessMessage]);

  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 8000);
      return () => clearTimeout(timer);
    }
  }, [error, setError]);

  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Data Validation</h1>
              <p className="mt-2 text-gray-600">
                Review and correct data quality issues in your scouting dataset
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => navigate('/picklist')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Generate Picklist
                <svg className="ml-2 -mr-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Error and Success Messages */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-red-500">⚠️</span>
              </div>
              <div className="ml-3">
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-green-500">✅</span>
              </div>
              <div className="ml-3">
                <p className="text-sm">{successMessage}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content - Validation Results and Lists */}
          <div className="lg:col-span-2 space-y-6">
            <ValidationResults
              validationResult={validationResult}
              loading={loading}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            {validationResult && (
              <div className="bg-white shadow rounded-lg p-6">
                {activeTab === 'missing' && (
                  <MissingDataList
                    missingMatches={validationResult.missing_scouting}
                    missingSuperscouting={validationResult.missing_superscouting}
                    onSelectMissing={handleSelectIssue}
                    selectedIssue={selectedIssue}
                  />
                )}

                {activeTab === 'outliers' && (
                  <OutlierList
                    outliers={validationResult.outliers}
                    onSelectIssue={handleSelectIssue}
                    selectedIssue={selectedIssue}
                  />
                )}

                {activeTab === 'todo' && (
                  <TodoList
                    todoList={todoList}
                    onUpdateStatus={handleUpdateTodoStatus}
                  />
                )}
              </div>
            )}
          </div>

          {/* Sidebar - Correction Panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <CorrectionPanel
                selectedIssue={selectedIssue}
                actionMode={actionMode}
                ignoreReason={ignoreReason}
                customReason={customReason}
                corrections={corrections}
                correctionReason={correctionReason}
                suggestions={suggestions}
                virtualScoutPreview={virtualScoutPreview}
                loading={loading}
                onActionModeChange={handleActionModeChange}
                onIgnoreReasonChange={setIgnoreReason}
                onCustomReasonChange={setCustomReason}
                onCorrectionChange={(metric, value) => {
                  setCorrections(prev => ({ ...prev, [metric]: value }));
                }}
                onCorrectionReasonChange={setCorrectionReason}
                onSubmitCorrection={submitCorrection}
                onSubmitIgnoreMatch={submitIgnoreMatch}
                onSubmitVirtualScout={submitVirtualScout}
                onCancel={handleCancel}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Validation;