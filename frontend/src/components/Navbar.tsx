// frontend/src/components/Navbar.tsx

import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { apiUrl, fetchWithNgrokHeaders } from "../config";
import ProgressTracker from "./ProgressTracker";

function Navbar() {
  const location = useLocation();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string | null>(null);
  const [operationId, setOperationId] = useState<string | null>(null);
  const [showProgress, setShowProgress] = useState(false);
  
  // Helper to determine if a link is active
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  // Handle refresh scouting data
  const handleRefreshData = async () => {
    setIsRefreshing(true);
    setRefreshStatus(null);

    try {
      // First, get current event info
      const setupResponse = await fetchWithNgrokHeaders(apiUrl("/api/setup/info"));
      let eventKey = "";
      let year = 2025;

      if (setupResponse.ok) {
        const setupData = await setupResponse.json();
        if (setupData.status === "success" && setupData.event_key) {
          eventKey = setupData.event_key;
          if (setupData.year) year = setupData.year;
        }
      }

      if (!eventKey) {
        setRefreshStatus("No active event found. Please complete setup first.");
        return;
      }

      // Trigger unified dataset rebuild with force_rebuild: true
      const response = await fetchWithNgrokHeaders(apiUrl("/api/unified/build"), {
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
        if (data.operation_id) {
          // Show progress tracker for the operation
          setOperationId(data.operation_id);
          setShowProgress(true);
          setRefreshStatus("Data refresh in progress...");
        } else {
          setRefreshStatus("Data refresh started successfully!");
          
          // Auto-clear success message after 3 seconds
          setTimeout(() => {
            setRefreshStatus(null);
          }, 3000);
        }
      } else {
        setRefreshStatus(data.detail || "Failed to start data refresh");
      }
    } catch (err) {
      console.error("Error refreshing data:", err);
      setRefreshStatus("Error connecting to server");
    } finally {
      // Only set isRefreshing to false if we're not showing progress
      if (!showProgress) {
        setIsRefreshing(false);
      }
    }
  };

  // Handle completion of the data refresh operation
  const handleRefreshComplete = (success: boolean) => {
    setShowProgress(false);
    setIsRefreshing(false);
    setOperationId(null);
    
    if (success) {
      setRefreshStatus("✅ Data refresh completed successfully!");
    } else {
      setRefreshStatus("❌ Data refresh failed. Please check the logs.");
    }
    
    // Auto-clear completion message after 5 seconds
    setTimeout(() => {
      setRefreshStatus(null);
    }, 5000);
  };

  return (
    <nav className="bg-blue-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold">FRC Strategy Assistant</span>
            </Link>
          </div>
          
          <div className="flex items-center">
            <div className="flex space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Home
              </Link>
              
              <Link
                to="/setup"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/setup") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Setup
              </Link>
              
              <Link
                to="/validation"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/validation") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Validation
              </Link>
              
              <Link
                to="/picklist"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/picklist") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Picklist
              </Link>
              
              <Link
                to="/alliance-selection"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname.startsWith("/alliance-selection") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Alliance Selection
              </Link>
              
              {/* Refresh Scouting Data Button */}
              <button
                onClick={handleRefreshData}
                disabled={isRefreshing}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isRefreshing
                    ? "bg-gray-600 text-gray-300 cursor-not-allowed" 
                    : "bg-green-600 text-white hover:bg-green-700"
                }`}
                title="Pull latest data from Google Sheets and rebuild unified database"
              >
                {isRefreshing ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Refreshing...
                  </div>
                ) : (
                  <div className="flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh Data
                  </div>
                )}
              </button>
            </div>
          </div>
        </div>
        
        
        {/* Status notification */}
        {refreshStatus && !showProgress && (
          <div className={`mx-4 pb-2 p-2 rounded text-sm ${
            refreshStatus.includes("successfully") || refreshStatus.includes("✅")
              ? "bg-green-100 text-green-800 border border-green-200" 
              : refreshStatus.includes("❌") || refreshStatus.includes("failed") || refreshStatus.includes("Error")
              ? "bg-red-100 text-red-800 border border-red-200"
              : "bg-blue-100 text-blue-800 border border-blue-200"
          }`}>
            {refreshStatus}
          </div>
        )}

        {/* Progress tracker for data refresh */}
        {showProgress && operationId && (
          <div className="mx-4 pb-2">
            <div className="bg-white rounded-lg border shadow-sm p-4">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">
                🔄 Refreshing Scouting Data
              </h4>
              <ProgressTracker 
                operationId={operationId} 
                onComplete={handleRefreshComplete}
                pollingInterval={1000} // Poll every second for faster updates
              />
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;