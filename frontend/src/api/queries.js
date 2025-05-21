import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for queries API
const QUERIES_API = `${API_BASE_URL}/queries`;

/**
 * Get list of available servers
 * 
 * @returns {Promise<Array>} List of server objects
 */
export const getServers = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${API_BASE_URL}/servers`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching servers:', error);
    throw error;
  }
};

/**
 * Execute a SQL query
 * 
 * @param {string} serverAlias - Server alias to run the query against
 * @param {string} sqlQuery - SQL query to execute
 * @returns {Promise<Object>} Query execution result
 */
export const executeQuery = async (serverAlias, sqlQuery) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${QUERIES_API}/execute`, {
      server_alias: serverAlias,
      sql_query: sqlQuery,
      client_ip: window.clientIP || '127.0.0.1' // Client IP for tracking
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error executing query:', error);
    throw error;
  }
};

/**
 * Get query execution history
 * 
 * @param {Object} options - Query options
 * @param {number} options.page - Page number
 * @param {number} options.limit - Results per page
 * @param {string} options.server - Filter by server
 * @param {string} options.status - Filter by status
 * @param {string} options.startDate - Filter by start date (ISO string)
 * @param {string} options.endDate - Filter by end date (ISO string)
 * @returns {Promise<Object>} Query history with pagination
 */
export const getQueryHistory = async (options = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      page: options.page || 1,
      limit: options.limit || 25,
      ...(options.server && { server: options.server }),
      ...(options.status && { status: options.status }),
      ...(options.startDate && { date_from: options.startDate }),
      ...(options.endDate && { date_to: options.endDate })
    };
    
    const response = await axios.get(`${QUERIES_API}/history`, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching query history:', error);
    throw error;
  }
};

/**
 * Request approval for a query
 * 
 * @param {Object} data - Query approval request data
 * @param {string} data.server_alias - Server alias
 * @param {string} data.sql_query - SQL query
 * @param {string} data.justification - Reason for the query
 * @param {string} data.priority - Priority level (low, normal, high, urgent)
 * @param {boolean} data.will_repeat - Whether the query will be used repeatedly
 * @returns {Promise<Object>} Approval request result
 */
export const requestQueryApproval = async (data) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${QUERIES_API}/request-approval`, data, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error requesting query approval:', error);
    throw error;
  }
};

/**
 * Check if a query requires approval
 * 
 * @param {string} serverAlias - Server alias
 * @param {string} sqlQuery - SQL query
 * @returns {Promise<Object>} Query approval status check result
 */
export const checkQueryApprovalStatus = async (serverAlias, sqlQuery) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${QUERIES_API}/check-approval`, {
      server_alias: serverAlias,
      sql_query: sqlQuery
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error checking query approval status:', error);
    throw error;
  }
};

/**
 * Get pending query approvals
 * 
 * @param {Object} options - Query options
 * @param {string} options.status - Filter by status (pending, approved, rejected)
 * @param {string} options.username - Filter by requesting username
 * @returns {Promise<Array>} List of pending approvals
 */
export const getPendingApprovals = async (options = {}) => {
  const token = getAuthToken();
  
  try {
    const params = {
      ...(options.status && { status: options.status }),
      ...(options.username && { username: options.username })
    };
    
    const response = await axios.get(`${API_BASE_URL}/admin/approvals`, {
      params,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching pending approvals:', error);
    throw error;
  }
};

/**
 * Approve a pending query
 * 
 * @param {number} queryId - Query ID to approve
 * @param {Object} options - Approval options
 * @param {boolean} options.addToWhitelist - Whether to add to whitelist
 * @param {string} options.description - Optional description for whitelist
 * @param {Array<string>} options.serverRestrictions - Optional server restrictions
 * @returns {Promise<Object>} Approval result
 */
export const approveQuery = async (queryId, options = {}) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${API_BASE_URL}/admin/approvals/${queryId}/approve`, options, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error approving query #${queryId}:`, error);
    throw error;
  }
};

/**
 * Reject a pending query
 * 
 * @param {number} queryId - Query ID to reject
 * @param {Object} options - Rejection options
 * @param {string} options.reason - Reason for rejection
 * @returns {Promise<Object>} Rejection result
 */
export const rejectQuery = async (queryId, options = {}) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${API_BASE_URL}/admin/approvals/${queryId}/reject`, options, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error rejecting query #${queryId}:`, error);
    throw error;
  }
};

/**
 * Analyze a SQL query (syntax validation and risk assessment)
 * 
 * @param {string} sqlQuery - SQL query to analyze
 * @returns {Promise<Object>} Query analysis result
 */
export const analyzeQuery = async (sqlQuery) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${QUERIES_API}/analyze`, {
      sql_query: sqlQuery
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error analyzing query:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:58:23
// Güncelleyen: Teeksss