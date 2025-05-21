/**
 * Notifications List Component
 * 
 * Displays a list of user notifications with filtering and pagination
 * 
 * Last updated: 2025-05-21 06:42:20
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Box,
  Typography,
  Divider,
  Chip,
  IconButton,
  CircularProgress,
  Pagination,
  Alert,
  Paper,
  Button,
  Tooltip
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoIcon from '@mui/icons-material/Info';
import ErrorIcon from '@mui/icons-material/Error';
import PowerBIIcon from '@mui/icons-material/BarChart';
import DatabaseIcon from '@mui/icons-material/Storage';
import DeleteIcon from '@mui/icons-material/Delete';
import { toast } from 'react-toastify';

import { notificationApi } from '../../services/notificationService';
import NoDataPlaceholder from '../common/NoDataPlaceholder';
import { formatDateTime } from '../../utils/formatters';

interface NotificationsListProps {
  unreadOnly?: boolean;
  limit?: number;
  maxHeight?: number | string;
  onNotificationClick?: (notification: any) => void;
}

const NotificationsList: React.FC<NotificationsListProps> = ({
  unreadOnly = false,
  limit = 10,
  maxHeight,
  onNotificationClick
}) => {
  const [page, setPage] = useState(1);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query for fetching notifications
  const {
    data: notifications,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['notifications', unreadOnly, page, limit],
    () => notificationApi.getNotifications(unreadOnly, (page - 1) * limit, limit),
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

  // Mutation for deleting a notification
  const deleteNotificationMutation = useMutation(
    (notificationId: number) => notificationApi.deleteNotification(notificationId),
    {
      onSuccess: () => {
        toast.success('Notification deleted');
        queryClient.invalidateQueries(['notifications']);
      }
    }
  );

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
    
    // If custom handler provided, use it
    if (onNotificationClick) {
      onNotificationClick(notification);
      return;
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

  // Handle delete notification
  const handleDeleteNotification = (event: React.MouseEvent, notificationId: number) => {
    event.stopPropagation();
    deleteNotificationMutation.mutate(notificationId);
  };

  // Get notification icon based on type
  const getNotificationIcon = (notification: any) => {
    switch (notification.notification_type) {
      case 'powerbi_refresh':
        return <PowerBIIcon color="primary" />;
      case 'system':
        return <InfoIcon color="info" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'query_complete':
        return <DatabaseIcon color="success" />;
      default:
        return <InfoIcon color="action" />;
    }
  };

  // Calculate total pages
  const totalPages = notifications ? Math.ceil(notifications.total / limit) : 0;

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading notifications: {(error as Error).message}
      </Alert>
    );
  }

  // No notifications
  if (!notifications?.items || notifications.items.length === 0) {
    return (
      <NoDataPlaceholder 
        message={unreadOnly ? "No unread notifications" : "No notifications found"} 
        sx={{ py: 3 }}
      />
    );
  }

  return (
    <Box>
      <Box sx={{ maxHeight, overflow: 'auto' }}>
        <List disablePadding>
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
                
                <Box>
                  {!notification.is_read && (
                    <Tooltip title="Mark as Read">
                      <IconButton
                        edge="end"
                        onClick={(e) => {
                          e.stopPropagation();
                          markAsReadMutation.mutate(notification.id);
                        }}
                        sx={{ mr: 1 }}
                      >
                        <CheckCircleIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  <Tooltip title="Delete">
                    <IconButton
                      edge="end"
                      onClick={(e) => handleDeleteNotification(e, notification.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </ListItem>
              <Divider component="li" />
            </React.Fragment>
          ))}
        </List>
      </Box>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
            size="small"
          />
        </Box>
      )}
    </Box>
  );
};

export default NotificationsList;

// Son güncelleme: 2025-05-21 06:42:20
// Güncelleyen: Teeksss