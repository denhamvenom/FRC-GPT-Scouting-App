/**
 * Base API client with error handling, interceptors, and retry logic
 */

interface ApiConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
  timeout?: number;
  retry?: number;
}

interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

export class ApiClientError extends Error {
  status?: number;
  code?: string;
  details?: any;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiClientError';
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
  }
}

export class ApiClient {
  private baseURL: string;
  private timeout: number;
  private defaultHeaders: Record<string, string>;
  private requestInterceptors: Array<(config: RequestOptions) => RequestOptions | Promise<RequestOptions>> = [];
  private responseInterceptors: Array<(response: Response) => Response | Promise<Response>> = [];

  constructor(config: ApiConfig = {}) {
    this.baseURL = config.baseURL || '/api';
    this.timeout = config.timeout || 30000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
    
    // Debug logging
    console.debug('ApiClient initialized with baseURL:', this.baseURL);
  }

  /**
   * Add request interceptor
   */
  addRequestInterceptor(interceptor: (config: RequestOptions) => RequestOptions | Promise<RequestOptions>) {
    this.requestInterceptors.push(interceptor);
    return () => {
      const index = this.requestInterceptors.indexOf(interceptor);
      if (index >= 0) {
        this.requestInterceptors.splice(index, 1);
      }
    };
  }

  /**
   * Add response interceptor
   */
  addResponseInterceptor(interceptor: (response: Response) => Response | Promise<Response>) {
    this.responseInterceptors.push(interceptor);
    return () => {
      const index = this.responseInterceptors.indexOf(interceptor);
      if (index >= 0) {
        this.responseInterceptors.splice(index, 1);
      }
    };
  }

  /**
   * Build URL with query parameters
   */
  private buildURL(endpoint: string, params?: Record<string, any>): string {
    console.debug('Building URL with endpoint:', endpoint, 'baseURL:', this.baseURL);
    
    if (!this.baseURL) {
      throw new Error('ApiClient baseURL is not configured');
    }
    
    if (!endpoint) {
      throw new Error('API endpoint is required');
    }
    
    // Handle both absolute and relative base URLs
    let fullURL: string;
    try {
      if (this.baseURL.startsWith('http')) {
        // Absolute URL
        fullURL = `${this.baseURL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
      } else {
        // Relative URL - construct relative to current origin
        if (typeof window === 'undefined' || !window.location) {
          throw new Error('Cannot construct relative URL in non-browser environment');
        }
        const baseURL = `${window.location.origin}${this.baseURL.replace(/\/$/, '')}`;
        fullURL = `${baseURL}/${endpoint.replace(/^\//, '')}`;
      }
      
      console.debug('Built URL:', fullURL);
      
      if (params && Object.keys(params).length > 0) {
        try {
          const url = new URL(fullURL);
          Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
              url.searchParams.append(key, String(value));
            }
          });
          const finalURL = url.toString();
          console.debug('URL with params:', finalURL);
          return finalURL;
        } catch (urlError) {
          console.error('Error constructing URL with params:', urlError);
          throw new Error(`Invalid URL construction: ${fullURL}`);
        }
      }
      
      return fullURL;
    } catch (error) {
      console.error('Error building URL:', error);
      throw new Error(`Failed to build URL for endpoint: ${endpoint}`);
    }
  }

  /**
   * Apply request interceptors
   */
  private async applyRequestInterceptors(config: RequestOptions): Promise<RequestOptions> {
    let modifiedConfig = config;
    
    for (const interceptor of this.requestInterceptors) {
      modifiedConfig = await interceptor(modifiedConfig);
    }
    
    return modifiedConfig;
  }

  /**
   * Apply response interceptors
   */
  private async applyResponseInterceptors(response: Response): Promise<Response> {
    let modifiedResponse = response;
    
    for (const interceptor of this.responseInterceptors) {
      modifiedResponse = await interceptor(modifiedResponse);
    }
    
    return modifiedResponse;
  }

  /**
   * Handle API errors
   */
  private async handleError(response: Response): Promise<never> {
    let errorData: any;
    
    try {
      const text = await response.text();
      try {
        errorData = JSON.parse(text);
      } catch {
        // If not JSON, use the text as the message
        errorData = { message: text || response.statusText || 'Unknown error' };
      }
    } catch {
      errorData = { message: response.statusText || 'Unknown error' };
    }
    
    console.error('API Error Response:', {
      status: response.status,
      statusText: response.statusText,
      url: response.url,
      errorData
    });
    
    // Extract error message with better fallback logic
    let message = 'Request failed';
    if (typeof errorData === 'string') {
      message = errorData;
    } else if (errorData && typeof errorData === 'object') {
      message = errorData.detail || errorData.message || errorData.error || 
               (Array.isArray(errorData) ? errorData.join(', ') : 'Request failed');
    }
    
    const error: ApiError = {
      message: message,
      status: response.status,
      code: errorData?.code || errorData?.error_code,
      details: errorData,
    };
    
    throw new ApiClientError(error);
  }

  /**
   * Make HTTP request with retry logic
   */
  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, retry = 0, ...fetchOptions } = options;
    
    const url = this.buildURL(endpoint, params);
    
    // Don't set Content-Type for FormData - browser will set it with boundary
    const headers = { ...this.defaultHeaders, ...fetchOptions.headers };
    if (fetchOptions.body instanceof FormData) {
      delete headers['Content-Type'];
    }
    
    const config: RequestOptions = {
      ...fetchOptions,
      headers,
    };
    
    // Apply request interceptors
    const finalConfig = await this.applyRequestInterceptors(config);
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.timeout);
    
    try {
      const response = await fetch(url, {
        ...finalConfig,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      // Apply response interceptors
      const processedResponse = await this.applyResponseInterceptors(response);
      
      if (!processedResponse.ok) {
        await this.handleError(processedResponse);
      }
      
      // Handle empty responses
      if (processedResponse.status === 204 || processedResponse.headers.get('content-length') === '0') {
        return {} as T;
      }
      
      return await processedResponse.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      // Retry logic for network errors
      if (retry > 0 && error instanceof TypeError && error.message.includes('fetch')) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return this.request<T>(endpoint, { ...options, retry: retry - 1 });
      }
      
      // Re-throw ApiClientError as is
      if (error instanceof ApiClientError) {
        throw error;
      }
      
      // Handle abort errors
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiClientError({
          message: 'Request timeout',
          code: 'TIMEOUT',
        });
      }
      
      // Handle other errors
      throw new ApiClientError({
        message: error instanceof Error ? error.message : 'Unknown error',
        code: 'NETWORK_ERROR',
      });
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    // Don't stringify FormData or Blob
    let body: any;
    if (data instanceof FormData || data instanceof Blob) {
      body = data;
    } else if (data) {
      body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    // Don't stringify FormData or Blob
    let body: any;
    if (data instanceof FormData || data instanceof Blob) {
      body = data;
    } else if (data) {
      body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    // Don't stringify FormData or Blob
    let body: any;
    if (data instanceof FormData || data instanceof Blob) {
      body = data;
    } else if (data) {
      body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body,
    });
  }
}

// Default API client instance
export const apiClient = new ApiClient();