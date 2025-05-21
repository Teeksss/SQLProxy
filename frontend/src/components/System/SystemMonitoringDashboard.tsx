/**
 * System Monitoring Dashboard Component
 * 
 * Dashboard for monitoring system status, resources, and health
 * 
 * Last updated: 2025-05-21 06:58:56
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardHeader,
  CardContent,
  Typography,
  Divider,
  CircularProgress,
  LinearProgress,
  Alert,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { useQuery } from 'react-query';
import RefreshIcon from '@mui/icons-material/Refresh';
import BarChartIcon from '@mui/icons-material/BarChart';
import StorageIcon from '@mui/icons-material/Storage';
import MemoryIcon from '@mui/icons-material/Memory';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import SpeedIcon from '@mui/icons-material/Speed';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TimelineIcon from '@mui/icons-material/Timeline';
import { useTheme } from '@mui/material/styles';

// Charts
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

// Services
import { systemApi } from '../../services/systemService';

// Types
interface ResourceUsage {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  timestamp: string;
}

interface ServiceStatus {
  id: string;
  name: string;
  type: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  lastChecked: string;
  metrics?: {
    responseTime?: number;
    uptime?: number;
    errorRate?: number;
  };
}

interface SystemMetrics {
  resources: ResourceUsage[];
  services: ServiceStatus[];
  queries: {
    total: number;
    succeeded: number;
    failed: number;
    avgExecutionTime: number;
  };
  storage: {
    total: number;
    used: number;
    free: number;
  };
  alerts: {
    critical: number;
    warning: number;
    info: number;
  };
}

// System Monitoring Dashboard Component
const SystemMonitoringDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState<string>('1h');
  const theme = useTheme();

  // Query for system metrics
  const {
    data: metrics,
    isLoading,
    error,
    refetch
  } = useQuery<SystemMetrics>(['system-metrics', timeRange], () => systemApi.getSystemMetrics(timeRange), {
    refetchInterval: 60000, // Refresh every minute
    staleTime: 55000
  });

  // Compute overall system health status
  const getSystemHealth = (): 'healthy' | 'warning' | 'error' | 'unknown' => {
    if (!metrics?.services.length) return 'unknown';
    
    const statuses = metrics.services.map(s => s.status);
    if (statuses.includes('error')) return 'error';
    if (statuses.includes('warning')) return 'warning';
    if (statuses.includes('unknown')) return 'unknown';
    return 'healthy';
  };

  // Status to color mapping
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy': return theme.palette.success.main;
      case 'warning': return theme.palette.warning.main;
      case 'error': return theme.palette.error.main;
      default: return theme.palette.grey[500];
    }
  };

  // Status to icon mapping
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon color="success" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <CircularProgress size={20} />;
    }
  };

  // Format byte values to human-readable format
  const formatBytes = (bytes: number, decimals = 2): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  // Handle time range change
  const handleTimeRangeChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setTimeRange(event.target.value as string);
  };

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Error loading system metrics: {(error as Error).message}
      </Alert>
    );
  }

  // Mock data if metrics not available
  const resourceData = metrics?.resources || Array(24).fill(0).map((_, i) => ({
    cpu: Math.random() * 80 + 10,
    memory: Math.random() * 70 + 20,
    disk: 45 + Math.random() * 10,
    network: Math.random() * 60 + 10,
    timestamp: new Date(Date.now() - (23 - i) * 60000).toISOString()
  }));

  const serviceStatuses = metrics?.services || [
    { id: '1', name: 'Database Service', type: 'database', status: 'healthy', lastChecked: new Date().toISOString() },
    { id: '2', name: 'PowerBI Connector', type: 'powerbi', status: 'healthy', lastChecked: new Date().toISOString() },
    { id: '3', name: 'Query Engine', type: 'query', status: 'healthy', lastChecked: new Date().toISOString() },
    { id: '4', name: 'Authentication Service', type: 'auth', status: 'healthy', lastChecked: new Date().toISOString() }
  ];

  // Prepare data for charts
  const cpuMemoryData = resourceData.map(r => ({
    timestamp: new Date(r.timestamp).toLocaleTimeString(),
    CPU: Math.round(r.cpu),
    Memory: Math.round(r.memory)
  }));

  const diskNetworkData = resourceData.map(r => ({
    timestamp: new Date(r.timestamp).toLocaleTimeString(),
    Disk: Math.round(r.disk),
    Network: Math.round(r.network)
  }));

  const storageData = [
    { name: 'Used', value: metrics?.storage?.used || 70 },
    { name: 'Free', value: metrics?.storage?.free || 30 }
  ];

  const queryData = [
    { name: 'Succeeded', value: metrics?.queries?.succeeded || 85 },
    { name: 'Failed', value: metrics?.queries?.failed || 15 }
  ];

  const chartColors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.error.main
  ];

  const systemHealth = getSystemHealth();

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          System Monitoring
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="time-range-label">Time Range</InputLabel>
            <Select
              labelId="time-range-label"
              value={timeRange}
              onChange={handleTimeRangeChange as any}
              label="Time Range"
            >
              <MenuItem value="1h">Last Hour</MenuItem>
              <MenuItem value="6h">Last 6 Hours</MenuItem>
              <MenuItem value="24h">Last 24 Hours</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh Metrics">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* System Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ py: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ mr: 2 }}>
                  <SpeedIcon fontSize="large" color="primary" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">System Health</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {getStatusIcon(systemHealth)}
                    <Typography variant="h5" sx={{ ml: 1, fontWeight: 'bold' }}>
                      {systemHealth.toUpperCase()}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ py: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ mr: 2 }}>
                  <MemoryIcon fontSize="large" color="primary" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">CPU Usage</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                    {Math.round(resourceData[resourceData.length - 1]?.cpu || 0)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={resourceData[resourceData.length - 1]?.cpu || 0} 
                    color={resourceData[resourceData.length - 1]?.cpu > 80 ? "error" : "primary"}
                    sx={{ mt: 1, height: 6, borderRadius: 3 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ py: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ mr: 2 }}>
                  <StorageIcon fontSize="large" color="primary" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Memory Usage</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                    {Math.round(resourceData[resourceData.length - 1]?.memory || 0)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={resourceData[resourceData.length - 1]?.memory || 0} 
                    color={resourceData[resourceData.length - 1]?.memory > 80 ? "error" : "primary"}
                    sx={{ mt: 1, height: 6, borderRadius: 3 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent sx={{ py: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ mr: 2 }}>
                  <BarChartIcon fontSize="large" color="primary" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Active Queries</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                    {metrics?.queries?.total || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Avg. Time: {metrics?.queries?.avgExecutionTime?.toFixed(2) || 0} ms
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* CPU & Memory Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardHeader 
              title="Resource Usage Over Time" 
              subheader={`Last ${timeRange} of CPU and Memory usage`}
              action={
                <IconButton size="small" onClick={() => refetch()}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <Divider />
            <CardContent>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={cpuMemoryData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis 
                      label={{ value: 'Usage %', angle: -90, position: 'insideLeft' }} 
                      domain={[0, 100]} 
                    />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="CPU" stroke={theme.palette.primary.main} activeDot={{ r: 8 }} strokeWidth={2} />
                    <Line type="monotone" dataKey="Memory" stroke={theme.palette.secondary.main} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Services Status */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: '100%' }}>
            <CardHeader 
              title="Services Status" 
              action={
                <IconButton size="small" onClick={() => refetch()}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <Divider />
            <CardContent sx={{ overflowY: 'auto', maxHeight: 300 }}>
              {serviceStatuses.map((service) => (
                <Box key={service.id} sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                  {getStatusIcon(service.status)}
                  <Box sx={{ ml: 1, flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography variant="subtitle2">{service.name}</Typography>
                      <Chip 
                        label={service.status.toUpperCase()} 
                        size="small" 
                        sx={{ 
                          bgcolor: getStatusColor(service.status),
                          color: '#fff',
                          height: 20,
                          fontSize: '0.7rem'
                        }} 
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Last checked: {new Date(service.lastChecked).toLocaleTimeString()}
                    </Typography>
                    {service.metrics?.responseTime && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Response time: {service.metrics.responseTime} ms
                      </Typography>
                    )}
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Storage Utilization */}
        <Grid item xs={12} md={6} lg={4}>
          <Card>
            <CardHeader title="Storage Utilization" />
            <Divider />
            <CardContent>
              <Box sx={{ height: 250, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={storageData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {storageData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={index === 0 ? theme.palette.primary.main : theme.palette.success.light} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
                <Typography variant="body2" align="center" color="text.secondary">
                  Total Space: {formatBytes(metrics?.storage?.total || 1024 * 1024 * 1024 * 100)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Query Success Rate */}
        <Grid item xs={12} md={6} lg={4}>
          <Card>
            <CardHeader title="Query Success Rate" />
            <Divider />
            <CardContent>
              <Box sx={{ height: 250, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={queryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      <Cell fill={theme.palette.success.main} />
                      <Cell fill={theme.palette.error.main} />
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
                <Typography variant="body2" align="center" color="text.secondary">
                  Total Queries: {metrics?.queries?.total || 100}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Network & Disk Chart */}
        <Grid item xs={12} md={12} lg={4}>
          <Card>
            <CardHeader 
              title="Disk & Network Usage" 
              action={
                <IconButton size="small" onClick={() => refetch()}>
                  <RefreshIcon />
                </IconButton>
              }
            />
            <Divider />
            <CardContent>
              <Box sx={{ height: 250 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={diskNetworkData.slice(-10)}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis domain={[0, 100]} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="Disk" stroke={theme.palette.info.main} strokeWidth={2} />
                    <Line type="monotone" dataKey="Network" stroke={theme.palette.warning.main} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Alerts */}
      {(metrics?.alerts?.critical || metrics?.alerts?.warning) && (
        <Card sx={{ mt: 3 }}>
          <CardHeader 
            title="System Alerts" 
            subheader={`${metrics?.alerts?.critical || 0} critical, ${metrics?.alerts?.warning || 0} warnings`}
          />
          <Divider />
          <CardContent>
            {metrics?.alerts?.critical > 0 && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Critical: High CPU usage detected (95%). System performance may be degraded.
              </Alert>
            )}
            {metrics?.alerts?.warning > 0 && (
              <Alert severity="warning">
                Warning: Database disk usage is approaching 80% threshold.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default SystemMonitoringDashboard;

// Son güncelleme: 2025-05-21 06:58:56
// Güncelleyen: Teeksss