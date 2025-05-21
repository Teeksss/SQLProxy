/**
 * PowerBI Service
 * 
 * Service for interacting with PowerBI integration APIs
 * 
 * Last updated: 2025-05-21 05:48:50
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';
import { 
  PowerBIWorkspace, 
  PowerBIWorkspacesResponse, 
  PowerBIReport,
  PowerBIReportsResponse,
  PowerBIEmbedToken,
  PowerBICreateReportParams
} from '../types/powerbi';

export const powerbiApi = {
  /**
   * Get PowerBI workspaces
   */
  getWorkspaces: async (): Promise<PowerBIWorkspacesResponse> => {
    try {
      const response = await api.get('/powerbi/workspaces');
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Get workspace details
   * 
   * @param workspaceId Workspace ID
   * @returns Workspace details
   */
  getWorkspace: async (workspaceId: string): Promise<PowerBIWorkspace> => {
    try {
      const response = await api.get(`/powerbi/workspaces/${workspaceId}`);
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Create a new PowerBI workspace
   * 
   * @param params Workspace creation parameters
   * @returns Created workspace
   */
  createWorkspace: async (params: { name: string; description?: string }): Promise<PowerBIWorkspace> => {
    try {
      const response = await api.post('/powerbi/workspaces', params);
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Get PowerBI reports
   * 
   * @param workspaceId Optional workspace ID
   * @returns List of reports
   */
  getReports: async (workspaceId?: string): Promise<PowerBIReportsResponse> => {
    try {
      const params = new URLSearchParams();
      if (workspaceId) {
        params.append('workspace_id', workspaceId);
      }
      
      const response = await api.get(`/powerbi/reports?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Get report details
   * 
   * @param reportId Report ID
   * @returns Report details
   */
  getReport: async (reportId: string): Promise<PowerBIReport> => {
    try {
      const response = await api.get(`/powerbi/reports/${reportId}`);
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Delete a PowerBI report
   * 
   * @param reportId Report ID
   * @returns Success message
   */
  deleteReport: async (reportId: string): Promise<any> => {
    try {
      const response = await api.delete(`/powerbi/reports/${reportId}`);
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Create a report from a SQL query
   * 
   * @param params Report creation parameters
   * @returns Created report
   */
  createReportFromQuery: async (params: PowerBICreateReportParams): Promise<PowerBIReport> => {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('server_id', params.server_id);
      
      if (params.query_id) {
        queryParams.append('query_id', params.query_id);
      } else if (params.query_text) {
        queryParams.append('query_text', params.query_text);
      }
      
      const response = await api.post(`/powerbi/reports?${queryParams.toString()}`, {
        name: params.name,
        description: params.description,
        workspace_id: params.workspace_id
      });
      
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Import a PowerBI report (PBIX file)
   * 
   * @param formData FormData with file and parameters
   * @returns Import result
   */
  importReport: async (formData: FormData): Promise<any> => {
    try {
      const response = await api.post('/powerbi/reports/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Get embed token for a report
   * 
   * @param reportId Report ID
   * @returns Embed token
   */
  getReportEmbedToken: async (reportId: string): Promise<PowerBIEmbedToken> => {
    try {
      const response = await api.post(`/powerbi/reports/${reportId}/embed`);
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  },

  /**
   * Update PowerBI credentials
   * 
   * @param credentials PowerBI credentials
   * @returns Success message
   */
  updateCredentials: async (credentials: {
    tenant_id: string;
    client_id: string;
    client_secret: string;
  }): Promise<any> => {
    try {
      const response = await api.post('/powerbi/refresh-credentials', credentials);
      return response.data;
    } catch (error) {
      throw handlePowerBIApiError(error);
    }
  }
};

/**
 * Handle API errors
 * 
 * @param error Error from API
 */
function handlePowerBIApiError(error: any) {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || error.message;
    return new Error(message);
  }
  return error;
}

// Son güncelleme: 2025-05-21 05:48:50
// Güncelleyen: Teeksss