import { useState, useEffect } from "react";
import { Team, PicklistAnalysis, PicklistGeneratorProps } from "../types";
import { useLocalStorageState } from "./useLocalStorageState";

interface PicklistState {
  picklist: Team[];
  analysis: PicklistAnalysis | null;
  isLoading: boolean;
  estimatedTime: number;
  error: string | null;
  isEditing: boolean;
  showAnalysis: boolean;
  successMessage: string | null;
  selectedTeams: number[];
  showComparison: boolean;
  missingTeamNumbers: number[];
  showMissingTeamsModal: boolean;
  isRankingMissingTeams: boolean;
  useBatching: boolean;
  setPicklist: (teams: Team[]) => void;
  setAnalysis: (analysis: PicklistAnalysis | null) => void;
  setIsLoading: (loading: boolean) => void;
  setEstimatedTime: (time: number) => void;
  setError: (error: string | null) => void;
  setIsEditing: (editing: boolean) => void;
  setShowAnalysis: (show: boolean) => void;
  setSuccessMessage: (message: string | null) => void;
  setSelectedTeams: (teams: number[]) => void;
  setShowComparison: (show: boolean) => void;
  setMissingTeamNumbers: (numbers: number[]) => void;
  setShowMissingTeamsModal: (show: boolean) => void;
  setIsRankingMissingTeams: (ranking: boolean) => void;
  setUseBatching: (batching: boolean) => void;
}

export function usePicklistState(props: PicklistGeneratorProps): PicklistState {
  const {
    datasetPath,
    yourTeamNumber,
    pickPosition,
    priorities,
    excludeTeams = [],
    initialPicklist = [],
  } = props;

  const [picklist, setPicklist] = useState<Team[]>(initialPicklist);
  const [analysis, setAnalysis] = useState<PicklistAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [estimatedTime, setEstimatedTime] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [showAnalysis, setShowAnalysis] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [selectedTeams, setSelectedTeams] = useState<number[]>([]);
  const [showComparison, setShowComparison] = useState<boolean>(false);

  const [missingTeamNumbers, setMissingTeamNumbers] = useState<number[]>([]);
  const [showMissingTeamsModal, setShowMissingTeamsModal] = useState<boolean>(false);
  const [isRankingMissingTeams, setIsRankingMissingTeams] = useState<boolean>(false);

  const [useBatching, setUseBatching] = useLocalStorageState("useBatching", false);

  useEffect(() => {
    console.log("PicklistGenerator dependencies changed:", {
      pickPosition,
      prioritiesCount: priorities.length,
      excludeTeamsCount: excludeTeams?.length,
    });

    if (excludeTeams && excludeTeams.length > 0) {
      console.log("Teams to exclude:", excludeTeams);
    }

    if (initialPicklist && initialPicklist.length > 0) {
      setPicklist(initialPicklist);
    }
  }, [datasetPath, yourTeamNumber, pickPosition, initialPicklist]);

  useEffect(() => {
    console.log("Priorities or exclusions changed significantly");
  }, [
    priorities.length,
    excludeTeams?.length,
    datasetPath,
    yourTeamNumber,
  ]);

  return {
    picklist,
    analysis,
    isLoading,
    estimatedTime,
    error,
    isEditing,
    showAnalysis,
    successMessage,
    selectedTeams,
    showComparison,
    missingTeamNumbers,
    showMissingTeamsModal,
    isRankingMissingTeams,
    useBatching,
    setPicklist,
    setAnalysis,
    setIsLoading,
    setEstimatedTime,
    setError,
    setIsEditing,
    setShowAnalysis,
    setSuccessMessage,
    setSelectedTeams,
    setShowComparison,
    setMissingTeamNumbers,
    setShowMissingTeamsModal,
    setIsRankingMissingTeams,
    setUseBatching,
  };
}