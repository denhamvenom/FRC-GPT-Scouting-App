import { useState, useEffect } from 'react';

// TypeScript interfaces for unified data structure
export interface TeamScoutingData {
  match_number: number;
  qual_number: number;
  team_number: number;
  auto: number;
  teleop: number;
  endgame: number;
  auto_coral_L1_scored: number;
  auto_coral_L2_scored: number;
  auto_coral_L3_scored: number;
  auto_coral_L4_scored: number;
  auto_net_score: number;
  auto_algae_processor_scored: number;
  'Auto Total Points': number;
  teleop_coral_L1_scored: number;
  teleop_coral_L2_scored: number;
  teleop_coral_L3_scored: number;
  teleop_coral_L4_scored: number;
  teleop_net_score: number;
  teleop_algae_processor_scored: number;
  'Teleop Total Points': number;
  endgame_ascent_level: number;
  endgame_shallow_ascent: number;
  endgame_deep_ascent: number;
  endgame_park: number;
  'Endgame Total Points': number;
  total_points: number;
  penalty_total: number;
  'Match Total Points': number;
  // Allow for additional dynamic fields
  [key: string]: any;
}

export interface TeamData {
  team_number: number;
  nickname: string;
  scouting_data: TeamScoutingData[];
  stats?: {
    [key: string]: any;
  };
}

export interface ExpectedMatch {
  match_number: number;
  team_number: number;
  alliance_color: string;
}

export interface UnifiedDataResponse {
  event_key: string;
  year: number;
  expected_matches: ExpectedMatch[];
  teams: {
    [teamNumber: string]: TeamData;
  };
}

export interface UseUnifiedDataReturn {
  data: UnifiedDataResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

// Helper function to get API base URL
const getApiBaseUrl = (): string => {
  // Check if we're in development and have a config
  if (typeof window !== 'undefined' && (window as any).APP_CONFIG?.apiBaseUrl) {
    return (window as any).APP_CONFIG.apiBaseUrl;
  }
  
  // Default to localhost for development
  return 'http://localhost:8000';
};

// Helper function to make API requests with proper headers
const fetchWithHeaders = async (url: string): Promise<Response> => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add ngrok headers if in development
  if (process.env.NODE_ENV === 'development') {
    headers['ngrok-skip-browser-warning'] = 'true';
  }

  return fetch(url, {
    method: 'GET',
    headers,
  });
};

export const useUnifiedData = (eventKey?: string): UseUnifiedDataReturn => {
  const [data, setData] = useState<UnifiedDataResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUnifiedData = async (targetEventKey?: string) => {
    setLoading(true);
    setError(null);

    try {
      // Validate event key before making the request
      if (!targetEventKey || targetEventKey.trim() === '') {
        throw new Error('Event key is required to fetch unified data');
      }

      const baseUrl = getApiBaseUrl();
      const url = `${baseUrl}/api/unified/dataset?event_key=${encodeURIComponent(targetEventKey)}`;

      console.log('Fetching unified data from:', url);
      
      const response = await fetchWithHeaders(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: UnifiedDataResponse = await response.json();
      
      // Validate the response structure
      if (!result.event_key || !result.teams) {
        throw new Error('Invalid unified data response structure');
      }

      setData(result);
      console.log('Unified data loaded successfully:', {
        event_key: result.event_key,
        year: result.year,
        team_count: Object.keys(result.teams).length,
        expected_matches: result.expected_matches?.length || 0
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Failed to load unified data: ${errorMessage}`);
      console.error('Error fetching unified data:', err);
    } finally {
      setLoading(false);
    }
  };

  const refetch = () => {
    // Only refetch if eventKey is valid
    if (eventKey && eventKey.trim() !== '') {
      fetchUnifiedData(eventKey);
    }
  };

  // Fetch data on mount and when eventKey changes
  useEffect(() => {
    // Only fetch if eventKey is provided and not empty
    if (eventKey && eventKey.trim() !== '') {
      fetchUnifiedData(eventKey);
    } else {
      // Clear previous data if eventKey is empty
      setData(null);
      setError(null);
      setLoading(false);
    }
  }, [eventKey]);

  return {
    data,
    loading,
    error,
    refetch
  };
};

// Helper function to extract numeric metrics from team data
export const extractNumericMetrics = (teamData: TeamData): { [key: string]: number } => {
  const metrics: { [key: string]: number } = {};
  
  if (teamData.scouting_data && teamData.scouting_data.length > 0) {
    // Get the first match data as sample (will be improved in Sprint 2)
    const sampleMatch = teamData.scouting_data[0];
    
    // Extract numeric fields
    Object.entries(sampleMatch).forEach(([key, value]) => {
      if (typeof value === 'number' && key !== 'match_number' && key !== 'qual_number' && key !== 'team_number') {
        metrics[key] = value;
      }
    });
  }
  
  return metrics;
};

// Helper function to get available teams from unified data
export const getAvailableTeams = (unifiedData: UnifiedDataResponse | null): Array<{ team_number: number; nickname: string }> => {
  if (!unifiedData?.teams) return [];
  
  return Object.values(unifiedData.teams).map(team => ({
    team_number: team.team_number,
    nickname: team.nickname
  }));
};

export default useUnifiedData;