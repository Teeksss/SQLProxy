/**
 * Authentication Context Provider for SQL Proxy Frontend
 * 
 * This component provides authentication state and methods
 * for the entire application.
 * 
 * Last updated: 2025-05-20 12:14:46
 * Updated by: Teeksss
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useMutation, useQuery } from 'react-query';
import jwt_decode from 'jwt-decode';
import { toast } from 'react-toastify';

import { authApi } from '../services/authService';
import { userApi } from '../services/userService';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { ErrorResponse } from '../types/api';

// Types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  roles: string[];
  permissions: string[];
  is_superuser: boolean;
  two_factor_enabled: boolean;
}

export interface JwtPayload {
  sub: number;
  exp: number;
  iat: number;
  roles: string[];
  permissions: string[];
  is_superuser: boolean;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitializing: boolean;
  error: string | null;
  login: (username: string, password: string, remember_me?: boolean, totp_code?: string) => Promise<void>;
  loginWithOAuth: (provider: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, username: string, password: string, full_name?: string) => Promise<void>;
  refreshUser: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  setNewPassword: (token: string, newPassword: string) => Promise<void>;
  setupTwoFactor: () => Promise<{secret: string, uri: string, qrCodeUrl: string}>;
  verifyTwoFactor: (code: string) => Promise<void>;
  disableTwoFactor: (password: string) => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider props
interface AuthProviderProps {
  children: ReactNode;
}

// Provider component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [accessToken, setAccessToken] = useLocalStorage<string | null>('auth_token', null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();

  // Check if access token is expired
  const isTokenExpired = (token: string): boolean => {
    try {
      const decoded = jwt_decode<JwtPayload>(token);
      const currentTime = Date.now() / 1000;
      return decoded.exp < currentTime;
    } catch (error) {
      return true;
    }
  };

  // Get current user data
  const fetchCurrentUser = async () => {
    if (!accessToken) return null;
    
    try {
      const response = await userApi.getCurrentUser();
      return response.data;
    } catch (error) {
      console.error('Error fetching current user:', error);
      throw error;
    }
  };

  // Use query to fetch and cache current user
  const { 
    data: userData,
    refetch: refreshUser
  } = useQuery(['currentUser', accessToken], fetchCurrentUser, {
    enabled: !!accessToken && !isTokenExpired(accessToken),
    onError: (error) => {
      console.error('Error fetching user data:', error);
      // If 401 error, token is invalid
      if ((error as ErrorResponse)?.status === 401) {
        handleLogout();
      }
    },
    onSettled: () => {
      setIsInitializing(false);
    }
  });

  // Login mutation
  const loginMutation = useMutation(
    (credentials: { username: string; password: string; remember_me?: boolean; totp_code?: string }) => 
      authApi.login(credentials.username, credentials.password, credentials.remember_me, credentials.totp_code),
    {
      onSuccess: (data) => {
        setAccessToken(data.access_token);
        refreshUser();
        
        // Redirect to intended page or dashboard
        const { from } = location.state as { from?: { pathname: string } } || { from: { pathname: '/dashboard' } };
        navigate(from?.pathname || '/dashboard');
        
        toast.success('Login successful!');
      },
      onError: (error: any) => {
        console.error('Login error:', error);
        
        // Handle 2FA required
        if (error.response?.headers?.['x-requires-2fa']) {
          setError('two_factor_required');
          return;
        }
        
        setError(error.response?.data?.detail || 'Login failed. Please check your credentials.');
        toast.error(error.response?.data?.detail || 'Login failed. Please check your credentials.');
      }
    }
  );

  // OAuth login mutation
  const oauthLoginMutation = useMutation(
    ({ provider, code }: { provider: string; code: string }) => 
      authApi.loginWithOAuth(provider, code, window.location.origin + '/oauth/callback'),
    {
      onSuccess: (data) => {
        setAccessToken(data.access_token);
        refreshUser();
        navigate('/dashboard');
        toast.success('Login successful!');
      },
      onError: (error: any) => {
        console.error('OAuth login error:', error);
        setError(error.response?.data?.detail || 'OAuth login failed.');
        toast.error(error.response?.data?.detail || 'OAuth login failed.');
        navigate('/login');
      }
    }
  );

  // Register mutation
  const registerMutation = useMutation(
    (userData: { email: string; username: string; password: string; full_name?: string }) => 
      authApi.register(userData.email, userData.username, userData.password, userData.full_name),
    {
      onSuccess: () => {
        toast.success('Registration successful! Please check your email to verify your account.');
        navigate('/login');
      },
      onError: (error: any) => {
        console.error('Registration error:', error);
        setError(error.response?.data?.detail || 'Registration failed. Please try again.');
        toast.error(error.response?.data?.detail || 'Registration failed. Please try again.');
      }
    }
  );

  // Reset password mutation
  const resetPasswordMutation = useMutation(
    (email: string) => authApi.resetPassword(email),
    {
      onSuccess: () => {
        toast.success('If your email is registered, you will receive password reset instructions.');
      },
      onError: (error: any) => {
        // Still show success to prevent email enumeration
        toast.success('If your email is registered, you will receive password reset instructions.');
        console.error('Reset password error:', error);
      }
    }
  );

  // Set new password mutation
  const setNewPasswordMutation = useMutation(
    ({ token, newPassword }: { token: string; newPassword: string }) => 
      authApi.setNewPassword(token, newPassword),
    {
      onSuccess: () => {
        toast.success('Password has been reset successfully! You can now log in with your new password.');
        navigate('/login');
      },
      onError: (error: any) => {
        console.error('Set new password error:', error);
        setError(error.response?.data?.detail || 'Failed to reset password. The link may be expired or invalid.');
        toast.error(error.response?.data?.detail || 'Failed to reset password. The link may be expired or invalid.');
      }
    }
  );

  // Two-factor setup mutation
  const setupTwoFactorMutation = useMutation(
    () => authApi.setupTwoFactor(),
    {
      onError: (error: any) => {
        console.error('Two-factor setup error:', error);
        toast.error(error.response?.data?.detail || 'Failed to set up two-factor authentication.');
      }
    }
  );

  // Two-factor verification mutation
  const verifyTwoFactorMutation = useMutation(
    (code: string) => authApi.verifyTwoFactor(code),
    {
      onSuccess: () => {
        toast.success('Two-factor authentication enabled successfully!');
        refreshUser();
      },
      onError: (error: any) => {
        console.error('Two-factor verification error:', error);
        toast.error(error.response?.data?.detail || 'Invalid verification code.');
      }
    }
  );

  // Disable two-factor mutation
  const disableTwoFactorMutation = useMutation(
    (password: string) => authApi.disableTwoFactor(password),
    {
      onSuccess: () => {
        toast.success('Two-factor authentication disabled successfully!');
        refreshUser();
      },
      onError: (error: any) => {
        console.error('Disable two-factor error:', error);
        toast.error(error.response?.data?.detail || 'Failed to disable two-factor authentication.');
      }
    }
  );

  // Update user state when userData changes
  useEffect(() => {
    if (userData) {
      setUser(userData);
    } else if (!isInitializing && !accessToken) {
      setUser(null);
    }
  }, [userData, accessToken, isInitializing]);

  // Check token expiration
  useEffect(() => {
    if (accessToken && isTokenExpired(accessToken)) {
      handleLogout();
    }
  }, [accessToken]);

  // Handle login
  const handleLogin = async (
    username: string, 
    password: string, 
    remember_me: boolean = false, 
    totp_code?: string
  ) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await loginMutation.mutateAsync({ username, password, remember_me, totp_code });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle OAuth login
  const handleOAuthLogin = async (provider: string, code: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await oauthLoginMutation.mutateAsync({ provider, code });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle logout
  const handleLogout = async () => {
    setIsLoading(true);
    
    try {
      if (accessToken) {
        await authApi.logout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setAccessToken(null);
      setUser(null);
      setIsLoading(false);
      navigate('/login');
    }
  };

  // Handle register
  const handleRegister = async (
    email: string, 
    username: string, 
    password: string, 
    full_name?: string
  ) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await registerMutation.mutateAsync({ email, username, password, full_name });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle password reset
  const handleResetPassword = async (email: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await resetPasswordMutation.mutateAsync(email);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle set new password
  const handleSetNewPassword = async (token: string, newPassword: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await setNewPasswordMutation.mutateAsync({ token, newPassword });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle two-factor setup
  const handleSetupTwoFactor = async () => {
    setIsLoading(true);
    
    try {
      const result = await setupTwoFactorMutation.mutateAsync();
      return result;
    } finally {
      setIsLoading(false);
    }
  };

  // Handle two-factor verification
  const handleVerifyTwoFactor = async (code: string) => {
    setIsLoading(true);
    
    try {
      await verifyTwoFactorMutation.mutateAsync(code);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle disable two-factor
  const handleDisableTwoFactor = async (password: string) => {
    setIsLoading(true);
    
    try {
      await disableTwoFactorMutation.mutateAsync(password);
    } finally {
      setIsLoading(false);
    }
  };

  // Check if user has permission
  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    // Super users have all permissions
    if (user.is_superuser) return true;
    
    return user.permissions.includes(permission);
  };

  // Check if user has role
  const hasRole = (role: string): boolean => {
    if (!user) return false;
    
    // Super users have all roles
    if (user.is_superuser) return true;
    
    return user.roles.includes(role);
  };

  const refreshUserData = async () => {
    try {
      await refreshUser();
    } catch (error) {
      console.error('Error refreshing user data:', error);
    }
  };

  // Context value
  const contextValue: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    isInitializing,
    error,
    login: handleLogin,
    loginWithOAuth: handleOAuthLogin,
    logout: handleLogout,
    register: handleRegister,
    refreshUser: refreshUserData,
    resetPassword: handleResetPassword,
    setNewPassword: handleSetNewPassword,
    setupTwoFactor: handleSetupTwoFactor,
    verifyTwoFactor: handleVerifyTwoFactor,
    disableTwoFactor: handleDisableTwoFactor,
    hasPermission,
    hasRole
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook for using auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

// Son güncelleme: 2025-05-20 12:14:46
// Güncelleyen: Teeksss