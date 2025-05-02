// frontend/src/pages/Home.tsx

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Home() {
  const [health, setHealth] = useState<string>("Loading...");

  useEffect(() => {
    fetch("http://localhost:8000/api/health/")
      .then((res) => res.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("Error connecting to backend"));
  }, []);

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex flex-col items-center mb-12">
        <h1 className="text-4xl font-bold mb-4">FRC Scouting Assistant</h1>
        <p className="text-lg">
          A year‑agnostic, team‑agnostic, data‑agnostic toolkit for FRC event scouting
        </p>
        <div className="mt-4 flex items-center">
          <span className="mr-2">Backend Status:</span>
          <span className={`px-3 py-1 rounded-full text-white ${
            health === "ok" ? "bg-green-500" : "bg-red-500"
          }`}>
            {health === "ok" ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <Link 
          to="/setup" 
          className="block p-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">Learning Setup</h2>
          <p>Upload a game manual and setup your season scouting parameters.</p>
        </Link>
        
        <Link 
          to="/schema" 
          className="block p-6 bg-green-600 text-white rounded-lg hover:bg-green-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">Schema Mapping</h2>
          <p>Map your scouting sheet headers to standardized variables.</p>
        </Link>
        
        <Link 
          to="/schema/superscout" 
          className="block p-6 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transform hover:scale-105 transition"
        >
          <h2 className="text-xl font-bold mb-3">SuperScout Mapping</h2>
          <p>Map qualitative SuperScouting data for strategy insights.</p>
        </Link>
        
        <div className="block p-6 bg-gray-600 text-white rounded-lg opacity-70">
          <h2 className="text-xl font-bold mb-3">Validation (Coming Soon)</h2>
          <p>Flag missing or outlier match data and fix issues.</p>
        </div>
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