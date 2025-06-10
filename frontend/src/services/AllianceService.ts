/**
 * Alliance Selection API Service
 */

import { apiClient } from './ApiClient';
import {
  CreateAllianceSelectionRequest,
  TeamActionRequest,
  AllianceSelectionResponse,
  SuccessResponse,
} from './types';

export class AllianceService {
  private basePath = '/alliance-selection';

  /**
   * Get current alliance selection state
   */
  async getSelection(eventKey: string): Promise<AllianceSelectionResponse | null> {
    try {
      return await apiClient.get<AllianceSelectionResponse>(
        `${this.basePath}/${eventKey}`
      );
    } catch (error: any) {
      if (error.status === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Create new alliance selection
   */
  async createSelection(data: CreateAllianceSelectionRequest): Promise<AllianceSelectionResponse> {
    return await apiClient.post<AllianceSelectionResponse>(
      this.basePath,
      data
    );
  }

  /**
   * Reset alliance selection
   */
  async resetSelection(eventKey: string): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.basePath}/${eventKey}/reset`
    );
  }

  /**
   * Advance to next round
   */
  async advanceRound(eventKey: string): Promise<AllianceSelectionResponse> {
    return await apiClient.post<AllianceSelectionResponse>(
      `${this.basePath}/${eventKey}/advance-round`
    );
  }

  /**
   * Perform team action (captain, accept, decline, remove)
   */
  async teamAction(eventKey: string, data: TeamActionRequest): Promise<AllianceSelectionResponse> {
    return await apiClient.post<AllianceSelectionResponse>(
      `${this.basePath}/${eventKey}/team-action`,
      data
    );
  }

  /**
   * Get available teams for selection
   */
  async getAvailableTeams(eventKey: string): Promise<AllianceSelectionResponse['available_teams']> {
    const selection = await this.getSelection(eventKey);
    return selection?.available_teams || [];
  }

  /**
   * Get alliance by number
   */
  async getAlliance(eventKey: string, allianceNumber: number) {
    const selection = await this.getSelection(eventKey);
    return selection?.alliances.find(a => a.number === allianceNumber);
  }

  /**
   * Check if selection is complete
   */
  async isSelectionComplete(eventKey: string): Promise<boolean> {
    const selection = await this.getSelection(eventKey);
    return selection?.is_complete || false;
  }

  /**
   * Export alliance selection data
   */
  async exportSelection(eventKey: string): Promise<Blob> {
    const response = await apiClient.get<any>(
      `${this.basePath}/${eventKey}/export`,
      {
        headers: {
          'Accept': 'application/json',
        },
      }
    );
    return new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
  }
}

// Export singleton instance
export const allianceService = new AllianceService();