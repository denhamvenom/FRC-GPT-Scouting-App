// frontend/src/pages/FieldSelection/components/FieldList.tsx

import React from 'react';
import { FieldMapping, CriticalFieldMappings, FIELD_CATEGORIES } from '../types';
import { formatFieldName, getCategoryColor } from '../utils';

interface FieldListProps {
  headers: string[];
  selectedFields: FieldMapping;
  criticalFieldMappings: CriticalFieldMappings;
  onFieldCategoryChange: (field: string, category: string) => void;
  onCriticalFieldToggle: (field: string, criticalType: 'team_number' | 'match_number') => void;
  sheetType: 'match' | 'pit' | 'super';
}

export const FieldList: React.FC<FieldListProps> = ({
  headers,
  selectedFields,
  criticalFieldMappings,
  onFieldCategoryChange,
  onCriticalFieldToggle,
  sheetType,
}) => {
  if (headers.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">📋</div>
        <div className="text-lg font-medium">No headers found</div>
        <div>No headers were found for this sheet type.</div>
      </div>
    );
  }

  const getSheetTypeLabel = () => {
    switch (sheetType) {
      case 'match': return 'Match Scouting';
      case 'pit': return 'Pit Scouting';
      case 'super': return 'Super Scouting';
      default: return 'Unknown';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          {getSheetTypeLabel()} Fields ({headers.length})
        </h3>
        
        <div className="text-sm text-gray-500">
          Categorized: {Object.keys(selectedFields).filter(h => headers.includes(h) && selectedFields[h] !== 'other').length} / {headers.length}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {headers.map((header, index) => (
          <div
            key={`${header}-${index}`}
            className="border border-gray-200 rounded-lg p-4 bg-white"
          >
            <div className="mb-3">
              <div className="font-medium text-gray-900 text-sm mb-1">
                {formatFieldName(header)}
              </div>
              <div className="text-xs text-gray-500 font-mono">
                {header}
              </div>
            </div>

            {/* Category Selection */}
            <div className="mb-3">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={selectedFields[header] || 'other'}
                onChange={(e) => onFieldCategoryChange(header, e.target.value)}
                className="block w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {FIELD_CATEGORIES.map(category => (
                  <option key={category.key} value={category.key}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Current Category Badge */}
            {selectedFields[header] && (
              <div className="mb-3">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(selectedFields[header])}`}>
                  {FIELD_CATEGORIES.find(c => c.key === selectedFields[header])?.label || selectedFields[header]}
                </span>
              </div>
            )}

            {/* Critical Field Checkboxes */}
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={criticalFieldMappings?.team_number?.includes(header) || false}
                  onChange={() => onCriticalFieldToggle(header, 'team_number')}
                  className="mr-2 h-3 w-3 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-xs text-gray-700">Team Number Field</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={criticalFieldMappings?.match_number?.includes(header) || false}
                  onChange={() => onCriticalFieldToggle(header, 'match_number')}
                  className="mr-2 h-3 w-3 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-xs text-gray-700">Match Number Field</span>
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};