import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for masking API
const MASKING_API = `${API_BASE_URL}/admin/masking`;

/**
 * Get all masking rules
 * 
 * @returns {Promise<Array>} Array of masking rules
 */
export const getMaskingRules = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(MASKING_API, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching masking rules:', error);
    throw error;
  }
};

/**
 * Get a specific masking rule by ID
 * 
 * @param {number} ruleId - ID of the masking rule
 * @returns {Promise<Object>} Masking rule object
 */
export const getMaskingRule = async (ruleId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${MASKING_API}/${ruleId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching masking rule #${ruleId}:`, error);
    throw error;
  }
};

/**
 * Create a new masking rule
 * 
 * @param {Object} ruleData - Masking rule data
 * @returns {Promise<Object>} Created masking rule
 */
export const createMaskingRule = async (ruleData) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(MASKING_API, ruleData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error creating masking rule:', error);
    throw error;
  }
};

/**
 * Update an existing masking rule
 * 
 * @param {number} ruleId - ID of the masking rule to update
 * @param {Object} ruleData - Updated masking rule data
 * @returns {Promise<Object>} Updated masking rule
 */
export const updateMaskingRule = async (ruleId, ruleData) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${MASKING_API}/${ruleId}`, ruleData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error updating masking rule #${ruleId}:`, error);
    throw error;
  }
};

/**
 * Delete a masking rule
 * 
 * @param {number} ruleId - ID of the masking rule to delete
 * @returns {Promise<Object>} Response data
 */
export const deleteMaskingRule = async (ruleId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.delete(`${MASKING_API}/${ruleId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error deleting masking rule #${ruleId}:`, error);
    throw error;
  }
};

/**
 * Test a table pattern against a table name
 * 
 * @param {string} pattern - Regular expression pattern to test
 * @param {string} tableName - Table name to test against the pattern
 * @returns {Promise<Object>} Test result with match status
 */
export const testMaskingPattern = async (pattern, tableName) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${MASKING_API}/test-pattern`, {
      pattern,
      table_name: tableName
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error testing masking pattern:', error);
    throw error;
  }
};

/**
 * Get a list of predefined masking types
 * 
 * @returns {Promise<Array>} List of available masking types
 */
export const getMaskingTypes = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${MASKING_API}/types`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching masking types:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:19:26
// Güncelleyen: Teeksss