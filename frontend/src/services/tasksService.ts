/**
 * Tasks Service
 * 
 * Service for interacting with scheduled tasks and background jobs
 * 
 * Last updated: 2025-05-21 05:35:49
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';
import { Task, TaskListResponse, TaskCreateParams } from '../types/tasks';

export const tasksApi = {
  /**
   * Get all scheduled tasks
   * 
   * @returns Promise with tasks data
   */
  getTasks: async (): Promise<TaskListResponse> => {
    try {
      const response = await api.get('/tasks');
      return response.data;
    } catch (error) {
      throw handleTasksApiError(error);
    }
  },

  /**
   * Create a new scheduled task
   * 
   * @param task Task creation parameters
   * @returns Promise with task data
   */
  createTask: async (task: TaskCreateParams): Promise<Task> => {
    try {
      const response = await api.post('/tasks', task);
      return response.data;
    } catch (error) {
      throw handleTasksApiError(error);
    }
  },

  /**
   * Delete a scheduled task
   * 
   * @param taskId Task ID
   * @returns Promise with response data
   */
  deleteTask: async (taskId: string): Promise<any> => {
    try {
      const response = await api.delete(`/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      throw handleTasksApiError(error);
    }
  },

  /**
   * Run a scheduled task immediately
   * 
   * @param taskId Task ID
   * @returns Promise with response data
   */
  runTaskNow: async (taskId: string): Promise<any> => {
    try {
      const response = await api.post(`/tasks/${taskId}/run-now`);
      return response.data;
    } catch (error) {
      throw handleTasksApiError(error);
    }
  }
};

/**
 * Handle API errors
 * 
 * @param error Error from API
 */
function handleTasksApiError(error: any) {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || error.message;
    return new Error(message);
  }
  return error;
}

// Son güncelleme: 2025-05-21 05:35:49
// Güncelleyen: Teeksss