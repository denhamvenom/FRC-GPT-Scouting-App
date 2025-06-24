// frontend/src/pages/SchemaMapping.tsx

import { useEffect, useState } from "react";

function SchemaMapping() {
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<{ [key: string]: string }>({});
  const [suggestedVariables, setSuggestedVariables] = useState<string[]>([]);
  // Define critical fields (used for highlighting in UI)
  const criticalFieldsList = ["team_number", "match_number", "qual_number"];
  const [criticalMappings, setCriticalMappings] = useState<{ [key: string]: string | null }>({
    team_number: null,
    match_number: null
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        // First, fetch schema headers
        const schemaRes = await fetch("http://localhost:8000/api/schema/learn");
        const schemaData = await schemaRes.json();
        
        if (schemaData.status === "success") {
          setHeaders(schemaData.headers);
          setMapping(schemaData.mapping);
          
          // Check for critical field mappings
          const newCriticalMappings = { ...criticalMappings };
          
          // Find team_number mapping
          for (const [header, value] of Object.entries(schemaData.mapping)) {
            if (value === "team_number") {
              newCriticalMappings.team_number = header;
            }
            // Find match_number or qual_number mapping
            if (value === "match_number" || value === "qual_number") {
              newCriticalMappings.match_number = header;
            }
          }
          
          setCriticalMappings(newCriticalMappings);
        } else {
          setError("Failed to load schema headers");
        }
        
        // Then fetch variable suggestions from the prompt builder
        try {
          const promptRes = await fetch("http://localhost:8000/api/prompt-builder/variables");
          const promptData = await promptRes.json();
          
          if (promptData.status === "success") {
            setSuggestedVariables(promptData.suggested_variables || []);
          }
        } catch (promptErr) {
          console.log("No suggested variables available yet");
        }
      } catch (err) {
        setError("Error connecting to server");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);

  // Handle critical field mapping changes
  const handleCriticalFieldChange = (fieldType: string, header: string, value: string) => {
    // Update the main mapping
    setMapping((prev) => ({
      ...prev,
      [header]: value
    }));
    
    // Update the critical mappings tracker
    if (fieldType === "team_number") {
      setCriticalMappings((prev) => ({
        ...prev,
        team_number: header
      }));
    } else if (fieldType === "match_number") {
      setCriticalMappings((prev) => ({
        ...prev,
        match_number: header
      }));
    }
  };

  const handleChange = (header: string, value: string) => {
    setMapping((prev) => ({
      ...prev,
      [header]: value
    }));
    
    // If this is setting a critical field, update our tracker
    if (value === "team_number") {
      setCriticalMappings((prev) => ({
        ...prev,
        team_number: header
      }));
    } else if (value === "match_number" || value === "qual_number") {
      setCriticalMappings((prev) => ({
        ...prev,
        match_number: header
      }));
    }
    
    // If this field was previously set as a critical field, but now is changing
    if (header === criticalMappings.team_number && value !== "team_number") {
      setCriticalMappings((prev) => ({
        ...prev,
        team_number: null
      }));
    } else if (header === criticalMappings.match_number && 
              value !== "match_number" && value !== "qual_number") {
      setCriticalMappings((prev) => ({
        ...prev,
        match_number: null
      }));
    }
  };

  const validateCriticalFields = () => {
    const missingFields = [];
    
    if (!criticalMappings.team_number) {
      missingFields.push("Team Number");
    }
    
    if (!criticalMappings.match_number) {
      missingFields.push("Match Number/Qual Number");
    }
    
    if (missingFields.length > 0) {
      setValidationMessage(`Warning: Missing required fields: ${missingFields.join(", ")}`);
      return false;
    }
    
    setValidationMessage(null);
    return true;
  };

  const handleSave = async () => {
    if (!validateCriticalFields()) {
      const proceed = window.confirm("Missing critical field mappings may cause data validation issues. Do you want to proceed anyway?");
      if (!proceed) return;
    }
    
    try {
      const response = await fetch("http://localhost:8000/api/schema/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mapping),
      });
      
      if (response.ok) {
        alert("Schema saved successfully.");
      } else {
        setError("Failed to save schema");
      }
    } catch (err) {
      setError("Error connecting to server");
      console.error(err);
    }
  };

  if (loading) return <div className="text-center p-8">Loading schema...</div>;

  // Find headers that might be good candidates for team_number and match_number
  const findHeaderCandidates = (type: string): string[] => {
    if (type === "team_number") {
      return headers.filter(h => 
        h.toLowerCase().includes("team") && 
        (h.toLowerCase().includes("number") || h.toLowerCase().includes("num"))
      );
    } else if (type === "match_number") {
      return headers.filter(h => 
        (h.toLowerCase().includes("match") || h.toLowerCase().includes("qual")) && 
        (h.toLowerCase().includes("number") || h.toLowerCase().includes("num"))
      );
    }
    return [];
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Scouting Schema Mapping</h1>
      
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {validationMessage && (
        <div className="p-3 mb-4 bg-yellow-100 text-yellow-700 rounded">
          {validationMessage}
        </div>
      )}
      
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
                      handleCriticalFieldChange("team_number", header, "team_number");
                    } else {
                      setCriticalMappings(prev => ({...prev, team_number: null}));
                    }
                  }}
                  className="w-full p-2 border rounded"
                >
                  <option value="">-- Select Team Number Header --</option>
                  {/* Show likely headers first */}
                  {findHeaderCandidates("team_number").map((header) => (
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
                      const mappingValue = header.toLowerCase().includes("qual") ? 
                        "qual_number" : "match_number";
                      handleCriticalFieldChange("match_number", header, mappingValue);
                    } else {
                      setCriticalMappings(prev => ({...prev, match_number: null}));
                    }
                  }}
                  className="w-full p-2 border rounded"
                >
                  <option value="">-- Select Match Number Header --</option>
                  {/* Show likely headers first */}
                  {findHeaderCandidates("match_number").map((header) => (
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
      
      <div className="flex space-x-4">
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
                const isCriticalField = 
                  header === criticalMappings.team_number || 
                  header === criticalMappings.match_number;
                  
                if (isCriticalField) {
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
                          onChange={(e) => handleChange(header, e.target.value)}
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
          
          <button
            onClick={handleSave}
            className="mt-6 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Save Schema
          </button>
        </div>
        
        <div className="w-1/4">
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-lg font-bold mb-3">Suggested Variables</h2>
            {suggestedVariables.length > 0 ? (
              <ul className="text-sm space-y-1 max-h-[400px] overflow-y-auto">
                {suggestedVariables.map((variable) => (
                  <li 
                    key={variable} 
                    className={`p-1 rounded cursor-pointer ${
                      criticalFieldsList.includes(variable) ? 
                      'bg-blue-100 font-medium' : 'hover:bg-gray-100'
                    }`}
                  >
                    {variable}
                    {criticalFieldsList.includes(variable) && 
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
      </div>
    </div>
  );
}

export default SchemaMapping;