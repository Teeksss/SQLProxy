/**
 * Server Form Component
 * 
 * Form for creating and editing database server connections
 * 
 * Last updated: 2025-05-21 06:51:05
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Grid,
  Paper,
  Alert,
  CircularProgress,
  Divider,
  Tooltip
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import InfoIcon from '@mui/icons-material/Info';

import { serverApi } from '../../services/serverService';
import { systemApi } from '../../services/systemService';

interface ServerFormProps {
  initialValues?: any;
  onSubmit: (values: any) => void;
  isSubmitting?: boolean;
  error?: string;
}

const ServerForm: React.FC<ServerFormProps> = ({
  initialValues,
  onSubmit,
  isSubmitting = false,
  error
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [advancedMode, setAdvancedMode] = useState(false);
  const [vaultAvailable, setVaultAvailable] = useState(false);

  // Check if Vault is available
  useEffect(() => {
    const checkVaultStatus = async () => {
      try {
        const status = await systemApi.getSystemStatus();
        setVaultAvailable(status?.services?.some(
          (service: any) => service.type === 'vault' && service.status === 'healthy'
        ) || false);
      } catch (error) {
        console.error('Error checking Vault status:', error);
        setVaultAvailable(false);
      }
    };

    checkVaultStatus();
  }, []);

  // Define validation schema
  const validationSchema = Yup.object({
    alias: Yup.string(),
    host: Yup.string().required('Host is required'),
    port: Yup.number().required('Port is required').min(1).max(65535),
    username: Yup.string().required('Username is required'),
    password: initialValues ? Yup.string() : Yup.string().required('Password is required'),
    database: Yup.string().required('Database name is required'),
    db_type: Yup.string().required('Database type is required')
  });

  // Initialize form with formik
  const formik = useFormik({
    initialValues: initialValues || {
      alias: '',
      host: '',
      port: 1433, // Default to MSSQL port
      username: '',
      password: '',
      database: '',
      service_name: '',
      db_type: 'sqlserver', // Default to MSSQL
      ssl_enabled: false,
      ssl_ca: '',
      ssl_cert: '',
      ssl_key: '',
      connection_params: {},
      use_vault: false
    },
    validationSchema,
    onSubmit: (values) => {
      onSubmit(values);
    }
  });

  // Update default port when db_type changes
  useEffect(() => {
    if (!initialValues && formik.values.port === 1433 && formik.values.db_type !== 'sqlserver') {
      let defaultPort = 1433;
      
      switch (formik.values.db_type) {
        case 'postgresql':
          defaultPort = 5432;
          break;
        case 'mysql':
          defaultPort = 3306;
          break;
        case 'oracle':
          defaultPort = 1521;
          break;
      }
      
      formik.setFieldValue('port', defaultPort);
    }
  }, [formik.values.db_type]);

  return (
    <form onSubmit={formik.handleSubmit}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Server Information
          </Typography>
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="alias"
            name="alias"
            label="Server Alias (Optional)"
            value={formik.values.alias}
            onChange={formik.handleChange}
            error={formik.touched.alias && Boolean(formik.errors.alias)}
            helperText={formik.touched.alias && formik.errors.alias}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel id="db-type-label">Database Type</InputLabel>
            <Select
              labelId="db-type-label"
              id="db_type"
              name="db_type"
              label="Database Type"
              value={formik.values.db_type}
              onChange={formik.handleChange}
              error={formik.touched.db_type && Boolean(formik.errors.db_type)}
            >
              <MenuItem value="sqlserver">SQL Server</MenuItem>
              <MenuItem value="postgresql">PostgreSQL</MenuItem>
              <MenuItem value="mysql">MySQL</MenuItem>
              <MenuItem value="oracle">Oracle</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={8}>
          <TextField
            fullWidth
            id="host"
            name="host"
            label="Host"
            value={formik.values.host}
            onChange={formik.handleChange}
            error={formik.touched.host && Boolean(formik.errors.host)}
            helperText={formik.touched.host && formik.errors.host}
          />
        </Grid>

        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            id="port"
            name="port"
            label="Port"
            type="number"
            value={formik.values.port}
            onChange={formik.handleChange}
            error={formik.touched.port && Boolean(formik.errors.port)}
            helperText={formik.touched.port && formik.errors.port}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            id="database"
            name="database"
            label="Database"
            value={formik.values.database}
            onChange={formik.handleChange}
            error={formik.touched.database && Boolean(formik.errors.database)}
            helperText={formik.touched.database && formik.errors.database}
          />
        </Grid>

        {formik.values.db_type === 'oracle' && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              id="service_name"
              name="service_name"
              label="Service Name (Oracle)"
              value={formik.values.service_name}
              onChange={formik.handleChange}
              error={formik.touched.service_name && Boolean(formik.errors.service_name)}
              helperText={formik.touched.service_name && formik.errors.service_name}
            />
          </Grid>
        )}

        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Authentication
          </Typography>
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="username"
            name="username"
            label="Username"
            value={formik.values.username}
            onChange={formik.handleChange}
            error={formik.touched.username && Boolean(formik.errors.username)}
            helperText={formik.touched.username && formik.errors.username}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            id="password"
            name="password"
            label="Password"
            type={showPassword ? "text" : "password"}
            value={formik.values.password}
            onChange={formik.handleChange}
            error={formik.touched.password && Boolean(formik.errors.password)}
            helperText={
              (formik.touched.password && formik.errors.password) || 
              (initialValues ? "Leave blank to keep current password" : "")
            }
          />
        </Grid>

        <Grid item xs={12}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch 
                  checked={showPassword} 
                  onChange={() => setShowPassword(!showPassword)} 
                />
              }
              label="Show Password"
            />
            
            {vaultAvailable && (
              <Box sx={{ ml: 3, display: 'flex', alignItems: 'center' }}>
                <FormControlLabel
                  control={
                    <Switch 
                      id="use_vault"
                      name="use_vault"
                      checked={formik.values.use_vault} 
                      onChange={formik.handleChange} 
                    />
                  }
                  label="Store in Vault"
                />
                <Tooltip title="Store credentials securely in HashiCorp Vault instead of the database">
                  <InfoIcon fontSize="small" color="action" />
                </Tooltip>
              </Box>
            )}
          </Box>
        </Grid>

        {formik.values.use_vault && (
          <Grid item xs={12}>
            <Alert severity="info">
              Credentials will be stored securely in HashiCorp Vault instead of the database.
            </Alert>
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
              disabled={isSubmitting}
            >
              {isSubmitting ? <CircularProgress size={24} /> : initialValues ? 'Update Server' : 'Create Server'}
            </Button>
          </Box>
        </Grid>

        {advancedMode && (
          <>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                SSL Configuration
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch 
                    id="ssl_enabled"
                    name="ssl_enabled"
                    checked={formik.values.ssl_enabled} 
                    onChange={formik.handleChange} 
                  />
                }
                label="Enable SSL/TLS"
              />
            </Grid>

            {formik.values.ssl_enabled && (
              <>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    id="ssl_ca"
                    name="ssl_ca"
                    label="CA Certificate"
                    multiline
                    rows={3}
                    value={formik.values.ssl_ca}
                    onChange={formik.handleChange}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    id="ssl_cert"
                    name="ssl_cert"
                    label="Client Certificate"
                    multiline
                    rows={3}
                    value={formik.values.ssl_cert}
                    onChange={formik.handleChange}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    id="ssl_key"
                    name="ssl_key"
                    label="Client Key"
                    multiline
                    rows={3}
                    value={formik.values.ssl_key}
                    onChange={formik.handleChange}
                  />
                </Grid>
              </>
            )}
          </>
        )}

        {error && (
          <Grid item xs={12}>
            <Alert severity="error">{error}</Alert>
          </Grid>
        )}
      </Grid>
    </form>
  );
};

export default ServerForm;

// Son güncelleme: 2025-05-21 06:51:05
// Güncelleyen: Teeksss