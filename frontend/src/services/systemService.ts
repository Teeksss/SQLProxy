/**
 * System Service
 * 
 * Service for interacting with system API endpoints
 * 
 * Last updated: 2025-05-21 07:07:17
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';

export const systemApi = {
  /**
   * Get system status information
   * 
   * @returns System status data
   */
  getSystemStatus: async () => {
    try {
      const response = await api.get('/system/status');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get system logs
   * 
   * @param level Log level filter
   * @param limit Maximum number of logs to return
   * @returns System logs
   */
  getSystemLogs: async (level?: string, limit?: number) => {
    try {
      const params = new URLSearchParams();
      if (level) params.append('level', level);
      if (limit) params.append('limit', limit.toString());
      
      const response = await api.get(`/system/logs?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get system resource metrics
   * 
   * @param timeframe Timeframe for metrics (e.g., "1h", "24h", "7d")
   * @returns System resource metrics
   */
  getSystemMetrics: async (timeframe: string = '1h') => {
    try {
      const response = await api.get(`/system/metrics?timeframe=${timeframe}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get system health check
   * 
   * @returns System health status
   */
  getSystemHealth: async () => {
    try {
      const response = await api.get('/system/health');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Restart a system service
   * 
   * @param serviceId Service ID to restart
   * @returns Success status
   */
  restartService: async (serviceId: string) => {
    try {
      const response = await api.post(`/system/services/${serviceId}/restart`);
      return response.data;
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