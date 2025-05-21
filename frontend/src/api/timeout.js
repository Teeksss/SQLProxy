import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for timeout API
const TIMEOUT_API = `${API_BASE_URL}/admin/timeouts`;

/**
 * Get all timeout settings (roles and custom)
 * 
 * @returns {Promise<Object>} Timeout settings object with role_settings and custom_settings
 */
export const getTimeoutSettings = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(TIMEOUT_API, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching timeout settings:', error);
    throw error;
  }
};

/**
 * Update a role's timeout setting
 * 
 * @param {string} role - Role name (admin, analyst, etc.)
 * @param {number} timeoutSeconds - New timeout in seconds
 * @returns {Promise<Object>} Updated role timeout
 */
export const updateRoleTimeout = async (role, timeoutSeconds) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${TIMEOUT_API}/roles/${role}`, {
      timeout_seconds: timeoutSeconds
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error updating role timeout for ${role}:`, error);
    throw error;
  }
};

/**
 * Create a new custom timeout setting
 * 
 * @param {Object} data - Custom timeout data
 * @param {string} data.type - Type of timeout (user or group)
 * @param {string} data.identifier - User or group identifier
 * @param {number} data.timeout_seconds - Timeout in seconds
 * @param {string} data.description - Optional description
 * @returns {Promise<Object>} Created custom timeout
 */
export const createCustomTimeout = async (data) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(TIMEOUT_API, data, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error creating custom timeout:', error);
    throw error;
  }
};

/**
 * Update an existing custom timeout setting
 * 
 * @param {number} id - Custom timeout ID
 * @param {Object} data - Updated timeout data
 * @returns {Promise<Object>} Updated custom timeout
 */
export const updateCustomTimeout = async (id, data) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${TIMEOUT_API}/${id}`, data, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error updating custom timeout #${id}:`, error);
    throw error;
  }
};

/**
 * Delete a custom timeout setting
 * 
 * @param {number} id - Custom timeout ID
 * @returns {Promise<Object>} Response data
 */
export const deleteCustomTimeout = async (id) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.delete(`${TIMEOUT_API}/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error deleting custom timeout #${id}:`, error);
    throw error;
  }
};

/**
 * Test a SQL query execution time
 * 
 * @param {string} query - SQL query to test
 * @param {string} serverAlias - Target server alias
 * @returns {Promise<Object>} Execution time results
 */
export const testQuery = async (query, serverAlias) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${TIMEOUT_API}/test-query`, {
      sql_query: query,
      server_alias: serverAlias
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error testing query execution time:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:19:26
// Güncelleyen: Teeksss