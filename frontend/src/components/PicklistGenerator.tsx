// frontend/src/components/PicklistGenerator.tsx

import React, { useState, useEffect } from 'react';

interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
}

interface MetricPriority {
  id: string;
  weight: number;
  reason?: string;
}

interface PicklistAnalysis {
  draft_reasoning: string;
  evaluation: string;
  final_recommendations: string;
}

interface PicklistResult {
  status: string;
  picklist: Team[];
  analysis: PicklistAnalysis;
  message?: string;
}

interface PicklistGeneratorProps {
  datasetPath: string;
  yourTeamNumber: number;
  pickPosition: 'first' | 'second' | 'third';
  priorities: MetricPriority[];
  excludeTeams?: number[];
  onPicklistGenerated?: (result: PicklistResult) => void;
  initialPicklist?: Team[]; // Add prop for initial picklist data
}

const PicklistGenerator: React.FC<PicklistGeneratorProps> = ({
  datasetPath,
  yourTeamNumber,
  pickPosition,
  priorities,
  excludeTeams = [],
  onPicklistGenerated,
  initialPicklist = []
}) => {
  const [picklist, setPicklist] = useState<Team[]>(initialPicklist);
  const [analysis, setAnalysis] = useState<PicklistAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [showAnalysis, setShowAnalysis] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  useEffect(() => {
    // Log when dependencies change
    console.log("PicklistGenerator dependencies changed:", { 
      pickPosition, 
      prioritiesCount: priorities.length,
      excludeTeamsCount: excludeTeams?.length
    });
    
    if (excludeTeams && excludeTeams.length > 0) {
      console.log("Teams to exclude:", excludeTeams);
    }
    
    // If we have an initial picklist, use it
    if (initialPicklist && initialPicklist.length > 0) {
      setPicklist(initialPicklist);
    } else {
      // Otherwise generate a new picklist
      generatePicklist();
    }
  }, [datasetPath, yourTeamNumber, pickPosition, JSON.stringify(priorities), JSON.stringify(excludeTeams)]);
  
  const generatePicklist = async () => {
    if (!datasetPath || !yourTeamNumber || !priorities.length) {
      setError('Missing required inputs for picklist generation');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Send the priorities as plain JSON objects without any methods or class structures
      const simplePriorities = [];
      for (const priority of priorities) {
        simplePriorities.push({
          id: priority.id,
          weight: priority.weight,
          reason: priority.reason || null
        });
      }
      
      // Create a request object with all primitive values
      // Ensure excludeTeams is always an array and log it
      const teamsToExclude = excludeTeams || [];
      console.log(`Excluding ${teamsToExclude.length} teams for ${pickPosition} pick:`, teamsToExclude);
      
      const requestBody = JSON.stringify({
        unified_dataset_path: datasetPath,
        your_team_number: yourTeamNumber,
        pick_position: pickPosition,
        priorities: simplePriorities,
        exclude_teams: teamsToExclude
      });
      
      console.log('Sending request:', requestBody);
      
      const response = await fetch('http://localhost:8000/api/picklist/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: requestBody
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate picklist');
      }
      
      const data: PicklistResult = await response.json();
      
      if (data.status === 'success') {
        setPicklist(data.picklist);
        setAnalysis(data.analysis);
        
        // Call the callback if provided
        if (onPicklistGenerated) {
          onPicklistGenerated(data);
        }
      } else {
        setError(data.message || 'Error generating picklist');
      }
    } catch (err: any) {
      setError(err.message || 'Error connecting to server');
      console.error('Error generating picklist:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const updatePicklist = async () => {
    if (!datasetPath || !picklist.length) {
      setError('No picklist data to update');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Convert picklist to user rankings format
      const userRankings = picklist.map((team, index) => ({
        team_number: team.team_number,
        position: index + 1,
        nickname: team.nickname
      }));
      
      const response = await fetch('http://localhost:8000/api/picklist/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          unified_dataset_path: datasetPath,
          original_picklist: picklist,
          user_rankings: userRankings
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update picklist');
      }
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setPicklist(data.picklist);
        setIsEditing(false);
      } else {
        setError(data.message || 'Error updating picklist');
      }
    } catch (err: any) {
      setError(err.message || 'Error connecting to server');
      console.error('Error updating picklist:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle team position change
  const handlePositionChange = (teamIndex: number, newPosition: number) => {
    // Validate the new position
    if (newPosition < 1 || newPosition > picklist.length) {
      setError(`Position must be between 1 and ${picklist.length}`);
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    // Convert from 1-based UI position to 0-based array index
    const newIndex = newPosition - 1;
    
    // Create a copy of the current picklist
    const newPicklist = [...picklist];
    
    // Remove the team from its current position
    const [teamToMove] = newPicklist.splice(teamIndex, 1);
    
    // Insert the team at the new position
    newPicklist.splice(newIndex, 0, teamToMove);
    
    // Update the picklist
    setPicklist(newPicklist);
    
    // Show feedback that rankings changed
    setSuccessMessage('Team position updated');
    setTimeout(() => setSuccessMessage(null), 2000);
  };
  
  if (isLoading && !picklist.length) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-blue-600">Generating picklist...</span>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">
          {pickPosition.charAt(0).toUpperCase() + pickPosition.slice(1)} Pick Rankings
        </h2>
        <div className="flex space-x-2">
          {isEditing ? (
            <>
              <button
                onClick={updatePicklist}
                disabled={isLoading}
                className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
              >
                Save Changes
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Edit Rankings
              </button>
              <button
                onClick={() => setShowAnalysis(!showAnalysis)}
                className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                {showAnalysis ? 'Hide Analysis' : 'Show Analysis'}
              </button>
              <button
                onClick={generatePicklist}
                disabled={isLoading}
                className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
              >
                {isLoading ? 'Regenerating...' : 'Regenerate'}
              </button>
            </>
          )}
        </div>
      </div>
      
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {successMessage}
        </div>
      )}
      
      {showAnalysis && analysis && (
        <div className="mb-6 bg-purple-50 p-4 rounded-lg border border-purple-200">
          <h3 className="font-bold text-purple-800 mb-2">GPT Analysis</h3>
          
          <div className="space-y-3">
            <div>
              <h4 className="font-semibold text-purple-700">Draft Reasoning:</h4>
              <p className="text-sm text-gray-700">{analysis.draft_reasoning}</p>
            </div>
            
            <div>
              <h4 className="font-semibold text-purple-700">Critical Evaluation:</h4>
              <p className="text-sm text-gray-700">{analysis.evaluation}</p>
            </div>
            
            <div>
              <h4 className="font-semibold text-purple-700">Final Recommendations:</h4>
              <p className="text-sm text-gray-700">{analysis.final_recommendations}</p>
            </div>
          </div>
        </div>
      )}
      
      <div className="overflow-hidden">
        {isEditing ? (
          <div className="space-y-3">
            <p className="text-sm text-blue-600 italic mb-2">
              Edit team positions by changing their rank numbers, then click "Save Changes" when done.
            </p>
            
            {picklist.map((team, index) => (
              <div 
                key={team.team_number} 
                className="p-3 bg-white rounded border border-gray-300 shadow-sm flex items-center hover:bg-blue-50 transition-colors duration-150"
              >
                <div className="mr-3 flex items-center">
                  <input
                    type="number"
                    min="1"
                    max={picklist.length}
                    value={index + 1}
                    onChange={(e) => handlePositionChange(index, parseInt(e.target.value) || 1)}
                    className="w-12 p-1 border border-gray-300 rounded text-center font-bold text-blue-600"
                  />
                </div>
                <div className="flex-1">
                  <div className="font-medium">Team {team.team_number}: {team.nickname}</div>
                  <div className="text-sm text-gray-600">Score: {team.score.toFixed(2)}</div>
                </div>
                <div className="text-gray-400 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {picklist.map((team, index) => (
              <div key={team.team_number} className="p-3 bg-white rounded border flex hover:bg-gray-50">
                <div className="mr-3 text-lg font-bold text-gray-500">{index + 1}</div>
                <div>
                  <div className="font-medium">Team {team.team_number}: {team.nickname}</div>
                  <div className="text-sm text-gray-600">Score: {team.score.toFixed(2)}</div>
                  <div className="text-sm mt-1">{team.reasoning}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PicklistGenerator;