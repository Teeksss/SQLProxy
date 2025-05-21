/**
 * PowerBI Types
 * 
 * Type definitions for PowerBI integration functionality
 * 
 * Last updated: 2025-05-21 05:48:50
 * Updated by: Teeksss
 */

/**
 * PowerBI workspace
 */
export interface PowerBIWorkspace {
  id: number;
  workspace_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  reports_count?: number;
  datasets_count?: number;
}

/**
 * PowerBI report
 */
export interface PowerBIReport {
  id: number;
  report_id: string;
  name: string;
  description?: string;
  embed_url?: string;
  dataset_id?: string;
  workspace_id?: string;
  created_at: string;
  updated_at?: string;
  refresh_schedule?: string;
  last_refreshed_at?: string;
  last_refresh_status?: string;
}

/**
 * PowerBI dataset
 */
export interface PowerBIDataset {
  id: number;
  dataset_id: string;
  name: string;
  description?: string;
  workspace_id?: string;
  created_at: string;
  updated_at?: string;
  refresh_schedule?: string;
  last_refreshed_at?: string;
  last_refresh_status?: string;
}

/**
 * PowerBI embed token
 */
export interface PowerBIEmbedToken {
  token: string;
  token_id: string;
  expiration: string;
  embed_url: string;
}

/**
 * PowerBI workspaces response
 */
export interface PowerBIWorkspacesResponse {
  items: PowerBIWorkspace[];
  total: number;
}

/**
 * PowerBI reports response
 */
export interface PowerBIReportsResponse {
  items: PowerBIReport[];
  total: number;
}

/**
 * PowerBI datasets response
 */
export interface PowerBIDatasetsResponse {
  items: PowerBIDataset[];
  total: number;
}

/**
 * PowerBI column definition
 */
export interface PowerBITableColumn {
  name: string;
  data_type: string;
}

/**
 * PowerBI table definition
 */
export interface PowerBITable {
  name: string;
  columns: PowerBITableColumn[];
}

/**
 * PowerBI dataset creation parameters
 */
export interface PowerBIDatasetCreate {
  name: string;
  default_mode: string;
  tables: PowerBITable[];
}

/**
 * PowerBI report creation parameters
 */
export interface PowerBICreateReportParams {
  name: string;
  description?: string;
  workspace_id?: string;
  server_id: string;
  query_id?: string;
  query_text?: string;
}

// Son güncelleme: 2025-05-21 05:48:50
// Güncelleyen: Teeksss