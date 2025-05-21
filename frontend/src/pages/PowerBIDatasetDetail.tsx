/**
 * PowerBI Dataset Detail Page
 * 
 * Displays detailed information about a PowerBI dataset
 * 
 * Last updated: 2025-05-21 06:23:45
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Container,
  Grid,
  Paper,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Button,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Helmet } from 'react-helmet-async';
import RefreshIcon from '@mui/icons-material/Refresh';
import StorageIcon from '@mui/icons-material/Storage';
import DeleteIcon from '@mui/icons-material/Delete';
import ScheduleIcon from '@mui/icons-material/Schedule';
import HistoryIcon from '@mui/icons-material/History';
import TableChartIcon from '@mui/icons-material/TableChart';
import UploadIcon from '@mui/icons-material/Upload';
import { toast } from 'react-toastify';

import { powerbiApi } from '../services/powerbiService';
import PageHeader from '../components/common/PageHeader';
import RefreshScheduleForm from '../components/PowerBI/RefreshScheduleForm';
import RefreshHistoryList from '../components/PowerBI/RefreshHistoryList';
import ConfirmationDialog from '../components/common/ConfirmationDialog';
import PushDataForm from '../components/PowerBI/PushDataForm';
import { formatDateTime } from '../utils/formatters';

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
      id={`dataset-detail-tabpanel-${index}`}
      aria-labelledby={`dataset-detail-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
};

const PowerBIDatasetDetail: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [tabIndex, setTabIndex] = useState(0);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showPushDataDialog, setShowPushDataDialog] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query for fetching dataset details
  const {
    data: dataset,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['powerbi-dataset', datasetId],
    () => powerbiApi.getDataset(datasetId as string),
    {
      enabled: !!datasetId,
      staleTime: 60000 // 1 minute
    }
  );

  // Query for fetching dataset tables
  const {
    data: tables,
    isLoading: isLoadingTables
  } = useQuery(
    ['powerbi-dataset-tables', datasetId],
    () => powerbiApi.getDatasetTables(datasetId as string, dataset?.workspace_id),
    {
      enabled: !!datasetId && !!dataset,
      staleTime: 300000 // 5 minutes
    }
  );

  // Mutation for refreshing dataset
  const refreshDatasetMutation = useMutation(
    () => powerbiApi.refreshDataset(datasetId as string, dataset?.workspace_id),
    {
      onSuccess: () => {
        toast.success('Dataset refresh started');
        queryClient.invalidateQueries(['powerbi-dataset', datasetId]);
      },
      onError: (error: any) => {
        toast.error(`Error refreshing dataset: ${error.message}`);
      }
    }
  );

  // Mutation for deleting dataset
  const deleteDatasetMutation = useMutation(
    () => powerbiApi.deleteDataset(datasetId as string, dataset?.workspace_id),
    {
      onSuccess: () => {
        toast.success('Dataset deleted successfully');
        navigate('/powerbi/datasets');
      },
      onError: (error: any) => {
        toast.error(`Error deleting dataset: ${error.message}`);
      }
    }
  );

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  // Handle refresh dataset
  const handleRefreshDataset = () => {
    refreshDatasetMutation.mutate();
  };

  // Handle delete dataset
  const handleDeleteDataset = () => {
    setShowDeleteDialog(true);
  };

  // Handle confirm delete
  const handleConfirmDelete = () => {
    deleteDatasetMutation.mutate();
  };

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error || !dataset) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading dataset: {((error as Error)?.message) || 'Dataset not found'}
      </Alert>
    );
  }

  return (
    <>
      <Helmet>
        <title>{`Dataset: ${dataset.name} | SQL Proxy PowerBI`}</title>
      </Helmet>

      <PageHeader 
        title={dataset.name} 
        subtitle="PowerBI Dataset"
        actions={
          <>
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              onClick={() => setShowPushDataDialog(true)}
              sx={{ mr: 1 }}
            >
              Push Data
            </Button>
            
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={handleRefreshDataset}
              disabled={refreshDatasetMutation.isLoading}
            >
              {refreshDatasetMutation.isLoading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Refresh Dataset'
              )}
            </Button>
          </>
        }
      />

      <Container maxWidth="xl">
        <Grid container spacing={3}>
          <Grid item xs={12} md={9}>
            <Paper variant="outlined">
              <Tabs
                value={tabIndex}
                onChange={handleTabChange}
                aria-label="dataset details tabs"
                sx={{ px: 2, pt: 1 }}
              >
                <Tab label="Overview" id="dataset-detail-tab-0" />
                <Tab label="Refresh Schedule" id="dataset-detail-tab-1" />
                <Tab label="Refresh History" id="dataset-detail-tab-2" />
              </Tabs>
              <Divider />
              
              <TabPanel value={tabIndex} index={0}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>
                      Dataset Information
                    </Typography>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        ID:
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                        {dataset.dataset_id}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        Workspace:
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                        {dataset.workspace_id || 'My Workspace'}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        Created:
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                        {formatDateTime(dataset.created_at)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        Last Updated:
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                        {dataset.updated_at ? formatDateTime(dataset.updated_at) : 'Never'}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        Refresh Schedule:
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                        {dataset.refresh_schedule || 'Not scheduled'}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        Last Refreshed:
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                        {dataset.last_refreshed_at ? formatDateTime(dataset.last_refreshed_at) : 'Never'}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        Status:
                      </Typography>
                      <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                        {dataset.last_refresh_status || 'N/A'}
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>
                      Dataset Tables
                    </Typography>
                    
                    {isLoadingTables ? (
                      <CircularProgress size={24} />
                    ) : tables?.tables && tables.tables.length > 0 ? (
                      <List>
                        {tables.tables.map((table: any) => (
                          <Paper 
                            key={table.name} 
                            variant="outlined" 
                            sx={{ mb: 2, p: 1 }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              <TableChartIcon color="primary" sx={{ mr: 1 }} />
                              <Typography variant="subtitle2">
                                {table.name}
                              </Typography>
                            </Box>
                            
                            <Box sx={{ pl: 4 }}>
                              <Typography variant="body2" color="text.secondary">
                                {table.columns?.length || 0} columns
                              </Typography>
                              
                              {table.columns && table.columns.length > 0 && (
                                <Box 
                                  component="pre" 
                                  sx={{ 
                                    mt: 1, 
                                    p: 1, 
                                    bgcolor: 'background.default',
                                    fontSize: 'x-small',
                                    borderRadius: 1,
                                    maxHeight: 150,
                                    overflow: 'auto'
                                  }}
                                >
                                  {table.columns.map((col: any) => (
                                    `${col.name} (${col.dataType})\n`
                                  ))}
                                </Box>
                              )}
                            </Box>
                          </Paper>
                        ))}
                      </List>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No tables information available
                      </Typography>
                    )}
                  </Grid>
                </Grid>
              </TabPanel>
              
              <TabPanel value={tabIndex} index={1}>
                <RefreshScheduleForm
                  dataset={dataset}
                  onSuccess={() => {
                    queryClient.invalidateQueries(['powerbi-dataset', datasetId]);
                    toast.success('Refresh schedule updated');
                  }}
                />
              </TabPanel>
              
              <TabPanel value={tabIndex} index={2}>
                <RefreshHistoryList
                  datasetId={datasetId as string}
                  workspaceId={dataset.workspace_id}
                />
              </TabPanel>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Actions
                </Typography>
                
                <List>
                  <ListItem 
                    button
                    onClick={handleRefreshDataset}
                    disabled={refreshDatasetMutation.isLoading}
                  >
                    <ListItemIcon>
                      <RefreshIcon />
                    </ListItemIcon>
                    <ListItemText primary="Refresh Dataset" />
                  </ListItem>
                  
                  <ListItem 
                    button
                    onClick={() => setTabIndex(1)}
                  >
                    <ListItemIcon>
                      <ScheduleIcon />
                    </ListItemIcon>
                    <ListItemText primary="Manage Schedule" />
                  </ListItem>
                  
                  <ListItem 
                    button
                    onClick={() => setShowPushDataDialog(true)}
                  >
                    <ListItemIcon>
                      <UploadIcon />
                    </ListItemIcon>
                    <ListItemText primary="Push Data" />
                  </ListItem>
                  
                  <ListItem 
                    button
                    onClick={handleDeleteDataset}
                  >
                    <ListItemIcon>
                      <DeleteIcon color="error" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Delete Dataset" 
                      primaryTypographyProps={{ color: 'error' }}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
            
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Related Resources
                </Typography>
                
                <List>
                  {dataset.workspace_id && (
                    <ListItem 
                      button
                      component="a"
                      href={`/powerbi/workspaces/${dataset.workspace_id}`}
                    >
                      <ListItemIcon>
                        <StorageIcon />
                      </ListItemIcon>
                      <ListItemText primary="View Workspace" />
                    </ListItem>
                  )}
                  
                  <ListItem 
                    button
                    component="a"
                    href="/powerbi/datasets"
                  >
                    <ListItemIcon>
                      <StorageIcon />
                    </ListItemIcon>
                    <ListItemText primary="All Datasets" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
      
      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleConfirmDelete}
        title="Delete PowerBI Dataset"
        content={
          <>
            <Typography variant="body1" gutterBottom>
              Are you sure you want to delete the dataset "{dataset.name}"?
            </Typography>
            <Typography variant="body2" color="error">
              This action cannot be undone. Any reports using this dataset will also be affected.
            </Typography>
          </>
        }
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isSubmitting={deleteDatasetMutation.isLoading}
      />
      
      {/* Push Data Dialog */}
      <Dialog
        open={showPushDataDialog}
        onClose={() => setShowPushDataDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Push Data to {dataset.name}
        </DialogTitle>
        <Divider />
        <Box sx={{ p: 3 }}>
          <PushDataForm
            datasetId={datasetId as string}
            workspaceId={dataset.workspace_id}
            tableName={tables?.tables?.[0]?.name || 'QueryResults'}
            onSuccess={() => {
              setShowPushDataDialog(false);
              queryClient.invalidateQueries(['powerbi-dataset', datasetId]);
              toast.success('Data pushed successfully');
            }}
          />
        </Box>
      </Dialog>
    </>
  );
};

export default PowerBIDatasetDetail;

// Son güncelleme: 2025-05-21 06:23:45
// Güncelleyen: Teeksss