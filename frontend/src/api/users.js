import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for users API
const USERS_API = `${API_BASE_URL}/users`;

/**
 * Get current user information
 * 
 * @returns {Promise<Object>} User information
 */
export const getCurrentUser = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${USERS_API}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching current user:', error);
    throw error;
  }
};

/**
 * Get user preferences and settings
 * 
 * @returns {Promise<Object>} User preferences
 */
export const getUserPreferences = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${USERS_API}/preferences`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching user preferences:', error);
    throw error;
  }
};

/**
 * Update user preferences
 * 
 * @param {Object} preferences - Updated preferences
 * @returns {Promise<Object>} Updated user preferences
 */
export const updateUserPreferences = async (preferences) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${USERS_API}/preferences`, preferences, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error updating user preferences:', error);
    throw error;
  }
};

/**
 * Get list of users (admin only)
 * 
 * @param {Object} options - Query options
 * @param {string} options.role - Filter by role
 * @param {boolean} options.active - Filter by active status
 * @returns {Promise<Array>} List of users
 */
export const getUsers = async (options = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      ...(options.role && { role: options.role }),
      ...(options.active !== undefined && { active: options.active.toString() })
    };
    
    const response = await axios.get(USERS_API, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};

/**
 * Get user activity history
 * 
 * @param {Object} options - Query options
 * @param {string} options.userId - User ID (admin only, defaults to current user)
 * @param {string} options.startDate - Filter by start date (ISO string)
 * @param {string} options.endDate - Filter by end date (ISO string)
 * @returns {Promise<Array>} User activity history
 */
export const getUserActivity = async (options = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      ...(options.userId && { user_id: options.userId }),
      ...(options.startDate && { start_date: options.startDate }),
      ...(options.endDate && { end_date: options.endDate })
    };
    
    const response = await axios.get(`${USERS_API}/activity`, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching user activity:', error);
    throw error;
  }
};

/**
 * Update user role (admin only)
 * 
 * @param {string} userId - User ID
 * @param {string} role - New role
 * @returns {Promise<Object>} Updated user information
 */
export const updateUserRole = async (userId, role) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${USERS_API}/${userId}/role`, { role }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error updating role for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Activate or deactivate a user (admin only)
 * 
 * @param {string} userId - User ID
 * @param {boolean} isActive - Active status
 * @returns {Promise<Object>} Updated user information
 */
export const setUserActiveStatus = async (userId, isActive) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${USERS_API}/${userId}/status`, 
      { is_active: isActive },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error(`Error updating status for user ${userId}:`, error);
    throw error;
  }
};

/**
 * Get user sessions
 * 
 * @param {string} userId - User ID (admin only, defaults to current user)
 * @returns {Promise<Array>} List of active sessions
 */
export const getUserSessions = async (userId = null) => {
  const token = getAuthToken();
  
  try {
    const url = userId ? `${USERS_API}/${userId}/sessions` : `${USERS_API}/sessions`;
    
    const response = await axios.get(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching user sessions:', error);
    throw error;
  }
};

/**
 * Revoke a specific session
 * 
 * @param {string} sessionId - Session ID to revoke
 * @returns {Promise<Object>} Response data
 */
export const revokeSession = async (sessionId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.delete(`${USERS_API}/sessions/${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error revoking session ${sessionId}:`, error);
    throw error;
  }
};

/**
 * Revoke all sessions except current
 * 
 * @returns {Promise<Object>} Response data
 */
export const revokeAllSessions = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.delete(`${USERS_API}/sessions`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error revoking all sessions:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:40:32
// Güncelleyen: Teeksss