/**
 * Notifications Page
 * 
 * Displays and manages user notifications
 * 
 * Last updated: 2025-05-21 06:38:34
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Button,
  CircularProgress,
  Pagination,
  Chip,
  Alert,
  Card,
  CardContent
} from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoIcon from '@mui/icons-material/Info';
import PowerBIIcon from '@mui/icons-material/BarChart';
import DatabaseIcon from '@mui/icons-material/Storage';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

import { notificationApi } from '../services/notificationService';
import PageHeader from '../components/common/PageHeader';
import NotificationSettingsForm from '../components/Notifications/NotificationSettingsForm';
import NoDataPlaceholder from '../components/common/NoDataPlaceholder';
import { formatDateTime } from '../utils/formatters';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`notifications-tabpanel-${index}`}
      aria-labelledby={`notifications-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
};

const NotificationsPage: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const pageSize = 20;

  // Query for fetching notifications
  const {
    data: notifications,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['notifications', tabIndex === 0, page],
    () => notificationApi.getNotifications(tabIndex === 0, (page - 1) * pageSize, pageSize),
    {
      staleTime: 60000, // 1 minute
      keepPreviousData: true
    }
  );

  // Mutation for marking a notification as read
  const markAsReadMutation = useMutation(
    (notificationId: number) => notificationApi.markAsRead(notificationId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['notifications']);
      }
    }
  );

  // Mutation for marking all notifications as read
  const markAllAsReadMutation = useMutation(
    () => notificationApi.markAllAsRead(),
    {
      onSuccess: () => {
        toast.success('All notifications marked as read');
        queryClient.invalidateQueries(['notifications']);
      }
    }
  );

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
    setPage(1);
  };

  // Handle page change
  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  // Handle notification click
  const handleNotificationClick = (notification: any) => {
    // Mark as read
    if (!notification.is_read) {
      markAsReadMutation.mutate(notification.id);
    }
    
    // Navigate based on notification type and entity
    if (notification.entity_type && notification.entity_id) {
      switch (notification.entity_type) {
        case 'powerbi_report':
          navigate(`/powerbi/reports/${notification.entity_id}`);
          break;
        case 'powerbi_dataset':
          navigate(`/powerbi/datasets/${notification.entity_id}`);
          break;
        case 'query':
          navigate(`/query-history?query=${notification.entity_id}`);
          break;
        case 'server':
          navigate(`/servers/${notification.entity_id}`);
          break;
        default:
          // Just mark as read without navigation
          break;
      }
    }
  };

  // Get notification icon based on type
  const getNotificationIcon = (notification: any) => {
    switch (notification.notification_type) {
      case 'powerbi_refresh':
        return <PowerBIIcon color="primary" />;
      case 'system':
        return <InfoIcon color="info" />;
      case 'error':
        return <InfoIcon color="error" />;
      case 'query_complete':
        return <DatabaseIcon color="success" />;
      default:
        return <InfoIcon color="action" />;
    }
  };

  // Calculate total pages
  const totalPages = notifications ? Math.ceil(notifications.total / pageSize) : 0;

  return (
    <>
      <Helmet>
        <title>Notifications | SQL Proxy</title>
      </Helmet>

      <PageHeader
        title="Notifications"
        subtitle="Manage and view your notifications"
        actions={
          <>
            {tabIndex === 0 && notifications?.items?.length > 0 && (
              <Button
                variant="outlined"
                onClick={() => markAllAsReadMutation.mutate()}
                disabled={markAllAsReadMutation.isLoading}
                sx={{ mr: 1 }}
              >
                Mark All as Read
              </Button>
            )}
            <Button
              variant="contained"
              startIcon={<SettingsIcon />}
              onClick={() => setTabIndex(2)}
            >
              Notification Settings
            </Button>
          </>
        }
      />

      <Container maxWidth="lg">
        <Paper variant="outlined">
          <Tabs
            value={tabIndex}
            onChange={handleTabChange}
            aria-label="notifications tabs"
            sx={{ px: 2, pt: 1 }}
          >
            <Tab 
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  Unread
                  {notifications?.unread_count > 0 && (
                    <Chip 
                      label={notifications.unread_count} 
                      color="error" 
                      size="small" 
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
              } 
              id="notifications-tab-0" 
            />
            <Tab label="All Notifications" id="notifications-tab-1" />
            <Tab label="Settings" id="notifications-tab-2" />
          </Tabs>
          <Divider />
          
          <TabPanel value={tabIndex} index={0}>
            {renderNotificationsList(true)}
          </TabPanel>
          
          <TabPanel value={tabIndex} index={1}>
            {renderNotificationsList(false)}
          </TabPanel>
          
          <TabPanel value={tabIndex} index={2}>
            <NotificationSettingsForm />
          </TabPanel>
        </Paper>
      </Container>
    </>
  );

  // Function to render notifications list
  function renderNotificationsList(unreadOnly: boolean) {
    if (isLoading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      );
    }

    if (error) {
      return (
        <Alert severity="error" sx={{ m: 2 }}>
          Error loading notifications: {(error as Error).message}
        </Alert>
      );
    }

    if (!notifications?.items || notifications.items.length === 0) {
      return (
        <NoDataPlaceholder 
          message={unreadOnly ? "No unread notifications" : "No notifications found"} 
          action={
            unreadOnly && notifications?.total > 0 ? (
              <Button variant="outlined" onClick={() => setTabIndex(1)}>
                View All Notifications
              </Button>
            ) : undefined
          }
        />
      );
    }

    return (
      <>
        <List sx={{ width: '100%' }}>
          {notifications.items.map((notification: any) => (
            <React.Fragment key={notification.id}>
              <ListItem
                button
                onClick={() => handleNotificationClick(notification)}
                sx={{
                  bgcolor: !notification.is_read ? 'action.hover' : 'transparent'
                }}
              >
                <ListItemIcon>
                  {getNotificationIcon(notification)}
                </ListItemIcon>
                
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="subtitle1" component="span">
                        {notification.title}
                      </Typography>
                      {!notification.is_read && (
                        <Chip 
                          label="New" 
                          color="primary" 
                          size="small" 
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body2" component="span">
                        {notification.message}
                      </Typography>
                      <Typography 
                        variant="caption" 
                        display="block" 
                        color="text.secondary"
                        sx={{ mt: 0.5 }}
                      >
                        {formatDateTime(notification.created_at)}
                      </Typography>
                    </>
                  }
                />
                
                {!notification.is_read && (
                  <Tooltip title="Mark as Read">
                    <IconButton
                      edge="end"
                      onClick={(e) => {
                        e.stopPropagation();
                        markAsReadMutation.mutate(notification.id);
                      }}
                    >
                      <CheckCircleIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </ListItem>
              <Divider component="li" />
            </React.Fragment>
          ))}
        </List>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              color="primary"
            />
          </Box>
        )}
      </>
    );
  }
};

export default NotificationsPage;

// Son güncelleme: 2025-05-21 06:38:34
// Güncelleyen: Teeksss