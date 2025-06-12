// frontend/src/pages/FieldSelection/FieldSelection.tsx

import React from 'react';
import { useFieldSelection } from './hooks/useFieldSelection';
import { 
  FieldList, 
  FieldPreview, 
  StatboticsPanel, 
  SelectionActions 
} from './components';
import { DATA_CATEGORIES } from './types';
import CategoryTabs from '../../components/CategoryTabs';

const FieldSelection: React.FC = () => {
  const {
    // State
    scoutingHeaders,
    superscoutingHeaders,
    pitScoutingHeaders,
    selectedFields,
    criticalFieldMappings,
    activeCategory,
    isLoading,
    error,
    successMessage,
    validationWarning,
    year,
    statboticsFields,
    selectedStatboticsFields,
    enableStatbotics,

    // Actions
    setSelectedFields,
    setCriticalFieldMappings,
    setActiveCategory,
    setError,
    setSuccessMessage,
    setValidationWarning,
    setSelectedStatboticsFields,
    setEnableStatbotics,
    saveFieldSelections,
    saveFieldSelectionsAndBuildDataset,
    autoCategorizeFields,
    validateSelections,
  } = useFieldSelection();

  // Handle field category change
  const handleFieldCategoryChange = (field: string, category: string) => {
    setSelectedFields(prev => ({
      ...prev,
      [field]: category
    }));
  };

  // Handle critical field toggle
  const handleCriticalFieldToggle = (field: string, criticalType: 'team_number' | 'match_number') => {
    setCriticalFieldMappings(prev => {
      // Ensure prev has the correct structure
      const safeState = {
        team_number: prev?.team_number || [],
        match_number: prev?.match_number || []
      };
      
      const currentFields = safeState[criticalType];
      const isSelected = currentFields.includes(field);
      
      if (isSelected) {
        return {
          ...safeState,
          [criticalType]: currentFields.filter(f => f !== field)
        };
      } else {
        return {
          ...safeState,
          [criticalType]: [...currentFields, field]
        };
      }
    });
  };

  // Check if we have valid selections
  const hasValidSelections = React.useMemo(() => {
    if (!criticalFieldMappings || !criticalFieldMappings.team_number || !criticalFieldMappings.match_number) {
      return false;
    }
    return criticalFieldMappings.team_number.length > 0 && 
           criticalFieldMappings.match_number.length > 0;
  }, [criticalFieldMappings]);

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

  React.useEffect(() => {
    if (validationWarning) {
      const timer = setTimeout(() => setValidationWarning(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [validationWarning, setValidationWarning]);

  // Get current headers based on active category
  const getCurrentHeaders = () => {
    switch (activeCategory) {
      case 'match': return scoutingHeaders;
      case 'pit': return pitScoutingHeaders;
      case 'super': return superscoutingHeaders;
      default: return [];
    }
  };

  const getCurrentSheetType = (): 'match' | 'pit' | 'super' => {
    switch (activeCategory) {
      case 'pit': return 'pit';
      case 'super': return 'super';
      default: return 'match';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Field Selection</h1>
          <p className="mt-2 text-gray-600">
            Categorize your scouting fields and configure Statbotics integration for Year {year}
          </p>
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

        {validationWarning && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-yellow-500">⚠️</span>
              </div>
              <div className="ml-3">
                <p className="text-sm">{validationWarning}</p>
              </div>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="mb-6 flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            <span>Loading sheet headers...</span>
          </div>
        )}

        <div className="space-y-8">
          {/* Category Tabs */}
          <CategoryTabs
            categories={DATA_CATEGORIES}
            activeCategory={activeCategory}
            onCategoryChange={setActiveCategory}
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column - Field Lists and Statbotics */}
            <div className="space-y-8">
              {/* Field List */}
              {activeCategory !== 'critical' && (
                <div className="bg-white shadow rounded-lg p-6">
                  <FieldList
                    headers={getCurrentHeaders()}
                    selectedFields={selectedFields}
                    criticalFieldMappings={criticalFieldMappings}
                    onFieldCategoryChange={handleFieldCategoryChange}
                    onCriticalFieldToggle={handleCriticalFieldToggle}
                    sheetType={getCurrentSheetType()}
                  />
                </div>
              )}

              {/* Statbotics Panel */}
              {activeCategory === 'critical' && (
                <StatboticsPanel
                  statboticsFields={statboticsFields}
                  selectedStatboticsFields={selectedStatboticsFields}
                  enableStatbotics={enableStatbotics}
                  onSelectionChange={setSelectedStatboticsFields}
                  onEnableChange={setEnableStatbotics}
                />
              )}
            </div>

            {/* Right Column - Preview */}
            <div>
              <div className="sticky top-8">
                <FieldPreview
                  scoutingHeaders={scoutingHeaders}
                  superscoutingHeaders={superscoutingHeaders}
                  pitScoutingHeaders={pitScoutingHeaders}
                  selectedFields={selectedFields}
                  criticalFieldMappings={criticalFieldMappings}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <SelectionActions
            isLoading={isLoading}
            hasValidSelections={hasValidSelections}
            onSave={saveFieldSelections}
            onSaveAndContinue={saveFieldSelectionsAndBuildDataset}
            onAutoCategorize={autoCategorizeFields}
            onValidate={validateSelections}
          />
        </div>
      </div>

      {/* Bottom padding to account for fixed action bar */}
      <div className="h-32"></div>
    </div>
  );
};

export default FieldSelection;