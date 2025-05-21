import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for audit API
const AUDIT_API = `${API_BASE_URL}/admin/audit`;

/**
 * Get audit logs with optional filters
 * 
 * @param {Object} filters - Query filters
 * @param {string} filters.username - Filter by username
 * @param {string} filters.server - Filter by server
 * @param {string} filters.status - Filter by execution status
 * @param {string} filters.query_type - Filter by query type
 * @param {string} filters.startDate - Filter by start date (ISO string)
 * @param {string} filters.endDate - Filter by end date (ISO string)
 * @param {number} filters.page - Page number
 * @param {number} filters.limit - Items per page
 * @returns {Promise<Object>} - Promise with audit logs data
 */
export const getAuditLogs = async (filters = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      page: filters.page || 1,
      limit: filters.limit || 50,
      ...(filters.username && { username: filters.username }),
      ...(filters.server && { server: filters.server }),
      ...(filters.status && { status: filters.status }),
      ...(filters.query_type && { query_type: filters.query_type }),
      ...(filters.startDate && { date_from: filters.startDate }),
      ...(filters.endDate && { date_to: filters.endDate })
    };
    
    const response = await axios.get(AUDIT_API, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching audit logs:', error);
    throw error;
  }
};

/**
 * Export audit logs with filters
 * 
 * @param {Object} filters - Query filters
 * @param {string} filters.format - Export format (csv, json, xlsx)
 * @returns {Promise<Blob>} - Promise with exported file content
 */
export const exportAuditLogs = async (filters = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      format: filters.format || 'csv',
      ...(filters.username && { username: filters.username }),
      ...(filters.server && { server: filters.server }),
      ...(filters.status && { status: filters.status }),
      ...(filters.query_type && { query_type: filters.query_type }),
      ...(filters.startDate && { date_from: filters.startDate }),
      ...(filters.endDate && { date_to: filters.endDate })
    };
    
    const response = await axios.get(`${AUDIT_API}/export`, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      },
      responseType: 'blob'
    });
    
    // Create a download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `audit_logs_${new Date().toISOString().split('T')[0]}.${filters.format || 'csv'}`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    return response.data;
  } catch (error) {
    console.error('Error exporting audit logs:', error);
    throw error;
  }
};

/**
 * Get audit log details by ID
 * 
 * @param {number} logId - Audit log ID
 * @returns {Promise<Object>} - Promise with audit log details
 */
export const getAuditLogDetails = async (logId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${AUDIT_API}/${logId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching audit log #${logId} details:`, error);
    throw error;
  }
};

/**
 * Get aggregated audit statistics
 * 
 * @param {Object} filters - Query filters for time period
 * @param {string} filters.startDate - Filter by start date (ISO string)
 * @param {string} filters.endDate - Filter by end date (ISO string)
 * @returns {Promise<Object>} - Promise with statistics data
 */
export const getAuditStatistics = async (filters = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      ...(filters.startDate && { date_from: filters.startDate }),
      ...(filters.endDate && { date_to: filters.endDate })
    };
    
    const response = await axios.get(`${AUDIT_API}/stats`, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching audit statistics:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-16 13:44:50
// Güncelleyen: Teeksss