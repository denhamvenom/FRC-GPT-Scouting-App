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
  
  useEffect(() => {
    // Check for dataset and load metrics
    checkDatasetStatus();
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
      <h1 className="text-3xl font-bold mb-6">Alliance Selection Picklist</h1>
      
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
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