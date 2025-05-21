/**
 * System Monitoring Dashboard Component
 * 
 * Displays real-time system metrics and resource utilization
 * 
 * Last updated: 2025-05-21 05:32:06
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  CircularProgress,
  LinearProgress,
  Divider,
  Paper,
  Tabs,
  Tab,
  Alert,
  Button,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import RefreshIcon from '@mui/icons-material/Refresh';
import TimelineIcon from '@mui/icons-material/Timeline';
import { useQuery } from 'react-query';

import { metricsApi } from '../../services/metricsService';
import { formatFileSize, formatNumber } from '../../utils/formatters';
import { theme } from '../../theme';
import CircularProgressWithLabel from '../common/CircularProgressWithLabel';
import NoDataPlaceholder from '../common/NoDataPlaceholder';

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
      id={`system-tabpanel-${index}`}
      aria-labelledby={`system-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 1 }}>{children}</Box>}
    </div>
  );
};

const SystemMonitoringDashboard: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [refreshInterval, setRefreshInterval] = useState<number>(10000); // 10 seconds
  const [historyData, setHistoryData] = useState<any[]>([]);
  
  // Query for fetching system metrics
  const {
    data: systemMetrics,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['systemMetrics'],
    metricsApi.getSystemMetrics,
    {
      refetchInterval: refreshInterval,
      onSuccess: (data) => {
        // Add data point to history
        const timestamp = new Date().toISOString();
        
        // Limit history to 30 data points
        const newHistory = [...historyData, { ...data, timestamp }];
        if (newHistory.length > 30) {
          newHistory.shift();
        }
        
        setHistoryData(newHistory);
      }
    }
  );
  
  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };
  
  // Handle refresh interval change
  const handleRefreshIntervalChange = (event: SelectChangeEvent<number>) => {
    setRefreshInterval(event.target.value as number);
  };
  
  // Format metrics for charts
  const cpuHistoryData = React.useMemo(() => {
    return historyData.map((point, index) => ({
      name: index,
      value: point.cpu?.usage_percent || 0,
      timestamp: point.timestamp
    }));
  }, [historyData]);
  
  const memoryHistoryData = React.useMemo(() => {
    return historyData.map((point, index) => ({
      name: index,
      used: point.memory?.used || 0,
      free: point.memory?.free || 0,
      total: point.memory?.total || 0,
      percentage: point.memory?.usage_percent || 0,
      timestamp: point.timestamp
    }));
  }, [historyData]);
  
  const diskHistoryData = React.useMemo(() => {
    return historyData.map((point, index) => ({
      name: index,
      used: point.disk?.used || 0,
      free: point.disk?.free || 0,
      total: point.disk?.total || 0,
      percentage: point.disk?.usage_percent || 0,
      timestamp: point.timestamp
    }));
  }, [historyData]);
  
  const networkHistoryData = React.useMemo(() => {
    // Calculate delta between points for sent/received bytes
    const result = historyData.map((point, index) => {
      const prevPoint = index > 0 ? historyData[index - 1] : null;
      
      let sentDelta = 0;
      let receivedDelta = 0;
      
      if (prevPoint && point.network && prevPoint.network) {
        sentDelta = Math.max(0, (point.network.sent || 0) - (prevPoint.network.sent || 0));
        receivedDelta = Math.max(0, (point.network.received || 0) - (prevPoint.network.received || 0));
      }
      
      return {
        name: index,
        sent: sentDelta,
        received: receivedDelta,
        timestamp: point.timestamp
      };
    });
    
    // Skip first item as it has no delta
    return result.slice(1);
  }, [historyData]);
  
  // Loading state
  if (isLoading && !systemMetrics) {
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
        Error loading system metrics: {(error as Error).message}
      </Alert>
    );
  }
  
  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          System Monitoring
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel id="refresh-interval-label">Refresh Rate</InputLabel>
            <Select
              labelId="refresh-interval-label"
              id="refresh-interval"
              value={refreshInterval}
              label="Refresh Rate"
              onChange={handleRefreshIntervalChange}
            >
              <MenuItem value={5000}>5 seconds</MenuItem>
              <MenuItem value={10000}>10 seconds</MenuItem>
              <MenuItem value={30000}>30 seconds</MenuItem>
              <MenuItem value={60000}>1 minute</MenuItem>
              <MenuItem value={300000}>5 minutes</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh Now">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* System Overview Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                CPU Usage
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                <CircularProgressWithLabel
                  value={systemMetrics?.cpu?.usage_percent || 0}
                  size={80}
                  thickness={8}
                  color={
                    (systemMetrics?.cpu?.usage_percent || 0) > 90 ? 'error' :
                    (systemMetrics?.cpu?.usage_percent || 0) > 70 ? 'warning' : 'primary'
                  }
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Cores: {systemMetrics?.cpu?.cores || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Memory Usage
              </Typography>
              <LinearProgress
                variant="determinate"
                value={systemMetrics?.memory?.usage_percent || 0}
                color={
                  (systemMetrics?.memory?.usage_percent || 0) > 90 ? 'error' :
                  (systemMetrics?.memory?.usage_percent || 0) > 70 ? 'warning' : 'primary'
                }
                sx={{ height: 10, mb: 1, mt: 2 }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Used: {formatFileSize(systemMetrics?.memory?.used || 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total: {formatFileSize(systemMetrics?.memory?.total || 0)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Disk Usage
              </Typography>
              <LinearProgress
                variant="determinate"
                value={systemMetrics?.disk?.usage_percent || 0}
                color={
                  (systemMetrics?.disk?.usage_percent || 0) > 90 ? 'error' :
                  (systemMetrics?.disk?.usage_percent || 0) > 70 ? 'warning' : 'primary'
                }
                sx={{ height: 10, mb: 1, mt: 2 }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Used: {formatFileSize(systemMetrics?.disk?.used || 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total: {formatFileSize(systemMetrics?.disk?.total || 0)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Network Traffic
              </Typography>
              <Typography variant="body1" sx={{ mb: 1, mt: 2 }}>
                {formatFileSize(systemMetrics?.network?.received || 0)} received
              </Typography>
              <Typography variant="body1">
                {formatFileSize(systemMetrics?.network?.sent || 0)} sent
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={tabIndex}
          onChange={handleTabChange}
          aria-label="system monitoring tabs"
        >
          <Tab label="Resource Trends" id="system-tab-0" />
          <Tab label="Process Metrics" id="system-tab-1" />
          <Tab label="System Logs" id="system-tab-2" />
        </Tabs>
      </Box>
      
      {/* Resource Trends Tab */}
      <TabPanel value={tabIndex} index={0}>
        <Grid container spacing={2}>
          {/* CPU Usage Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="CPU Usage" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300 }}>
                  {cpuHistoryData.length < 2 ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Typography variant="body2" color="text.secondary">
                        Collecting data... (Refreshes every {refreshInterval/1000} seconds)
                      </Typography>
                    </Box>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={cpuHistoryData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} label={{ value: 'Usage (%)', angle: -90, position: 'insideLeft' }} />
                        <RechartsTooltip 
                          formatter={(value: any) => [`${formatNumber(value)}%`, 'CPU Usage']}
                          labelFormatter={(label: any) => `Time ${label}`}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="value" 
                          stroke={theme.palette.primary.main} 
                          activeDot={{ r: 8 }} 
                          isAnimationActive={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Memory Usage Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Memory Usage" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300 }}>
                  {memoryHistoryData.length < 2 ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Typography variant="body2" color="text.secondary">
                        Collecting data... (Refreshes every {refreshInterval/1000} seconds)
                      </Typography>
                    </Box>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={memoryHistoryData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis label={{ value: 'Memory (%)', angle: -90, position: 'insideLeft' }} />
                        <RechartsTooltip 
                          formatter={(value: any) => [`${formatNumber(value)}%`, 'Usage']}
                          labelFormatter={(label: any) => `Time ${label}`}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="percentage" 
                          stroke={theme.palette.info.main} 
                          fill={theme.palette.info.light} 
                          isAnimationActive={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Disk Usage Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Disk Usage" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300 }}>
                  {diskHistoryData.length < 2 ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Typography variant="body2" color="text.secondary">
                        Collecting data... (Refreshes every {refreshInterval/1000} seconds)
                      </Typography>
                    </Box>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={diskHistoryData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis label={{ value: 'Disk (%)', angle: -90, position: 'insideLeft' }} />
                        <RechartsTooltip 
                          formatter={(value: any) => [`${formatNumber(value)}%`, 'Usage']}
                          labelFormatter={(label: any) => `Time ${label}`}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="percentage" 
                          stroke={theme.palette.warning.main} 
                          fill={theme.palette.warning.light} 
                          isAnimationActive={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Network Traffic Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Network Traffic" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300 }}>
                  {networkHistoryData.length < 2 ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Typography variant="body2" color="text.secondary">
                        Collecting data... (Refreshes every {refreshInterval/1000} seconds)
                      </Typography>
                    </Box>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={networkHistoryData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis label={{ value: 'Bytes', angle: -90, position: 'insideLeft' }} />
                        <RechartsTooltip 
                          formatter={(value: any) => [formatFileSize(value), '']}
                          labelFormatter={(label: any) => `Time ${label}`}
                        />
                        <Legend />
                        <Bar 
                          dataKey="received" 
                          name="Received" 
                          fill={theme.palette.success.main} 
                          isAnimationActive={false}
                        />
                        <Bar 
                          dataKey="sent" 
                          name="Sent" 
                          fill={theme.palette.error.main} 
                          isAnimationActive={false}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
      
      {/* Process Metrics Tab */}
      <TabPanel value={tabIndex} index={1}>
        <Alert severity="info" sx={{ mb: 2 }}>
          Process metrics show resources used by the SQL Proxy application itself.
        </Alert>
        
        <Card variant="outlined">
          <CardHeader 
            title="Process Information" 
            titleTypographyProps={{ variant: 'subtitle1' }}
          />
          <Divider />
          <CardContent>
            <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Detailed process metrics are available in the Prometheus integration.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>
      
      {/* System Logs Tab */}
      <TabPanel value={tabIndex} index={2}>
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1">System Logs</Typography>
            
            <Button 
              variant="outlined" 
              size="small" 
              startIcon={<TimelineIcon />}
            >
              View Full Logs
            </Button>
          </Box>
          
          <Box sx={{ bgcolor: 'background.default', p: 2, maxHeight: 400, overflow: 'auto' }}>
            <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
              {/* Log content would go here - this is a placeholder */}
              System logs are available in the server logs section.
            </Typography>
          </Box>
        </Paper>
      </TabPanel>
    </Box>
  );
};

export default SystemMonitoringDashboard;

// Son güncelleme: 2025-05-21 05:32:06
// Güncelleyen: Teeksss