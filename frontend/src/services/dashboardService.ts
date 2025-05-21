/**
 * Dashboard Service
 * 
 * Service for interacting with dashboard API endpoints
 * 
 * Last updated: 2025-05-21 06:38:34
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';

export const dashboardApi = {
  /**
   * Get dashboard configuration
   * 
   * @param dashboardId Dashboard ID or "default"
   * @returns Dashboard configuration
   */
  getDashboard: async (dashboardId: string = 'default') => {
    try {
      const response = await api.get(`/dashboards/${dashboardId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Update dashboard configuration
   * 
   * @param dashboardId Dashboard ID or "default"
   * @param data Dashboard configuration data
   * @returns Updated dashboard
   */
  updateDashboard: async (dashboardId: string = 'default', data: any) => {
    try {
      const response = await api.patch(`/dashboards/${dashboardId}`, data);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Create a new dashboard
   * 
   * @param data Dashboard creation data
   * @returns Created dashboard
   */
  createDashboard: async (data: any) => {
    try {
      const response = await api.post('/dashboards', data);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Delete a dashboard
   * 
   * @param dashboardId Dashboard ID
   * @returns Success status
   */
  deleteDashboard: async (dashboardId: string) => {
    try {
      const response = await api.delete(`/dashboards/${dashboardId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get all user dashboards
   * 
   * @returns List of dashboards
   */
  getAllDashboards: async () => {
    try {
      const response = await api.get('/dashboards');
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

// Son güncelleme: 2025-05-21 06:38:34
// Güncelleyen: Teeksss