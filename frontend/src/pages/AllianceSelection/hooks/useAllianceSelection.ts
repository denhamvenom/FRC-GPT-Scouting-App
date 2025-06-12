/**
 * Main hook for alliance selection state management
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiContext } from '../../../providers/ApiProvider';
import { 
  LockedPicklist, 
  SelectionState, 
  UseAllianceSelectionReturn,
  PicklistsResponse,
  SelectionResponse,
  PicklistResponse,
  CreateSelectionRequest,
  CreateSelectionResponse
} from '../types';
import { getTeamListFromPicklist } from '../utils';

export const useAllianceSelection = (): UseAllianceSelectionReturn => {
  const navigate = useNavigate();
  
  // Get API services from context
  const { allianceService } = useApiContext();
  
  // State
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [picklist, setPicklist] = useState<LockedPicklist | null>(null);
  const [selection, setSelection] = useState<SelectionState | null>(null);
  const [teamList, setTeamList] = useState<number[]>([]);

  const clearError = useCallback(() => setError(null), []);
  const clearSuccessMessage = useCallback(() => setSuccessMessage(null), []);

  const fetchPicklistDetails = useCallback(async (picklistId: number): Promise<LockedPicklist> => {
    const data: PicklistResponse = await allianceService.getPicklistDetails(picklistId);
    
    if (data.status !== 'success' || !data.picklist) {
      throw new Error('Invalid picklist data');
    }
    
    return data.picklist;
  }, [allianceService]);

  const loadPicklists = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data: PicklistsResponse = await allianceService.getPicklists();
      
      if (data.status === 'success' && data.picklists && data.picklists.length > 0) {
        // Find the most recent picklist
        const latestPicklist = data.picklists.sort((a, b) => {
          return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
        })[0];
        
        // Check if there's an active selection for this picklist
        try {
          const selectionData: SelectionResponse = await allianceService.getSelection(latestPicklist.id);
          
          if (selectionData.status === 'success' && selectionData.selection) {
            // Redirect to existing selection
            navigate(`/alliance-selection/${selectionData.selection.id}`);
            return;
          }
        } catch (selectionErr) {
          // No existing selection found - this is normal
        }
        
        // If no selection exists, load the picklist details
        const picklistDetails = await fetchPicklistDetails(latestPicklist.id);
        setPicklist(picklistDetails);
        
        // Get team list from picklist
        const teams = getTeamListFromPicklist(picklistDetails);
        setTeamList(teams);
      } else {
        setError('No locked picklists found. Please lock a picklist before proceeding.');
      }
    } catch (err: any) {
      setError('Error loading picklists: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [navigate, fetchPicklistDetails, allianceService]);

  const loadSelectionData = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const data: SelectionResponse = await allianceService.getSelection(id);
      
      if (data.status === 'success' && data.selection) {
        setSelection(data.selection);
        
        // Also fetch the picklist data if picklist_id is defined
        if (data.selection.picklist_id) {
          try {
            const picklistDetails = await fetchPicklistDetails(data.selection.picklist_id);
            setPicklist(picklistDetails);
          } catch (picklistErr) {
            console.error('Error fetching picklist details:', picklistErr);
            // Continue without picklist data - we can still use the alliance selection
          }
        } else {
          console.warn('Alliance selection has no picklist_id, proceeding without picklist data');
          
          // Fallback: Try to find the picklist from the list (if a picklist with this event_key exists)
          try {
            const picklistsData: PicklistsResponse = await allianceService.getPicklists();
            
            if (picklistsData.status === 'success' && picklistsData.picklists && picklistsData.picklists.length > 0) {
              // Find a picklist for the same event
              const matchingPicklist = picklistsData.picklists.find((p) => 
                p.event_key === data.selection.event_key
              );
              
              if (matchingPicklist) {
                const picklistDetails = await fetchPicklistDetails(matchingPicklist.id);
                setPicklist(picklistDetails);
              }
            }
          } catch (fallbackErr) {
            console.error('Error in picklist fallback attempt:', fallbackErr);
          }
        }
      } else {
        setError('Alliance selection not found');
      }
    } catch (err: any) {
      setError('Error loading alliance selection: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [fetchPicklistDetails, allianceService]);

  const createNewSelection = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use picklist data if available, otherwise use default values
      const event_key = picklist?.event_key || '2025arc';
      const year = picklist?.year || 2025;
      let picklist_id = picklist?.id || null;
      
      // If we don't have a picklist ID but have a team number and event key, try to find a matching picklist
      if (!picklist_id) {
        try {
          const picklistsData: PicklistsResponse = await allianceService.getPicklists();
          
          if (picklistsData.status === 'success' && picklistsData.picklists && picklistsData.picklists.length > 0) {
            // Find the latest picklist for the same event
            const matchingPicklists = picklistsData.picklists.filter((p) => 
              p.event_key === event_key
            );
            
            if (matchingPicklists.length > 0) {
              // Sort by creation date (newest first)
              const latestPicklist = matchingPicklists.sort((a, b) => {
                return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
              })[0];
              
              // Fetch the picklist details to use for sorting teams
              const picklistDetails = await fetchPicklistDetails(latestPicklist.id);
              setPicklist(picklistDetails);
              
              // Update our picklist_id for the new alliance selection
              picklist_id = latestPicklist.id;
            }
          }
        } catch (err) {
          console.error("Error looking for matching picklist:", err);
        }
      }
      
      const requestBody: CreateSelectionRequest = {
        picklist_id: picklist_id,
        event_key: event_key,
        year: year,
        team_list: teamList
      };
      
      const data: CreateSelectionResponse = await allianceService.createSelection(requestBody);
      
      // Navigate to the new selection
      navigate(`/alliance-selection/${data.id}`);
      
    } catch (err: any) {
      setError('Error creating alliance selection: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [picklist, teamList, navigate, fetchPicklistDetails, allianceService]);

  return {
    // State
    loading,
    error,
    successMessage,
    picklist,
    selection,
    teamList,
    
    // Actions
    loadPicklists,
    loadSelectionData,
    createNewSelection,
    clearError,
    clearSuccessMessage,
  };
};