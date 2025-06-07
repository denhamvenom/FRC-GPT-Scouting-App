// API Response Types for FRC GPT Scouting App

// Standard API Response Pattern
export interface APIResponse<T = any> {
  status: "success" | "error" | "warning" | "processing" | "not_found";
  message?: string;
  data?: T;
  [key: string]: any;
}

// HTTP Error Response
export interface APIError {
  detail: string;
  status_code: number;
  type?: string;
}

// Health Check Response
export interface HealthCheckResponse {
  status: "healthy" | "unhealthy";
  timestamp: string;
  version?: string;
  services?: Record<string, "up" | "down">;
}

// Progress Tracking Types
export interface ProgressInfo {
  operation_id: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress_percentage: number;
  current_step?: string;
  total_steps?: number;
  start_time: string;
  estimated_completion?: string;
  error_message?: string;
}

// Batch Processing Status
export interface BatchProcessingStatus {
  total_batches: number;
  current_batch: number;
  progress_percentage: number;
  processing_complete: boolean;
}

// Chat Message for Team Comparison
export interface ChatMessage {
  type: "question" | "answer";
  content: string;
  timestamp: string;
}

// Common API Request Headers
export interface APIHeaders {
  'Content-Type'?: string;
  'Authorization'?: string;
  'X-Request-ID'?: string;
}

// Pagination Response
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

// File Upload Response
export interface FileUploadResponse {
  status: "success" | "error";
  filename?: string;
  file_path?: string;
  file_size?: number;
  upload_id?: string;
  error_message?: string;
}

// Debug Log Entry
export interface LogEntry {
  timestamp: string;
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  message: string;
  module?: string;
  function?: string;
  line_number?: number;
  extra_data?: Record<string, any>;
}

// Manual Processing Response
export interface ManualProcessingResponse {
  status: "success" | "error" | "processing";
  manual_url?: string;
  parsed_sections?: string[];
  processing_id?: string;
  error_message?: string;
}