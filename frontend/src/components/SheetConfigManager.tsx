// frontend/src/components/SheetConfigManager.tsx

import React, { useState, useEffect } from 'react';

// Define interface for sheet configuration
interface SheetConfig {
  id: number;
  name: string;
  spreadsheet_id: string;
  match_scouting_sheet: string;
  pit_scouting_sheet?: string;
  super_scouting_sheet?: string;
  event_key: string;
  year: number;
  is_active: boolean;
  created_at: string;
}

interface SheetConfigManagerProps {
  currentEventKey?: string;
  currentYear?: number;
  onConfigurationChange?: () => void;
}

const SheetConfigManager: React.FC<SheetConfigManagerProps> = ({
  currentEventKey,
  currentYear,
  onConfigurationChange
}) => {
  // State
  const [configurations, setConfigurations] = useState<SheetConfig[]>([]);
  const [availableSheets, setAvailableSheets] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [showConfigForm, setShowConfigForm] = useState<boolean>(false);
  const [configName, setConfigName] = useState<string>("");
  const [spreadsheetId, setSpreadsheetId] = useState<string>("");
  const [spreadsheetTitle, setSpreadsheetTitle] = useState<string>("");
  const [matchScoutingSheet, setMatchScoutingSheet] = useState<string>("");
  const [pitScoutingSheet, setPitScoutingSheet] = useState<string>("");
  const [superScoutingSheet, setSuperScoutingSheet] = useState<string>("");
  const [testingConnection, setTestingConnection] = useState<boolean>(false);
  const [connectionStatus, setConnectionStatus] = useState<'none' | 'success' | 'error'>('none');
  const [connectionError, setConnectionError] = useState<string | null>(null);
  
  // Load configurations when the component mounts
  useEffect(() => {
    fetchConfigurations();
  }, [currentEventKey, currentYear]);
  
  const fetchConfigurations = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let url = 'http://localhost:8000/api/sheet-config/list';
      
      // Add filters if provided
      if (currentEventKey || currentYear) {
        const params = new URLSearchParams();
        if (currentEventKey) params.append('event_key', currentEventKey);
        if (currentYear) params.append('year', currentYear.toString());
        url += `?${params.toString()}`;
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch configurations: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setConfigurations(data.configurations || []);
      } else {
        setError(data.message || 'Failed to fetch configurations');
      }
    } catch (err: any) {
      setError(`Error: ${err.message || 'Unknown error'}`);
      console.error('Failed to fetch configurations:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const testConnection = async () => {
    // Modified to allow testing with just the Spreadsheet ID
    if (!spreadsheetId) {
      setConnectionStatus('error');
      setConnectionError('Please enter a Google Spreadsheet ID');
      return;
    }

    setTestingConnection(true);
    setConnectionStatus('none');
    setConnectionError(null);

    try {
      const requestBody: any = {
        spreadsheet_id: spreadsheetId
      };

      // Include sheet name if provided, but not required
      if (matchScoutingSheet) {
        requestBody.sheet_name = matchScoutingSheet;
      }

      const response = await fetch('http://localhost:8000/api/sheet-config/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (data.status === 'success') {
        setConnectionStatus('success');
        setSpreadsheetTitle(data.spreadsheet_title || 'Unknown');

        // Handle available sheets - they might be in different places depending on the response structure
        if (data.available_sheets) {
          setAvailableSheets(data.available_sheets);
        } else if (data.sheet_names) {
          setAvailableSheets(data.sheet_names);
        } else {
          setAvailableSheets([]);
        }
      } else {
        setConnectionStatus('error');
        setConnectionError(data.message || 'Failed to connect to spreadsheet');
      }
    } catch (err: any) {
      setConnectionStatus('error');
      setConnectionError(`Error: ${err.message || 'Unknown error'}`);
      console.error('Failed to test connection:', err);
    } finally {
      setTestingConnection(false);
    }
  };
  
  const handleCreateConfig = async () => {
    // Validate required fields
    const missingFields = [];
    if (!configName) missingFields.push('Configuration Name');
    if (!spreadsheetId) missingFields.push('Spreadsheet ID');
    if (!matchScoutingSheet) missingFields.push('Match Scouting Sheet');

    if (missingFields.length > 0) {
      setError(`Please fill in the required fields: ${missingFields.join(', ')}`);
      return;
    }
    
    if (!currentEventKey || !currentYear) {
      setError('No active event found');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/sheet-config/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: configName,
          spreadsheet_id: spreadsheetId,
          match_scouting_sheet: matchScoutingSheet,
          pit_scouting_sheet: pitScoutingSheet || undefined,
          super_scouting_sheet: superScoutingSheet || undefined,
          event_key: currentEventKey,
          year: currentYear,
          set_active: true
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccess(`Successfully ${data.is_new ? 'created' : 'updated'} configuration "${configName}"`);
        
        // Reset form
        setShowConfigForm(false);
        setConfigName('');
        setSpreadsheetId('');
        setSpreadsheetTitle('');
        setMatchScoutingSheet('');
        setPitScoutingSheet('');
        setSuperScoutingSheet('');
        setConnectionStatus('none');
        
        // Refresh configurations
        fetchConfigurations();
        
        // Notify parent
        if (onConfigurationChange) {
          onConfigurationChange();
        }
      } else {
        setError(data.message || 'Failed to create configuration');
      }
    } catch (err: any) {
      setError(`Error: ${err.message || 'Unknown error'}`);
      console.error('Failed to create configuration:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSetActive = async (configId: number) => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/sheet-config/set-active', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config_id: configId
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccess(data.message || 'Successfully set active configuration');
        
        // Refresh configurations
        fetchConfigurations();
        
        // Notify parent
        if (onConfigurationChange) {
          onConfigurationChange();
        }
      } else {
        setError(data.message || 'Failed to set active configuration');
      }
    } catch (err: any) {
      setError(`Error: ${err.message || 'Unknown error'}`);
      console.error('Failed to set active configuration:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteConfig = async (configId: number, configName: string) => {
    if (!window.confirm(`Are you sure you want to delete the configuration "${configName}"?`)) {
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/sheet-config/${configId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccess(data.message || 'Successfully deleted configuration');
        
        // Refresh configurations
        fetchConfigurations();
        
        // Notify parent
        if (onConfigurationChange) {
          onConfigurationChange();
        }
      } else {
        setError(data.message || 'Failed to delete configuration');
      }
    } catch (err: any) {
      setError(`Error: ${err.message || 'Unknown error'}`);
      console.error('Failed to delete configuration:', err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Google Sheets Configuration</h2>
        
        {!showConfigForm && (
          <button
            onClick={() => setShowConfigForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            disabled={!currentEventKey || !currentYear}
            title={!currentEventKey || !currentYear ? 'Please select an event first' : 'Add new configuration'}
          >
            Add Configuration
          </button>
        )}
      </div>
      
      {/* Error and success messages */}
      {error && (
        <div className="p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {success && (
        <div className="p-3 bg-green-100 text-green-700 rounded">
          {success}
        </div>
      )}
      
      {/* Configuration form */}
      {showConfigForm && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="font-semibold mb-3">Add/Edit Sheet Configuration</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Configuration Name*</label>
              <input
                type="text"
                value={configName}
                onChange={(e) => setConfigName(e.target.value)}
                placeholder="e.g. Match Scouting 2025"
                className="w-full p-2 border rounded"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Google Spreadsheet ID*</label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={spreadsheetId}
                  onChange={(e) => setSpreadsheetId(e.target.value)}
                  placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                  className="flex-1 p-2 border rounded"
                />
                <button
                  onClick={testConnection}
                  disabled={testingConnection || !spreadsheetId}
                  className={`px-3 py-2 rounded ${
                    connectionStatus === 'success' 
                      ? 'bg-green-600 text-white' 
                      : connectionStatus === 'error'
                      ? 'bg-red-600 text-white'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {testingConnection ? 'Testing...' : 'Test Connection'}
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                The ID is the part of the URL after "/d/" and before "/edit"
              </p>
              
              {/* Connection status */}
              {connectionStatus === 'success' && (
                <div className="mt-2 p-2 bg-green-50 text-green-700 rounded text-sm">
                  ✅ Connected to spreadsheet: <strong>{spreadsheetTitle}</strong>
                  <div className="mt-1">Available sheets: {availableSheets.join(', ')}</div>
                </div>
              )}
              
              {connectionStatus === 'error' && connectionError && (
                <div className="mt-2 p-2 bg-red-50 text-red-700 rounded text-sm">
                  ❌ {connectionError}
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Match Scouting Sheet*</label>
              <select
                value={matchScoutingSheet}
                onChange={(e) => setMatchScoutingSheet(e.target.value)}
                className="w-full p-2 border rounded"
                disabled={availableSheets.length === 0}
              >
                <option value="">Select a sheet...</option>
                {availableSheets.map(sheet => (
                  <option key={sheet} value={sheet}>
                    {sheet}
                  </option>
                ))}
              </select>
              {availableSheets.length === 0 && (
                <p className="mt-1 text-xs text-amber-500">
                  Test connection to see available sheets
                </p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Pit Scouting Sheet (Optional)</label>
              <select
                value={pitScoutingSheet}
                onChange={(e) => setPitScoutingSheet(e.target.value)}
                className="w-full p-2 border rounded"
                disabled={availableSheets.length === 0}
              >
                <option value="">None</option>
                {availableSheets.map(sheet => (
                  <option key={sheet} value={sheet}>
                    {sheet}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Super Scouting Sheet (Optional)</label>
              <select
                value={superScoutingSheet}
                onChange={(e) => setSuperScoutingSheet(e.target.value)}
                className="w-full p-2 border rounded"
                disabled={availableSheets.length === 0}
              >
                <option value="">None</option>
                {availableSheets.map(sheet => (
                  <option key={sheet} value={sheet}>
                    {sheet}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex justify-between pt-2">
              <button
                onClick={() => {
                  setShowConfigForm(false);
                  setConnectionStatus('none');
                }}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100"
                disabled={loading}
              >
                Cancel
              </button>
              
              <button
                onClick={handleCreateConfig}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                disabled={loading || !configName || !spreadsheetId || !matchScoutingSheet}
              >
                {loading ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Configurations list */}
      <div>
        <h3 className="font-semibold mb-3">Saved Configurations</h3>
        
        {loading && configurations.length === 0 ? (
          <div className="text-center p-4">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
            <p className="mt-2 text-gray-600">Loading configurations...</p>
          </div>
        ) : configurations.length > 0 ? (
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sheets</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {configurations.map((config) => (
                  <tr key={config.id} className={`hover:bg-gray-50 ${config.is_active ? 'bg-blue-50' : ''}`}>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{config.name}</div>
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {config.spreadsheet_id}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm">
                        <div className="mb-1">
                          <span className="font-medium">Match:</span> {config.match_scouting_sheet}
                        </div>
                        {config.pit_scouting_sheet && (
                          <div className="mb-1">
                            <span className="font-medium">Pit:</span> {config.pit_scouting_sheet}
                          </div>
                        )}
                        {config.super_scouting_sheet && (
                          <div>
                            <span className="font-medium">Super:</span> {config.super_scouting_sheet}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      {config.is_active ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-right">
                      {!config.is_active && (
                        <button
                          onClick={() => handleSetActive(config.id)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                          disabled={loading}
                        >
                          Set Active
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteConfig(config.id, config.name)}
                        className="text-red-600 hover:text-red-900"
                        disabled={loading}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center p-6 bg-gray-50 rounded-lg border border-dashed border-gray-300">
            <p className="text-gray-500">No configurations found</p>
            {currentEventKey && currentYear && (
              <p className="mt-2 text-sm text-gray-500">
                Click "Add Configuration" to connect your Google Sheet.
              </p>
            )}
            {(!currentEventKey || !currentYear) && (
              <p className="mt-2 text-sm text-gray-500">
                Select an event first to add configurations.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SheetConfigManager;