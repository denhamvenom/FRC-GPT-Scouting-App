// frontend/src/pages/UnifiedDatasetBuilder.tsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import ProgressTracker from "../components/ProgressTracker";

function UnifiedDatasetBuilder() {
  const navigate = useNavigate();
  const [eventKey, setEventKey] = useState<string>("");
  const [year, setYear] = useState<number>(2025);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [operationId, setOperationId] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [isFetchingEventData, setIsFetchingEventData] = useState<boolean>(true);
  const [setupInfo, setSetupInfo] = useState<{event_key?: string, year?: number} | null>(null);

  // Fetch the current event information when the component mounts
  useEffect(() => {
    const fetchEventInfo = async () => {
      setIsFetchingEventData(true);
      try {
        // Try to get active event info from setup API
        const response = await fetch("http://localhost:8000/api/setup/info");

        if (response.ok) {
          const data = await response.json();

          if (data.status === "success" && data.event_key) {
            // Set eventKey and year from backend
            setEventKey(data.event_key);
            if (data.year) setYear(data.year);
            setSetupInfo(data);
          }
        }
      } catch (err) {
        console.error("Failed to fetch event info:", err);
        // Don't show error to user - just use default empty state
      } finally {
        setIsFetchingEventData(false);
      }
    };

    fetchEventInfo();
  }, []);

  const handleEventKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEventKey(e.target.value);
  };

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setYear(parseInt(e.target.value));
  };

  const handleBuildDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/api/unified/build", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_key: eventKey,
          year: year,
          force_rebuild: true,
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setOperationId(data.operation_id);
      } else {
        setError(data.detail || "Failed to start dataset build process");
      }
    } catch (err) {
      setError("Error connecting to server");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = (success: boolean) => {
    setIsComplete(true);
  };

  const handleContinue = () => {
    // Navigate to validation page instead of directly to picklist
    navigate("/validation");
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Unified Dataset Builder</h1>
      
      {!operationId ? (
        <form onSubmit={handleBuildDataset} className="space-y-6 bg-white p-6 rounded-lg shadow">
          {isFetchingEventData ? (
            <div className="text-center p-4">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
              <p className="mt-2 text-gray-600">Fetching event information...</p>
            </div>
          ) : (
            <>
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
                <label className="block mb-2 font-semibold">Event Key</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={eventKey}
                    onChange={handleEventKeyChange}
                    placeholder="e.g., 2025nyny"
                    className={`w-full p-2 border rounded ${setupInfo?.event_key ? 'bg-blue-50' : ''}`}
                    required
                  />
                  {setupInfo?.event_key && (
                    <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                      From Setup
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  {setupInfo?.event_key
                    ? `Using the event key from setup: ${setupInfo.event_key}`
                    : "Enter the TBA event key (format: YYYY[event code], e.g., 2025nyny)"}
                </p>
              </div>

              {error && (
                <div className="p-3 bg-red-100 text-red-700 rounded">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || !eventKey}
                className="w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
              >
                {isLoading ? "Starting..." : "Build Unified Dataset"}
              </button>
            </>
          )}
          
          
          <div className="text-sm text-gray-600">
            <p className="font-medium">Note:</p>
            <p>Building a unified dataset takes approximately 2-3 minutes. This process:</p>
            <ul className="list-disc list-inside ml-2 mt-1">
              <li>Fetches and processes match scouting data</li>
              <li>Fetches and processes superscouting data</li>
              <li>Pulls team data from The Blue Alliance</li>
              <li>Retrieves EPA statistics from Statbotics</li>
              <li>Merges all data into a comprehensive dataset</li>
            </ul>
          </div>
        </form>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow space-y-6">
          <h2 className="text-2xl font-semibold">Building Unified Dataset</h2>
          
          <ProgressTracker 
            operationId={operationId} 
            onComplete={handleComplete}
            pollingInterval={1500}
          />
          
          {isComplete && (
            <button
              onClick={handleContinue}
              className="w-full py-3 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Continue to Data Validation
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default UnifiedDatasetBuilder;