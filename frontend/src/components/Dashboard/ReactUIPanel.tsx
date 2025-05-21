/**
 * React UI Panel Component
 * 
 * Central management panel for SQL Proxy services and PowerBI integrations
 * 
 * Last updated: 2025-05-21 06:48:31
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Badge,
  Chip,
  Tooltip,
  CircularProgress,
  Alert,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import { useQuery } from 'react-query';
import RefreshIcon from '@mui/icons-material/Refresh';
import SettingsIcon from '@mui/icons-material/Settings';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import BarChartIcon from '@mui/icons-material/BarChart';
import StorageIcon from '@mui/icons-material/Storage';
import TimelineIcon from '@mui/icons-material/Timeline';
import CloudSyncIcon from '@mui/icons-material/CloudSync';
import { useNavigate } from 'react-router-dom';

import { systemApi } from '../../services/systemService';
import { powerbiApi } from '../../services/powerbiService';
import SystemStatusChart from './SystemStatusChart';
import SystemResourcesChart from './SystemResourcesChart';

// Define service types and statuses for type safety
type ServiceStatus = 'healthy' | 'warning' | 'error' | 'unknown';
type ServiceType = 'powerbi' | 'database' | 'query' | 'auth' | 'scheduler' | 'notification';

interface ServiceInfo {
  id: string;
  name: string;
  type: ServiceType;
  status: ServiceStatus;
  lastChecked: string;
  metrics: {
    responseTime?: number;
    uptime?: number;
    errorRate?: number;
    activeConnections?: number;
    queueSize?: number;
  };
  details?: string;
}

const ReactUIPanel: React.FC = () => {
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds
  const navigate = useNavigate();

  // Query system status
  const { 
    data: systemStatus,
    isLoading: isLoadingStatus,
    error: statusError,
    refetch: refetchStatus
  } = useQuery(
    ['system-status'],
    systemApi.getSystemStatus,
    {
      refetchInterval: refreshInterval,
      staleTime: refreshInterval - 5000
    }
  );

  // Query PowerBI integration status
  const {
    data: powerbiStatus,
    isLoading: isLoadingPowerBI,
    error: powerbiError,
    refetch: refetchPowerBI
  } = useQuery(
    ['powerbi-status'],
    powerbiApi.getStatus,
    {
      refetchInterval: refreshInterval,
      staleTime: refreshInterval - 5000
    }
  );

  // Manually refresh all status data
  const handleRefresh = () => {
    refetchStatus();
    refetchPowerBI();
  };

  // Get status indicator color
  const getStatusColor = (status: ServiceStatus) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  // Calculate overall system health
  const getOverallHealth = () => {
    if (!systemStatus?.services || systemStatus.services.length === 0) 
      return 'unknown';
    
    const statuses = systemStatus.services.map(s => s.status);
    
    if (statuses.includes('error')) return 'error';
    if (statuses.includes('warning')) return 'warning';
    return 'healthy';
  };

  // Get status icon
  const getStatusIcon = (status: ServiceStatus) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon color="success" />;
      case 'warning': return <ErrorIcon color="warning" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <CircularProgress size={20} />;
    }
  };

  // Loading state
  if (isLoadingStatus && isLoadingPowerBI) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (statusError || powerbiError) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Error loading system status: {((statusError as Error)?.message || (powerbiError as Error)?.message || 'Unknown error')}
      </Alert>
    );
  }

  // Get services from status data
  const services: ServiceInfo[] = systemStatus?.services || [];
  const powerbiServices = powerbiStatus?.services || [];
  
  // Combine all services
  const allServices = [...services, ...powerbiServices];

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          System Dashboard
        </Typography>
        
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          
          <Button
            variant="contained"
            startIcon={<SettingsIcon />}
            onClick={() => navigate('/settings')}
          >
            Settings
          </Button>
        </Box>
      </Box>

      {/* System Overview Card */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardHeader 
              title="System Status" 
              subheader={`Last updated: ${new Date().toLocaleTimeString()}`}
              avatar={
                <Chip 
                  label={getOverallHealth().toUpperCase()} 
                  color={getStatusColor(getOverallHealth() as ServiceStatus)} 
                />
              }
            />
            <Divider />
            <CardContent>
              <SystemStatusChart 
                services={allServices} 
                height={200}
              />
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Service Status Summary
                </Typography>
                
                <Grid container spacing={1}>
                  <Grid item xs={4}>
                    <Paper variant="outlined" sx={{ p: 1, textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {allServices.filter(s => s.status === 'healthy').length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Healthy
                      </Typography>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={4}>
                    <Paper variant="outlined" sx={{ p: 1, textAlign: 'center' }}>
                      <Typography variant="h4" color="warning.main">
                        {allServices.filter(s => s.status === 'warning').length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Warnings
                      </Typography>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={4}>
                    <Paper variant="outlined" sx={{ p: 1, textAlign: 'center' }}>
                      <Typography variant="h4" color="error.main">
                        {allServices.filter(s => s.status === 'error').length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Errors
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardHeader 
              title="System Resources" 
              subheader="CPU, Memory, and Storage Usage"
              action={
                <Tooltip title="View Details">
                  <IconButton size="small" onClick={() => navigate('/system/resources')}>
                    <TimelineIcon />
                  </IconButton>
                </Tooltip>
              }
            />
            <Divider />
            <CardContent>
              <SystemResourcesChart 
                data={systemStatus?.resources || {}}
                height={250}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Services Status */}
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Services Status
        </Typography>
        
        <Grid container spacing={2}>
          {/* Core Services */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Core Services" 
                subheader="Database, Query, and Authentication Services"
              />
              <Divider />
              <List disablePadding>
                {services.map((service) => (
                  <React.Fragment key={service.id}>
                    <ListItem
                      secondaryAction={
                        <Chip 
                          label={service.status.toUpperCase()} 
                          color={getStatusColor(service.status)} 
                          size="small"
                        />
                      }
                    >
                      <ListItemIcon>
                        {getStatusIcon(service.status)}
                      </ListItemIcon>
                      <ListItemText 
                        primary={service.name}
                        secondary={`Last checked: ${new Date(service.lastChecked).toLocaleTimeString()}`}
                      />
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            </Card>
          </Grid>
          
          {/* PowerBI Services */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="PowerBI Integration" 
                subheader="PowerBI API and Connector Services"
                action={
                  <Tooltip title="PowerBI Settings">
                    <IconButton size="small" onClick={() => navigate('/powerbi/settings')}>
                      <SettingsIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                }
              />
              <Divider />
              <List disablePadding>
                {powerbiServices.map((service) => (
                  <React.Fragment key={service.id}>
                    <ListItem
                      secondaryAction={
                        <Chip 
                          label={service.status.toUpperCase()} 
                          color={getStatusColor(service.status)} 
                          size="small"
                        />
                      }
                    >
                      <ListItemIcon>
                        {getStatusIcon(service.status)}
                      </ListItemIcon>
                      <ListItemText 
                        primary={service.name}
                        secondary={service.details || `Last checked: ${new Date(service.lastChecked).toLocaleTimeString()}`}
                      />
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
                
                {powerbiServices.length === 0 && (
                  <ListItem>
                    <ListItemText 
                      primary="No PowerBI services configured"
                      secondary="Please configure PowerBI integration in settings"
                    />
                  </ListItem>
                )}
              </List>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Recent Activity */}
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Activity
        </Typography>
        
        <Card variant="outlined">
          <CardContent>
            <RecentActivityList systemStatus={systemStatus} />
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

// Recent Activity sub-component
const RecentActivityList: React.FC<{ systemStatus: any }> = ({ systemStatus }) => {
  const activities = systemStatus?.recentActivity || [];
  
  if (activities.length === 0) {
    return (
      <Alert severity="info">
        No recent activities to display
      </Alert>
    );
  }
  
  return (
    <List disablePadding>
      {activities.map((activity: any, index: number) => (
        <React.Fragment key={index}>
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              {activity.type === 'powerbi' ? <BarChartIcon color="primary" /> :
               activity.type === 'database' ? <StorageIcon color="secondary" /> :
               activity.type === 'sync' ? <CloudSyncIcon color="info" /> :
               <TimelineIcon />}
            </ListItemIcon>
            <ListItemText
              primary={activity.title}
              secondary={
                <React.Fragment>
                  <Typography variant="body2" component="span">
                    {activity.description}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {new Date(activity.timestamp).toLocaleString()}
                  </Typography>
                </React.Fragment>
              }
            />
          </ListItem>
          {index < activities.length - 1 && <Divider component="li" />}
        </React.Fragment>
      ))}
    </List>
  );
};

export default ReactUIPanel;

// Son güncelleme: 2025-05-21 06:48:31
// Güncelleyen: Teeksss