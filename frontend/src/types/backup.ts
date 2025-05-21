/**
 * Backup Types
 * 
 * Type definitions for backup functionality
 * 
 * Last updated: 2025-05-21 05:21:55
 * Updated by: Teeksss
 */

export enum BackupType {
  FULL = 'full',
  INCREMENTAL = 'incremental'
}

export enum BackupStatus {
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

/**
 * Backup record as returned from the API
 */
export interface BackupRecord {
  backup_id: string;
  filename: string;
  backup_type: BackupType;
  description: string;
  size_bytes: number;
  storage_type: string;
  storage_path: string;
  status: BackupStatus;
  created_at: string;
  metadata?: Record<string, any>;
}

/**
 * Backup creation parameters
 */
export interface BackupCreateParams {
  backup_type: BackupType;
  description: string;
  include_queries: boolean;
}

/**
 * Backup list response from the API
 */
export interface BackupListResponse {
  items: BackupRecord[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Storage information
 */
export interface StorageInfo {
  storage_type: string;
  local_path?: string;
  cloud_info?: {
    bucket?: string;
    region?: string;
    container?: string;
  };
  local_size_bytes: number;
  local_size_human: string;
  file_count: number;
  retention_days: number;
}

// Son güncelleme: 2025-05-21 05:21:55
// Güncelleyen: Teeksss