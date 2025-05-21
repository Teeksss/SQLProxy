/**
 * PowerBI Workspace Manager Component
 * 
 * Manages PowerBI workspaces, allowing creation, viewing and management
 * 
 * Last updated: 2025-05-21 05:48:50
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
  Tooltip
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import AddIcon from '@mui/icons-material/Add';
import FolderIcon from '@mui/icons-material/Folder';
import BarChartIcon from '@mui/icons-material/BarChart';
import StorageIcon from '@mui/icons-material/Storage';
import EditIcon from '@mui/icons-material/Edit';
import { toast } from 'react-toastify';

import { powerbiApi } from '../../services/powerbiService';
import NoDataPlaceholder from '../common/NoDataPlaceholder';

const PowerBIWorkspaceManager: React.FC = () => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const queryClient = useQueryClient();

  // Query for fetching workspaces
  const {
    data: workspaces,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['powerbi-workspaces'],
    powerbiApi.getWorkspaces,
    {
      staleTime: 300000 // 5 minutes
    }
  );

  // Mutation for creating workspace
  const createWorkspaceMutation = useMutation(
    (data: any) => powerbiApi.createWorkspace(data),
    {
      onSuccess: () => {
        toast.success('Workspace created successfully');
        setShowCreateDialog(false);
        queryClient.invalidateQueries(['powerbi-workspaces']);
        formik.resetForm();
      },
      onError: (error: any) => {
        toast.error(`Error creating workspace: ${error.message}`);
      }
    }
  );

  // Formik for creating workspace
  const formik = useFormik({
    initialValues: {
      name: '',
      description: ''
    },
    validationSchema: Yup.object({
      name: Yup.string().required('Name is required'),
      description: Yup.string()
    }),
    onSubmit: (values) => {
      createWorkspaceMutation.mutate(values);
    }
  });

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
        Error loading PowerBI workspaces: {(error as Error).message}
      </Alert>
    );
  }

  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h1">
          PowerBI Workspaces
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setShowCreateDialog(true)}
        >
          Create Workspace
        </Button>
      </Box>

      {!workspaces?.items || workspaces.items.length === 0 ? (
        <NoDataPlaceholder message="No PowerBI workspaces found" />
      ) : (
        <Grid container spacing={3}>
          {workspaces.items.map((workspace: any) => (
            <Grid item xs={12} sm={6} md={4} key={workspace.workspace_id}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <FolderIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6" component="div">
                      {workspace.name}
                    </Typography>
                  </Box>
                  
                  {workspace.description && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {workspace.description}
                    </Typography>
                  )}
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-around', mb: 1 }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Tooltip title="Reports">
                        <Box>
                          <BarChartIcon color="primary" />
                          <Typography variant="h6">
                            {workspace.reports_count || 0}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Reports
                          </Typography>
                        </Box>
                      </Tooltip>
                    </Box>
                    
                    <Box sx={{ textAlign: 'center' }}>
                      <Tooltip title="Datasets">
                        <Box>
                          <StorageIcon color="primary" />
                          <Typography variant="h6">
                            {workspace.datasets_count || 0}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Datasets
                          </Typography>
                        </Box>
                      </Tooltip>
                    </Box>
                  </Box>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    href={`/powerbi/workspaces/${workspace.workspace_id}`}
                  >
                    View Reports
                  </Button>
                  
                  <Button size="small" href={`/powerbi/workspaces/${workspace.workspace_id}/datasets`}>
                    View Datasets
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Workspace Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={formik.handleSubmit}>
          <DialogTitle>Create PowerBI Workspace</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              id="name"
              name="name"
              label="Workspace Name"
              value={formik.values.name}
              onChange={formik.handleChange}
              error={formik.touched.name && Boolean(formik.errors.name)}
              helperText={formik.touched.name && formik.errors.name}
              margin="normal"
              autoFocus
            />
            
            <TextField
              fullWidth
              id="description"
              name="description"
              label="Description"
              value={formik.values.description}
              onChange={formik.handleChange}
              error={formik.touched.description && Boolean(formik.errors.description)}
              helperText={formik.touched.description && formik.errors.description}
              margin="normal"
              multiline
              rows={3}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={createWorkspaceMutation.isLoading}
            >
              {createWorkspaceMutation.isLoading ? (
                <CircularProgress size={24} />
              ) : (
                'Create'
              )}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};

export default PowerBIWorkspaceManager;

// Son güncelleme: 2025-05-21 05:48:50
// Güncelleyen: Teeksss