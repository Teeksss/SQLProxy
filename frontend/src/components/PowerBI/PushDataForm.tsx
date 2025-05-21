/**
 * Push Data Form Component
 * 
 * Form for pushing data to PowerBI datasets from SQL queries or direct input
 * 
 * Last updated: 2025-05-21 06:28:06
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Divider,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tab,
  Tabs,
  FormHelperText
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useQuery, useMutation } from 'react-query';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import CodeIcon from '@mui/icons-material/Code';
import StorageIcon from '@mui/icons-material/Storage';

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
      id={`push-data-tabpanel-${index}`}
      aria-labelledby={`push-data-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 1 }}>{children}</Box>}
    </div>
  );
};

interface PushDataFormProps {
  datasetId: string;
  tableName: string;
  workspaceId?: string;
  onSuccess: () => void;
}

const PushDataForm: React.FC<PushDataFormProps> = ({
  datasetId,
  tableName,
  workspaceId,
  onSuccess
}) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [sqlQuery, setSqlQuery] = useState('');
  const [queryError, setQueryError] = useState<string | null>(null);
  const [jsonData, setJsonData] = useState<string>('[]');
  const [jsonError, setJsonError] = useState<string | null>(null);

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

  // Mutation for pushing data from query
  const pushDataFromQueryMutation = useMutation(
    (data: any) => powerbiApi.pushDataFromQuery(
      datasetId,
      tableName,
      data.query_text,
      data.query_id,
      data.server_id,
      workspaceId
    ),
    {
      onSuccess: () => {
        onSuccess();
      }
    }
  );

  // Mutation for pushing JSON data
  const pushJsonDataMutation = useMutation(
    (data: any[]) => powerbiApi.pushData(
      datasetId,
      tableName,
      data,
      workspaceId
    ),
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

  // Validate JSON data
  const validateJsonData = (json: string): boolean => {
    try {
      const data = JSON.parse(json);
      if (!Array.isArray(data)) {
        setJsonError('Data must be an array of objects');
        return false;
      }
      if (data.length === 0) {
        setJsonError('Array cannot be empty');
        return false;
      }
      if (!data.every(item => typeof item === 'object' && item !== null)) {
        setJsonError('All items must be objects');
        return false;
      }
      setJsonError(null);
      return true;
    } catch (error) {
      setJsonError(`Invalid JSON: ${(error as Error).message}`);
      return false;
    }
  };

  // Handle JSON data change
  const handleJsonDataChange = (value: string) => {
    setJsonData(value);
    validateJsonData(value);
  };

  // SQL Query Form
  const queryFormik = useFormik({
    initialValues: {
      query_type: 'direct', // direct or saved
      query_id: '',
      server_id: ''
    },
    validationSchema: Yup.object({
      query_type: Yup.string().required('Query type is required'),
      query_id: Yup.string().when('query_type', {
        is: 'saved',
        then: Yup.string().required('Saved query is required')
      }),
      server_id: Yup.string().required('Server is required')
    }),
    onSubmit: (values) => {
      if (values.query_type === 'direct' && !sqlQuery) {
        setQueryError('SQL query is required');
        return;
      }

      setQueryError(null);

      // Push data from query
      pushDataFromQueryMutation.mutate({
        query_text: values.query_type === 'direct' ? sqlQuery : undefined,
        query_id: values.query_type === 'saved' ? values.query_id : undefined,
        server_id: values.server_id
      });
    }
  });

  // Handle JSON data submit
  const handleSubmitJsonData = () => {
    if (!validateJsonData(jsonData)) {
      return;
    }

    const data = JSON.parse(jsonData);
    pushJsonDataMutation.mutate(data);
  };

  // Determine if any push mutation is loading
  const isLoading = pushDataFromQueryMutation.isLoading || pushJsonDataMutation.isLoading;

  return (
    <Box>
      <Typography variant="body1" gutterBottom>
        Push data to the "{tableName}" table in the dataset. 
        You can push data from a SQL query or directly using JSON.
      </Typography>

      <Tabs value={tabIndex} onChange={handleTabChange} aria-label="push data tabs">
        <Tab 
          label="From SQL Query" 
          id="push-data-tab-0" 
          icon={<StorageIcon />} 
          iconPosition="start"
        />
        <Tab 
          label="From JSON" 
          id="push-data-tab-1" 
          icon={<CodeIcon />} 
          iconPosition="start"
        />
      </Tabs>

      <Divider sx={{ mb: 2 }} />

      {/* SQL Query Tab */}
      <TabPanel value={tabIndex} index={0}>
        <form onSubmit={queryFormik.handleSubmit}>
          <Grid container spacing={2}>
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
                  {isLoadingServers ? (
                    <MenuItem disabled>Loading servers...</MenuItem>
                  ) : servers?.length ? (
                    servers.map((server: any) => (
                      <MenuItem key={server.id} value={server.id}>
                        {server.alias || server.host} ({server.database})
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem disabled>No servers available</MenuItem>
                  )}
                </Select>
                {queryFormik.touched.server_id && queryFormik.errors.server_id && (
                  <FormHelperText>{queryFormik.errors.server_id}</FormHelperText>
                )}
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
                    {isLoadingSavedQueries ? (
                      <MenuItem disabled>Loading queries...</MenuItem>
                    ) : savedQueries?.length ? (
                      savedQueries.map((query: any) => (
                        <MenuItem key={query.id} value={query.id}>
                          {query.name}
                        </MenuItem>
                      ))
                    ) : (
                      <MenuItem disabled>No saved queries available</MenuItem>
                    )}
                  </Select>
                  {queryFormik.touched.query_id && queryFormik.errors.query_id && (
                    <FormHelperText>{queryFormik.errors.query_id}</FormHelperText>
                  )}
                </FormControl>
              </Grid>
            ) : (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
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
                  <Alert severity="error" sx={{ mt: 1 }}>
                    {queryError}
                  </Alert>
                )}
              </Grid>
            )}

            <Grid item xs={12}>
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <CircularProgress size={24} />
                  ) : (
                    'Push Data from Query'
                  )}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </TabPanel>

      {/* JSON Data Tab */}
      <TabPanel value={tabIndex} index={1}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>
              JSON Data (Array of Objects)
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Enter data as a JSON array of objects. Each object should have property names matching the dataset columns.
            </Typography>
            <Paper variant="outlined" sx={{ p: 1 }}>
              <TextField
                fullWidth
                multiline
                rows={10}
                value={jsonData}
                onChange={(e) => handleJsonDataChange(e.target.value)}
                placeholder='[
  {"column1": "value1", "column2": 42},
  {"column1": "value2", "column2": 43}
]'
                variant="outlined"
                sx={{ fontFamily: 'monospace' }}
              />
            </Paper>
            
            {jsonError && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {jsonError}
              </Alert>
            )}
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={handleSubmitJsonData}
                disabled={isLoading || !!jsonError}
              >
                {isLoading ? (
                  <CircularProgress size={24} />
                ) : (
                  'Push JSON Data'
                )}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </TabPanel>

      {pushDataFromQueryMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {(pushDataFromQueryMutation.error as Error).message}
        </Alert>
      )}

      {pushJsonDataMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {(pushJsonDataMutation.error as Error).message}
        </Alert>
      )}
    </Box>
  );
};

export default PushDataForm;

// Son güncelleme: 2025-05-21 06:28:06
// Güncelleyen: Teeksss