/**
 * Create PowerBI Report Form Component
 * 
 * Form for creating new PowerBI reports from SQL queries or importing PBIX files
 * 
 * Last updated: 2025-05-21 05:48:50
 * Updated by: Teeksss
 */

import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Tab,
  Tabs,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  CircularProgress,
  Grid,
  Paper,
  Divider,
  Alert,
  AlertTitle
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useMutation, useQuery } from 'react-query';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

import { powerbiApi } from '../../services/powerbiService';
import { serverApi } from '../../services/serverService';
import { queryApi } from '../../services/queryService';
import SQLEditor from '../SQLEditor/SQLEditor';

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
      id={`create-report-tabpanel-${index}`}
      aria-labelledby={`create-report-tab-${index}`}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>{children}</Box>
      )}
    </div>
  );
};

interface CreatePowerBIReportFormProps {
  workspaces: any[];
  onSuccess: () => void;
}

const CreatePowerBIReportForm: React.FC<CreatePowerBIReportFormProps> = ({
  workspaces,
  onSuccess
}) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [sqlQuery, setSqlQuery] = useState('');
  const [queryError, setQueryError] = useState<string | null>(null);

  // Query for fetching servers
  const {
    data: servers,
    isLoading: isLoadingServers
  } = useQuery(
    ['servers'],
    serverApi.getServers,
    {
      staleTime: 300000 // 5 minutes
    }
  );

  // Query for fetching saved queries
  const {
    data: savedQueries,
    isLoading: isLoadingSavedQueries
  } = useQuery(
    ['saved-queries'],
    queryApi.getSavedQueries,
    {
      staleTime: 60000 // 1 minute
    }
  );

  // Mutation for creating report from query
  const createFromQueryMutation = useMutation(
    (data: any) => powerbiApi.createReportFromQuery(data),
    {
      onSuccess: () => {
        onSuccess();
      }
    }
  );

  // Mutation for importing PBIX file
  const importPbixMutation = useMutation(
    (data: FormData) => powerbiApi.importReport(data),
    {
      onSuccess: () => {
        onSuccess();
      }
    }
  );

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    }
  };

  // Trigger file input click
  const handleFileInputClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Clean up selected file
  const handleFileCleanup = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // SQL Query Tab Formik
  const queryFormik = useFormik({
    initialValues: {
      name: '',
      description: '',
      workspace_id: workspaces.length > 0 ? workspaces[0].workspace_id : '',
      server_id: '',
      query_id: '',
      query_type: 'direct' // direct or saved
    },
    validationSchema: Yup.object({
      name: Yup.string().required('Name is required'),
      description: Yup.string(),
      workspace_id: Yup.string(),
      server_id: Yup.string().required('Server is required'),
      query_id: Yup.string().when('query_type', {
        is: 'saved',
        then: Yup.string().required('Saved query is required')
      }),
      query_type: Yup.string().required()
    }),
    onSubmit: (values) => {
      if (values.query_type === 'direct' && !sqlQuery) {
        setQueryError('SQL query is required');
        return;
      }

      setQueryError(null);

      // Prepare data for API call
      const data = {
        name: values.name,
        description: values.description,
        workspace_id: values.workspace_id || undefined,
        server_id: values.server_id
      };

      if (values.query_type === 'direct') {
        createFromQueryMutation.mutate({
          ...data,
          query_text: sqlQuery
        });
      } else {
        createFromQueryMutation.mutate({
          ...data,
          query_id: values.query_id
        });
      }
    }
  });

  // Import PBIX Tab Formik
  const importFormik = useFormik({
    initialValues: {
      name: '',
      description: '',
      workspace_id: workspaces.length > 0 ? workspaces[0].workspace_id : ''
    },
    validationSchema: Yup.object({
      name: Yup.string().required('Name is required'),
      description: Yup.string(),
      workspace_id: Yup.string()
    }),
    onSubmit: (values) => {
      if (!selectedFile) {
        return;
      }

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('name', values.name);
      formData.append('description', values.description || '');
      if (values.workspace_id) {
        formData.append('workspace_id', values.workspace_id);
      }

      // Submit the form
      importPbixMutation.mutate(formData);
    }
  });

  return (
    <Box sx={{ minHeight: 400 }}>
      <Tabs value={tabIndex} onChange={handleTabChange} aria-label="create report tabs">
        <Tab label="Create from SQL Query" id="create-report-tab-0" />
        <Tab label="Import PBIX File" id="create-report-tab-1" />
      </Tabs>

      {/* Create from SQL Query Tab */}
      <TabPanel value={tabIndex} index={0}>
        <form onSubmit={queryFormik.handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                id="name"
                name="name"
                label="Report Name"
                value={queryFormik.values.name}
                onChange={queryFormik.handleChange}
                error={queryFormik.touched.name && Boolean(queryFormik.errors.name)}
                helperText={queryFormik.touched.name && queryFormik.errors.name}
                margin="normal"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl 
                fullWidth 
                margin="normal"
                error={queryFormik.touched.workspace_id && Boolean(queryFormik.errors.workspace_id)}
              >
                <InputLabel id="workspace-label">Workspace</InputLabel>
                <Select
                  labelId="workspace-label"
                  id="workspace_id"
                  name="workspace_id"
                  value={queryFormik.values.workspace_id}
                  onChange={queryFormik.handleChange}
                  label="Workspace"
                >
                  <MenuItem value="">My Workspace</MenuItem>
                  {workspaces.map((workspace) => (
                    <MenuItem key={workspace.workspace_id} value={workspace.workspace_id}>
                      {workspace.name}
                    </MenuItem>
                  ))}
                </Select>
                {queryFormik.touched.workspace_id && queryFormik.errors.workspace_id && (
                  <FormHelperText>{queryFormik.errors.workspace_id}</FormHelperText>
                )}
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                id="description"
                name="description"
                label="Description"
                value={queryFormik.values.description}
                onChange={queryFormik.handleChange}
                error={queryFormik.touched.description && Boolean(queryFormik.errors.description)}
                helperText={queryFormik.touched.description && queryFormik.errors.description}
                margin="normal"
                multiline
                rows={2}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControl 
                fullWidth 
                margin="normal"
                error={queryFormik.touched.server_id && Boolean(queryFormik.errors.server_id)}
              >
                <InputLabel id="server-label">Database Server</InputLabel>
                <Select
                  labelId="server-label"
                  id="server_id"
                  name="server_id"
                  value={queryFormik.values.server_id}
                  onChange={queryFormik.handleChange}
                  label="Database Server"
                >
                  {servers?.map((server: any) => (
                    <MenuItem key={server.id} value={server.id}>
                      {server.alias || server.host} ({server.database})
                    </MenuItem>
                  ))}
                </Select>
                {queryFormik.touched.server_id && queryFormik.errors.server_id && (
                  <FormHelperText>{queryFormik.errors.server_id}</FormHelperText>
                )}
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="query-type-label">Query Type</InputLabel>
                <Select
                  labelId="query-type-label"
                  id="query_type"
                  name="query_type"
                  value={queryFormik.values.query_type}
                  onChange={queryFormik.handleChange}
                  label="Query Type"
                >
                  <MenuItem value="direct">Direct SQL Query</MenuItem>
                  <MenuItem value="saved">Saved Query</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {queryFormik.values.query_type === 'saved' ? (
              <Grid item xs={12}>
                <FormControl 
                  fullWidth 
                  margin="normal"
                  error={queryFormik.touched.query_id && Boolean(queryFormik.errors.query_id)}
                >
                  <InputLabel id="saved-query-label">Saved Query</InputLabel>
                  <Select
                    labelId="saved-query-label"
                    id="query_id"
                    name="query_id"
                    value={queryFormik.values.query_id}
                    onChange={queryFormik.handleChange}
                    label="Saved Query"
                  >
                    {savedQueries?.map((query: any) => (
                      <MenuItem key={query.id} value={query.id}>
                        {query.name}
                      </MenuItem>
                    ))}
                  </Select>
                  {queryFormik.touched.query_id && queryFormik.errors.query_id && (
                    <FormHelperText>{queryFormik.errors.query_id}</FormHelperText>
                  )}
                </FormControl>
              </Grid>
            ) : (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  SQL Query
                </Typography>
                <Paper variant="outlined" sx={{ p: 1 }}>
                  <SQLEditor
                    value={sqlQuery}
                    onChange={(value) => {
                      setSqlQuery(value);
                      setQueryError(null);
                    }}
                    height="200px"
                  />
                </Paper>
                {queryError && (
                  <FormHelperText error>{queryError}</FormHelperText>
                )}
              </Grid>
            )}

            <Grid item xs={12}>
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={createFromQueryMutation.isLoading}
                >
                  {createFromQueryMutation.isLoading ? (
                    <CircularProgress size={24} />
                  ) : (
                    'Create Report'
                  )}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </TabPanel>

      {/* Import PBIX File Tab */}
      <TabPanel value={tabIndex} index={1}>
        <form onSubmit={importFormik.handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                id="name"
                name="name"
                label="Report Name"
                value={importFormik.values.name}
                onChange={importFormik.handleChange}
                error={importFormik.touched.name && Boolean(importFormik.errors.name)}
                helperText={importFormik.touched.name && importFormik.errors.name}
                margin="normal"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl 
                fullWidth 
                margin="normal"
                error={importFormik.touched.workspace_id && Boolean(importFormik.errors.workspace_id)}
              >
                <InputLabel id="workspace-label-import">Workspace</InputLabel>
                <Select
                  labelId="workspace-label-import"
                  id="workspace_id"
                  name="workspace_id"
                  value={importFormik.values.workspace_id}
                  onChange={importFormik.handleChange}
                  label="Workspace"
                >
                  <MenuItem value="">My Workspace</MenuItem>
                  {workspaces.map((workspace) => (
                    <MenuItem key={workspace.workspace_id} value={workspace.workspace_id}>
                      {workspace.name}
                    </MenuItem>
                  ))}
                </Select>
                {importFormik.touched.workspace_id && importFormik.errors.workspace_id && (
                  <FormHelperText>{importFormik.errors.workspace_id}</FormHelperText>
                )}
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                id="description"
                name="description"
                label="Description"
                value={importFormik.values.description}
                onChange={importFormik.handleChange}
                error={importFormik.touched.description && Boolean(importFormik.errors.description)}
                helperText={importFormik.touched.description && importFormik.errors.description}
                margin="normal"
                multiline
                rows={2}
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ mt: 2 }}>
                <input
                  type="file"
                  accept=".pbix"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  onChange={handleFileSelect}
                />
                <Paper
                  variant="outlined"
                  sx={{
                    p: 3,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: 'pointer',
                    bgcolor: 'background.default'
                  }}
                  onClick={handleFileInputClick}
                >
                  <CloudUploadIcon fontSize="large" color="primary" sx={{ mb: 2 }} />
                  {selectedFile ? (
                    <>
                      <Typography variant="subtitle1" gutterBottom>
                        {selectedFile.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </Typography>
                      <Button
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFileCleanup();
                        }}
                        sx={{ mt: 1 }}
                      >
                        Remove
                      </Button>
                    </>
                  ) : (
                    <>
                      <Typography variant="subtitle1" gutterBottom>
                        Drop a PowerBI (.pbix) file here
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        or click to browse files
                      </Typography>
                    </>
                  )}
                </Paper>
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={importPbixMutation.isLoading || !selectedFile}
                >
                  {importPbixMutation.isLoading ? (
                    <CircularProgress size={24} />
                  ) : (
                    'Upload Report'
                  )}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </TabPanel>

      {createFromQueryMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {(createFromQueryMutation.error as Error).message}
        </Alert>
      )}

      {importPbixMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {(importPbixMutation.error as Error).message}
        </Alert>
      )}
    </Box>
  );
};

export default CreatePowerBIReportForm;

// Son güncelleme: 2025-05-21 05:48:50
// Güncelleyen: Teeksss