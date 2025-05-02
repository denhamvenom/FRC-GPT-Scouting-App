// frontend/src/pages/FieldSelection.tsx

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface FieldCategory {
  key: string;
  label: string;
  description: string;
}

interface CriticalField {
  key: string;
  label: string;
  description: string;
  requiredPattern: RegExp;
}

const CRITICAL_FIELDS: CriticalField[] = [
  { 
    key: 'team_number', 
    label: 'Team Number', 
    description: 'Identifies which team the data belongs to', 
    requiredPattern: /team|number|^\d+$/i
  },
  { 
    key: 'match_number', 
    label: 'Match Number', 
    description: 'Identifies which match the data belongs to',
    requiredPattern: /match|qual/i
  }
];

const FIELD_CATEGORIES: FieldCategory[] = [
  { key: 'team_info', label: 'Team Information', description: 'Basic team identifiers and match metadata' },
  { key: 'auto', label: 'Autonomous', description: 'Robot actions during the autonomous period' },
  { key: 'teleop', label: 'Teleop', description: 'Robot actions during the teleop period' },
  { key: 'endgame', label: 'Endgame', description: 'Robot actions during the endgame period' },
  { key: 'strategy', label: 'Strategy', description: 'Strategic assessment and qualitative observations' },
  { key: 'other', label: 'Other', description: 'Any additional fields that don\'t fit above categories' },
];

function FieldSelection() {
  const navigate = useNavigate();
  const [scoutingHeaders, setScoutingHeaders] = useState<string[]>([]);
  const [superscoutingHeaders, setSuperscoutingHeaders] = useState<string[]>([]);
  const [selectedFields, setSelectedFields] = useState<{ [key: string]: string }>({});
  const [criticalFieldMappings, setCriticalFieldMappings] = useState<{ [key: string]: string | null }>({
    team_number: null,
    match_number: null
  });
  // Robot grouping for superscouting
  const [robotGroups, setRobotGroups] = useState<{ [key: string]: string[] }>({
    robot_1: [],
    robot_2: [],
    robot_3: []
  });
  // Current robot group being edited
  const [activeRobotGroup, setActiveRobotGroup] = useState<string>('robot_1');
  // Headers that are already assigned to a robot group
  const [assignedHeaders, setAssignedHeaders] = useState<Set<string>>(new Set());
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);
  const [gameManualUrl, setGameManualUrl] = useState<string>('');
  const [year, setYear] = useState<number>(2025);

  useEffect(() => {
    // Fetch headers from Google Sheets
    const fetchHeaders = async () => {
      setIsLoading(true);
      try {
        // Fetch scouting headers
        const scoutResponse = await fetch('http://localhost:8000/api/sheets/headers?tab=Scouting');
        if (!scoutResponse.ok) {
          throw new Error('Failed to fetch scouting headers');
        }
        const scoutData = await scoutResponse.json();
        
        // Fetch superscouting headers
        const superResponse = await fetch('http://localhost:8000/api/sheets/headers?tab=SuperScouting');
        if (!superResponse.ok) {
          throw new Error('Failed to fetch superscouting headers');
        }
        const superData = await superResponse.json();
        
        // Set headers
        setScoutingHeaders(scoutData.headers || []);
        setSuperscoutingHeaders(superData.headers || []);
        
        // Initialize all headers as "ignore" by default
        const initialFields: { [key: string]: string } = {};
        [...scoutData.headers || [], ...superData.headers || []].forEach(header => {
          initialFields[header] = 'ignore';
        });
        
        // Try to auto-detect critical fields
        const newCriticalMappings = { ...criticalFieldMappings };
        
        // Look for team number field
        const teamNumberHeader = [...scoutData.headers || []]
          .find(header => CRITICAL_FIELDS[0].requiredPattern.test(header));
        if (teamNumberHeader) {
          initialFields[teamNumberHeader] = 'team_number';
          newCriticalMappings.team_number = teamNumberHeader;
        }
        
        // Look for match number field
        const matchNumberHeader = [...scoutData.headers || []]
          .find(header => CRITICAL_FIELDS[1].requiredPattern.test(header));
        if (matchNumberHeader) {
          initialFields[matchNumberHeader] = 'match_number';
          newCriticalMappings.match_number = matchNumberHeader;
        }
        
        // Try to auto-detect robot groupings in superscouting headers
        const superHeaders = superData.headers || [];
        const newRobotGroups = { ...robotGroups };
        const newAssignedHeaders = new Set<string>();
        
        // Try to detect patterns like "Robot 1 X", "Robot 2 X", "Robot 3 X" 
        // or "R1 X", "R2 X", "R3 X"
        const robotPatterns = [
          [/robot\s*1|r1\b/i, /robot\s*2|r2\b/i, /robot\s*3|r3\b/i],
          [/\b1\s*-/, /\b2\s*-/, /\b3\s*-/],
          [/_1_/, /_2_/, /_3_/]
        ];
        
        for (const patternSet of robotPatterns) {
          const r1Headers = superHeaders.filter(h => patternSet[0].test(h));
          const r2Headers = superHeaders.filter(h => patternSet[1].test(h));
          const r3Headers = superHeaders.filter(h => patternSet[2].test(h));
          
          // If we found substantial matches for all robots, use them
          if (r1Headers.length > 1 && r2Headers.length > 1 && r3Headers.length > 1) {
            newRobotGroups.robot_1 = r1Headers;
            newRobotGroups.robot_2 = r2Headers;
            newRobotGroups.robot_3 = r3Headers;
            
            // Mark these headers as assigned
            [...r1Headers, ...r2Headers, ...r3Headers].forEach((h: string) => {
              newAssignedHeaders.add(h);
            });
            
            break;
          }
        }
        
        setSelectedFields(initialFields);
        setCriticalFieldMappings(newCriticalMappings);
        setRobotGroups(newRobotGroups);
        setAssignedHeaders(newAssignedHeaders);
      } catch (err) {
        console.error('Error fetching headers:', err);
        setError('Error fetching headers from Google Sheets');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchHeaders();
  }, []);

  useEffect(() => {
    // Validate critical fields whenever selected fields change
    validateCriticalFields();
  }, [selectedFields]);

  const validateCriticalFields = () => {
    const missingFields = [];
    
    // Check if team_number is mapped
    if (!Object.values(selectedFields).includes('team_number')) {
      missingFields.push('Team Number');
    }
    
    // Check if match_number is mapped
    if (!Object.values(selectedFields).includes('match_number')) {
      missingFields.push('Match Number');
    }
    
    if (missingFields.length > 0) {
      setValidationWarning(`Warning: Missing required fields: ${missingFields.join(', ')}`);
    } else {
      setValidationWarning(null);
    }
    
    // Update critical field mappings
    const newCriticalMappings = { 
      team_number: null, 
      match_number: null 
    };
    
    Object.entries(selectedFields).forEach(([header, category]) => {
      if (category === 'team_number') {
        newCriticalMappings.team_number = header;
      } else if (category === 'match_number') {
        newCriticalMappings.match_number = header;
      }
    });
    
    setCriticalFieldMappings(newCriticalMappings);
  };

  const handleCategoryChange = (header: string, category: string) => {
    // If we're changing a header that was previously mapped to a critical field
    const previousMapping = selectedFields[header];
    if (previousMapping === 'team_number' || previousMapping === 'match_number') {
      // Clear that critical field mapping
      const fieldType = previousMapping as keyof typeof criticalFieldMappings;
      if (criticalFieldMappings[fieldType] === header) {
        setCriticalFieldMappings(prev => ({
          ...prev,
          [fieldType]: null
        }));
      }
    }
    
    // If we're mapping a new header to a critical field
    if (category === 'team_number' || category === 'match_number') {
      // Clear any previous mapping for that critical field
      Object.entries(selectedFields).forEach(([existingHeader, existingCategory]) => {
        if (existingHeader !== header && existingCategory === category) {
          setSelectedFields(prev => ({
            ...prev,
            [existingHeader]: 'ignore'
          }));
        }
      });
      
      // Update critical field mapping
      setCriticalFieldMappings(prev => ({
        ...prev,
        [category]: header
      }));
    }
    
    // Update the field mapping
    setSelectedFields(prev => ({
      ...prev,
      [header]: category
    }));
  };

  const handleAddToRobotGroup = (header: string) => {
    // Remove from any existing robot group
    const updatedGroups = { ...robotGroups };
    
    // Remove header from all groups
    Object.keys(updatedGroups).forEach(group => {
      updatedGroups[group] = updatedGroups[group].filter(h => h !== header);
    });
    
    // Add to current active group
    updatedGroups[activeRobotGroup] = [...updatedGroups[activeRobotGroup], header];
    
    // Update state
    setRobotGroups(updatedGroups);
    
    // Update assigned headers
    const newAssignedHeaders = new Set(assignedHeaders);
    newAssignedHeaders.add(header);
    setAssignedHeaders(newAssignedHeaders);
  };

  const handleRemoveFromRobotGroup = (header: string, group: string) => {
    const updatedGroups = { ...robotGroups };
    updatedGroups[group] = updatedGroups[group].filter(h => h !== header);
    setRobotGroups(updatedGroups);
    
    // Only remove from assigned headers if it's not in any group
    const isAssigned = Object.values(updatedGroups).some(headers => headers.includes(header));
    if (!isAssigned) {
      const newAssignedHeaders = new Set(assignedHeaders);
      newAssignedHeaders.delete(header);
      setAssignedHeaders(newAssignedHeaders);
    }
  };

  const handleRobotGroupChange = (robot: string) => {
    setActiveRobotGroup(robot);
  };

  const handleSaveSchema = async () => {
    // Validate critical fields before saving
    const missingFields = [];
    
    if (!criticalFieldMappings.team_number) {
      missingFields.push('Team Number');
    }
    
    if (!criticalFieldMappings.match_number) {
      missingFields.push('Match Number');
    }
    
    if (missingFields.length > 0) {
      const proceed = window.confirm(
        `Warning: The following critical fields are not mapped: ${missingFields.join(', ')}. ` +
        `This will prevent proper data validation and match tracking. Do you want to proceed anyway?`
      );
      
      if (!proceed) {
        return;
      }
    }
    
    try {
      // Save the schema
      const schema = {
        field_selections: selectedFields,
        manual_url: gameManualUrl,
        year: year,
        critical_mappings: criticalFieldMappings,
        robot_groups: robotGroups
      };
      
      const response = await fetch('http://localhost:8000/api/schema/save-selections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schema)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save schema');
      }
      
      // Navigate to workflow page
      navigate('/workflow');
    } catch (err) {
      console.error('Error saving schema:', err);
      setError('Error saving field selections');
    }
  };

  // Find suggested headers for critical fields
  const findCriticalFieldCandidates = (field: CriticalField): string[] => {
    const allHeaders = [...scoutingHeaders];
    return allHeaders.filter(header => field.requiredPattern.test(header));
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Field Selection</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-bold mb-4">Game Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-2">Year</label>
            <select
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="w-full p-2 border rounded"
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
            </select>
          </div>
          <div>
            <label className="block font-medium mb-2">Game Manual URL (Optional)</label>
            <input
              type="url"
              value={gameManualUrl}
              onChange={(e) => setGameManualUrl(e.target.value)}
              placeholder="https://example.com/game-manual.pdf"
              className="w-full p-2 border rounded"
            />
            <p className="text-sm text-gray-500 mt-1">
              Used for picklist generation and strategy insights.
            </p>
          </div>
        </div>
      </div>
      
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {validationWarning && (
        <div className="p-3 mb-4 bg-yellow-100 text-yellow-700 rounded">
          {validationWarning}
        </div>
      )}
      
      {/* Critical Fields Section */}
      <div className="bg-blue-50 p-6 rounded-lg shadow-md mb-6 border-l-4 border-blue-500">
        <h2 className="text-xl font-bold text-blue-800 mb-2">Critical Fields</h2>
        <p className="mb-4 text-blue-700">
          These fields are required for proper data validation and match tracking. 
          They must be mapped correctly for the system to function properly.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {CRITICAL_FIELDS.map(field => {
            const candidates = findCriticalFieldCandidates(field);
            const currentMapping = criticalFieldMappings[field.key as keyof typeof criticalFieldMappings];
            
            return (
              <div key={field.key} className="bg-white p-4 rounded border">
                <h3 className="font-bold mb-1">{field.label}</h3>
                <p className="text-sm mb-3 text-gray-600">{field.description}</p>
                
                <div className="flex items-center">
                  <select
                    value={currentMapping || ""}
                    onChange={(e) => {
                      const header = e.target.value;
                      if (header) {
                        // Update both the critical mapping and the field selection
                        handleCategoryChange(header, field.key);
                      } else {
                        // Clear the mapping if no header is selected
                        setCriticalFieldMappings(prev => ({
                          ...prev,
                          [field.key]: null
                        }));
                      }
                    }}
                    className="w-full p-2 border rounded"
                  >
                    <option value="">-- Select {field.label} Field --</option>
                    
                    {/* Show likely candidates first */}
                    {candidates.length > 0 && (
                      <optgroup label="Suggested Fields">
                        {candidates.map(header => (
                          <option key={`suggested-${header}`} value={header}>
                            {header}
                          </option>
                        ))}
                      </optgroup>
                    )}
                    
                    {/* Show all fields */}
                    <optgroup label="All Fields">
                      {scoutingHeaders.map(header => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                  
                  <div className="ml-2 text-sm">
                    {currentMapping ? (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
                        Mapped
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full">
                        Not Mapped
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-bold mb-4">Scouting Fields</h2>
        <p className="mb-4 text-gray-600">
          Select which fields to include in analysis and categorize them.
        </p>
        
        <div className="mb-6">
          <table className="min-w-full border">
            <thead className="bg-gray-100">
              <tr>
                <th className="border px-4 py-2 text-left">Header</th>
                <th className="border px-4 py-2 text-left">Category</th>
              </tr>
            </thead>
            <tbody>
              {scoutingHeaders.map((header, index) => {
                const isCriticalField = header === criticalFieldMappings.team_number || 
                                      header === criticalFieldMappings.match_number;
                                      
                return (
                  <tr 
                    key={`scout-${index}`} 
                    className={`${isCriticalField ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                  >
                    <td className="border px-4 py-2">
                      {isCriticalField && (
                        <span className="inline-block mr-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                          Critical
                        </span>
                      )}
                      {header}
                    </td>
                    <td className="border px-4 py-2">
                      <select
                        value={selectedFields[header] || 'ignore'}
                        onChange={(e) => handleCategoryChange(header, e.target.value)}
                        className={`w-full p-1 border rounded ${isCriticalField ? 'bg-blue-50 font-medium' : ''}`}
                        disabled={isCriticalField} // Disable changing critical fields here
                      >
                        <option value="ignore">Ignore</option>
                        <option value="team_number">Team Number</option>
                        <option value="match_number">Match Number</option>
                        {FIELD_CATEGORIES.map(category => (
                          <option key={category.key} value={category.key}>
                            {category.label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {/* SuperScouting Robot Groups Section */}
        <h2 className="text-xl font-bold mb-4">SuperScouting Robot Groups</h2>
        <p className="mb-4 text-gray-600">
          Group superscouting headers by robot to create separate records for each robot in a match.
        </p>
        
        {/* Robot Group Selection Tabs */}
        <div className="flex border-b mb-4">
          {Object.keys(robotGroups).map((robot) => (
            <button
              key={robot}
              onClick={() => handleRobotGroupChange(robot)}
              className={`py-2 px-4 font-medium ${
                activeRobotGroup === robot
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {robot.replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>
        
        {/* Robot Group Members Display */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(robotGroups).map(([robot, headers]) => (
            <div 
              key={robot} 
              className={`border rounded-lg p-4 ${
                activeRobotGroup === robot ? 'border-blue-500 bg-blue-50' : ''
              }`}
            >
              <h3 className="font-bold mb-2">{robot.replace('_', ' ').toUpperCase()}</h3>
              {headers.length === 0 ? (
                <p className="text-gray-500 text-sm italic">No fields assigned</p>
              ) : (
                <ul className="space-y-1">
                  {headers.map(header => (
                    <li key={header} className="flex justify-between items-center text-sm">
                      <span>{header}</span>
                      <button
                        onClick={() => handleRemoveFromRobotGroup(header, robot)}
                        className="text-red-500 hover:text-red-700"
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
        
        <h2 className="text-xl font-bold mb-4">Available SuperScouting Fields</h2>
        <p className="mb-4 text-gray-600">
          Add fields to the currently selected robot group above.
        </p>
        
        <div>
          <table className="min-w-full border">
            <thead className="bg-gray-100">
              <tr>
                <th className="border px-4 py-2 text-left">Header</th>
                <th className="border px-4 py-2 text-left">Category</th>
                <th className="border px-4 py-2 text-center w-24">Robot Group</th>
              </tr>
            </thead>
            <tbody>
              {superscoutingHeaders.map((header, index) => {
                const isAssigned = assignedHeaders.has(header);
                const assignedGroup = Object.entries(robotGroups)
                  .find(([_, headers]) => headers.includes(header))?.[0];
                  
                return (
                  <tr 
                    key={`super-${index}`} 
                    className={`${isAssigned ? 'bg-gray-100' : 'hover:bg-gray-50'}`}
                  >
                    <td className="border px-4 py-2">
                      {header}
                      {assignedGroup && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {assignedGroup.replace('_', ' ').toUpperCase()}
                        </span>
                      )}
                    </td>
                    <td className="border px-4 py-2">
                      <select
                        value={selectedFields[header] || 'ignore'}
                        onChange={(e) => handleCategoryChange(header, e.target.value)}
                        className="w-full p-1 border rounded"
                      >
                        <option value="ignore">Ignore</option>
                        {FIELD_CATEGORIES.map(category => (
                          <option key={category.key} value={category.key}>
                            {category.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="border px-4 py-2 text-center">
                      {assignedGroup ? (
                        <button
                          onClick={() => handleRemoveFromRobotGroup(header, assignedGroup)}
                          className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs hover:bg-red-200"
                        >
                          Remove
                        </button>
                      ) : (
                        <button
                          onClick={() => handleAddToRobotGroup(header)}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                        >
                          {`Add to ${activeRobotGroup.replace('_', ' ').toUpperCase()}`}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="flex justify-end">
        <button
          onClick={handleSaveSchema}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Save Field Selections
        </button>
      </div>
    </div>
  );
}

export default FieldSelection;