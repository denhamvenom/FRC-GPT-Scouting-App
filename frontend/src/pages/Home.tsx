// frontend/src/pages/Home.tsx

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface EventInfo {
  event_key?: string;
  event_name?: string;
  year?: number;
}

function Home() {
  const [health, setHealth] = useState<string>("Loading...");
  const [eventInfo, setEventInfo] = useState<EventInfo>({});
  const [isLoadingEvent, setIsLoadingEvent] = useState<boolean>(true);

  useEffect(() => {
    // Check backend health
    fetch("http://localhost:8000/api/health/")
      .then((res) => res.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("Error connecting to backend"));
    
    // Fetch current event info
    fetch("http://localhost:8000/api/setup/info")
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          setEventInfo({
            event_key: data.event_key,
            event_name: data.event_name,
            year: data.year
          });
        }
      })
      .catch((err) => console.error("Error fetching event info:", err))
      .finally(() => setIsLoadingEvent(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex flex-col items-center mb-8">
        <h1 className="text-4xl font-bold mb-4">FRC Strategy Assistant</h1>
        <p className="text-lg mb-4">
          A year‑agnostic, team‑agnostic, data‑agnostic toolkit for FRC event strategy
        </p>
        
        {/* Status indicators */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <span className="mr-2">Backend Status:</span>
            <span className={`px-3 py-1 rounded-full text-white ${
              health === "ok" ? "bg-green-500" : "bg-red-500"
            }`}>
              {health === "ok" ? "Connected" : "Disconnected"}
            </span>
          </div>
          
          <div className="flex items-center">
            <span className="mr-2">Current Event:</span>
            {isLoadingEvent ? (
              <span className="px-3 py-1 rounded-full bg-gray-200 text-gray-700">Loading...</span>
            ) : eventInfo.event_key ? (
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
                {eventInfo.event_name || eventInfo.event_key} ({eventInfo.year})
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full bg-yellow-100 text-yellow-800">None Selected</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <Link 
          to="/setup" 
          className="block p-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">Setup</h2>
          <p>Configure event details, upload a game manual, and setup your season parameters.</p>
        </Link>
        
        <Link 
          to="/field-selection" 
          className="block p-6 bg-green-600 text-white rounded-lg hover:bg-green-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">Field Selection</h2>
          <p>Select which fields from your scouting spreadsheet to analyze.</p>
        </Link>
        
        <Link 
          to="/validation" 
          className="block p-6 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">Validation</h2>
          <p>Flag missing or outlier match data and fix issues interactively.</p>
        </Link>
        
        <Link 
          to="/picklist" 
          className="block p-6 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">Picklist Generator</h2>
          <p>Create ranked first, second, and third pick lists based on your priorities.</p>
        </Link>
        
        <Link 
          to="/alliance-selection" 
          className="block p-6 bg-red-600 text-white rounded-lg hover:bg-red-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">Alliance Selection</h2>
          <p>Live draft tracker that strikes picked teams and re-ranks candidates.</p>
        </Link>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Project Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border p-4 rounded">
            <h3 className="font-bold text-blue-700 mb-2">Learning</h3>
            <p className="text-sm">Parse game manuals + sample data to discover optimal scouting variables.</p>
          </div>
          <div className="border p-4 rounded">
            <h3 className="font-bold text-green-700 mb-2">Validation</h3>
            <p className="text-sm">Flag missing or outlier match rows and fix issues interactively.</p>
          </div>
          <div className="border p-4 rounded">
            <h3 className="font-bold text-purple-700 mb-2">Pick-List</h3>
            <p className="text-sm">Create ranked lists based on validated data and strategic priorities.</p>
          </div>
          <div className="border p-4 rounded">
            <h3 className="font-bold text-red-700 mb-2">Alliance Selection</h3>
            <p className="text-sm">Live draft tracker that strikes picked teams and re-ranks candidates.</p>
          </div>
          <div className="border p-4 rounded col-span-2">
            <h3 className="font-bold text-gray-700 mb-2">Data Sources</h3>
            <p className="text-sm">Integrates Google Sheets (scouting), The Blue Alliance (event data), Statbotics (analytics), and GPT-4o (insights).</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;