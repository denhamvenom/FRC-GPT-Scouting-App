// frontend/src/components/PicklistGenerator.tsx

import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

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
}

const PicklistGenerator: React.FC<PicklistGeneratorProps> = ({
  datasetPath,
  yourTeamNumber,
  pickPosition,
  priorities,
  excludeTeams = [],
  onPicklistGenerated
}) => {
  const [picklist, setPicklist] = useState<Team[]>([]);
  const [analysis, setAnalysis] = useState<PicklistAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [showAnalysis, setShowAnalysis] = useState<boolean>(false);
  
  useEffect(() => {
    // Generate picklist when component mounts or when inputs change
    generatePicklist();
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
      const requestBody = JSON.stringify({
        unified_dataset_path: datasetPath,
        your_team_number: yourTeamNumber,
        pick_position: pickPosition,
        priorities: simplePriorities,
        exclude_teams: excludeTeams || []
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
  
  const handleDragEnd = (result: any) => {
    if (!result.destination) {
      return; // Dropped outside the list
    }
    
    if (result.destination.index === result.source.index) {
      return; // Dropped in the same position
    }
    
    // Reorder the list
    const newPicklist = [...picklist];
    const [removed] = newPicklist.splice(result.source.index, 1);
    newPicklist.splice(result.destination.index, 0, removed);
    
    setPicklist(newPicklist);
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
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="picklist">
              {(provided) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className="space-y-2"
                >
                  {picklist.map((team, index) => (
                    <Draggable key={team.team_number.toString()} draggableId={team.team_number.toString()} index={index}>
                      {(provided) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className="p-3 bg-white rounded border border-gray-300 shadow-sm flex items-center"
                        >
                          <div className="mr-3 text-lg font-bold text-gray-500">{index + 1}</div>
                          <div className="flex-1">
                            <div className="font-medium">Team {team.team_number}: {team.nickname}</div>
                            <div className="text-sm text-gray-600">Score: {team.score.toFixed(2)}</div>
                          </div>
                          <div className="text-gray-400 flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
                            </svg>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
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