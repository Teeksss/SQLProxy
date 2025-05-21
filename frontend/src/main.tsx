/**
 * Main entry point for SQL Proxy frontend
 * 
 * This file initializes the React application and sets up
 * the main providers for routing, state management, and theming.
 * 
 * Last updated: 2025-05-20 12:00:43
 * Updated by: Teeksss
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { SnackbarProvider } from 'notistack';

import App from './App';
import { store } from './store';
import { theme } from './theme';
import { AuthProvider } from './contexts/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { initAnalytics } from './utils/analytics';
import { setupAxiosInterceptors } from './utils/api';

// Initialize analytics
initAnalytics();

// Setup axios interceptors for API calls
setupAxiosInterceptors();

// Create React root
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Render the application
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <Provider store={store}>
        <BrowserRouter>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <SnackbarProvider 
                maxSnack={3} 
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                autoHideDuration={5000}
              >
                <AuthProvider>
                  <App />
                </AuthProvider>
              </SnackbarProvider>
            </LocalizationProvider>
          </ThemeProvider>
        </BrowserRouter>
      </Provider>
    </ErrorBoundary>
  </React.StrictMode>
);

// Son güncelleme: 2025-05-20 12:00:43
// Güncelleyen: Teeksss