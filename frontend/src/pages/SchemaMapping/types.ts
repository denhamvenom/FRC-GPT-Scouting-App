// TypeScript definitions for SchemaMapping page

export interface SchemaMappingState {
  headers: string[];
  mapping: { [key: string]: string };
  suggestedVariables: string[];
  criticalMappings: { [key: string]: string | null };
  loading: boolean;
  error: string | null;
  validationMessage: string | null;
}

export interface CriticalFieldsConfig {
  team_number: string | null;
  match_number: string | null;
}

export interface SchemaResponse {
  status: string;
  headers: string[];
  mapping: { [key: string]: string };
  message?: string;
}

export interface VariablesResponse {
  status: string;
  suggested_variables?: string[];
  message?: string;
}

export const CRITICAL_FIELDS_LIST = ["team_number", "match_number", "qual_number"];

export const DEFAULT_CRITICAL_MAPPINGS: CriticalFieldsConfig = {
  team_number: null,
  match_number: null
};