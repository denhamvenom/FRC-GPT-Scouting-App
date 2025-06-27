import { useEffect } from "react";
import { 
  PicklistGeneratorProps, 
  PicklistResult, 
  MissingTeamsResult,
  Team,
  PicklistAnalysis,
} from "../types";
import { useBatchProcessing } from "./useBatchProcessing";
import { apiUrl, fetchWithNgrokHeaders } from "../../../config";

interface PicklistGenerationState {
  batchProcessing: ReturnType<typeof useBatchProcessing>;
  shouldShowProgress: boolean;
  clearPicklist: () => Promise<void>;
  generatePicklist: () => Promise<void>;
  updatePicklist: () => Promise<void>;
  rankMissingTeams: () => Promise<void>;
  handleSkipMissingTeams: () => void;
  handlePositionChange: (teamIndex: number, newPosition: number) => void;
  toggleTeamSelection: (teamNumber: number) => void;
  applyComparison: (teams: Team[]) => void;
}

interface PicklistState {
  picklist: Team[];
  analysis: PicklistAnalysis | null;
  isLoading: boolean;
  estimatedTime: number;
  error: string | null;
  successMessage: string | null;
  selectedTeams: number[];
  missingTeamNumbers: number[];
  useBatching: boolean;
  setPicklist: (teams: Team[]) => void;
  setAnalysis: (analysis: PicklistAnalysis | null) => void;
  setIsLoading: (loading: boolean) => void;
  setEstimatedTime: (time: number) => void;
  setError: (error: string | null) => void;
  setSuccessMessage: (message: string | null) => void;
  setSelectedTeams: (teams: number[]) => void;
  setMissingTeamNumbers: (numbers: number[]) => void;
  setShowMissingTeamsModal: (show: boolean) => void;
  setIsRankingMissingTeams: (ranking: boolean) => void;
}

export function usePicklistGeneration(
  props: PicklistGeneratorProps,
  picklistState: PicklistState,
  paginationSetters: {
    setCurrentPage: (page: number) => void;
    setTotalPages: (pages: number) => void;
    teamsPerPage: number;
  }
): PicklistGenerationState {
  const {
    datasetPath,
    yourTeamNumber,
    pickPosition,
    priorities,
    excludeTeams = [],
    onPicklistGenerated,
    onPicklistCleared,
  } = props;

  const {
    picklist,
    analysis,
    isLoading,
    estimatedTime,
    error,
    successMessage,
    selectedTeams,
    missingTeamNumbers,
    useBatching,
    setPicklist,
    setAnalysis,
    setIsLoading,
    setEstimatedTime,
    setError,
    setSuccessMessage,
    setSelectedTeams,
    setMissingTeamNumbers,
    setShowMissingTeamsModal,
    setIsRankingMissingTeams,
  } = picklistState;

  const { setCurrentPage, setTotalPages, teamsPerPage } = paginationSetters;
  const batchProcessing = useBatchProcessing();

  const {
    batchProcessingActive,
    batchProcessingInfo,
    pollingCacheKey,
    setBatchProcessingActive,
    setBatchProcessingInfo,
    setPollingCacheKey,
  } = batchProcessing;

  const shouldShowProgress = (isLoading && !picklist.length) || batchProcessingActive;

  useEffect(() => {
    let pollingInterval: ReturnType<typeof setInterval> | null = null;

    if (batchProcessingActive && pollingCacheKey) {
      pollingInterval = setInterval(async () => {
        try {
          const response = await fetchWithNgrokHeaders(
            apiUrl("/api/picklist/generate/status"),
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ cache_key: pollingCacheKey }),
            },
          );

          if (!response.ok) {
            console.error("Error polling batch status:", response.status);
            return;
          }

          const data = await response.json();

          if (data.batch_processing) {
            setBatchProcessingInfo(data.batch_processing);

            if (data.batch_processing.processing_complete) {
              setBatchProcessingActive(false);
              if (pollingInterval) clearInterval(pollingInterval);

              if (data.picklist) {
                console.log("Processing completed picklist data:", data);

                setPicklist(data.picklist);
                if (data.analysis) setAnalysis(data.analysis);

                setBatchProcessingInfo(null);
                setPollingCacheKey(null);

                setCurrentPage(1);
                setTotalPages(Math.ceil(data.picklist.length / teamsPerPage));

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
  }, [batchProcessingActive, pollingCacheKey]);

  const fetchCompletedPicklist = async () => {
    if (!pollingCacheKey) return;

    try {
      const response = await fetchWithNgrokHeaders(
        apiUrl("/api/picklist/generate/status"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cache_key: pollingCacheKey }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to fetch completed picklist");
      }

      const data = await response.json();

      if (data.status === "success" && data.picklist) {
        setPicklist(data.picklist);
        if (data.analysis) setAnalysis(data.analysis);

        setBatchProcessingActive(false);
        setBatchProcessingInfo(null);
        setPollingCacheKey(null);

        setCurrentPage(1);
        setTotalPages(Math.ceil(data.picklist.length / teamsPerPage));

        if (onPicklistGenerated) {
          onPicklistGenerated(data);
        }
      }
    } catch (err) {
      console.error("Error fetching completed picklist:", err);
      setError("Failed to fetch the completed picklist");

      setBatchProcessingActive(false);
      setBatchProcessingInfo(null);
      setPollingCacheKey(null);
    } finally {
      setIsLoading(false);
    }
  };

  const clearPicklist = async () => {
    setPicklist([]);
    setAnalysis(null);

    try {
      const response = await fetchWithNgrokHeaders(
        apiUrl("/api/picklist/clear-cache"),
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

    setError(null);
    setSuccessMessage("Picklist cleared successfully");

    setCurrentPage(1);
    setTotalPages(1);

    setBatchProcessingActive(false);
    setBatchProcessingInfo(null);
    setPollingCacheKey(null);

    if (onPicklistCleared) {
      onPicklistCleared();
    }
  };

  const generatePicklist = async () => {
    if (!datasetPath || !yourTeamNumber || !priorities.length) {
      setError("Missing required inputs for picklist generation");
      return;
    }

    setIsLoading(true);
    setError(null);

    setBatchProcessingActive(false);
    setBatchProcessingInfo(null);
    setPollingCacheKey(null);

    const teamsToRank = excludeTeams ? 75 - excludeTeams.length : 75;
    const estimatedSeconds = teamsToRank * 0.9;
    setEstimatedTime(estimatedSeconds);

    try {
      const simplePriorities = [];
      for (const priority of priorities) {
        simplePriorities.push({
          id: priority.id,
          weight: priority.weight,
          reason: priority.reason || null,
        });
      }

      const teamsToExclude = excludeTeams || [];
      console.log(
        `Excluding ${teamsToExclude.length} teams for ${pickPosition} pick:`,
        teamsToExclude,
      );

      console.log("Current useBatching state before request:", useBatching);

      const requestBody = JSON.stringify({
        unified_dataset_path: datasetPath,
        your_team_number: yourTeamNumber,
        pick_position: pickPosition,
        priorities: simplePriorities,
        exclude_teams: teamsToExclude,
        use_batching: useBatching,
        batch_size: 60,
        reference_teams_count: 3,
        reference_selection: "top_middle_bottom",
      });

      console.log("Full request body being sent:", requestBody);

      const response = await fetchWithNgrokHeaders(
        apiUrl("/api/picklist/generate"),
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
          setBatchProcessingActive(true);
          setPollingCacheKey(data.cache_key);

          if (data.batch_processing) {
            setBatchProcessingInfo(data.batch_processing);
          } else {
            setBatchProcessingInfo({
              total_batches: 0,
              current_batch: 0,
              progress_percentage: 0,
              processing_complete: false,
            });
          }

          return;
        }
      }

      if (data.status === "success") {
        setBatchProcessingActive(false);
        setBatchProcessingInfo(null);
        setPollingCacheKey(null);

        setPicklist(data.picklist);
        setAnalysis(data.analysis);

        setEstimatedTime(0);
        setTotalPages(Math.ceil(data.picklist.length / teamsPerPage));
        setCurrentPage(1);

        if (data.missing_team_numbers && data.missing_team_numbers.length > 0) {
          const autoAddedTeamsCount = data.picklist.filter(
            (team) => team.is_fallback,
          ).length;

          if (autoAddedTeamsCount > 0) {
            setMissingTeamNumbers(data.missing_team_numbers);
            setShowMissingTeamsModal(true);
          } else {
            setMissingTeamNumbers([]);
          }
        } else {
          setMissingTeamNumbers([]);
        }

        if (onPicklistGenerated) {
          onPicklistGenerated(data);
        }
      } else {
        setError(data.message || "Error generating picklist");
      }
    } catch (err: any) {
      setError(err.message || "Error connecting to server");
      console.error("Error generating picklist:", err);

      setBatchProcessingActive(false);
      setBatchProcessingInfo(null);
      setPollingCacheKey(null);
    } finally {
      setIsLoading(false);
    }
  };

  const updatePicklist = async () => {
    if (!datasetPath || !picklist.length) {
      setError("No picklist data to update");
      return;
    }

    setIsLoading(true);
    setError(null);

    const teamsToRank = excludeTeams ? 75 - excludeTeams.length : 75;
    const estimatedSeconds = teamsToRank * 0.9;
    setEstimatedTime(estimatedSeconds);

    try {
      const userRankings = picklist.map((team, index) => ({
        team_number: team.team_number,
        position: index + 1,
        nickname: team.nickname,
      }));

      const response = await fetchWithNgrokHeaders(
        apiUrl("/api/picklist/update"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            unified_dataset_path: datasetPath,
            original_picklist: picklist,
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
        setPicklist(data.picklist);
      } else {
        setError(data.message || "Error updating picklist");
      }
    } catch (err: any) {
      setError(err.message || "Error connecting to server");
      console.error("Error updating picklist:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const rankMissingTeams = async () => {
    if (!datasetPath || !missingTeamNumbers.length) {
      setError("No missing teams to rank");
      return;
    }

    setIsRankingMissingTeams(true);
    setError(null);

    try {
      const simplePriorities = [];
      for (const priority of priorities) {
        simplePriorities.push({
          id: priority.id,
          weight: priority.weight,
          reason: priority.reason || null,
        });
      }

      const response = await fetchWithNgrokHeaders(
        apiUrl("/api/picklist/rank-missing-teams"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            unified_dataset_path: datasetPath,
            missing_team_numbers: missingTeamNumbers,
            ranked_teams: picklist,
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
        const rerankedTeamNumbers = data.missing_team_rankings.map(
          (team) => team.team_number,
        );
        const filteredPicklist = picklist.filter(
          (team) =>
            !team.is_fallback ||
            !rerankedTeamNumbers.includes(team.team_number),
        );

        const updatedPicklist = [
          ...filteredPicklist,
          ...data.missing_team_rankings,
        ];

        updatedPicklist.sort((a, b) => b.score - a.score);

        setPicklist(updatedPicklist);
        setTotalPages(Math.ceil(updatedPicklist.length / teamsPerPage));

        setSuccessMessage(
          `Successfully replaced ${data.missing_team_rankings.length} auto-added teams with proper rankings!`,
        );
        setTimeout(() => setSuccessMessage(null), 3000);

        if (onPicklistGenerated) {
          onPicklistGenerated({
            status: "success",
            picklist: updatedPicklist,
            analysis: analysis as PicklistAnalysis,
          });
        }
      } else {
        setError(data.message || "Error ranking missing teams");
      }
    } catch (err: any) {
      setError(err.message || "Error connecting to server");
      console.error("Error ranking missing teams:", err);
    } finally {
      setIsRankingMissingTeams(false);
      setShowMissingTeamsModal(false);
    }
  };

  const handleSkipMissingTeams = () => {
    setShowMissingTeamsModal(false);
    setMissingTeamNumbers([]);

    const sortedPicklist = [...picklist].sort((a, b) => b.score - a.score);
    setPicklist(sortedPicklist);
  };

  const handlePositionChange = (teamIndex: number, newPosition: number) => {
    if (newPosition < 1 || newPosition > picklist.length) {
      setError(`Position must be between 1 and ${picklist.length}`);
      setTimeout(() => setError(null), 3000);
      return;
    }

    const newIndex = newPosition - 1;
    const newPicklist = [...picklist];
    const [teamToMove] = newPicklist.splice(teamIndex, 1);
    newPicklist.splice(newIndex, 0, teamToMove);

    setPicklist(newPicklist);
    setTotalPages(Math.ceil(newPicklist.length / teamsPerPage));

    setSuccessMessage("Team position updated");
    setTimeout(() => setSuccessMessage(null), 2000);
  };

  const toggleTeamSelection = (teamNumber: number) => {
    setSelectedTeams((prev) => {
      const exists = prev.includes(teamNumber);
      if (exists) {
        return prev.filter((n) => n !== teamNumber);
      }
      if (prev.length >= 3) return prev;
      return [...prev, teamNumber];
    });
  };

  const applyComparison = (teams: Team[]) => {
    const indices = selectedTeams
      .map((num) => picklist.findIndex((t) => t.team_number === num))
      .filter((i) => i !== -1)
      .sort((a, b) => a - b);
    const newList = [...picklist];
    teams.forEach((team, idx) => {
      const targetIndex = indices[idx];
      if (targetIndex !== undefined) {
        newList[targetIndex] = team;
      }
    });
    setPicklist(newList);
    setSelectedTeams([]);
  };

  return {
    batchProcessing,
    shouldShowProgress,
    clearPicklist,
    generatePicklist,
    updatePicklist,
    rankMissingTeams,
    handleSkipMissingTeams,
    handlePositionChange,
    toggleTeamSelection,
    applyComparison,
  };
}