// frontend/src/pages/PicklistNew.tsx

import React, { useState, useEffect } from 'react';
import { useApiContext } from '../providers/ApiProvider';
import { PicklistGenerator } from './PicklistNew/components';
import { Team } from './PicklistNew/types';

const PicklistNew: React.FC = () => {
  const { apiClient } = useApiContext();
  
  // State for picklist configuration
  const [datasetPath, setDatasetPath] = useState<string>('');
  const [yourTeamNumber, setYourTeamNumber] = useState<number>(0);
  const [pickPosition, setPickPosition] = useState<string>('first');
  const [priorities, setPriorities] = useState<string>('');
  const [excludeTeams, setExcludeTeams] = useState<number[]>([]);
  const [picklist, setPicklist] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Fetch event info and configuration on mount
  useEffect(() => {
    const fetchEventInfo = async () => {
      try {
        // Get setup info which contains event_key and team_number
        const setupResponse = await apiClient.get('/setup/info');
        if (setupResponse.event_key) {
          setDatasetPath(`/app/data/unified_event_${setupResponse.event_key}.json`);
          setYourTeamNumber(setupResponse.team_number || 0);
        }
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching event info:', error);
        setIsLoading(false);
      }
    };
    
    fetchEventInfo();
  }, [apiClient]);
  
  const handlePicklistGenerated = (generatedPicklist: Team[]) => {
    setPicklist(generatedPicklist);
  };
  
  const handleExcludeTeam = (teamNumber: number) => {
    setExcludeTeams(prev => [...prev, teamNumber]);
  };
  
  const handlePicklistCleared = () => {
    setPicklist([]);
  };
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading event information...</p>
        </div>
      </div>
    );
  }
  
  if (!datasetPath) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Setup Required
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>Please complete the setup process before generating a picklist.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Picklist Generator</h1>
        
        <PicklistGenerator
          datasetPath={datasetPath}
          yourTeamNumber={yourTeamNumber}
          pickPosition={pickPosition}
          priorities={priorities}
          allPriorities={[]}
          excludeTeams={excludeTeams}
          onPicklistGenerated={handlePicklistGenerated}
          initialPicklist={picklist}
          onExcludeTeam={handleExcludeTeam}
          isLocked={false}
          onPicklistCleared={handlePicklistCleared}
          useBatching={true}
        />
      </div>
    </div>
  );
};

export default PicklistNew;