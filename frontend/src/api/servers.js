import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Get all server configurations
 */
export const getServers = async () => {
  try {
    const response = await axios.get(`${API_URL}/admin/servers`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Create a new server configuration
 */
export const createServer = async (serverData) => {
  try {
    const response = await axios.post(`${API_URL}/admin/servers`, serverData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Update an existing server configuration
 */
export const updateServer = async (serverId, serverData) => {
  try {
    const response = await axios.put(`${API_URL}/admin/servers/${serverId}`, serverData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Delete a server configuration
 */
export const deleteServer = async (serverId) => {
  try {
    const response = await axios.delete(`${API_URL}/admin/servers/${serverId}`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Test connection to a database server
 */
export const testServerConnection = async (connectionData) => {
  try {
    const response = await axios.post(`${API_URL}/admin/servers/test-connection`, connectionData);
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