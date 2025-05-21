/**
 * Audit Service
 * 
 * Service for interacting with audit log API endpoints
 * 
 * Last updated: 2025-05-21 07:07:17
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';

export const auditApi = {
  /**
   * Get audit logs with filtering
   * 
   * @param params Filter parameters
   * @returns Filtered audit logs
   */
  getAuditLogs: async (params: any = {}) => {
    try {
      // Build query parameters
      const queryParams = new URLSearchParams();
      
      if (params.page !== undefined) {
        queryParams.append('offset', (params.page * (params.limit || 10)).toString());
      }
      
      if (params.limit !== undefined) {
        queryParams.append('limit', params.limit.toString());
      }
      
      if (params.eventType) {
        queryParams.append('event_type', params.eventType);
      }
      
      if (params.resourceType) {
        queryParams.append('resource_type', params.resourceType);
      }
      
      if (params.action) {
        queryParams.append('action', params.action);
      }
      
      if (params.userId) {
        queryParams.append('user_id', params.userId);
      }
      
      if (params.status) {
        queryParams.append('status', params.status);
      }
      
      if (params.startDate) {
        queryParams.append('start_date', params.startDate);
      }
      
      if (params.endDate) {
        queryParams.append('end_date', params.endDate);
      }
      
      const response = await api.get(`/audit/logs?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get audit log summary
   * 
   * @param days Number of days to include in summary (default: 30)
   * @returns Audit log summary
   */
  getAuditSummary: async (days: number = 30) => {
    try {
      const response = await api.get(`/audit/summary?days=${days}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get audit log details
   * 
   * @param logId Audit log ID
   * @returns Audit log details
   */
  getAuditLogDetails: async (logId: string) => {
    try {
      const response = await api.get(`/audit/logs/${logId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Export audit logs
   * 
   * @param filters Filter parameters
   * @param format Export format ('csv', 'json', 'excel')
   * @returns Exported file
   */
  exportAuditLogs: async (filters: any = {}, format: string = 'csv') => {
    try {
      // Build query parameters
      const queryParams = new URLSearchParams();
      
      if (filters.eventType) {
        queryParams.append('event_type', filters.eventType);
      }
      
      if (filters.resourceType) {
        queryParams.append('resource_type', filters.resourceType);
      }
      
      if (filters.action) {
        queryParams.append('action', filters.action);
      }
      
      if (filters.userId) {
        queryParams.append('user_id', filters.userId);
      }
      
      if (filters.status) {
        queryParams.append('status', filters.status);
      }
      
      if (filters.startDate) {
        queryParams.append('start_date', filters.startDate);
      }
      
      if (filters.endDate) {
        queryParams.append('end_date', filters.endDate);
      }
      
      queryParams.append('format', format);
      
      // Use fetch with blob response to handle file download
      const response = await fetch(`${api.defaults.baseURL}/audit/export?${queryParams.toString()}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`Export failed with status ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Create a hidden link and trigger download
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      return true;
    } catch (error) {
      throw handleApiError(error);
    }
  }
};

/**
 * Handle API errors
 * 
 * @param error Error from API
 * @returns Error object
 */
function handleApiError(error: any) {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || error.message;
    return new Error(message);
  }
  return error;
}

// Son güncelleme: 2025-05-21 07:07:17
// Güncelleyen: Teeksss