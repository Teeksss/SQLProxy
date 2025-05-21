/**
 * Performance Dashboard Component
 * 
 * Displays performance metrics and analytics for SQL queries and API endpoints
 * 
 * Last updated: 2025-05-21 05:17:27
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  CardHeader, 
  CircularProgress, 
  Divider, 
  Grid, 
  Paper, 
  Typography,
  Tabs,
  Tab,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  IconButton,
  Tooltip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
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
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import WarningIcon from '@mui/icons-material/Warning';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import { useQuery } from 'react-query';

import NoDataPlaceholder from '../common/NoDataPlaceholder';
import { metricsApi } from '../../services/metricsService';
import { formatDuration, formatDateTime, formatNumber } from '../../utils/formatters';
import { theme } from '../../theme';

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
      id={`performance-tabpanel-${index}`}
      aria-labelledby={`performance-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 1 }}>{children}</Box>}
    </div>
  );
};

const PerformanceDashboard: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedDatabase, setSelectedDatabase] = useState<string>('all');
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>('all');
  
  // Query for fetching performance metrics
  const { 
    data: performanceData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery(
    ['performanceMetrics', timeRange],
    () => metricsApi.getPerformanceMetrics(timeRange),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      refetchOnWindowFocus: true
    }
  );
  
  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };
  
  // Handle time range change
  const handleTimeRangeChange = (event: SelectChangeEvent<string>) => {
    setTimeRange(event.target.value);
  };
  
  // Handle database selection
  const handleDatabaseChange = (event: SelectChangeEvent<string>) => {
    setSelectedDatabase(event.target.value);
  };
  
  // Handle endpoint selection
  const handleEndpointChange = (event: SelectChangeEvent<string>) => {
    setSelectedEndpoint(event.target.value);
  };
  
  // Extract database options from metrics
  const databaseOptions = React.useMemo(() => {
    if (!performanceData?.queries) return [];
    
    return ['all', ...Object.keys(performanceData.queries)];
  }, [performanceData?.queries]);
  
  // Extract endpoint options from metrics
  const endpointOptions = React.useMemo(() => {
    if (!performanceData?.endpoints || selectedDatabase === 'all') return [];
    
    const endpoints = new Set<string>();
    
    // Get all endpoints from the selected database
    if (performanceData.queries[selectedDatabase]) {
      Object.keys(performanceData.queries[selectedDatabase].endpoints || {}).forEach(
        endpoint => endpoints.add(endpoint)
      );
    }
    
    return ['all', ...Array.from(endpoints)];
  }, [performanceData?.endpoints, selectedDatabase, performanceData?.queries]);
  
  // Filter metrics based on selections
  const filteredQueryMetrics = React.useMemo(() => {
    if (!performanceData?.queries) return {};
    
    const filteredMetrics: any = {};
    
    if (selectedDatabase === 'all') {
      // Include all databases
      return performanceData.queries;
    } else {
      // Include only the selected database
      if (performanceData.queries[selectedDatabase]) {
        filteredMetrics[selectedDatabase] = performanceData.queries[selectedDatabase];
      }
    }
    
    return filteredMetrics;
  }, [performanceData?.queries, selectedDatabase]);
  
  // Prepare data for query performance chart
  const queryPerformanceData = React.useMemo(() => {
    if (!filteredQueryMetrics) return [];
    
    return Object.entries(filteredQueryMetrics).map(([dbName, metrics]: [string, any]) => ({
      name: dbName,
      average: metrics.average * 1000, // Convert to ms
      p95: metrics.p95 * 1000, // Convert to ms
      median: metrics.median * 1000, // Convert to ms
      count: metrics.count
    }));
  }, [filteredQueryMetrics]);
  
  // Prepare data for endpoint response time chart
  const endpointResponseTimeData = React.useMemo(() => {
    if (!performanceData?.endpoints) return [];
    
    return Object.entries(performanceData.endpoints).map(([method, metrics]: [string, any]) => ({
      name: method,
      average: metrics.average * 1000, // Convert to ms
      p95: metrics.p95 * 1000, // Convert to ms
      median: metrics.median * 1000, // Convert to ms
      count: metrics.count
    }));
  }, [performanceData?.endpoints]);
  
  // Prepare data for query distribution chart
  const queryDistributionData = React.useMemo(() => {
    if (!filteredQueryMetrics) return [];
    
    let totalCount = 0;
    const distribution: Record<string, number> = {};
    
    Object.entries(filteredQueryMetrics).forEach(([dbName, metrics]: [string, any]) => {
      distribution[dbName] = metrics.count;
      totalCount += metrics.count;
    });
    
    return Object.entries(distribution).map(([name, value]) => ({
      name,
      value,
      percentage: totalCount > 0 ? (value / totalCount) * 100 : 0
    }));
  }, [filteredQueryMetrics]);
  
  // Prepare data for detailed query metrics table
  const detailedQueryMetricsData = React.useMemo(() => {
    if (!filteredQueryMetrics) return [];
    
    const detailedMetrics: any[] = [];
    
    Object.entries(filteredQueryMetrics).forEach(([dbName, dbMetrics]: [string, any]) => {
      // Skip if not the selected database and a specific database is selected
      if (selectedDatabase !== 'all' && dbName !== selectedDatabase) return;
      
      // Add database-level metrics
      detailedMetrics.push({
        type: 'database',
        name: dbName,
        average: dbMetrics.average * 1000,
        median: dbMetrics.median * 1000,
        p95: dbMetrics.p95 * 1000,
        min: dbMetrics.min * 1000,
        max: dbMetrics.max * 1000,
        count: dbMetrics.count
      });
      
      // Add endpoint-level metrics
      Object.entries(dbMetrics.endpoints || {}).forEach(([endpoint, endpointMetrics]: [string, any]) => {
        // Skip if not the selected endpoint and a specific endpoint is selected
        if (selectedEndpoint !== 'all' && endpoint !== selectedEndpoint) return;
        
        detailedMetrics.push({
          type: 'endpoint',
          database: dbName,
          name: endpoint,
          average: endpointMetrics.average * 1000,
          median: endpointMetrics.median * 1000,
          p95: endpointMetrics.p95 * 1000,
          min: endpointMetrics.min * 1000,
          max: endpointMetrics.max * 1000,
          count: endpointMetrics.count
        });
      });
    });
    
    return detailedMetrics;
  }, [filteredQueryMetrics, selectedDatabase, selectedEndpoint]);
  
  // Check for slow queries
  const slowQueries = React.useMemo(() => {
    if (!filteredQueryMetrics) return [];
    
    const slow: any[] = [];
    
    Object.entries(filteredQueryMetrics).forEach(([dbName, dbMetrics]: [string, any]) => {
      Object.entries(dbMetrics.endpoints || {}).forEach(([endpoint, endpointMetrics]: [string, any]) => {
        if (endpointMetrics.max * 1000 > 500) { // 500ms threshold for slow queries
          slow.push({
            database: dbName,
            endpoint,
            maxTime: endpointMetrics.max * 1000,
            avgTime: endpointMetrics.average * 1000,
            count: endpointMetrics.count
          });
        }
      });
    });
    
    return slow.sort((a, b) => b.maxTime - a.maxTime);
  }, [filteredQueryMetrics]);

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
        Error loading performance metrics: {(error as Error).message}
      </Alert>
    );
  }
  
  // No data state
  if (!performanceData || !performanceData.queries || Object.keys(performanceData.queries).length === 0) {
    return (
      <NoDataPlaceholder message="No performance metrics available" />
    );
  }
  
  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          Performance Dashboard
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
          
          <Tooltip title="Refresh Data">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export Data">
            <IconButton onClick={() => metricsApi.exportPerformanceMetrics()}>
              <DownloadIcon />
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
                {Object.values(performanceData.queries).reduce((sum, db: any) => sum + db.count, 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all databases
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
                {formatDuration(
                  Object.values(performanceData.queries).reduce((sum, db: any) => sum + db.average, 0) / 
                  Object.values(performanceData.queries).length * 1000
                )}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                P95: {formatDuration(
                  Math.max(...Object.values(performanceData.queries).map((db: any) => db.p95 * 1000))
                )}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Total API Requests
              </Typography>
              <Typography variant="h4">
                {Object.values(performanceData.endpoints).reduce((sum, method: any) => sum + method.count, 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all endpoints
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
              <Typography variant="h4" sx={{ color: slowQueries.length > 0 ? 'warning.main' : 'inherit' }}>
                {slowQueries.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Queries taking &gt;500ms
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Filter Controls */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel id="database-label">Database</InputLabel>
          <Select
            labelId="database-label"
            id="database"
            value={selectedDatabase}
            label="Database"
            onChange={handleDatabaseChange}
          >
            {databaseOptions.map(db => (
              <MenuItem key={db} value={db}>{db}</MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {selectedDatabase !== 'all' && (
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel id="endpoint-label">Endpoint</InputLabel>
            <Select
              labelId="endpoint-label"
              id="endpoint"
              value={selectedEndpoint}
              label="Endpoint"
              onChange={handleEndpointChange}
            >
              {endpointOptions.map(endpoint => (
                <MenuItem key={endpoint} value={endpoint}>
                  {endpoint === 'all' ? 'All Endpoints' : endpoint}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>
      
      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={tabIndex} 
          onChange={handleTabChange}
          aria-label="performance tabs"
        >
          <Tab label="Overview" id="performance-tab-0" />
          <Tab label="Queries" id="performance-tab-1" />
          <Tab label="Endpoints" id="performance-tab-2" />
          <Tab label="Slow Queries" id="performance-tab-3" />
        </Tabs>
      </Box>
      
      {/* Overview Tab */}
      <TabPanel value={tabIndex} index={0}>
        <Grid container spacing={2}>
          {/* Query Response Time Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Query Response Time" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={queryPerformanceData}
                      margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} />
                      <YAxis label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }} />
                      <RechartsTooltip formatter={(value: any) => `${formatNumber(value)} ms`} />
                      <Legend />
                      <Bar dataKey="average" name="Average" fill={theme.palette.primary.main} />
                      <Bar dataKey="p95" name="95th Percentile" fill={theme.palette.secondary.main} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Endpoint Response Time Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Endpoint Response Time" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={endpointResponseTimeData}
                      margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={60} />
                      <YAxis label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }} />
                      <RechartsTooltip formatter={(value: any) => `${formatNumber(value)} ms`} />
                      <Legend />
                      <Bar dataKey="average" name="Average" fill={theme.palette.info.main} />
                      <Bar dataKey="p95" name="95th Percentile" fill={theme.palette.warning.main} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Query Distribution Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Query Distribution" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={queryDistributionData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {queryDistributionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip formatter={(value: any, name: any, props: any) => 
                        [`${formatNumber(value)} queries (${(props.payload.percentage).toFixed(1)}%)`, props.payload.name]
                      } />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Performance Trends Chart */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Slow Query Trends" 
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <Divider />
              <CardContent>
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Trend data not available in this view
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
      
      {/* Queries Tab */}
      <TabPanel value={tabIndex} index={1}>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Database/Endpoint</TableCell>
                <TableCell align="right">Average (ms)</TableCell>
                <TableCell align="right">Median (ms)</TableCell>
                <TableCell align="right">P95 (ms)</TableCell>
                <TableCell align="right">Min (ms)</TableCell>
                <TableCell align="right">Max (ms)</TableCell>
                <TableCell align="right">Count</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {detailedQueryMetricsData.map((row, index) => (
                <TableRow 
                  key={index}
                  sx={{ 
                    backgroundColor: row.type === 'database' 
                      ? 'rgba(0, 0, 0, 0.04)' 
                      : 'inherit',
                    '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.08)' }
                  }}
                >
                  <TableCell>
                    {row.type === 'database' 
                      ? <strong>{row.name}</strong> 
                      : <Box sx={{ pl: 2 }}>{row.name}</Box>}
                  </TableCell>
                  <TableCell align="right">{formatNumber(row.average)}</TableCell>
                  <TableCell align="right">{formatNumber(row.median)}</TableCell>
                  <TableCell align="right">{formatNumber(row.p95)}</TableCell>
                  <TableCell align="right">{formatNumber(row.min)}</TableCell>
                  <TableCell align="right">{formatNumber(row.max)}</TableCell>
                  <TableCell align="right">{formatNumber(row.count)}</TableCell>
                </TableRow>
              ))}
              
              {detailedQueryMetricsData.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No query metrics available for the selected filters
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>
      
      {/* Endpoints Tab */}
      <TabPanel value={tabIndex} index={2}>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Method/Endpoint</TableCell>
                <TableCell align="right">Average (ms)</TableCell>
                <TableCell align="right">P95 (ms)</TableCell>
                <TableCell align="right">Max (ms)</TableCell>
                <TableCell align="right">Count</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {performanceData.endpoints && Object.entries(performanceData.endpoints).map(([method, methodData]: [string, any]) => (
                <React.Fragment key={method}>
                  {/* Method row */}
                  <TableRow sx={{ backgroundColor: 'rgba(0, 0, 0, 0.04)' }}>
                    <TableCell>
                      <strong>{method}</strong>
                    </TableCell>
                    <TableCell align="right">{formatNumber(methodData.average * 1000)}</TableCell>
                    <TableCell align="right">{formatNumber(methodData.p95 * 1000)}</TableCell>
                    <TableCell align="right">{formatNumber(methodData.max * 1000)}</TableCell>
                    <TableCell align="right">{formatNumber(methodData.count)}</TableCell>
                  </TableRow>
                  
                  {/* Endpoint rows */}
                  {Object.entries(methodData.endpoints || {}).map(([endpoint, endpointData]: [string, any]) => (
                    <TableRow key={`${method}-${endpoint}`}>
                      <TableCell>
                        <Box sx={{ pl: 2 }}>{endpoint}</Box>
                      </TableCell>
                      <TableCell align="right">{formatNumber(endpointData.average * 1000)}</TableCell>
                      <TableCell align="right">{formatNumber(endpointData.p95 * 1000)}</TableCell>
                      <TableCell align="right">{formatNumber(endpointData.max * 1000)}</TableCell>
                      <TableCell align="right">{formatNumber(endpointData.count)}</TableCell>
                    </TableRow>
                  ))}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>
      
      {/* Slow Queries Tab */}
      <TabPanel value={tabIndex} index={3}>
        {slowQueries.length === 0 ? (
          <Alert severity="success" sx={{ mt: 2 }}>
            No slow queries detected in the selected time range.
          </Alert>
        ) : (
          <>
            <Alert severity="warning" sx={{ mt: 2, mb: 2 }}>
              {slowQueries.length} slow queries detected (execution time &gt;500ms)
            </Alert>
            
            <TableContainer component={Paper} variant="outlined">
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
                  {slowQueries.map((query, index) => (
                    <TableRow key={index}>
                      <TableCell>{query.database}</TableCell>
                      <TableCell>{query.endpoint}</TableCell>
                      <TableCell align="right" sx={{ color: 'error.main' }}>
                        {formatNumber(query.maxTime)}
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(query.avgTime)}
                      </TableCell>
                      <TableCell align="right">{formatNumber(query.count)}</TableCell>
                      <TableCell align="right">
                        <Tooltip title="Analyze Query">
                          <IconButton size="small">
                            <MoreHorizIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </TabPanel>
    </Box>
  );
};

export default PerformanceDashboard;

// Son güncelleme: 2025-05-21 05:17:27
// Güncelleyen: Teeksss