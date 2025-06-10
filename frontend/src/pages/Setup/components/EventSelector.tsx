import React from 'react';
import type { Event, GroupedEvents } from '../types';

interface EventSelectorProps {
  year: number;
  selectedEvent: string;
  selectedEventName: string;
  events: Event[];
  groupedEvents: GroupedEvents;
  loadingEvents: boolean;
  eventsError: string | null;
  isSettingUpEvent: boolean;
  onYearChange: (year: number) => void;
  onEventChange: (eventKey: string) => void;
  onEventSetup: () => void;
}

export const EventSelector: React.FC<EventSelectorProps> = ({
  year,
  selectedEvent,
  selectedEventName,
  events,
  groupedEvents,
  loadingEvents,
  eventsError,
  isSettingUpEvent,
  onYearChange,
  onEventChange,
  onEventSetup
}) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">Select Event</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block mb-2 font-semibold">FRC Season Year</label>
          <select
            value={year}
            onChange={(e) => onYearChange(parseInt(e.target.value))}
            className="w-full p-2 border rounded"
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
          </select>
        </div>

        <div>
          <label className="block mb-2 font-semibold">Select Event</label>
          {loadingEvents ? (
            <div className="p-2 text-blue-600">Loading events...</div>
          ) : eventsError ? (
            <div className="p-2 text-red-600">{eventsError}</div>
          ) : (
            <div className="space-y-2">
              <select
                value={selectedEvent}
                onChange={(e) => onEventChange(e.target.value)}
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
                Select the event you're scouting for. This will be used to pre-populate team lists and event data.
              </p>
            </div>
          )}
        </div>

        <button
          onClick={onEventSetup}
          disabled={!selectedEvent || loadingEvents || isSettingUpEvent}
          className="w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
        >
          {isSettingUpEvent ? "Setting up event..." : "Set Event"}
        </button>
      </div>
    </div>
  );
};