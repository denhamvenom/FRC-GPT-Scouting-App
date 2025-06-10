// frontend/src/pages/PicklistView/hooks/usePicklistView.ts

import { useState, useEffect } from 'react';
import { 
  Team, 
  Metric, 
  MetricPriority, 
  PickPosition, 
  LockedPicklist 
} from '../types';

export const usePicklistView = () => {
  // Dataset
  const [datasetPath, setDatasetPath] = useState<string>("");
  const [yourTeamNumber, setYourTeamNumber] = useState<number>(0);

  // UI state
  const [activeTab, setActiveTab] = useState<PickPosition>("first");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLocking, setIsLocking] = useState<boolean>(false);

  // Metrics
  const [universalMetrics, setUniversalMetrics] = useState<Metric[]>([]);
  const [gameMetrics, setGameMetrics] = useState<Metric[]>([]);

  // Priorities for each pick position
  const [firstPickPriorities, setFirstPickPriorities] = useState<MetricPriority[]>([]);
  const [secondPickPriorities, setSecondPickPriorities] = useState<MetricPriority[]>([]);
  const [thirdPickPriorities, setThirdPickPriorities] = useState<MetricPriority[]>([]);

  // Generated picklists
  const [firstPicklist, setFirstPicklist] = useState<Team[]>([]);
  const [secondPicklist, setSecondPicklist] = useState<Team[]>([]);
  const [thirdPicklist, setThirdPicklist] = useState<Team[]>([]);

  // Excluded teams
  const [excludedTeams, setExcludedTeams] = useState<number[]>([]);

  // Existing data
  const [picklists, setPicklists] = useState<LockedPicklist[]>([]);
  const [hasLockedPicklist, setHasLockedPicklist] = useState<boolean>(false);
  const [activeAllianceSelection, setActiveAllianceSelection] = useState<number | null>(null);

  // Initialize data
  useEffect(() => {
    checkDatasetStatus();
    fetchLockedPicklists();
  }, []);

  // Update excluded teams when picklists change
  useEffect(() => {
    const excluded: number[] = [];

    // Add teams from first pick if we're on second or third tab
    if (activeTab === "second" || activeTab === "third") {
      firstPicklist.slice(0, 1).forEach((team) => {
        excluded.push(team.team_number);
      });
    }

    // Add teams from second pick if we're on third tab
    if (activeTab === "third") {
      secondPicklist.slice(0, 1).forEach((team) => {
        excluded.push(team.team_number);
      });
    }

    setExcludedTeams(excluded);
  }, [activeTab, firstPicklist, secondPicklist]);

  const checkDatasetStatus = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Check for unified dataset
      const response = await fetch(
        "http://localhost:8000/api/unified/status?event_key=2025arc&year=2025",
      );
      const data = await response.json();

      if (data.status === "exists" && data.path) {
        setDatasetPath(data.path);
        await fetchMetrics(data.path);
      } else {
        setError("No dataset found. Please build a unified dataset first.");
      }
    } catch (err) {
      console.error("Error checking dataset status:", err);
      setError("Error checking for datasets");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMetrics = async (path: string) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/picklist/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ unified_dataset_path: path }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to fetch metrics");
      }

      const data = await response.json();

      if (data.status === "success") {
        setUniversalMetrics(data.universal_metrics || []);
        setGameMetrics(data.game_metrics || []);

        // Get your team number from dataset if available
        if (data.your_team_number) {
          setYourTeamNumber(data.your_team_number);
        }
      }
    } catch (err) {
      console.error("Error fetching metrics:", err);
      setError("Error loading metrics data");
    }
  };

  const fetchLockedPicklists = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/picklist/locked");
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === "success") {
          setPicklists(data.picklists || []);
          setHasLockedPicklist(data.picklists && data.picklists.length > 0);
        }
      }
    } catch (err) {
      console.error("Error fetching locked picklists:", err);
    }

    // Check for active alliance selection
    try {
      const response = await fetch("http://localhost:8000/api/alliance-selection/status");
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === "success" && data.is_active) {
          setActiveAllianceSelection(data.id);
        }
      }
    } catch (err) {
      console.error("Error checking alliance selection status:", err);
    }
  };

  const handleAddMetric = (metric: Metric) => {
    const newPriority: MetricPriority = {
      id: metric.id,
      weight: 1.0,
    };

    // Add to the appropriate list based on active tab
    if (activeTab === "first") {
      if (!firstPickPriorities.some((p) => p.id === metric.id)) {
        setFirstPickPriorities([...firstPickPriorities, newPriority]);
      }
    } else if (activeTab === "second") {
      if (!secondPickPriorities.some((p) => p.id === metric.id)) {
        setSecondPickPriorities([...secondPickPriorities, newPriority]);
      }
    } else if (activeTab === "third") {
      if (!thirdPickPriorities.some((p) => p.id === metric.id)) {
        setThirdPickPriorities([...thirdPickPriorities, newPriority]);
      }
    }
  };

  const handleRemovePriority = (metricId: string) => {
    // Remove from the appropriate list based on active tab
    if (activeTab === "first") {
      setFirstPickPriorities(
        firstPickPriorities.filter((p) => p.id !== metricId),
      );
    } else if (activeTab === "second") {
      setSecondPickPriorities(
        secondPickPriorities.filter((p) => p.id !== metricId),
      );
    } else if (activeTab === "third") {
      setThirdPickPriorities(
        thirdPickPriorities.filter((p) => p.id !== metricId),
      );
    }
  };

  const handleWeightChange = (metricId: string, weight: number) => {
    // Update weight in the appropriate list based on active tab
    if (activeTab === "first") {
      setFirstPickPriorities(
        firstPickPriorities.map((p) =>
          p.id === metricId ? { ...p, weight } : p,
        ),
      );
    } else if (activeTab === "second") {
      setSecondPickPriorities(
        secondPickPriorities.map((p) =>
          p.id === metricId ? { ...p, weight } : p,
        ),
      );
    } else if (activeTab === "third") {
      setThirdPickPriorities(
        thirdPickPriorities.map((p) =>
          p.id === metricId ? { ...p, weight } : p,
        ),
      );
    }
  };

  const getCurrentPriorities = (): MetricPriority[] => {
    switch (activeTab) {
      case "first": return firstPickPriorities;
      case "second": return secondPickPriorities;
      case "third": return thirdPickPriorities;
      default: return [];
    }
  };

  const getCurrentPicklist = (): Team[] => {
    switch (activeTab) {
      case "first": return firstPicklist;
      case "second": return secondPicklist;
      case "third": return thirdPicklist;
      default: return [];
    }
  };

  const setCurrentPicklist = (teams: Team[]) => {
    switch (activeTab) {
      case "first": setFirstPicklist(teams); break;
      case "second": setSecondPicklist(teams); break;
      case "third": setThirdPicklist(teams); break;
    }
  };

  const generatePicklist = async () => {
    const priorities = getCurrentPriorities();
    
    if (priorities.length === 0) {
      setError("Please add at least one metric priority before generating a picklist.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/api/picklist/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unified_dataset_path: datasetPath,
          position: activeTab,
          team_number: yourTeamNumber,
          priority_metrics: priorities,
          excluded_teams: excludedTeams,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate picklist");
      }

      const data = await response.json();

      if (data.status === "success") {
        setCurrentPicklist(data.picklist || []);
        setSuccessMessage(`${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} pick picklist generated successfully!`);
      } else {
        setError(data.message || "Error generating picklist");
      }
    } catch (err) {
      console.error("Error generating picklist:", err);
      setError("Error generating picklist");
    } finally {
      setIsLoading(false);
    }
  };

  const lockPicklist = async () => {
    const priorities = getCurrentPriorities();
    const picklist = getCurrentPicklist();
    
    if (picklist.length === 0) {
      setError("Please generate a picklist before locking it.");
      return;
    }

    setIsLocking(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/api/picklist/lock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          position: activeTab,
          team_number: yourTeamNumber,
          excluded_teams: excludedTeams,
          strategy_prompt: `${activeTab} pick strategy`,
          priority_metrics: priorities,
          picklist: picklist,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to lock picklist");
      }

      const data = await response.json();

      if (data.status === "success") {
        setSuccessMessage(`${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} pick picklist locked successfully!`);
        await fetchLockedPicklists();
      } else {
        setError(data.message || "Error locking picklist");
      }
    } catch (err) {
      console.error("Error locking picklist:", err);
      setError("Error locking picklist");
    } finally {
      setIsLocking(false);
    }
  };

  const unlockPicklist = async () => {
    setIsLocking(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/picklist/unlock/${activeTab}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to unlock picklist");
      }

      const data = await response.json();

      if (data.status === "success") {
        setSuccessMessage(`${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} pick picklist unlocked successfully!`);
        await fetchLockedPicklists();
      } else {
        setError(data.message || "Error unlocking picklist");
      }
    } catch (err) {
      console.error("Error unlocking picklist:", err);
      setError("Error unlocking picklist");
    } finally {
      setIsLocking(false);
    }
  };

  return {
    // State
    datasetPath,
    yourTeamNumber,
    activeTab,
    isLoading,
    error,
    successMessage,
    isLocking,
    universalMetrics,
    gameMetrics,
    firstPickPriorities,
    secondPickPriorities,
    thirdPickPriorities,
    firstPicklist,
    secondPicklist,
    thirdPicklist,
    excludedTeams,
    picklists,
    hasLockedPicklist,
    activeAllianceSelection,

    // Actions
    setDatasetPath,
    setYourTeamNumber,
    setActiveTab,
    setIsLoading,
    setError,
    setSuccessMessage,
    setIsLocking,
    setUniversalMetrics,
    setGameMetrics,
    setFirstPickPriorities,
    setSecondPickPriorities,
    setThirdPickPriorities,
    setFirstPicklist,
    setSecondPicklist,
    setThirdPicklist,
    setExcludedTeams,
    setPicklists,
    setHasLockedPicklist,
    setActiveAllianceSelection,
    checkDatasetStatus,
    fetchMetrics,
    fetchLockedPicklists,
    handleAddMetric,
    handleRemovePriority,
    handleWeightChange,
    getCurrentPriorities,
    getCurrentPicklist,
    generatePicklist,
    lockPicklist,
    unlockPicklist,
  };
};