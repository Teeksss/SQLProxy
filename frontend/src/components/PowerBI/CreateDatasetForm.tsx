/**
 * Create Dataset Form Component
 * 
 * Form for creating PowerBI datasets from SQL queries or schema definitions
 * 
 * Last updated: 2025-05-21 06:02:47
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
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useQuery, useMutation } from 'react-query';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import CodeIcon from '@mui/icons-material/Code';

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
      id={`create-dataset-tabpanel-${index}`}
      aria-labelledby={`create-dataset-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 1 }}>{children}</Box>}
    </div>
  );
};

// Interface for column definition
interface ColumnDefinition {
  name: string;
  dataType: string;
}

interface CreateDatasetFormProps {
  workspaceId?: string;
  onSuccess: () => void;
}

const CreateDatasetForm: React.FC<CreateDatasetFormProps> = ({ workspaceId, onSuccess }) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [sqlQuery, setSqlQuery] = useState('');
  const [queryError, setQueryError] = useState<string | null>(null);
  const [columns, setColumns] = useState<ColumnDefinition[]>([]);

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

  // Mutation for creating a dataset
  const createDatasetMutation = useMutation(
    (data: any) => powerbiApi.createDataset(data),
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

  // Handle adding a column
  const handleAddColumn = () => {
    setColumns([...columns, { name: '', dataType: 'String' }]);
  };

  // Handle removing a column
  const handleRemoveColumn = (index: number) => {
    const newColumns = [...columns];
    newColumns.splice(index, 1);
    setColumns(newColumns);
  };

  // Handle column name change
  const handleColumnNameChange = (index: number, value: string) => {
    const newColumns = [...columns];
    newColumns[index].name = value;
    setColumns(newColumns);
  };

  // Handle column data type change
  const handleColumnDataTypeChange = (index: number, value: string) => {
    const newColumns = [...columns];
    newColumns[index].dataType = value;
    setColumns(newColumns);
  };

  // Handle schema inference from SQL Query
  const handleInferSchema = async () => {
    if (!sqlQuery || !schemaFormik.values.server_id) {
      setQueryError('Please provide both a SQL query and select a server');
      return;
    }

    try {
      setQueryError(null);
      
      // Execute the query to get schema
      const result = await queryApi.previewQuery(sqlQuery, schemaFormik.values.server_id);
      
      if (!result.columns || result.columns.length === 0) {
        setQueryError('Could not infer schema from query');
        return;
      }
      
      // Infer data types from the first row of data
      const inferredColumns: ColumnDefinition[] = [];
      const firstRow = result.data && result.data.length > 0 ? result.data[0] : null;
      
      result.columns.forEach((column: string, index: number) => {
        let dataType = 'String';
        
        if (firstRow) {
          const value = firstRow[index];
          if (typeof value === 'number') {
            dataType = Number.isInteger(value) ? 'Int64' : 'Double';
          } else if (typeof value === 'boolean') {
            dataType = 'Boolean';
          } else if (value instanceof Date) {
            dataType = 'DateTime';
          }
        }
        
        inferredColumns.push({
          name: column,
          dataType
        });
      });
      
      setColumns(inferredColumns);
      
      // Switch to schema tab
      setTabIndex(1);
    } catch (error) {
      setQueryError(`Error inferring schema: ${(error as Error).message}`);
    }
  };

  // Schema definition form
  const schemaFormik = useFormik({
    initialValues: {
      name: '',
      description: '',
      workspace_id: workspaceId || '',
      server_id: '',
      table_name: 'QueryResults',
      default_mode: 'Push'
    },
    validationSchema: Yup.object({
      name: Yup.string().required('Dataset name is required'),
      description: Yup.string(),
      table_name: Yup.string().required('Table name is required')
    }),
    onSubmit: (values) => {
      // Validate that we have at least one column
      if (columns.length === 0) {
        setQueryError('At least one column must be defined');
        return;
      }
      
      // Validate column names
      const invalidColumns = columns.filter(col => !col.name.trim());
      if (invalidColumns.length > 0) {
        setQueryError('All columns must have a name');
        return;
      }
      
      setQueryError(null);
      
      // Prepare dataset schema
      const dataset = {
        name: values.name,
        description: values.description,
        workspace_id: values.workspace_id || undefined,
        default_mode: values.default_mode,
        tables: [
          {
            name: values.table_name,
            columns: columns.map(col => ({
              name: col.name,
              data_type: col.dataType
            }))
          }
        ]
      };
      
      // Create the dataset
      createDatasetMutation.mutate(dataset);
    }
  });

  return (
    <Box sx={{ minHeight: 400 }}>
      <Tabs value={tabIndex} onChange={handleTabChange} aria-label="create dataset tabs">
        <Tab label="SQL Query" id="create-dataset-tab-0" />
        <Tab label="Schema Definition" id="create-dataset-tab-1" />
      </Tabs>

      {/* SQL Query Tab */}
      <TabPanel value={tabIndex} index={0}>
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Define Dataset from SQL Query
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="server-label">Database Server</InputLabel>
                <Select
                  labelId="server-label"
                  id="server_id"
                  name="server_id"
                  value={schemaFormik.values.server_id}
                  onChange={schemaFormik.handleChange}
                  label="Database Server"
                >
                  {servers?.map((server: any) => (
                    <MenuItem key={server.id} value={server.id}>
                      {server.alias || server.host} ({server.database})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
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
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Button
                  variant="outlined"
                  onClick={handleInferSchema}
                  startIcon={<CodeIcon />}
                  disabled={!sqlQuery || !schemaFormik.values.server_id}
                >
                  Infer Schema from Query
                </Button>
                
                <Button
                  variant="contained"
                  onClick={() => setTabIndex(1)}
                  disabled={columns.length === 0}
                >
                  Continue to Schema Definition
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </TabPanel>

      {/* Schema Definition Tab */}
      <TabPanel value={tabIndex} index={1}>
        <form onSubmit={schemaFormik.handleSubmit}>
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Define Dataset Schema
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  id="name"
                  name="name"
                  label="Dataset Name"
                  value={schemaFormik.values.name}
                  onChange={schemaFormik.handleChange}
                  error={schemaFormik.touched.name && Boolean(schemaFormik.errors.name)}
                  helperText={schemaFormik.touched.name && schemaFormik.errors.name}
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  id="table_name"
                  name="table_name"
                  label="Table Name"
                  value={schemaFormik.values.table_name}
                  onChange={schemaFormik.handleChange}
                  error={schemaFormik.touched.table_name && Boolean(schemaFormik.errors.table_name)}
                  helperText={schemaFormik.touched.table_name && schemaFormik.errors.table_name}
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="description"
                  name="description"
                  label="Description"
                  value={schemaFormik.values.description}
                  onChange={schemaFormik.handleChange}
                  error={schemaFormik.touched.description && Boolean(schemaFormik.errors.description)}
                  helperText={schemaFormik.touched.description && schemaFormik.errors.description}
                  margin="normal"
                  multiline
                  rows={2}
                />
              </Grid>
              
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle2">
                    Column Definitions
                  </Typography>
                  
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={handleAddColumn}
                  >
                    Add Column
                  </Button>
                </Box>
                
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell width="50%">Name</TableCell>
                        <TableCell width="40%">Data Type</TableCell>
                        <TableCell width="10%" align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {columns.map((column, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <TextField
                              fullWidth
                              size="small"
                              value={column.name}
                              onChange={(e) => handleColumnNameChange(index, e.target.value)}
                              placeholder="Column name"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <FormControl fullWidth size="small">
                              <Select
                                value={column.dataType}
                                onChange={(e) => handleColumnDataTypeChange(index, e.target.value)}
                              >
                                <MenuItem value="String">String</MenuItem>
                                <MenuItem value="Int64">Int64</MenuItem>
                                <MenuItem value="Double">Double</MenuItem>
                                <MenuItem value="Boolean">Boolean</MenuItem>
                                <MenuItem value="DateTime">DateTime</MenuItem>
                                <MenuItem value="Decimal">Decimal</MenuItem>
                              </Select>
                            </FormControl>
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => handleRemoveColumn(index)}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                      
                      {columns.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={3} align="center">
                            <Typography variant="body2" color="text.secondary">
                              No columns defined. Click "Add Column" or use "Infer Schema from Query".
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid item xs={12}>
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={createDatasetMutation.isLoading || columns.length === 0}
                  >
                    {createDatasetMutation.isLoading ? (
                      <CircularProgress size={24} />
                    ) : (
                      'Create Dataset'
                    )}
                  </Button>
                </Box>
              </Grid>
            </Grid>
            
            {createDatasetMutation.isError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {(createDatasetMutation.error as Error).message}
              </Alert>
            )}
          </Box>
        </form>
      </TabPanel>
    </Box>
  );
};

export default CreateDatasetForm;

// Son güncelleme: 2025-05-21 06:02:47
// Güncelleyen: Teeksss