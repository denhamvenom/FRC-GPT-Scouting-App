// Database Model Types for FRC GPT Scouting App
// These types mirror the SQLAlchemy models in backend/app/database/models.py

import { BaseEntity } from './common';
import { PicklistData } from './picklist';

// Locked Picklist Database Model
export interface LockedPicklistModel extends BaseEntity {
  id: number;
  team_number: number;
  event_key: string;
  year: number;
  
  // JSON fields storing picklist data
  first_pick_data: PicklistData;
  second_pick_data: PicklistData;
  third_pick_data?: PicklistData; // Optional for games without third picks
  
  // Additional picklist metadata
  excluded_teams?: number[]; // List of teams excluded from consideration
  strategy_prompts?: Record<string, string>; // Original strategy prompts for each pick position
  
  // Timestamps
  created_at: string;
  updated_at?: string;
  
  // Relationships
  alliance_selections?: AllianceSelectionModel[];
}

// Alliance Selection Database Model
export interface AllianceSelectionModel extends BaseEntity {
  id: number;
  picklist_id?: number;
  event_key: string;
  year: number;
  
  // Status tracking
  is_completed: boolean;
  current_round: number; // Default: 1
  
  // Timestamps
  created_at: string;
  updated_at?: string;
  
  // Relationships
  picklist?: LockedPicklistModel;
  alliances?: AllianceModel[];
  team_statuses?: TeamSelectionStatusModel[];
}

// Alliance Database Model
export interface AllianceModel extends BaseEntity {
  id: number;
  selection_id: number;
  alliance_number: number; // 1-8 for the 8 alliances
  
  // Team numbers (0 means empty slot)
  captain_team_number: number; // Default: 0
  first_pick_team_number: number; // Default: 0
  second_pick_team_number: number; // Default: 0
  backup_team_number?: number; // Optional backup, default: 0
  
  // Timestamps
  created_at: string;
  updated_at?: string;
  
  // Relationships
  selection?: AllianceSelectionModel;
}

// Team Selection Status Database Model
export interface TeamSelectionStatusModel extends BaseEntity {
  id: number;
  selection_id: number;
  team_number: number;
  
  // Status flags
  is_captain: boolean; // Default: false
  is_picked: boolean; // Default: false
  has_declined: boolean; // Default: false
  round_eliminated?: number; // Round in which team was eliminated
  
  // Timestamps
  created_at: string;
  updated_at?: string;
  
  // Relationships
  selection?: AllianceSelectionModel;
}

// Archived Event Database Model
export interface ArchivedEventModel extends BaseEntity {
  id: number;
  name: string; // User-friendly name for the archive
  event_key: string;
  year: number;
  
  // Archive data
  archive_data?: Uint8Array; // Binary data (SQLite BLOB)
  archive_metadata: ArchiveMetadata; // JSON metadata about the archive
  
  // Archive status
  is_active: boolean; // Whether this is the currently active archive
  
  // Timestamps
  created_at: string;
  created_by?: string; // User who created the archive
  notes?: string; // Optional notes about the archive
  
  // Computed property
  formatted_date: string; // Formatted date string for display
}

// Archive Metadata Structure
export interface ArchiveMetadata {
  tables: string[];
  record_counts: Record<string, number>;
  data_sources: string[];
  archive_size_bytes: number;
  compression_ratio?: number;
  archive_version: string;
  included_data_types: string[];
  export_timestamp: string;
  integrity_checksum?: string;
}

// Game Manual Database Model
export interface GameManualModel extends BaseEntity {
  id: number;
  year: number;
  original_filename: string;
  sanitized_filename_base: string; // For easier lookups
  
  // Paths to stored files
  stored_pdf_path?: string; // Should ideally not be null after initial processing
  toc_json_path?: string;
  parsed_sections_path?: string; // Populated after section parsing
  
  // Timestamps
  upload_timestamp: string;
  last_accessed_timestamp?: string;
}

// Sheet Configuration Database Model
export interface SheetConfigurationModel extends BaseEntity {
  id: number;
  name: string; // User-friendly name for this configuration
  spreadsheet_id: string; // Google Sheets ID
  
  // Sheet names for different data types (tab names in the spreadsheet)
  match_scouting_sheet: string;
  pit_scouting_sheet?: string;
  super_scouting_sheet?: string;
  
  // Event association
  event_key: string;
  year: number;
  
  // Status and timestamps
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  
  // Cache for sheet headers (to avoid repeated API calls)
  match_scouting_headers?: string[];
  pit_scouting_headers?: string[];
  super_scouting_headers?: string[];
  
  // Computed property
  formatted_date: string; // Formatted date string for display
}

// Database Query Options
export interface DatabaseQueryOptions {
  include_relationships?: string[];
  order_by?: string;
  order_direction?: "asc" | "desc";
  limit?: number;
  offset?: number;
  filters?: Record<string, any>;
}

// Database Transaction Context
export interface DatabaseTransaction {
  id: string;
  started_at: string;
  operations: DatabaseOperation[];
  status: "active" | "committed" | "rolled_back" | "failed";
}

export interface DatabaseOperation {
  operation_type: "create" | "update" | "delete" | "select";
  table_name: string;
  entity_id?: number | string;
  changes?: Record<string, any>;
  timestamp: string;
}

// Database Migration Types
export interface DatabaseMigration {
  version: string;
  name: string;
  description: string;
  sql_up: string[];
  sql_down: string[];
  applied_at?: string;
  checksum: string;
}

export interface MigrationStatus {
  current_version: string;
  available_migrations: DatabaseMigration[];
  pending_migrations: DatabaseMigration[];
  applied_migrations: DatabaseMigration[];
  needs_migration: boolean;
}

// Database Health Check
export interface DatabaseHealth {
  status: "healthy" | "degraded" | "unhealthy";
  connection_status: boolean;
  response_time_ms: number;
  active_connections: number;
  max_connections: number;
  disk_usage_mb: number;
  last_backup?: string;
  issues: string[];
}

// Data Validation Types for Database Models
export interface ModelValidationRule {
  field: string;
  rule_type: "required" | "unique" | "foreign_key" | "range" | "format" | "custom";
  parameters?: any;
  error_message: string;
}

export interface ModelValidationResult {
  is_valid: boolean;
  errors: Array<{
    field: string;
    message: string;
    value: any;
  }>;
  warnings: Array<{
    field: string;
    message: string;
    value: any;
  }>;
}

// Database Backup Types
export interface DatabaseBackup {
  id: string;
  created_at: string;
  backup_type: "full" | "incremental" | "schema_only" | "data_only";
  file_path: string;
  file_size_bytes: number;
  compression_type?: "gzip" | "lz4" | "none";
  tables_included: string[];
  record_counts: Record<string, number>;
  checksum: string;
  retention_period_days: number;
  expires_at: string;
}

export interface BackupRestoreOptions {
  backup_id: string;
  target_database?: string;
  tables_to_restore?: string[];
  overwrite_existing: boolean;
  restore_data: boolean;
  restore_schema: boolean;
  dry_run: boolean;
}

// Repository Pattern Types
export interface Repository<T extends BaseEntity> {
  find_by_id(id: number | string): Promise<T | null>;
  find_all(options?: DatabaseQueryOptions): Promise<T[]>;
  create(data: Omit<T, keyof BaseEntity>): Promise<T>;
  update(id: number | string, data: Partial<T>): Promise<T>;
  delete(id: number | string): Promise<boolean>;
  count(filters?: Record<string, any>): Promise<number>;
}

// Unit of Work Pattern
export interface UnitOfWork {
  locked_picklists: Repository<LockedPicklistModel>;
  alliance_selections: Repository<AllianceSelectionModel>;
  alliances: Repository<AllianceModel>;
  team_selection_statuses: Repository<TeamSelectionStatusModel>;
  archived_events: Repository<ArchivedEventModel>;
  game_manuals: Repository<GameManualModel>;
  sheet_configurations: Repository<SheetConfigurationModel>;
  
  begin_transaction(): Promise<void>;
  commit(): Promise<void>;
  rollback(): Promise<void>;
  is_in_transaction(): boolean;
}