/**
 * Backup Service
 * 
 * Service for interacting with backup APIs
 * 
 * Last updated: 2025-05-21 05:21:55
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';
import { 
  BackupRecord, 
  BackupType, 
  BackupListResponse, 
  BackupCreateParams,
  StorageInfo 
} from '../types/backup';

export const backupApi = {
  /**
   * Create a new backup
   * 
   * @param params Backup creation parameters
   * @returns Promise with backup data
   */
  createBackup: async (params: BackupCreateParams) => {
    try {
      const response = await api.post('/backups', params);
      return response.data;
    } catch (error) {
      throw handleBackupApiError(error);
    }
  },

  /**
   * Get list of backups with pagination
   * 
   * @param options Pagination and filter options
   * @returns Promise with backup list data
   */
  getBackups: async (options?: {
    page?: number;
    limit?: number;
    backupType?: string;
  }): Promise<BackupListResponse> => {
    try {
      const params = new URLSearchParams();
      
      if (options?.page) params.append('page', options.page.toString());
      if (options?.limit) params.append('limit', options.limit.toString());
      if (options?.backupType) params.append('backup_type', options.backupType);
      
      const response = await api.get(`/backups?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw handleBackupApiError(error);
    }
  },

  /**
   * Get backup details by ID
   * 
   * @param backupId Backup ID
   * @returns Promise with backup details
   */
  getBackupDetails: async (backupId: string): Promise<BackupRecord> => {
    try {
      const response = await api.get(`/backups/${backupId}`);
      return response.data;
    } catch (error) {
      throw handleBackupApiError(error);
    }
  },

  /**
   * Restore a backup
   * 
   * @param backupId Backup ID
   * @returns Promise with response data
   */
  restoreBackup: async (backupId: string) => {
    try {
      const response = await api.post(`/backups/${backupId}/restore`);
      return response.data;
    } catch (error) {
      throw handleBackupApiError(error);
    }
  },

  /**
   * Delete a backup
   * 
   * @param backupId Backup ID
   * @returns Promise with response data
   */
  deleteBackup: async (backupId: string) => {
    try {
      const response = await api.delete(`/backups/${backupId}`);
      return response.data;
    } catch (error) {
      throw handleBackupApiError(error);
    }
  },

  /**
   * Download a backup
   * 
   * @param backupId Backup ID
   */
  downloadBackup: async (backupId: string) => {
    try {
      const response = await api.get(`/backups/${backupId}/download`, {
        responseType: 'blob'
      });
      
      // Create a download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from Content-Disposition header if available
      const contentDisposition = response.headers['content-disposition'];
      let filename = `backup_${backupId}.tar.gz`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      throw handleBackupApiError(error);
    }
  },

  /**
   * Clean up old backups
   * 
   * @param retentionDays Number of days to retain backups
   * @returns Promise with response data
   */
  cleanupBackups: async (retentionDays?: number) => {
    try {
      const params = new URLSearchParams();
      if (retentionDays) params.append('retention_days', retentionDays.toString());
      
      const response = await api.post(`/backups/cleanup?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw handleBackupApiError(error);
    }
  },

  /**
   * Get storage information
   * 
   * @returns Promise with storage information
   */
  getStorageInfo: async (): Promise<StorageInfo> => {
    try {
      const response = await api.get('/backups/storage/info');
      return response.data;
    } catch (error) {
      throw handleBackupApiError(error);
    }
  }
};

/**
 * Handle API errors
 * 
 * @param error Error from API
 */
function handleBackupApiError(error: any) {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || error.message;
    return new Error(message);
  }
  return error;
}

// Son güncelleme: 2025-05-21 05:21:55
// Güncelleyen: Teeksss