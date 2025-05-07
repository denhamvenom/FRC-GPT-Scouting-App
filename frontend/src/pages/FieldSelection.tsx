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

// Enhanced utility function to auto-categorize fields based on patterns
const autoCategorizeField = (header: string): string => {
  // Convert to lowercase for case-insensitive matching
  const headerLower = header.toLowerCase();
  
  // Special handling for robot team numbers in SuperScouting
  if (/robot\s*\d+\s*number/i.test(header)) {
    return 'team_number'; // Identify "Robot X Number" as team number fields
  }
  
  // Check for team number or match number patterns (general)
  if ((/team|^t\d+$|^frc\d+$/i.test(headerLower)) && /number/i.test(headerLower)) {
    return 'team_number';
  }
  
  // Handle match/qual number fields
  if (/qual\s*number/i.test(headerLower)) {
    return 'match_number';
  }
  
  if (/match|qualification|^q\d+$/i.test(headerLower)) {
    return 'match_number';
  }
  
  // Check for autonomous/auto patterns
  if (/auto|autonomous|^a_|^a\.|auton/i.test(headerLower)) {
    return 'auto';
  }
  
  // Check for teleop patterns
  if (/tele|teleop|teleoperated|driver|^t_|^t\./i.test(headerLower)) {
    return 'teleop';
  }
  
  // Check for endgame patterns
  if (/end|endgame|final|climb|parking|docking|hanging/i.test(headerLower)) {
    return 'endgame';
  }
  
  // Check for strategy/subjective patterns
  if (/strat|comment|note|subjective|rating|skill|defense|speed|observ/i.test(headerLower)) {
    return 'strategy';
  }
  
  // Check for team info patterns
  if (/alliance|color|station|position|start/i.test(headerLower)) {
    return 'team_info';
  }
  
  // Default to 'other' if no patterns match
  return 'other';
};

// Helper function to ensure robot group team numbers and match numbers are correctly handled
const processRobotGroups = (groups: { [key: string]: string[] }, selectedFields: { [key: string]: string }) => {
  // Check all fields for potential match numbers
  Object.entries(selectedFields).forEach(([header, _]) => {
    if (/qual\s*number/i.test(header)) {
      selectedFields[header] = 'match_number';
    }
  });
  
  Object.entries(groups).forEach(([_, headers]) => {
    // Find team number field in this robot group
    const teamNumberField = headers.find(header => 
      /robot\s*\d+\s*number/i.test(header)
    );
    
    // If found, make sure it's mapped as team_number
    if (teamNumberField) {
      selectedFields[teamNumberField] = 'team_number';
    }
    
    // Also map match related fields if they exist in groups
    headers.forEach(header => {
      if (/qual\s*number/i.test(header)) {
        selectedFields[header] = 'match_number';
      }
    });
  });
  
  return selectedFields;
};

function FieldSelection() {
  const navigate = useNavigate();
  const [scoutingHeaders, setScoutingHeaders] = useState<string[]>([]);
  const [superscoutingHeaders, setSuperscoutingHeaders] = useState<string[]>([]);
  const [selectedFields, setSelectedFields] = useState<{ [key: string]: string }>({});
  // Updated to support multiple fields per critical category
  const [criticalFieldMappings, setCriticalFieldMappings] = useState<{ 
    team_number: string[], 
    match_number: string[] 
  }>({
    team_number: [],
    match_number: []
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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
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
        
        // Initialize all headers with auto-categorization
        const initialFields: { [key: string]: string } = {};
        [...scoutData.headers || [], ...superData.headers || []].forEach(header => {
          initialFields[header] = autoCategorizeField(header);
        });
        
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
          const r1Headers = superHeaders.filter((h: string) => patternSet[0].test(h));
          const r2Headers = superHeaders.filter((h: string) => patternSet[1].test(h));
          const r3Headers = superHeaders.filter((h: string) => patternSet[2].test(h));
          
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
        
        // Set up robot groups first
        setRobotGroups(newRobotGroups);
        setAssignedHeaders(newAssignedHeaders);
        
        // Process fields after robot groups are established
        const processedFields = processRobotGroups(newRobotGroups, initialFields);
        setSelectedFields(processedFields);
        
        // Update critical field mappings after processing
        const newCriticalMappings = { 
          team_number: [] as string[], 
          match_number: [] as string[]
        };
        
        Object.entries(processedFields).forEach(([header, category]) => {
          if (category === 'team_number') {
            newCriticalMappings.team_number.push(header);
          } else if (category === 'match_number') {
            newCriticalMappings.match_number.push(header);
          }
        });
        setCriticalFieldMappings(newCriticalMappings);
        
        // Add feedback about automated categorization
        const autoMappedCount = Object.values(processedFields).filter(v => v !== 'ignore' && v !== 'other').length;
        if (autoMappedCount > 0) {
          setSuccessMessage(`Auto-categorized ${autoMappedCount} fields based on naming patterns. Please review and adjust as needed.`);
        }
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
    // Find all team_number and match_number mappings
    const teamNumberFields: string[] = [];
    const matchNumberFields: string[] = [];
    
    Object.entries(selectedFields).forEach(([header, category]) => {
      if (category === 'team_number') {
        teamNumberFields.push(header);
      } else if (category === 'match_number') {
        matchNumberFields.push(header);
      }
    });
    
    // Update state with the mappings
    setCriticalFieldMappings({
      team_number: teamNumberFields,
      match_number: matchNumberFields
    });
    
    // Check if we have at least one of each critical field type
    const missingFields = [];
    
    if (teamNumberFields.length === 0) {
      missingFields.push('Team Number');
    }
    
    if (matchNumberFields.length === 0) {
      missingFields.push('Match Number');
    }
    
    if (missingFields.length > 0) {
      setValidationWarning(`Warning: Missing required fields: ${missingFields.join(', ')}`);
    } else {
      setValidationWarning(null);
    }
  };

  // Modified to allow multiple critical field mappings
  const handleCategoryChange = (header: string, category: string) => {
    // Update the field mapping
    setSelectedFields(prev => ({
      ...prev,
      [header]: category
    }));
    
    // Validation will run automatically via useEffect
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
    
    if (criticalFieldMappings.team_number.length === 0) {
      missingFields.push('Team Number');
    }
    
    if (criticalFieldMappings.match_number.length === 0) {
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
      setIsLoading(true);
      
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
      
      // Show initial success message
      setSuccessMessage('Field selections saved successfully! Now learning schema mappings...');
      
      // Trigger schema mapping for both regular scouting and superscout
      try {
        // Learn regular scouting schema
        await fetch('http://localhost:8000/api/schema/learn');
        
        // Learn superscouting schema with data analysis
        const superResponse = await fetch('http://localhost:8000/api/schema_superscout/learn');
        const superData = await superResponse.json();
        
        if (superResponse.ok && superData.status === 'success') {
          setSuccessMessage('Field selections and schema mappings saved successfully! Analyzing data content...');
        }
        
        // Navigate to workflow page after a brief delay
        setTimeout(() => {
          navigate('/workflow');
        }, 1500);
      } catch (schemaErr) {
        console.error('Error learning schema mappings:', schemaErr);
        // Still continue to workflow even if schema learning fails
        // The user can manually trigger schema learning later
        setSuccessMessage('Field selections saved, but schema learning had issues. Continuing to workflow.');
        setTimeout(() => {
          navigate('/workflow');
        }, 2000);
      }
    } catch (err) {
      console.error('Error saving schema:', err);
      setError('Error saving field selections');
      setIsLoading(false);
    }
  };

  // Find suggested headers for critical fields
  const findCriticalFieldCandidates = (field: CriticalField): string[] => {
    // Include both scouting and superscouting headers for better suggestions
    const allHeaders = [...scoutingHeaders, ...superscoutingHeaders];
    return allHeaders.filter(header => field.requiredPattern.test(header));
  };

 
  // Helper to get the critical field type
  const getCriticalFieldType = (header: string): string | null => {
    if (criticalFieldMappings.team_number.includes(header)) {
      return 'team_number';
    }
    if (criticalFieldMappings.match_number.includes(header)) {
      return 'match_number';
    }
    return null;
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
      
      {successMessage && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {successMessage}
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
          <span className="block mt-1">Note: You can select multiple team number and match number fields for superscouting robot groups.</span>
        </p>
        
        <div className="grid grid-cols-1 gap-4">
          {CRITICAL_FIELDS.map(field => {
            const candidates = findCriticalFieldCandidates(field);
            const currentMappings = criticalFieldMappings[field.key as keyof typeof criticalFieldMappings];
            
            return (
              <div key={field.key} className="bg-white p-4 rounded border">
                <h3 className="font-bold mb-1">{field.label}s</h3>
                <p className="text-sm mb-3 text-gray-600">{field.description}</p>
                
                {/* Display currently mapped fields */}
                {currentMappings.length > 0 ? (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold mb-2">Currently Mapped Fields:</h4>
                    <div className="flex flex-wrap gap-2">
                      {currentMappings.map(header => (
                        <div key={header} className="flex items-center bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                          <span>{header}</span>
                          <button 
                            onClick={() => handleCategoryChange(header, 'ignore')}
                            className="ml-2 text-blue-800 hover:text-blue-600"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="mb-4 bg-red-100 text-red-700 p-2 rounded">
                    No {field.label} fields mapped yet.
                  </div>
                )}
                
                {/* Field Suggestions */}
                <div>
                  <h4 className="text-sm font-semibold mb-2">Add A {field.label} Field:</h4>
                  <select
                    value=""
                    onChange={(e) => {
                      const header = e.target.value;
                      if (header) {
                        handleCategoryChange(header, field.key);
                      }
                    }}
                    className="w-full p-2 border rounded"
                  >
                    <option value="">-- Select {field.label} Field --</option>
                    
                    {/* Show likely candidates first */}
                    {candidates.length > 0 && (
                      <optgroup label="Suggested Fields">
                        {candidates
                          .filter(header => !currentMappings.includes(header))
                          .map(header => (
                            <option key={`suggested-${header}`} value={header}>
                              {header}
                            </option>
                          ))}
                      </optgroup>
                    )}
                    
                    {/* Show fields grouped by section */}
                    <optgroup label="Scouting Fields">
                      {scoutingHeaders
                        .filter(header => !currentMappings.includes(header) && selectedFields[header] !== field.key)
                        .map(header => (
                          <option key={header} value={header}>
                            {header}
                          </option>
                        ))}
                    </optgroup>
                    
                    <optgroup label="SuperScouting Fields">
                      {superscoutingHeaders
                        .filter(header => !currentMappings.includes(header) && selectedFields[header] !== field.key)
                        .map(header => (
                          <option key={`super-${header}`} value={header}>
                            {header}
                          </option>
                        ))}
                    </optgroup>
                  </select>
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
                const criticalType = getCriticalFieldType(header);
                                      
                return (
                  <tr 
                    key={`scout-${index}`} 
                    className={`${criticalType ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                  >
                    <td className="border px-4 py-2">
                      {criticalType && (
                        <span className="inline-block mr-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {criticalType === 'team_number' ? 'Team Number' : 'Match Number'}
                        </span>
                      )}
                      {header}
                    </td>
                    <td className="border px-4 py-2">
                      <select
                        value={selectedFields[header] || 'ignore'}
                        onChange={(e) => handleCategoryChange(header, e.target.value)}
                        className={`w-full p-1 border rounded ${criticalType ? 'bg-blue-50 font-medium' : ''}`}
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
        
        {/* SuperScouting Robot Groups Section - Only show if there are superscouting headers */}
        {superscoutingHeaders.length > 0 ? (
          <>
            <h2 className="text-xl font-bold mb-4">SuperScouting Robot Groups</h2>
            <p className="mb-4 text-gray-600">
              Group superscouting headers by robot to create separate records for each robot in a match.
              <span className="block mt-1 font-semibold text-blue-700">
                You can mark multiple team number fields - one for each robot group.
              </span>
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
                      {headers.map(header => {
                        const criticalType = getCriticalFieldType(header);
                        return (
                          <li key={header} className="flex justify-between items-center text-sm">
                            <span>
                              {header}
                              {criticalType && (
                                <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                                  {criticalType === 'team_number' ? 'Team #' : 'Match #'}
                                </span>
                              )}
                            </span>
                            <button
                              onClick={() => handleRemoveFromRobotGroup(header, robot)}
                              className="text-red-500 hover:text-red-700"
                            >
                              ×
                            </button>
                          </li>
                        );
                      })}
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
                    const criticalType = getCriticalFieldType(header);
                      
                    return (
                      <tr 
                        key={`super-${index}`} 
                        className={`${isAssigned ? 'bg-gray-100' : 'hover:bg-gray-50'} ${
                          criticalType ? 'bg-blue-50' : ''
                        }`}
                      >
                        <td className="border px-4 py-2">
                          {header}
                          {assignedGroup && (
                            <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                              {assignedGroup.replace('_', ' ').toUpperCase()}
                            </span>
                          )}
                          {criticalType && (
                            <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                              {criticalType === 'team_number' ? 'Team #' : 'Match #'}
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
                            <option value="team_number">Team Number</option>
                            <option value="match_number">Match Number</option>
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
          </>
        ) : (
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-300 mb-6">
            <h2 className="text-xl font-bold text-yellow-800 mb-2">SuperScouting Data Not Found</h2>
            <p className="text-yellow-700 mb-2">
              No SuperScouting headers were detected in your spreadsheet. This may indicate:
            </p>
            <ul className="list-disc list-inside text-yellow-700 mb-2">
              <li>You don't have a "SuperScouting" tab in your Google Sheet</li>
              <li>The "SuperScouting" tab exists but is empty or formatted incorrectly</li>
              <li>There might be an API connection issue with the Google Sheets service</li>
            </ul>
            <p className="text-yellow-700">
              SuperScouting data is optional but helpful for qualitative robot assessments and strategy notes.
              You can still proceed without SuperScouting data.
            </p>
          </div>
        )}
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