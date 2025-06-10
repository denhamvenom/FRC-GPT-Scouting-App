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
    const url = new URL(endpoint, this.baseURL);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    return url.toString();
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
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText || 'Unknown error' };
    }
    
    const error: ApiError = {
      message: errorData.detail || errorData.message || 'Request failed',
      status: response.status,
      code: errorData.code,
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
    const config: RequestOptions = {
      ...fetchOptions,
      headers: {
        ...this.defaultHeaders,
        ...fetchOptions.headers,
      },
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
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
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
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

// Default API client instance
export const apiClient = new ApiClient();