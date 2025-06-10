/**
 * Picklist Generation API Service
 */

import { apiClient } from './ApiClient';
import {
  GeneratePicklistRequest,
  CompareTeamsRequest,
  LockPicklistRequest,
  PicklistGenerateResponse,
  PicklistStatusResponse,
  TeamComparisonResponse,
  LockedPicklistResponse,
  SuccessResponse,
} from './types';

export class PicklistService {
  private basePath = '/picklist';

  /**
   * Generate a new picklist
   */
  async generatePicklist(data: GeneratePicklistRequest): Promise<PicklistGenerateResponse> {
    return await apiClient.post<PicklistGenerateResponse>(
      `${this.basePath}/generate`,
      data
    );
  }

  /**
   * Get picklist generation status
   */
  async getStatus(operationId: string): Promise<PicklistStatusResponse> {
    return await apiClient.get<PicklistStatusResponse>(
      `${this.basePath}/status/${operationId}`
    );
  }

  /**
   * Compare multiple teams
   */
  async compareTeams(data: CompareTeamsRequest): Promise<TeamComparisonResponse> {
    return await apiClient.post<TeamComparisonResponse>(
      `${this.basePath}/compare`,
      data
    );
  }

  /**
   * Lock a picklist
   */
  async lockPicklist(data: LockPicklistRequest): Promise<LockedPicklistResponse> {
    return await apiClient.post<LockedPicklistResponse>(
      `${this.basePath}/lock`,
      data
    );
  }

  /**
   * Get locked picklist
   */
  async getLockedPicklist(eventKey: string): Promise<LockedPicklistResponse | null> {
    try {
      return await apiClient.get<LockedPicklistResponse>(
        `${this.basePath}/locked/${eventKey}`
      );
    } catch (error: any) {
      if (error.status === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Update locked picklist
   */
  async updateLockedPicklist(eventKey: string, data: Partial<LockPicklistRequest>): Promise<LockedPicklistResponse> {
    return await apiClient.put<LockedPicklistResponse>(
      `${this.basePath}/locked/${eventKey}`,
      data
    );
  }

  /**
   * Delete locked picklist
   */
  async deleteLockedPicklist(eventKey: string): Promise<SuccessResponse> {
    return await apiClient.delete<SuccessResponse>(
      `${this.basePath}/locked/${eventKey}`
    );
  }

  /**
   * Clear picklist cache
   */
  async clearCache(): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.basePath}/clear-cache`
    );
  }

  /**
   * Poll for picklist completion
   */
  async pollForCompletion(
    operationId: string,
    onProgress?: (progress: number, message?: string) => void,
    maxAttempts = 60,
    interval = 2000
  ): Promise<PicklistGenerateResponse> {
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      const status = await this.getStatus(operationId);
      
      if (status.progress !== undefined && onProgress) {
        onProgress(status.progress, status.message);
      }
      
      if (status.status === 'completed' && status.result) {
        return status.result;
      }
      
      if (status.status === 'failed') {
        throw new Error(status.message || 'Picklist generation failed');
      }
      
      await new Promise(resolve => setTimeout(resolve, interval));
      attempts++;
    }
    
    throw new Error('Picklist generation timed out');
  }

  /**
   * Export picklist as CSV
   */
  async exportPicklist(eventKey: string, picklist: any[]): Promise<Blob> {
    const headers = ['Rank', 'Team Number', 'Team Name', 'Score', 'Reasoning'];
    const rows = picklist.map((team, index) => [
      index + 1,
      team.team_number,
      team.nickname,
      team.score,
      team.reasoning?.replace(/,/g, ';'), // Replace commas in reasoning
    ]);
    
    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
    ].join('\n');
    
    return new Blob([csv], { type: 'text/csv' });
  }
}

// Export singleton instance
export const picklistService = new PicklistService();