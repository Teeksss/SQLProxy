/**
 * DSN Generator Form Component
 * 
 * Form for generating DSN (Data Source Name) configurations
 * for PowerBI and other data connectors
 * 
 * Last updated: 2025-05-21 06:45:04
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Paper,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Link,
  Chip
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import CodeIcon from '@mui/icons-material/Code';
import { toast } from 'react-toastify';

import { dsnApi } from '../../services/dsnService';
import { serverApi } from '../../services/serverService';

interface DSNGeneratorFormProps {
  initialServerId?: string;
}

const DSNGeneratorForm: React.FC<DSNGeneratorFormProps> = ({ initialServerId }) => {
  const [advancedMode, setAdvancedMode] = useState(false);
  const queryClient = useQueryClient();

  // Query for fetching DSN templates
  const {
    data: templatesData,
    isLoading: isLoadingTemplates,
    error: templatesError
  } = useQuery(
    ['dsn-templates'],
    dsnApi.getTemplates,
    {
      staleTime: 300000 // 5 minutes
    }
  );

  // Query for fetching user DSN configs
  const {
    data: userConfigsData,
    isLoading: isLoadingConfigs,
    error: configsError,
    refetch: refetchConfigs
  } = useQuery(
    ['dsn-user-configs'],
    dsnApi.getUserConfigs,
    {
      staleTime: 60000 // 1 minute
    }
  );

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

  // Mutation for generating DSN
  const generateDSNMutation = useMutation(
    (data: any) => dsnApi.generateDSN(data),
    {
      onSuccess: () => {
        toast.success('DSN configuration generated successfully');
        queryClient.invalidateQueries(['dsn-user-configs']);
        formik.resetForm();
      }
    }
  );

  // Mutation for deleting DSN config
  const deleteDSNConfigMutation = useMutation(
    (dsnName: string) => dsnApi.deleteUserConfig(dsnName),
    {
      onSuccess: () => {
        toast.success('DSN configuration deleted successfully');
        queryClient.invalidateQueries(['dsn-user-configs']);
      }
    }
  );

  // Form validation schema
  const validationSchema = Yup.object({
    templateId: Yup.string().required('Template is required'),
    serverId: Yup.string().required('Server is required'),
    dsnName: Yup.string().matches(/^[a-zA-Z0-9_]+$/, 'Only alphanumeric characters and underscores are allowed')
  });

  // Initialize form with formik
  const formik = useFormik({
    initialValues: {
      templateId: 'powerbi_direct', // Default template
      serverId: initialServerId || '',
      dsnName: '',
      additionalParams: '{}'
    },
    validationSchema,
    onSubmit: (values) => {
      generateDSNMutation.mutate(values);
    }
  });

  // Update form when initialServerId changes
  useEffect(() => {
    if (initialServerId) {
      formik.setFieldValue('serverId', initialServerId);
    }
  }, [initialServerId]);

  // Handle copy to clipboard
  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.info('Copied to clipboard');
  };

  // Handle DSN config deletion
  const handleDeleteConfig = (dsnName: string) => {
    if (confirm(`Are you sure you want to delete the DSN configuration "${dsnName}"?`)) {
      deleteDSNConfigMutation.mutate(dsnName);
    }
  };

  // Get available templates
  const templates = templatesData?.templates || {};
  const userConfigs = userConfigsData?.configs || [];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Generate PowerBI DSN Configuration
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        Generate Data Source Name (DSN) configurations for easy connection to your data sources from PowerBI and other tools.
      </Alert>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 3 }}>
            <form onSubmit={formik.handleSubmit}>
              <Typography variant="subtitle1" gutterBottom>
                New DSN Configuration
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl 
                    fullWidth 
                    error={formik.touched.templateId && Boolean(formik.errors.templateId)}
                  >
                    <InputLabel id="template-label">DSN Template Type</InputLabel>
                    <Select
                      labelId="template-label"
                      id="templateId"
                      name="templateId"
                      value={formik.values.templateId}
                      onChange={formik.handleChange}
                      label="DSN Template Type"
                    >
                      {isLoadingTemplates ? (
                        <MenuItem disabled>Loading templates...</MenuItem>
                      ) : (
                        Object.entries(templates).map(([id, template]: [string, any]) => (
                          <MenuItem key={id} value={id}>
                            {id === 'powerbi_direct' ? 'PowerBI Direct Connection' :
                             id === 'powerbi_odbc' ? 'PowerBI ODBC Connection' :
                             id.charAt(0).toUpperCase() + id.slice(1)}
                          </MenuItem>
                        ))
                      )}
                    </Select>
                    {formik.touched.templateId && formik.errors.templateId && (
                      <Typography variant="caption" color="error">
                        {formik.errors.templateId}
                      </Typography>
                    )}
                  </FormControl>
                </Grid>
                
                <Grid item xs={12}>
                  <FormControl 
                    fullWidth 
                    error={formik.touched.serverId && Boolean(formik.errors.serverId)}
                  >
                    <InputLabel id="server-label">Database Server</InputLabel>
                    <Select
                      labelId="server-label"
                      id="serverId"
                      name="serverId"
                      value={formik.values.serverId}
                      onChange={formik.handleChange}
                      label="Database Server"
                    >
                      {isLoadingServers ? (
                        <MenuItem disabled>Loading servers...</MenuItem>
                      ) : (
                        servers?.map((server: any) => (
                          <MenuItem key={server.id} value={server.id}>
                            {server.alias || server.host} ({server.database})
                          </MenuItem>
                        ))
                      )}
                    </Select>
                    {formik.touched.serverId && formik.errors.serverId && (
                      <Typography variant="caption" color="error">
                        {formik.errors.serverId}
                      </Typography>
                    )}
                  </FormControl>
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    id="dsnName"
                    name="dsnName"
                    label="DSN Name (optional)"
                    value={formik.values.dsnName}
                    onChange={formik.handleChange}
                    error={formik.touched.dsnName && Boolean(formik.errors.dsnName)}
                    helperText={
                      (formik.touched.dsnName && formik.errors.dsnName) || 
                      "Leave empty for auto-generated name"
                    }
                  />
                </Grid>
                
                {advancedMode && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      id="additionalParams"
                      name="additionalParams"
                      label="Additional Parameters (JSON)"
                      value={formik.values.additionalParams}
                      onChange={formik.handleChange}
                      multiline
                      rows={3}
                      error={formik.touched.additionalParams && Boolean(formik.errors.additionalParams)}
                      helperText={formik.touched.additionalParams && formik.errors.additionalParams}
                    />
                  </Grid>
                )}
                
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Button
                      variant="text"
                      onClick={() => setAdvancedMode(!advancedMode)}
                    >
                      {advancedMode ? 'Hide Advanced Options' : 'Show Advanced Options'}
                    </Button>
                    
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={generateDSNMutation.isLoading}
                    >
                      {generateDSNMutation.isLoading ? (
                        <CircularProgress size={24} />
                      ) : (
                        'Generate DSN'
                      )}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </form>
            
            {generateDSNMutation.isError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {(generateDSNMutation.error as Error).message}
              </Alert>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Your DSN Configurations
            </Typography>
            
            {isLoadingConfigs ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                <CircularProgress size={24} />
              </Box>
            ) : configsError ? (
              <Alert severity="error">
                {(configsError as Error).message}
              </Alert>
            ) : userConfigs.length === 0 ? (
              <Alert severity="info">
                You haven't created any DSN configurations yet. Use the form to generate your first configuration.
              </Alert>
            ) : (
              userConfigs.map((config: any, index: number) => (
                <Accordion key={index} variant="outlined" sx={{ mb: 1 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                      <Typography variant="subtitle2">
                        {config.dsn_name}
                      </Typography>
                      <Chip 
                        label={config.template_id} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Created: {new Date(config.created_at).toLocaleString()}
                      </Typography>
                      
                      <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between' }}>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<DownloadIcon />}
                          component="a"
                          href={config.download_url}
                          target="_blank"
                        >
                          Download
                        </Button>
                        
                        <Tooltip title="Delete Configuration">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteConfig(config.dsn_name)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))
            )}
          </Paper>
          
          {/* Connection String Preview */}
          {formik.values.serverId && (
            <Paper variant="outlined" sx={{ p: 3, mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Connection String Preview
              </Typography>
              
              <ConnectionStringPreview serverId={formik.values.serverId} />
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

// Connection String Preview Component
const ConnectionStringPreview: React.FC<{ serverId: string }> = ({ serverId }) => {
  const { data, isLoading, error } = useQuery(
    ['powerbi-connection', serverId],
    () => dsnApi.getPowerBIConnection(serverId),
    {
      enabled: !!serverId,
      staleTime: 300000 // 5 minutes
    }
  );

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.info('Copied to clipboard');
  };

  if (isLoading) {
    return <CircularProgress size={24} />;
  }

  if (error) {
    return <Alert severity="error">{(error as Error).message}</Alert>;
  }

  if (!data) {
    return <Alert severity="info">Select a server to see connection details</Alert>;
  }

  return (
    <Box>
      <Typography variant="body2" gutterBottom>
        <strong>Server:</strong> {data.server}
      </Typography>
      <Typography variant="body2" gutterBottom>
        <strong>Database:</strong> {data.database}
      </Typography>
      
      <Divider sx={{ my: 1 }} />
      
      <Box sx={{ mt: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle2">Connection String:</Typography>
          <Tooltip title="Copy Connection String">
            <IconButton
              size="small"
              onClick={() => handleCopyToClipboard(data.connection_string)}
            >
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Paper 
          variant="outlined" 
          sx={{ 
            p: 1, 
            mt: 0.5, 
            fontFamily: 'monospace', 
            fontSize: '0.8rem',
            wordBreak: 'break-all'
          }}
        >
          {data.connection_string}
        </Paper>
      </Box>
      
      <Alert severity="info" sx={{ mt: 2 }}>
        Replace <strong>YOUR_PASSWORD_HERE</strong> with your actual database password when using this connection string.
      </Alert>
    </Box>
  );
};

export default DSNGeneratorForm;

// Son güncelleme: 2025-05-21 06:45:04
// Güncelleyen: Teeksss