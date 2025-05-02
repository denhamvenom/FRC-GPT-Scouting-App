// frontend/src/pages/Validation.tsx

import React, { useState, useEffect } from 'react';

interface TeamMatch {
  team_number: number;
  match_number: number;
}

interface ValidationIssue {
  team_number: number;
  match_number: number;
  issues: Array<{
    metric: string;
    value: number;
    detection_method: string;
    z_score?: number;
    bounds?: [number, number];
    team_z_score?: number;
  }>;
}

interface ValidationResult {
  missing_scouting: TeamMatch[];
  missing_superscouting: { team_number: number }[];
  outliers: ValidationIssue[];
  status: string;
  summary: {
    total_missing_matches: number;
    total_missing_superscouting: number;
    total_outliers: number;
    has_issues: boolean;
  };
}

interface CorrectionSuggestion {
  metric: string;
  current_value: number;
  suggested_corrections: Array<{
    value: number;
    method: string;
  }>;
}

function Validation() {
  const [datasetPath, setDatasetPath] = useState<string>('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'missing' | 'outliers'>('missing');
  const [selectedIssue, setSelectedIssue] = useState<TeamMatch | ValidationIssue | null>(null);
  const [suggestions, setSuggestions] = useState<CorrectionSuggestion[]>([]);
  const [corrections, setCorrections] = useState<{ [key: string]: number }>({});
  const [correctionReason, setCorrectionReason] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Check for existing datasets
  useEffect(() => {
    const checkDatasets = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/unified/status?event_key=2025arc&year=2025');
        const data = await response.json();
        
        if (data.status === 'exists' && data.path) {
          setDatasetPath(data.path);
          fetchValidationData(data.path);
        }
      } catch (err) {
        console.error('Error checking datasets:', err);
        setError('Error checking for datasets');
      }
    };
    
    checkDatasets();
  }, []);

  const fetchValidationData = async (path: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/validate/enhanced?unified_dataset_path=${encodeURIComponent(path)}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch validation data');
      }
      
      const data = await response.json();
      setValidationResult(data);
    } catch (err) {
      console.error('Error fetching validation data:', err);
      setError('Error loading validation data');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectIssue = async (issue: TeamMatch | ValidationIssue) => {
    setSelectedIssue(issue);
    setSuggestions([]);
    setCorrections({});
    setCorrectionReason('');
    
    // If this is an outlier, fetch suggestions
    if ('issues' in issue) {
      try {
        const response = await fetch(
          `http://localhost:8000/api/validate/suggest-corrections?unified_dataset_path=${encodeURIComponent(datasetPath)}&team_number=${issue.team_number}&match_number=${issue.match_number}`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch correction suggestions');
        }
        
        const data = await response.json();
        
        if (data.status === 'suggestions_found') {
          setSuggestions(data.suggestions);
        }
      } catch (err) {
        console.error('Error fetching suggestions:', err);
        setError('Error loading correction suggestions');
      }
    }
  };

  const handleCorrectionChange = (metric: string, value: number) => {
    setCorrections(prev => ({
      ...prev,
      [metric]: value
    }));
  };

  const applyCorrections = async () => {
    if (!selectedIssue || Object.keys(corrections).length === 0) return;
    
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/validate/apply-correction?unified_dataset_path=${encodeURIComponent(datasetPath)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          team_number: selectedIssue.team_number,
          match_number: selectedIssue.match_number,
          corrections: corrections,
          reason: correctionReason || 'Manual correction'
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to apply corrections');
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccessMessage('Corrections applied successfully');
        // Refresh validation data
        await fetchValidationData(datasetPath);
        // Clear selection and corrections
        setSelectedIssue(null);
        setCorrections({});
        setCorrectionReason('');
      } else {
        setError(data.message || 'Error applying corrections');
      }
    } catch (err) {
      console.error('Error applying corrections:', err);
      setError('Error applying corrections');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !validationResult) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>;
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Data Validation</h1>
      
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
      
      {validationResult ? (
        <>
          <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <h2 className="text-xl font-bold mb-3">Validation Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`p-4 rounded-lg ${validationResult.summary.total_missing_matches > 0 ? 'bg-red-100' : 'bg-green-100'}`}>
                <span className="text-3xl font-bold block">{validationResult.summary.total_missing_matches}</span>
                <span className="text-gray-700">Missing Match Records</span>
              </div>
              <div className={`p-4 rounded-lg ${validationResult.summary.total_missing_superscouting > 0 ? 'bg-red-100' : 'bg-green-100'}`}>
                <span className="text-3xl font-bold block">{validationResult.summary.total_missing_superscouting}</span>
                <span className="text-gray-700">Missing SuperScouting</span>
              </div>
              <div className={`p-4 rounded-lg ${validationResult.summary.total_outliers > 0 ? 'bg-yellow-100' : 'bg-green-100'}`}>
                <span className="text-3xl font-bold block">{validationResult.summary.total_outliers}</span>
                <span className="text-gray-700">Statistical Outliers</span>
              </div>
            </div>
            
            <div className="mt-4 text-right">
              <button 
                onClick={() => fetchValidationData(datasetPath)}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
              >
                {loading ? 'Refreshing...' : 'Refresh Data'}
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="flex border-b">
                  <button 
                    className={`flex-1 py-3 px-4 font-medium ${activeTab === 'missing' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'}`}
                    onClick={() => setActiveTab('missing')}
                  >
                    Missing Data
                  </button>
                  <button 
                    className={`flex-1 py-3 px-4 font-medium ${activeTab === 'outliers' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'}`}
                    onClick={() => setActiveTab('outliers')}
                  >
                    Outliers
                  </button>
                </div>
                
                <div className="p-4 h-[600px] overflow-y-auto">
                  {activeTab === 'missing' && (
                    validationResult.missing_scouting.length > 0 ? (
                      <ul className="divide-y">
                        {validationResult.missing_scouting.map((issue, idx) => (
                          <li 
                            key={`${issue.team_number}-${issue.match_number}`}
                            className={`py-2 px-3 cursor-pointer hover:bg-gray-100 ${
                              selectedIssue && 'match_number' in selectedIssue && 
                              selectedIssue.team_number === issue.team_number && 
                              selectedIssue.match_number === issue.match_number ? 
                              'bg-blue-100' : ''
                            }`}
                            onClick={() => handleSelectIssue(issue)}
                          >
                            <div className="font-medium">Team {issue.team_number}</div>
                            <div className="text-sm text-gray-600">Match {issue.match_number}</div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="p-4 text-center text-gray-500">
                        No missing match data found! 🎉
                      </div>
                    )
                  )}
                  
                  {activeTab === 'outliers' && (
                    validationResult.outliers.length > 0 ? (
                      <ul className="divide-y">
                        {validationResult.outliers.map((issue, idx) => (
                          <li 
                            key={`${issue.team_number}-${issue.match_number}`}
                            className={`py-2 px-3 cursor-pointer hover:bg-gray-100 ${
                              selectedIssue && 'issues' in selectedIssue && 
                              selectedIssue.team_number === issue.team_number && 
                              selectedIssue.match_number === issue.match_number ? 
                              'bg-blue-100' : ''
                            }`}
                            onClick={() => handleSelectIssue(issue)}
                          >
                            <div className="font-medium">Team {issue.team_number}</div>
                            <div className="text-sm text-gray-600">Match {issue.match_number}</div>
                            <div className="text-xs text-orange-600">{issue.issues.length} issues found</div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="p-4 text-center text-gray-500">
                        No statistical outliers found! 🎉
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
            
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-md p-6 h-full">
                {selectedIssue ? (
                  <>
                    <h2 className="text-xl font-bold mb-4">
                      Team {selectedIssue.team_number} - Match {selectedIssue.match_number}
                    </h2>
                    
                    {'issues' in selectedIssue ? (
                      // Outlier details and correction
                      <>
                        <div className="mb-6">
                          <h3 className="font-medium mb-2">Issues Detected:</h3>
                          <ul className="space-y-4">
                            {selectedIssue.issues.map((issue, idx) => (
                              <li key={idx} className="bg-orange-50 p-3 rounded border border-orange-200">
                                <div className="font-medium">{issue.metric}</div>
                                <div className="text-sm">Current value: <span className="font-mono">{issue.value}</span></div>
                                <div className="text-xs text-gray-600">
                                Detection method: {issue.detection_method}
                                  {issue.z_score && ` (z-score: ${issue.z_score.toFixed(2)})`}
                                  {issue.team_z_score && ` (team z-score: ${issue.team_z_score.toFixed(2)})`}
                                  {issue.bounds && ` (reasonable range: ${issue.bounds[0].toFixed(2)} - ${issue.bounds[1].toFixed(2)})`}
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                        
                        {suggestions.length > 0 ? (
                          <div className="mb-6">
                            <h3 className="font-medium mb-2">Suggested Corrections:</h3>
                            <div className="space-y-4">
                              {suggestions.map((suggestion, idx) => (
                                <div key={idx} className="bg-white p-3 rounded border">
                                  <div className="font-medium">{suggestion.metric}</div>
                                  <div className="text-sm mb-2">Current value: <span className="font-mono">{suggestion.current_value}</span></div>
                                  
                                  <div className="grid grid-cols-2 gap-2">
                                    {suggestion.suggested_corrections.map((correction, cIdx) => (
                                      <button
                                        key={cIdx}
                                        className={`p-2 text-sm rounded border ${
                                          corrections[suggestion.metric] === correction.value
                                            ? 'bg-blue-100 border-blue-400'
                                            : 'hover:bg-gray-100'
                                        }`}
                                        onClick={() => handleCorrectionChange(suggestion.metric, correction.value)}
                                      >
                                        <div className="font-mono">{correction.value}</div>
                                        <div className="text-xs text-gray-600">{correction.method}</div>
                                      </button>
                                    ))}
                                    
                                    <button
                                      className={`p-2 text-sm rounded border ${
                                        corrections[suggestion.metric] === undefined
                                          ? 'bg-gray-100 border-gray-400'
                                          : 'hover:bg-gray-100'
                                      }`}
                                      onClick={() => {
                                        const newCorrections = {...corrections};
                                        delete newCorrections[suggestion.metric];
                                        setCorrections(newCorrections);
                                      }}
                                    >
                                      <div className="font-mono">No Change</div>
                                      <div className="text-xs text-gray-600">keep original</div>
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="mb-6 p-4 bg-gray-100 rounded">
                            No correction suggestions available
                          </div>
                        )}
                        
                        <div className="mb-6">
                          <label className="block font-medium mb-2">Correction Reason:</label>
                          <textarea
                            value={correctionReason}
                            onChange={(e) => setCorrectionReason(e.target.value)}
                            placeholder="Why is this correction being made? (e.g., 'Verified with pit crew', 'Video review', etc.)"
                            className="w-full p-2 border rounded h-24"
                          />
                        </div>
                        
                        <div className="flex justify-end">
                          <button
                            onClick={() => setSelectedIssue(null)}
                            className="px-4 py-2 text-gray-600 border rounded mr-2 hover:bg-gray-100"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={applyCorrections}
                            disabled={Object.keys(corrections).length === 0 || loading}
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
                          >
                            {loading ? 'Applying...' : 'Apply Corrections'}
                          </button>
                        </div>
                      </>
                    ) : (
                      // Missing data details
                      <>
                        <div className="bg-red-50 p-4 rounded border border-red-200 mb-6">
                          <h3 className="font-medium text-red-800 mb-2">Missing Match Data</h3>
                          <p>There is no scouting data for Team {selectedIssue.team_number} in Match {selectedIssue.match_number}.</p>
                        </div>
                        
                        <div className="bg-yellow-50 p-4 rounded border border-yellow-200 mb-6">
                          <h3 className="font-medium text-yellow-800 mb-2">Possible Actions:</h3>
                          <ul className="list-disc list-inside">
                            <li>Find the original scout and have them record the data</li>
                            <li>Watch match video and record the data manually</li>
                            <li>Create a "virtual scout" based on team averages (coming soon)</li>
                          </ul>
                        </div>
                        
                        <div className="flex justify-end">
                          <button
                            onClick={() => setSelectedIssue(null)}
                            className="px-4 py-2 text-gray-600 border rounded hover:bg-gray-100"
                          >
                            Close
                          </button>
                        </div>
                      </>
                    )}
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-gray-500">
                    <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16m-7 6h7" />
                    </svg>
                    <p>Select an issue from the list to view details and apply corrections</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h2 className="text-xl font-bold mb-4">No Dataset Available</h2>
          <p className="mb-4">Please build a unified dataset first before using the validation tool.</p>
          <a 
            href="/workflow"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 inline-block"
          >
            Go to Workflow
          </a>
        </div>
      )}
    </div>
  );
}

export default Validation;