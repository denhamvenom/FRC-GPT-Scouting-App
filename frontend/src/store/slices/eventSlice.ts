import { StateCreator } from 'zustand';
import { AppStore } from '../useAppStore';
import { AppStateService } from '../../services/AppStateService';

// Types for event slice
export interface EventMetadata {
  name: string;
  location: string;
  startDate: string;
  endDate: string;
  weekNumber: number;
  status: 'upcoming' | 'active' | 'completed';
  teamsCount: number;
  matchesCount: number;
}

export interface EventState {
  currentEventKey: string | null;
  currentYear: number;
  eventMetadata: EventMetadata | null;
  recentEvents: RecentEvent[];
  eventCache: Record<string, EventMetadata>;
}

export interface RecentEvent {
  eventKey: string;
  year: number;
  name: string;
  lastAccessed: number;
}

export interface EventActions {
  // Event management
  setEvent: (eventKey: string, year: number, metadata?: EventMetadata) => void;
  clearEvent: () => void;
  updateEventMetadata: (metadata: Partial<EventMetadata>) => void;
  
  // Recent events
  addRecentEvent: (event: Omit<RecentEvent, 'lastAccessed'>) => void;
  removeRecentEvent: (eventKey: string, year: number) => void;
  clearRecentEvents: () => void;
  
  // Event cache
  cacheEventMetadata: (eventKey: string, metadata: EventMetadata) => void;
  getCachedEventMetadata: (eventKey: string) => EventMetadata | null;
  clearEventCache: () => void;
  
  // Utilities
  isEventSelected: () => boolean;
  getEventDisplayName: () => string;
  canSwitchEvent: () => boolean;
}

export type EventSlice = EventState & EventActions;

// Create the event slice
export const createEventSlice: StateCreator<
  AppStore,
  [],
  [],
  EventSlice
> = (set, get) => ({
  // Initial state
  currentEventKey: null,
  currentYear: 2025,
  eventMetadata: null,
  recentEvents: [],
  eventCache: {},
  
  // Event management
  setEvent: (eventKey, year, metadata) => {
    set((state) => {
      const newRecentEvent: RecentEvent = {
        eventKey,
        year,
        name: metadata?.name || eventKey,
        lastAccessed: Date.now(),
      };
      
      // Update recent events (keep last 10)
      const filteredRecent = state.recentEvents
        .filter(e => !(e.eventKey === eventKey && e.year === year))
        .slice(0, 9);
      
      return {
        currentEventKey: eventKey,
        currentYear: year,
        eventMetadata: metadata || null,
        recentEvents: [newRecentEvent, ...filteredRecent],
        ...(metadata && {
          eventCache: {
            ...state.eventCache,
            [`${eventKey}-${year}`]: metadata,
          },
        }),
      };
    });
    
    // Sync with AppStateService
    AppStateService.setCurrentEvent(eventKey, year);
  },
  
  clearEvent: () => {
    set({
      currentEventKey: null,
      currentYear: 2025,
      eventMetadata: null,
    });
  },
  
  updateEventMetadata: (metadata) => {
    set((state) => ({
      eventMetadata: state.eventMetadata
        ? { ...state.eventMetadata, ...metadata }
        : null,
    }));
  },
  
  // Recent events
  addRecentEvent: (event) => {
    set((state) => {
      const newEvent: RecentEvent = {
        ...event,
        lastAccessed: Date.now(),
      };
      
      // Remove existing entry for this event
      const filtered = state.recentEvents.filter(
        e => !(e.eventKey === event.eventKey && e.year === event.year)
      );
      
      // Add new entry at the beginning and keep last 10
      return {
        recentEvents: [newEvent, ...filtered].slice(0, 10),
      };
    });
  },
  
  removeRecentEvent: (eventKey, year) => {
    set((state) => ({
      recentEvents: state.recentEvents.filter(
        e => !(e.eventKey === eventKey && e.year === year)
      ),
    }));
  },
  
  clearRecentEvents: () => {
    set({ recentEvents: [] });
  },
  
  // Event cache
  cacheEventMetadata: (eventKey, metadata) => {
    set((state) => ({
      eventCache: {
        ...state.eventCache,
        [`${eventKey}-${metadata.name || 'unknown'}`]: metadata,
      },
    }));
  },
  
  getCachedEventMetadata: (eventKey) => {
    const cache = get().eventCache;
    return cache[eventKey] || null;
  },
  
  clearEventCache: () => {
    set({ eventCache: {} });
  },
  
  // Utilities
  isEventSelected: () => {
    const { currentEventKey } = get();
    return !!currentEventKey;
  },
  
  getEventDisplayName: () => {
    const { currentEventKey, eventMetadata } = get();
    if (!currentEventKey) return 'No Event Selected';
    return eventMetadata?.name || currentEventKey;
  },
  
  canSwitchEvent: () => {
    // Add logic to determine if event switching is allowed
    // For example, check if there are unsaved changes
    return true;
  },
});

// Import this in main store file
export default createEventSlice;