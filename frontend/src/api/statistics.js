import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for statistics API
const STATISTICS_API = `${API_BASE_URL}/admin/statistics`;

/**
 * Get system statistics
 * 
 * @param {string} timeRange - Time range for statistics (24h, 7d, 30d, 90d)
 * @returns {Promise<Object>} Statistics data
 */
export const getStatistics = async (timeRange = '7d') => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(STATISTICS_API, {
      params: { time_range: timeRange },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching statistics:', error);
    throw error;
  }
};

/**
 * Get user-specific statistics
 * 
 * @param {string} userId - User ID (defaults to current user)
 * @param {string} timeRange - Time range for statistics (24h, 7d, 30d, 90d)
 * @returns {Promise<Object>} User statistics data
 */
export const getUserStatistics = async (userId = null, timeRange = '7d') => {
  const token = getAuthToken();
  
  try {
    const url = userId ? `${STATISTICS_API}/users/${userId}` : `${STATISTICS_API}/users/me`;
    
    const response = await axios.get(url, {
      params: { time_range: timeRange },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching user statistics:', error);
    throw error;
  }
};

/**
 * Get server statistics
 * 
 * @param {string} serverAlias - Server alias
 * @param {string} timeRange - Time range for statistics (24h, 7d, 30d, 90d)
 * @returns {Promise<Object>} Server statistics data
 */
export const getServerStatistics = async (serverAlias, timeRange = '7d') => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${STATISTICS_API}/servers/${serverAlias}`, {
      params: { time_range: timeRange },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching statistics for server ${serverAlias}:`, error);
    throw error;
  }
};

/**
 * Get real-time active queries
 * 
 * @returns {Promise<Array>} List of currently running queries
 */
export const getActiveQueries = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${STATISTICS_API}/active-queries`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching active queries:', error);
    throw error;
  }
};

/**
 * Get performance metrics
 * 
 * @param {string} metricType - Type of metric (cpu, memory, queries, etc.)
 * @param {string} timeRange - Time range for metrics (1h, 6h, 24h, 7d)
 * @returns {Promise<Object>} Performance metrics data
 */
export const getPerformanceMetrics = async (metricType = 'queries', timeRange = '1h') => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${STATISTICS_API}/performance`, {
      params: { 
        metric: metricType,
        time_range: timeRange 
      },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching performance metrics:', error);
    throw error;
  }
};

/**
 * Export statistics to CSV or Excel
 * 
 * @param {string} format - Export format (csv, xlsx)
 * @param {string} reportType - Type of report (queries, users, servers, etc.)
 * @param {string} timeRange - Time range for statistics (24h, 7d, 30d, 90d)
 * @returns {Promise<Blob>} File blob
 */
export const exportStatistics = async (format = 'csv', reportType = 'queries', timeRange = '7d') => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${STATISTICS_API}/export`, {
      params: {
        format,
        report_type: reportType,
        time_range: timeRange
      },
      headers: {
        'Authorization': `Bearer ${token}`
      },
      responseType: 'blob'
    });
    
    // Create a download link
    const filename = `sql_proxy_stats_${reportType}_${timeRange}.${format}`;
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    return response.data;
  } catch (error) {
    console.error('Error exporting statistics:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:40:32
// Güncelleyen: Teeksss