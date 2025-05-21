/**
 * Audit Logs Viewer Component
 * 
 * Interface for viewing and analyzing system audit logs
 * 
 * Last updated: 2025-05-21 07:03:15
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Button,
  CircularProgress,
  Alert,
  Tooltip,
  Card,
  CardContent,
  Grid,
  Divider,
  Collapse
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import VisibilityIcon from '@mui/icons-material/Visibility';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DateTimePicker } from '@mui/x-date-pickers';
import { useQuery } from 'react-query';
import { format } from 'date-fns';

import { auditApi } from '../../services/auditService';

interface AuditLogFilters {
  eventType: string;
  resourceType: string;
  action: string;
  userId: string;
  status: string;
  startDate: Date | null;
  endDate: Date | null;
}

const AuditLogsViewer: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedLog, setSelectedLog] = useState<any | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [filters, setFilters] = useState<AuditLogFilters>({
    eventType: '',
    resourceType: '',
    action: '',
    userId: '',
    status: '',
    startDate: null,
    endDate: null
  });

  // Query for fetching audit logs
  const {
    data: auditLogsData,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['audit-logs', page, rowsPerPage, filters],
    () => auditApi.getAuditLogs({
      page,
      limit: rowsPerPage,
      ...filters,
      startDate: filters.startDate ? format(filters.startDate, "yyyy-MM-dd'T'HH:mm:ss") : undefined,
      endDate: filters.endDate ? format(filters.endDate, "yyyy-MM-dd'T'HH:mm:ss") : undefined
    }),
    {
      keepPreviousData: true
    }
  );

  // Query for fetching audit summary
  const {
    data: auditSummary,
    isLoading: isLoadingSummary
  } = useQuery(
    ['audit-summary'],
    () => auditApi.getAuditSummary(),
    {
      staleTime: 300000 // 5 minutes
    }
  );

  // Handle page change
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Handle search change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  // Handle filter change
  const handleFilterChange = (event: React.ChangeEvent<{ name?: string; value: unknown }>) => {
    const name = event.target.name as keyof AuditLogFilters;
    setFilters({
      ...filters,
      [name]: event.target.value
    });
  };

  // Handle date filter change
  const handleDateChange = (name: 'startDate' | 'endDate', value: Date | null) => {
    setFilters({
      ...filters,
      [name]: value
    });
  };

  // Handle reset filters
  const handleResetFilters = () => {
    setFilters({
      eventType: '',
      resourceType: '',
      action: '',
      userId: '',
      status: '',
      startDate: null,
      endDate: null
    });
    setPage(0);
  };

  // Handle apply filters
  const handleApplyFilters = () => {
    refetch();
    setPage(0);
  };

  // Handle export logs
  const handleExportLogs = () => {
    auditApi.exportAuditLogs(filters);
  };

  // View log details
  const handleViewDetails = (log: any) => {
    setSelectedLog(log);
    setShowDetails(true);
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return 'success';
      case 'failure':
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Get event type color
  const getEventTypeColor = (eventType: string) => {
    switch (eventType.toLowerCase()) {
      case 'security':
        return 'primary';
      case 'data':
        return 'info';
      case 'system':
        return 'secondary';
      default:
        return 'default';
    }
  };

  // Filter logs based on search term
  const filteredLogs = (auditLogsData?.items || []).filter(log => {
    if (!searchTerm) return true;
    
    const search = searchTerm.toLowerCase();
    return (
      (log.username && log.username.toLowerCase().includes(search)) ||
      (log.resource_id && log.resource_id.toLowerCase().includes(search)) ||
      (log.action && log.action.toLowerCase().includes(search))
    );
  });

  // Loading state
  if (isLoading && !auditLogsData) {
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
        Error loading audit logs: {(error as Error).message}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Audit Logs
      </Typography>
      
      {/* Summary Cards */}
      {!isLoadingSummary && auditSummary && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Total Events
                </Typography>
                <Typography variant="h3">
                  {auditSummary.total_events}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last {auditSummary.days} days
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Event Types
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-around' }}>
                  <Box textAlign="center">
                    <Typography variant="h5">{auditSummary.event_types?.security || 0}</Typography>
                    <Chip label="Security" color="primary" size="small" />
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="h5">{auditSummary.event_types?.data || 0}</Typography>
                    <Chip label="Data" color="info" size="small" />
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="h5">{auditSummary.event_types?.system || 0}</Typography>
                    <Chip label="System" color="secondary" size="small" />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Status Distribution
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-around' }}>
                  <Box textAlign="center">
                    <Typography variant="h5">{auditSummary.statuses?.success || 0}</Typography>
                    <Chip label="Success" color="success" size="small" />
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="h5">{auditSummary.statuses?.failure || 0}</Typography>
                    <Chip label="Failure" color="error" size="small" />
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="h5">{auditSummary.statuses?.error || 0}</Typography>
                    <Chip label="Error" color="error" size="small" />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
      
      {/* Search and Filter Bar */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            placeholder="Search logs..."
            value={searchTerm}
            onChange={handleSearchChange}
            variant="outlined"
            size="small"
            sx={{ width: 300, mr: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          
          <Button
            variant="outlined"
            startIcon={showFilters ? <ExpandLessIcon /> : <FilterListIcon />}
            onClick={() => setShowFilters(!showFilters)}
            sx={{ mr: 2 }}
          >
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </Button>
          
          <Tooltip title="Refresh Logs">
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Button
          variant="outlined"
          startIcon={<FileDownloadIcon />}
          onClick={handleExportLogs}
        >
          Export Logs
        </Button>
      </Box>
      
      {/* Filters */}
      <Collapse in={showFilters}>
        <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Filter Audit Logs
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel id="event-type-label">Event Type</InputLabel>
                <Select
                  labelId="event-type-label"
                  id="eventType"
                  name="eventType"
                  value={filters.eventType}
                  onChange={handleFilterChange}
                  label="Event Type"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="security">Security</MenuItem>
                  <MenuItem value="data">Data</MenuItem>
                  <MenuItem value="system">System</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel id="resource-type-label">Resource Type</InputLabel>
                <Select
                  labelId="resource-type-label"
                  id="resourceType"
                  name="resourceType"
                  value={filters.resourceType}
                  onChange={handleFilterChange}
                  label="Resource Type"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="user">User</MenuItem>
                  <MenuItem value="query">Query</MenuItem>
                  <MenuItem value="server">Server</MenuItem>
                  <MenuItem value="powerbi">PowerBI</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel id="action-label">Action</InputLabel>
                <Select
                  labelId="action-label"
                  id="action"
                  name="action"
                  value={filters.action}
                  onChange={handleFilterChange}
                  label="Action"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="create">Create</MenuItem>
                  <MenuItem value="update">Update</MenuItem>
                  <MenuItem value="delete">Delete</MenuItem>
                  <MenuItem value="execute">Execute</MenuItem>
                  <MenuItem value="login">Login</MenuItem>
                  <MenuItem value="logout">Logout</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel id="status-label">Status</InputLabel>
                <Select
                  labelId="status-label"
                  id="status"
                  name="status"
                  value={filters.status}
                  onChange={handleFilterChange}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="success">Success</MenuItem>
                  <MenuItem value="failure">Failure</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                id="userId"
                name="userId"
                label="User ID"
                size="small"
                value={filters.userId}
                onChange={handleFilterChange}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="Start Date"
                  value={filters.startDate}
                  onChange={(date) => handleDateChange('startDate', date)}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DateTimePicker
                  label="End Date"
                  value={filters.endDate}
                  onChange={(date) => handleDateChange('endDate', date)}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', height: '100%', alignItems: 'center' }}>
                <Button
                  variant="outlined"
                  onClick={handleResetFilters}
                  sx={{ mr: 1 }}
                >
                  Reset
                </Button>
                <Button
                  variant="contained"
                  onClick={handleApplyFilters}
                >
                  Apply
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Collapse>
      
      {/* Audit Logs Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Event Type</TableCell>
              <TableCell>Resource</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Status</TableCell>
              <TableCell width={80}>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredLogs.map((log) => (
              <TableRow key={log.id} hover>
                <TableCell>{formatTimestamp(log.timestamp)}</TableCell>
                <TableCell>
                  {log.username || (log.user_id ? `User #${log.user_id}` : 'System')}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={log.event_type} 
                    color={getEventTypeColor(log.event_type)} 
                    size="small" 
                    variant="outlined" 
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {log.resource_type}
                  </Typography>
                  {log.resource_id && (
                    <Typography variant="caption" color="text.secondary">
                      ID: {log.resource_id}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>{log.action}</TableCell>
                <TableCell>
                  <Chip 
                    label={log.status} 
                    color={getStatusColor(log.status)} 
                    size="small" 
                  />
                </TableCell>
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton size="small" onClick={() => handleViewDetails(log)}>
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            
            {filteredLogs.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No audit logs found matching your criteria
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={auditLogsData?.total || 0}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
      
      {/* Log Details Dialog */}
      <Dialog
        open={showDetails}
        onClose={() => setShowDetails(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Audit Log Details
        </DialogTitle>
        <Divider />
        <DialogContent>
          {selectedLog && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Event ID</Typography>
                <Typography variant="body1" gutterBottom>{selectedLog.id}</Typography>
                
                <Typography variant="subtitle2">Timestamp</Typography>
                <Typography variant="body1" gutterBottom>{formatTimestamp(selectedLog.timestamp)}</Typography>
                
                <Typography variant="subtitle2">User</Typography>
                <Typography variant="body1" gutterBottom>
                  {selectedLog.username || (selectedLog.user_id ? `User #${selectedLog.user_id}` : 'System')}
                </Typography>
                
                <Typography variant="subtitle2">IP Address</Typography>
                <Typography variant="body1" gutterBottom>{selectedLog.client_ip || 'N/A'}</Typography>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Event Type</Typography>
                <Typography variant="body1" gutterBottom>
                  <Chip 
                    label={selectedLog.event_type} 
                    color={getEventTypeColor(selectedLog.event_type)} 
                    size="small" 
                  />
                </Typography>
                
                <Typography variant="subtitle2">Resource</Typography>
                <Typography variant="body1" gutterBottom>
                  {selectedLog.resource_type} {selectedLog.resource_id ? `(${selectedLog.resource_id})` : ''}
                </Typography>
                
                <Typography variant="subtitle2">Action</Typography>
                <Typography variant="body1" gutterBottom>{selectedLog.action}</Typography>
                
                <Typography variant="subtitle2">Status</Typography>
                <Typography variant="body1" gutterBottom>
                  <Chip 
                    label={selectedLog.status} 
                    color={getStatusColor(selectedLog.status)} 
                    size="small" 
                  />
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Additional Details
                </Typography>
                
                {selectedLog.details ? (
                  <Box 
                    component="pre" 
                    sx={{ 
                      bgcolor: 'background.default',
                      p: 2,
                      borderRadius: 1,
                      overflow: 'auto',
                      maxHeight: 300,
                      fontSize: '0.875rem'
                    }}
                  >
                    {JSON.stringify(selectedLog.details, null, 2)}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No additional details available
                  </Typography>
                )}
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetails(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AuditLogsViewer;

// Son güncelleme: 2025-05-21 07:03:15
// Güncelleyen: Teeksss