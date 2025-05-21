import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Login with username and password
 */
export const login = async (username, password) => {
  try {
    // Use form-urlencoded format for OAuth2 compatibility
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    const response = await axios.post(`${API_URL}/auth/token`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    return response.data;
  } catch (error) {
    if (error.response) {
      // The server responded with an error
      const errorMessage = error.response.data.detail || 'Login failed';
      throw new Error(errorMessage);
    } else if (error.request) {
      // No response was received
      throw new Error('No response from server. Please check your connection.');
    } else {
      // Something else happened
      throw new Error('An error occurred during login.');
    }
  }
};

/**
 * Get the currently logged in user
 */
export const getCurrentUser = async () => {
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    const response = await axios.get(`${API_URL}/auth/users/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      throw new Error('Authentication expired. Please login again.');
    }
    
    throw error;
  }
};

/**
 * Test LDAP connection
 */
export const testLdapConnection = async () => {
  try {
    const response = await axios.post(`${API_URL}/auth/ldap/test-connection`);
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
    return new Error(errorMessage);
  } else if (error.request) {
    // The request was made but no response was received
    return new Error('No response from server. Please check your connection.');
  } else {
    // Something happened in setting up the request that triggered an Error
    return new Error(error.message || 'An unexpected error occurred');
  }
};