// TypeScript definitions for Setup page

export interface Event {
  key: string;
  name: string;
  code: string;
  location: string;
  dates: string;
  type: string;
  week: number;
}

export interface GroupedEvents {
  [key: string]: Event[];
}

export interface EventInfo {
  event_key?: string;
  event_name?: string;
  year?: number;
}

export interface TocItemType {
  title: string;
  level: number;
  page: number;
  [key: string]: any;
}

export interface GameManualBase {
  id: number;
  year: number;
  original_filename: string;
  sanitized_filename_base: string;
  upload_timestamp?: string;
  last_accessed_timestamp?: string;
}

export interface GameManualResponse extends GameManualBase {}

export interface GameManualDetailResponse extends GameManualResponse {
  stored_pdf_path?: string;
  toc_json_path?: string;
  parsed_sections_path?: string;
  toc_content?: TocItemType[];
  toc_error?: string;
}

export interface CurrentManualInfo {
  manual_db_id?: number;
  saved_manual_filename?: string;
  original_filename?: string;
  sanitized_filename_base?: string;
  toc_data?: TocItemType[];
  toc_found?: boolean;
  toc_extraction_attempted?: boolean;
  analysis_complete?: boolean;
  text_length?: number;
  using_cached_manual?: boolean;
  toc_error?: string;
}

export interface ProcessedSectionsResult {
  saved_text_path: string;
  extracted_text_length: number;
  sample_text: string;
}

export interface SetupResult {
  status: string;
  message?: string;
  sample_teams?: Array<{
    team_number: number;
    team_name: string;
    epa_total?: number;
  }>;
  manual_info?: CurrentManualInfo;
}

export interface PendingEventAction {
  eventKey: string;
  eventName: string;
  year: number;
}

export interface SetupState {
  // Step management
  currentStep: number;
  completedSteps: Set<number>;
  
  // Manual training states
  selectedManualFile: File | null;
  isUploadingManual: boolean;
  manualUploadError: string | null;
  selectedTocItems: Map<string, TocItemType>;
  processedSectionsResult: ProcessedSectionsResult | null;
  isProcessingSections: boolean;
  processSectionsError: string | null;
  currentManualInfo: CurrentManualInfo | null;
  
  // Manual management states
  managedManuals: GameManualResponse[];
  isLoadingManagedManuals: boolean;
  managedManualsError: string | null;
  activeDeletingManualId: number | null;
  deleteManualError: string | null;
  isLoadingSelectedManualId: number | null;
  selectedManualError: string | null;
  
  // Event selection states
  year: number;
  loadingEvents: boolean;
  eventsError: string | null;
  events: Event[];
  groupedEvents: GroupedEvents;
  selectedEvent: string;
  selectedEventName: string;
  
  // Current event state
  currentEvent: EventInfo;
  isLoadingCurrentEvent: boolean;
  
  // Event switching confirmation
  showEventSwitchDialog: boolean;
  pendingEventAction: PendingEventAction | null;
  
  // Setup result state
  setupResult: SetupResult | null;
  isSettingUpEvent: boolean;
}

export interface SetupStep {
  number: number;
  title: string;
  description: string;
}

export const SETUP_STEPS: SetupStep[] = [
  { number: 1, title: "Manual Training", description: "Upload game manual" },
  { number: 2, title: "Event Selection", description: "Choose competition" },
  { number: 3, title: "Database Alignment", description: "Configure sheets" },
  { number: 4, title: "Setup Complete", description: "Review & finish" }
];