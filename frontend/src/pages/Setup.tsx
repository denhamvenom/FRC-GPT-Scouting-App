// frontend/src/pages/Setup.tsx

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Setup() {
  const navigate = useNavigate();
  const [year, setYear] = useState<number>(2025);
  const [manualUrl, setManualUrl] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [setupResult, setSetupResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setYear(parseInt(e.target.value));
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setManualUrl(e.target.value);
  };

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("year", year.toString());
      
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
    navigate("/schema");
  };

  // Determine if the manual was used or if we fell back to basic analysis
  const getAnalysisMethod = () => {
    if (!setupResult) return null;
    
    const manualInfo = setupResult.manual_info || {};
    
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
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">FRC Scouting Assistant Setup</h1>
      
      {!setupResult ? (
        <form onSubmit={handleSetup} className="space-y-6 bg-white p-6 rounded-lg shadow">
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
            <label className="block mb-2 font-semibold">Game Manual URL (PDF)</label>
            <input
              type="url"
              value={manualUrl}
              onChange={handleUrlChange}
              placeholder="https://firstfrc.blob.core.windows.net/frc2025/Manual/2025GameManual.pdf"
              className="w-full p-2 border rounded"
            />
            <p className="mt-1 text-sm text-gray-500">
              Enter the URL to the official game manual PDF. If left empty, a basic game analysis will be generated.
            </p>
          </div>
          
          {error && (
            <div className="p-3 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}
          
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isLoading ? "Processing..." : "Start Setup"}
          </button>
        </form>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow space-y-6">
          <h2 className="text-2xl font-semibold">Setup Complete</h2>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Game Manual Analysis</h3>
            {setupResult.game_analysis ? (
              <div className={`p-4 rounded ${
                analysisMethod === "full" ? "bg-green-50" : 
                analysisMethod === "basic" ? "bg-yellow-50" : 
                analysisMethod === "error" ? "bg-red-50" : "bg-gray-50"
              }`}>
                <div className="flex items-center mb-2">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full mr-2 ${
                    analysisMethod === "full" ? "bg-green-200 text-green-800" : 
                    analysisMethod === "basic" ? "bg-yellow-200 text-yellow-800" : 
                    analysisMethod === "error" ? "bg-red-200 text-red-800" : "bg-gray-200"
                  }`}>
                    {analysisMethod === "full" ? "FULL MANUAL ANALYSIS" : 
                     analysisMethod === "basic" ? "BASIC ANALYSIS (NO MANUAL)" : 
                     analysisMethod === "error" ? "MANUAL ERROR - FALLBACK USED" : "UNKNOWN"}
                  </span>
                  <h4 className="font-semibold">{setupResult.game_analysis.game_name}</h4>
                </div>
                
                {analysisMethod === "full" && (
                  <p className="text-green-700 text-sm mb-2">
                    Successfully analyzed game manual ({setupResult.manual_info.text_length.toLocaleString()} characters)
                  </p>
                )}
                
                {analysisMethod === "basic" && (
                  <p className="text-yellow-700 text-sm mb-2">
                    No manual provided. Using AI-generated game overview.
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
  );
}

export default Setup;