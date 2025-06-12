/**
 * Event Management API Service
 */

import { apiClient } from './ApiClient';
import {
  UpdateEventRequest,
  ArchiveEventRequest,
  EventResponse,
  ArchivedEventResponse,
  SuccessResponse,
  PaginatedResponse,
} from './types';

export class EventService {
  private basePath = '/events';
  private archivePath = '/archive';

  /**
   * Get all events
   */
  async getEvents(year?: number): Promise<EventResponse[]> {
    const path = year ? `${this.basePath}/${year}` : this.basePath;
    return await apiClient.get<EventResponse[]>(path);
  }

  /**
   * Get event by key
   */
  async getEvent(eventKey: string): Promise<EventResponse> {
    return await apiClient.get<EventResponse>(
      `${this.basePath}/${eventKey}`
    );
  }

  /**
   * Get active event
   */
  async getActiveEvent(): Promise<EventResponse | null> {
    try {
      return await apiClient.get<EventResponse>(
        `${this.basePath}/active`
      );
    } catch (error: any) {
      if (error.status === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Set active event
   */
  async setActiveEvent(eventKey: string): Promise<EventResponse> {
    return await apiClient.post<EventResponse>(
      `${this.basePath}/${eventKey}/activate`
    );
  }

  /**
   * Update event
   */
  async updateEvent(eventKey: string, data: UpdateEventRequest): Promise<EventResponse> {
    return await apiClient.patch<EventResponse>(
      `${this.basePath}/${eventKey}`,
      data
    );
  }

  /**
   * Archive event
   */
  async archiveEvent(data: ArchiveEventRequest): Promise<ArchivedEventResponse> {
    return await apiClient.post<ArchivedEventResponse>(
      `${this.archivePath}/event`,
      data
    );
  }

  /**
   * Get archived events
   */
  async getArchivedEvents(
    page = 1,
    pageSize = 20
  ): Promise<{ status: string; archives: ArchivedEventResponse[] }> {
    return await apiClient.get<{ status: string; archives: ArchivedEventResponse[] }>(
      `${this.archivePath}/list`,
      {
        params: { page, page_size: pageSize },
      }
    );
  }

  /**
   * Restore archived event
   */
  async restoreArchivedEvent(archiveId: number): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.archivePath}/restore/${archiveId}`
    );
  }

  /**
   * Delete archived event
   */
  async deleteArchivedEvent(archiveId: number): Promise<SuccessResponse> {
    return await apiClient.delete<SuccessResponse>(
      `${this.archivePath}/${archiveId}`
    );
  }

  /**
   * Get event teams
   */
  async getEventTeams(eventKey: string): Promise<any[]> {
    return await apiClient.get<any[]>(
      `${this.basePath}/${eventKey}/teams`
    );
  }

  /**
   * Get event matches
   */
  async getEventMatches(eventKey: string): Promise<any[]> {
    return await apiClient.get<any[]>(
      `${this.basePath}/${eventKey}/matches`
    );
  }

  /**
   * Get event rankings
   */
  async getEventRankings(eventKey: string): Promise<any> {
    return await apiClient.get<any>(
      `${this.basePath}/${eventKey}/rankings`
    );
  }

  /**
   * Sync event data from TBA
   */
  async syncEventData(eventKey: string): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.basePath}/${eventKey}/sync`
    );
  }
}

// Export singleton instance
export const eventService = new EventService();