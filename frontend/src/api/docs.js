import axios from 'axios';
import { API_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/auth';

// Base URL for docs API
const DOCS_API = `${API_BASE_URL}/docs`;

/**
 * Get list of available documentation categories
 * 
 * @returns {Promise<Array>} List of document categories
 */
export const getDocumentCategories = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${DOCS_API}/categories`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching document categories:', error);
    throw error;
  }
};

/**
 * Get documents in a category
 * 
 * @param {string} categoryId - Category ID
 * @returns {Promise<Array>} List of documents in the category
 */
export const getCategoryDocuments = async (categoryId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${DOCS_API}/categories/${categoryId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching documents for category ${categoryId}:`, error);
    throw error;
  }
};

/**
 * Get a specific document
 * 
 * @param {string} documentId - Document ID
 * @returns {Promise<Object>} Document content
 */
export const getDocument = async (documentId) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${DOCS_API}/${documentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching document ${documentId}:`, error);
    throw error;
  }
};

/**
 * Search documentation
 * 
 * @param {string} query - Search query
 * @returns {Promise<Array>} Search results
 */
export const searchDocumentation = async (query) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${DOCS_API}/search`, {
      params: { query },
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error searching documentation:', error);
    throw error;
  }
};

/**
 * Get commonly asked questions (FAQ)
 * 
 * @returns {Promise<Array>} List of FAQ items
 */
export const getFaq = async () => {
  const token = getAuthToken();
  
  try {
    const response = await axios.get(`${DOCS_API}/faq`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching FAQ:', error);
    throw error;
  }
};

/**
 * Get user guide
 * 
 * @param {string} section - Optional specific section
 * @returns {Promise<Object>} User guide content
 */
export const getUserGuide = async (section = null) => {
  const token = getAuthToken();
  
  try {
    const url = section ? `${DOCS_API}/guide/${section}` : `${DOCS_API}/guide`;
    
    const response = await axios.get(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching user guide:', error);
    throw error;
  }
};

/**
 * Submit feedback on documentation
 * 
 * @param {string} documentId - Document ID
 * @param {Object} feedback - Feedback data
 * @returns {Promise<Object>} Response data
 */
export const submitDocFeedback = async (documentId, feedback) => {
  const token = getAuthToken();
  
  try {
    const response = await axios.post(`${DOCS_API}/${documentId}/feedback`, feedback, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error submitting documentation feedback:', error);
    throw error;
  }
};

// Son güncelleme: 2025-05-20 05:50:02
// Güncelleyen: Teeksss