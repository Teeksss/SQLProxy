/**
 * PowerBI Dataset Manager Component
 * 
 * Manages PowerBI datasets, allowing creation, refreshing, and data pushing
 * 
 * Last updated: 2025-05-21 06:02:47
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Paper,
  Divider,
  Chip,
  IconButton,
  Tooltip,
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
  Tab,
  Tabs
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import ScheduleIcon from '@mui/icons-material/Schedule';
import HistoryIcon from '@mui/icons-material/History';
import DownloadIcon from '@mui/icons-material/Download';
import { toast } from 'react-toastify';

import { powerbiApi } from '../../services/powerbiService';
import NoDataPlaceholder from '../common/NoDataPlaceholder';
import ConfirmationDialog from '../common/ConfirmationDialog';
import { formatDateTime } from '../../utils/formatters';
import CreateDatasetForm from './CreateDatasetForm';
import RefreshScheduleForm from './RefreshScheduleForm';
import RefreshHistoryList from './RefreshHistoryList';

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
      id={`dataset-tabpanel-${index}`}
      aria-labelledby={`dataset-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 1 }}>{children}</Box>}
    </div>
  );
};

interface PowerBIDatasetManagerProps {
  workspaceId?: string;
}

const PowerBIDatasetManager: React.FC<PowerBIDatasetManagerProps> = ({ workspaceId }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<any>(null);
  const [tabIndex, setTabIndex] = useState(0);

  const queryClient = useQueryClient();

  // Query for fetching datasets
  const {
    data: datasets,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['powerbi-datasets', workspaceId],
    () => powerbiApi.getDatasets(workspaceId),
    {
      staleTime: 60000 // 1 minute
    }
  );

  // Mutation for refreshing dataset
  const refreshDatasetMutation = useMutation(
    (datasetId: string) => powerbiApi.refreshDataset(datasetId, workspaceId),
    {
      onSuccess: () => {
        toast.success('Dataset refresh started');
        queryClient.invalidateQueries(['powerbi-datasets']);
      },
      onError: (error: any) => {
        toast.error(`Error refreshing dataset: ${error.message}`);
      }
    }
  );

  // Mutation for deleting dataset
  const deleteDatasetMutation = useMutation(
    (datasetId: string) => powerbiApi.deleteDataset(datasetId, workspaceId),
    {
      onSuccess: () => {
        toast.success('Dataset deleted successfully');
        setShowDeleteDialog(false);
        queryClient.invalidateQueries(['powerbi-datasets']);
      },
      onError: (error: any) => {
        toast.error(`Error deleting dataset: ${error.message}`);
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

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  // Handle refresh dataset
  const handleRefreshDataset = (dataset: any) => {
    refreshDatasetMutation.mutate(dataset.dataset_id);
  };

  // Handle open delete dialog
  const handleOpenDeleteDialog = (dataset: any) => {
    setSelectedDataset(dataset);
    setShowDeleteDialog(true);
  };

  // Handle confirm delete
  const handleConfirmDelete = () => {
    if (selectedDataset) {
      deleteDatasetMutation.mutate(selectedDataset.dataset_id);
    }
  };

  // Handle open schedule dialog
  const handleOpenScheduleDialog = (dataset: any) => {
    setSelectedDataset(dataset);
    setShowScheduleDialog(true);
  };

  // Handle open history dialog
  const handleOpenHistoryDialog = (dataset: any) => {
    setSelectedDataset(dataset);
    setShowHistoryDialog(true);
  };

  // Handle export dataset data
  const handleExportData = (dataset: any, format: string = 'csv') => {
    // First we need to get the tables in the dataset
    // For simplicity, we'll assume there's a default table
    powerbiApi.exportDatasetData(dataset.dataset_id, 'QueryResults', format, workspaceId);
  };

  // Filter datasets by search term
  const filteredDatasets = React.useMemo(() => {
    if (!datasets?.items) return [];
    
    return datasets.items.filter(dataset => 
      searchTerm === '' || 
      dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (dataset.description && dataset.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [datasets?.items, searchTerm]);

  // Get paginated datasets
  const paginatedDatasets = React.useMemo(() => {
    const startIndex = page * rowsPerPage;
    return filteredDatasets.slice(startIndex, startIndex + rowsPerPage);
  }, [filteredDatasets, page, rowsPerPage]);

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
        Error loading PowerBI datasets: {(error as Error).message}
      </Alert>
    );
  }

  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          PowerBI Datasets
          {workspaceId && (
            <Typography variant="caption" sx={{ ml: 1 }}>
              (Workspace: {workspaceId})
            </Typography>
          )}
        </Typography>
        
        <Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowCreateDialog(true)}
          >
            Create Dataset
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            sx={{ ml: 1 }}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            placeholder="Search datasets..."
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            sx={{ width: 300 }}
          />
          
          <Tabs
            value={tabIndex}
            onChange={handleTabChange}
            aria-label="dataset tabs"
            sx={{ ml: 3 }}
          >
            <Tab label="All Datasets" id="dataset-tab-0" />
            <Tab label="Scheduled" id="dataset-tab-1" />
          </Tabs>
        </Box>
      </Paper>

      {!datasets?.items || datasets.items.length === 0 ? (
        <NoDataPlaceholder message="No PowerBI datasets found" />
      ) : (
        <>
          <TableContainer component={Paper} variant="outlined">
            <Table size="medium">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Workspace</TableCell>
                  <TableCell>Refresh Schedule</TableCell>
                  <TableCell>Last Refreshed</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedDatasets
                  .filter(dataset => {
                    if (tabIndex === 0) return true;
                    return tabIndex === 1 && dataset.refresh_schedule !== null;
                  })
                  .map((dataset) => (
                    <TableRow key={dataset.dataset_id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {dataset.name}
                        </Typography>
                        {dataset.description && (
                          <Typography variant="caption" color="text.secondary">
                            {dataset.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {dataset.workspace_id || 'My Workspace'}
                      </TableCell>
                      <TableCell>
                        {dataset.refresh_schedule ? (
                          <Chip 
                            size="small" 
                            label={dataset.refresh_schedule} 
                            color="primary" 
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Not scheduled
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {dataset.last_refreshed_at ? formatDateTime(dataset.last_refreshed_at) : 'Never'}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          size="small"
                          label={dataset.last_refresh_status || 'N/A'} 
                          color={
                            dataset.last_refresh_status === 'Completed' ? 'success' :
                            dataset.last_refresh_status === 'Failed' ? 'error' :
                            dataset.last_refresh_status === 'In Progress' ? 'warning' :
                            'default'
                          }
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Refresh Dataset">
                          <IconButton 
                            size="small" 
                            onClick={() => handleRefreshDataset(dataset)}
                            color="primary"
                            disabled={refreshDatasetMutation.isLoading}
                          >
                            <RefreshIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Refresh Schedule">
                          <IconButton 
                            size="small" 
                            onClick={() => handleOpenScheduleDialog(dataset)}
                            color="primary"
                          >
                            <ScheduleIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Refresh History">
                          <IconButton 
                            size="small" 
                            onClick={() => handleOpenHistoryDialog(dataset)}
                          >
                            <HistoryIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Export Data">
                          <IconButton 
                            size="small" 
                            onClick={() => handleExportData(dataset)}
                          >
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Delete Dataset">
                          <IconButton 
                            size="small" 
                            onClick={() => handleOpenDeleteDialog(dataset)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                
                {paginatedDatasets
                  .filter(dataset => {
                    if (tabIndex === 0) return true;
                    return tabIndex === 1 && dataset.refresh_schedule !== null;
                  })
                  .length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No datasets found matching the current filters
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredDatasets.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </>
      )}

      {/* Create Dataset Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create PowerBI Dataset</DialogTitle>
        <DialogContent>
          <CreateDatasetForm
            workspaceId={workspaceId}
            onSuccess={() => {
              setShowCreateDialog(false);
              queryClient.invalidateQueries(['powerbi-datasets']);
              toast.success('Dataset created successfully');
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Refresh Schedule Dialog */}
      {selectedDataset && (
        <Dialog
          open={showScheduleDialog}
          onClose={() => setShowScheduleDialog(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Refresh Schedule for {selectedDataset.name}</DialogTitle>
          <DialogContent>
            <RefreshScheduleForm
              dataset={selectedDataset}
              onSuccess={() => {
                setShowScheduleDialog(false);
                queryClient.invalidateQueries(['powerbi-datasets']);
                toast.success('Refresh schedule updated');
              }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowScheduleDialog(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Refresh History Dialog */}
      {selectedDataset && (
        <Dialog
          open={showHistoryDialog}
          onClose={() => setShowHistoryDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Refresh History for {selectedDataset.name}</DialogTitle>
          <DialogContent>
            <RefreshHistoryList
              datasetId={selectedDataset.dataset_id}
              workspaceId={selectedDataset.workspace_id || workspaceId}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowHistoryDialog(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleConfirmDelete}
        title="Delete PowerBI Dataset"
        content={
          <>
            <Typography variant="body1" gutterBottom>
              Are you sure you want to delete the dataset "{selectedDataset?.name}"?
            </Typography>
            <Typography variant="body2" color="error">
              This action cannot be undone. All reports using this dataset may also be affected.
            </Typography>
          </>
        }
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isSubmitting={deleteDatasetMutation.isLoading}
      />
    </Box>
  );
};

export default PowerBIDatasetManager;

// Son güncelleme: 2025-05-21 06:02:47
// Güncelleyen: Teeksss