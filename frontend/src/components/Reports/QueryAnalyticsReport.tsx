/**
 * Query Analytics Report Component
 * 
 * Displays analytics for SQL queries with filtering and visualization options
 * 
 * Last updated: 2025-05-21 05:21:55
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Button,
  CircularProgress,
  Divider,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  SelectChangeEvent
} from '@mui/material';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import GetAppIcon from '@mui/icons-material/GetApp';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';
import { useQuery } from 'react-query';

import NoDataPlaceholder from '../common/NoDataPlaceholder';
import { metricsApi } from '../../services/metricsService';
import { serverApi } from '../../services/serverService';
import { formatDuration, formatNumber, formatDateTime } from '../../utils/formatters';
import { theme } from '../../theme';

const QueryAnalyticsReport: React.FC = () => {
  const [selectedServer, setSelectedServer] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  
  // Query for fetching server list
  const {
    data: servers,
    isLoading: isLoadingServers
  } = useQuery(
    ['servers'],
    () => serverApi.getServers(),
    {
      staleTime: 300000 // 5 minutes
    }
  );
  
  // Query for fetching query analytics
  const {
    data: analyticsData,
    isLoading: isLoadingAnalytics,
    error: analyticsError,
    refetch: refetchAnalytics
  } = useQuery(
    ['queryAnalytics', selectedServer, timeRange],
    () => metricsApi.getQueryAnalytics(selectedServer === 'all' ? undefined : selectedServer, timeRange),
    {
      staleTime: 60000, // 1 minute
      refetchInterval: 300000 // 5 minutes
    }
  );
  
  // Handle server selection change
  const handleServerChange = (event: SelectChangeEvent<string>) => {
    setSelectedServer(event.target.value);
  };
  
  // Handle time range change
  const handleTimeRangeChange = (event: SelectChangeEvent<string>) => {
    setTimeRange(event.target.value);
  };
  
  // Prepare data for database distribution chart
  const databaseDistributionData = React.useMemo(() => {
    if (!analyticsData?.query_stats) return [];
    
    return Object.entries(analyticsData.query_stats).map(([dbName, metrics]: [string, any]) => ({
      name: dbName,
      value: metrics.count
    }));
  }, [analyticsData?.query_stats]);
  
  // Colors for charts
  const COLORS = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.error.main,
    theme.palette.info.main,
    '#8884d8',
    '#82ca9d',
    '#ffc658',
    '#ff8042'
  ];
  
  // Loading state
  if (isLoadingServers || isLoadingAnalytics) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  // Error state
  if (analyticsError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading query analytics: {(analyticsError as Error).message}
      </Alert>
    );
  }
  
  // No data state
  if (!analyticsData || !analyticsData.query_stats || Object.keys(analyticsData.query_stats).length === 0) {
    return (
      <NoDataPlaceholder message="No query analytics data available for the selected filter" />
    );
  }
  
  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          Query Analytics Report
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="time-range-label">Time Range</InputLabel>
            <Select
              labelId="time-range-label"
              id="time-range"
              value={timeRange}
              label="Time Range"
              onChange={handleTimeRangeChange}
            >
              <MenuItem value="1h">Last Hour</MenuItem>
              <MenuItem value="6h">Last 6 Hours</MenuItem>
              <MenuItem value="24h">Last 24 Hours</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
              <MenuItem value="30d">Last 30 Days</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel id="server-label">Database Server</InputLabel>
            <Select
              labelId="server-label"
              id="server"
              value={selectedServer}
              label="Database Server"
              onChange={handleServerChange}
            >
              <MenuItem value="all">All Servers</MenuItem>
              {servers?.map((server: any) => (
                <MenuItem key={server.id} value={server.id}>
                  {server.alias || server.host}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh Data">
            <IconButton onClick={() => refetchAnalytics()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export Data">
            <IconButton onClick={() => metricsApi.exportPerformanceMetrics()}>
              <GetAppIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* Overview Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Total Queries
              </Typography>
              <Typography variant="h4">
                {formatNumber(analyticsData.total_queries)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Over {timeRange} period
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Avg Query Time
              </Typography>
              <Typography variant="h4">
                {formatDuration(analyticsData.avg_query_time)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Max: {formatDuration(analyticsData.max_query_time)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Slow Queries
              </Typography>
              <Typography variant="h4" sx={{ color: analyticsData.slow_queries.length > 0 ? 'warning.main' : 'inherit' }}>
                {formatNumber(analyticsData.slow_queries.length)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Queries taking &gt;500ms
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Time Period
              </Typography>
              <Typography variant="h4">
                {analyticsData.time_range.hours}h
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatDateTime(analyticsData.time_range.start)} to {formatDateTime(analyticsData.time_range.end)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Charts and Data */}
      <Grid container spacing={2}>
        {/* Database Distribution Chart */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Query Distribution by Database
              </Typography>
              <Box sx={{ height: 300 }}>
                {databaseDistributionData.length === 0 ? (
                  <NoDataPlaceholder message="No data available for distribution chart" />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={databaseDistributionData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {databaseDistributionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip formatter={(value: any) => formatNumber(value)} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Query Performance Chart */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Query Performance by Database
              </Typography>
              <Box sx={{ height: 300 }}>
                {Object.keys(analyticsData.query_stats).length === 0 ? (
                  <NoDataPlaceholder message="No data available for performance chart" />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={Object.entries(analyticsData.query_stats).map(([name, stats]: [string, any]) => ({
                        name,
                        avg: stats.average * 1000,
                        max: stats.max * 1000
                      }))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} />
                      <YAxis label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }} />
                      <RechartsTooltip formatter={(value: any) => `${formatNumber(value)} ms`} />
                      <Legend />
                      <Bar dataKey="avg" name="Avg Query Time" fill={theme.palette.primary.main} />
                      <Bar dataKey="max" name="Max Query Time" fill={theme.palette.warning.main} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Slow Queries Table */}
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Slow Queries
              </Typography>
              
              {analyticsData.slow_queries.length === 0 ? (
                <Alert severity="success" sx={{ mt: 2 }}>
                  No slow queries detected in the selected time range.
                </Alert>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Database</TableCell>
                        <TableCell>Endpoint</TableCell>
                        <TableCell align="right">Max Time (ms)</TableCell>
                        <TableCell align="right">Avg Time (ms)</TableCell>
                        <TableCell align="right">Count</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analyticsData.slow_queries.map((query: any, index: number) => (
                        <TableRow key={index}>
                          <TableCell>{query.database}</TableCell>
                          <TableCell>{query.endpoint}</TableCell>
                          <TableCell align="right" sx={{ color: 'error.main' }}>
                            {formatNumber(query.max_time)}
                          </TableCell>
                          <TableCell align="right">
                            {formatNumber(query.avg_time)}
                          </TableCell>
                          <TableCell align="right">{formatNumber(query.count)}</TableCell>
                          <TableCell align="right">
                            <Tooltip title="Analyze Query">
                              <IconButton size="small">
                                <SearchIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Detailed Stats Table */}
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Detailed Query Statistics
              </Typography>
              
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Database</TableCell>
                      <TableCell align="right">Queries</TableCell>
                      <TableCell align="right">Avg Time (ms)</TableCell>
                      <TableCell align="right">Median (ms)</TableCell>
                      <TableCell align="right">P95 (ms)</TableCell>
                      <TableCell align="right">Min (ms)</TableCell>
                      <TableCell align="right">Max (ms)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(analyticsData.query_stats).map(([dbName, stats]: [string, any]) => (
                      <TableRow key={dbName}>
                        <TableCell>{dbName}</TableCell>
                        <TableCell align="right">{formatNumber(stats.count)}</TableCell>
                        <TableCell align="right">{formatNumber(stats.average * 1000)}</TableCell>
                        <TableCell align="right">{formatNumber(stats.median * 1000)}</TableCell>
                        <TableCell align="right">{formatNumber(stats.p95 * 1000)}</TableCell>
                        <TableCell align="right">{formatNumber(stats.min * 1000)}</TableCell>
                        <TableCell align="right">{formatNumber(stats.max * 1000)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default QueryAnalyticsReport;

// Son güncelleme: 2025-05-21 05:21:55
// Güncelleyen: Teeksss