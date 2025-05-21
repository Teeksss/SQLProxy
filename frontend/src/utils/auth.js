import jwtDecode from 'jwt-decode';

/**
 * Save authentication token and user info in local storage
 */
export const setAuthToken = (token, expiresAt, user) => {
  localStorage.setItem('token', token);
  localStorage.setItem('expiresAt', expiresAt);
  localStorage.setItem('user', JSON.stringify(user));
};

/**
 * Get the authentication token from local storage
 */
export const getAuthToken = () => {
  return localStorage.getItem('token');
};

/**
 * Get user info from local storage
 */
export const getUserInfo = () => {
  const userJson = localStorage.getItem('user');
  return userJson ? JSON.parse(userJson) : null;
};

/**
 * Check if the user is authenticated (has valid token)
 */
export const isAuthenticated = () => {
  const token = getAuthToken();
  const expiresAt = localStorage.getItem('expiresAt');
  
  if (!token) {
    return false;
  }
  
  // Check expiration
  if (expiresAt) {
    const now = Math.floor(Date.now() / 1000); // Current time in seconds
    if (now >= parseInt(expiresAt, 10)) {
      // Token has expired
      logout();
      return false;
    }
  }
  
  return true;
};

/**
 * Check if the current user has admin role
 */
export const isAdmin = () => {
  const user = getUserInfo();
  return user && user.role === 'admin';
};

/**
 * Logout the user by removing tokens and user info
 */
export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('expiresAt');
  localStorage.removeItem('user');
  
  // Redirect to login - use window.location for full page refresh
  window.location.href = '/login';
};

/**
 * Get user role
 */
export const getUserRole = () => {
  const user = getUserInfo();
  return user ? user.role : null;
};

/**
 * Parse JWT token
 */
export const parseJwt = (token) => {
  try {
    return jwtDecode(token);
  } catch (e) {
    return null;
  }
};