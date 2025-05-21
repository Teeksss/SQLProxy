/**
 * PowerBI Settings Form Component
 * 
 * Form for configuring PowerBI integration settings
 * 
 * Last updated: 2025-05-21 05:48:50
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  Alert,
  AlertTitle,
  CircularProgress,
  Divider,
  InputAdornment,
  IconButton,
  Card,
  CardContent
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useMutation } from 'react-query';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import { toast } from 'react-toastify';

import { powerbiApi } from '../../services/powerbiService';

const PowerBISettingsForm: React.FC = () => {
  const [showClientSecret, setShowClientSecret] = useState(false);

  // Mutation for updating credentials
  const updateCredentialsMutation = useMutation(
    (data: any) => powerbiApi.updateCredentials(data),
    {
      onSuccess: () => {
        toast.success('PowerBI credentials updated successfully');
      },
      onError: (error: any) => {
        toast.error(`Error updating PowerBI credentials: ${error.message}`);
      }
    }
  );

  // Formik for credentials form
  const formik = useFormik({
    initialValues: {
      tenant_id: '',
      client_id: '',
      client_secret: ''
    },
    validationSchema: Yup.object({
      tenant_id: Yup.string().required('Tenant ID is required'),
      client_id: Yup.string().required('Client ID is required'),
      client_secret: Yup.string().required('Client Secret is required')
    }),
    onSubmit: (values) => {
      updateCredentialsMutation.mutate(values);
    }
  });

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        PowerBI Integration Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <form onSubmit={formik.handleSubmit}>
            <Paper variant="outlined" sx={{ p: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                PowerBI Service Principal Credentials
              </Typography>
              
              <Alert severity="info" sx={{ mb: 3 }}>
                <AlertTitle>Azure AD Setup Required</AlertTitle>
                To integrate with PowerBI, you need to register an application in Azure Active Directory
                and grant it appropriate permissions to PowerBI service. 
                See the <a href="https://docs.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal" target="_blank" rel="noopener noreferrer">Microsoft documentation</a> for details.
              </Alert>
              
              <TextField
                fullWidth
                id="tenant_id"
                name="tenant_id"
                label="Azure Tenant ID"
                value={formik.values.tenant_id}
                onChange={formik.handleChange}
                error={formik.touched.tenant_id && Boolean(formik.errors.tenant_id)}
                helperText={formik.touched.tenant_id && formik.errors.tenant_id}
                margin="normal"
              />
              
              <TextField
                fullWidth
                id="client_id"
                name="client_id"
                label="Client ID (Application ID)"
                value={formik.values.client_id}
                onChange={formik.handleChange}
                error={formik.touched.client_id && Boolean(formik.errors.client_id)}
                helperText={formik.touched.client_id && formik.errors.client_id}
                margin="normal"
              />
              
              <TextField
                fullWidth
                id="client_secret"
                name="client_secret"
                label="Client Secret"
                type={showClientSecret ? 'text' : 'password'}
                value={formik.values.client_secret}
                onChange={formik.handleChange}
                error={formik.touched.client_secret && Boolean(formik.errors.client_secret)}
                helperText={formik.touched.client_secret && formik.errors.client_secret}
                margin="normal"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowClientSecret(!showClientSecret)}
                        edge="end"
                      >
                        {showClientSecret ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
              />
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={updateCredentialsMutation.isLoading}
                >
                  {updateCredentialsMutation.isLoading ? (
                    <CircularProgress size={24} />
                  ) : (
                    'Save Credentials'
                  )}
                </Button>
              </Box>
            </Paper>
          </form>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Integration Instructions
              </Typography>
              
              <Divider sx={{ mb: 2 }} />
              
              <Typography variant="body2" gutterBottom>
                To set up PowerBI integration with SQL Proxy, follow these steps:
              </Typography>
              
              <ol style={{ paddingLeft: '1.5rem' }}>
                <li>
                  <Typography variant="body2" gutterBottom>
                    Register an application in Azure Active Directory
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" gutterBottom>
                    Grant the application permissions to PowerBI service (e.g., Report.Read.All, Dataset.Read.All)
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" gutterBottom>
                    Create a client secret for the application
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" gutterBottom>
                    Enter the Tenant ID, Client ID, and Client Secret in the form
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" gutterBottom>
                    Create workspaces and reports in the SQL Proxy interface
                  </Typography>
                </li>
              </ol>
              
              <Alert severity="warning" sx={{ mt: 2 }}>
                Keep your client secret secure and do not share it with others.
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PowerBISettingsForm;

// Son güncelleme: 2025-05-21 05:48:50
// Güncelleyen: Teeksss