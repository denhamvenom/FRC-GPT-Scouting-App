// Common/Shared Types for FRC GPT Scouting App

// Generic Status Types
export type Status = "success" | "error" | "warning" | "info" | "loading" | "idle";
export type ProcessingStatus = "pending" | "in_progress" | "completed" | "failed" | "cancelled";
export type ValidationStatus = "valid" | "invalid" | "warning" | "unknown";

// Severity Levels
export type SeverityLevel = "low" | "medium" | "high" | "critical";
export type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

// Common Timestamps
export interface Timestamps {
  created_at: string;
  updated_at?: string;
  deleted_at?: string;
}

// Pagination Types
export interface PaginationParams {
  page?: number;
  per_page?: number;
  limit?: number;
  offset?: number;
}

export interface PaginationInfo {
  current_page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
  next_page?: number;
  previous_page?: number;
}

export interface PaginatedData<T> {
  data: T[];
  pagination: PaginationInfo;
}

// Sorting Types
export interface SortOptions {
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface SortableColumn {
  key: string;
  label: string;
  sortable: boolean;
  default_order?: "asc" | "desc";
}

// Filter Types
export interface FilterOptions {
  filters?: Record<string, any>;
  search?: string;
  date_range?: DateRange;
  include_inactive?: boolean;
}

export interface DateRange {
  start_date?: string;
  end_date?: string;
}

// Selection Types
export interface SelectionOption<T = any> {
  value: T;
  label: string;
  disabled?: boolean;
  group?: string;
  description?: string;
}

export interface MultiSelectOptions {
  allow_multiple: boolean;
  max_selections?: number;
  min_selections?: number;
  select_all_option?: boolean;
}

// Form Field Types
export interface FormField {
  name: string;
  label: string;
  type: FormFieldType;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  description?: string;
  validation_rules?: ValidationRule[];
  default_value?: any;
  options?: SelectionOption[];
}

export type FormFieldType = 
  | "text" 
  | "number" 
  | "email" 
  | "password" 
  | "textarea" 
  | "select" 
  | "multiselect" 
  | "checkbox" 
  | "radio" 
  | "date" 
  | "datetime" 
  | "file" 
  | "hidden";

export interface ValidationRule {
  type: "required" | "min" | "max" | "minLength" | "maxLength" | "pattern" | "custom";
  value?: any;
  message: string;
  validator?: (value: any) => boolean;
}

export interface FormError {
  field: string;
  message: string;
  type: string;
}

// Data Export Types
export interface ExportOptions {
  format: "json" | "csv" | "excel" | "pdf";
  filename?: string;
  include_metadata?: boolean;
  date_format?: string;
  delimiter?: string; // for CSV
  encoding?: string;
}

export interface ExportProgress {
  status: "preparing" | "exporting" | "completed" | "error";
  progress_percentage: number;
  estimated_time_remaining?: number;
  download_url?: string;
  error_message?: string;
}

// Search Types
export interface SearchParams {
  query: string;
  fields?: string[];
  exact_match?: boolean;
  case_sensitive?: boolean;
  max_results?: number;
}

export interface SearchResult<T> {
  item: T;
  score: number;
  matched_fields: string[];
  highlights?: Record<string, string>;
}

export interface SearchResponse<T> {
  results: SearchResult<T>[];
  total_results: number;
  search_time_ms: number;
  query: string;
  suggestions?: string[];
}

// Cache Types
export interface CacheOptions {
  ttl?: number; // Time to live in seconds
  refresh_on_access?: boolean;
  background_refresh?: boolean;
  compression?: boolean;
}

export interface CacheInfo {
  key: string;
  created_at: string;
  expires_at?: string;
  last_accessed?: string;
  hit_count: number;
  size_bytes?: number;
}

// Notification Types
export interface Notification {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  auto_dismiss?: boolean;
  dismiss_timeout?: number; // milliseconds
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: "dismiss" | "navigate" | "execute" | "download";
  target?: string;
  handler?: () => void;
}

// Theme and UI Types
export interface ThemeConfig {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  typography: {
    font_family: string;
    font_sizes: Record<string, string>;
    font_weights: Record<string, number>;
  };
  spacing: Record<string, string>;
  breakpoints: Record<string, string>;
}

export interface ViewportSize {
  width: number;
  height: number;
  is_mobile: boolean;
  is_tablet: boolean;
  is_desktop: boolean;
}

// Performance Monitoring
export interface PerformanceMetrics {
  operation_name: string;
  start_time: number;
  end_time: number;
  duration_ms: number;
  memory_usage?: number;
  success: boolean;
  error_message?: string;
  metadata?: Record<string, any>;
}

// Configuration Types
export interface ConfigurationValue {
  key: string;
  value: any;
  type: "string" | "number" | "boolean" | "object" | "array";
  description?: string;
  required: boolean;
  default_value?: any;
  validation_pattern?: string;
  environment?: "development" | "staging" | "production" | "all";
}

// File Types
export interface FileInfo {
  name: string;
  size: number;
  type: string;
  last_modified: string;
  path: string;
  url?: string;
  checksum?: string;
}

export interface UploadedFile extends FileInfo {
  upload_id: string;
  upload_status: "uploading" | "completed" | "failed";
  upload_progress?: number;
  error_message?: string;
}

// Generic Entity Types
export interface BaseEntity {
  id: number | string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
  version?: number;
}

export interface AuditableEntity extends BaseEntity {
  audit_log: AuditLogEntry[];
}

export interface AuditLogEntry {
  timestamp: string;
  action: "created" | "updated" | "deleted" | "viewed" | "exported";
  user: string;
  changes?: Record<string, { old_value: any; new_value: any }>;
  metadata?: Record<string, any>;
}

// API Client Types
export interface APIClientConfig {
  base_url: string;
  timeout: number;
  retry_attempts: number;
  retry_delay: number;
  headers: Record<string, string>;
  auth_token?: string;
}

export interface RequestOptions {
  timeout?: number;
  retry?: boolean;
  cache?: boolean;
  background?: boolean;
  signal?: AbortSignal;
}

// Error Types
export interface ApplicationError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  request_id?: string;
  user_message?: string;
  recoverable: boolean;
  retry_after?: number;
}

export interface ValidationError extends ApplicationError {
  field_errors: Record<string, string[]>;
  form_errors: string[];
}

// Feature Flag Types
export interface FeatureFlag {
  name: string;
  enabled: boolean;
  description?: string;
  rollout_percentage?: number;
  target_users?: string[];
  target_environments?: string[];
  expiry_date?: string;
}

// Analytics Types
export interface AnalyticsEvent {
  event_name: string;
  timestamp: string;
  user_id?: string;
  session_id?: string;
  properties: Record<string, any>;
  context: {
    page: string;
    referrer?: string;
    user_agent: string;
    viewport: ViewportSize;
  };
}

// Utility Types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
export type NonNullable<T> = T extends null | undefined ? never : T;

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  style?: React.CSSProperties;
  id?: string;
  testId?: string;
  'aria-label'?: string;
  'aria-describedby'?: string;
}

export interface LoadingProps {
  loading?: boolean;
  loadingText?: string;
  showSpinner?: boolean;
}

export interface DisabledProps {
  disabled?: boolean;
  disabledReason?: string;
}

export interface ErrorProps {
  error?: string | Error | null;
  onErrorRetry?: () => void;
  showErrorDetails?: boolean;
}