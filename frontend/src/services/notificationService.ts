/**
 * Notification Service
 * 
 * Service for interacting with notification API endpoints
 * 
 * Last updated: 2025-05-21 06:38:34
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';

export const notificationApi = {
  /**
   * Get user notifications
   * 
   * @param unreadOnly Whether to return only unread notifications
   * @param skip Number of items to skip
   * @param limit Maximum number of items to return
   * @returns List of notifications
   */
  getNotifications: async (unreadOnly: boolean = false, skip: number = 0, limit: number = 10) => {
    try {
      const params = new URLSearchParams();
      if (unreadOnly) {
        params.append('unread_only', 'true');
      }
      params.append('skip', skip.toString());
      params.append('limit', limit.toString());
      
      const response = await api.get(`/notifications?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Mark a notification as read
   * 
   * @param notificationId Notification ID
   * @returns Success status
   */
  markAsRead: async (notificationId: number) => {
    try {
      const response = await api.post(`/notifications/${notificationId}/read`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Mark all notifications as read
   * 
   * @returns Success status
   */
  markAllAsRead: async () => {
    try {
      const response = await api.post('/notifications/read-all');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Update notification preferences
   * 
   * @param preferences Notification preferences
   * @returns Updated preferences
   */
  updatePreferences: async (preferences: any) => {
    try {
      const response = await api.post('/notifications/preferences', preferences);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get notification preferences
   * 
   * @returns Notification preferences
   */
  getPreferences: async () => {
    try {
      const response = await api.get('/notifications/preferences');
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