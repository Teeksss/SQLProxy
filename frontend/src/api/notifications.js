import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for notifications API
const NOTIFICATION_API = `${API_BASE_URL}/notifications`;

/**
 * Get user notifications
 * 
 * @param {Object} options - Query options
 * @param {boolean} options.unreadOnly - Get only unread notifications
 * @param {number} options.limit - Maximum number of notifications to retrieve
 * @returns {Promise<Array>} Array of notifications
 */
export const getUserNotifications = async (options = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      unread_only: options.unreadOnly ? 'true' : 'false',
      limit: options.limit || 20
    };
    
    const response = await axios.get(NOTIFICATION_API, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching notifications:', error);
    throw error;
  }
};

/**
 * Mark notification as read
 * 
 * @param {number} notificationId - ID of the notification to mark as read
 * @returns {Promise<Object>} Updated notification
 */
export const markNotificationAsRead = async (notificationId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${NOTIFICATION_API}/${notificationId}/read`, null, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error marking notification #${notificationId} as read:`, error);
    throw error;
  }
};

/**
 * Mark all notifications as read
 * 
 * @returns {Promise<Object>} Response data
 */
export const markAllNotificationsAsRead = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${NOTIFICATION_API}/read-all`, null, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error marking all notifications as read:', error);
    throw error;
  }
};

/**
 * Get notification settings
 * 
 * @returns {Promise<Object>} Notification settings
 */
export const getNotificationSettings = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${NOTIFICATION_API}/settings`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching notification settings:', error);
    throw error;
  }
};

/**
 * Update notification settings
 * 
 * @param {Object} settings - Updated notification settings
 * @returns {Promise<Object>} Updated settings
 */
export const updateNotificationSettings = async (settings) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.put(`${NOTIFICATION_API}/settings`, settings, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error updating notification settings:', error);
    throw error;
  }
};

/**
 * Delete a notification
 * 
 * @param {number} notificationId - ID of the notification to delete
 * @returns {Promise<Object>} Response data
 */
export const deleteNotification = async (notificationId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.delete(`${NOTIFICATION_API}/${notificationId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error deleting notification #${notificationId}:`, error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:33:12
// Güncelleyen: Teeksss