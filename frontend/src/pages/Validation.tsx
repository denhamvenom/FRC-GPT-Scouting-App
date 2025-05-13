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

interface IgnoredMatch {
  team_number: number;
  match_number: number;
  reason_category: string;
  reason: string;
  timestamp: string;
}

interface TodoItem {
  team_number: number;
  match_number: number;
  added_timestamp: string;
  updated_timestamp?: string;
  status: 'pending' | 'completed' | 'cancelled';
}

interface ValidationResult {
  missing_scouting: TeamMatch[];
  missing_superscouting: { team_number: number }[];
  ignored_matches: IgnoredMatch[];
  outliers: ValidationIssue[];
  status: string;
  summary: {
    total_missing_matches: number;
    total_missing_superscouting: number;
    total_outliers: number;
    total_ignored_matches: number;
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
  const [activeTab, setActiveTab] = useState<'missing' | 'outliers' | 'todo'>('missing');
  const [selectedIssue, setSelectedIssue] = useState<TeamMatch | ValidationIssue | null>(null);
  const [suggestions, setSuggestions] = useState<CorrectionSuggestion[]>([]);
  const [corrections, setCorrections] = useState<{ [key: string]: number }>({});
  const [correctionReason, setCorrectionReason] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [todoList, setTodoList] = useState<TodoItem[]>([]);
  const [virtualScoutPreview, setVirtualScoutPreview] = useState<any>(null);
  
  // State for handling missing data resolution
  const [actionMode, setActionMode] = useState<'none' | 'watch-video' | 'virtual-scout' | 'ignore-match'>('none');
  const [ignoreReason, setIgnoreReason] = useState<'not_operational' | 'not_present' | 'other'>('not_operational');
  const [customReason, setCustomReason] = useState<string>('');

  // Check for existing datasets
  useEffect(() => {
    const fetchEventInfoAndCheckDatasets = async () => {
      try {
        // First, get current event info from setup
        const setupResponse = await fetch("http://localhost:8000/api/setup/info");
        let eventKey = "";
        let yearValue = 2025; // Default

        if (setupResponse.ok) {
          const setupData = await setupResponse.json();

          if (setupData.status === "success" && setupData.event_key) {
            eventKey = setupData.event_key;
            if (setupData.year) {
              yearValue = setupData.year;
            }
          }
        }

        // If we couldn't get event info from setup, show an error message
        if (!eventKey) {
          console.warn("Could not retrieve event info from setup");
          setError("No event selected. Please go to Setup page and select an event first.");
          return;
        }

        // Now check for datasets with this event key
        const response = await fetch(`http://localhost:8000/api/unified/status?event_key=${eventKey}&year=${yearValue}`);
        const data = await response.json();

        if (data.status === 'exists' && data.path) {
          setDatasetPath(data.path);
          fetchValidationData(data.path);
          fetchTodoList(data.path);
        } else {
          setError(`No dataset found for event ${eventKey}. Please build the dataset first.`);
        }
      } catch (err) {
        console.error('Error checking datasets:', err);
        setError('Error checking for datasets');
      }
    };

    fetchEventInfoAndCheckDatasets();
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
  
  const fetchTodoList = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/validate/todo-list?unified_dataset_path=${encodeURIComponent(path)}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch to-do list');
      }
      
      const data = await response.json();
      if (data.status === 'success') {
        setTodoList(data.todo_list || []);
      }
    } catch (err) {
      console.error('Error fetching to-do list:', err);
    }
  };
  
  const fetchVirtualScoutPreview = async () => {
    if (!selectedIssue) return;
    
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/validate/preview-virtual-scout?unified_dataset_path=${encodeURIComponent(datasetPath)}&team_number=${selectedIssue.team_number}&match_number=${selectedIssue.match_number}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch virtual scout preview');
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setVirtualScoutPreview(data.virtual_scout_preview);
      } else {
        setError(data.message || 'Error generating virtual scout preview');
      }
    } catch (err) {
      console.error('Error fetching virtual scout preview:', err);
      setError('Error generating virtual scout preview');
    } finally {
      setLoading(false);
    }
  };

  const handleActionModeChange = (mode: 'none' | 'watch-video' | 'virtual-scout' | 'ignore-match') => {
    setActionMode(mode);
    
    // Clear any previous preview
    setVirtualScoutPreview(null);
    
    // If virtual scout is selected, fetch the preview
    if (mode === 'virtual-scout') {
      fetchVirtualScoutPreview();
    }
  };

  const handleSelectIssue = async (issue: TeamMatch | ValidationIssue) => {
    setSelectedIssue(issue);
    setSuggestions([]);
    setCorrections({});
    setCorrectionReason('');
    setActionMode('none');
    setCustomReason('');
    setVirtualScoutPreview(null);
    
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
  // Handle missing data resolution
  const handleMissingDataAction = async () => {
    if (!selectedIssue) return;
    
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      let response;
      
      switch (actionMode) {
        case 'watch-video':
          response = await fetch(`http://localhost:8000/api/validate/add-to-todo?unified_dataset_path=${encodeURIComponent(datasetPath)}&team_number=${selectedIssue.team_number}&match_number=${selectedIssue.match_number}`, {
            method: 'POST'
          });
          break;
        
        case 'virtual-scout':
          response = await fetch(`http://localhost:8000/api/validate/create-virtual-scout?unified_dataset_path=${encodeURIComponent(datasetPath)}&team_number=${selectedIssue.team_number}&match_number=${selectedIssue.match_number}`, {
            method: 'POST'
          });
          break;
        
        case 'ignore-match':
          response = await fetch(`http://localhost:8000/api/validate/ignore-match?unified_dataset_path=${encodeURIComponent(datasetPath)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              team_number: selectedIssue.team_number,
              match_number: selectedIssue.match_number,
              reason_category: ignoreReason,
              reason_text: ignoreReason === 'other' ? customReason : ''
            })
          });
          break;
          
        default:
          setError('No action selected');
          setLoading(false);
          return;
      }
      
      if (!response.ok) {
        throw new Error(`Failed to ${actionMode === 'watch-video' ? 'add to to-do list' : actionMode === 'virtual-scout' ? 'create virtual scout' : 'ignore match'}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccessMessage(data.message || 'Action completed successfully');
        // Refresh validation data and todo list
        await fetchValidationData(datasetPath);
        await fetchTodoList(datasetPath);
        // Clear selection
        setSelectedIssue(null);
        setActionMode('none');
      } else {
        setError(data.message || 'Error performing action');
      }
    } catch (err) {
      console.error('Error handling missing data action:', err);
      setError('Error performing action');
    } finally {
      setLoading(false);
    }
  };
  
  // Update to-do list item status
  const updateTodoStatus = async (item: TodoItem, newStatus: 'pending' | 'completed' | 'cancelled') => {
    try {
      const response = await fetch(`http://localhost:8000/api/validate/update-todo-status?unified_dataset_path=${encodeURIComponent(datasetPath)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          team_number: item.team_number,
          match_number: item.match_number,
          status: newStatus
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update to-do status');
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        await fetchTodoList(datasetPath);
        await fetchValidationData(datasetPath);
      }
    } catch (err) {
      console.error('Error updating to-do status:', err);
      setError('Error updating to-do status');
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
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
              <div className={`p-4 rounded-lg bg-blue-100`}>
                <span className="text-3xl font-bold block">{validationResult.summary.total_ignored_matches || 0}</span>
                <span className="text-gray-700">Ignored Matches</span>
              </div>
            </div>
            
            <div className="mt-4 flex justify-between items-center">
              <button
                onClick={() => window.location.href = '/picklist'}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
              >
                <span className="mr-2">Validation Complete</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path fillRule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
                </svg>
              </button>

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
                  <button 
                    className={`flex-1 py-3 px-4 font-medium ${activeTab === 'todo' ? 'bg-blue-100 text-blue-800' : 'bg-white text-gray-600'}`}
                    onClick={() => setActiveTab('todo')}
                  >
                    To-Do List
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
                  
                  {activeTab === 'todo' && (
                    todoList.length > 0 ? (
                      <div>
                        <h3 className="font-medium mb-2 text-blue-800">Matches to Re-Scout</h3>
                        <ul className="divide-y">
                          {todoList.map((item, idx) => (
                            <li
                              key={`todo-${idx}`}
                              className="py-3 px-3"
                            >
                              <div className="flex justify-between items-center">
                                <div>
                                  <div className="font-medium">Team {item.team_number}</div>
                                  <div className="text-sm text-gray-600">Match {item.match_number}</div>
                                  <div className={`text-xs mt-1 px-2 py-0.5 inline-block rounded-full ${
                                    item.status === 'completed' ? 'bg-green-100 text-green-800' :
                                    item.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                                    'bg-yellow-100 text-yellow-800'
                                  }`}>
                                    {item.status === 'completed' ? 'Completed' :
                                     item.status === 'cancelled' ? 'Cancelled' : 'Pending'}
                                  </div>
                                </div>
                                <div className="flex space-x-2">
                                  {item.status === 'pending' && (
                                    <>
                                      <button
                                        onClick={() => updateTodoStatus(item, 'completed')}
                                        className="p-1 bg-green-500 text-white rounded hover:bg-green-600"
                                        title="Mark as completed"
                                      >
                                        ✓
                                      </button>
                                      <button
                                        onClick={() => updateTodoStatus(item, 'cancelled')}
                                        className="p-1 bg-red-500 text-white rounded hover:bg-red-600"
                                        title="Cancel task"
                                      >
                                        ✕
                                      </button>
                                    </>
                                  )}
                                  {item.status !== 'pending' && (
                                    <button
                                      onClick={() => updateTodoStatus(item, 'pending')}
                                      className="p-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                                      title="Reset to pending"
                                    >
                                      ↺
                                    </button>
                                  )}
                                </div>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <div className="p-4 text-center text-gray-500">
                        No items in the to-do list.
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
                      // Missing data details with new action options
                      <>
                        <div className="bg-red-50 p-4 rounded border border-red-200 mb-6">
                          <h3 className="font-medium text-red-800 mb-2">Missing Match Data</h3>
                          <p>There is no scouting data for Team {selectedIssue.team_number} in Match {selectedIssue.match_number}.</p>
                        </div>
                        
                        <div className="mb-6">
                          <h3 className="font-medium mb-3">Choose an Action:</h3>
                          
                          <div className="space-y-3">
                            <div 
                              className={`p-3 rounded border cursor-pointer ${actionMode === 'watch-video' ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'}`}
                              onClick={() => handleActionModeChange('watch-video')}
                            >
                              <div className="flex items-center">
                                <input 
                                  type="radio" 
                                  checked={actionMode === 'watch-video'} 
                                  onChange={() => handleActionModeChange('watch-video')} 
                                  className="mr-2"
                                />
                                <div>
                                  <h4 className="font-medium">Watch Match Video and Rescout</h4>
                                  <p className="text-sm text-gray-600">This match will be added to a to-do list for manual scouting later.</p>
                                </div>
                              </div>
                            </div>
                            
                            <div 
                              className={`p-3 rounded border cursor-pointer ${actionMode === 'virtual-scout' ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'}`}
                              onClick={() => handleActionModeChange('virtual-scout')}
                            >
                              <div className="flex items-start">
                                <input 
                                  type="radio" 
                                  checked={actionMode === 'virtual-scout'} 
                                  onChange={() => handleActionModeChange('virtual-scout')} 
                                  className="mr-2 mt-1"
                                />
                                <div>
                                  <h4 className="font-medium">Create Virtual Scout Data</h4>
                                  <p className="text-sm text-gray-600">Generate scouting data based on team averages and Blue Alliance match data.</p>
                                  
                                  {actionMode === 'virtual-scout' && (
                                    <div className="mt-4">
                                      {virtualScoutPreview ? (
                                        <div className="border rounded p-3 bg-white">
                                          <h5 className="font-medium text-blue-800 mb-2">Virtual Scout Data Preview:</h5>
                                          <div className="max-h-64 overflow-y-auto">
                                            <table className="w-full text-sm">
                                              <thead className="bg-gray-50">
                                                <tr>
                                                  <th className="p-2 text-left">Metric</th>
                                                  <th className="p-2 text-left">Value</th>
                                                  <th className="p-2 text-left">Source</th>
                                                </tr>
                                              </thead>
                                              <tbody>
                                                {Object.entries(virtualScoutPreview)
                                                  .filter(([key, _]) => !['team_number', 'match_number', 'qual_number', 'is_virtual_scout', 'virtual_scout_timestamp'].includes(key))
                                                  .map(([key, value], idx) => (
                                                    <tr key={key} className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                                                      <td className="p-2 font-medium">{key}</td>
                                                      <td className="p-2">{typeof value === 'number' ? 
                                                        Number.isInteger(value) ? value : value.toFixed(2) : 
                                                        String(value)}</td>
                                                      <td className="p-2 text-xs text-gray-500">
                                                        {typeof value === 'number' ? 'Team average with match adjustment' : 'Static value'}
                                                      </td>
                                                    </tr>
                                                  ))}
                                              </tbody>
                                            </table>
                                          </div>
                                          <p className="text-xs text-gray-500 mt-2">
                                            Values are calculated from team's average performance across other matches, 
                                            adjusted based on the alliance performance in this match.
                                          </p>
                                        </div>
                                      ) : (
                                        <div className="flex justify-center items-center h-12">
                                          <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-blue-500"></div>
                                          <span className="ml-2 text-sm text-blue-600">Generating preview...</span>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            <div 
                              className={`p-3 rounded border cursor-pointer ${actionMode === 'ignore-match' ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'}`}
                              onClick={() => handleActionModeChange('ignore-match')}
                            >
                              <div className="flex items-start">
                                <input 
                                  type="radio" 
                                  checked={actionMode === 'ignore-match'} 
                                  onChange={() => handleActionModeChange('ignore-match')} 
                                  className="mr-2 mt-1"
                                />
                                <div>
                                  <h4 className="font-medium">Ignore Match with Reason</h4>
                                  <p className="text-sm text-gray-600 mb-2">Mark this match as intentionally skipped.</p>
                                  
                                  {actionMode === 'ignore-match' && (
                                    <div className="pl-2 border-l-2 border-gray-200 mt-3">
                                      <div className="mb-2">
                                        <label className="flex items-center">
                                          <input 
                                            type="radio" 
                                            name="ignoreReason" 
                                            checked={ignoreReason === 'not_operational'} 
                                            onChange={() => setIgnoreReason('not_operational')} 
                                            className="mr-2"
                                          />
                                          <span>Robot was not operational in the match</span>
                                        </label>
                                      </div>
                                      
                                      <div className="mb-2">
                                        <label className="flex items-center">
                                          <input 
                                            type="radio" 
                                            name="ignoreReason" 
                                            checked={ignoreReason === 'not_present'} 
                                            onChange={() => setIgnoreReason('not_present')} 
                                            className="mr-2"
                                          />
                                          <span>Robot was not present in the match</span>
                                        </label>
                                      </div>
                                      
                                      <div className="mb-2">
                                        <label className="flex items-center">
                                          <input 
                                            type="radio" 
                                            name="ignoreReason" 
                                            checked={ignoreReason === 'other'} 
                                            onChange={() => setIgnoreReason('other')} 
                                            className="mr-2"
                                          />
                                          <span>Other reason</span>
                                        </label>
                                        
                                        {ignoreReason === 'other' && (
                                          <textarea
                                            value={customReason}
                                            onChange={(e) => setCustomReason(e.target.value)}
                                            placeholder="Please specify the reason..."
                                            className="w-full p-2 border rounded mt-2 text-sm"
                                            rows={3}
                                          />
                                        )}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        
                          <div className="flex justify-end mt-6">
                            <button
                              onClick={() => setSelectedIssue(null)}
                              className="px-4 py-2 text-gray-600 border rounded mr-2 hover:bg-gray-100"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={handleMissingDataAction}
                              disabled={actionMode === 'none' || (actionMode === 'ignore-match' && ignoreReason === 'other' && !customReason) || loading}
                              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
                            >
                              {loading ? 'Processing...' : actionMode === 'watch-video' ? 'Add to To-Do List' : 
                              actionMode === 'virtual-scout' ? 'Create Virtual Scout' : 'Ignore Match'}
                            </button>
                          </div>
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
          <p className="mb-4">
            {error ? error : "Please build a unified dataset first before using the validation tool."}
          </p>
          <div className="flex justify-center space-x-4">
            <a
              href="/workflow"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 inline-block"
            >
              Go to Workflow
            </a>
            <a
              href="/build-dataset"
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 inline-block"
            >
              Build Dataset
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default Validation;
