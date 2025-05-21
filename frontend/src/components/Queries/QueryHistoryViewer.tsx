/**
 * Query History Viewer Component
 * 
 * Component for viewing and managing SQL query execution history
 * 
 * Last updated: 2025-05-21 07:14:55
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
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
  Button,
  CircularProgress,
  Alert,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Divider,
  Badge,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Grid
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate, useLocation } from 'react-router-dom';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import VisibilityIcon from '@mui/icons-material/Visibility';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import SaveIcon from '@mui/icons-material/Save';
import ScheduleIcon from '@mui/icons-material/Schedule';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import CloseIcon from '@mui/icons-material/Close';
import { toast } from 'react-toastify';
import { format } from 'date-fns';

import { queryApi } from '../../services/queryService';
import { formatBytes, formatDuration } from '../../utils/formatters';
import QueryResultDisplay from './QueryResultDisplay';
import SaveQueryDialog from './SaveQueryDialog';
import ScheduleQueryDialog from './ScheduleQueryDialog';

// Define TabPanel component
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
      id={`query-history-tabpanel-${index}`}
      aria-labelledby={`query-history-tab-${index}`}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
};

// Query History Table component
interface QueryHistoryTableProps {
  queries: any[];
  isLoading: boolean;
  error: any;
  onViewQuery: (query: any) => void;
  onOpenMenu: (event: React.MouseEvent<HTMLElement>, queryId: string) => void;
}

const QueryHistoryTable: React.FC<QueryHistoryTableProps> = ({
  queries,
  isLoading,
  error,
  onViewQuery,
  onOpenMenu
}) => {
  // Format date for display
  const formatDate = (date: string) => {
    return format(new Date(date), 'yyyy-MM-dd HH:mm:ss');
  };
  
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return 'success';
      case 'error':
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };
  
  // Function to truncate SQL for display
  const truncateSql = (sql: string, maxLength: number = 50) => {
    if (sql.length <= maxLength) return sql;
    return sql.substring(0, maxLength) + '...';
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading query history: {(error as Error).message}
      </Alert>
    );
  }

  if (queries.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No queries found matching your criteria.
      </Alert>
    );
  }

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Execution Time</TableCell>
            <TableCell>SQL</TableCell>
            <TableCell>Server</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Duration</TableCell>
            <TableCell align="right">Rows</TableCell>
            <TableCell width={60}>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {queries.map((query) => (
            <TableRow key={query.id} hover>
              <TableCell>{formatDate(query.executed_at)}</TableCell>
              <TableCell>
                <Tooltip title={query.sql_text}>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontFamily: 'monospace', 
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: 300,
                      cursor: 'pointer'
                    }}
                    onClick={() => onViewQuery(query)}
                  >
                    {truncateSql(query.sql_text)}
                  </Typography>
                </Tooltip>
              </TableCell>
              <TableCell>{query.server_name || query.server_id}</TableCell>
              <TableCell>
                <Chip 
                  label={query.status.toUpperCase()} 
                  color={getStatusColor(query.status)} 
                  size="small" 
                />
              </TableCell>
              <TableCell>{formatDuration(query.duration_ms)}</TableCell>
              <TableCell align="right">{query.row_count || 0}</TableCell>
              <TableCell>
                <Box sx={{ display: 'flex' }}>
                  <Tooltip title="View Query">
                    <IconButton size="small" onClick={() => onViewQuery(query)}>
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Actions">
                    <IconButton size="small" onClick={(e) => onOpenMenu(e, query.id)}>
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

const QueryHistoryViewer: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const searchParams = new URLSearchParams(location.search);
  
  // State for search and filters
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [tabIndex, setTabIndex] = useState<number>(0);
  const [selectedQuery, setSelectedQuery] = useState<any>(null);
  const [page, setPage] = useState<number>(0);
  const [rowsPerPage, setRowsPerPage] = useState<number>(10);
  const [showDetailDialog, setShowDetailDialog] = useState<boolean>(false);
  const [showSaveDialog, setShowSaveDialog] = useState<boolean>(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState<boolean>(false);
  
  // Menu state
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [activeQueryId, setActiveQueryId] = useState<string | null>(null);

  // Extract query ID from URL if present
  const selectedQueryId = searchParams.get('query');
  
  // Query for fetching query history
  const {
    data: historyData,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory
  } = useQuery(
    ['query-history', page, rowsPerPage, tabIndex],
    () => queryApi.getQueryHistory({
      offset: page * rowsPerPage,
      limit: rowsPerPage,
      status: tabIndex === 1 ? 'success' : (tabIndex === 2 ? 'error' : undefined)
    }),
    {
      keepPreviousData: true,
      staleTime: 30000 // 30 seconds
    }
  );
  
  // Query for fetching detailed query info if selected
  const {
    data: queryDetail,
    isLoading: isLoadingDetail
  } = useQuery(
    ['query-detail', selectedQueryId],
    () => queryApi.getQueryDetail(selectedQueryId || ''),
    {
      enabled: !!selectedQueryId,
      onSuccess: (data) => {
        if (data) {
          setSelectedQuery(data);
          setShowDetailDialog(true);
        }
      }
    }
  );
  
  // Mutation for deleting query history item
  const deleteQueryMutation = useMutation(
    (queryId: string) => queryApi.deleteQueryHistory(queryId),
    {
      onSuccess: () => {
        toast.success('Query history item deleted successfully');
        queryClient.invalidateQueries(['query-history']);
        
        // Close detail dialog if open for this query
        if (selectedQuery?.id === activeQueryId) {
          setShowDetailDialog(false);
        }
      }
    }
  );
  
  // Mutation for re-running a query
  const rerunQueryMutation = useMutation(
    (query: any) => queryApi.executeQuery({
      sql: query.sql_text,
      serverId: query.server_id
    }),
    {
      onSuccess: (data) => {
        toast.success('Query executed successfully');
        queryClient.invalidateQueries(['query-history']);
        
        // Navigate to query detail
        if (data?.id) {
          navigate(`/query-history?query=${data.id}`);
        }
      }
    }
  );
  
  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
    setPage(0); // Reset to first page when tab changes
  };
  
  // Handle search change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };
  
  // Handle page change
  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };
  
  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Handle query actions menu
  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>, queryId: string) => {
    setMenuAnchorEl(event.currentTarget);
    setActiveQueryId(queryId);
  };
  
  const handleCloseMenu = () => {
    setMenuAnchorEl(null);
  };
  
  // Handle view query details
  const handleViewQuery = (query: any) => {
    setSelectedQuery(query);
    setShowDetailDialog(true);
    handleCloseMenu();
  };
  
  // Handle save query
  const handleSaveQuery = () => {
    const query = historyData?.items.find(q => q.id === activeQueryId);
    if (query) {
      setSelectedQuery(query);
      setShowSaveDialog(true);
    }
    handleCloseMenu();
  };
  
  // Handle schedule query
  const handleScheduleQuery = () => {
    const query = historyData?.items.find(q => q.id === activeQueryId);
    if (query) {
      setSelectedQuery(query);
      setShowScheduleDialog(true);
    }
    handleCloseMenu();
  };
  
  // Handle copy query to clipboard
  const handleCopyQuery = () => {
    const query = historyData?.items.find(q => q.id === activeQueryId);
    if (query) {
      navigator.clipboard.writeText(query.sql_text);
      toast.info('Query copied to clipboard');
    }
    handleCloseMenu();
  };
  
  // Handle rerun query
  const handleRerunQuery = () => {
    const query = historyData?.items.find(q => q.id === activeQueryId);
    if (query) {
      rerunQueryMutation.mutate(query);
    }
    handleCloseMenu();
  };
  
  // Handle delete query history item
  const handleDeleteQuery = () => {
    if (activeQueryId && confirm('Are you sure you want to delete this query history item?')) {
      deleteQueryMutation.mutate(activeQueryId);
    }
    handleCloseMenu();
  };
  
  // Handle download query results
  const handleDownloadResults = () => {
    const query = historyData?.items.find(q => q.id === activeQueryId);
    if (query && query.result_id) {
      queryApi.downloadQueryResult(query.result_id);
    }
    handleCloseMenu();
  };
  
  // Format date for display
  const formatDate = (date: string) => {
    return format(new Date(date), 'yyyy-MM-dd HH:mm:ss');
  };
  
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return 'success';
      case 'error':
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };
  
  // Filtered queries based on search term
  const filteredQueries = historyData?.items.filter(query => {
    if (!searchTerm) return true;
    
    const search = searchTerm.toLowerCase();
    return (
      query.sql_text.toLowerCase().includes(search) ||
      (query.server_name && query.server_name.toLowerCase().includes(search)) ||
      (query.database_name && query.database_name.toLowerCase().includes(search))
    );
  }) || [];
  
  // Effect to check for selectedQueryId from URL
  useEffect(() => {
    if (selectedQueryId && !selectedQuery && !isLoadingDetail && !queryDetail) {
      queryClient.fetchQuery(['query-detail', selectedQueryId]);
    }
  }, [selectedQueryId, selectedQuery, isLoadingDetail, queryDetail]);
  
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Query History
      </Typography>
      
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <TextField
          placeholder="Search queries..."
          value={searchTerm}
          onChange={handleSearchChange}
          variant="outlined"
          size="small"
          sx={{ width: 300 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
        
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={() => refetchHistory()}
          disabled={isLoadingHistory}
        >
          Refresh
        </Button>
      </Box>
      
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabIndex}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab 
            label={
              <Badge 
                badgeContent={historyData?.total || 0} 
                color="primary"
                max={999}
                showZero
              >
                All Queries
              </Badge>
            } 
            id="query-history-tab-0"
          />
          <Tab 
            label={
              <Badge 
                badgeContent={historyData?.stats?.success || 0} 
                color="success"
                max={999}
                showZero
              >
                Successful
              </Badge>
            } 
            id="query-history-tab-1"
          />
          <Tab 
            label={
              <Badge 
                badgeContent={historyData?.stats?.error || 0} 
                color="error"
                max={999}
                showZero
              >
                Failed
              </Badge>
            } 
            id="query-history-tab-2"
          />
        </Tabs>
        
        <TabPanel value={tabIndex} index={0}>
          <QueryHistoryTable 
            queries={filteredQueries}
            isLoading={isLoadingHistory}
            error={historyError}
            onViewQuery={handleViewQuery}
            onOpenMenu={handleOpenMenu}
          />
        </TabPanel>
        
        <TabPanel value={tabIndex} index={1}>
          <QueryHistoryTable 
            queries={filteredQueries}
            isLoading={isLoadingHistory}
            error={historyError}
            onViewQuery={handleViewQuery}
            onOpenMenu={handleOpenMenu}
          />
        </TabPanel>
        
        <TabPanel value={tabIndex} index={2}>
          <QueryHistoryTable 
            queries={filteredQueries}
            isLoading={isLoadingHistory}
            error={historyError}
            onViewQuery={handleViewQuery}
            onOpenMenu={handleOpenMenu}
          />
        </TabPanel>
        
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={historyData?.total || 0}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
      
      {/* Query actions menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={() => handleViewQuery(historyData?.items.find(q => q.id === activeQueryId))}>
          <ListItemIcon>
            <VisibilityIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleRerunQuery}>
          <ListItemIcon>
            <PlayArrowIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Run Again</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleCopyQuery}>
          <ListItemIcon>
            <ContentCopyIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Copy SQL</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleSaveQuery}>
          <ListItemIcon>
            <SaveIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Save Query</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleScheduleQuery}>
          <ListItemIcon>
            <ScheduleIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Schedule Query</ListItemText>
        </MenuItem>
        
        <Divider />
        
        <MenuItem 
          onClick={handleDownloadResults}
          disabled={!historyData?.items.find(q => q.id === activeQueryId)?.result_id}
        >
          <ListItemIcon>
            <FileDownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download Results</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleDeleteQuery}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>
      
      {/* Query detail dialog */}
      <Dialog
        open={showDetailDialog}
        onClose={() => setShowDetailDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Query Details
          <IconButton
            aria-label="close"
            onClick={() => setShowDetailDialog(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {isLoadingDetail ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : selectedQuery ? (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Execution Time</Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatDate(selectedQuery.executed_at)}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Status</Typography>
                  <Typography variant="body1" gutterBottom>
                    <Chip 
                      label={selectedQuery.status.toUpperCase()} 
                      color={getStatusColor(selectedQuery.status)} 
                      size="small" 
                    />
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Server</Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedQuery.server_name || selectedQuery.server_id}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Database</Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedQuery.database_name || 'Unknown'}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Duration</Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatDuration(selectedQuery.duration_ms)}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Rows Affected/Returned</Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedQuery.row_count || 0}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Result Size</Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatBytes(selectedQuery.result_size_bytes || 0)}
                  </Typography>
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" gutterBottom>SQL Query</Typography>
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    overflow: 'auto',
                    maxHeight: 200
                  }}
                >
                  {selectedQuery.sql_text}
                </Paper>
                
                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    startIcon={<ContentCopyIcon />}
                    onClick={() => {
                      navigator.clipboard.writeText(selectedQuery.sql_text);
                      toast.info('Query copied to clipboard');
                    }}
                  >
                    Copy SQL
                  </Button>
                </Box>
              </Box>
              
              {selectedQuery.error_message && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" color="error" gutterBottom>Error Message</Typography>
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      p: 2, 
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      overflow: 'auto',
                      maxHeight: 200,
                      color: 'error.main',
                      bgcolor: 'error.light',
                      opacity: 0.8
                    }}
                  >
                    {selectedQuery.error_message}
                  </Paper>
                </Box>
              )}
              
              {selectedQuery.status === 'success' && selectedQuery.result_id && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>Query Results</Typography>
                  <QueryResultDisplay resultId={selectedQuery.result_id} />
                </Box>
              )}
              
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Button
                  variant="outlined"
                  startIcon={<ScheduleIcon />}
                  onClick={() => {
                    setShowDetailDialog(false);
                    setShowScheduleDialog(true);
                  }}
                >
                  Schedule
                </Button>
                
                <Box>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this query history item?')) {
                        deleteQueryMutation.mutate(selectedQuery.id);
                        setShowDetailDialog(false);
                      }
                    }}
                    sx={{ mr: 1 }}
                  >
                    Delete
                  </Button>
                  
                  <Button
                    variant="contained"
                    startIcon={<PlayArrowIcon />}
                    onClick={() => {
                      rerunQueryMutation.mutate(selectedQuery);
                      setShowDetailDialog(false);
                    }}
                  >
                    Run Again
                  </Button>
                </Box>
              </Box>
            </Box>
          ) : (
            <Alert severity="error">
              Query details not found
            </Alert>
          )}
        </DialogContent>
      </Dialog>
      
      {/* Save Query Dialog */}
      {showSaveDialog && selectedQuery && (
        <SaveQueryDialog
          open={showSaveDialog}
          onClose={() => setShowSaveDialog(false)}
          initialValues={{
            name: '',
            description: '',
            sql: selectedQuery.sql_text,
            serverId: selectedQuery.server_id
          }}
          onSave={() => {
            toast.success('Query saved successfully');
            setShowSaveDialog(false);
          }}
        />
      )}
      
      {/* Schedule Query Dialog */}
      {showScheduleDialog && selectedQuery && (
        <ScheduleQueryDialog
          open={showScheduleDialog}
          onClose={() => setShowScheduleDialog(false)}
          initialValues={{
            name: '',
            description: '',
            sql: selectedQuery.sql_text,
            serverId: selectedQuery.server_id,
            schedule: {
              type: 'daily',
              time: '08:00'
            }
          }}
          onSchedule={() => {
            toast.success('Query scheduled successfully');
            setShowScheduleDialog(false);
          }}
        />
      )}
    </Box>
  );
};

export default QueryHistoryViewer;

// Son güncelleme: 2025-05-21 07:14:55
// Güncelleyen: Teeksss