import { useState, useEffect } from 'react';

// TypeScript interfaces for field metadata structure
export interface FieldLabelMapping {
  label: string;
  category: string;
  description: string;
  data_type: string;
  typical_range: string;
  usage_context: string;
}

export interface FieldSelection {
  category: string;
  source: string;
  label_mapping?: FieldLabelMapping;
}

export interface FieldMetadata {
  year: number;
  event_key: string;
  field_selections: {
    [fieldName: string]: FieldSelection;
  };
  critical_mappings: {
    [key: string]: string[];
  };
  robot_groups: {
    [key: string]: string[];
  };
  manual_url: string | null;
}

export interface ProcessedMetric {
  field_name: string;
  display_label: string;
  category: string;
  description: string;
  data_type: string;
  typical_range: string;
  usage_context: string;
}

export interface MetricsByCategory {
  [category: string]: ProcessedMetric[];
}

export interface UseFieldMetadataReturn {
  fieldMetadata: FieldMetadata | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  getNumericMetrics: () => ProcessedMetric[];
  getMetricsByCategory: () => MetricsByCategory;
  getMetricLabel: (fieldName: string) => string;
  getMetricCategory: (fieldName: string) => string;
}

// Helper function to get API base URL
const getApiBaseUrl = (): string => {
  // Check if we're in development and have a config
  if (typeof window !== 'undefined' && (window as any).APP_CONFIG?.apiBaseUrl) {
    return (window as any).APP_CONFIG.apiBaseUrl;
  }
  
  // Default to localhost for development
  return 'http://localhost:8000';
};

// Helper function to make API requests with proper headers
const fetchWithHeaders = async (url: string): Promise<Response> => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add ngrok headers if in development
  if (process.env.NODE_ENV === 'development') {
    headers['ngrok-skip-browser-warning'] = 'true';
  }

  return fetch(url, {
    method: 'GET',
    headers,
  });
};

export const useFieldMetadata = (eventKey?: string): UseFieldMetadataReturn => {
  const [fieldMetadata, setFieldMetadata] = useState<FieldMetadata | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFieldMetadata = async (targetEventKey?: string) => {
    setLoading(true);
    setError(null);

    try {
      const baseUrl = getApiBaseUrl();
      let url = `${baseUrl}/api/schema/field-metadata`;
      
      // Add event_key parameter if provided
      if (targetEventKey) {
        url += `?event_key=${encodeURIComponent(targetEventKey)}`;
      }

      console.log('Fetching field metadata from:', url);
      
      const response = await fetchWithHeaders(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: FieldMetadata = await response.json();
      
      // Validate the response structure
      if (!result.field_selections) {
        throw new Error('Invalid field metadata response structure');
      }

      setFieldMetadata(result);
      console.log('Field metadata loaded successfully:', {
        event_key: result.event_key,
        year: result.year,
        field_count: Object.keys(result.field_selections).length
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Failed to load field metadata: ${errorMessage}`);
      console.error('Error fetching field metadata:', err);
    } finally {
      setLoading(false);
    }
  };

  const refetch = () => {
    fetchFieldMetadata(eventKey);
  };

  // Get only numeric metrics that are suitable for radar charts
  const getNumericMetrics = (): ProcessedMetric[] => {
    if (!fieldMetadata) return [];

    const numericMetrics: ProcessedMetric[] = [];
    
    Object.entries(fieldMetadata.field_selections).forEach(([fieldName, selection]) => {
      // Only include fields with label_mapping and numeric data_type
      if (selection.label_mapping && 
          selection.label_mapping.data_type === 'count' &&
          selection.category !== 'ignore' &&
          selection.category !== 'team_number' &&
          selection.category !== 'match_number') {
        
        numericMetrics.push({
          field_name: selection.label_mapping.label,
          display_label: selection.label_mapping.label.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          category: selection.label_mapping.category,
          description: selection.label_mapping.description,
          data_type: selection.label_mapping.data_type,
          typical_range: selection.label_mapping.typical_range,
          usage_context: selection.label_mapping.usage_context
        });
      }
    });

    return numericMetrics;
  };

  // Group metrics by category
  const getMetricsByCategory = (): MetricsByCategory => {
    const metrics = getNumericMetrics();
    const groupedMetrics: MetricsByCategory = {};

    metrics.forEach(metric => {
      if (!groupedMetrics[metric.category]) {
        groupedMetrics[metric.category] = [];
      }
      groupedMetrics[metric.category].push(metric);
    });

    return groupedMetrics;
  };

  // Get display label for a field
  const getMetricLabel = (fieldName: string): string => {
    if (!fieldMetadata) return fieldName;

    // Search through field_selections to find the matching label_mapping
    for (const selection of Object.values(fieldMetadata.field_selections)) {
      if (selection.label_mapping && selection.label_mapping.label === fieldName) {
        return selection.label_mapping.label.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      }
    }

    // Fallback to formatted field name
    return fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Get category for a field
  const getMetricCategory = (fieldName: string): string => {
    if (!fieldMetadata) return 'unknown';

    // Search through field_selections to find the matching category
    for (const selection of Object.values(fieldMetadata.field_selections)) {
      if (selection.label_mapping && selection.label_mapping.label === fieldName) {
        return selection.label_mapping.category;
      }
    }

    return 'unknown';
  };

  // Fetch data on mount and when eventKey changes
  useEffect(() => {
    fetchFieldMetadata(eventKey);
  }, [eventKey]);

  return {
    fieldMetadata,
    loading,
    error,
    refetch,
    getNumericMetrics,
    getMetricsByCategory,
    getMetricLabel,
    getMetricCategory
  };
};

export default useFieldMetadata;