/**
 * Tasks Types
 * 
 * Type definitions for scheduled tasks and background jobs
 * 
 * Last updated: 2025-05-21 05:35:49
 * Updated by: Teeksss
 */

/**
 * Task as returned from the API
 */
export interface Task {
  id: string;
  next_run: string | null;
  last_run: string | null;
  interval: string | null;
  tags: string[];
}

/**
 * Task creation parameters
 */
export interface TaskCreateParams {
  task_id: string;
  task_type: string;
  parameters: Record<string, any>;
  interval_hours?: number;
  interval_minutes?: number;
  interval_seconds?: number;
  first_run?: string;
  run_at?: string;
  run_daily?: boolean;
}

/**
 * Task list response from the API
 */
export interface TaskListResponse {
  tasks: Task[];
}

// Son güncelleme: 2025-05-21 05:35:49
// Güncelleyen: Teeksss