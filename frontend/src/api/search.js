import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for search API
const SEARCH_API = `${API_BASE_URL}/search`;

/**
 * Search the entire system
 * 
 * @param {string} query - Search query
 * @returns {Promise<Object>} Search results grouped by type
 */
export const searchSystem = async (query) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(SEARCH_API, {
      params: { query },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error searching system:', error);
    throw error;
  }
};

/**
 * Search queries (history and whitelist)
 * 
 * @param {string} query - Search query
 * @returns {Promise<Object>} Query search results
 */
export const searchQueries = async (query) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${SEARCH_API}/queries`, {
      params: { query },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error searching queries:', error);
    throw error;
  }
};

/**
 * Search users
 * 
 * @param {string} query - Search query
 * @returns {Promise<Array>} User search results
 */
export const searchUsers = async (query) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${SEARCH_API}/users`, {
      params: { query },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error searching users:', error);
    throw error;
  }
};

/**
 * Search documentation
 * 
 * @param {string} query - Search query
 * @returns {Promise<Array>} Documentation search results
 */
export const searchDocumentation = async (query) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${SEARCH_API}/docs`, {
      params: { query },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error searching documentation:', error);
    throw error;
  }
};

/**
 * Search audit logs
 * 
 * @param {string} query - Search query
 * @param {Object} filters - Additional filters
 * @returns {Promise<Array>} Audit log search results
 */
export const searchAuditLogs = async (query, filters = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      query,
      ...filters
    };
    
    const response = await axios.get(`${SEARCH_API}/audit-logs`, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error searching audit logs:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:50:02
// Güncelleyen: Teeksss