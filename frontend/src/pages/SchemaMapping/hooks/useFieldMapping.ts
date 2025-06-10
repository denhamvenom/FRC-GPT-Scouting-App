import { useMemo } from 'react';

export const useFieldMapping = (headers: string[]) => {
  // Find headers that might be good candidates for team_number and match_number
  const findHeaderCandidates = useMemo(() => {
    return (type: string): string[] => {
      if (type === "team_number") {
        return headers.filter(h => 
          h.toLowerCase().includes("team") && 
          (h.toLowerCase().includes("number") || h.toLowerCase().includes("num"))
        );
      } else if (type === "match_number") {
        return headers.filter(h => 
          (h.toLowerCase().includes("match") || h.toLowerCase().includes("qual")) && 
          (h.toLowerCase().includes("number") || h.toLowerCase().includes("num"))
        );
      }
      return [];
    };
  }, [headers]);

  const getTeamNumberCandidates = useMemo(() => {
    return findHeaderCandidates("team_number");
  }, [findHeaderCandidates]);

  const getMatchNumberCandidates = useMemo(() => {
    return findHeaderCandidates("match_number");
  }, [findHeaderCandidates]);

  const isCriticalField = (header: string, teamHeader: string | null, matchHeader: string | null): boolean => {
    return header === teamHeader || header === matchHeader;
  };

  const getMappingValue = (header: string): string => {
    return header.toLowerCase().includes("qual") ? "qual_number" : "match_number";
  };

  return {
    getTeamNumberCandidates,
    getMatchNumberCandidates,
    isCriticalField,
    getMappingValue
  };
};