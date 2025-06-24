// frontend/src/pages/Workflow.tsx

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface DatasetStatus {
  status: 'exists' | 'not_found';
  path?: string;
  last_modified?: string;
}

interface ValidationSummary {
  total_missing_matches: number;
  total_missing_superscouting: number;
  total_outliers: number;
  has_issues: boolean;
}

function Workflow() {
  const [year, setYear] = useState<number>(2025);
  const [eventKey, setEventKey] = useState<string>('2025arc');
  const [isBuilding, setIsBuilding] = useState<boolean>(false);
  const [datasetStatus, setDatasetStatus] = useState<DatasetStatus | null>(null);
  const [validationSummary, setValidationSummary] = useState<ValidationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check dataset status on load and when year/event changes
  useEffect(() => {
    checkDatasetStatus();
  }, [year, eventKey]);

  // Check if dataset exists
  const checkDatasetStatus = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/unified/status?event_key=${eventKey}&year=${year}`);
      const data = await response.json();
      setDatasetStatus(data);
      
      // If dataset exists, get validation summary
      if (data.status === 'exists') {
        getValidationSummary(data.path);
      } else {
        setValidationSummary(null);
      }
    } catch (err) {
      console.error('Error checking dataset status:', err);
      setError('Error checking dataset status');
    }
  };

  // Get validation summary
  const getValidationSummary = async (datasetPath: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/validate/enhanced?unified_dataset_path=${encodeURIComponent(datasetPath)}`);
      const data = await response.json();
      
      if (data.summary) {
        setValidationSummary(data.summary);
      }
    } catch (err) {
      console.error('Error getting validation summary:', err);
      setError('Error loading validation data');
    }
  };

  // Build or rebuild the dataset
  const buildUnifiedDataset = async (forceRebuild: boolean = false) => {
    setIsBuilding(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/unified/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_key: eventKey,
          year: year,
          force_rebuild: forceRebuild
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        await checkDatasetStatus();
      } else {
        setError(data.detail || 'Error building unified dataset');
      }
    } catch (err) {
      console.error('Error building dataset:', err);
      setError('Error connecting to server');
    } finally {
      setIsBuilding(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">FRC Scouting Workflow</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Step 1: Learning/Setup */}
        <div className="bg-white p-5 rounded-lg shadow-md border-l-4 border-blue-500">
          <h2 className="text-xl font-bold">1. Learning Setup</h2>
          <p className="text-gray-600 mb-4">Upload game manual and define scouting parameters.</p>
          <Link
            to="/setup"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 inline-block"
          >
            Go to Setup
          </Link>
        </div>

        {/* Step 2: Field Selection */}
        <div className="bg-white p-5 rounded-lg shadow-md border-l-4 border-green-500">
          <h2 className="text-xl font-bold">2. Field Selection</h2>
          <p className="text-gray-600 mb-4">Map scouting sheet headers and define critical fields.</p>
          <Link
            to="/field-selection"
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 inline-block"
          >
            Field Selection
          </Link>
        </div>

        {/* Step 3: Data Validation */}
        <div className="bg-white p-5 rounded-lg shadow-md border-l-4 border-amber-500">
          <h2 className="text-xl font-bold">3. Data Validation</h2>
          <p className="text-gray-600 mb-4">Find missing data and statistical outliers.</p>
          <Link
            to="/validation"
            className={`px-4 py-2 ${datasetStatus?.status === 'exists'
              ? 'bg-amber-600 hover:bg-amber-700'
              : 'bg-gray-400 cursor-not-allowed'} text-white rounded inline-block`}
            onClick={(e) => {
              if (datasetStatus?.status !== 'exists') {
                e.preventDefault();
                alert('Build the unified dataset first before validation');
              }
            }}
          >
            Go to Validation
          </Link>
        </div>
      </div>
      
      {/* Unified Dataset Builder */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-2xl font-bold mb-4">Unified Dataset Builder</h2>
        <p className="mb-4 text-gray-600">
          Build or update the unified dataset that combines scouting data, match schedule, and team metrics.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block mb-2 font-semibold">Year</label>
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
            <label className="block mb-2 font-semibold">Event Key</label>
            <input
              type="text"
              value={eventKey}
              onChange={(e) => setEventKey(e.target.value)}
              placeholder="e.g., 2025arc"
              className="w-full p-2 border rounded"
            />
          </div>
        </div>
        
        {error && (
          <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}
        
        {datasetStatus && (
          <div className={`p-3 mb-4 rounded ${
            datasetStatus.status === 'exists' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
          }`}>
            {datasetStatus.status === 'exists' ? (
              <>
                <p className="font-semibold">Dataset exists</p>
                <p>Path: {datasetStatus.path}</p>
                <p>Last modified: {datasetStatus.last_modified}</p>
                {validationSummary && (
                  <div className="mt-2 pt-2 border-t border-green-200">
                    <p className="font-semibold">Validation Summary:</p>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      <div className={`p-2 rounded ${validationSummary.total_missing_matches > 0 ? 'bg-red-200' : 'bg-green-200'}`}>
                        <span className="font-bold text-lg">{validationSummary.total_missing_matches}</span>
                        <span className="block text-sm">Missing Matches</span>
                      </div>
                      <div className={`p-2 rounded ${validationSummary.total_missing_superscouting > 0 ? 'bg-red-200' : 'bg-green-200'}`}>
                        <span className="font-bold text-lg">{validationSummary.total_missing_superscouting}</span>
                        <span className="block text-sm">Missing SuperScouting</span>
                      </div>
                      <div className={`p-2 rounded ${validationSummary.total_outliers > 0 ? 'bg-red-200' : 'bg-green-200'}`}>
                        <span className="font-bold text-lg">{validationSummary.total_outliers}</span>
                        <span className="block text-sm">Outliers</span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p>No dataset found for event key "{eventKey}"</p>
            )}
          </div>
        )}
        
        <div className="flex space-x-4">
          <button
            onClick={() => buildUnifiedDataset(false)}
            disabled={isBuilding || datasetStatus?.status === 'exists'}
            className={`px-4 py-2 rounded ${
              isBuilding || datasetStatus?.status === 'exists'
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white`}
          >
            {isBuilding ? 'Building...' : 'Build Dataset'}
          </button>
          
          <button
            onClick={() => buildUnifiedDataset(true)}
            disabled={isBuilding}
            className={`px-4 py-2 rounded ${
              isBuilding
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-amber-600 hover:bg-amber-700'
            } text-white`}
          >
            {isBuilding ? 'Rebuilding...' : 'Rebuild Dataset'}
          </button>
        </div>
      </div>
      
      {/* Workflow Steps */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-4">Workflow Steps</h2>
        
        <ol className="list-decimal list-inside space-y-6">
          <li className="pb-4 border-b">
            <span className="font-semibold text-lg">Upload game manual and setup</span>
            <p className="ml-6 mt-2 text-gray-600">
              Go to the Setup page to upload the game manual and define event parameters.
              GPT will analyze the manual to extract relevant scouting variables.
            </p>
          </li>
          
          <li className="pb-4 border-b">
            <span className="font-semibold text-lg">Configure field selection</span>
            <p className="ml-6 mt-2 text-gray-600">
              Go to the Field Selection page to map your spreadsheet headers to standardized variables
              and define critical fields. This step automatically builds the dataset when completed.
            </p>
          </li>

          <li className="pb-4 border-b">
            <span className="font-semibold text-lg">Dataset building (automatic)</span>
            <p className="ml-6 mt-2 text-gray-600">
              The unified dataset is built automatically after field selection. It combines your scouting data
              with match information from The Blue Alliance and team metrics from Statbotics.
              You can also use the controls above to manually rebuild it if needed.
            </p>
          </li>
          
          <li className="pb-4 border-b">
            <span className="font-semibold text-lg">Validate data quality</span>
            <p className="ml-6 mt-2 text-gray-600">
              Go to the Validation page to check for missing data and statistical outliers.
              You can apply corrections to improve data quality.
            </p>
          </li>
          
          <li>
            <span className="font-semibold text-lg">Generate pick lists</span>
            <p className="ml-6 mt-2 text-gray-600">
              Once data is validated, generate ranked team lists based on performance metrics and strategy priorities.
            </p>
          </li>
        </ol>
      </div>
    </div>
  );
}

export default Workflow;