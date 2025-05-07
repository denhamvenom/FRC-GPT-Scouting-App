// frontend/src/pages/EventManager.tsx

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AppStateService from '../services/AppStateService';

interface ArchivedEvent {
  id: string;
  eventKey: string;
  year: number;
  name: string;
  createdAt: string;
}

function EventManager() {
  const navigate = useNavigate();
  const [newEventKey, setNewEventKey] = useState<string>('');
  const [newEventYear, setNewEventYear] = useState<number>(new Date().getFullYear());
  const [archivedEvents, setArchivedEvents] = useState<ArchivedEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Load archived events on mount
  useEffect(() => {
    const loadArchivedEvents = async () => {
      // In a real implementation, we would fetch event details from the server
      // For this demo, we'll just use the IDs from AppStateService and create mock details
      const archivedIds = AppStateService.getArchivedEvents();
      
      const mockEvents: ArchivedEvent[] = archivedIds.map(id => {
        const [yearStr, eventKey] = id.split('_');
        return {
          id,
          eventKey,
          year: parseInt(yearStr),
          name: `${yearStr} ${eventKey.toUpperCase()}`,
          createdAt: new Date().toISOString()
        };
      });
      
      setArchivedEvents(mockEvents);
    };
    
    loadArchivedEvents();
  }, []);
  
  const handleStartNewEvent = () => {
    if (!newEventKey) {
      setError('Please enter an event key');
      return;
    }
    
    // Save current event if it exists
    const currentState = AppStateService.getState();
    if (currentState.currentEventKey) {
      AppStateService.archiveEvent(currentState.currentEventKey, currentState.currentYear);
    }
    
    // Reset state for new event
    AppStateService.resetForNewEvent(newEventKey, newEventYear);
    
    setSuccessMessage(`Started new event: ${newEventYear} ${newEventKey}`);
    setTimeout(() => {
      navigate('/setup');
    }, 1500);
  };
  
  const handleLoadArchivedEvent = (archivedEvent: ArchivedEvent) => {
    // Save current event if it exists
    const currentState = AppStateService.getState();
    if (currentState.currentEventKey) {
      AppStateService.archiveEvent(currentState.currentEventKey, currentState.currentYear);
    }
    
    // Set current event to the archived one
    AppStateService.updateState({
      currentEventKey: archivedEvent.eventKey,
      currentYear: archivedEvent.year,
      setupCompleted: true,
      fieldSelectionCompleted: true,
      datasetBuilt: true,
      validationCompleted: true
    });
    
    setSuccessMessage(`Loaded archived event: ${archivedEvent.year} ${archivedEvent.eventKey}`);
    setTimeout(() => {
      navigate('/picklist');
    }, 1500);
  };
  
  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Event Manager</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {successMessage}
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Start New Event Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Start New Event</h2>
          <p className="text-gray-600 mb-4">
            Begin a new scouting workflow for a competition. This will save any current work
            and start fresh with a new event.
          </p>
          
          <div className="space-y-4">
            <div>
              <label className="block mb-2 font-semibold">Year</label>
              <select
                value={newEventYear}
                onChange={(e) => setNewEventYear(parseInt(e.target.value))}
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
                value={newEventKey}
                onChange={(e) => setNewEventKey(e.target.value)}
                placeholder="e.g., nyny, galileo, einstein"
                className="w-full p-2 border rounded"
              />
              <p className="mt-1 text-sm text-gray-500">
                Enter the TBA event key without the year (e.g., "nyny" for New York)
              </p>
            </div>
            
            <button
              onClick={handleStartNewEvent}
              disabled={loading || !newEventKey}
              className={`w-full py-2 rounded text-white ${
                loading || !newEventKey
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? 'Starting...' : 'Start New Event'}
            </button>
          </div>
        </div>
        
        {/* Archived Events Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Archived Events</h2>
          <p className="text-gray-600 mb-4">
            Load a previously archived event to continue working with its data.
          </p>
          
          {archivedEvents.length > 0 ? (
            <div className="overflow-y-auto max-h-80">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Event
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Year
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {archivedEvents.map((event, idx) => (
                    <tr
                      key={event.id}
                      className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                    >
                      <td className="px-4 py-3 text-sm font-medium">
                        {event.eventKey}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {event.year}
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        <button
                          onClick={() => handleLoadArchivedEvent(event)}
                          className="text-blue-600 hover:underline"
                        >
                          Load
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 text-center text-gray-500 bg-gray-50 rounded">
              No archived events found. Events are archived automatically when you start a new event.
            </div>
          )}
        </div>
      </div>
      
      {/* Current Workflow Status */}
      <div className="mt-6 bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Current Workflow Status</h2>
        
        <div className="space-y-4">
          {(() => {
            const state = AppStateService.getState();
            const currentEvent = state.currentEventKey ? 
              `${state.currentYear} ${state.currentEventKey}` : 
              "No event selected";
              
            return (
              <>
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                  <div>
                    <span className="font-medium">Current Event:</span> {currentEvent}
                  </div>
                  {state.currentEventKey && (
                    <Link
                      to="/workflow"
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      View Workflow
                    </Link>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  <div className={`p-3 rounded border ${state.setupCompleted ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center mb-1">
                      {state.setupCompleted ? (
                        <svg className="w-5 h-5 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-gray-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="font-medium">Setup</span>
                    </div>
                    <div className="text-xs">
                      {state.setupCompleted ? "Completed" : "Not started"}
                    </div>
                  </div>
                  
                  <div className={`p-3 rounded border ${state.fieldSelectionCompleted ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center mb-1">
                      {state.fieldSelectionCompleted ? (
                        <svg className="w-5 h-5 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-gray-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="font-medium">Field Selection</span>
                    </div>
                    <div className="text-xs">
                      {state.fieldSelectionCompleted ? "Completed" : "Not started"}
                    </div>
                  </div>
                  
                  <div className={`p-3 rounded border ${state.datasetBuilt ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center mb-1">
                      {state.datasetBuilt ? (
                        <svg className="w-5 h-5 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-gray-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="font-medium">Build Dataset</span>
                    </div>
                    <div className="text-xs">
                      {state.datasetBuilt ? "Completed" : "Not started"}
                    </div>
                  </div>
                  
                  <div className={`p-3 rounded border ${state.validationCompleted ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center mb-1">
                      {state.validationCompleted ? (
                        <svg className="w-5 h-5 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-gray-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="font-medium">Validation</span>
                    </div>
                    <div className="text-xs">
                      {state.validationCompleted ? "Completed" : "Not started"}
                    </div>
                  </div>
                  
                  <div className={`p-3 rounded border ${state.validationCompleted ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center mb-1">
                      {state.validationCompleted ? (
                        <svg className="w-5 h-5 text-blue-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-gray-400 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clipRule="evenodd" />
                        </svg>
                      )}
                      <span className="font-medium">Picklist</span>
                    </div>
                    <div className="text-xs">
                      {state.validationCompleted ? "Ready" : "Not ready"}
                    </div>
                  </div>
                </div>
              </>
            );
          })()}
        </div>
      </div>
    </div>
  );
}

export default EventManager;