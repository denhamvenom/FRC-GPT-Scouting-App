// frontend/src/pages/PicklistNew.tsx

import React, { useState, useEffect } from 'react';

// Type definitions
interface Team {
  team_number: number;
  nickname: string;
  stats: Record<string, number>;
  score?: number;
}

interface Metric {
  id: string;
  label: string;
  category: string;
  importance_score?: number;
  win_correlation?: number;
  variability?: number;
}

interface MetricWeight {
  id: string;
  weight: number;
}

const PicklistNew: React.FC = () => {
  // State for dataset path
  const [datasetPath, setDatasetPath] = useState<string>('');
  
  // State for metrics and priorities
  const [universalMetrics, setUniversalMetrics] = useState<Metric[]>([]);
  const [gameMetrics, setGameMetrics] = useState<Metric[]>([]);
  const [suggestedMetrics, setSuggestedMetrics] = useState<Metric[]>([]);
  const [metricsStats, setMetricsStats] = useState<Record<string, any>>({});
  
  // State for selected priorities for each pick type
  const [firstPickPriorities, setFirstPickPriorities] = useState<MetricWeight[]>([]);
  const [secondPickPriorities, setSecondPickPriorities] = useState<MetricWeight[]>([]);
  const [thirdPickPriorities, setThirdPickPriorities] = useState<MetricWeight[]>([]);
  
  // State for natural language prompt
  const [strategyPrompt, setStrategyPrompt] = useState<string>('');
  const [parsedPriorities, setParsedPriorities] = useState<any>(null);
  
  // State for active tab
  const [activeTab, setActiveTab] = useState<'first' | 'second' | 'third'>('first');
  
  // State for loading, error, success
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccessMessage] = useState<string | null>(null);
  
  // Fetch dataset path on load
  useEffect(() => {
    const checkDatasets = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/unified/status?event_key=2025arc&year=2025');
        const data = await response.json();
        
        if (data.status === 'exists' && data.path) {
          setDatasetPath(data.path);
          // For now, mock some data for testing
          mockMetricsData();
          // Later, uncomment this to fetch from API
          // await fetchPicklistAnalysis(data.path);
        }
      } catch (err) {
        console.error('Error checking datasets:', err);
        setError('Error checking for datasets');
      }
    };
    
    checkDatasets();
  }, []);

  // Mock data for testing purposes
  const mockMetricsData = () => {
    setUniversalMetrics([
      { id: "reliability", label: "Reliability / Consistency", category: "universal" },
      { id: "driver_skill", label: "Driver Skill", category: "universal" },
      { id: "defense", label: "Defensive Capability", category: "universal" },
      { id: "cycle_time", label: "Cycle Time", category: "universal" }
    ]);
    
    setGameMetrics([
      { id: "auto_l1_scoring", label: "Auto L1 Scoring", category: "auto" },
      { id: "auto_l4_scoring", label: "Auto L4 Scoring", category: "auto" },
      { id: "teleop_l1_scoring", label: "Teleop L1 Scoring", category: "teleop" },
      { id: "teleop_l4_scoring", label: "Teleop L4 Scoring", category: "teleop" },
      { id: "endgame_climb", label: "Endgame Climb", category: "endgame" }
    ]);
    
    setSuggestedMetrics([
      { id: "auto_l4_scoring", label: "Auto L4 Scoring", category: "auto", importance_score: 4.5 },
      { id: "teleop_l4_scoring", label: "Teleop L4 Scoring", category: "teleop", importance_score: 3.8 },
      { id: "defense", label: "Defensive Capability", category: "universal", importance_score: 2.6 }
    ]);
  };

  // Fetch picklist analysis data
  const fetchPicklistAnalysis = async (path: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/picklist/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ unified_dataset_path: path })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch picklist analysis');
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setUniversalMetrics(data.universal_metrics || []);
        setGameMetrics(data.game_metrics || []);
        setSuggestedMetrics(data.suggested_metrics || []);
        setMetricsStats(data.metrics_stats || {});
      } else {
        setError(data.message || 'Error in picklist analysis');
      }
    } catch (err) {
      console.error('Error fetching picklist analysis:', err);
      setError('Error loading picklist analysis data');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle strategy prompt submission
  const handlePromptSubmit = async () => {
    if (!strategyPrompt.trim()) {
      setError('Please enter a strategy description');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // For now, mock the response
      setParsedPriorities({
        interpretation: "Looking for a robot with strong L4 scoring and auto capabilities.",
        parsed_metrics: [
          { id: "auto_l4_scoring", weight: 2.0 },
          { id: "teleop_l4_scoring", weight: 1.5 },
          { id: "reliability", weight: 1.0 }
        ]
      });
      
      // Apply the mocked parsed metrics to the current tab
      const currentTab = activeTab;
      let currentPriorities: MetricWeight[];
      let setCurrentPriorities: React.Dispatch<React.SetStateAction<MetricWeight[]>>;
      
      if (currentTab === 'first') {
        currentPriorities = firstPickPriorities;
        setCurrentPriorities = setFirstPickPriorities;
      } else if (currentTab === 'second') {
        currentPriorities = secondPickPriorities;
        setCurrentPriorities = setSecondPickPriorities;
      } else {
        currentPriorities = thirdPickPriorities;
        setCurrentPriorities = setThirdPickPriorities;
      }
      
      // Add the parsed metrics to current priorities (avoiding duplicates)
      const newPriorities = [...currentPriorities];
      const parsedMetrics = [
        { id: "auto_l4_scoring", weight: 2.0 },
        { id: "teleop_l4_scoring", weight: 1.5 },
        { id: "reliability", weight: 1.0 }
      ];
      
      parsedMetrics.forEach(metric => {
        if (!newPriorities.some(p => p.id === metric.id)) {
          newPriorities.push(metric);
        }
      });
      
      setCurrentPriorities(newPriorities);
      setSuccessMessage('Strategy parsed and applied to priorities');
    } catch (err) {
      console.error('Error parsing strategy prompt:', err);
      setError('Error parsing strategy description');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle adding a metric to the current priority list
  const handleAddMetric = (metric: Metric) => {
    const currentPriorities = 
      activeTab === 'first' ? firstPickPriorities :
      activeTab === 'second' ? secondPickPriorities :
      thirdPickPriorities;
    
    // Check if this metric is already in the list
    if (currentPriorities.some(p => p.id === metric.id)) {
      return; // Skip if already added
    }
    
    // Add to the appropriate list
    if (activeTab === 'first') {
      setFirstPickPriorities([...firstPickPriorities, { id: metric.id, weight: 1.0 }]);
    } else if (activeTab === 'second') {
      setSecondPickPriorities([...secondPickPriorities, { id: metric.id, weight: 1.0 }]);
    } else {
      setThirdPickPriorities([...thirdPickPriorities, { id: metric.id, weight: 1.0 }]);
    }
  };
  
  // Handle adjusting the weight of a priority
  const handleWeightChange = (pickType: 'first' | 'second' | 'third', metricId: string, newWeight: number) => {
    if (pickType === 'first') {
      const newPriorities = firstPickPriorities.map(p => 
        p.id === metricId ? { ...p, weight: newWeight } : p
      );
      setFirstPickPriorities(newPriorities);
    } else if (pickType === 'second') {
      const newPriorities = secondPickPriorities.map(p => 
        p.id === metricId ? { ...p, weight: newWeight } : p
      );
      setSecondPickPriorities(newPriorities);
    } else if (pickType === 'third') {
      const newPriorities = thirdPickPriorities.map(p => 
        p.id === metricId ? { ...p, weight: newWeight } : p
      );
      setThirdPickPriorities(newPriorities);
    }
  };

  // Handle removing a priority
  const handleRemovePriority = (pickType: 'first' | 'second' | 'third', metricId: string) => {
    if (pickType === 'first') {
      setFirstPickPriorities(firstPickPriorities.filter(p => p.id !== metricId));
    } else if (pickType === 'second') {
      setSecondPickPriorities(secondPickPriorities.filter(p => p.id !== metricId));
    } else if (pickType === 'third') {
      setThirdPickPriorities(thirdPickPriorities.filter(p => p.id !== metricId));
    }
  };

  // Move a priority up in the list
  const handleMoveUp = (pickType: 'first' | 'second' | 'third', index: number) => {
    if (index === 0) return; // Already at the top
    
    if (pickType === 'first') {
      const newPriorities = [...firstPickPriorities];
      const temp = newPriorities[index];
      newPriorities[index] = newPriorities[index - 1];
      newPriorities[index - 1] = temp;
      setFirstPickPriorities(newPriorities);
    } else if (pickType === 'second') {
      const newPriorities = [...secondPickPriorities];
      const temp = newPriorities[index];
      newPriorities[index] = newPriorities[index - 1];
      newPriorities[index - 1] = temp;
      setSecondPickPriorities(newPriorities);
    } else if (pickType === 'third') {
      const newPriorities = [...thirdPickPriorities];
      const temp = newPriorities[index];
      newPriorities[index] = newPriorities[index - 1];
      newPriorities[index - 1] = temp;
      setThirdPickPriorities(newPriorities);
    }
  };

  // Move a priority down in the list
  const handleMoveDown = (pickType: 'first' | 'second' | 'third', index: number) => {
    const priorities = 
      pickType === 'first' ? firstPickPriorities :
      pickType === 'second' ? secondPickPriorities :
      thirdPickPriorities;
      
    if (index === priorities.length - 1) return; // Already at the bottom
    
    if (pickType === 'first') {
      const newPriorities = [...firstPickPriorities];
      const temp = newPriorities[index];
      newPriorities[index] = newPriorities[index + 1];
      newPriorities[index + 1] = temp;
      setFirstPickPriorities(newPriorities);
    } else if (pickType === 'second') {
      const newPriorities = [...secondPickPriorities];
      const temp = newPriorities[index];
      newPriorities[index] = newPriorities[index + 1];
      newPriorities[index + 1] = temp;
      setSecondPickPriorities(newPriorities);
    } else if (pickType === 'third') {
      const newPriorities = [...thirdPickPriorities];
      const temp = newPriorities[index];
      newPriorities[index] = newPriorities[index + 1];
      newPriorities[index + 1] = temp;
      setThirdPickPriorities(newPriorities);
    }
  };

  // Find metric label by ID
  const getMetricLabel = (metricId: string): string => {
    // Check all metric lists
    const allMetrics = [...universalMetrics, ...gameMetrics, ...suggestedMetrics];
    const metric = allMetrics.find(m => m.id === metricId);
    return metric ? metric.label : metricId;
  };

  // Get active priorities based on current tab
  const getActivePriorities = (): MetricWeight[] => {
    if (activeTab === 'first') return firstPickPriorities;
    if (activeTab === 'second') return secondPickPriorities;
    return thirdPickPriorities;
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Picklist Builder</h1>
      
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {success && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {success}
        </div>
      )}
      
      {!datasetPath ? (
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-300 mb-6">
          <h2 className="text-xl font-bold text-yellow-800 mb-2">No Dataset Found</h2>
          <p className="text-yellow-700 mb-2">
            Please build a unified dataset first before using the picklist builder.
          </p>
          <a 
            href="/workflow"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 inline-block"
          >
            Go to Workflow
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Available Metrics */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-4 mb-6">
              <h2 className="text-xl font-bold mb-4">Strategy Description</h2>
              <p className="text-gray-600 mb-4">
                Describe what you're looking for in a robot partner using natural language.
              </p>
              <textarea
                value={strategyPrompt}
                onChange={(e) => setStrategyPrompt(e.target.value)}
                className="w-full p-2 border rounded h-32 mb-4"
                placeholder="Example: I need a second pick that is good at scoring on L4 and has a reliable auto routine."
              />
              <button
                onClick={handlePromptSubmit}
                disabled={isLoading || !strategyPrompt.trim()}
                className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
              >
                {isLoading ? 'Processing...' : 'Parse Strategy'}
              </button>
              
              {parsedPriorities && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <h3 className="font-semibold text-blue-800 mb-2">Strategy Interpretation</h3>
                  <p className="text-sm text-blue-700">{parsedPriorities.interpretation || 'Strategy analyzed successfully'}</p>
                </div>
              )}
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-xl font-bold mb-4">Available Metrics</h2>
              
              {/* Suggested Metrics Section */}
              {suggestedMetrics.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-semibold text-blue-700 mb-2">Suggested Metrics</h3>
                  {suggestedMetrics.map((metric) => (
                    <div
                      key={metric.id}
                      onClick={() => handleAddMetric(metric)}
                      className="bg-blue-50 border border-blue-200 p-3 rounded mb-2 flex justify-between items-center cursor-pointer hover:bg-blue-100"
                    >
                      <div>
                        <span className="font-medium">{metric.label}</span>
                        <span className="ml-2 text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                          {metric.category}
                        </span>
                      </div>
                      {metric.importance_score !== undefined && (
                        <span className="text-sm text-gray-600">
                          Score: {metric.importance_score.toFixed(2)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {/* Universal Metrics Section */}
              {universalMetrics.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-semibold text-gray-700 mb-2">Universal Metrics</h3>
                  {universalMetrics.map((metric) => (
                    <div
                      key={metric.id}
                      onClick={() => handleAddMetric(metric)}
                      className="bg-white border p-3 rounded mb-2 cursor-pointer hover:bg-gray-50"
                    >
                      <span className="font-medium">{metric.label}</span>
                      <span className="ml-2 text-xs px-2 py-0.5 bg-gray-100 text-gray-800 rounded-full">
                        {metric.category}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Game-Specific Metrics Section */}
              {gameMetrics.length > 0 && (
                <div>
                  <h3 className="font-semibold text-green-700 mb-2">Game Metrics</h3>
                  {gameMetrics.map((metric) => (
                    <div
                      key={metric.id}
                      onClick={() => handleAddMetric(metric)}
                      className="bg-green-50 border border-green-200 p-3 rounded mb-2 cursor-pointer hover:bg-green-100"
                    >
                      <span className="font-medium">{metric.label}</span>
                      <span className="ml-2 text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded-full">
                        {metric.category}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Right Columns - Priority Lists and Team Rankings */}
          <div className="lg:col-span-2">
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
              
              <div className="min-h-[200px] border-2 border-dashed rounded-lg p-4">
                <h3 className="text-lg font-bold mb-4">
                  {activeTab === 'first' 
                    ? 'First Pick Priorities' 
                    : activeTab === 'second' 
                      ? 'Second Pick Priorities' 
                      : 'Third Pick Priorities'
                  }
                </h3>
                
                {getActivePriorities().length === 0 ? (
                  <div className="flex flex-col items-center justify-center text-gray-400 py-8">
                    <p>Click on metrics from the left to add to your priorities</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {getActivePriorities().map((priority, index) => (
                      <div
                        key={`priority-${priority.id}`}
                        className="bg-white border rounded p-3 flex items-center shadow-sm"
                      >
                        <div className="mr-3 font-medium">{index + 1}.</div>
                        <div className="flex-1">
                          <div className="font-medium">{getMetricLabel(priority.id)}</div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <div className="flex items-center">
                            <span className="mr-2 text-sm">Weight:</span>
                            <select
                              value={priority.weight}
                              onChange={(e) => handleWeightChange(
                                activeTab, 
                                priority.id, 
                                parseFloat(e.target.value)
                              )}
                              className="border rounded p-1 text-sm w-16"
                            >
                              <option value="0.5">0.5×</option>
                              <option value="1.0">1.0×</option>
                              <option value="1.5">1.5×</option>
                              <option value="2.0">2.0×</option>
                              <option value="3.0">3.0×</option>
                            </select>
                          </div>
                          
                          <div className="flex space-x-1">
                            <button
                              onClick={() => handleMoveUp(activeTab, index)}
                              disabled={index === 0}
                              className={`p-1 rounded ${index === 0 ? 'text-gray-300' : 'text-blue-500 hover:bg-blue-50'}`}
                              title="Move up"
                            >
                              ↑
                            </button>
                            <button
                              onClick={() => handleMoveDown(activeTab, index)}
                              disabled={index === getActivePriorities().length - 1}
                              className={`p-1 rounded ${index === getActivePriorities().length - 1 ? 'text-gray-300' : 'text-blue-500 hover:bg-blue-50'}`}
                              title="Move down"
                            >
                              ↓
                            </button>
                          </div>
                          
                          <button 
                            onClick={() => handleRemovePriority(activeTab, priority.id)}
                            className="text-red-500 hover:text-red-700 p-1"
                            title="Remove priority"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => {
                    // This would call the picklist generation endpoint
                    alert('Generate Picklist functionality coming in next update');
                  }}
                  disabled={getActivePriorities().length === 0 || isLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
                >
                  Generate Picklist
                </button>
              </div>
            </div>
            
            {/* Team Rankings Section (Placeholder for now) */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-xl font-bold mb-4">Team Rankings</h2>
              <p className="text-gray-600 text-center py-8">
                Team rankings will appear here after generating the picklist.
                <br />
                <span className="text-sm">
                  First, set your priorities in the section above and click "Generate Picklist".
                </span>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PicklistNew;