import React from 'react';
import { CRITICAL_FIELDS_LIST } from '../types';

interface SchemaPreviewProps {
  suggestedVariables: string[];
}

export const SchemaPreview: React.FC<SchemaPreviewProps> = ({
  suggestedVariables
}) => {
  return (
    <div className="w-1/4">
      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-lg font-bold mb-3">Suggested Variables</h2>
        {suggestedVariables.length > 0 ? (
          <ul className="text-sm space-y-1 max-h-[400px] overflow-y-auto">
            {suggestedVariables.map((variable) => (
              <li 
                key={variable} 
                className={`p-1 rounded cursor-pointer ${
                  CRITICAL_FIELDS_LIST.includes(variable) ? 
                  'bg-blue-100 font-medium' : 'hover:bg-gray-100'
                }`}
              >
                {variable}
                {CRITICAL_FIELDS_LIST.includes(variable) && 
                  <span className="ml-2 text-xs text-blue-700">(critical)</span>
                }
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 text-sm">
            No suggestions available. Upload a game manual in the Setup page first.
          </p>
        )}
      </div>
      
      <div className="bg-white p-4 rounded shadow mt-4">
        <h2 className="text-lg font-bold mb-3">Help</h2>
        <div className="text-sm text-gray-700 space-y-2">
          <p>
            <strong>Team Number</strong>: Maps your team number field (e.g., "Team Number", "Team")
          </p>
          <p>
            <strong>Match Number/Qual Number</strong>: Maps your match identifier (e.g., "Match Number", "Qualification Match")
          </p>
          <p>
            The system will automatically add both <code>match_number</code> and <code>qual_number</code> fields to ensure compatibility.
          </p>
        </div>
      </div>
    </div>
  );
};