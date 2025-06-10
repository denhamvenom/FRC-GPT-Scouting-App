import React from 'react';
import type { CriticalFieldsConfig } from '../types';

interface MappingActionsProps {
  criticalMappings: CriticalFieldsConfig;
  mapping: { [key: string]: string };
  headers: string[];
  teamNumberCandidates: string[];
  matchNumberCandidates: string[];
  onCriticalFieldChange: (fieldType: string, header: string, value: string) => void;
  onClearCriticalMapping: (fieldType: string) => void;
  onSave: () => void;
  getMappingValue: (header: string) => string;
}

export const MappingActions: React.FC<MappingActionsProps> = ({
  criticalMappings,
  mapping,
  headers,
  teamNumberCandidates,
  matchNumberCandidates,
  onCriticalFieldChange,
  onClearCriticalMapping,
  onSave,
  getMappingValue
}) => {
  return (
    <>
      {/* Critical Fields Section */}
      <div className="mb-8">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-4">
          <h2 className="text-xl font-bold text-blue-800 mb-2">Critical Fields</h2>
          <p className="mb-4 text-blue-700">
            These fields are essential for proper data validation and pick-list generation.
            <strong> They must be mapped correctly</strong> for the system to function properly.
          </p>
          
          <div className="grid grid-cols-1 gap-4">
            {/* Team Number Field */}
            <div className="bg-white p-4 rounded border">
              <h3 className="font-bold mb-2">Team Number</h3>
              <p className="text-sm mb-2">
                Select which header in your scouting sheet contains the team number.
              </p>
              
              <div className="flex items-center">
                <select 
                  value={criticalMappings.team_number || ""} 
                  onChange={(e) => {
                    const header = e.target.value;
                    if (header) {
                      onCriticalFieldChange("team_number", header, "team_number");
                    } else {
                      onClearCriticalMapping("team_number");
                    }
                  }}
                  className="w-full p-2 border rounded"
                >
                  <option value="">-- Select Team Number Header --</option>
                  {/* Show likely headers first */}
                  {teamNumberCandidates.map((header) => (
                    <option key={header} value={header}>{header}</option>
                  ))}
                  <optgroup label="All Headers">
                    {headers.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </optgroup>
                </select>
                
                <div className="ml-2 px-3 py-2 rounded text-sm">
                  {criticalMappings.team_number ? (
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                      Mapped to: {criticalMappings.team_number}
                    </span>
                  ) : (
                    <span className="bg-red-100 text-red-800 px-2 py-1 rounded">
                      Not Mapped
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            {/* Match Number Field */}
            <div className="bg-white p-4 rounded border">
              <h3 className="font-bold mb-2">Match Number / Qual Number</h3>
              <p className="text-sm mb-2">
                Select which header in your scouting sheet contains the match number or qualification match number.
              </p>
              
              <div className="flex items-center">
                <select 
                  value={criticalMappings.match_number || ""} 
                  onChange={(e) => {
                    const header = e.target.value;
                    if (header) {
                      // Decide whether to map to match_number or qual_number
                      const mappingValue = getMappingValue(header);
                      onCriticalFieldChange("match_number", header, mappingValue);
                    } else {
                      onClearCriticalMapping("match_number");
                    }
                  }}
                  className="w-full p-2 border rounded"
                >
                  <option value="">-- Select Match Number Header --</option>
                  {/* Show likely headers first */}
                  {matchNumberCandidates.map((header) => (
                    <option key={header} value={header}>{header}</option>
                  ))}
                  <optgroup label="All Headers">
                    {headers.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </optgroup>
                </select>
                
                <div className="ml-2 px-3 py-2 rounded text-sm">
                  {criticalMappings.match_number ? (
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                      Mapped to: {criticalMappings.match_number} as {
                        mapping[criticalMappings.match_number] === "qual_number" ? 
                        "qual_number" : "match_number"
                      }
                    </span>
                  ) : (
                    <span className="bg-red-100 text-red-800 px-2 py-1 rounded">
                      Not Mapped
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={onSave}
        className="mt-6 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Save Schema
      </button>
    </>
  );
};