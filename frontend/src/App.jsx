import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from '@/components/ui/toaster';
import { isAuthenticated, isAdmin } from '@/utils/auth';

// Layouts
import AdminLayout from '@/layouts/AdminLayout';
import UserLayout from '@/layouts/UserLayout';

// Pages
import LoginPage from '@/pages/Login';
import DashboardPage from '@/pages/Dashboard';
import QueryApprovalPage from '@/pages/QueryApproval';
import RateLimitManagerPage from '@/pages/RateLimitManager';
import ServerManagementPage from '@/pages/ServerManagement';
import AuditLogPage from '@/pages/AuditLog';
import WhitelistPage from '@/pages/Whitelist';
import RoleManagementPage from '@/pages/RoleManagement';
import MaskingSettingsPage from '@/pages/MaskingSettings';
import TimeoutSettingsPage from '@/pages/TimeoutSettings';
import StatisticsPage from '@/pages/Statistics';
import HistoryPage from '@/pages/History';
import HelpPage from '@/pages/Help';
import SettingsPage from '@/pages/Settings';
import NotFoundPage from '@/pages/NotFound';

// Create a client for react-query
const queryClient = new QueryClient();

// Protected Route component for auth check
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  
  if (requireAdmin && !isAdmin()) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* User routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <UserLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="help" element={<HelpPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          
          {/* Admin routes */}
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute requireAdmin={true}>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="query-approval" element={<QueryApprovalPage />} />
            <Route path="rate-limits" element={<RateLimitManagerPage />} />
            <Route path="servers" element={<ServerManagementPage />} />
            <Route path="roles" element={<RoleManagementPage />} />
            <Route path="audit-logs" element={<AuditLogPage />} />
            <Route path="whitelist" element={<WhitelistPage />} />
            <Route path="masking" element={<MaskingSettingsPage />} />
            <Route path="timeouts" element={<TimeoutSettingsPage />} />
            <Route path="statistics" element={<StatisticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          
          {/* 404 route */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Router>
      
      <Toaster />
    </QueryClientProvider>
  );
};

// Son güncelleme: 2025-05-20 05:40:32
// Güncelleyen: Teeksss

export default App;