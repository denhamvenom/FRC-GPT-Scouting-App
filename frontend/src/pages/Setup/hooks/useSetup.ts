import { useState, useEffect, useCallback } from 'react';
import type { 
  SetupState, 
  Event, 
  GroupedEvents, 
  EventInfo,
  GameManualResponse,
  GameManualDetailResponse,
  CurrentManualInfo,
  ProcessedSectionsResult,
  SetupResult,
  PendingEventAction,
  TocItemType
} from '../types';

const initialState: SetupState = {
  currentStep: 1,
  completedSteps: new Set(),
  selectedManualFile: null,
  isUploadingManual: false,
  manualUploadError: null,
  selectedTocItems: new Map(),
  processedSectionsResult: null,
  isProcessingSections: false,
  processSectionsError: null,
  currentManualInfo: null,
  managedManuals: [],
  isLoadingManagedManuals: false,
  managedManualsError: null,
  activeDeletingManualId: null,
  deleteManualError: null,
  isLoadingSelectedManualId: null,
  selectedManualError: null,
  year: 2025,
  loadingEvents: false,
  eventsError: null,
  events: [],
  groupedEvents: {},
  selectedEvent: "",
  selectedEventName: "",
  currentEvent: {},
  isLoadingCurrentEvent: true,
  showEventSwitchDialog: false,
  pendingEventAction: null,
  setupResult: null,
  isSettingUpEvent: false,
};

export const useSetup = () => {
  const [state, setState] = useState<SetupState>(initialState);

  // Load current event info and events when the component mounts
  useEffect(() => {
    fetchCurrentEvent();
    fetchEvents(state.year);
    fetchManagedManuals();
  }, []);

  // When current event changes or year changes, load events for that year
  useEffect(() => {
    if (state.currentEvent.year && !state.isLoadingCurrentEvent) {
      fetchEvents(state.currentEvent.year);
    }
  }, [state.currentEvent, state.isLoadingCurrentEvent]);

  const fetchCurrentEvent = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/setup/info");
      const data = await response.json();
      
      if (data.status === "success" && data.event_key) {
        setState(prev => ({
          ...prev,
          currentEvent: {
            event_key: data.event_key,
            event_name: data.event_name,
            year: data.year
          },
          year: data.year || prev.year
        }));
      }
    } catch (err) {
      console.error("Error fetching current event:", err);
    } finally {
      setState(prev => ({ ...prev, isLoadingCurrentEvent: false }));
    }
  };

  const fetchManagedManuals = async () => {
    setState(prev => ({ ...prev, isLoadingManagedManuals: true, managedManualsError: null }));
    try {
      const response = await fetch("http://localhost:8000/api/manuals");
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch manuals");
      }
      const data: GameManualResponse[] = await response.json();
      setState(prev => ({ ...prev, managedManuals: data }));
    } catch (err: any) {
      setState(prev => ({ ...prev, managedManualsError: err.message || "Error fetching manuals" }));
      console.error(err);
    } finally {
      setState(prev => ({ ...prev, isLoadingManagedManuals: false }));
    }
  };

  const fetchEvents = async (yearToFetch: number) => {
    setState(prev => ({ ...prev, loadingEvents: true, eventsError: null }));

    try {
      const response = await fetch(`http://localhost:8000/api/setup/events?year=${yearToFetch}`);

      if (!response.ok) {
        throw new Error("Failed to fetch events");
      }

      const data = await response.json();

      if (data.status === "success") {
        setState(prev => ({
          ...prev,
          events: data.all_events || [],
          groupedEvents: data.grouped_events || {}
        }));
      } else {
        setState(prev => ({ ...prev, eventsError: data.message || "Failed to fetch events" }));
      }
    } catch (err) {
      setState(prev => ({ ...prev, eventsError: "Error fetching events" }));
      console.error(err);
    } finally {
      setState(prev => ({ ...prev, loadingEvents: false }));
    }
  };

  // Step navigation
  const canProceedToNextStep = useCallback(() => {
    switch (state.currentStep) {
      case 1:
        return state.currentManualInfo || state.managedManuals.some(m => m.year === state.year);
      case 2:
        return state.selectedEvent || state.currentEvent.event_key;
      case 3:
        return state.completedSteps.has(3);
      case 4:
        return false;
      default:
        return false;
    }
  }, [state.currentStep, state.currentManualInfo, state.managedManuals, state.year, state.selectedEvent, state.currentEvent.event_key, state.completedSteps]);

  const handleNextStep = useCallback(() => {
    if (canProceedToNextStep()) {
      setState(prev => ({
        ...prev,
        completedSteps: new Set([...prev.completedSteps, prev.currentStep]),
        currentStep: prev.currentStep + 1
      }));
    }
  }, [canProceedToNextStep]);

  const handlePreviousStep = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentStep: Math.max(1, prev.currentStep - 1)
    }));
  }, []);

  const handleStepClick = useCallback((step: number) => {
    setState(prev => {
      if (step <= prev.currentStep || prev.completedSteps.has(step)) {
        return { ...prev, currentStep: step };
      }
      return prev;
    });
  }, []);

  // Manual management handlers
  const handleManualFileChange = useCallback((file: File | null) => {
    setState(prev => ({ ...prev, selectedManualFile: file }));
  }, []);

  const handleManualUpload = async () => {
    if (!state.selectedManualFile) return;
    
    setState(prev => ({ ...prev, isUploadingManual: true, manualUploadError: null }));

    try {
      const formData = new FormData();
      formData.append("year", state.year.toString());
      formData.append("manual_file", state.selectedManualFile);
      
      const response = await fetch("http://localhost:8000/api/setup/start", {
        method: "POST",
        body: formData, 
      });

      const data = await response.json();

      if (response.ok) {
        setState(prev => ({
          ...prev,
          currentManualInfo: data.manual_info,
          selectedManualFile: null,
          selectedTocItems: new Map(),
          processedSectionsResult: null,
          processSectionsError: null,
          completedSteps: new Set([...prev.completedSteps, 1])
        }));
        
        await fetchManagedManuals();
      } else {
        setState(prev => ({ ...prev, manualUploadError: data.detail || "Failed to upload manual" }));
      }
    } catch (err) {
      setState(prev => ({ ...prev, manualUploadError: "Error connecting to server" }));
      console.error(err);
    } finally {
      setState(prev => ({ ...prev, isUploadingManual: false }));
    }
  };

  const handleSelectManagedManual = async (manual: GameManualResponse) => {
    setState(prev => ({ ...prev, isLoadingSelectedManualId: manual.id, selectedManualError: null }));
    try {
      const response = await fetch(`http://localhost:8000/api/manuals/${manual.id}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch details for manual ${manual.id}`);
      }
      const data: GameManualDetailResponse = await response.json();

      const newManualInfo: CurrentManualInfo = {
        manual_db_id: data.id,
        saved_manual_filename: data.original_filename,
        original_filename: data.original_filename,
        sanitized_filename_base: data.sanitized_filename_base,
        toc_data: data.toc_content || [],
        toc_found: !!(data.toc_content && data.toc_content.length > 0),
        toc_extraction_attempted: true,
        analysis_complete: !!(data.toc_content && data.toc_content.length > 0),
        text_length: data.toc_content ? 1 : 0,
        using_cached_manual: true,
      };
      if (data.toc_error) {
        newManualInfo.toc_error = data.toc_error;
      }
      
      setState(prev => ({
        ...prev,
        currentManualInfo: newManualInfo,
        year: data.year,
        selectedManualFile: null,
        selectedTocItems: new Map(),
        processedSectionsResult: null,
        processSectionsError: null,
        manualUploadError: null,
        completedSteps: new Set([...prev.completedSteps, 1])
      }));

    } catch (err: any) {
      setState(prev => ({ ...prev, selectedManualError: err.message || `Error loading manual ${manual.id}` }));
      console.error(err);
    } finally {
      setState(prev => ({ ...prev, isLoadingSelectedManualId: null }));
    }
  };

  const handleDeleteManual = async (manualId: number) => {
    if (!window.confirm("Are you sure you want to delete this manual and its associated files? This action cannot be undone.")) {
      return;
    }
    setState(prev => ({ ...prev, activeDeletingManualId: manualId, deleteManualError: null }));
    try {
      const response = await fetch(`http://localhost:8000/api/manuals/${manualId}`, { method: 'DELETE' });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete manual ${manualId}`);
      }
      
      fetchManagedManuals();

      setState(prev => {
        if (prev.currentManualInfo?.manual_db_id === manualId) {
          return {
            ...prev,
            currentManualInfo: null,
            selectedTocItems: new Map(),
            processedSectionsResult: null
          };
        }
        return prev;
      });

    } catch (err: any) {
      setState(prev => ({ ...prev, deleteManualError: err.message || `Error deleting manual ${manualId}` }));
      console.error(err);
    } finally {
      setState(prev => ({ ...prev, activeDeletingManualId: null }));
    }
  };

  // Event handlers
  const handleYearChange = useCallback((year: number) => {
    setState(prev => ({
      ...prev,
      year,
      selectedEvent: "",
      selectedEventName: ""
    }));
    fetchEvents(year);
  }, []);

  const handleEventChange = useCallback((eventKey: string) => {
    const event = state.events.find(e => e.key === eventKey);
    setState(prev => ({
      ...prev,
      selectedEvent: eventKey,
      selectedEventName: event?.name || ""
    }));
  }, [state.events]);

  const checkForEventSwitch = useCallback(() => {
    if (state.currentEvent.event_key && state.selectedEvent && state.currentEvent.event_key !== state.selectedEvent) {
      setState(prev => ({
        ...prev,
        pendingEventAction: {
          eventKey: prev.selectedEvent,
          eventName: prev.selectedEventName,
          year: prev.year
        },
        showEventSwitchDialog: true
      }));
    } else {
      handleEventSetup();
    }
  }, [state.currentEvent.event_key, state.selectedEvent, state.selectedEventName, state.year]);

  const handleEventSetup = async () => {
    const eventToUse = state.pendingEventAction?.eventKey || state.selectedEvent;
    const yearToUse = state.pendingEventAction?.year || state.year;
    
    if (!eventToUse) return;

    setState(prev => ({ ...prev, isSettingUpEvent: true, eventsError: null }));

    try {
      const formData = new FormData();
      formData.append("year", yearToUse.toString());
      formData.append("event_key", eventToUse);

      const response = await fetch("http://localhost:8000/api/setup/start", {
        method: "POST",
        body: formData, 
      });

      const data = await response.json();

      if (response.ok) {
        setState(prev => ({
          ...prev,
          setupResult: data,
          currentEvent: {
            event_key: eventToUse,
            event_name: prev.selectedEventName || eventToUse,
            year: yearToUse
          },
          completedSteps: new Set([...prev.completedSteps, 2]),
          pendingEventAction: null
        }));
      } else {
        setState(prev => ({ ...prev, eventsError: data.detail || "Failed to set up event" }));
      }
    } catch (err) {
      setState(prev => ({ ...prev, eventsError: "Error connecting to server" }));
      console.error(err);
    } finally {
      setState(prev => ({ ...prev, isSettingUpEvent: false }));
    }
  };

  const handleEventSwitchDialogClose = useCallback(() => {
    setState(prev => ({ ...prev, showEventSwitchDialog: false }));
  }, []);

  const handleCancelEventSwitch = useCallback(() => {
    setState(prev => ({
      ...prev,
      showEventSwitchDialog: false,
      pendingEventAction: null,
      selectedEvent: prev.currentEvent.event_key || "",
      selectedEventName: prev.currentEvent.event_name || ""
    }));
  }, []);

  const handleArchiveAndSwitch = useCallback(() => {
    setState(prev => ({ ...prev, showEventSwitchDialog: false, currentStep: 2 }));
    // Scroll to archive section
    setTimeout(() => {
      document.getElementById("archiveSection")?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, []);

  const handleContinueWithoutArchiving = useCallback(() => {
    setState(prev => ({ ...prev, showEventSwitchDialog: false }));
    handleEventSetup();
  }, []);

  // Sheet configuration handlers
  const handleSheetConfigurationChange = useCallback(() => {
    setState(prev => ({
      ...prev,
      completedSteps: new Set([...prev.completedSteps, 3])
    }));
  }, []);

  return {
    state,
    actions: {
      handleNextStep,
      handlePreviousStep,
      handleStepClick,
      handleManualFileChange,
      handleManualUpload,
      handleSelectManagedManual,
      handleDeleteManual,
      handleYearChange,
      handleEventChange,
      checkForEventSwitch,
      handleEventSwitchDialogClose,
      handleCancelEventSwitch,
      handleArchiveAndSwitch,
      handleContinueWithoutArchiving,
      handleSheetConfigurationChange,
      fetchManagedManuals,
    },
    canProceedToNextStep
  };
};