/**
 * Data Validation API Service
 */

import { apiClient } from './ApiClient';
import {
  ValidationRequest,
  CorrectValidationRequest,
  VirtualScoutRequest,
  ValidationResponse,
  ValidationPreviewResponse,
  SuccessResponse,
} from './types';

export class ValidationService {
  private basePath = '/validate';

  /**
   * Validate dataset
   */
  async validateDataset(data: ValidationRequest): Promise<ValidationResponse> {
    return await apiClient.post<ValidationResponse>(
      `${this.basePath}/enhanced`,
      data
    );
  }

  /**
   * Get validation todo list
   */
  async getTodoList(unifiedDatasetPath: string): Promise<ValidationResponse['todos']> {
    return await apiClient.get<ValidationResponse['todos']>(
      `${this.basePath}/todo`,
      {
        params: { unified_dataset_path: unifiedDatasetPath },
      }
    );
  }

  /**
   * Apply corrections to dataset
   */
  async applyCorrections(data: CorrectValidationRequest): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.basePath}/correct`,
      data
    );
  }

  /**
   * Preview virtual scouting
   */
  async previewVirtualScouting(
    unifiedDatasetPath: string
  ): Promise<ValidationPreviewResponse> {
    return await apiClient.get<ValidationPreviewResponse>(
      `${this.basePath}/preview-virtual-scout`,
      {
        params: { unified_dataset_path: unifiedDatasetPath },
      }
    );
  }

  /**
   * Apply virtual scouting
   */
  async applyVirtualScouting(data: VirtualScoutRequest): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.basePath}/virtual-scout`,
      data
    );
  }

  /**
   * Get validation statistics
   */
  async getValidationStats(eventKey: string): Promise<any> {
    return await apiClient.get<any>(
      `${this.basePath}/stats/${eventKey}`
    );
  }

  /**
   * Export validation report
   */
  async exportValidationReport(
    eventKey: string,
    format: 'json' | 'csv' = 'json'
  ): Promise<Blob> {
    const response = await apiClient.get<any>(
      `${this.basePath}/export/${eventKey}`,
      {
        params: { format },
        headers: {
          'Accept': format === 'csv' ? 'text/csv' : 'application/json',
        },
      }
    );
    
    if (format === 'csv') {
      return new Blob([response], { type: 'text/csv' });
    }
    
    return new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' });
  }

  /**
   * Get validation history
   */
  async getValidationHistory(eventKey: string, limit = 10): Promise<any[]> {
    return await apiClient.get<any[]>(
      `${this.basePath}/history/${eventKey}`,
      {
        params: { limit },
      }
    );
  }

  /**
   * Clear validation cache
   */
  async clearCache(): Promise<SuccessResponse> {
    return await apiClient.post<SuccessResponse>(
      `${this.basePath}/clear-cache`
    );
  }

  /**
   * Get field statistics
   */
  async getFieldStats(
    unifiedDatasetPath: string,
    fieldName: string
  ): Promise<any> {
    return await apiClient.get<any>(
      `${this.basePath}/field-stats`,
      {
        params: {
          unified_dataset_path: unifiedDatasetPath,
          field: fieldName,
        },
      }
    );
  }
}

// Export singleton instance
export const validationService = new ValidationService();