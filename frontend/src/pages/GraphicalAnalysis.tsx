import React, { useState, useEffect } from 'react';
import { useUnifiedData, getAvailableTeams } from '../hooks/useUnifiedData';
import { useFieldMetadata } from '../hooks/useFieldMetadata';
import { 
  getAvailableMetrics, 
  processUnifiedDataForChart, 
  validateChartData 
} from '../utils/chartDataProcessing';
import { 
  GraphicalAnalysisState, 
  MetricsByCategory, 
  METRIC_PRESETS, 
  DEFAULT_SETTINGS 
} from '../types/graphicalAnalysis';
import RadarChartVisualization from '../components/RadarChartVisualization';
import { apiUrl, fetchWithNgrokHeaders } from '../config';

interface GraphicalAnalysisProps {}

const GraphicalAnalysis: React.FC<GraphicalAnalysisProps> = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [eventKey, setEventKey] = useState<string>('');
  const [setupLoading, setSetupLoading] = useState<boolean>(true);
  
  // State for metric and team selection
  const [state, setState] = useState<GraphicalAnalysisState>({
    selectedMetrics: [],
    selectedTeams: [],
    normalizationMode: 'by_global_max',
    aggregationMode: 'average',
    showDataTable: false,
    expandedCategories: new Set(['autonomous', 'teleop', 'endgame']),
    excludeOutliers: {
      enabled: false,
      excludeLowest: 1,
      excludeHighest: 1
    }
  });
  
  const { data: unifiedData, loading: dataLoading, error: dataError } = useUnifiedData(eventKey);
  const { 
    fieldMetadata, 
    loading: metadataLoading, 
    error: metadataError, 
    getNumericMetrics, 
    getMetricsByCategory 
  } = useFieldMetadata();

  // Handler functions for state updates
  const handleMetricToggle = (metric: string) => {
    setState(prev => ({
      ...prev,
      selectedMetrics: prev.selectedMetrics.includes(metric)
        ? prev.selectedMetrics.filter(m => m !== metric)
        : [...prev.selectedMetrics, metric]
    }));
  };

  const handleTeamToggle = (teamNumber: number) => {
    setState(prev => ({
      ...prev,
      selectedTeams: prev.selectedTeams.includes(teamNumber)
        ? prev.selectedTeams.filter(t => t !== teamNumber)
        : prev.selectedTeams.length < 6 
          ? [...prev.selectedTeams, teamNumber]
          : prev.selectedTeams
    }));
  };

  const handleCategoryToggle = (category: string) => {
    setState(prev => {
      const newExpanded = new Set(prev.expandedCategories);
      if (newExpanded.has(category)) {
        newExpanded.delete(category);
      } else {
        newExpanded.add(category);
      }
      return {
        ...prev,
        expandedCategories: newExpanded
      };
    });
  };

  const handlePresetSelect = (preset: typeof METRIC_PRESETS[0]) => {
    setState(prev => ({
      ...prev,
      selectedMetrics: preset.metrics
    }));
  };

  const handleClearSelections = () => {
    setState(prev => ({
      ...prev,
      selectedMetrics: [],
      selectedTeams: []
    }));
  };

  // Get processed data for display
  const availableTeams = unifiedData ? getAvailableTeams(unifiedData) : [];
  const availableMetrics = unifiedData ? getAvailableMetrics(unifiedData) : [];
  const metricsByCategory = getMetricsByCategory();

  // Process chart data when selections change
  const chartProcessingResult = React.useMemo(() => {
    if (!unifiedData || state.selectedMetrics.length === 0 || state.selectedTeams.length === 0) {
      console.log('Chart processing skipped:', {
        hasUnifiedData: !!unifiedData,
        selectedMetrics: state.selectedMetrics.length,
        selectedTeams: state.selectedTeams.length
      });
      return null;
    }

    console.log('Processing chart data:', {
      selectedMetrics: state.selectedMetrics,
      selectedTeams: state.selectedTeams,
      normalizationMode: state.normalizationMode,
      aggregationMode: state.aggregationMode,
      excludeOutliers: state.excludeOutliers
    });

    try {
      const result = processUnifiedDataForChart(unifiedData, {
        selectedMetrics: state.selectedMetrics,
        selectedTeams: state.selectedTeams,
        normalizationMode: state.normalizationMode,
        aggregationMode: state.aggregationMode,
        excludeOutliers: state.excludeOutliers
      });
      
      console.log('Chart data processed successfully:', {
        chartDataPoints: result.chartData.length,
        teamMetrics: result.teamMetrics.length
      });
      
      return result;
    } catch (error) {
      console.error('Error processing chart data:', error);
      return null;
    }
  }, [unifiedData, state.selectedMetrics, state.selectedTeams, state.normalizationMode, state.aggregationMode, state.excludeOutliers]);

  // Build team names mapping for chart
  const teamNames = React.useMemo(() => {
    const names: { [teamNumber: number]: string } = {};
    availableTeams.forEach(team => {
      names[team.team_number] = `Team ${team.team_number} - ${team.nickname}`;
    });
    return names;
  }, [availableTeams]);

  // Fetch event key from setup on component mount
  useEffect(() => {
    const fetchEventInfo = async () => {
      setSetupLoading(true);
      try {
        const response = await fetchWithNgrokHeaders(apiUrl("/api/setup/info"));
        
        if (response.ok) {
          const data = await response.json();
          
          if (data.status === "success" && data.event_key) {
            setEventKey(data.event_key);
            console.log('Using event key from setup:', data.event_key, `(${data.year})`);
          } else {
            setError('No active event found. Please configure an event in Setup first.');
          }
        } else {
          setError('Unable to fetch event information. Please check your setup.');
        }
      } catch (err) {
        console.error("Failed to fetch event info:", err);
        setError('Failed to connect to backend. Please ensure the server is running.');
      } finally {
        setSetupLoading(false);
      }
    };

    fetchEventInfo();
  }, []);

  // Show loading state
  if (loading || dataLoading || metadataLoading || setupLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            <span className="ml-4 text-gray-600">
              {setupLoading ? 'Loading event configuration...' : 
               dataLoading ? 'Loading team data...' : 
               metadataLoading ? 'Loading field metadata...' : 
               'Loading graphical analysis...'}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error || dataError || metadataError) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error || dataError || metadataError}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Graphical Analysis</h1>
        <p className="text-gray-600">
          Visualize and compare team performance using Multi-Axis Radar Charts
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          <span className="block sm:inline">{successMessage}</span>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Panel */}
        <div className="lg:col-span-1 order-2 lg:order-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Analysis Controls</h2>
            
            {/* Event Information */}
            {unifiedData && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Event Information</h3>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-600">
                    <strong>Event:</strong> {unifiedData.event_key}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>Year:</strong> {unifiedData.year}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>Teams:</strong> {unifiedData.teams ? Object.keys(unifiedData.teams).length : 0}
                  </p>
                </div>
              </div>
            )}

            {/* Metric Presets */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Quick Presets</h3>
              <div className="grid grid-cols-1 gap-2">
                {METRIC_PRESETS.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => handlePresetSelect(preset)}
                    className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded text-left transition-colors"
                  >
                    <div className="font-medium">{preset.name}</div>
                    <div className="text-xs text-gray-500">{preset.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Metric Selection */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Metric Selection ({state.selectedMetrics.length} selected)
              </h3>
              <div className="max-h-64 overflow-y-auto border rounded p-2">
                {Object.entries(metricsByCategory).map(([category, metrics]) => (
                  <div key={category} className="mb-2">
                    <button
                      onClick={() => handleCategoryToggle(category)}
                      className="flex items-center w-full px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
                    >
                      <svg
                        className={`w-4 h-4 mr-2 transition-transform ${
                          state.expandedCategories.has(category) ? 'rotate-90' : ''
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      {category.charAt(0).toUpperCase() + category.slice(1)} ({metrics.length})
                    </button>
                    {state.expandedCategories.has(category) && (
                      <div className="ml-6 mt-1 space-y-1">
                        {metrics.map(metric => (
                          <label key={metric.field_name} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={state.selectedMetrics.includes(metric.field_name)}
                              onChange={() => handleMetricToggle(metric.field_name)}
                              className="mr-2"
                            />
                            <span className="text-sm text-gray-600">{metric.display_label}</span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Team Selection */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Team Selection ({state.selectedTeams.length}/6 selected)
              </h3>
              <div className="max-h-48 overflow-y-auto border rounded p-2">
                {availableTeams.map(team => (
                  <label key={team.team_number} className="flex items-center p-2 hover:bg-gray-50 rounded">
                    <input
                      type="checkbox"
                      checked={state.selectedTeams.includes(team.team_number)}
                      onChange={() => handleTeamToggle(team.team_number)}
                      disabled={!state.selectedTeams.includes(team.team_number) && state.selectedTeams.length >= 6}
                      className="mr-3"
                    />
                    <div>
                      <div className="text-sm font-medium">{team.team_number}</div>
                      <div className="text-xs text-gray-500">{team.nickname}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Chart Controls */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Chart Options</h3>
              <div className="space-y-3">
                <div>
                  <label className="flex items-center text-sm mb-1">
                    <span className="text-gray-600 mr-2">Normalization:</span>
                    <select
                      value={state.normalizationMode}
                      onChange={(e) => setState(prev => ({ ...prev, normalizationMode: e.target.value as any }))}
                      className="text-xs border rounded px-2 py-1"
                    >
                      <option value="by_global_max">Global Max</option>
                      <option value="by_percentile">95th Percentile</option>
                      <option value="by_team_max">Team Max</option>
                      <option value="none">Raw Values</option>
                    </select>
                  </label>
                  <p className="text-xs text-gray-500 ml-2">
                    {state.normalizationMode === 'by_global_max' && 'Scale to highest value across all teams (0-100)'}
                    {state.normalizationMode === 'by_percentile' && 'Scale to 95th percentile for stable comparison'}
                    {state.normalizationMode === 'by_team_max' && 'Scale each team to their own maximum'}
                    {state.normalizationMode === 'none' && 'Show actual raw values without scaling'}
                  </p>
                </div>
                
                <div>
                  <label className="flex items-center text-sm mb-1">
                    <span className="text-gray-600 mr-2">Aggregation:</span>
                    <select
                      value={state.aggregationMode}
                      onChange={(e) => setState(prev => ({ ...prev, aggregationMode: e.target.value as any }))}
                      className="text-xs border rounded px-2 py-1"
                    >
                      <option value="average">Average</option>
                      <option value="total">Total</option>
                      <option value="max">Maximum</option>
                      <option value="last_match">Last Match</option>
                    </select>
                  </label>
                  <p className="text-xs text-gray-500 ml-2">
                    {state.aggregationMode === 'average' && 'Average performance across all matches'}
                    {state.aggregationMode === 'total' && 'Sum of all match values'}
                    {state.aggregationMode === 'max' && 'Best single match performance'}
                    {state.aggregationMode === 'last_match' && 'Most recent match data only'}
                  </p>
                </div>

                <div>
                  <label className="flex items-center text-sm mb-1">
                    <input
                      type="checkbox"
                      checked={state.excludeOutliers.enabled}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        excludeOutliers: { ...prev.excludeOutliers, enabled: e.target.checked }
                      }))}
                      className="mr-2"
                    />
                    <span className="text-gray-600">Exclude Outlier Matches</span>
                  </label>
                  
                  {state.excludeOutliers.enabled && (
                    <div className="ml-4 mt-2 space-y-2">
                      <div className="flex items-center space-x-4">
                        <label className="flex items-center text-xs">
                          <span className="text-gray-600 mr-1">Exclude lowest:</span>
                          <input
                            type="number"
                            min="0"
                            max="5"
                            value={state.excludeOutliers.excludeLowest}
                            onChange={(e) => setState(prev => ({ 
                              ...prev, 
                              excludeOutliers: { 
                                ...prev.excludeOutliers, 
                                excludeLowest: parseInt(e.target.value) || 0 
                              }
                            }))}
                            className="w-16 text-xs border rounded px-1 py-1"
                          />
                          <span className="text-gray-500 ml-1">matches</span>
                        </label>
                        
                        <label className="flex items-center text-xs">
                          <span className="text-gray-600 mr-1">Exclude highest:</span>
                          <input
                            type="number"
                            min="0"
                            max="5"
                            value={state.excludeOutliers.excludeHighest}
                            onChange={(e) => setState(prev => ({ 
                              ...prev, 
                              excludeOutliers: { 
                                ...prev.excludeOutliers, 
                                excludeHighest: parseInt(e.target.value) || 0 
                              }
                            }))}
                            className="w-16 text-xs border rounded px-1 py-1"
                          />
                          <span className="text-gray-500 ml-1">matches</span>
                        </label>
                      </div>
                    </div>
                  )}
                  
                  <p className="text-xs text-gray-500 ml-2">
                    {state.excludeOutliers.enabled 
                      ? `Remove ${state.excludeOutliers.excludeLowest} worst and ${state.excludeOutliers.excludeHighest} best matches for more consistent analysis`
                      : 'Include all matches in analysis'}
                  </p>
                </div>
              </div>
            </div>

            {/* Clear Selections */}
            <div className="mb-4">
              <button
                onClick={handleClearSelections}
                className="w-full px-4 py-2 bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors"
              >
                Clear All Selections
              </button>
            </div>
          </div>
        </div>

        {/* Chart Panel */}
        <div className="lg:col-span-2 order-1 lg:order-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Multi-Axis Radar Chart</h2>
            
            {/* Current Selections Summary */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="text-sm font-medium text-blue-800 mb-2">Current Selections</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-blue-600 font-medium mb-1">Selected Metrics ({state.selectedMetrics.length})</p>
                  {state.selectedMetrics.length > 0 ? (
                    <div className="text-xs text-blue-700">
                      {state.selectedMetrics.slice(0, 3).map(metric => 
                        metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                      ).join(', ')}
                      {state.selectedMetrics.length > 3 && ` and ${state.selectedMetrics.length - 3} more...`}
                    </div>
                  ) : (
                    <div className="text-xs text-blue-500 italic">No metrics selected</div>
                  )}
                </div>
                <div>
                  <p className="text-xs text-blue-600 font-medium mb-1">Selected Teams ({state.selectedTeams.length})</p>
                  {state.selectedTeams.length > 0 ? (
                    <div className="text-xs text-blue-700">
                      {state.selectedTeams.slice(0, 3).join(', ')}
                      {state.selectedTeams.length > 3 && ` and ${state.selectedTeams.length - 3} more...`}
                    </div>
                  ) : (
                    <div className="text-xs text-blue-500 italic">No teams selected</div>
                  )}
                </div>
              </div>
            </div>

            {/* Radar Chart Visualization */}
            {state.selectedMetrics.length > 0 && state.selectedTeams.length > 0 ? (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <RadarChartVisualization
                  chartData={chartProcessingResult?.chartData || []}
                  selectedTeams={state.selectedTeams}
                  teamNames={teamNames}
                  teamMetrics={chartProcessingResult?.teamMetrics || []}
                  selectedMetrics={state.selectedMetrics}
                  loading={loading}
                  error={chartProcessingResult === null ? 'Unable to process chart data' : null}
                  height={500}
                />
              </div>
            ) : (
              <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <div className="text-gray-400 mb-4">
                  <svg
                    className="mx-auto h-16 w-16"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Multi-Axis Radar Chart</h3>
                <p className="text-gray-500 mb-4">
                  Select metrics and teams to visualize performance comparisons
                </p>
                <div className="text-sm text-gray-400 space-y-1">
                  <p>• Choose metrics from the categories on the left</p>
                  <p>• Select 1-6 teams for comparison</p>
                  <p>• Use presets for quick metric selection</p>
                  <p>• Interactive tooltips and legend available</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Debug Information */}
      {process.env.NODE_ENV === 'development' && unifiedData && (
        <div className="mt-6 bg-gray-100 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Debug Information</h3>
          <div className="text-xs text-gray-600 font-mono">
            <p>Event Key: {unifiedData.event_key}</p>
            <p>Teams Count: {unifiedData.teams ? Object.keys(unifiedData.teams).length : 0}</p>
            <p>Data Structure: {typeof unifiedData}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphicalAnalysis;