/**
 * Notification Settings Form Component
 * 
 * Form for configuring user notification preferences
 * 
 * Last updated: 2025-05-21 06:38:34
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  AlertTitle
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-toastify';

import { notificationApi } from '../../services/notificationService';

const NotificationSettingsForm: React.FC = () => {
  const [preferences, setPreferences] = useState({
    email_notifications: true,
    powerbi_refresh_notifications: true,
    query_complete_notifications: true,
    system_notifications: true
  });

  const queryClient = useQueryClient();

  // Query for fetching notification preferences
  const {
    data,
    isLoading,
    error
  } = useQuery(
    ['notification-preferences'],
    notificationApi.getPreferences,
    {
      staleTime: 300000, // 5 minutes
      onSuccess: (data) => {
        setPreferences(data);
      }
    }
  );

  // Mutation for updating notification preferences
  const updatePreferencesMutation = useMutation(
    (newPreferences: any) => notificationApi.updatePreferences(newPreferences),
    {
      onSuccess: () => {
        toast.success('Notification preferences updated successfully');
        queryClient.invalidateQueries(['notification-preferences']);
      },
      onError: (error: any) => {
        toast.error(`Error updating preferences: ${error.message}`);
      }
    }
  );

  // Handle preference change
  const handlePreferenceChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = event.target;
    setPreferences({
      ...preferences,
      [name]: checked
    });
  };

  // Handle save preferences
  const handleSavePreferences = () => {
    updatePreferencesMutation.mutate(preferences);
  };

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading notification preferences: {(error as Error).message}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Notification Preferences
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Email Notifications
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.email_notifications}
                  onChange={handlePreferenceChange}
                  name="email_notifications"
                />
              }
              label="Receive email notifications"
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
              When enabled, important notifications will be sent to your email address in addition to the in-app notifications.
            </Typography>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="subtitle1" gutterBottom>
              Notification Types
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.powerbi_refresh_notifications}
                  onChange={handlePreferenceChange}
                  name="powerbi_refresh_notifications"
                />
              }
              label="PowerBI Refresh Notifications"
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Receive notifications when PowerBI datasets are refreshed.
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.query_complete_notifications}
                  onChange={handlePreferenceChange}
                  name="query_complete_notifications"
                />
              }
              label="Query Completion Notifications"
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Receive notifications when long-running queries are completed.
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.system_notifications}
                  onChange={handlePreferenceChange}
                  name="system_notifications"
                />
              }
              label="System Notifications"
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Receive system notifications about service updates, maintenance, etc.
            </Typography>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={handleSavePreferences}
                disabled={updatePreferencesMutation.isLoading}
              >
                {updatePreferencesMutation.isLoading ? (
                  <CircularProgress size={24} />
                ) : (
                  'Save Preferences'
                )}
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                About Notifications
              </Typography>
              
              <Typography variant="body2" paragraph>
                Notifications keep you informed about important events in SQL Proxy, such as completed operations, system updates, and errors.
              </Typography>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                <AlertTitle>Email Notifications</AlertTitle>
                Email notifications are only sent for important events and require a valid email address in your profile.
              </Alert>
              
              <Typography variant="subtitle2" gutterBottom>
                Notification Categories
              </Typography>
              
              <Typography variant="body2">
                <strong>PowerBI Refresh:</strong> Dataset refresh completions and errors.
              </Typography>
              
              <Typography variant="body2">
                <strong>Query Completion:</strong> Long-running query results.
              </Typography>
              
              <Typography variant="body2">
                <strong>System:</strong> Maintenance, updates, and important announcements.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default NotificationSettingsForm;

// Son güncelleme: 2025-05-21 06:38:34
// Güncelleyen: Teeksss