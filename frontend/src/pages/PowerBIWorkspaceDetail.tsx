/**
 * PowerBI Workspace Detail Page
 * 
 * Displays detailed information about a PowerBI workspace including
 * its reports and datasets
 * 
 * Last updated: 2025-05-21 06:28:06
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
import AddIcon from '@mui/icons-material/Add';
import BarChartIcon from '@mui/icons-material/BarChart';
import StorageIcon from '@mui/icons-material/Storage';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import RefreshIcon from '@mui/icons-material/Refresh';
import { toast } from 'react-toastify';

import { powerbiApi } from '../services/powerbiService';
import PageHeader from '../components/common/PageHeader';
import PowerBIReportsList from '../components/PowerBI/PowerBIReportsList';
import PowerBIDatasetManager from '../components/PowerBI/PowerBIDatasetManager';
import ConfirmationDialog from '../components/common/ConfirmationDialog';
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
      id={`workspace-detail-tabpanel-${index}`}
      aria-labelledby={`workspace-detail-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
};

const PowerBIWorkspaceDetail: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const isMyWorkspace = workspaceId === 'my';
  const actualWorkspaceId = isMyWorkspace ? undefined : workspaceId;
  
  const [tabIndex, setTabIndex] = useState(0);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query for fetching workspace details
  const {
    data: workspace,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['powerbi-workspace', actualWorkspaceId],
    () => actualWorkspaceId ? powerbiApi.getWorkspace(actualWorkspaceId) : { name: 'My Workspace', description: 'Default personal workspace' },
    {
      staleTime: 300000, // 5 minutes
      enabled: !isLoading
    }
  );

  // Mutation for deleting workspace
  const deleteWorkspaceMutation = useMutation(
    () => powerbiApi.deleteWorkspace(actualWorkspaceId as string),
    {
      onSuccess: () => {
        toast.success('Workspace deleted successfully');
        navigate('/powerbi');
      },
      onError: (error: any) => {
        toast.error(`Error deleting workspace: ${error.message}`);
      }
    }
  );

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  // Handle delete workspace
  const handleDeleteWorkspace = () => {
    if (isMyWorkspace) {
      toast.error('My Workspace cannot be deleted');
      return;
    }
    setShowDeleteDialog(true);
  };

  // Handle confirm delete
  const handleConfirmDelete = () => {
    if (actualWorkspaceId) {
      deleteWorkspaceMutation.mutate();
    }
  };

  // Loading state
  if (isLoading && !isMyWorkspace) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error && !isMyWorkspace) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading workspace: {((error as Error)?.message) || 'Workspace not found'}
      </Alert>
    );
  }

  const workspaceName = workspace?.name || 'Workspace';

  return (
    <>
      <Helmet>
        <title>{`${workspaceName} | SQL Proxy PowerBI`}</title>
      </Helmet>

      <PageHeader 
        title={workspaceName}
        subtitle="PowerBI Workspace"
        actions={
          <>
            {!isMyWorkspace && (
              <Button
                variant="outlined"
                startIcon={<DeleteIcon />}
                onClick={handleDeleteWorkspace}
                color="error"
                sx={{ mr: 1 }}
              >
                Delete Workspace
              </Button>
            )}
            
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setTabIndex(tabIndex === 0 ? 0 : 0)}
            >
              New Report
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
                aria-label="workspace details tabs"
                sx={{ px: 2, pt: 1 }}
              >
                <Tab 
                  label="Reports" 
                  id="workspace-detail-tab-0" 
                  icon={<BarChartIcon />}
                  iconPosition="start"
                />
                <Tab 
                  label="Datasets" 
                  id="workspace-detail-tab-1" 
                  icon={<StorageIcon />}
                  iconPosition="start"
                />
              </Tabs>
              <Divider />
              
              <TabPanel value={tabIndex} index={0}>
                <PowerBIReportsList workspaceId={actualWorkspaceId} />
              </TabPanel>
              
              <TabPanel value={tabIndex} index={1}>
                <PowerBIDatasetManager workspaceId={actualWorkspaceId} />
              </TabPanel>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Workspace Information
                </Typography>
                
                <Divider sx={{ mb: 2 }} />
                
                {workspace?.description && (
                  <Typography variant="body2" paragraph>
                    {workspace.description}
                  </Typography>
                )}
                
                {!isMyWorkspace && workspace?.created_at && (
                  <Typography variant="body2" color="text.secondary">
                    Created: {formatDateTime(workspace.created_at)}
                  </Typography>
                )}
                
                {!isMyWorkspace && workspace?.updated_at && (
                  <Typography variant="body2" color="text.secondary">
                    Last Updated: {formatDateTime(workspace.updated_at)}
                  </Typography>
                )}
                
                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<RefreshIcon />}
                    onClick={() => {
                      refetch();
                      queryClient.invalidateQueries(['powerbi-reports', actualWorkspaceId]);
                      queryClient.invalidateQueries(['powerbi-datasets', actualWorkspaceId]);
                    }}
                  >
                    Refresh
                  </Button>
                  
                  {!isMyWorkspace && (
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={() => setShowEditDialog(true)}
                    >
                      Edit
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
            
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Quick Actions
                </Typography>
                
                <Divider sx={{ mb: 2 }} />
                
                <List>
                  <ListItem 
                    button
                    onClick={() => setTabIndex(0)}
                  >
                    <ListItemIcon>
                      <BarChartIcon />
                    </ListItemIcon>
                    <ListItemText primary="View Reports" />
                  </ListItem>
                  
                  <ListItem 
                    button
                    onClick={() => setTabIndex(1)}
                  >
                    <ListItemIcon>
                      <StorageIcon />
                    </ListItemIcon>
                    <ListItemText primary="Manage Datasets" />
                  </ListItem>
                  
                  <ListItem 
                    button
                    component="a"
                    href="/powerbi/workspaces"
                  >
                    <ListItemIcon>
                      <StorageIcon />
                    </ListItemIcon>
                    <ListItemText primary="All Workspaces" />
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
        title="Delete PowerBI Workspace"
        content={
          <>
            <Typography variant="body1" gutterBottom>
              Are you sure you want to delete the workspace "{workspace?.name}"?
            </Typography>
            <Typography variant="body2" color="error">
              This action cannot be undone. All reports and datasets in this workspace will also be deleted.
            </Typography>
          </>
        }
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isSubmitting={deleteWorkspaceMutation.isLoading}
      />
    </>
  );
};

export default PowerBIWorkspaceDetail;

// Son güncelleme: 2025-05-21 06:28:06
// Güncelleyen: Teeksss