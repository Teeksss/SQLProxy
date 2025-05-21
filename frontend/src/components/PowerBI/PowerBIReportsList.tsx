/**
 * PowerBI Reports List Component
 * 
 * Displays and manages PowerBI reports with filtering and embedding options
 * 
 * Last updated: 2025-05-21 05:48:50
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Divider,
  CircularProgress,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  AlertTitle
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import SettingsIcon from '@mui/icons-material/Settings';
import { toast } from 'react-toastify';

import { powerbiApi } from '../../services/powerbiService';
import PowerBIReportEmbed from './PowerBIReportEmbed';
import CreatePowerBIReportForm from './CreatePowerBIReportForm';
import NoDataPlaceholder from '../common/NoDataPlaceholder';
import ConfirmationDialog from '../common/ConfirmationDialog';
import { formatDateTime } from '../../utils/formatters';

const PowerBIReportsList: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEmbedDialog, setShowEmbedDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedReport, setSelectedReport] = useState<any>(null);

  const queryClient = useQueryClient();

  // Query for fetching workspaces
  const {
    data: workspaces,
    isLoading: isLoadingWorkspaces
  } = useQuery(
    ['powerbi-workspaces'],
    powerbiApi.getWorkspaces,
    {
      staleTime: 300000 // 5 minutes
    }
  );

  // Query for fetching reports
  const {
    data: reports,
    isLoading: isLoadingReports,
    error: reportsError,
    refetch: refetchReports
  } = useQuery(
    ['powerbi-reports', selectedWorkspace],
    () => powerbiApi.getReports(selectedWorkspace || undefined),
    {
      staleTime: 60000 // 1 minute
    }
  );

  // Delete report mutation
  const deleteReportMutation = useMutation(
    (reportId: string) => powerbiApi.deleteReport(reportId),
    {
      onSuccess: () => {
        toast.success('Report deleted successfully');
        queryClient.invalidateQueries(['powerbi-reports']);
        setShowDeleteDialog(false);
      },
      onError: (error: any) => {
        toast.error(`Error deleting report: ${error.message}`);
      }
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
    setPage(0);
  };

  // Handle workspace change
  const handleWorkspaceChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedWorkspace(event.target.value as string);
    setPage(0);
  };

  // Open embed dialog
  const handleOpenEmbedDialog = (report: any) => {
    setSelectedReport(report);
    setShowEmbedDialog(true);
  };

  // Open delete dialog
  const handleOpenDeleteDialog = (report: any) => {
    setSelectedReport(report);
    setShowDeleteDialog(true);
  };

  // Handle confirm delete
  const handleConfirmDelete = () => {
    if (selectedReport) {
      deleteReportMutation.mutate(selectedReport.report_id);
    }
  };

  // Filter reports by search term
  const filteredReports = React.useMemo(() => {
    if (!reports?.items) return [];
    
    return reports.items.filter(report => 
      searchTerm === '' || 
      report.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (report.description && report.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [reports?.items, searchTerm]);

  // Get paginated reports
  const paginatedReports = React.useMemo(() => {
    const startIndex = page * rowsPerPage;
    return filteredReports.slice(startIndex, startIndex + rowsPerPage);
  }, [filteredReports, page, rowsPerPage]);

  // Loading state
  if (isLoadingReports && !reports) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (reportsError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading PowerBI reports: {(reportsError as Error).message}
      </Alert>
    );
  }

  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          PowerBI Reports
        </Typography>
        
        <Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowCreateDialog(true)}
            sx={{ ml: 1 }}
          >
            Create Report
          </Button>
        </Box>
      </Box>
      
      <Paper variant="outlined" sx={{ mb: 3, p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search reports..."
              value={searchTerm}
              onChange={handleSearchChange}
              variant="outlined"
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small" variant="outlined">
              <InputLabel id="workspace-filter-label">Workspace</InputLabel>
              <Select
                labelId="workspace-filter-label"
                id="workspace-filter"
                value={selectedWorkspace}
                onChange={handleWorkspaceChange as any}
                label="Workspace"
              >
                <MenuItem value="">All Workspaces</MenuItem>
                {workspaces?.items?.map((workspace: any) => (
                  <MenuItem key={workspace.workspace_id} value={workspace.workspace_id}>
                    {workspace.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={4} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Tooltip title="Refresh">
              <IconButton onClick={() => refetchReports()}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>
      </Paper>
      
      {!reports?.items || reports.items.length === 0 ? (
        <NoDataPlaceholder message="No PowerBI reports found" />
      ) : (
        <>
          <TableContainer component={Paper} variant="outlined">
            <Table size="medium">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Workspace</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Last Refreshed</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedReports.map((report) => {
                  // Find workspace name
                  const workspace = workspaces?.items?.find(
                    (w: any) => w.workspace_id === report.workspace_id
                  );
                  const workspaceName = workspace ? workspace.name : 'My Workspace';
                  
                  return (
                    <TableRow key={report.report_id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {report.name}
                        </Typography>
                        {report.description && (
                          <Typography variant="caption" color="text.secondary">
                            {report.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{workspaceName}</TableCell>
                      <TableCell>{formatDateTime(report.created_at)}</TableCell>
                      <TableCell>
                        {report.last_refreshed_at ? formatDateTime(report.last_refreshed_at) : 'Never'}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          size="small"
                          label={report.last_refresh_status || 'N/A'} 
                          color={
                            report.last_refresh_status === 'Succeeded' ? 'success' :
                            report.last_refresh_status === 'Failed' ? 'error' :
                            'default'
                          }
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="View Report">
                          <IconButton 
                            size="small" 
                            onClick={() => handleOpenEmbedDialog(report)}
                            color="primary"
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Report">
                          <IconButton 
                            size="small" 
                            onClick={() => handleOpenDeleteDialog(report)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
          
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredReports.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </>
      )}
      
      {/* Create Report Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create PowerBI Report</DialogTitle>
        <DialogContent>
          <CreatePowerBIReportForm 
            workspaces={workspaces?.items || []}
            onSuccess={() => {
              setShowCreateDialog(false);
              queryClient.invalidateQueries(['powerbi-reports']);
              toast.success('Report created successfully');
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
      
      {/* Embed Report Dialog */}
      <Dialog
        open={showEmbedDialog}
        onClose={() => setShowEmbedDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>{selectedReport?.name}</DialogTitle>
        <DialogContent dividers>
          {selectedReport && (
            <PowerBIReportEmbed 
              reportId={selectedReport.report_id} 
              embedHeight={600}
              onReportError={(error) => {
                toast.error(`Error loading report: ${error.message || 'Unknown error'}`);
              }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEmbedDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleConfirmDelete}
        title="Delete PowerBI Report"
        content="Are you sure you want to delete this report? This action cannot be undone."
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isSubmitting={deleteReportMutation.isLoading}
      />
    </Box>
  );
};

export default PowerBIReportsList;

// Son güncelleme: 2025-05-21 05:48:50
// Güncelleyen: Teeksss