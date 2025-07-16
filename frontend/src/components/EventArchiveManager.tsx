// frontend/src/components/EventArchiveManager.tsx

import React, { useState, useEffect } from 'react';
import { apiUrl, fetchWithNgrokHeaders } from '../config';

// DEBUG flag to enable extra console output
const DEBUG = true;

// Helper function for debug logging
const debugLog = (...args: any[]) => {
  if (DEBUG) {
    console.log(...args);
  }
};

interface ArchivedEvent {
  id: number;
  name: string;
  event_key: string;
  year: number;
  created_at: string;
  created_by?: string;
  notes?: string;
  is_active: boolean;
  metadata?: {
    tables: {
      [key: string]: number;
    };
    event_key: string;
    year: number;
    archived_at: string;
    is_empty?: boolean;
    files?: string[];
    data_types?: {
      event_specific: number;
      manual_data: number;
      cache_files: number;
      config_files: number;
      manual_processing: number;
    };
  };
}

interface ArchiveManagerProps {
  currentEventKey?: string;
  currentYear?: number;
  onArchiveSuccess?: () => void;
  onRestoreSuccess?: () => void;
}

const EventArchiveManager: React.FC<ArchiveManagerProps> = ({
  currentEventKey,
  currentYear,
  onArchiveSuccess,
  onRestoreSuccess
}) => {
  // State
  const [archives, setArchives] = useState<ArchivedEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // New archive form state
  const [showArchiveForm, setShowArchiveForm] = useState<boolean>(false);
  const [archiveName, setArchiveName] = useState<string>("");
  const [archiveNotes, setArchiveNotes] = useState<string>("");
  const [archiveCreator, setArchiveCreator] = useState<string>("");
  
  // For restoration confirmation
  const [selectedArchive, setSelectedArchive] = useState<ArchivedEvent | null>(null);
  const [showRestoreConfirm, setShowRestoreConfirm] = useState<boolean>(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<boolean>(false);
  
  // Define fetchArchives function before using it in useEffect
  const fetchArchives = async () => {
    debugLog('🔄 Fetching archives...');
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetchWithNgrokHeaders(apiUrl('/api/archive/list'));
      debugLog('📊 Archive list response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        debugLog('❌ Failed to fetch archives:', errorText);
        throw new Error(`Failed to fetch archives: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      debugLog('📋 Archive list response data:', data);
      
      if (data.status === 'success') {
        debugLog(`✅ Retrieved ${data.archives?.length || 0} archives`);
        setArchives(data.archives || []);
      } else {
        debugLog('❌ Fetch archives failed:', data.message);
        setError(data.message || 'Failed to fetch archives');
      }
    } catch (err: any) {
      const errorMessage = 'Error: ' + (err.message || 'Unknown error');
      debugLog('⚠️ Fetch archives exception:', err);
      setError(errorMessage);
      console.error('Failed to fetch archives:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Load archives when the component mounts
  useEffect(() => {
    fetchArchives();
  }, []);
  
  const handleArchiveCurrentEvent = async () => {
    if (!currentEventKey || !currentYear) {
      setError('No active event found to archive');
      console.error('Missing currentEventKey or currentYear:', { currentEventKey, currentYear });
      return;
    }
    
    if (!archiveName.trim()) {
      setError('Please provide a name for this archive');
      return;
    }
    
    console.log('Starting archive operation with:', { 
      currentEventKey, 
      currentYear, 
      archiveName, 
      archiveNotes, 
      archiveCreator 
    });
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const requestData = {
        name: archiveName,
        event_key: currentEventKey,
        year: currentYear,
        notes: archiveNotes || undefined,
        created_by: archiveCreator || undefined
      };
      
      console.log('Sending archive request:', requestData);
      
      const response = await fetchWithNgrokHeaders(apiUrl('/api/archive/create'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      console.log('Archive response status:', response.status);
      
      const data = await response.json();
      console.log('Archive response data:', data);
      
      if (data.status === 'success') {
        setSuccess(`Successfully archived event: ${archiveName}`);
        // Reset form
        setArchiveName('');
        setArchiveNotes('');
        setShowArchiveForm(false);
        // Refresh the archives list
        fetchArchives();
        // Notify parent component
        if (onArchiveSuccess) onArchiveSuccess();
      } else {
        setError(data.message || 'Failed to archive event');
        console.error('Archive failed:', data);
      }
    } catch (err: any) {
      const errorMessage = 'Error: ' + (err.message || 'Unknown error');
      setError(errorMessage);
      console.error('Archive exception:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleArchiveAndClear = async () => {
    if (!currentEventKey || !currentYear) {
      setError('No active event found to archive');
      console.error('Missing currentEventKey or currentYear:', { currentEventKey, currentYear });
      return;
    }
    
    if (!archiveName.trim()) {
      setError('Please provide a name for this archive');
      return;
    }
    
    console.log('Starting archive and clear operation with:', { 
      currentEventKey, 
      currentYear, 
      archiveName, 
      archiveNotes, 
      archiveCreator 
    });
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const requestData = {
        name: archiveName,
        event_key: currentEventKey,
        year: currentYear,
        notes: archiveNotes || undefined,
        created_by: archiveCreator || undefined
      };
      
      console.log('Sending archive and clear request:', requestData);
      
      const response = await fetchWithNgrokHeaders(apiUrl('/api/archive/archive-and-clear'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      console.log('Archive and clear response status:', response.status);
      
      const data = await response.json();
      console.log('Archive and clear response data:', data);
      
      if (data.status === 'success' || data.status === 'partial') {
        let message = `Successfully archived event: ${archiveName}`;
        if (data.status === 'partial') {
          message += ` (${data.message})`;
        } else {
          message += ' and cleared data';
        }
        
        setSuccess(message);
        // Reset form
        setArchiveName('');
        setArchiveNotes('');
        setShowArchiveForm(false);
        // Refresh the archives list
        fetchArchives();
        // Notify parent component
        if (onArchiveSuccess) onArchiveSuccess();
      } else {
        setError(data.message || 'Failed to archive and clear event');
        console.error('Archive and clear failed:', data);
      }
    } catch (err: any) {
      const errorMessage = 'Error: ' + (err.message || 'Unknown error');
      setError(errorMessage);
      console.error('Archive and clear exception:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleClearEvent = async () => {
    if (!currentEventKey || !currentYear) {
      setError('No active event found to clear');
      return;
    }
    
    if (!window.confirm(`Are you sure you want to clear all data for event ${currentEventKey}? This action cannot be undone.`)) {
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetchWithNgrokHeaders(apiUrl('/api/archive/clear'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event_key: currentEventKey,
          year: currentYear
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccess(`Successfully cleared event data`);
        // Notify parent component
        if (onArchiveSuccess) onArchiveSuccess();
      } else {
        setError(data.message || 'Failed to clear event');
      }
    } catch (err: any) {
      setError('Error: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleRestoreArchive = async () => {
    if (!selectedArchive) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetchWithNgrokHeaders(apiUrl('/api/archive/restore'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          archive_id: selectedArchive.id
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccess(`Successfully restored archive: ${selectedArchive.name}`);
        // Close the confirmation dialog
        setShowRestoreConfirm(false);
        setSelectedArchive(null);
        // Notify parent component
        if (onRestoreSuccess) onRestoreSuccess();
      } else {
        setError(data.message || 'Failed to restore archive');
      }
    } catch (err: any) {
      setError('Error: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteArchive = async () => {
    if (!selectedArchive) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetchWithNgrokHeaders(apiUrl('/api/archive/delete'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          archive_id: selectedArchive.id
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSuccess(`Successfully deleted archive: ${selectedArchive.name}`);
        // Close the confirmation dialog
        setShowDeleteConfirm(false);
        setSelectedArchive(null);
        // Refresh the archives list
        fetchArchives();
      } else {
        setError(data.message || 'Failed to delete archive');
      }
    } catch (err: any) {
      setError('Error: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Event Archive Manager</h2>
        
        {!showArchiveForm && (
          <button
            onClick={() => setShowArchiveForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Archive Current Event
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
      
      {/* Debug info */}
      {DEBUG && (
        <div className="p-3 mt-2 bg-gray-100 text-gray-700 rounded text-xs font-mono">
          <details>
            <summary className="font-bold cursor-pointer">📊 Debug Information</summary>
            <div className="mt-2 overflow-auto max-h-32">
              <div><strong>Current Event:</strong> {currentEventKey || "none"}</div>
              <div><strong>Current Year:</strong> {currentYear || "none"}</div>
              <div><strong>Archive Count:</strong> {archives.length}</div>
              <div><strong>Loading:</strong> {loading ? "true" : "false"}</div>
              <div><strong>Form Visible:</strong> {showArchiveForm ? "true" : "false"}</div>
              <div><strong>Local Time:</strong> {new Date().toLocaleString()}</div>
              {archives.length > 0 && (
                <div className="mt-2">
                  <strong>Sample Archive Data:</strong>
                  <pre className="text-xs text-gray-600 mt-1">
                    {JSON.stringify(archives[0]?.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </details>
        </div>
      )}
      
      {/* Archive form */}
      {showArchiveForm && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="font-semibold mb-3">Archive Current Event</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Archive Name*</label>
              <input
                type="text"
                value={archiveName}
                onChange={(e) => setArchiveName(e.target.value)}
                placeholder="e.g. 2025 Championship - Dallas"
                className="w-full p-2 border rounded"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Created By</label>
              <input
                type="text"
                value={archiveCreator}
                onChange={(e) => setArchiveCreator(e.target.value)}
                placeholder="Your name"
                className="w-full p-2 border rounded"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Notes</label>
              <textarea
                value={archiveNotes}
                onChange={(e) => setArchiveNotes(e.target.value)}
                placeholder="Optional notes about this archive"
                className="w-full p-2 border rounded h-20"
              />
            </div>
            
            <div className="flex justify-between pt-2">
              <div>
                <button
                  onClick={() => setShowArchiveForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded mr-2"
                  disabled={loading}
                >
                  Cancel
                </button>
                
                <button
                  onClick={handleClearEvent}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                  disabled={loading || !currentEventKey}
                  title={!currentEventKey ? "No event selected" : "Clear event data without archiving"}
                >
                  Clear Without Archiving
                </button>
              </div>
              
              <div>
                <button
                  onClick={() => {
                    debugLog("Archive Only button clicked", {
                      currentEventKey,
                      currentYear,
                      archiveName
                    });
                    handleArchiveCurrentEvent();
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 mr-2"
                  disabled={loading || !archiveName.trim() || !currentEventKey}
                  title={!currentEventKey 
                    ? "No event selected" 
                    : !archiveName.trim() 
                      ? "Archive name is required" 
                      : "Archive event data only"
                  }
                >
                  {loading ? "Archiving..." : "Archive Only"}
                </button>
                
                <button
                  onClick={() => {
                    debugLog("Archive & Clear button clicked", {
                      currentEventKey,
                      currentYear,
                      archiveName
                    });
                    handleArchiveAndClear();
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  disabled={loading || !archiveName.trim() || !currentEventKey}
                  title={!currentEventKey 
                    ? "No event selected" 
                    : !archiveName.trim() 
                      ? "Archive name is required" 
                      : "Archive and clear event data"
                  }
                >
                  {loading ? "Processing..." : "Archive & Clear"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Archived events list */}
      <div>
        <h3 className="font-semibold mb-3">Archived Events</h3>

        {loading && !archives.length ? (
          <div className="text-center p-4">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
            <p className="mt-2 text-gray-600">Loading archives...</p>
          </div>
        ) : archives.length > 0 ? (
          <div className="overflow-x-auto">
            <div className="bg-white rounded-lg border">
              <table className="min-w-full divide-y divide-gray-200 table-fixed">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="w-1/4 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="w-1/6 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                    <th className="w-1/6 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    <th className="w-1/4 px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                    <th className="w-1/6 px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {archives.map((archive) => (
                    <tr key={archive.id} className="hover:bg-gray-50">
                      <td className="px-3 py-4 text-sm">
                        <div className="font-medium text-gray-900">{archive.name}</div>
                        {archive.notes && (
                          <div className="text-sm text-gray-500 truncate max-w-xs" title={archive.notes}>
                            {archive.notes}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-4 text-sm">
                        <div className="text-gray-900">{archive.event_key}</div>
                        <div className="text-gray-500">{archive.year}</div>
                      </td>
                      <td className="px-3 py-4 text-sm">
                        <div className="text-gray-900">{archive.created_at}</div>
                        {archive.created_by && (
                          <div className="text-gray-500">By: {archive.created_by}</div>
                        )}
                      </td>
                      <td className="px-3 py-4 text-sm">
                        {/* Display traditional table data */}
                        {archive.metadata?.tables && (
                          <div className="text-xs text-gray-500 mb-2">
                            {Object.entries(archive.metadata.tables).map(([table, count]) => (
                              <div key={table} className={table === 'unified_dataset' ? 'font-bold text-blue-600' : ''}>
                                {table === 'unified_dataset' ? '📊 Unified Dataset' : table}: {count}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Display enhanced data types */}
                        {archive.metadata?.data_types && (
                          <div className="text-xs text-gray-600 mb-2">
                            <div className="font-semibold text-gray-700 mb-1">Data Types:</div>
                            {archive.metadata.data_types.event_specific > 0 && (
                              <div className="text-blue-600">
                                🎯 Event-specific: {archive.metadata.data_types.event_specific}
                              </div>
                            )}
                            {archive.metadata.data_types.manual_data > 0 && (
                              <div className="text-green-600">
                                📝 Manual data: {archive.metadata.data_types.manual_data}
                              </div>
                            )}
                            {archive.metadata.data_types.cache_files > 0 && (
                              <div className="text-orange-600">
                                🗂️ Cache files: {archive.metadata.data_types.cache_files}
                              </div>
                            )}
                            {archive.metadata.data_types.config_files > 0 && (
                              <div className="text-purple-600">
                                ⚙️ Config files: {archive.metadata.data_types.config_files}
                              </div>
                            )}
                            {archive.metadata.data_types.manual_processing > 0 && (
                              <div className="text-indigo-600">
                                🔄 Manual processing: {archive.metadata.data_types.manual_processing}
                              </div>
                            )}
                            {/* Show message if no enhanced data types are present */}
                            {Object.values(archive.metadata.data_types).every(count => count === 0) && (
                              <div className="text-gray-400 italic">
                                No enhanced data types available
                              </div>
                            )}
                          </div>
                        )}

                        {archive.metadata?.is_empty && (
                          <div className="text-xs text-amber-500 mt-1">
                            ⚠️ Empty archive (no database entries)
                          </div>
                        )}

                        {archive.metadata?.files?.length > 0 && (
                          <div className="text-xs text-green-600 mt-1">
                            📁 Includes {archive.metadata.files.length} file(s)
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-4 text-sm text-center">
                        <div className="flex justify-center space-x-2">
                          <button
                            onClick={() => {
                              setSelectedArchive(archive);
                              setShowRestoreConfirm(true);
                            }}
                            className="bg-blue-100 text-blue-700 px-2 py-1 rounded hover:bg-blue-200"
                          >
                            Restore
                          </button>
                          <button
                            onClick={() => {
                              setSelectedArchive(archive);
                              setShowDeleteConfirm(true);
                            }}
                            className="bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center p-6 bg-gray-50 rounded-lg border border-dashed border-gray-300">
            <p className="text-gray-500">No archived events found</p>
          </div>
        )}
      </div>
      
      {/* Restore confirmation modal */}
      {showRestoreConfirm && selectedArchive && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Restore Archive</h3>
            <p className="mb-4">
              Are you sure you want to restore the archive "{selectedArchive.name}"? 
              This will load data for event {selectedArchive.event_key} ({selectedArchive.year}).
            </p>
            <p className="mb-6 text-sm text-red-600">
              Note: This will fail if event data already exists for {selectedArchive.event_key}. 
              Clear any existing data first.
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowRestoreConfirm(false);
                  setSelectedArchive(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleRestoreArchive}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                disabled={loading}
              >
                {loading ? "Restoring..." : "Restore Archive"}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Delete confirmation modal */}
      {showDeleteConfirm && selectedArchive && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Delete Archive</h3>
            <p className="mb-4">
              Are you sure you want to delete the archive "{selectedArchive.name}"? 
              This action cannot be undone.
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setSelectedArchive(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteArchive}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                disabled={loading}
              >
                {loading ? "Deleting..." : "Delete Archive"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventArchiveManager;