/**
 * Metrics Service
 * 
 * Service for interacting with metrics and performance monitoring APIs
 * 
 * Last updated: 2025-05-21 05:17:27
 * Updated by: Teeksss
 */

import { api } from './api';

export interface PerformanceMetrics {
  queries: Record<string, DatabaseMetrics>;
  endpoints: Record<string, EndpointMethodMetrics>;
  timestamp: string;
  collection_period: {
    start: string;
    end: string;
  };
}

interface DatabaseMetrics {
  average: number;
  median: number;
  p95: number;
  min: number;
  max: number;
  count: number;
  endpoints: Record<string, EndpointMetrics>;
}

interface EndpointMethodMetrics {
  average: number;
  median: number;
  p95: number;
  min: number;
  max: number;
  count: number;
  endpoints: Record<string, EndpointMetrics>;
}

interface EndpointMetrics {
  average: number;
  median: number;
  p95: number;
  min: number;
  max: number;
  count: number;
}

export const metricsApi = {
  /**
   * Get performance metrics
   * 
   * @param timeRange Time range for metrics (1h, 6h, 24h, 7d, 30d)
   * @returns Performance metrics
   */
  getPerformanceMetrics: async (timeRange: string = '24h'): Promise<PerformanceMetrics> => {
    const response = await api.get(`/metrics/performance?timeRange=${timeRange}`);
    return response.data;
  },
  
  /**
   * Export performance metrics as CSV
   */
  exportPerformanceMetrics: async (): Promise<void> => {
    const response = await api.get('/metrics/performance/export', {
      responseType: 'blob'
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `performance_metrics_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
  
  /**
   * Get system metrics
   * 
   * @returns System metrics
   */
  getSystemMetrics: async () => {
    const response = await api.get('/metrics/system');
    return response.data;
  },
  
  /**
   * Get query analytics
   * 
   * @param serverId Server ID
   * @param timeRange Time range
   * @returns Query analytics
   */
  getQueryAnalytics: async (serverId?: string, timeRange: string = '24h') => {
    const params = new URLSearchParams();
    if (serverId) params.append('serverId', serverId);
    params.append('timeRange', timeRange);
    
    const response = await api.get(`/metrics/query-analytics?${params.toString()}`);
    return response.data;
  },
  
  /**
   * Reset performance metrics
   */
  resetPerformanceMetrics: async () => {
    await api.post('/metrics/performance/reset');
  },
  
  /**
   * Analyze query performance
   * 
   * @param query SQL query
   * @param parameters Query parameters
   * @param serverId Server ID
   * @returns Query performance analysis
   */
  analyzeQueryPerformance: async (query: string, parameters?: Record<string, any>, serverId?: string) => {
    const response = await api.post('/metrics/analyze-query', {
      query,
      parameters,
      serverId
    });
    return response.data;
  }
};

// Son güncelleme: 2025-05-21 05:17:27
// Güncelleyen: Teeksss