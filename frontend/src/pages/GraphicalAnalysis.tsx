import React, { useState, useEffect } from 'react';
import { useUnifiedData } from '../hooks/useUnifiedData';

interface GraphicalAnalysisProps {}

const GraphicalAnalysis: React.FC<GraphicalAnalysisProps> = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const { data: unifiedData, loading: dataLoading, error: dataError } = useUnifiedData();

  useEffect(() => {
    // Initialize component
    setLoading(false);
    setError(null);
  }, []);

  // Show loading state
  if (loading || dataLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            <span className="ml-4 text-gray-600">Loading graphical analysis...</span>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error || dataError) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error || dataError}</span>
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
        <div className="lg:col-span-1">
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

            {/* Metric Selection Placeholder */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Metric Selection</h3>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-500 italic">
                  Metric selection will be implemented in Sprint 2
                </p>
              </div>
            </div>

            {/* Team Selection Placeholder */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Team Selection</h3>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-500 italic">
                  Team selection will be implemented in Sprint 2
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Chart Panel */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Radar Chart Visualization</h2>
            
            {/* Chart Placeholder */}
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
              <h3 className="text-lg font-medium text-gray-700 mb-2">Radar Chart</h3>
              <p className="text-gray-500 mb-4">
                Multi-axis radar chart will be implemented in Sprint 3
              </p>
              <p className="text-sm text-gray-400">
                Select metrics and teams from the controls panel to generate visualizations
              </p>
            </div>
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