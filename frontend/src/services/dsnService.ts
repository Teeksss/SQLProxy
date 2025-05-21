/**
 * DSN Service
 * 
 * Service for interacting with DSN (Data Source Name) API endpoints
 * 
 * Last updated: 2025-05-21 06:45:04
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';

export const dsnApi = {
  /**
   * Get available DSN templates
   * 
   * @returns List of templates
   */
  getTemplates: async () => {
    try {
      const response = await api.get('/dsn/templates');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Generate DSN configuration
   * 
   * @param data Generation parameters
   * @returns DSN generation result
   */
  generateDSN: async (data: any) => {
    try {
      // Convert to form data
      const formData = new FormData();
      formData.append('template_id', data.templateId);
      
      if (data.serverId) {
        formData.append('server_id', data.serverId);
      }
      
      if (data.dsnName) {
        formData.append('dsn_name', data.dsnName);
      }
      
      if (data.additionalParams) {
        formData.append('additional_params', data.additionalParams);
      }
      
      const response = await api.post('/dsn/generate', formData);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get user DSN configurations
   * 
   * @returns User's DSN configurations
   */
  getUserConfigs: async () => {
    try {
      const response = await api.get('/dsn/user-configs');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Delete user DSN configuration
   * 
   * @param dsnName DSN name
   * @returns Delete result
   */
  deleteUserConfig: async (dsnName: string) => {
    try {
      const response = await api.delete(`/dsn/user-configs/${dsnName}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get PowerBI connection string
   * 
   * @param serverId Server ID
   * @returns Connection details
   */
  getPowerBIConnection: async (serverId: string) => {
    try {
      const response = await api.get(`/dsn/powerbi-connection/${serverId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Upload custom DSN template (admin only)
   * 
   * @param file Template JSON file
   * @returns Upload result
   */
  uploadTemplate: async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('template_file', file);
      
      const response = await api.post('/dsn/upload-template', formData);
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

// Son güncelleme: 2025-05-21 06:45:04
// Güncelleyen: Teeksss