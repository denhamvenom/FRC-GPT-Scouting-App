// frontend/src/pages/PicklistNew.tsx

import React, { useState, useEffect } from 'react';

// Type definitions
interface Team {
  team_number: number;
  nickname: string;
  stats: Record<string, number>;
  score?: number;
  metrics_contribution?: Array<{
    id: string;
    value: number;
    weighted_value: number;
    metrics_used?: string[];
  }>;
  match_count?: number;
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
  reason?: string;
}

interface ParsedStrategy {
  interpretation: string;
  parsed_metrics: MetricWeight[];
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
  const [parsedPriorities, setParsedPriorities] = useState<ParsedStrategy | null>(null);
  const [isParsingStrategy, setIsParsingStrategy] = useState<boolean>(false);
  
  // State for team rankings
  const [teamRankings, setTeamRankings] = useState<Team[]>([]);
  const [isGeneratingRankings, setIsGeneratingRankings] = useState<boolean>(false);
  
  // State for active tab
  const [activeTab, setActiveTab] = useState<'first' | 'second' | 'third'>('first');
  
  // State for loading, error, success
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Fetch dataset path on load
  useEffect(() => {
    const checkDatasets = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/unified/status?event_key=2025arc&year=2025');
        const data = await response.json();
        
        if (data.status === 'exists' && data.path) {
          setDatasetPath(data.path);
          await fetchPicklistAnalysis(data.path);
        }
      } catch (err) {
        console.error('Error checking datasets:', err);
        setError('Error checking for datasets');
      }
    };
    
    checkDatasets();
  }, []);

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
    
    setIsParsingStrategy(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/picklist/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          unified_dataset_path: datasetPath,
          strategy_prompt: strategyPrompt
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to parse strategy');
      }
      
      const data = await response.json();
      
      if (data.status === 'success' && data.parsed_priorities) {
        setParsedPriorities(data.parsed_priorities);
        
        // Apply the parsed metrics to the current tab
        const currentTab = activeTab;
        let setCurrentPriorities: React.Dispatch<React.SetStateAction<MetricWeight[]>>;
        
        if (currentTab === 'first') {
          setCurrentPriorities = setFirstPickPriorities;
        } else if (currentTab === 'second') {
          setCurrentPriorities = setSecondPickPriorities;
        } else {
          setCurrentPriorities = setThirdPickPriorities;
        }
        
        // Add the parsed metrics to current priorities (avoiding duplicates)
        setCurrentPriorities(prev => {
          const existingIds = new Set(prev.map(p => p.id));
          const newPriorities = [...prev];
          
          for (const metric of data.parsed_priorities.parsed_metrics) {
            if (!existingIds.has(metric.id)) {
              newPriorities.push(metric);
              existingIds.add(metric.id);
            }
          }
          
          return newPriorities;
        });
        
        setSuccessMessage('Strategy parsed and applied to priorities');
      } else {
        setError(data.message || 'Error parsing strategy description');
      }
    } catch (err) {
      console.error('Error parsing strategy prompt:', err);
      setError('Error parsing strategy description');
    } finally {
      setIsParsingStrategy(false);
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
  
    // Generate team rankings
    const generateRankings = async () => {
      const currentPriorities = 
        activeTab === 'first' ? firstPickPriorities :
        activeTab === 'second' ? secondPickPriorities :
        thirdPickPriorities;
        
      if (currentPriorities.length === 0) {
        setError('Please add at least one priority before generating rankings');
        return;
      }
      
      setIsGeneratingRankings(true);
      setError(null);
      
      try {
        const response = await fetch('http://localhost:8000/api/picklist/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            unified_dataset_path: datasetPath,
            priorities: currentPriorities
          })
        });
        
        if (!response.ok) {
          throw new Error('Failed to generate team rankings');
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.team_rankings) {
          setTeamRankings(data.team_rankings);
          setSuccessMessage('Team rankings generated successfully');
        } else {
          setError(data.message || 'Error generating team rankings');
        }
      } catch (err) {
        console.error('Error generating team rankings:', err);
        setError('Error generating team rankings');
      } finally {
        setIsGeneratingRankings(false);
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
  
    if (isLoading && !universalMetrics.length) {
      return <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>;
    }
  
    return (
      <div className="max-w-6xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Picklist Builder</h1>
        
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
                disabled={isParsingStrategy || !strategyPrompt.trim()}
                className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
              >
                {isParsingStrategy ? 'Processing...' : 'Parse Strategy'}
              </button>
              
              {parsedPriorities && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <h3 className="font-semibold text-blue-800 mb-2">Strategy Interpretation</h3>
                  <p className="text-sm text-blue-700 mb-3">{parsedPriorities.interpretation}</p>
                  
                  {parsedPriorities.parsed_metrics.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-blue-800 mb-1">Identified Metrics:</h4>
                      <ul className="text-xs space-y-1">
                        {parsedPriorities.parsed_metrics.map((metric, idx) => (
                          <li key={idx} className="flex justify-between">
                            <span>{getMetricLabel(metric.id)}</span>
                            <span className="text-blue-600">Weight: {metric.weight.toFixed(1)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
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
                          {priority.reason && (
                            <div className="text-xs text-gray-500">{priority.reason}</div>
                          )}
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
                  onClick={generateRankings}
                  disabled={getActivePriorities().length === 0 || isGeneratingRankings}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
                >
                  {isGeneratingRankings ? 'Generating...' : 'Generate Rankings'}
                </button>
              </div>
            </div>
            
            {/* Team Rankings Section */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Team Rankings</h2>
              </div>
              
              {teamRankings.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full border">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="border px-4 py-2 text-left">Rank</th>
                        <th className="border px-4 py-2 text-left">Team</th>
                        <th className="border px-4 py-2 text-left">Score</th>
                        <th className="border px-4 py-2 text-left">Key Metrics</th>
                      </tr>
                    </thead>
                    <tbody>
                      {teamRankings.map((team, index) => (
                        <tr key={team.team_number} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                          <td className="border px-4 py-2 font-bold">{index + 1}</td>
                          <td className="border px-4 py-2">
                            <div className="font-medium">{team.team_number}</div>
                            <div className="text-sm text-gray-600">{team.nickname}</div>
                          </td>
                          <td className="border px-4 py-2 font-mono">
                            {team.score?.toFixed(2) || '0.00'}
                          </td>
                          <td className="border px-4 py-2">
                            {team.metrics_contribution && team.metrics_contribution.length > 0 ? (
                              <div className="grid grid-cols-2 gap-1">
                                {team.metrics_contribution.map((metric, mIdx) => (
                                  <div key={mIdx} className="text-xs bg-blue-50 p-1 rounded">
                                    <span className="font-medium">{getMetricLabel(metric.id)}:</span> {metric.value.toFixed(2)}
                                    <span className="text-blue-600"> ({metric.weighted_value.toFixed(2)})</span>
                                    
                                    {metric.metrics_used && metric.metrics_used.length > 0 && (
                                      <div className="text-xs text-gray-500 mt-0.5">
                                        Using: {metric.metrics_used.slice(0, 2).join(', ')}
                                        {metric.metrics_used.length > 2 && '...'}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <span className="text-gray-500">No metrics data</span>
                            )}
                            <div className="text-xs text-gray-500 mt-1">
                              From {team.match_count || 0} matches
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 text-center text-gray-500">
                  {isGeneratingRankings ? (
                    <div className="flex justify-center items-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500"></div>
                      <span className="ml-2">Generating rankings...</span>
                    </div>
                  ) : (
                    <>
                      <p>Team rankings will appear here after clicking "Generate Rankings".</p>
                      <p className="text-sm mt-2">
                        First, set your priorities in the section above.
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PicklistNew;