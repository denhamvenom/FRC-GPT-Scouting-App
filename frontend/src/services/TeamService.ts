/**
 * Team API Service
 */

import { apiClient } from './ApiClient';
import {
  GetTeamRequest,
  GetTeamHistoryRequest,
  TeamResponse,
  PaginatedResponse,
} from './types';

export class TeamService {
  private basePath = '/teams';

  /**
   * Get team information
   */
  async getTeam(teamNumber: number, eventKey?: string): Promise<TeamResponse> {
    const params: GetTeamRequest = { team_number: teamNumber };
    if (eventKey) {
      params.event_key = eventKey;
    }
    
    return await apiClient.get<TeamResponse>(
      `${this.basePath}/${teamNumber}`,
      { params }
    );
  }

  /**
   * Get multiple teams
   */
  async getTeams(teamNumbers: number[]): Promise<TeamResponse[]> {
    return await apiClient.post<TeamResponse[]>(
      `${this.basePath}/batch`,
      { team_numbers: teamNumbers }
    );
  }

  /**
   * Get team history
   */
  async getTeamHistory(
    teamNumber: number,
    limit = 10
  ): Promise<PaginatedResponse<any>> {
    const params: GetTeamHistoryRequest = {
      team_number: teamNumber,
      limit,
    };
    
    return await apiClient.get<PaginatedResponse<any>>(
      `${this.basePath}/${teamNumber}/history`,
      { params }
    );
  }

  /**
   * Search teams by name or number
   */
  async searchTeams(query: string, limit = 20): Promise<TeamResponse[]> {
    return await apiClient.get<TeamResponse[]>(
      `${this.basePath}/search`,
      {
        params: { q: query, limit },
      }
    );
  }

  /**
   * Get team statistics for an event
   */
  async getTeamStats(teamNumber: number, eventKey: string): Promise<Record<string, any>> {
    return await apiClient.get<Record<string, any>>(
      `${this.basePath}/${teamNumber}/stats/${eventKey}`
    );
  }

  /**
   * Get team awards
   */
  async getTeamAwards(teamNumber: number, year?: number): Promise<any[]> {
    const path = year
      ? `${this.basePath}/${teamNumber}/awards/${year}`
      : `${this.basePath}/${teamNumber}/awards`;
    
    return await apiClient.get<any[]>(path);
  }

  /**
   * Get team media
   */
  async getTeamMedia(teamNumber: number, year?: number): Promise<any[]> {
    const path = year
      ? `${this.basePath}/${teamNumber}/media/${year}`
      : `${this.basePath}/${teamNumber}/media`;
    
    return await apiClient.get<any[]>(path);
  }

  /**
   * Check if team exists
   */
  async teamExists(teamNumber: number): Promise<boolean> {
    try {
      await this.getTeam(teamNumber);
      return true;
    } catch (error: any) {
      if (error.status === 404) {
        return false;
      }
      throw error;
    }
  }
}

// Export singleton instance
export const teamService = new TeamService();