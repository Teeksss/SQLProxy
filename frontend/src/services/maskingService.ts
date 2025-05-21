/**
 * Data Masking Service
 * 
 * Service for interacting with the data masking API
 * 
 * Last updated: 2025-05-20 14:59:32
 * Updated by: Teeksss
 */

import { AxiosError } from 'axios';
import { api } from './api';
import { MaskingRule, MaskingRuleTestResult } from '../types/masking';

const maskingApi = {
  /**
   * Get all masking rules
   */
  getMaskingRules: async () => {
    try {
      const response = await api.get('/masking');
      return response.data;
    } catch (error) {
      throw handleMaskingApiError(error);
    }
  },

  /**
   * Create a new masking rule
   * 
   * @param rule - Masking rule to create
   */
  createMaskingRule: async (rule: Partial<MaskingRule>) => {
    try {
      const response = await api.post('/masking', rule);
      return response.data;
    } catch (error) {
      throw handleMaskingApiError(error);
    }
  },

  /**
   * Update an existing masking rule
   * 
   * @param id - ID of the rule to update
   * @param rule - Updated rule data
   */
  updateMaskingRule: async (id: number, rule: Partial<MaskingRule>) => {
    try {
      const response = await api.put(`/masking/${id}`, rule);
      return response.data;
    } catch (error) {
      throw handleMaskingApiError(error);
    }
  },

  /**
   * Delete a masking rule
   * 
   * @param id - ID of the rule to delete
   */
  deleteMaskingRule: async (id: number) => {
    try {
      const response = await api.delete(`/masking/${id}`);
      return response.data;
    } catch (error) {
      throw handleMaskingApiError(error);
    }
  },

  /**
   * Test a masking rule
   * 
   * @param data - Test data including rule configuration and test data
   */
  testMaskingRule: async (data: {
    rule_type: string;
    masking_method: string;
    pattern?: string;
    column_name?: string;
    test_data: string[];
  }): Promise<MaskingRuleTestResult> => {
    try {
      const response = await api.post('/masking/test', data);
      return response.data;
    } catch (error) {
      throw handleMaskingApiError(error);
    }
  },

  /**
   * Get masking status
   */
  getMaskingStatus: async () => {
    try {
      const response = await api.get('/masking/enabled');
      return response.data;
    } catch (error) {
      throw handleMaskingApiError(error);
    }
  },
};

/**
 * Handle API errors
 * 
 * @param error - Error from API
 */
function handleMaskingApiError(error: any) {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || error.message;
    return new Error(message);
  }
  return error;
}

export { maskingApi };

// Son güncelleme: 2025-05-20 14:59:32
// Güncelleyen: Teeksss