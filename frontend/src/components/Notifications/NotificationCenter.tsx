/**
 * Notification Center Component
 * 
 * Manages and displays user notifications throughout the application
 * 
 * Last updated: 2025-05-21 06:32:20
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Badge,
  IconButton,
  Popover,
  List,
  ListItem,
  ListItemText,
  Box,
  Typography,
  Divider,
  Button,
  CircularProgress,
  Chip,
  Tooltip,
  ListItemIcon,
  ListItemButton
} from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import PowerBIIcon from '@mui/icons-material/BarChart';
import DatabaseIcon from '@mui/icons-material/Storage';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';

import { notificationApi } from '../../services/notificationService';
import { formatRelativeTime } from '../../utils/formatters';
import NoDataPlaceholder from '../common/NoDataPlaceholder';

interface NotificationCenterProps {
  maxHeight?: number | string;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ maxHeight = 400 }) => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query for fetching notifications
  const {
    data: notifications,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['notifications', 'unread'],
    () => notificationApi.getNotifications(true),
    {
      staleTime: 60000, // 1 minute
      refetchInterval: 60000 // Poll every minute
    }
  );

  // Mutation for marking notifications as read
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
        queryClient.invalidateQueries(['notifications']);
      }
    }
  );

  // Handle click to open popover
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    refetch();
  };

  // Handle close popover
  const handleClose = () => {
    setAnchorEl(null);
  };

  // Handle click on notification
  const handleNotificationClick = (notification: any) => {
    // Mark as read
    markAsReadMutation.mutate(notification.id);
    
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
    
    handleClose();
  };

  // Handle mark all as read
  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate();
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

  // Determine if popover should be open
  const open = Boolean(anchorEl);
  const id = open ? 'notification-popover' : undefined;

  // Calculate unread count
  const unreadCount = notifications?.unread_count || 0;

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton
          color="inherit"
          onClick={handleClick}
          aria-describedby={id}
        >
          <Badge badgeContent={unreadCount} color="error">
            <NotificationsIcon />
          </Badge>
        </IconButton>
      </Tooltip>
      
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <Box sx={{ width: 360, maxWidth: '100%' }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle1">Notifications</Typography>
            
            {unreadCount > 0 && (
              <Button 
                size="small" 
                onClick={handleMarkAllAsRead}
                disabled={markAllAsReadMutation.isLoading}
              >
                Mark all as read
              </Button>
            )}
          </Box>
          
          <Divider />
          
          <Box sx={{ maxHeight, overflow: 'auto' }}>
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress size={24} />
              </Box>
            ) : error ? (
              <Box sx={{ p: 2 }}>
                <Typography color="error">
                  Failed to load notifications
                </Typography>
              </Box>
            ) : notifications?.items.length === 0 ? (
              <NoDataPlaceholder 
                message="No new notifications" 
                sx={{ py: 4 }}
              />
            ) : (
              <List disablePadding>
                {notifications?.items.map((notification: any) => (
                  <React.Fragment key={notification.id}>
                    <ListItemButton onClick={() => handleNotificationClick(notification)}>
                      <ListItemIcon>
                        {getNotificationIcon(notification)}
                      </ListItemIcon>
                      <ListItemText
                        primary={notification.title}
                        secondary={
                          <>
                            {notification.message}
                            <Typography 
                              variant="caption" 
                              display="block" 
                              color="text.secondary"
                              sx={{ mt: 0.5 }}
                            >
                              {formatRelativeTime(notification.created_at)}
                            </Typography>
                          </>
                        }
                      />
                    </ListItemButton>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            )}
          </Box>
          
          <Divider />
          
          <Box sx={{ p: 1.5, display: 'flex', justifyContent: 'center' }}>
            <Button 
              size="small" 
              onClick={() => {
                navigate('/notifications');
                handleClose();
              }}
            >
              View All Notifications
            </Button>
          </Box>
        </Box>
      </Popover>
    </>
  );
};

export default NotificationCenter;

// Son güncelleme: 2025-05-21 06:32:20
// Güncelleyen: Teeksss