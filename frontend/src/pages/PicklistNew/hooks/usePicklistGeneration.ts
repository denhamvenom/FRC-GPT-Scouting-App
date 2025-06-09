// frontend/src/pages/PicklistNew/hooks/usePicklistGeneration.ts

import { useState, useEffect, useCallback } from 'react';
import { 
  UsePicklistGeneration, 
  PicklistGenerationState, 
  BatchProcessingState,
  MetricPriority,
  PicklistResult,
  MissingTeamsResult,
  Team,
  PicklistAnalysis,
  PickPosition
} from '../types';

interface UsePicklistGenerationParams {
  datasetPath: string;
  yourTeamNumber: number;
  pickPosition: PickPosition;
  priorities: MetricPriority[];
  excludeTeams: number[];
  useBatching: boolean;
  onPicklistGenerated?: (result: PicklistResult) => void;
  onPicklistCleared?: () => void;
  initialPicklist?: Team[];
}

export const usePicklistGeneration = ({
  datasetPath,
  yourTeamNumber,
  pickPosition,
  priorities,
  excludeTeams,
  useBatching,
  onPicklistGenerated,
  onPicklistCleared,
  initialPicklist = [],
}: UsePicklistGenerationParams): UsePicklistGeneration => {
  
  // Main generation state
  const [state, setState] = useState<PicklistGenerationState>({
    picklist: initialPicklist,
    analysis: null,
    isLoading: false,
    estimatedTime: 0,
    error: null,
    successMessage: null,
    missingTeamNumbers: [],
    showMissingTeamsModal: false,
    isRankingMissingTeams: false,
  });

  // Batch processing state
  const [batchState, setBatchState] = useState<BatchProcessingState>({
    batchProcessingActive: false,
    batchProcessingInfo: null,
    pollingCacheKey: null,
    elapsedTime: 0,
  });

  // Update picklist when initialPicklist changes
  useEffect(() => {
    if (initialPicklist && initialPicklist.length > 0) {
      setState(prev => ({ ...prev, picklist: initialPicklist }));
    }
  }, [initialPicklist]);

  // Elapsed time counter for batch processing
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;

    if (batchState.batchProcessingActive) {
      timer = setInterval(() => {
        setBatchState(prev => ({ ...prev, elapsedTime: prev.elapsedTime + 0.1 }));
      }, 100);
    } else {
      setBatchState(prev => ({ ...prev, elapsedTime: 0 }));
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [batchState.batchProcessingActive]);

  // Polling effect for batch processing status
  useEffect(() => {
    let pollingInterval: ReturnType<typeof setInterval> | null = null;

    if (batchState.batchProcessingActive && batchState.pollingCacheKey) {
      pollingInterval = setInterval(async () => {
        try {
          const response = await fetch(
            "http://localhost:8000/api/picklist/generate/status",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ cache_key: batchState.pollingCacheKey }),
            },
          );

          if (!response.ok) {
            console.error("Error polling batch status:", response.status);
            return;
          }

          const data = await response.json();

          if (data.batch_processing) {
            setBatchState(prev => ({ ...prev, batchProcessingInfo: data.batch_processing }));

            if (data.batch_processing.processing_complete) {
              setBatchState(prev => ({ ...prev, batchProcessingActive: false }));
              if (pollingInterval) clearInterval(pollingInterval);

              if (data.picklist) {
                setState(prev => ({
                  ...prev,
                  picklist: data.picklist,
                  analysis: data.analysis || null,
                  isLoading: false,
                }));

                setBatchState({
                  batchProcessingActive: false,
                  batchProcessingInfo: null,
                  pollingCacheKey: null,
                  elapsedTime: 0,
                });

                if (onPicklistGenerated) {
                  onPicklistGenerated(data);
                }
              } else {
                await fetchCompletedPicklist();
              }
            }
          }
        } catch (err) {
          console.error("Error polling batch status:", err);
        }
      }, 5000);
    }

    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [batchState.batchProcessingActive, batchState.pollingCacheKey, onPicklistGenerated]);

  // Function to fetch completed picklist
  const fetchCompletedPicklist = async () => {
    if (!batchState.pollingCacheKey) return;

    try {
      const response = await fetch(
        "http://localhost:8000/api/picklist/generate/status",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cache_key: batchState.pollingCacheKey }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to fetch completed picklist");
      }

      const data = await response.json();

      if (data.status === "success" && data.picklist) {
        setState(prev => ({
          ...prev,
          picklist: data.picklist,
          analysis: data.analysis || null,
          isLoading: false,
        }));

        setBatchState({
          batchProcessingActive: false,
          batchProcessingInfo: null,
          pollingCacheKey: null,
          elapsedTime: 0,
        });

        if (onPicklistGenerated) {
          onPicklistGenerated(data);
        }
      }
    } catch (err) {
      console.error("Error fetching completed picklist:", err);
      setState(prev => ({ ...prev, error: "Failed to fetch the completed picklist", isLoading: false }));
      setBatchState({
        batchProcessingActive: false,
        batchProcessingInfo: null,
        pollingCacheKey: null,
        elapsedTime: 0,
      });
    }
  };

  const generatePicklist = useCallback(async () => {
    if (!datasetPath || !yourTeamNumber || !priorities.length) {
      setState(prev => ({ ...prev, error: "Missing required inputs for picklist generation" }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    setBatchState({
      batchProcessingActive: false,
      batchProcessingInfo: null,
      pollingCacheKey: null,
      elapsedTime: 0,
    });

    // Calculate estimated time
    const teamsToRank = excludeTeams ? 75 - excludeTeams.length : 75;
    const estimatedSeconds = teamsToRank * 0.9;
    setState(prev => ({ ...prev, estimatedTime: estimatedSeconds }));

    try {
      const simplePriorities = priorities.map(priority => ({
        id: priority.id,
        weight: priority.weight,
        reason: priority.reason || null,
      }));

      const requestBody = JSON.stringify({
        unified_dataset_path: datasetPath,
        your_team_number: yourTeamNumber,
        pick_position: pickPosition,
        priorities: simplePriorities,
        exclude_teams: excludeTeams,
        use_batching: useBatching,
        batch_size: 20,
        reference_teams_count: 3,
        reference_selection: "top_middle_bottom",
      });

      console.log("Generating picklist with request:", requestBody);

      const response = await fetch(
        "http://localhost:8000/api/picklist/generate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: requestBody,
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate picklist");
      }

      const data: PicklistResult = await response.json();

      if (data.status === "success" && data.batched) {
        console.log("Batch processing initiated", data);

        if (data.cache_key) {
          setBatchState({
            batchProcessingActive: true,
            batchProcessingInfo: data.batch_processing || {
              total_batches: 0,
              current_batch: 0,
              progress_percentage: 0,
              processing_complete: false,
            },
            pollingCacheKey: data.cache_key,
            elapsedTime: 0,
          });
          return;
        }
      }

      // For non-batched results or immediate completion
      if (data.status === "success") {
        setBatchState({
          batchProcessingActive: false,
          batchProcessingInfo: null,
          pollingCacheKey: null,
          elapsedTime: 0,
        });

        setState(prev => ({
          ...prev,
          picklist: data.picklist,
          analysis: data.analysis,
          estimatedTime: 0,
          isLoading: false,
        }));

        // Check for missing teams
        if (data.missing_team_numbers && data.missing_team_numbers.length > 0) {
          const autoAddedTeamsCount = data.picklist.filter(team => team.is_fallback).length;
          
          if (autoAddedTeamsCount > 0) {
            setState(prev => ({
              ...prev,
              missingTeamNumbers: data.missing_team_numbers || [],
              showMissingTeamsModal: true,
            }));
          }
        }

        if (onPicklistGenerated) {
          onPicklistGenerated(data);
        }
      } else {
        setState(prev => ({ ...prev, error: data.message || "Error generating picklist", isLoading: false }));
      }
    } catch (err: any) {
      setState(prev => ({ 
        ...prev, 
        error: err.message || "Error connecting to server", 
        isLoading: false 
      }));
      console.error("Error generating picklist:", err);

      setBatchState({
        batchProcessingActive: false,
        batchProcessingInfo: null,
        pollingCacheKey: null,
        elapsedTime: 0,
      });
    }
  }, [datasetPath, yourTeamNumber, pickPosition, priorities, excludeTeams, useBatching, onPicklistGenerated]);

  const updatePicklist = useCallback(async () => {
    if (!datasetPath || !state.picklist.length) {
      setState(prev => ({ ...prev, error: "No picklist data to update" }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const userRankings = state.picklist.map((team, index) => ({
        team_number: team.team_number,
        position: index + 1,
        nickname: team.nickname,
      }));

      const response = await fetch(
        "http://localhost:8000/api/picklist/update",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            unified_dataset_path: datasetPath,
            original_picklist: state.picklist,
            user_rankings: userRankings,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update picklist");
      }

      const data = await response.json();

      if (data.status === "success") {
        setState(prev => ({ 
          ...prev, 
          picklist: data.picklist, 
          isLoading: false,
          successMessage: "Picklist updated successfully"
        }));
        setTimeout(() => setState(prev => ({ ...prev, successMessage: null })), 3000);
      } else {
        setState(prev => ({ ...prev, error: data.message || "Error updating picklist", isLoading: false }));
      }
    } catch (err: any) {
      setState(prev => ({ 
        ...prev, 
        error: err.message || "Error connecting to server", 
        isLoading: false 
      }));
      console.error("Error updating picklist:", err);
    }
  }, [datasetPath, state.picklist]);

  const clearPicklist = useCallback(async () => {
    setState(prev => ({ 
      ...prev, 
      picklist: [], 
      analysis: null, 
      error: null,
      successMessage: "Picklist cleared successfully"
    }));

    setTimeout(() => setState(prev => ({ ...prev, successMessage: null })), 3000);

    try {
      const response = await fetch(
        "http://localhost:8000/api/picklist/clear-cache",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
      );

      if (!response.ok) {
        console.error("Failed to clear backend cache");
      } else {
        const result = await response.json();
        console.log("Cache cleared:", result.message);
      }
    } catch (error) {
      console.error("Error clearing cache:", error);
    }

    setBatchState({
      batchProcessingActive: false,
      batchProcessingInfo: null,
      pollingCacheKey: null,
      elapsedTime: 0,
    });

    if (onPicklistCleared) {
      onPicklistCleared();
    }
  }, [onPicklistCleared]);

  const rankMissingTeams = useCallback(async () => {
    if (!datasetPath || !state.missingTeamNumbers.length) {
      setState(prev => ({ ...prev, error: "No missing teams to rank" }));
      return;
    }

    setState(prev => ({ ...prev, isRankingMissingTeams: true, error: null }));

    try {
      const simplePriorities = priorities.map(priority => ({
        id: priority.id,
        weight: priority.weight,
        reason: priority.reason || null,
      }));

      const response = await fetch(
        "http://localhost:8000/api/picklist/rank-missing-teams",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            unified_dataset_path: datasetPath,
            missing_team_numbers: state.missingTeamNumbers,
            ranked_teams: state.picklist,
            your_team_number: yourTeamNumber,
            pick_position: pickPosition,
            priorities: simplePriorities,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to rank missing teams");
      }

      const data: MissingTeamsResult = await response.json();

      if (data.status === "success" && data.missing_team_rankings) {
        const rerankedTeamNumbers = data.missing_team_rankings.map(team => team.team_number);
        const filteredPicklist = state.picklist.filter(
          team => !team.is_fallback || !rerankedTeamNumbers.includes(team.team_number)
        );

        const updatedPicklist = [...filteredPicklist, ...data.missing_team_rankings];
        updatedPicklist.sort((a, b) => b.score - a.score);

        setState(prev => ({
          ...prev,
          picklist: updatedPicklist,
          isRankingMissingTeams: false,
          showMissingTeamsModal: false,
          successMessage: `Successfully replaced ${data.missing_team_rankings.length} auto-added teams with proper rankings!`
        }));

        setTimeout(() => setState(prev => ({ ...prev, successMessage: null })), 3000);

        if (onPicklistGenerated) {
          onPicklistGenerated({
            status: "success",
            picklist: updatedPicklist,
            analysis: state.analysis as PicklistAnalysis,
          });
        }
      } else {
        setState(prev => ({ ...prev, error: data.message || "Error ranking missing teams", isRankingMissingTeams: false }));
      }
    } catch (err: any) {
      setState(prev => ({ 
        ...prev, 
        error: err.message || "Error connecting to server", 
        isRankingMissingTeams: false 
      }));
      console.error("Error ranking missing teams:", err);
    } finally {
      setState(prev => ({ ...prev, showMissingTeamsModal: false }));
    }
  }, [datasetPath, state.missingTeamNumbers, state.picklist, state.analysis, yourTeamNumber, pickPosition, priorities, onPicklistGenerated]);

  const handleSkipMissingTeams = useCallback(() => {
    setState(prev => ({
      ...prev,
      showMissingTeamsModal: false,
      missingTeamNumbers: [],
      picklist: [...prev.picklist].sort((a, b) => b.score - a.score),
    }));
  }, []);

  return {
    state,
    batchState,
    actions: {
      generatePicklist,
      updatePicklist,
      clearPicklist,
      rankMissingTeams,
      handleSkipMissingTeams,
    },
  };
};