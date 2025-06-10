/**
 * Dataset Building API Service
 */

import { apiClient } from './ApiClient';
import {
  BuildDatasetRequest,
  DatasetStatusRequest,
  DatasetBuildResponse,
  DatasetStatusResponse,
  SuccessResponse,
} from './types';

export class DatasetService {
  private basePath = '/dataset';

  /**
   * Build unified dataset
   */
  async buildDataset(data: BuildDatasetRequest): Promise<DatasetBuildResponse> {
    return await apiClient.post<DatasetBuildResponse>(
      `${this.basePath}/build`,
      data,
      {
        timeout: 60000, // 60 second timeout for dataset building
      }
    );
  }

  /**
   * Get dataset status
   */
  async getDatasetStatus(eventKey: string): Promise<DatasetStatusResponse> {
    return await apiClient.get<DatasetStatusResponse>(
      `${this.basePath}/status/${eventKey}`
    );
  }

  /**
   * Download dataset
   */
  async downloadDataset(eventKey: string): Promise<Blob> {
    const response = await apiClient.get<any>(
      `${this.basePath}/download/${eventKey}`,
      {
        headers: {
          'Accept': 'application/json',
        },
      }
    );
    
    return new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
  }

  /**
   * Refresh dataset
   */
  async refreshDataset(eventKey: string): Promise<DatasetBuildResponse> {
    return await apiClient.post<DatasetBuildResponse>(
      `${this.basePath}/refresh/${eventKey}`
    );
  }

  /**
   * Delete dataset
   */
  async deleteDataset(eventKey: string): Promise<SuccessResponse> {
    return await apiClient.delete<SuccessResponse>(
      `${this.basePath}/${eventKey}`
    );
  }

  /**
   * Get dataset preview
   */
  async getDatasetPreview(
    eventKey: string,
    limit = 10
  ): Promise<any> {
    return await apiClient.get<any>(
      `${this.basePath}/preview/${eventKey}`,
      {
        params: { limit },
      }
    );
  }

  /**
   * Get dataset fields
   */
  async getDatasetFields(eventKey: string): Promise<string[]> {
    return await apiClient.get<string[]>(
      `${this.basePath}/fields/${eventKey}`
    );
  }

  /**
   * Get dataset statistics
   */
  async getDatasetStats(eventKey: string): Promise<any> {
    return await apiClient.get<any>(
      `${this.basePath}/stats/${eventKey}`
    );
  }

  /**
   * Clear dataset cache
   */
  async clearCache(): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.basePath}/clear-cache`
    );
  }

  /**
   * Validate dataset integrity
   */
  async validateDataset(eventKey: string): Promise<any> {
    return await apiClient.post<any>(
      `${this.basePath}/validate/${eventKey}`
    );
  }
}

// Export singleton instance
export const datasetService = new DatasetService();