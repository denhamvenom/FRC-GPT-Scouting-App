import React from 'react';
import type { CriticalFieldsConfig } from '../types';

interface FieldMapperProps {
  headers: string[];
  mapping: { [key: string]: string };
  criticalMappings: CriticalFieldsConfig;
  suggestedVariables: string[];
  teamNumberCandidates: string[];
  matchNumberCandidates: string[];
  onCriticalFieldChange: (fieldType: string, header: string, value: string) => void;
  onMappingChange: (header: string, value: string) => void;
  onClearCriticalMapping: (fieldType: string) => void;
  getMappingValue: (header: string) => string;
  isCriticalField: (header: string, teamHeader: string | null, matchHeader: string | null) => boolean;
}

export const FieldMapper: React.FC<FieldMapperProps> = ({
  headers,
  mapping,
  criticalMappings,
  suggestedVariables,
  teamNumberCandidates,
  matchNumberCandidates,
  onCriticalFieldChange,
  onMappingChange,
  onClearCriticalMapping,
  getMappingValue,
  isCriticalField
}) => {
  return (
    <div className="w-3/4">
      <h2 className="text-xl font-bold mb-3">All Scouting Variables</h2>
      <p className="mb-4 text-gray-600">
        Map each header in your scouting sheet to a standardized variable name.
        Set to "ignore" for headers that should not be processed.
      </p>
      
      <table className="w-full table-auto border">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-4 py-2 w-1/3">Header</th>
            <th className="border px-4 py-2 w-2/3">Mapped Tag</th>
          </tr>
        </thead>
        <tbody>
          {headers.map((header) => {
            // Skip headers that are already mapped as critical fields
            const isCritical = isCriticalField(
              header, 
              criticalMappings.team_number, 
              criticalMappings.match_number
            );
              
            if (isCritical) {
              return (
                <tr key={header} className="bg-blue-50">
                  <td className="border px-4 py-2 font-medium">{header}</td>
                  <td className="border px-4 py-2">
                    <div className="flex items-center">
                      <input
                        className="w-full p-1 border rounded bg-blue-50"
                        value={mapping[header] || ""}
                        readOnly
                      />
                      <span className="ml-2 text-blue-700 text-sm">
                        (Critical Field)
                      </span>
                    </div>
                  </td>
                </tr>
              );
            }
            
            return (
              <tr key={header} className="hover:bg-gray-50">
                <td className="border px-4 py-2">{header}</td>
                <td className="border px-4 py-2">
                  <div className="flex">
                    <input
                      className="w-full p-1 border rounded"
                      value={mapping[header] || ""}
                      onChange={(e) => onMappingChange(header, e.target.value)}
                      list="variables-list"
                    />
                    <datalist id="variables-list">
                      <option value="ignore">ignore</option>
                      {suggestedVariables.map((variable) => (
                        <option key={variable} value={variable}>
                          {variable}
                        </option>
                      ))}
                    </datalist>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};