import React, { useState, useEffect } from 'react';

interface Log {
  status: string;
  log_count: number;
  logs: string[];
}

const DebugLogs: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);
  const [lineCount, setLineCount] = useState<number>(100);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/debug/logs/picklist?lines=${lineCount}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.statusText}`);
      }
      
      const data: Log = await response.json();
      
      if (data.status === 'success') {
        setLogs(data.logs);
        setError(null);
      } else {
        setError(data.message || 'Error fetching logs');
      }
    } catch (err: any) {
      setError(err.message || 'Error fetching logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    // Clean up any existing interval
    return () => {
      if (refreshInterval !== null) {
        clearInterval(refreshInterval);
      }
    };
  }, [lineCount]);
  
  useEffect(() => {
    // Set up or clear auto-refresh
    if (autoRefresh) {
      const interval = window.setInterval(fetchLogs, 5000); // Refresh every 5 seconds
      setRefreshInterval(interval);
    } else if (refreshInterval !== null) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
    
    return () => {
      if (refreshInterval !== null) {
        clearInterval(refreshInterval);
      }
    };
  }, [autoRefresh]);

  // Parse log line for styling
  const parseLogLine = (line: string) => {
    // Check log level for styling
    if (line.includes(' - ERROR ')) {
      return <span className="text-red-600">{line}</span>;
    } else if (line.includes(' - WARNING ')) {
      return <span className="text-yellow-600">{line}</span>;
    } else if (line.includes('STARTING PICKLIST GENERATION') || 
               line.includes('PICKLIST GENERATION COMPLETE')) {
      return <span className="font-bold text-green-600">{line}</span>;
    } else if (line.includes('Chunk ')) {
      return <span className="text-blue-600">{line}</span>;
    } else {
      return <span>{line}</span>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">GPT Picklist Generation Logs</h1>
        <div className="flex space-x-2">
          <select 
            value={lineCount}
            onChange={(e) => setLineCount(parseInt(e.target.value))}
            className="border rounded px-2 py-1"
          >
            <option value="50">50 lines</option>
            <option value="100">100 lines</option>
            <option value="250">250 lines</option>
            <option value="500">500 lines</option>
          </select>
          
          <div className="flex items-center space-x-2">
            <input 
              type="checkbox" 
              id="autoRefresh" 
              checked={autoRefresh} 
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="h-4 w-4"
            />
            <label htmlFor="autoRefresh" className="text-sm">Auto-refresh (5s)</label>
          </div>
          
          <button 
            onClick={fetchLogs} 
            className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="bg-gray-900 text-gray-100 p-4 rounded overflow-auto h-[75vh] font-mono text-sm">
        {logs.length === 0 ? (
          <div className="text-center py-10">
            {loading ? 'Loading logs...' : 'No logs available. Generate a picklist first.'}
          </div>
        ) : (
          <div className="whitespace-pre-wrap">
            {logs.map((log, index) => (
              <div key={index} className="py-0.5">
                {parseLogLine(log)}
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="mt-4 text-sm text-gray-500">
        <p>
          Showing {logs.length} log entries. 
          {autoRefresh && " Auto-refreshing every 5 seconds."}
        </p>
      </div>
    </div>
  );
};

export default DebugLogs;