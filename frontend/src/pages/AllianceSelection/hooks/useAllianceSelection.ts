/**
 * Main hook for alliance selection state management
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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

const API_BASE_URL = 'http://localhost:8000/api';

export const useAllianceSelection = (): UseAllianceSelectionReturn => {
  const navigate = useNavigate();
  
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
    const response = await fetch(`${API_BASE_URL}/alliance/picklist/${picklistId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch picklist details');
    }
    
    const data: PicklistResponse = await response.json();
    
    if (data.status !== 'success' || !data.picklist) {
      throw new Error('Invalid picklist data');
    }
    
    return data.picklist;
  }, []);

  const loadPicklists = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/alliance/picklists`);
      const data: PicklistsResponse = await response.json();
      
      if (data.status === 'success' && data.picklists && data.picklists.length > 0) {
        // Find the most recent picklist
        const latestPicklist = data.picklists.sort((a, b) => {
          return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
        })[0];
        
        // Check if there's an active selection for this picklist
        const selectionResponse = await fetch(`${API_BASE_URL}/alliance/selection/${latestPicklist.id}`);
        
        if (selectionResponse.ok) {
          const selectionData: SelectionResponse = await selectionResponse.json();
          
          if (selectionData.status === 'success' && selectionData.selection) {
            // Redirect to existing selection
            navigate(`/alliance-selection/${selectionData.selection.id}`);
            return;
          }
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
  }, [navigate, fetchPicklistDetails]);

  const loadSelectionData = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/alliance/selection/${id}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch alliance selection data');
      }
      
      const data: SelectionResponse = await response.json();
      
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
            const picklistsResponse = await fetch(`${API_BASE_URL}/alliance/picklists`);
            const picklistsData: PicklistsResponse = await picklistsResponse.json();
            
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
  }, [fetchPicklistDetails]);

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
          const picklistsResponse = await fetch(`${API_BASE_URL}/alliance/picklists`);
          const picklistsData: PicklistsResponse = await picklistsResponse.json();
          
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
      
      const response = await fetch(`${API_BASE_URL}/alliance/selection/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create alliance selection');
      }
      
      const data: CreateSelectionResponse = await response.json();
      
      // Navigate to the new selection
      navigate(`/alliance-selection/${data.id}`);
      
    } catch (err: any) {
      setError('Error creating alliance selection: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [picklist, teamList, navigate, fetchPicklistDetails]);

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