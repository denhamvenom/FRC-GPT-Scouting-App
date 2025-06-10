// frontend/src/pages/Validation/hooks/useOutliers.ts

import { useState, useMemo } from 'react';
import { ValidationIssue } from '../types';

export const useOutliers = (outliers: ValidationIssue[]) => {
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'team' | 'match' | 'severity' | 'metric'>('severity');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Filter and sort outliers
  const filteredOutliers = useMemo(() => {
    let filtered = [...outliers];

    // Filter by team if selected
    if (selectedTeam) {
      filtered = filtered.filter(outlier => outlier.team_number === selectedTeam);
    }

    // Filter by metric if selected
    if (selectedMetric) {
      filtered = filtered.filter(outlier => 
        outlier.issues.some(issue => issue.metric === selectedMetric)
      );
    }

    // Sort outliers
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case 'team':
          aValue = a.team_number;
          bValue = b.team_number;
          break;
        case 'match':
          aValue = a.match_number;
          bValue = b.match_number;
          break;
        case 'severity':
          // Calculate severity based on z-scores
          aValue = Math.max(...a.issues.map(issue => Math.abs(issue.z_score || 0)));
          bValue = Math.max(...b.issues.map(issue => Math.abs(issue.z_score || 0)));
          break;
        case 'metric':
          aValue = a.issues[0]?.metric || '';
          bValue = b.issues[0]?.metric || '';
          break;
        default:
          aValue = 0;
          bValue = 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [outliers, selectedTeam, selectedMetric, sortBy, sortOrder]);

  // Get unique teams
  const uniqueTeams = useMemo(() => {
    const teams = new Set(outliers.map(outlier => outlier.team_number));
    return Array.from(teams).sort((a, b) => a - b);
  }, [outliers]);

  // Get unique metrics
  const uniqueMetrics = useMemo(() => {
    const metrics = new Set<string>();
    outliers.forEach(outlier => {
      outlier.issues.forEach(issue => {
        metrics.add(issue.metric);
      });
    });
    return Array.from(metrics).sort();
  }, [outliers]);

  // Get severity level for an outlier
  const getSeverityLevel = (outlier: ValidationIssue): 'low' | 'medium' | 'high' | 'critical' => {
    const maxZScore = Math.max(...outlier.issues.map(issue => Math.abs(issue.z_score || 0)));
    
    if (maxZScore >= 4) return 'critical';
    if (maxZScore >= 3) return 'high';
    if (maxZScore >= 2) return 'medium';
    return 'low';
  };

  // Get severity color
  const getSeverityColor = (outlier: ValidationIssue): string => {
    const level = getSeverityLevel(outlier);
    
    switch (level) {
      case 'critical': return 'text-red-700 bg-red-100';
      case 'high': return 'text-orange-700 bg-orange-100';
      case 'medium': return 'text-yellow-700 bg-yellow-100';
      case 'low': return 'text-blue-700 bg-blue-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const toggleSort = (newSortBy: 'team' | 'match' | 'severity' | 'metric') => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  };

  const clearFilters = () => {
    setSelectedTeam(null);
    setSelectedMetric(null);
  };

  return {
    filteredOutliers,
    uniqueTeams,
    uniqueMetrics,
    selectedTeam,
    selectedMetric,
    sortBy,
    sortOrder,
    setSelectedTeam,
    setSelectedMetric,
    setSortBy,
    setSortOrder,
    toggleSort,
    clearFilters,
    getSeverityLevel,
    getSeverityColor,
  };
};