import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Get all rate limit rules
 */
export const getRateLimitRules = async () => {
  try {
    const response = await axios.get(`${API_URL}/admin/rate-limits`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Create a new rate limit rule
 */
export const createRateLimitRule = async (ruleData) => {
  try {
    const response = await axios.post(`${API_URL}/admin/rate-limits`, ruleData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Update an existing rate limit rule
 */
export const updateRateLimitRule = async (ruleId, ruleData) => {
  try {
    const response = await axios.put(`${API_URL}/admin/rate-limits/${ruleId}`, ruleData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Delete a rate limit rule
 */
export const deleteRateLimitRule = async (ruleId) => {
  try {
    const response = await axios.delete(`${API_URL}/admin/rate-limits/${ruleId}`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get rate limit status for current user
 */
export const getRateLimitStatus = async () => {
  try {
    const response = await axios.get(`${API_URL}/rate-limit/status`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Handle API errors in a consistent way
 */
const handleApiError = (error) => {
  if (error.response) {
    // The server responded with a status code outside the 2xx range
    const errorMessage = error.response.data.detail || 'An error occurred';
    return {
      status: error.response.status,
      message: errorMessage,
      data: error.response.data
    };
  } else if (error.request) {
    // The request was made but no response was received
    return {
      status: 0,
      message: 'No response from server. Please check your connection.',
      data: null
    };
  } else {
    // Something happened in setting up the request that triggered an Error
    return {
      status: 0,
      message: error.message || 'An unexpected error occurred',
      data: null
    };
  }
};