// frontend/src/pages/Setup.tsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import EventArchiveManager from "../components/EventArchiveManager";
import SheetConfigManager from "../components/SheetConfigManager";
import { apiUrl, fetchWithNgrokHeaders } from "../config";

interface Event {
  key: string;
  name: string;
  code: string;
  location: string;
  dates: string;
  type: string;
  week: number;
}

interface GroupedEvents {
  [key: string]: Event[];
}

interface EventInfo {
  event_key?: string;
  event_name?: string;
  year?: number;
}

// Define the ToC item type based on backend structure
interface TocItemType {
  title: string;
  level: number;
  page: number;
  // Allow any other fields that might come from the backend
  [key: string]: any; 
}

// Interfaces for GameManual management
interface GameManualBase {
  id: number;
  year: number;
  original_filename: string;
  sanitized_filename_base: string;
  upload_timestamp?: string; // Assuming ISO string from backend
  last_accessed_timestamp?: string; // Assuming ISO string from backend
}

interface GameManualResponse extends GameManualBase {}

interface GameManualDetailResponse extends GameManualResponse {
  stored_pdf_path?: string;
  toc_json_path?: string;
  parsed_sections_path?: string;
  toc_content?: TocItemType[];
  toc_error?: string;
}


function Setup() {
  const navigate = useNavigate();
  
  // Step management
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  
  // Step 1: Manual Training states
  const [selectedManualFile, setSelectedManualFile] = useState<File | null>(null);
  const [isUploadingManual, setIsUploadingManual] = useState<boolean>(false);
  const [manualUploadError, setManualUploadError] = useState<string | null>(null);
  const [selectedTocItems, setSelectedTocItems] = useState<Map<string, TocItemType>>(new Map());
  const [processedSectionsResult, setProcessedSectionsResult] = useState<any>(null);
  const [isProcessingSections, setIsProcessingSections] = useState<boolean>(false);
  const [processSectionsError, setProcessSectionsError] = useState<string | null>(null);
  const [currentManualInfo, setCurrentManualInfo] = useState<any>(null);
  
  // Manual Management States
  const [managedManuals, setManagedManuals] = useState<GameManualResponse[]>([]);
  const [isLoadingManagedManuals, setIsLoadingManagedManuals] = useState<boolean>(false);
  const [managedManualsError, setManagedManualsError] = useState<string | null>(null);
  const [activeDeletingManualId, setActiveDeletingManualId] = useState<number | null>(null);
  const [deleteManualError, setDeleteManualError] = useState<string | null>(null);
  const [isLoadingSelectedManualId, setIsLoadingSelectedManualId] = useState<number | null>(null);
  const [selectedManualError, setSelectedManualError] = useState<string | null>(null);
  
  // Step 2: Event Selection states
  const [year, setYear] = useState<number>(2025);
  const [loadingEvents, setLoadingEvents] = useState<boolean>(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [groupedEvents, setGroupedEvents] = useState<GroupedEvents>({});
  const [selectedEvent, setSelectedEvent] = useState<string>("");
  const [selectedEventName, setSelectedEventName] = useState<string>("");
  
  // Manual event input states
  const [isManualEventMode, setIsManualEventMode] = useState<boolean>(false);
  const [manualEventKey, setManualEventKey] = useState<string>("");
  const [isValidatingManualEvent, setIsValidatingManualEvent] = useState<boolean>(false);
  const [manualEventValidation, setManualEventValidation] = useState<{
    isValid: boolean;
    eventData?: Event;
    error?: string;
  } | null>(null);
  
  // Current event state
  const [currentEvent, setCurrentEvent] = useState<EventInfo>({});
  const [isLoadingCurrentEvent, setIsLoadingCurrentEvent] = useState<boolean>(true);
  
  // Event switching confirmation dialog
  const [showEventSwitchDialog, setShowEventSwitchDialog] = useState<boolean>(false);
  const [pendingEventAction, setPendingEventAction] = useState<{
    eventKey: string;
    eventName: string;
    year: number;
  } | null>(null);
  
  // Step 3: Database Alignment states
  // Sheet configuration is handled by SheetConfigManager component
  
  // Setup result state (for backward compatibility during transition)
  const [setupResult, setSetupResult] = useState<any>(null);
  const [isSettingUpEvent, setIsSettingUpEvent] = useState<boolean>(false);

  // Load current event info and events when the component mounts
  useEffect(() => {
    // Fetch current event info
    const fetchCurrentEvent = async () => {
      try {
        const response = await fetchWithNgrokHeaders(apiUrl("/api/setup/info"));
        const data = await response.json();
        
        if (data.status === "success" && data.event_key) {
          setCurrentEvent({
            event_key: data.event_key,
            event_name: data.event_name,
            year: data.year
          });
          
          // If we have a current event, set the year to match
          if (data.year) {
            setYear(data.year);
          }
        }
      } catch (err) {
        console.error("Error fetching current event:", err);
      } finally {
        setIsLoadingCurrentEvent(false);
      }
    };
    
    fetchCurrentEvent();
    fetchEvents(year);
    fetchManagedManuals();
  }, []);
  
  // When current event changes or year changes, load events for that year
  useEffect(() => {
    if (currentEvent.year && !isLoadingCurrentEvent) {
      fetchEvents(currentEvent.year);
    }
  }, [currentEvent, isLoadingCurrentEvent]);

  const fetchManagedManuals = async () => {
    setIsLoadingManagedManuals(true);
    setManagedManualsError(null);
    try {
      const response = await fetchWithNgrokHeaders(apiUrl("/api/manuals"));
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch manuals");
      }
      const data: GameManualResponse[] = await response.json();
      setManagedManuals(data);
    } catch (err: any) {
      setManagedManualsError(err.message || "Error fetching manuals");
      console.error(err);
    } finally {
      setIsLoadingManagedManuals(false);
    }
  };

  const fetchEvents = async (yearToFetch: number) => {
    setLoadingEvents(true);
    setEventsError(null);

    try {
      const response = await fetchWithNgrokHeaders(apiUrl(`/api/setup/events?year=${yearToFetch}`));

      if (!response.ok) {
        throw new Error("Failed to fetch events");
      }

      const data = await response.json();

      if (data.status === "success") {
        setEvents(data.all_events || []);
        setGroupedEvents(data.grouped_events || {});
      } else {
        setEventsError(data.message || "Failed to fetch events");
      }
    } catch (err) {
      setEventsError("Error fetching events");
      console.error(err);
    } finally {
      setLoadingEvents(false);
    }
  };

  // Step navigation
  const canProceedToNextStep = () => {
    switch (currentStep) {
      case 1:
        // Can proceed from manual step if manual is uploaded/selected or if manual exists for the year
        return currentManualInfo || managedManuals.some(m => m.year === year);
      case 2:
        // Can proceed from event selection if event is selected
        return selectedEvent || currentEvent.event_key;
      case 3:
        // Can proceed from sheet config if it's completed
        return completedSteps.has(3);
      case 4:
        // Can't proceed from summary - it's the last step
        return false;
      default:
        return false;
    }
  };

  const handleNextStep = () => {
    if (canProceedToNextStep()) {
      setCompletedSteps(prev => new Set([...prev, currentStep]));
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePreviousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepClick = (step: number) => {
    // Allow clicking on completed steps or the current step
    if (step <= currentStep || completedSteps.has(step)) {
      setCurrentStep(step);
    }
  };

  // Manual upload handler
  const handleManualUpload = async () => {
    if (!selectedManualFile) return;
    
    setIsUploadingManual(true);
    setManualUploadError(null);

    try {
      const formData = new FormData();
      formData.append("year", year.toString());
      formData.append("manual_file", selectedManualFile);
      
      const response = await fetchWithNgrokHeaders(apiUrl("/api/setup/start"), {
        method: "POST",
        body: formData, 
      });

      const data = await response.json();

      if (response.ok) {
        setCurrentManualInfo(data.manual_info);
        setSelectedManualFile(null);
        setSelectedTocItems(new Map());
        setProcessedSectionsResult(null);
        setProcessSectionsError(null);
        
        // Refresh the managed manuals list
        await fetchManagedManuals();
        
        // Mark step as completed
        setCompletedSteps(prev => new Set([...prev, 1]));
      } else {
        setManualUploadError(data.detail || "Failed to upload manual");
      }
    } catch (err) {
      setManualUploadError("Error connecting to server");
      console.error(err);
    } finally {
      setIsUploadingManual(false);
    }
  };

  const handleManualFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedManualFile(e.target.files[0]);
    } else {
      setSelectedManualFile(null);
    }
  };

  const handleSelectManagedManual = async (manual: GameManualResponse) => {
    setIsLoadingSelectedManualId(manual.id);
    setSelectedManualError(null);
    try {
      const response = await fetchWithNgrokHeaders(apiUrl(`/api/manuals/${manual.id}`));
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch details for manual ${manual.id}`);
      }
      const data: GameManualDetailResponse = await response.json();

      // Set current manual info
      const newManualInfo: any = {
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
      
      setCurrentManualInfo(newManualInfo);
      setYear(data.year);
      setSelectedManualFile(null);
      setSelectedTocItems(new Map());
      setProcessedSectionsResult(null);
      setProcessSectionsError(null);
      setManualUploadError(null);
      
      // Mark step as completed
      setCompletedSteps(prev => new Set([...prev, 1]));

    } catch (err: any) {
      setSelectedManualError(err.message || `Error loading manual ${manual.id}`);
      console.error(err);
    } finally {
      setIsLoadingSelectedManualId(null);
    }
  };

  const handleDeleteManual = async (manualId: number) => {
    if (!window.confirm("Are you sure you want to delete this manual and its associated files? This action cannot be undone.")) {
      return;
    }
    setActiveDeletingManualId(manualId);
    setDeleteManualError(null);
    try {
      const response = await fetchWithNgrokHeaders(apiUrl(`/api/manuals/${manualId}`), { method: 'DELETE' });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete manual ${manualId}`);
      }
      
      fetchManagedManuals(); // Refresh list

      // If the deleted manual was the one currently loaded
      if (currentManualInfo?.manual_db_id === manualId) {
        setCurrentManualInfo(null);
        setSelectedTocItems(new Map());
        setProcessedSectionsResult(null);
      }

    } catch (err: any) {
      setDeleteManualError(err.message || `Error deleting manual ${manualId}`);
      console.error(err);
    } finally {
      setActiveDeletingManualId(null);
    }
  };

  const handleTocItemToggle = (item: TocItemType) => {
    const key = `${item.title}-${item.page}`;
    const isCurrentlySelected = selectedTocItems.has(key);
    
    setSelectedTocItems(prev => {
      const newMap = new Map(prev);
      
      if (isCurrentlySelected) {
        // Deselecting: Remove this item and all its children
        newMap.delete(key);
        
        // Find and remove all child items (higher level numbers after this item)
        if (currentManualInfo?.toc_data) {
          const currentIndex = currentManualInfo.toc_data.findIndex(tocItem => 
            `${tocItem.title}-${tocItem.page}` === key
          );
          
          if (currentIndex !== -1) {
            // Look ahead for child items (items with higher level that come after this one)
            for (let i = currentIndex + 1; i < currentManualInfo.toc_data.length; i++) {
              const nextItem = currentManualInfo.toc_data[i];
              
              // If we encounter an item at the same or lower level, stop
              if (nextItem.level <= item.level) {
                break;
              }
              
              // This is a child item, remove it
              const childKey = `${nextItem.title}-${nextItem.page}`;
              newMap.delete(childKey);
            }
          }
        }
      } else {
        // Selecting: Add this item and all its children
        newMap.set(key, item);
        
        // Find and add all child items
        if (currentManualInfo?.toc_data) {
          const currentIndex = currentManualInfo.toc_data.findIndex(tocItem => 
            `${tocItem.title}-${tocItem.page}` === key
          );
          
          if (currentIndex !== -1) {
            // Look ahead for child items
            for (let i = currentIndex + 1; i < currentManualInfo.toc_data.length; i++) {
              const nextItem = currentManualInfo.toc_data[i];
              
              // If we encounter an item at the same or lower level, stop
              if (nextItem.level <= item.level) {
                break;
              }
              
              // This is a child item, add it
              const childKey = `${nextItem.title}-${nextItem.page}`;
              newMap.set(childKey, nextItem);
            }
          }
        }
        
        // Check if we should auto-select parent items
        // If all siblings are now selected, select the parent too
        if (currentManualInfo?.toc_data && item.level > 1) {
          autoSelectParents(newMap, item);
        }
      }
      
      return newMap;
    });
  };

  // Helper function to auto-select parent items when all children are selected
  const autoSelectParents = (selectionMap: Map<string, TocItemType>, childItem: TocItemType) => {
    if (!currentManualInfo?.toc_data || childItem.level <= 1) return;
    
    const tocData = currentManualInfo.toc_data;
    const childIndex = tocData.findIndex(item => 
      `${item.title}-${item.page}` === `${childItem.title}-${childItem.page}`
    );
    
    if (childIndex === -1) return;
    
    // Find the parent (previous item with lower level)
    let parentIndex = -1;
    for (let i = childIndex - 1; i >= 0; i--) {
      if (tocData[i].level < childItem.level) {
        parentIndex = i;
        break;
      }
    }
    
    if (parentIndex === -1) return;
    
    const parentItem = tocData[parentIndex];
    const parentKey = `${parentItem.title}-${parentItem.page}`;
    
    // Find all children of this parent
    const parentChildren: TocItemType[] = [];
    for (let i = parentIndex + 1; i < tocData.length; i++) {
      const item = tocData[i];
      
      // If we hit an item at the same or lower level than parent, stop
      if (item.level <= parentItem.level) {
        break;
      }
      
      // If this is a direct child (one level deeper), add it
      if (item.level === parentItem.level + 1) {
        parentChildren.push(item);
      }
    }
    
    // Check if all direct children are selected
    const allChildrenSelected = parentChildren.every(child => {
      const childKey = `${child.title}-${child.page}`;
      return selectionMap.has(childKey);
    });
    
    // If all children are selected and parent isn't already selected, select parent
    if (allChildrenSelected && !selectionMap.has(parentKey)) {
      selectionMap.set(parentKey, parentItem);
      
      // Recursively check if we should select grandparent
      autoSelectParents(selectionMap, parentItem);
    }
  };

  const handleProcessSelectedSections = async () => {
    if (!currentManualInfo?.saved_manual_filename || selectedTocItems.size === 0) {
      setProcessSectionsError("Manual information or selected ToC items are missing.");
      return;
    }

    setIsProcessingSections(true);
    setProcessSectionsError(null);
    setProcessedSectionsResult(null);

    const payload = {
      manual_identifier: currentManualInfo.saved_manual_filename,
      year: year,
      selected_sections: Array.from(selectedTocItems.values()),
    };

    try {
      const response = await fetchWithNgrokHeaders(apiUrl("/api/manuals/process-sections"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        setProcessedSectionsResult(data);
      } else {
        setProcessSectionsError(data.detail || "Failed to process selected sections.");
      }
    } catch (err) {
      setProcessSectionsError("Error connecting to server for section processing.");
      console.error("Error processing sections:", err);
    } finally {
      setIsProcessingSections(false);
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return "N/A";
    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      return "Invalid Date";
    }
  };

  // Event selection handlers
  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newYear = parseInt(e.target.value);
    setYear(newYear);
    setSelectedEvent("");
    setSelectedEventName("");
    fetchEvents(newYear);
  };

  const handleEventChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const key = e.target.value;
    setSelectedEvent(key);

    const event = events.find(e => e.key === key);
    if (event) {
      setSelectedEventName(event.name);
    }
  };

  const checkForEventSwitch = () => {
    // If there's already an active event and user is trying to set up a different one
    if (currentEvent.event_key && selectedEvent && currentEvent.event_key !== selectedEvent) {
      // Store the pending action
      setPendingEventAction({
        eventKey: selectedEvent,
        eventName: selectedEventName,
        year: year
      });
      
      // Show the confirmation dialog
      setShowEventSwitchDialog(true);
    } else {
      // No event switch needed, proceed normally
      handleEventSetup();
    }
  };

  const handleEventSetup = async () => {
    const eventToUse = pendingEventAction?.eventKey || selectedEvent;
    const yearToUse = pendingEventAction?.year || year;
    
    if (!eventToUse) return;

    setIsSettingUpEvent(true);
    setEventsError(null);

    try {
      const formData = new FormData();
      formData.append("year", yearToUse.toString());
      formData.append("event_key", eventToUse);

      const response = await fetchWithNgrokHeaders(apiUrl("/api/setup/start"), {
        method: "POST",
        body: formData, 
      });

      const data = await response.json();

      if (response.ok) {
        setSetupResult(data);
        setCurrentEvent({
          event_key: eventToUse,
          event_name: selectedEventName || eventToUse,
          year: yearToUse
        });
        
        // Mark step as completed
        setCompletedSteps(prev => new Set([...prev, 2]));
        
        // Clear pending action
        setPendingEventAction(null);
      } else {
        setEventsError(data.detail || "Failed to set up event");
      }
    } catch (err) {
      setEventsError("Error connecting to server");
      console.error(err);
    } finally {
      setIsSettingUpEvent(false);
    }
  };

  // Manual event validation function
  const validateManualEvent = async (eventKey: string) => {
    if (!eventKey.trim()) {
      setManualEventValidation(null);
      return;
    }

    setIsValidatingManualEvent(true);
    setManualEventValidation(null);

    try {
      // Try to fetch event data from TBA API via backend
      const response = await fetchWithNgrokHeaders(apiUrl(`/api/setup/event/${eventKey}`));
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.status === 'success' && data.event) {
          const eventData = data.event;
          setManualEventValidation({
            isValid: true,
            eventData: {
              key: eventData.key,
              name: eventData.name,
              code: eventData.event_code,
              location: eventData.location_name || 
                       `${eventData.city || ''}${eventData.city && eventData.state_prov ? ', ' : ''}${eventData.state_prov || ''}${(eventData.city || eventData.state_prov) && eventData.country ? ', ' : ''}${eventData.country || ''}`.trim(),
              dates: eventData.start_date && eventData.end_date 
                ? `${eventData.start_date} to ${eventData.end_date}`
                : 'Dates TBD',
              type: eventData.event_type_string || 'Unknown',
              week: eventData.week || 0
            }
          });
          setSelectedEvent(eventKey);
          setSelectedEventName(eventData.name);
        } else {
          // Backend returned success but no event data
          setManualEventValidation({
            isValid: false,
            error: `Event "${eventKey}" not found in The Blue Alliance database. You can still proceed with this event code.`
          });
          setSelectedEvent(eventKey);
          setSelectedEventName(eventKey);
        }
      } else {
        // Event not found in TBA, but allow manual entry anyway
        setManualEventValidation({
          isValid: false,
          error: `Event "${eventKey}" not found in The Blue Alliance database. You can still proceed with this event code.`
        });
        setSelectedEvent(eventKey);
        setSelectedEventName(eventKey);
      }
    } catch (err) {
      console.error("Error validating manual event:", err);
      setManualEventValidation({
        isValid: false,
        error: "Unable to validate event. You can still proceed with this event code."
      });
      setSelectedEvent(eventKey);
      setSelectedEventName(eventKey);
    } finally {
      setIsValidatingManualEvent(false);
    }
  };

  // Handle manual event key input
  const handleManualEventKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setManualEventKey(value);
    
    if (value.length < 3) {
      setManualEventValidation(null);
      setSelectedEvent("");
      setSelectedEventName("");
    }
  };

  // Debounced validation effect
  useEffect(() => {
    if (manualEventKey.length >= 3) {
      const timeoutId = setTimeout(() => {
        validateManualEvent(manualEventKey);
      }, 500);
      
      return () => clearTimeout(timeoutId);
    }
  }, [manualEventKey]);

  const handleContinue = () => {
    navigate("/field-selection");
  };

  // Render step indicator
  const renderStepIndicator = () => {
    const steps = [
      { number: 1, title: "Manual Training", description: "Upload game manual" },
      { number: 2, title: "Event Selection", description: "Choose competition" },
      { number: 3, title: "Database Alignment", description: "Configure sheets" },
      { number: 4, title: "Setup Complete", description: "Review & finish" }
    ];

    return (
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <React.Fragment key={step.number}>
              <div
                className={`flex flex-col items-center cursor-pointer ${
                  step.number === currentStep ? 'text-blue-600' : 
                  completedSteps.has(step.number) ? 'text-green-600' : 'text-gray-400'
                }`}
                onClick={() => handleStepClick(step.number)}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg border-2 ${
                  step.number === currentStep ? 'bg-blue-600 text-white border-blue-600' :
                  completedSteps.has(step.number) ? 'bg-green-600 text-white border-green-600' :
                  'bg-white text-gray-400 border-gray-300'
                }`}>
                  {completedSteps.has(step.number) ? '✓' : step.number}
                </div>
                <div className="mt-2 text-center">
                  <div className="font-semibold">{step.title}</div>
                  <div className="text-sm text-gray-500">{step.description}</div>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className={`flex-1 h-1 mx-4 ${
                  completedSteps.has(step.number) ? 'bg-green-600' : 'bg-gray-300'
                }`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  };

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return renderManualTrainingStep();
      case 2:
        return renderEventSelectionStep();
      case 3:
        return renderDatabaseAlignmentStep();
      case 4:
        return renderSetupCompleteStep();
      default:
        return null;
    }
  };

  // Step 1: Manual Training
  const renderManualTrainingStep = () => (
    <div className="space-y-6">
      {/* Upload New Manual Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Upload Game Manual</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block mb-2 font-semibold">FRC Season Year</label>
            <select
              value={year}
              onChange={handleYearChange}
              className="w-full p-2 border rounded"
              disabled={isUploadingManual}
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 font-semibold">Game Manual PDF</label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleManualFileChange}
              disabled={isUploadingManual}
              className="w-full p-2 border rounded file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-blue-50 file:text-blue-700
                        hover:file:bg-blue-100"
            />
            {selectedManualFile && (
              <p className="mt-1 text-sm text-gray-600">
                Selected file: <strong>{selectedManualFile.name}</strong> ({(selectedManualFile.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>

          {manualUploadError && (
            <div className="p-3 bg-red-100 text-red-700 rounded">
              {manualUploadError}
            </div>
          )}

          <button
            onClick={handleManualUpload}
            disabled={!selectedManualFile || isUploadingManual}
            className="w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isUploadingManual ? "Uploading..." : "Upload Manual"}
          </button>
        </div>
      </div>

      {/* Existing Manuals Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Existing Manuals</h2>
        
        <button
          onClick={fetchManagedManuals}
          disabled={isLoadingManagedManuals}
          className="mb-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
        >
          {isLoadingManagedManuals ? "Refreshing..." : "Refresh List"}
        </button>

        {managedManualsError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">{managedManualsError}</div>}
        {deleteManualError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">Delete Error: {deleteManualError}</div>}
        {selectedManualError && <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">Load Error: {selectedManualError}</div>}

        {isLoadingManagedManuals && !managedManuals.length ? (
          <p>Loading manuals...</p>
        ) : !managedManuals.length && !managedManualsError ? (
          <p>No manuals uploaded yet.</p>
        ) : managedManuals.length > 0 ? (
          <div className="overflow-x-auto max-h-96">
            <table className="min-w-full border text-sm">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="border px-3 py-2 text-left">Filename</th>
                  <th className="border px-3 py-2 text-left">Year</th>
                  <th className="border px-3 py-2 text-left">Uploaded</th>
                  <th className="border px-3 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {managedManuals.map(manual => (
                  <tr key={manual.id} className="hover:bg-gray-50">
                    <td className="border px-3 py-2">{manual.original_filename}</td>
                    <td className="border px-3 py-2">{manual.year}</td>
                    <td className="border px-3 py-2">{formatTimestamp(manual.upload_timestamp)}</td>
                    <td className="border px-3 py-2">
                      <button
                        onClick={() => handleSelectManagedManual(manual)}
                        disabled={isLoadingSelectedManualId === manual.id}
                        className="mr-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 disabled:bg-blue-300"
                      >
                        {isLoadingSelectedManualId === manual.id ? "Loading..." : "Load ToC"}
                      </button>
                      <button
                        onClick={() => handleDeleteManual(manual.id)}
                        disabled={activeDeletingManualId === manual.id}
                        className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 disabled:bg-red-300"
                      >
                        {activeDeletingManualId === manual.id ? "Deleting..." : "Delete"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {/* ToC Selection Section */}
      {currentManualInfo?.toc_data && currentManualInfo.toc_data.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-2">Table of Contents - {currentManualInfo.original_filename}</h3>
          <p className="text-sm text-gray-600 mb-4">
            💡 <strong>Tip:</strong> Selecting a major section will automatically select all its subsections. 
            Selecting all subsections will automatically select the parent section.
          </p>
          <div className="max-h-96 overflow-y-auto border rounded p-4 bg-gray-50 space-y-1">
            {currentManualInfo.toc_data.map((item: TocItemType, index: number) => {
              const key = `${item.title}-${item.page}`;
              const isMainSection = item.level === 1;
              const hasChildren = index < currentManualInfo.toc_data.length - 1 && 
                                  currentManualInfo.toc_data[index + 1].level > item.level;
              
              return (
                <div 
                  key={key} 
                  className={`flex items-center py-1 px-2 rounded hover:bg-blue-50 ${
                    isMainSection ? 'bg-blue-25' : ''
                  }`} 
                  style={{ marginLeft: `${(item.level -1) * 20}px`}}
                >
                  <input
                    type="checkbox"
                    id={`toc-${key}`}
                    checked={selectedTocItems.has(key)}
                    onChange={() => handleTocItemToggle(item)}
                    className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label 
                    htmlFor={`toc-${key}`} 
                    className={`text-sm cursor-pointer hover:text-blue-700 ${
                      isMainSection ? 'font-medium text-gray-900' : 'text-gray-700'
                    }`}
                  >
                    {hasChildren && isMainSection && '📁 '}
                    {item.title} 
                    <span className="text-gray-500 text-xs ml-1">(p. {item.page})</span>
                  </label>
                </div>
              );
            })}
          </div>
          {selectedTocItems.size > 0 && (
            <button
              onClick={handleProcessSelectedSections}
              disabled={isProcessingSections}
              className="mt-4 w-full py-2 px-4 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:bg-indigo-300"
            >
              {isProcessingSections ? "Processing Sections..." : `Process ${selectedTocItems.size} Selected Section(s)`}
            </button>
          )}
          {processSectionsError && (
            <div className="mt-2 p-3 bg-red-100 text-red-700 rounded">
              {processSectionsError}
            </div>
          )}
          {processedSectionsResult && (
            <div className="mt-2 p-3 bg-green-50 text-green-700 rounded">
              <h4 className="font-semibold">Sections Processed Successfully!</h4>
              <p className="text-sm">Saved to: {processedSectionsResult.saved_text_path}</p>
              <p className="text-sm">Extracted Length: {processedSectionsResult.extracted_text_length} chars</p>
              <p className="text-xs mt-1">Sample: <pre className="whitespace-pre-wrap bg-gray-100 p-1 rounded text-xs">{processedSectionsResult.sample_text}</pre></p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Step 2: Event Selection
  const renderEventSelectionStep = () => (
    <div className="space-y-6">
      {/* Event Switch Confirmation Dialog */}
      {showEventSwitchDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
            <div className="flex items-center text-yellow-600 mb-4">
              <svg className="w-6 h-6 mr-2" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
              <h3 className="text-xl font-bold">Change Active Event?</h3>
            </div>
            
            <p className="mb-4">
              An event is already loaded in the system: <strong>{currentEvent.event_name || currentEvent.event_key}</strong>
            </p>
            
            <p className="mb-4">
              To switch to <strong>{pendingEventAction?.eventName || pendingEventAction?.eventKey}</strong>, you must either:
            </p>
            
            <ul className="list-disc pl-5 mb-6 text-gray-700">
              <li className="mb-2">Archive the current event (recommended to preserve data)</li>
              <li className="mb-2">Continue without archiving (data may be lost)</li>
              <li>Cancel and keep working with the current event</li>
            </ul>
            
            <div className="flex flex-col space-y-3">
              <button
                onClick={() => {
                  setShowEventSwitchDialog(false);
                  setCurrentStep(2); // Stay on event selection
                  document.getElementById("archiveSection")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Archive Current Event
              </button>
              
              <button
                onClick={() => {
                  setShowEventSwitchDialog(false);
                  handleEventSetup();
                }}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
              >
                Continue Without Archiving
              </button>
              
              <button
                onClick={() => {
                  setShowEventSwitchDialog(false);
                  setPendingEventAction(null);
                  setSelectedEvent(currentEvent.event_key || "");
                  setSelectedEventName(currentEvent.event_name || "");
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Current Event Display */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Current Event</h2>
        
        {isLoadingCurrentEvent ? (
          <div className="p-2 text-blue-600">Loading current event...</div>
        ) : (
          <div className="mb-6">
            <div className="flex items-center">
              <span className="font-semibold mr-2">Active Event:</span>
              {currentEvent.event_key ? (
                <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
                  {currentEvent.event_name || currentEvent.event_key} ({currentEvent.year})
                </span>
              ) : (
                <span className="px-3 py-1 rounded-full bg-yellow-100 text-yellow-800">
                  None Selected
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Event Selection Form */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Select Event</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block mb-2 font-semibold">FRC Season Year</label>
            <select
              value={year}
              onChange={handleYearChange}
              className="w-full p-2 border rounded"
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block font-semibold">Select Event</label>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Manual Input</span>
                <button
                  type="button"
                  onClick={() => {
                    setIsManualEventMode(!isManualEventMode);
                    setSelectedEvent("");
                    setSelectedEventName("");
                    setManualEventKey("");
                    setManualEventValidation(null);
                  }}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isManualEventMode ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isManualEventMode ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>

            {isManualEventMode ? (
              <div className="space-y-3">
                <div>
                  <input
                    type="text"
                    value={manualEventKey}
                    onChange={handleManualEventKeyChange}
                    placeholder="Enter event code (e.g., 2025txhou, 2025casd, 2025nyny)"
                    className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {isValidatingManualEvent && (
                    <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                        <span className="text-blue-600 text-sm">Validating event...</span>
                      </div>
                    </div>
                  )}
                </div>

                {manualEventValidation && (
                  <div className={`p-3 rounded border ${
                    manualEventValidation.isValid 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-yellow-50 border-yellow-200'
                  }`}>
                    {manualEventValidation.isValid && manualEventValidation.eventData ? (
                      <div>
                        <div className="flex items-center mb-2">
                          <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                          </svg>
                          <span className="font-semibold text-green-800">Event Found!</span>
                        </div>
                        <p className="font-semibold">{manualEventValidation.eventData.name}</p>
                        <p className="text-sm mt-1">
                          Event Code: {manualEventValidation.eventData.key}
                          <span className="ml-2">({manualEventValidation.eventData.dates})</span>
                        </p>
                        <p className="text-sm">
                          Location: {manualEventValidation.eventData.location}
                        </p>
                        <p className="text-sm">
                          Type: {manualEventValidation.eventData.type}
                        </p>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center mb-2">
                          <svg className="w-5 h-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
                          </svg>
                          <span className="font-semibold text-yellow-800">Note</span>
                        </div>
                        <p className="text-sm text-yellow-800">{manualEventValidation.error}</p>
                      </div>
                    )}
                  </div>
                )}

                <p className="text-sm text-gray-500">
                  Enter the event code manually. The system will try to validate it against The Blue Alliance database and pull event details automatically.
                </p>
              </div>
            ) : (
              <>
                {loadingEvents ? (
                  <div className="p-2 text-blue-600">Loading events...</div>
                ) : eventsError ? (
                  <div className="p-2 text-red-600">{eventsError}</div>
                ) : (
                  <div className="space-y-2">
                    <select
                      value={selectedEvent}
                      onChange={handleEventChange}
                      className="w-full p-2 border rounded"
                    >
                      <option value="">-- Select an event --</option>

                      {/* Display events grouped by type */}
                      {Object.entries(groupedEvents).map(([type, eventsList]) => (
                        <optgroup key={type} label={type}>
                          {eventsList.map(event => (
                            <option key={event.key} value={event.key}>
                              {event.name} - {event.location}
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>

                    {selectedEvent && (
                      <div className="p-2 bg-blue-50 border border-blue-200 rounded">
                        <p className="font-semibold">{selectedEventName}</p>
                        <p className="text-sm mt-1">
                          Event Code: {selectedEvent}
                          {events.find(e => e.key === selectedEvent)?.dates && (
                            <span className="ml-2">
                              ({events.find(e => e.key === selectedEvent)?.dates})
                            </span>
                          )}
                        </p>
                      </div>
                    )}

                    <p className="text-sm text-gray-500">
                      Select the event you're scouting for from the official TBA event list. This will be used to pre-populate team lists and event data.
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          <button
            onClick={checkForEventSwitch}
            disabled={!selectedEvent || loadingEvents || isSettingUpEvent}
            className="w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          >
            {isSettingUpEvent ? "Setting up event..." : "Set Event"}
          </button>
        </div>
      </div>

      {/* Success Message */}
      {setupResult && !isSettingUpEvent && (
        <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
            </svg>
            <span className="text-green-800 font-medium">Event successfully configured!</span>
          </div>
        </div>
      )}

      {/* Sample Teams Display */}
      {setupResult && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Event Setup Details</h2>
          
          
          {setupResult.sample_teams && setupResult.sample_teams.length > 0 ? (
            <>
              <h3 className="text-lg font-semibold mb-2">Sample Teams from {selectedEventName || currentEvent.event_name}</h3>
              <p className="text-sm text-gray-600 mb-4">
                These teams are participating in the selected event. This confirms we're connected to the correct event data.
              </p>
              <div className="overflow-x-auto">
                <table className="min-w-full border">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border px-4 py-2">Team #</th>
                      <th className="border px-4 py-2">Name</th>
                      <th className="border px-4 py-2">EPA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {setupResult.sample_teams.map((team: any) => (
                      <tr key={team.team_number}>
                        <td className="border px-4 py-2">{team.team_number}</td>
                        <td className="border px-4 py-2">{team.team_name}</td>
                        <td className="border px-4 py-2">{team.epa_total?.toFixed(1) || "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="text-gray-600">No sample teams data available. Check console for setup response.</p>
          )}
        </div>
      )}

      {/* Event Archive Manager */}
      <div id="archiveSection" className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Event Management</h2>
        
        <EventArchiveManager
          currentEventKey={currentEvent.event_key || selectedEvent}
          currentYear={currentEvent.year || year}
          onArchiveSuccess={() => {
            console.log("Archive success callback triggered");
            setSetupResult(null);
            
            // If there was a pending event change, proceed with it after archiving
            if (pendingEventAction) {
              setSelectedEvent(pendingEventAction.eventKey);
              setSelectedEventName(pendingEventAction.eventName);
              setYear(pendingEventAction.year);
              setPendingEventAction(null);
              
              // Wait a moment then submit the form
              setTimeout(() => {
                handleEventSetup();
              }, 500);
            }
          }}
          onRestoreSuccess={() => {
            console.log("Restore success callback triggered");
            window.location.reload();
          }}
        />
      </div>
    </div>
  );

  // Step 3: Database Alignment
  const renderDatabaseAlignmentStep = () => (
    <div className="space-y-6">
      {/* Sheet Configuration Manager */}
      <div className="bg-white p-6 rounded-lg shadow">
        <SheetConfigManager
          currentEventKey={currentEvent.event_key || selectedEvent}
          currentYear={currentEvent.year || year}
          onConfigurationChange={() => {
            console.log("Configuration changed");
            // Mark step as completed when configuration is saved
            setCompletedSteps(prev => new Set([...prev, 3]));
          }}
          onConfigurationConfirmed={() => {
            console.log("Configuration confirmed for use");
            // Mark step as completed when user confirms to use active configuration
            setCompletedSteps(prev => new Set([...prev, 3]));
          }}
        />
      </div>

    </div>
  );

  // Step 4: Setup Complete Summary
  const renderSetupCompleteStep = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center mb-6">
          <svg className="w-8 h-8 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
          </svg>
          <h2 className="text-2xl font-bold text-green-800">Setup Complete!</h2>
        </div>

        <p className="text-gray-600 mb-6">
          Your FRC Scouting Assistant has been successfully configured. Here's a summary of your setup:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Manual Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"/>
              </svg>
              Game Manual
            </h3>
            {currentManualInfo ? (
              <div>
                <p className="text-sm text-gray-700">
                  <strong>File:</strong> {currentManualInfo.original_filename}
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Year:</strong> {year}
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Status:</strong> {currentManualInfo.using_cached_manual ? 'Loaded from database' : 'Newly uploaded'}
                </p>
                {processedSectionsResult && (
                  <p className="text-sm text-green-700">
                    <strong>Processed Sections:</strong> {selectedTocItems.size} sections extracted
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-yellow-700">Using existing manual for {year} or basic analysis</p>
            )}
          </div>

          {/* Event Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
              </svg>
              Event Selection
            </h3>
            <div>
              <p className="text-sm text-gray-700">
                <strong>Event:</strong> {currentEvent.event_name || currentEvent.event_key}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Year:</strong> {currentEvent.year || year}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Event Key:</strong> {currentEvent.event_key}
              </p>
              {setupResult?.sample_teams && (
                <p className="text-sm text-green-700">
                  <strong>Teams Found:</strong> {setupResult.sample_teams.length} sample teams loaded
                </p>
              )}
            </div>
          </div>

          {/* Sheets Configuration */}
          <div className="bg-gray-50 p-4 rounded-lg md:col-span-2">
            <h3 className="font-semibold text-lg mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V8z" clipRule="evenodd"/>
              </svg>
              Google Sheets Configuration
            </h3>
            {completedSteps.has(3) ? (
              <p className="text-sm text-green-700">
                ✓ Google Sheets configuration has been completed. Sheet mappings are ready for field selection.
              </p>
            ) : (
              <p className="text-sm text-yellow-700">
                Configuration in progress - please complete the sheets setup above.
              </p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleContinue}
              className="flex-1 py-3 px-6 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
            >
              Continue to Field Selection →
            </button>
            
            <button
              onClick={() => setCurrentStep(1)}
              className="flex-1 py-3 px-6 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Review Setup Steps
            </button>
          </div>
          
          <p className="text-center text-sm text-gray-500">
            You can return to setup at any time to modify these configurations.
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">FRC Scouting Assistant Setup</h1>

      {/* Step Indicator */}
      {renderStepIndicator()}

      {/* Step Content */}
      {renderStepContent()}

      {/* Navigation Buttons */}
      <div className="mt-8 flex justify-between">
        <button
          onClick={handlePreviousStep}
          disabled={currentStep === 1}
          className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
        >
          Previous
        </button>
        
        {currentStep < 4 && (
          <button
            onClick={handleNextStep}
            disabled={!canProceedToNextStep()}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          >
            {currentStep === 3 ? "Review Setup" : "Next"}
          </button>
        )}
      </div>
    </div>
  );
}

export default Setup;