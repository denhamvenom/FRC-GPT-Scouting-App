// frontend/src/pages/PicklistView.tsx

import React, { useState, useEffect } from 'react';
import PicklistGenerator from '../components/PicklistGenerator';

interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
}

interface MetricPriority {
  id: string;
  weight: number;
  reason?: string;
}

interface Metric {
  id: string;
  label: string;
  category: string;
}

const PicklistView: React.FC = () => {
  const [datasetPath, setDatasetPath] = useState<string>('');
  const [yourTeamNumber, setYourTeamNumber] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<'first' | 'second' | 'third'>('first');
  
  // Priorities for each pick position
  const [firstPickPriorities, setFirstPickPriorities] = useState<MetricPriority[]>([]);
  const [secondPickPriorities, setSecondPickPriorities] = useState<MetricPriority[]>([]);
  const [thirdPickPriorities, setThirdPickPriorities] = useState<MetricPriority[]>([]);
  
  // Available metrics
  const [universalMetrics, setUniversalMetrics] = useState<Metric[]>([]);
  const [gameMetrics, setGameMetrics] = useState<Metric[]>([]);
  
  // Generated picklists
  const [firstPicklist, setFirstPicklist] = useState<Team[]>([]);
  const [secondPicklist, setSecondPicklist] = useState<Team[]>([]);
  const [thirdPicklist, setThirdPicklist] = useState<Team[]>([]);
  
  // Track teams already picked in previous lists
  const [excludedTeams, setExcludedTeams] = useState<number[]>([]);
  
  // Loading, error states
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLocking, setIsLocking] = useState<boolean>(false);
  const [picklists, setPicklists] = useState<any[]>([]);
  const [hasLockedPicklist, setHasLockedPicklist] = useState<boolean>(false);
  const [activeAllianceSelection, setActiveAllianceSelection] = useState<number | null>(null);
  
  useEffect(() => {
    // Check for dataset and load metrics
    checkDatasetStatus();
    // Check for existing locked picklists
    fetchLockedPicklists();
  }, []);
  
  // Update excluded teams when picklists change
  useEffect(() => {
    const excluded: number[] = [];
    
    // Add teams from first pick if we're on second or third tab
    if (activeTab === 'second' || activeTab === 'third') {
      firstPicklist.slice(0, 1).forEach(team => {
        excluded.push(team.team_number);
      });
    }
    
    // Add teams from second pick if we're on third tab
    if (activeTab === 'third') {
      secondPicklist.slice(0, 1).forEach(team => {
        excluded.push(team.team_number);
      });
    }
    
    setExcludedTeams(excluded);
  }, [activeTab, firstPicklist, secondPicklist]);
  
  const checkDatasetStatus = async () => {
    try {
      // Check for unified dataset
      const response = await fetch('http://localhost:8000/api/unified/status?event_key=2025arc&year=2025');
      const data = await response.json();
      
      if (data.status === 'exists' && data.path) {
        setDatasetPath(data.path);
        await fetchMetrics(data.path);
      }
    } catch (err) {
      console.error('Error checking dataset status:', err);
      setError('Error checking for datasets');
    } finally {
      setIsLoading(false);
    }
  };
  
  const fetchMetrics = async (path: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/picklist/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ unified_dataset_path: path })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setUniversalMetrics(data.universal_metrics || []);
        setGameMetrics(data.game_metrics || []);
        
        // Get your team number from dataset if available
        if (data.your_team_number) {
          setYourTeamNumber(data.your_team_number);
        }
      }
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError('Error loading metrics data');
    }
  };
  
  const handleAddMetric = (metric: Metric) => {
    const newPriority: MetricPriority = {
      id: metric.id,
      weight: 1.0
    };
    
    // Add to the appropriate list based on active tab
    if (activeTab === 'first') {
      if (!firstPickPriorities.some(p => p.id === metric.id)) {
        setFirstPickPriorities([...firstPickPriorities, newPriority]);
      }
    } else if (activeTab === 'second') {
      if (!secondPickPriorities.some(p => p.id === metric.id)) {
        setSecondPickPriorities([...secondPickPriorities, newPriority]);
      }
    } else if (activeTab === 'third') {
      if (!thirdPickPriorities.some(p => p.id === metric.id)) {
        setThirdPickPriorities([...thirdPickPriorities, newPriority]);
      }
    }
  };
  
  const handleRemovePriority = (metricId: string) => {
    // Remove from the appropriate list based on active tab
    if (activeTab === 'first') {
      setFirstPickPriorities(firstPickPriorities.filter(p => p.id !== metricId));
    } else if (activeTab === 'second') {
      setSecondPickPriorities(secondPickPriorities.filter(p => p.id !== metricId));
    } else if (activeTab === 'third') {
      setThirdPickPriorities(thirdPickPriorities.filter(p => p.id !== metricId));
    }
  };
  
  const handleWeightChange = (metricId: string, weight: number) => {
    // Update weight in the appropriate list based on active tab
    if (activeTab === 'first') {
      setFirstPickPriorities(firstPickPriorities.map(p => 
        p.id === metricId ? { ...p, weight } : p
      ));
    } else if (activeTab === 'second') {
      setSecondPickPriorities(secondPickPriorities.map(p => 
        p.id === metricId ? { ...p, weight } : p
      ));
    } else if (activeTab === 'third') {
      setThirdPickPriorities(thirdPickPriorities.map(p => 
        p.id === metricId ? { ...p, weight } : p
      ));
    }
  };
  
  const fetchLockedPicklists = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alliance/picklists');
      const data = await response.json();
      
      if (data.status === 'success') {
        setPicklists(data.picklists || []);
        
        // Check if there's a locked picklist for the current event and team
        const currentPicklist = data.picklists.find((p: any) => 
          p.team_number === yourTeamNumber && p.event_key === '2025arc'
        );
        
        setHasLockedPicklist(!!currentPicklist);
        
        // Check if there's an active alliance selection
        if (currentPicklist) {
          // Fetch alliance selections for this picklist
          const selectionResponse = await fetch(`http://localhost:8000/api/alliance/selection/${currentPicklist.id}`);
          const selectionData = await selectionResponse.json();
          
          if (selectionData.status === 'success' && selectionData.selection) {
            setActiveAllianceSelection(selectionData.selection.id);
          }
        }
      }
    } catch (err) {
      console.error('Error fetching locked picklists:', err);
    }
  };
  
  const handleLockPicklist = async () => {
    // Validate we have first and second picks
    if (!firstPicklist.length || !secondPicklist.length) {
      setError('You must generate both first and second pick rankings before locking your picklist.');
      return;
    }
    
    // Validate team number
    if (!yourTeamNumber) {
      setError('You must enter your team number before locking your picklist.');
      return;
    }
    
    setIsLocking(true);
    setError(null);
    
    try {
      const requestBody = {
        team_number: yourTeamNumber,
        event_key: '2025arc', // Hardcoded for now, could be made dynamic
        year: 2025,           // Hardcoded for now, could be made dynamic
        first_pick_data: {
          teams: firstPicklist,
          analysis: null,      // Add analysis if available
          metadata: {
            priorities: firstPickPriorities
          }
        },
        second_pick_data: {
          teams: secondPicklist,
          analysis: null,      // Add analysis if available
          metadata: {
            priorities: secondPickPriorities
          }
        },
        third_pick_data: thirdPicklist.length ? {
          teams: thirdPicklist,
          analysis: null,      // Add analysis if available
          metadata: {
            priorities: thirdPickPriorities
          }
        } : null
      };
      
      const response = await fetch('http://localhost:8000/api/alliance/lock-picklist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to lock picklist');
      }
      
      const data = await response.json();
      
      // Update state with success message
      setSuccessMessage('Picklist successfully locked! You can now proceed to the Alliance Selection screen.');
      setHasLockedPicklist(true);
      
      // Refresh the picklists
      fetchLockedPicklists();
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
      
    } catch (err: any) {
      setError(err.message || 'Error locking picklist');
      console.error('Error locking picklist:', err);
    } finally {
      setIsLocking(false);
    }
  };
  
  const handlePicklistGenerated = (position: 'first' | 'second' | 'third', result: any) => {
    if (result.status === 'success') {
      if (position === 'first') {
        setFirstPicklist(result.picklist);
      } else if (position === 'second') {
        setSecondPicklist(result.picklist);
      } else if (position === 'third') {
        setThirdPicklist(result.picklist);
      }
    }
  };
  
  const getActivePriorities = () => {
    if (activeTab === 'first') return firstPickPriorities;
    if (activeTab === 'second') return secondPickPriorities;
    return thirdPickPriorities;
  };
  
  if (isLoading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>;
  }
  
  if (!datasetPath) {
    return (
      <div className="max-w-5xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h2 className="text-xl font-bold mb-4">No Dataset Available</h2>
          <p className="mb-4">Please build a unified dataset first before using the picklist builder.</p>
          <a 
            href="/workflow"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 inline-block"
          >
            Go to Workflow
          </a>
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Alliance Selection Picklist</h1>
        
        <div className="flex space-x-4">
          {/* Show Lock button only if we have first and second picks */}
          {(firstPicklist.length > 0 && secondPicklist.length > 0) && (
            <button
              onClick={handleLockPicklist}
              disabled={isLocking || hasLockedPicklist}
              className={`px-4 py-2 rounded font-medium flex items-center ${
                hasLockedPicklist
                  ? 'bg-green-600 text-white cursor-default'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isLocking ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                  Locking...
                </>
              ) : hasLockedPicklist ? (
                <>
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                  Picklist Locked
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                  Lock Picklist
                </>
              )}
            </button>
          )}
          
          {/* Show Alliance Selection button if picklist is locked */}
          {hasLockedPicklist && (
            <a
              href={`/alliance-selection${activeAllianceSelection ? `/${activeAllianceSelection}` : ''}`}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 font-medium flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
              </svg>
              Alliance Selection
            </a>
          )}
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
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Available Metrics & Priorities */}
        <div className="lg:col-span-1">
          {/* Your team info */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <h2 className="text-xl font-bold mb-4">Your Team</h2>
            <div className="mb-4">
              <label className="block font-medium mb-2">Your Team Number</label>
              <input
                type="number"
                value={yourTeamNumber || ''}
                onChange={(e) => setYourTeamNumber(parseInt(e.target.value) || 0)}
                placeholder="Enter your team number"
                className="w-full p-2 border rounded"
              />
            </div>
          </div>
          
          {/* Priorities Configuration */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <div className="flex border-b mb-4">
              <button
                onClick={() => setActiveTab('first')}
                className={`py-2 px-4 font-medium ${
                  activeTab === 'first'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                First Pick
              </button>
              <button
                onClick={() => setActiveTab('second')}
                className={`py-2 px-4 font-medium ${
                  activeTab === 'second'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Second Pick
              </button>
              <button
                onClick={() => setActiveTab('third')}
                className={`py-2 px-4 font-medium ${
                  activeTab === 'third'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Third Pick
              </button>
            </div>
            
            <h2 className="text-lg font-bold mb-3">Current Priorities</h2>
            
            {getActivePriorities().length === 0 ? (
              <p className="text-gray-500 text-sm mb-4">No priorities selected. Add metrics from below.</p>
            ) : (
              <div className="space-y-3 mb-4">
                {getActivePriorities().map((priority) => {
                  const metric = [...universalMetrics, ...gameMetrics].find(m => m.id === priority.id);
                  return (
                    <div key={priority.id} className="p-2 bg-blue-50 border border-blue-200 rounded flex items-center">
                      <div className="flex-1">
                        <div className="font-medium">{metric?.label || priority.id}</div>
                        <div className="flex items-center">
                          <span className="text-sm mr-2">Weight:</span>
                          <input
                            type="range"
                            min="0.5"
                            max="3"
                            step="0.1"
                            value={priority.weight}
                            onChange={(e) => handleWeightChange(priority.id, parseFloat(e.target.value))}
                            className="w-24"
                          />
                          <span className="text-sm ml-2">{priority.weight.toFixed(1)}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemovePriority(priority.id)}
                        className="text-red-500 p-1 hover:text-red-700"
                      >
                        ×
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
            
            <h3 className="font-semibold text-blue-700 mb-2">Universal Metrics</h3>
            <div className="space-y-2 mb-4">
              {universalMetrics.map((metric) => (
                <div
                  key={metric.id}
                  onClick={() => handleAddMetric(metric)}
                  className="p-2 border rounded cursor-pointer hover:bg-gray-50"
                >
                  <span className="font-medium">{metric.label}</span>
                  <span className="ml-2 text-xs px-2 py-0.5 bg-gray-100 text-gray-800 rounded-full">
                    {metric.category}
                  </span>
                </div>
              ))}
            </div>
            
            <h3 className="font-semibold text-green-700 mb-2">Game-Specific Metrics</h3>
            <div className="space-y-2">
              {gameMetrics.map((metric) => (
                <div
                  key={metric.id}
                  onClick={() => handleAddMetric(metric)}
                  className="p-2 border rounded cursor-pointer hover:bg-gray-50"
                >
                  <span className="font-medium">{metric.label}</span>
                  <span className="ml-2 text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded-full">
                    {metric.category}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Right Column - Picklist */}
        <div className="lg:col-span-2">
          {activeTab === 'first' && (
            <PicklistGenerator
              datasetPath={datasetPath}
              yourTeamNumber={yourTeamNumber}
              pickPosition="first"
              priorities={firstPickPriorities}
              onPicklistGenerated={(result) => handlePicklistGenerated('first', result)}
            />
          )}
          
          {activeTab === 'second' && (
            <PicklistGenerator
              datasetPath={datasetPath}
              yourTeamNumber={yourTeamNumber}
              pickPosition="second"
              priorities={secondPickPriorities}
              excludeTeams={excludedTeams}
              onPicklistGenerated={(result) => handlePicklistGenerated('second', result)}
            />
          )}
          
          {activeTab === 'third' && (
            <PicklistGenerator
              datasetPath={datasetPath}
              yourTeamNumber={yourTeamNumber}
              pickPosition="third"
              priorities={thirdPickPriorities}
              excludeTeams={excludedTeams}
              onPicklistGenerated={(result) => handlePicklistGenerated('third', result)}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default PicklistView;