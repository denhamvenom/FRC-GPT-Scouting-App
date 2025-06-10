// frontend/src/pages/FieldSelection/components/StatboticsPanel.tsx

import React from 'react';
import { StatboticsField } from '../types';
import { useStatbotics } from '../hooks/useStatbotics';
import { formatFieldName, getDataTypeIcon } from '../utils';

interface StatboticsPanelProps {
  statboticsFields: StatboticsField[];
  selectedStatboticsFields: string[];
  enableStatbotics: boolean;
  onSelectionChange: (fields: string[]) => void;
  onEnableChange: (enabled: boolean) => void;
}

export const StatboticsPanel: React.FC<StatboticsPanelProps> = ({
  statboticsFields,
  selectedStatboticsFields,
  enableStatbotics,
  onSelectionChange,
  onEnableChange,
}) => {
  const {
    searchTerm,
    selectedCategory,
    categories,
    filteredFields,
    fieldCounts,
    allFilteredSelected,
    setSearchTerm,
    setSelectedCategory,
    toggleField,
    selectAllFiltered,
    deselectAllFiltered,
    clearAllSelections,
    selectRecommended,
  } = useStatbotics(statboticsFields, selectedStatboticsFields, onSelectionChange);

  return (
    <div className="bg-white border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Statbotics Integration</h3>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={enableStatbotics}
            onChange={(e) => onEnableChange(e.target.checked)}
            className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <span className="text-sm font-medium text-gray-700">Enable Statbotics</span>
        </label>
      </div>

      {!enableStatbotics ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">📊</div>
          <div className="text-lg font-medium">Statbotics Integration Disabled</div>
          <div>Enable Statbotics to include EPA and other advanced metrics in your analysis.</div>
        </div>
      ) : statboticsFields.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🔄</div>
          <div className="text-lg font-medium">Loading Statbotics Fields</div>
          <div>Fetching available fields from Statbotics...</div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Controls */}
          <div className="flex flex-wrap gap-4 items-center">
            {/* Search */}
            <div className="flex-1 min-w-64">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search fields..."
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* Category Filter */}
            <div>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="block w-48 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : formatFieldName(category)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={selectRecommended}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Select Recommended
            </button>
            
            {filteredFields.length > 0 && (
              <>
                {allFilteredSelected ? (
                  <button
                    onClick={deselectAllFiltered}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Deselect All Filtered
                  </button>
                ) : (
                  <button
                    onClick={selectAllFiltered}
                    className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Select All Filtered
                  </button>
                )}
              </>
            )}
            
            {fieldCounts.selected > 0 && (
              <button
                onClick={clearAllSelections}
                className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Clear All ({fieldCounts.selected})
              </button>
            )}
          </div>

          {/* Field Counts */}
          <div className="text-sm text-gray-600">
            Showing {fieldCounts.filtered} of {fieldCounts.total} fields 
            ({fieldCounts.selectedFiltered} selected)
          </div>

          {/* Fields List */}
          <div className="max-h-96 overflow-y-auto space-y-2">
            {filteredFields.map((field) => {
              const isSelected = selectedStatboticsFields.includes(field.field_name);
              
              return (
                <div
                  key={field.field_name}
                  onClick={() => toggleField(field.field_name)}
                  className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleField(field.field_name)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div>
                        <div className="font-medium text-sm">
                          {formatFieldName(field.field_name)}
                        </div>
                        <div className="text-xs text-gray-500 font-mono">
                          {field.field_name}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getDataTypeIcon(field.data_type)}</span>
                      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                        {formatFieldName(field.category)}
                      </span>
                    </div>
                  </div>
                  
                  {field.description && (
                    <div className="mt-2 text-xs text-gray-600">
                      {field.description}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {filteredFields.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <div className="text-lg font-medium">No fields match your criteria</div>
              <div>Try adjusting your search or category filter.</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};