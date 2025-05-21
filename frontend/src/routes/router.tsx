/**
 * Router Configuration
 * 
 * Defines the application routes and handles authentication
 * 
 * Last updated: 2025-05-21 06:23:45
 * Updated by: Teeksss
 */

import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Layouts
import MainLayout from '../layouts/MainLayout';
import AuthLayout from '../layouts/AuthLayout';

// Pages
import Dashboard from '../pages/Dashboard';
import Login from '../pages/Login';
import Register from '../pages/Register';
import ForgotPassword from '../pages/ForgotPassword';
import QueryEditor from '../pages/QueryEditor';
import Servers from '../pages/Servers';
import ServerDetail from '../pages/ServerDetail';
import ServerCreate from '../pages/ServerCreate';
import Users from '../pages/Users';
import UserProfile from '../pages/UserProfile';
import SavedQueries from '../pages/SavedQueries';
import QueryHistory from '../pages/QueryHistory';
import BackupPage from '../pages/BackupPage';
import RestorePage from '../pages/RestorePage';
import Settings from '../pages/Settings';
import NotFound from '../pages/NotFound';
import PowerBIDashboard from '../pages/PowerBIDashboard';
import PowerBIReportDetail from '../pages/PowerBIReportDetail';
import PowerBIWorkspaceDetail from '../pages/PowerBIWorkspaceDetail';
import PowerBIDatasetDetail from '../pages/PowerBIDatasetDetail';

// Context
import { useAuth } from '../contexts/AuthContext';

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000 // 5 minutes
    }
  }
});

/**
 * Protected Route Component
 * Redirects to login if user is not authenticated
 */
const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  
  // Show loading or redirect if not authenticated
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" />;
};

/**
 * Public Route Component
 * Redirects to dashboard if user is already authenticated
 */
const PublicRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  
  // Show loading or redirect if already authenticated
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  return isAuthenticated ? <Navigate to="/dashboard" /> : <Outlet />;
};

/**
 * Admin Route Component
 * Redirects to dashboard if user is not an admin
 */
const AdminRoute: React.FC = () => {
  const { isAdmin, isLoading } = useAuth();
  
  // Show loading or redirect if not admin
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  return isAdmin ? <Outlet /> : <Navigate to="/dashboard" />;
};

// Define the router
const router = createBrowserRouter([
  // Protected routes (require authentication)
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <MainLayout />,
        children: [
          { path: '/', element: <Navigate to="/dashboard" replace /> },
          { path: '/dashboard', element: <Dashboard /> },
          { path: '/query-editor', element: <QueryEditor /> },
          { path: '/saved-queries', element: <SavedQueries /> },
          { path: '/query-history', element: <QueryHistory /> },
          { path: '/servers', element: <Servers /> },
          { path: '/servers/:serverId', element: <ServerDetail /> },
          { path: '/servers/create', element: <ServerCreate /> },
          { path: '/backups', element: <BackupPage /> },
          { path: '/restore', element: <RestorePage /> },
          { path: '/profile', element: <UserProfile /> },
          { path: '/settings', element: <Settings /> },
          
          // PowerBI routes
          { path: '/powerbi', element: <PowerBIDashboard /> },
          { path: '/powerbi/reports', element: <PowerBIDashboard /> },
          { path: '/powerbi/reports/:reportId', element: <PowerBIReportDetail /> },
          { path: '/powerbi/workspaces/:workspaceId', element: <PowerBIWorkspaceDetail /> },
          { path: '/powerbi/datasets/:datasetId', element: <PowerBIDatasetDetail /> },
          
          // Admin routes
          {
            element: <AdminRoute />,
            children: [
              { path: '/users', element: <Users /> }
            ]
          }
        ]
      }
    ]
  },
  
  // Public routes (accessible without authentication)
  {
    element: <PublicRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <Login /> },
          { path: '/register', element: <Register /> },
          { path: '/forgot-password', element: <ForgotPassword /> }
        ]
      }
    ]
  },
  
  // Catch-all route for 404
  { path: '*', element: <NotFound /> }
]);

/**
 * Router Provider Component
 * Wraps the router with necessary providers
 */
const RouterConfig: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ToastContainer position="top-right" autoClose={5000} />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
};

export default RouterConfig;

// Son güncelleme: 2025-05-21 06:23:45
// Güncelleyen: Teeksss