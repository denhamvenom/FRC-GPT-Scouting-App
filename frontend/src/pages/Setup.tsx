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

function Setup() {
  const navigate = useNavigate();
  const [year, setYear] = useState<number>(2025);
  const [manualUrl, setManualUrl] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [setupResult, setSetupResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Event selection states
  const [loadingEvents, setLoadingEvents] = useState<boolean>(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [groupedEvents, setGroupedEvents] = useState<GroupedEvents>({});
  const [selectedEvent, setSelectedEvent] = useState<string>("");
  const [selectedEventName, setSelectedEventName] = useState<string>("");

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newYear = parseInt(e.target.value);
    setYear(newYear);
    // Reset selected event when year changes
    setSelectedEvent("");
    setSelectedEventName("");
    // Load events for the new year
    fetchEvents(newYear);
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setManualUrl(e.target.value);
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

  // Load events when the component mounts or when the year changes
  useEffect(() => {
    fetchEvents(year);
  }, []);

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

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("year", year.toString());

      if (selectedEvent) {
        formData.append("event_key", selectedEvent);
      }

      if (manualUrl) {
        formData.append("manual_url", manualUrl);
      }

      const response = await fetch("http://localhost:8000/api/setup/start", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setSetupResult(data);
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

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">FRC Scouting Assistant Setup</h1>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column - Event Setup */}
        <div className="lg:col-span-5">
          {!setupResult ? (
            <form onSubmit={handleSetup} className="space-y-6 bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">New Event Setup</h2>

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
                <label className="block mb-2 font-semibold">Game Manual URL (PDF)</label>
                <input
                  type="url"
                  value={manualUrl}
                  onChange={handleUrlChange}
                  placeholder="https://firstfrc.blob.core.windows.net/frc2025/Manual/2025GameManual.pdf"
                  className="w-full p-2 border rounded"
                />
                <div className="flex items-center mt-1">
                  <svg className="h-4 w-4 text-blue-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-blue-700">
                    If a manual has already been processed for this year, it will be used automatically.
                  </p>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  Enter the URL to the official game manual PDF. If left empty and no previous manual is found,
                  a basic game analysis will be generated but with limited accuracy.
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
                        Using previously analyzed game manual from this season
                        {setupResult.manual_info.url && (
                          <span className="block mt-1">Source: {setupResult.manual_info.url}</span>
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

              <div>
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
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">Event Management</h2>
              <p className="mb-4 text-sm text-gray-600">
                Current Event: {selectedEvent || setupResult?.event_key || "None selected"}
                <br/>Year: {year}
              </p>

              <EventArchiveManager
                currentEventKey={selectedEvent || (setupResult?.event_key ? setupResult.event_key : undefined)}
                currentYear={year}
                onArchiveSuccess={() => {
                  // Reload the page or clear setup result
                  console.log("Archive success callback triggered");
                  setSetupResult(null);
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