// frontend/src/pages/FieldSelection/components/FieldPreview.tsx

import React from 'react';
import { FieldMapping, CriticalFieldMappings, FIELD_CATEGORIES } from '../types';
import { groupFieldsByCategory, getCategoryColor } from '../utils';

interface FieldPreviewProps {
  scoutingHeaders: string[];
  superscoutingHeaders: string[];
  pitScoutingHeaders: string[];
  selectedFields: FieldMapping;
  criticalFieldMappings: CriticalFieldMappings;
}

export const FieldPreview: React.FC<FieldPreviewProps> = ({
  scoutingHeaders,
  superscoutingHeaders,
  pitScoutingHeaders,
  selectedFields,
  criticalFieldMappings,
}) => {
  const allHeaders = [
    ...scoutingHeaders,
    ...superscoutingHeaders,
    ...pitScoutingHeaders
  ];

  const groupedFields = groupFieldsByCategory(allHeaders, selectedFields);

  const getCategoryCount = (category: string) => {
    return groupedFields[category]?.length || 0;
  };

  const getTotalCategorized = () => {
    return Object.values(selectedFields).filter(cat => cat !== 'other').length;
  };

  if (allHeaders.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        <div className="text-lg font-medium">No fields to preview</div>
        <div>Load sheet headers to see field categorization preview.</div>
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Field Categorization Preview</h3>
      
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="text-blue-600 text-sm font-medium">Total Fields</div>
          <div className="text-2xl font-bold text-blue-700">{allHeaders.length}</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="text-green-600 text-sm font-medium">Categorized</div>
          <div className="text-2xl font-bold text-green-700">{getTotalCategorized()}</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
          <div className="text-purple-600 text-sm font-medium">Team Fields</div>
          <div className="text-2xl font-bold text-purple-700">{criticalFieldMappings?.team_number?.length || 0}</div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
          <div className="text-orange-600 text-sm font-medium">Match Fields</div>
          <div className="text-2xl font-bold text-orange-700">{criticalFieldMappings?.match_number?.length || 0}</div>
        </div>
      </div>

      {/* Critical Fields Section */}
      <div className="mb-6">
        <h4 className="text-md font-medium mb-3 text-gray-800">Critical Field Mappings</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-purple-200 rounded-lg p-3 bg-purple-50">
            <div className="text-sm font-medium text-purple-800 mb-2">
              Team Number Fields ({criticalFieldMappings?.team_number?.length || 0})
            </div>
            {criticalFieldMappings?.team_number?.length > 0 ? (
              <div className="space-y-1">
                {criticalFieldMappings.team_number.map((field, index) => (
                  <div key={index} className="text-xs text-purple-700 font-mono bg-white px-2 py-1 rounded">
                    {field}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-purple-600 italic">No team number fields selected</div>
            )}
          </div>
          
          <div className="border border-orange-200 rounded-lg p-3 bg-orange-50">
            <div className="text-sm font-medium text-orange-800 mb-2">
              Match Number Fields ({criticalFieldMappings?.match_number?.length || 0})
            </div>
            {criticalFieldMappings?.match_number?.length > 0 ? (
              <div className="space-y-1">
                {criticalFieldMappings.match_number.map((field, index) => (
                  <div key={index} className="text-xs text-orange-700 font-mono bg-white px-2 py-1 rounded">
                    {field}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-orange-600 italic">No match number fields selected</div>
            )}
          </div>
        </div>
      </div>

      {/* Categories Section */}
      <div>
        <h4 className="text-md font-medium mb-3 text-gray-800">Fields by Category</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FIELD_CATEGORIES.map(category => {
            const count = getCategoryCount(category.key);
            const fields = groupedFields[category.key] || [];
            
            return (
              <div key={category.key} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(category.key)}`}>
                    {category.label}
                  </span>
                  <span className="text-sm font-medium text-gray-600">
                    {count}
                  </span>
                </div>
                
                <div className="text-xs text-gray-600 mb-2">
                  {category.description}
                </div>
                
                {fields.length > 0 ? (
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {fields.map((field, index) => (
                      <div key={index} className="text-xs text-gray-700 font-mono bg-white px-2 py-1 rounded">
                        {field}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-gray-500 italic">No fields in this category</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Validation Warnings */}
      {(criticalFieldMappings?.team_number?.length === 0 || criticalFieldMappings?.match_number?.length === 0) && (
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-yellow-500">⚠️</span>
            </div>
            <div className="ml-3">
              <div className="text-sm font-medium text-yellow-800">
                Missing Critical Fields
              </div>
              <div className="text-sm text-yellow-700 mt-1">
                {criticalFieldMappings?.team_number?.length === 0 && "No team number field selected. "}
                {criticalFieldMappings?.match_number?.length === 0 && "No match number field selected. "}
                These fields are required for proper data validation.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};