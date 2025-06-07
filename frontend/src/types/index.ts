// Type Exports for FRC GPT Scouting App
// This file centralizes all type definitions for easy importing

// API Response Types
export * from './api';
export type {
  APIResponse,
  APIError,
  HealthCheckResponse,
  ProgressInfo,
  BatchProcessingStatus,
  ChatMessage,
  APIHeaders,
  PaginatedResponse,
  FileUploadResponse,
  LogEntry,
  ManualProcessingResponse,
} from './api';

// Team-related Types
export * from './team';
export type {
  Team,
  TeamSelectionStatus,
  UserRanking,
  TeamActionRequest,
  CompareTeamsRequest,
  TeamComparisonResponse,
  TeamSummary,
  MetricPriority,
  TeamStatistics,
  TeamPerformanceMetrics,
  TeamMatchData,
  TeamAvailabilityStatus,
  TeamSearchParams,
  TeamFilterOptions,
  TeamEventParticipation,
  TeamListResponse,
  TeamResponse,
  TeamComparisonApiResponse,
  TeamStatisticsResponse,
  TeamPerformanceResponse,
  TeamActionResponse,
} from './team';

// Alliance-related Types
export * from './alliance';
export type {
  Alliance,
  AllianceSelection,
  AllianceSelectionConfig,
  AllianceDraftRules,
  AllianceSelectionState,
  AlliancePerformance,
  AllianceComplementarity,
  AllianceActionType,
  AllianceAction,
  AllianceSelectionHistory,
  AllianceSelectionSnapshot,
  AllianceTimelineEvent,
  CreateAllianceSelectionRequest,
  UpdateAllianceSelectionRequest,
  AllianceActionRequest,
  SimulateAllianceSelectionRequest,
  AllianceSelectionResponse,
  AllianceSelectionListResponse,
  AlliancePerformanceResponse,
  AllianceActionResponse,
  AllianceSimulationResponse,
  AllianceSimulationResult,
  AllianceStatistics,
  AllianceStrategy,
  AllianceDraftPrediction,
} from './alliance';

// Picklist-related Types
export * from './picklist';
export type {
  PicklistData,
  PicklistMetadata,
  LockedPicklist,
  PicklistRequest,
  PicklistGenerationStatus,
  UpdatePicklistRequest,
  RankMissingTeamsRequest,
  LockPicklistRequest,
  PicklistAnalysisResponse,
  GameMetric,
  AnalysisMetadata,
  PicklistConfiguration,
  PicklistExportOptions,
  PicklistComparison,
  PicklistHistory,
  PicklistResponse,
  PicklistAnalysisApiResponse,
  PicklistGenerationStatusResponse,
  LockedPicklistResponse,
  LockedPicklistListResponse,
  PicklistComparisonResponse,
  PicklistHistoryResponse,
  PicklistSearchParams,
  PicklistFilterOptions,
  PicklistValidationResult,
  PicklistValidationError,
  PicklistValidationWarning,
  PicklistOptimizationRequest,
  PicklistOptimizationResult,
} from './picklist';

// Event-related Types
export * from './event';
export type {
  FRCEvent,
  EventConfiguration,
  ValidationRules,
  CustomValidationRule,
  EventSetupInfo,
  SheetConfiguration,
  EventDataStatistics,
  ArchivedEvent,
  ArchiveMetadata,
  EventMatch,
  EventAlliance,
  EventRankings,
  CreateSheetConfigRequest,
  UpdateSheetConfigRequest,
  TestConnectionRequest,
  CreateArchiveRequest,
  RestoreArchiveRequest,
  FRCEventResponse,
  FRCEventListResponse,
  EventSetupInfoResponse,
  SheetConfigurationResponse,
  SheetConfigurationListResponse,
  EventDataStatisticsResponse,
  ArchivedEventResponse,
  ArchivedEventListResponse,
  EventMatchResponse,
  EventRankingsResponse,
  TestConnectionResponse,
  EventSearchParams,
  EventFilterOptions,
  EventStatus,
  EventPhase,
  EventWorkflow,
  EventPerformanceSummary,
} from './event';

// Common/Shared Types
export * from './common';
export type {
  Status,
  ProcessingStatus,
  ValidationStatus,
  SeverityLevel,
  LogLevel,
  Timestamps,
  PaginationParams,
  PaginationInfo,
  PaginatedData,
  SortOptions,
  SortableColumn,
  FilterOptions,
  DateRange,
  SelectionOption,
  MultiSelectOptions,
  FormField,
  FormFieldType,
  ValidationRule,
  FormError,
  ExportOptions,
  ExportProgress,
  SearchParams,
  SearchResult,
  SearchResponse,
  CacheOptions,
  CacheInfo,
  Notification,
  NotificationAction,
  ThemeConfig,
  ViewportSize,
  PerformanceMetrics,
  ConfigurationValue,
  FileInfo,
  UploadedFile,
  BaseEntity,
  AuditableEntity,
  AuditLogEntry,
  APIClientConfig,
  RequestOptions,
  ApplicationError,
  ValidationError,
  FeatureFlag,
  AnalyticsEvent,
  Optional,
  RequiredBy,
  DeepPartial,
  NonNullable,
  BaseComponentProps,
  LoadingProps,
  DisabledProps,
  ErrorProps,
} from './common';

// Database Model Types
export * from './database';
export type {
  LockedPicklistModel,
  AllianceSelectionModel,
  AllianceModel,
  TeamSelectionStatusModel,
  ArchivedEventModel,
  GameManualModel,
  SheetConfigurationModel,
  DatabaseQueryOptions,
  DatabaseTransaction,
  DatabaseOperation,
  DatabaseMigration,
  MigrationStatus,
  DatabaseHealth,
  ModelValidationRule,
  ModelValidationResult,
  DatabaseBackup,
  BackupRestoreOptions,
  Repository,
  UnitOfWork,
} from './database';

// Additional type utility exports for convenience
export type {
  // React-related utilities
  ComponentProps,
  ReactNode,
  ReactElement,
  CSSProperties,
} from 'react';

// Form-related type unions
export type FormStatus = "idle" | "validating" | "submitting" | "success" | "error";
export type LoadingState = "idle" | "loading" | "success" | "error";
export type NetworkStatus = "online" | "offline" | "slow";

// Common ID types
export type ID = string | number;
export type TeamNumber = number;
export type EventKey = string;
export type Year = number;

// Validation result union type
export type ValidationResultType = "valid" | "invalid" | "pending";

// Common response status union
export type ResponseStatus = "success" | "error" | "loading" | "idle";

// Pick position union for type safety
export type PickPosition = "first" | "second" | "third";

// Alliance color union for type safety  
export type AllianceColor = "red" | "blue";

// Match type union
export type MatchType = "qualification" | "playoff" | "practice";

// Event type union
export type EventType = "regional" | "district" | "championship" | "offseason" | "preseason";

// Data source union
export type DataSource = "sheets" | "tba" | "statbotics" | "manual" | "cache";

// Sort direction union
export type SortDirection = "asc" | "desc";

// Theme mode union
export type ThemeMode = "light" | "dark" | "auto";

// Screen size union
export type ScreenSize = "mobile" | "tablet" | "desktop" | "ultrawide";

// Export format union
export type ExportFormat = "json" | "csv" | "excel" | "pdf";

// Environment union
export type Environment = "development" | "staging" | "production";

// Re-export commonly used React types for convenience
export type { FC, ReactNode, ReactElement, CSSProperties, RefObject } from 'react';