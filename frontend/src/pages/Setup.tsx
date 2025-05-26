// frontend/src/pages/Setup.tsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import EventArchiveManager from "../components/EventArchiveManager";
import SheetConfigManager from "../components/SheetConfigManager";

interface Event {
  key: string;
  name: string;
  code: string;
  location: string;
  dates: string;
  type: string;
  week: number;
}

interface GroupedEvents {
  [key: string]: Event[];
}

interface EventInfo {
  event_key?: string;
  event_name?: string;
  year?: number;
}

// Define the ToC item type based on backend structure
interface TocItemType {
  title: string;
  level: number;
  page: number;
  // Allow any other fields that might come from the backend
  [key: string]: any; 
}

// Interfaces for GameManual management
interface GameManualBase {
  id: number;
  year: number;
  original_filename: string;
  sanitized_filename_base: string;
  upload_timestamp?: string; // Assuming ISO string from backend
  last_accessed_timestamp?: string; // Assuming ISO string from backend
}

interface GameManualResponse extends GameManualBase {}

interface GameManualDetailResponse extends GameManualResponse {
  stored_pdf_path?: string;
  toc_json_path?: string;
  parsed_sections_path?: string;
  toc_content?: TocItemType[];
  toc_error?: string;
}


function Setup() {
  const navigate = useNavigate();
  const [year, setYear] = useState<number>(2025);
  // const [manualUrl, setManualUrl] = useState<string>(""); // Removed
  const [selectedManualFile, setSelectedManualFile] = useState<File | null>(null); // Added
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [setupResult, setSetupResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // ToC and Section Processing States
  const [selectedTocItems, setSelectedTocItems] = useState<Map<string, TocItemType>>(new Map());
  const [processedSectionsResult, setProcessedSectionsResult] = useState<any>(null);
  const [isProcessingSections, setIsProcessingSections] = useState<boolean>(false);
  const [processSectionsError, setProcessSectionsError] = useState<string | null>(null);

  // Manual Management States
  const [managedManuals, setManagedManuals] = useState<GameManualResponse[]>([]);
  const [isLoadingManagedManuals, setIsLoadingManagedManuals] = useState<boolean>(false);
  const [managedManualsError, setManagedManualsError] = useState<string | null>(null);
  const [activeDeletingManualId, setActiveDeletingManualId] = useState<number | null>(null);
  const [deleteManualError, setDeleteManualError] = useState<string | null>(null);
  const [isLoadingSelectedManualId, setIsLoadingSelectedManualId] = useState<number | null>(null);
  const [selectedManualError, setSelectedManualError] = useState<string | null>(null);


  // Event selection states
  const [loadingEvents, setLoadingEvents] = useState<boolean>(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [groupedEvents, setGroupedEvents] = useState<GroupedEvents>({});
  const [selectedEvent, setSelectedEvent] = useState<string>("");
  const [selectedEventName, setSelectedEventName] = useState<string>("");
  
  // Current event state
  const [currentEvent, setCurrentEvent] = useState<EventInfo>({});
  const [isLoadingCurrentEvent, setIsLoadingCurrentEvent] = useState<boolean>(true);
  
  // Event switching confirmation dialog
  const [showEventSwitchDialog, setShowEventSwitchDialog] = useState<boolean>(false);
  const [pendingEventAction, setPendingEventAction] = useState<{
    eventKey: string;
    eventName: string;
    year: number;
  } | null>(null);

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newYear = parseInt(e.target.value);
    setYear(newYear);
    // Reset selected event when year changes
    setSelectedEvent("");
    setSelectedEventName("");
    // Load events for the new year
    fetchEvents(newYear);
  };

  // const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => { // Removed
  //   setManualUrl(e.target.value);
  // };

  const handleManualFileChange = (e: React.ChangeEvent<HTMLInputElement>) => { // Added
    if (e.target.files && e.target.files[0]) {
      setSelectedManualFile(e.target.files[0]);
    } else {
      setSelectedManualFile(null);
    }
  };

  const handleEventChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const key = e.target.value;
    setSelectedEvent(key);

    // Find the event name to display
    const event = events.find(e => e.key === key);
    if (event) {
      setSelectedEventName(event.name);
    }
  };

  // Load current event info and events when the component mounts
  useEffect(() => {
    // Fetch current event info
    const fetchCurrentEvent = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/setup/info");
        const data = await response.json();
        
        if (data.status === "success" && data.event_key) {
          setCurrentEvent({
            event_key: data.event_key,
            event_name: data.event_name,
            year: data.year
          });
          
          // If we have a current event, set the year to match
          if (data.year) {
            setYear(data.year);
          }
        }
      } catch (err) {
        console.error("Error fetching current event:", err);
      } finally {
        setIsLoadingCurrentEvent(false);
      }
    };
    
    fetchCurrentEvent();
    fetchEvents(year);
    fetchManagedManuals(); // Fetch managed manuals on initial load
  }, []);
  
  // When current event changes or year changes, load events for that year
  useEffect(() => {
    if (currentEvent.year && !isLoadingCurrentEvent) {
      fetchEvents(currentEvent.year);
    }
  }, [currentEvent, isLoadingCurrentEvent]);

  // Refetch managed manuals if a new manual is successfully processed via upload
  useEffect(() => {
    if (setupResult?.manual_info?.manual_db_id && !isLoading) { // isLoading is for the initial setup form
      fetchManagedManuals();
    }
  }, [setupResult?.manual_info?.manual_db_id, isLoading]);


  const fetchManagedManuals = async () => {
    setIsLoadingManagedManuals(true);
    setManagedManualsError(null);
    try {
      const response = await fetch("http://localhost:8000/api/manuals");
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch manuals");
      }
      const data: GameManualResponse[] = await response.json();
      setManagedManuals(data);
    } catch (err: any) {
      setManagedManualsError(err.message || "Error fetching manuals");
      console.error(err);
    } finally {
      setIsLoadingManagedManuals(false);
    }
  };

  const fetchEvents = async (yearToFetch: number) => {
    setLoadingEvents(true);
    setEventsError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/setup/events?year=${yearToFetch}`);

      if (!response.ok) {
        throw new Error("Failed to fetch events");
      }

      const data = await response.json();

      if (data.status === "success") {
        setEvents(data.all_events || []);
        setGroupedEvents(data.grouped_events || {});
      } else {
        setEventsError(data.message || "Failed to fetch events");
      }
    } catch (err) {
      setEventsError("Error fetching events");
      console.error(err);
    } finally {
      setLoadingEvents(false);
    }
  };

  const checkForEventSwitch = (e: React.FormEvent) => {
    e.preventDefault();
    
    // If there's already an active event and user is trying to set up a different one
    if (currentEvent.event_key && selectedEvent && currentEvent.event_key !== selectedEvent) {
      // Store the pending action
      setPendingEventAction({
        eventKey: selectedEvent,
        eventName: selectedEventName,
        year: year
      });
      
      // Show the confirmation dialog
      setShowEventSwitchDialog(true);
    } else {
      // No event switch needed, proceed normally
      handleSetup(e);
    }
  };

  const handleSetup = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      
      // Use pending event action if it exists (this is for event switching)
      const eventToUse = pendingEventAction?.eventKey || selectedEvent;
      const yearToUse = pendingEventAction?.year || year;
      
      formData.append("year", yearToUse.toString());

      if (eventToUse) {
        formData.append("event_key", eventToUse);
      }

      // if (manualUrl) { // Removed
      //   formData.append("manual_url", manualUrl);
      // }

      if (selectedManualFile) { // Added
        formData.append("manual_file", selectedManualFile);
      }

      // When using FormData with fetch, the browser automatically sets 
      // the 'Content-Type' header to 'multipart/form-data'.
      // Explicitly setting it can cause issues.
      const response = await fetch("http://localhost:8000/api/setup/start", {
        method: "POST",
        body: formData, 
        // headers: { 'Content-Type': 'application/json' } // REMOVE THIS LINE
      });

      const data = await response.json();

      if (response.ok) {
        setSetupResult(data);
        // Clear file input and ToC selection if setup was successful with a new file
        if (selectedManualFile) {
          setSelectedManualFile(null); 
        }
        setSelectedTocItems(new Map());
        setProcessedSectionsResult(null);
        setProcessSectionsError(null);
      } else {
        setError(data.detail || "Failed to start setup process");
      }
    } catch (err) {
      setError("Error connecting to server");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    navigate("/field-selection");
  };

  // Determine if the manual was used or if we fell back to basic analysis
  const getAnalysisMethod = () => {
    if (!setupResult) return null;

    const manualInfo = setupResult.manual_info || {};

    if (manualInfo.no_manual_warning) {
      return "warning";  // No manual found for this year
    }
    if (manualInfo.using_cached_manual) {
      return "cached";  // Using cached manual from previous run
    }
    if (manualInfo.analysis_method === "basic_overview") {
      return "basic";
    }
    if (manualInfo.analysis_error) {
      return "error";
    }
    if (manualInfo.text_length > 0 && manualInfo.analysis_complete) {
      return "full";
    }
    return "unknown";
  };

  const analysisMethod = getAnalysisMethod();

  const handleTocItemToggle = (item: TocItemType) => {
    const key = `${item.title}-${item.page}`; // Unique key for the map
    setSelectedTocItems(prev => {
      const newMap = new Map(prev);
      if (newMap.has(key)) {
        newMap.delete(key);
      } else {
        newMap.set(key, item);
      }
      return newMap;
    });
  };

  const handleProcessSelectedSections = async () => {
    if (!setupResult?.manual_info?.saved_manual_filename || selectedTocItems.size === 0) {
      setProcessSectionsError("Manual information or selected ToC items are missing.");
      return;
    }

    setIsProcessingSections(true);
    setProcessSectionsError(null);
    setProcessedSectionsResult(null);

    const payload = {
      manual_identifier: setupResult.manual_info.saved_manual_filename, // This is the original_filename
      year: setupResult.year,
      selected_sections: Array.from(selectedTocItems.values()),
    };

    try {
      const response = await fetch("http://localhost:8000/api/manuals/process-sections", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        setProcessedSectionsResult(data);
      } else {
        setProcessSectionsError(data.detail || "Failed to process selected sections.");
      }
    } catch (err) {
      setProcessSectionsError("Error connecting to server for section processing.");
      console.error("Error processing sections:", err);
    } finally {
      setIsProcessingSections(false);
    }
  };

  const handleSelectManagedManual = async (manual: GameManualResponse) => {
    setIsLoadingSelectedManualId(manual.id);
    setSelectedManualError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/manuals/${manual.id}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch details for manual ${manual.id}`);
      }
      const data: GameManualDetailResponse = await response.json();

      // Construct a new setupResult-like object or update relevant parts
      const newManualInfo: any = {
        manual_db_id: data.id,
        saved_manual_filename: data.original_filename, // Used by process-sections
        original_filename: data.original_filename, // For display consistency
        sanitized_filename_base: data.sanitized_filename_base,
        toc_data: data.toc_content || [],
        toc_found: !!(data.toc_content && data.toc_content.length > 0),
        toc_extraction_attempted: true, // Assume if it's in DB, it was attempted
        analysis_complete: !!(data.toc_content && data.toc_content.length > 0), // Or based on other criteria if available
        text_length: data.toc_content ? 1 : 0, // Placeholder, real text length not fetched here
        using_cached_manual: true, // Indicates it's from DB, not a fresh upload
      };
      if (data.toc_error) {
        newManualInfo.toc_error = data.toc_error;
      }
      
      // Preserve existing game_analysis and sample_teams if any, or set to defaults
      // This might need more sophisticated merging if selecting a manual should also fetch its specific game_analysis
      setSetupResult((prevResult: any) => ({
        ...prevResult, // Keep event_key, sample_teams, etc. if already set
        year: data.year,
        manual_info: newManualInfo,
        game_analysis: prevResult?.year === data.year ? prevResult.game_analysis : null, // Clear game analysis if year changes
      }));
      
      setYear(data.year); // Update the main year state
      setSelectedManualFile(null); // Clear any selected file
      setSelectedTocItems(new Map()); // Reset ToC selections
      setProcessedSectionsResult(null); // Reset section processing results
      setProcessSectionsError(null);
      setError(null); // Clear main form error

    } catch (err: any) {
      setSelectedManualError(err.message || `Error loading manual ${manual.id}`);
      console.error(err);
    } finally {
      setIsLoadingSelectedManualId(null);
    }
  };

  const handleDeleteManual = async (manualId: number) => {
    if (!window.confirm("Are you sure you want to delete this manual and its associated files? This action cannot be undone.")) {
      return;
    }
    setActiveDeletingManualId(manualId);
    setDeleteManualError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/manuals/${manualId}`, { method: 'DELETE' });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete manual ${manualId}`);
      }
      // const resultMessage = await response.json();
      // console.log(resultMessage.message); // Or display it
      fetchManagedManuals(); // Refresh list

      // If the deleted manual was the one currently loaded in setupResult
      if (setupResult?.manual_info?.manual_db_id === manualId) {
        setSetupResult((prev: any) => ({
          ...prev,
          manual_info: { manual_file_received: false }, // Reset manual_info or parts of it
          game_analysis: null // Potentially clear game analysis too
        }));
        setSelectedTocItems(new Map());
        setProcessedSectionsResult(null);
      }

    } catch (err: any) {
      setDeleteManualError(err.message || `Error deleting manual ${manualId}`);
      console.error(err);
    } finally {
      setActiveDeletingManualId(null);
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return "N/A";
    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      return "Invalid Date";
    }
  };


  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">FRC Scouting Assistant Setup</h1>

      {/* Manual Management Section */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-xl font-bold mb-4">Manage Uploaded Manuals</h2>
        <button
          onClick={fetchManagedManuals}
          disabled={isLoadingManagedManuals}
          className="mb-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
        >
          {isLoadingManagedManuals ? "Refreshing..." : "Refresh List"}
        </button>

        {managedManualsError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">{managedManualsError}</div>}
        {deleteManualError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">Delete Error: {deleteManualError}</div>}
        {selectedManualError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">Load Error: {selectedManualError}</div>}

        {isLoadingManagedManuals && !managedManuals.length ? (
          <p>Loading manuals...</p>
        ) : !managedManuals.length && !managedManualsError ? (
          <p>No manuals uploaded yet.</p>
        ) : managedManuals.length > 0 ? (
          <div className="overflow-x-auto max-h-96">
            <table className="min-w-full border text-sm">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="border px-3 py-2 text-left">Filename</th>
                  <th className="border px-3 py-2 text-left">Year</th>
                  <th className="border px-3 py-2 text-left">Uploaded</th>
                  <th className="border px-3 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {managedManuals.map(manual => (
                  <tr key={manual.id} className="hover:bg-gray-50">
                    <td className="border px-3 py-2">{manual.original_filename}</td>
                    <td className="border px-3 py-2">{manual.year}</td>
                    <td className="border px-3 py-2">{formatTimestamp(manual.upload_timestamp)}</td>
                    <td className="border px-3 py-2">
                      <button
                        onClick={() => handleSelectManagedManual(manual)}
                        disabled={isLoadingSelectedManualId === manual.id}
                        className="mr-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 disabled:bg-blue-300"
                      >
                        {isLoadingSelectedManualId === manual.id ? "Loading..." : "Load ToC"}
                      </button>
                      <button
                        onClick={() => handleDeleteManual(manual.id)}
                        disabled={activeDeletingManualId === manual.id}
                        className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 disabled:bg-red-300"
                      >
                        {activeDeletingManualId === manual.id ? "Deleting..." : "Delete"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column - Event Setup */}
        <div className="lg:col-span-5">
          {/* Event Switch Confirmation Dialog */}
          {showEventSwitchDialog && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
                <div className="flex items-center text-yellow-600 mb-4">
                  <svg className="w-6 h-6 mr-2" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                  </svg>
                  <h3 className="text-xl font-bold">Change Active Event?</h3>
                </div>
                
                <p className="mb-4">
                  An event is already loaded in the system: <strong>{currentEvent.event_name || currentEvent.event_key}</strong>
                </p>
                
                <p className="mb-4">
                  To switch to <strong>{pendingEventAction?.eventName || pendingEventAction?.eventKey}</strong>, you must either:
                </p>
                
                <ul className="list-disc pl-5 mb-6 text-gray-700">
                  <li className="mb-2">Archive the current event (recommended to preserve data)</li>
                  <li className="mb-2">Continue without archiving (data may be lost)</li>
                  <li>Cancel and keep working with the current event</li>
                </ul>
                
                <div className="flex flex-col space-y-3">
                  <button
                    onClick={() => {
                      setShowEventSwitchDialog(false);
                      // Redirect to archive section
                      document.getElementById("archiveSection")?.scrollIntoView({ behavior: "smooth" });
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Archive Current Event
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowEventSwitchDialog(false);
                      // Proceed with setup
                      handleSetup();
                    }}
                    className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
                  >
                    Continue Without Archiving
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowEventSwitchDialog(false);
                      setPendingEventAction(null);
                      // Reset the selected event to the current one
                      setSelectedEvent(currentEvent.event_key || "");
                      setSelectedEventName(currentEvent.event_name || "");
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        
          {!setupResult ? (
            <form onSubmit={checkForEventSwitch} className="space-y-6 bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">New Event Setup (Upload or Select Existing Manual)</h2>

              <div>
                <label className="block mb-2 font-semibold">FRC Season Year</label>
                <select
                  value={year}
                  onChange={handleYearChange}
                  className="w-full p-2 border rounded"
                >
                  <option value={2025}>2025</option>
                  <option value={2024}>2024</option>
                  <option value={2023}>2023</option>
                </select>
              </div>

              <div>
                <label className="block mb-2 font-semibold">Select Event</label>
                {loadingEvents ? (
                  <div className="p-2 text-blue-600">Loading events...</div>
                ) : eventsError ? (
                  <div className="p-2 text-red-600">{eventsError}</div>
                ) : (
                  <div className="space-y-2">
                    <select
                      value={selectedEvent}
                      onChange={handleEventChange}
                      className="w-full p-2 border rounded"
                    >
                      <option value="">-- Select an event --</option>

                      {/* Display events grouped by type */}
                      {Object.entries(groupedEvents).map(([type, eventsList]) => (
                        <optgroup key={type} label={type}>
                          {eventsList.map(event => (
                            <option key={event.key} value={event.key}>
                              {event.name} - {event.location}
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>

                    {selectedEvent && (
                      <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                        <p className="font-semibold">{selectedEventName}</p>
                        <p className="text-sm mt-1">
                          Event Code: {selectedEvent}
                          {events.find(e => e.key === selectedEvent)?.dates && (
                            <span className="ml-2">
                              ({events.find(e => e.key === selectedEvent)?.dates})
                            </span>
                          )}
                        </p>
                      </div>
                    )}

                    <p className="text-sm text-gray-500">
                      Select the event you're scouting for. This will be used to pre-populate team lists and event data.
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="block mb-2 font-semibold">Game Manual PDF</label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleManualFileChange}
                  className="w-full p-2 border rounded file:mr-4 file:py-2 file:px-4
                            file:rounded-full file:border-0
                            file:text-sm file:font-semibold
                            file:bg-blue-50 file:text-blue-700
                            hover:file:bg-blue-100"
                />
                {selectedManualFile && (
                  <p className="mt-1 text-sm text-gray-600">
                    Selected file: <strong>{selectedManualFile.name}</strong> ({(selectedManualFile.size / 1024).toFixed(1)} KB)
                  </p>
                )}
                <div className="flex items-center mt-1">
                  <svg className="h-4 w-4 text-blue-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-blue-700">
                    If a manual has already been processed for this year (from DB), it might be used. Uploading a new one will process it.
                  </p>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  Upload the official game manual PDF. If left empty and no manual is found in the database for this year,
                  a basic game analysis will be generated with limited accuracy.
                </p>
              </div>

              {error && (
                <div className="p-3 bg-red-100 text-red-700 rounded">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || loadingEvents}
                className="w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
              >
                {isLoading ? "Processing..." : "Start Setup"}
              </button>
            </form>
          ) : (
            <div className="bg-white p-6 rounded-lg shadow space-y-6">
              <h2 className="text-2xl font-semibold">Setup Complete</h2>

              {setupResult.event_key && (
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <h3 className="text-lg font-medium mb-2">Selected Event</h3>
                  <p className="font-semibold">{selectedEventName || setupResult.event_key}</p>
                  <p className="text-sm text-blue-700">Event Key: {setupResult.event_key}</p>
                </div>
              )}

              <div>
                <h3 className="text-lg font-medium mb-2">Game Manual Analysis</h3>
                {setupResult.game_analysis ? (
                  <div className={`p-4 rounded ${
                    analysisMethod === "full" ? "bg-green-50" :
                    analysisMethod === "cached" ? "bg-blue-50" :
                    analysisMethod === "basic" ? "bg-yellow-50" :
                    analysisMethod === "warning" ? "bg-orange-50" :
                    analysisMethod === "error" ? "bg-red-50" : "bg-gray-50"
                  }`}>
                    <div className="flex items-center mb-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full mr-2 ${
                        analysisMethod === "full" ? "bg-green-200 text-green-800" :
                        analysisMethod === "cached" ? "bg-blue-200 text-blue-800" :
                        analysisMethod === "basic" ? "bg-yellow-200 text-yellow-800" :
                        analysisMethod === "warning" ? "bg-orange-200 text-orange-800" :
                        analysisMethod === "error" ? "bg-red-200 text-red-800" : "bg-gray-200"
                      }`}>
                        {analysisMethod === "full" ? "FULL MANUAL ANALYSIS" :
                         analysisMethod === "cached" ? "USING CACHED MANUAL" :
                         analysisMethod === "basic" ? "BASIC ANALYSIS (NO MANUAL)" :
                         analysisMethod === "warning" ? "NO MANUAL FOUND" :
                         analysisMethod === "error" ? "MANUAL ERROR - FALLBACK USED" : "UNKNOWN"}
                      </span>
                      <h4 className="font-semibold">{setupResult.game_analysis.game_name}</h4>
                    </div>

                    {analysisMethod === "full" && (
                      <p className="text-green-700 text-sm mb-2">
                        Successfully analyzed game manual ({setupResult.manual_info.text_length.toLocaleString()} characters)
                      </p>
                    )}

                    {analysisMethod === "cached" && (
                      <p className="text-blue-700 text-sm mb-2">
                        Using previously analyzed game manual from this season.
                        {setupResult.manual_info.processed_filename_from_cache && (
                          <span className="block mt-1">Cached File: {setupResult.manual_info.processed_filename_from_cache}</span>
                        )}
                         {setupResult.manual_info.processed_url_from_cache && ( // Legacy
                          <span className="block mt-1">Source URL (Legacy): {setupResult.manual_info.processed_url_from_cache}</span>
                        )}
                      </p>
                    )}

                    {analysisMethod === "basic" && (
                      <p className="text-yellow-700 text-sm mb-2">
                        No manual provided. Using AI-generated game overview with limited accuracy.
                      </p>
                    )}

                    {analysisMethod === "warning" && (
                      <p className="text-orange-700 text-sm mb-2">
                        <strong>Warning:</strong> No manual found for this year and none provided.
                        The AI is making educated guesses about the game. For better results, please provide a manual URL.
                      </p>
                    )}

                    {analysisMethod === "error" && (
                      <p className="text-red-700 text-sm mb-2">
                        Error processing manual: {setupResult.manual_info.analysis_error}
                      </p>
                    )}

                    <div className="mt-4">
                      <h5 className="font-medium mb-1">Field Elements:</h5>
                      <ul className="list-disc list-inside text-sm ml-2">
                        {(setupResult.game_analysis.field_elements || []).slice(0, 3).map((element: string, idx: number) => (
                          <li key={idx}>{element}</li>
                        ))}
                        {(setupResult.game_analysis.field_elements || []).length > 3 && (
                          <li>...and {setupResult.game_analysis.field_elements.length - 3} more</li>
                        )}
                      </ul>
                    </div>

                    <div className="mt-3">
                      <h5 className="font-medium mb-1">Scouting Variables:</h5>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {Object.entries(setupResult.game_analysis.scouting_variables || {}).map(([category, variables]: [string, any]) => (
                          <div key={category} className="bg-white p-2 rounded border">
                            <strong className="capitalize">{category.replace('_', ' ')}:</strong> {Array.isArray(variables) ? variables.length : 0} vars
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-red-50 p-4 rounded">
                    <p className="text-red-700">
                      Analysis failed. No game data available.
                    </p>
                  </div>
                )}
              </div>

              {/* ToC Display and Selection */}
              {setupResult?.manual_info?.toc_data && setupResult.manual_info.toc_data.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-medium mb-2">Table of Contents</h3>
                  <div className="max-h-96 overflow-y-auto border rounded p-4 bg-gray-50 space-y-2">
                    {setupResult.manual_info.toc_data.map((item: TocItemType, index: number) => {
                      const key = `${item.title}-${item.page}`;
                      return (
                        <div key={key} className="flex items-center" style={{ marginLeft: `${(item.level -1) * 20}px`}}>
                          <input
                            type="checkbox"
                            id={`toc-${key}`}
                            checked={selectedTocItems.has(key)}
                            onChange={() => handleTocItemToggle(item)}
                            className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <label htmlFor={`toc-${key}`} className="text-sm cursor-pointer hover:text-blue-700">
                            {item.title} <span className="text-gray-500 text-xs">(p. {item.page})</span>
                          </label>
                        </div>
                      );
                    })}
                  </div>
                  {selectedTocItems.size > 0 && (
                    <button
                      onClick={handleProcessSelectedSections}
                      disabled={isProcessingSections || !setupResult?.manual_info?.saved_manual_filename}
                      className="mt-4 w-full py-2 px-4 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:bg-indigo-300"
                    >
                      {isProcessingSections ? "Processing Sections..." : `Process ${selectedTocItems.size} Selected Section(s)`}
                    </button>
                  )}
                  {processSectionsError && (
                    <div className="mt-2 p-3 bg-red-100 text-red-700 rounded">
                      {processSectionsError}
                    </div>
                  )}
                  {processedSectionsResult && (
                    <div className="mt-2 p-3 bg-green-50 text-green-700 rounded">
                      <h4 className="font-semibold">Sections Processed Successfully!</h4>
                      <p className="text-sm">Saved to: {processedSectionsResult.saved_text_path}</p>
                      <p className="text-sm">Extracted Length: {processedSectionsResult.extracted_text_length} chars</p>
                      <p className="text-xs mt-1">Sample: <pre className="whitespace-pre-wrap bg-gray-100 p-1 rounded text-xs">{processedSectionsResult.sample_text}</pre></p>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-6"> {/* Added margin top for spacing */}
                <h3 className="text-lg font-medium mb-2">Sample Teams</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full border">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="border px-4 py-2">Team #</th>
                        <th className="border px-4 py-2">Name</th>
                        <th className="border px-4 py-2">EPA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {setupResult.sample_teams.map((team: any) => (
                        <tr key={team.team_number}>
                          <td className="border px-4 py-2">{team.team_number}</td>
                          <td className="border px-4 py-2">{team.team_name}</td>
                          <td className="border px-4 py-2">{team.epa_total?.toFixed(1) || "N/A"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <button
                onClick={handleContinue}
                className="w-full py-3 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Continue to Schema Setup
              </button>
            </div>
          )}
        </div>

        {/* Right Column - Event Archive Manager */}
        <div className="lg:col-span-7">
          <div className="space-y-6">
            {/* Event Archive Manager */}
            <div id="archiveSection" className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">Event Management</h2>
              
              {isLoadingCurrentEvent ? (
                <div className="p-2 text-blue-600">Loading current event...</div>
              ) : (
                <div className="mb-6">
                  <div className="flex items-center">
                    <span className="font-semibold mr-2">Current Event:</span>
                    {currentEvent.event_key ? (
                      <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
                        {currentEvent.event_name || currentEvent.event_key} ({currentEvent.year})
                      </span>
                    ) : (
                      <span className="px-3 py-1 rounded-full bg-yellow-100 text-yellow-800">
                        None Selected
                      </span>
                    )}
                  </div>
                  
                  {setupResult?.event_key && currentEvent.event_key !== setupResult.event_key && (
                    <div className="mt-2 text-green-700">
                      <span className="font-semibold">New Event Selected:</span> {setupResult.event_key}
                    </div>
                  )}
                </div>
              )}

              <EventArchiveManager
                currentEventKey={currentEvent.event_key || selectedEvent || (setupResult?.event_key ? setupResult.event_key : undefined)}
                currentYear={currentEvent.year || year}
                onArchiveSuccess={() => {
                  // Reload the page or clear setup result
                  console.log("Archive success callback triggered");
                  setSetupResult(null);
                  
                  // If there was a pending event change, proceed with it after archiving
                  if (pendingEventAction) {
                    setSelectedEvent(pendingEventAction.eventKey);
                    setSelectedEventName(pendingEventAction.eventName);
                    setYear(pendingEventAction.year);
                    setPendingEventAction(null);
                    
                    // Wait a moment then submit the form
                    setTimeout(() => {
                      handleSetup();
                    }, 500);
                  }
                }}
                onRestoreSuccess={() => {
                  // Reload the page to show restored data
                  console.log("Restore success callback triggered");
                  window.location.reload();
                }}
              />
            </div>

            {/* Sheet Configuration Manager */}
            <div className="bg-white p-6 rounded-lg shadow">
              <SheetConfigManager
                currentEventKey={selectedEvent || (setupResult?.event_key ? setupResult.event_key : undefined)}
                currentYear={year}
                onConfigurationChange={() => {
                  // Notify of configuration changes
                  console.log("Configuration changed");
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Setup;