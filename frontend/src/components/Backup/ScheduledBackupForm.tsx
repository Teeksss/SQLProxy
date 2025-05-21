/**
 * Scheduled Backup Form Component
 * 
 * Form for configuring automated and scheduled backups
 * 
 * Last updated: 2025-05-21 05:35:49
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  TextField,
  FormControl,
  FormControlLabel,
  FormHelperText,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  Button,
  Typography,
  Alert,
  AlertTitle,
  CircularProgress,
  Tooltip,
  InputAdornment,
  IconButton
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import InfoIcon from '@mui/icons-material/Info';
import DeleteIcon from '@mui/icons-material/Delete';
import { toast } from 'react-toastify';

import { BackupType } from '../../types/backup';
import { tasksApi } from '../../services/tasksService';
import ConfirmationDialog from '../common/ConfirmationDialog';

const ScheduledBackupForm: React.FC = () => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  
  const queryClient = useQueryClient();
  
  // Fetch scheduled tasks
  const {
    data: tasks,
    isLoading: isLoadingTasks,
    refetch: refetchTasks
  } = useQuery(
    ['scheduledTasks'],
    tasksApi.getTasks,
    {
      refetchOnWindowFocus: true,
      onError: (error: any) => {
        toast.error(`Error loading scheduled tasks: ${error.message}`);
      }
    }
  );
  
  // Create task mutation
  const createTaskMutation = useMutation(
    (taskData: any) => tasksApi.createTask(taskData),
    {
      onSuccess: () => {
        toast.success('Scheduled backup created successfully');
        queryClient.invalidateQueries(['scheduledTasks']);
        formik.resetForm();
      },
      onError: (error: any) => {
        toast.error(`Error creating scheduled backup: ${error.message}`);
      }
    }
  );
  
  // Delete task mutation
  const deleteTaskMutation = useMutation(
    (taskId: string) => tasksApi.deleteTask(taskId),
    {
      onSuccess: () => {
        toast.success('Scheduled backup deleted successfully');
        queryClient.invalidateQueries(['scheduledTasks']);
      },
      onError: (error: any) => {
        toast.error(`Error deleting scheduled backup: ${error.message}`);
      }
    }
  );
  
  // Run task mutation
  const runTaskMutation = useMutation(
    (taskId: string) => tasksApi.runTaskNow(taskId),
    {
      onSuccess: () => {
        toast.success('Backup task started successfully');
      },
      onError: (error: any) => {
        toast.error(`Error running backup task: ${error.message}`);
      }
    }
  );
  
  // Get backup tasks
  const backupTasks = React.useMemo(() => {
    if (!tasks?.tasks) return [];
    
    return tasks.tasks.filter(task => 
      task.id.startsWith('backup_') || 
      task.tags.includes('backup')
    );
  }, [tasks]);
  
  // Validation schema
  const validationSchema = Yup.object({
    taskId: Yup.string()
      .required('Task ID is required')
      .matches(/^[a-zA-Z0-9_]+$/, 'Task ID can only contain letters, numbers, and underscores'),
    backupType: Yup.string().required('Backup type is required'),
    description: Yup.string().required('Description is required').max(100, 'Description cannot exceed 100 characters'),
    scheduleType: Yup.string().required('Schedule type is required'),
    interval: Yup.number().when('scheduleType', {
      is: 'interval',
      then: Yup.number().required('Interval is required').positive('Interval must be positive')
    }),
    intervalUnit: Yup.string().when('scheduleType', {
      is: 'interval',
      then: Yup.string().required('Interval unit is required')
    }),
    runAt: Yup.string().when('scheduleType', {
      is: 'daily',
      then: Yup.string().required('Time is required').matches(/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/, 'Time must be in HH:MM format')
    }),
    firstRun: Yup.date().when('scheduleType', {
      is: 'once',
      then: Yup.date().required('First run time is required').min(new Date(), 'First run time must be in the future')
    }),
    includeQueries: Yup.boolean()
  });
  
  // Initialize form
  const formik = useFormik({
    initialValues: {
      taskId: `backup_${Date.now()}`,
      backupType: BackupType.FULL,
      description: 'Scheduled backup',
      scheduleType: 'interval',
      interval: 24,
      intervalUnit: 'hours',
      runAt: '02:00',
      firstRun: new Date(new Date().getTime() + 3600000), // 1 hour from now
      includeQueries: true
    },
    validationSchema,
    onSubmit: (values) => {
      // Prepare task data
      let taskData = {
        task_id: values.taskId,
        task_type: 'backup',
        parameters: {
          backup_type: values.backupType,
          description: values.description,
          include_queries: values.includeQueries
        }
      };
      
      // Add scheduling info based on schedule type
      if (values.scheduleType === 'interval') {
        if (values.intervalUnit === 'hours') {
          taskData = {
            ...taskData,
            interval_hours: values.interval,
            interval_minutes: undefined,
            interval_seconds: undefined,
            first_run: undefined,
            run_at: undefined,
            run_daily: false
          };
        } else if (values.intervalUnit === 'minutes') {
          taskData = {
            ...taskData,
            interval_hours: undefined,
            interval_minutes: values.interval,
            interval_seconds: undefined,
            first_run: undefined,
            run_at: undefined,
            run_daily: false
          };
        } else if (values.intervalUnit === 'seconds') {
          taskData = {
            ...taskData,
            interval_hours: undefined,
            interval_minutes: undefined,
            interval_seconds: values.interval,
            first_run: undefined,
            run_at: undefined,
            run_daily: false
          };
        }
      } else if (values.scheduleType === 'daily') {
        taskData = {
          ...taskData,
          interval_hours: undefined,
          interval_minutes: undefined,
          interval_seconds: undefined,
          first_run: undefined,
          run_at: values.runAt,
          run_daily: true
        };
      } else if (values.scheduleType === 'once') {
        taskData = {
          ...taskData,
          interval_hours: undefined,
          interval_minutes: undefined,
          interval_seconds: undefined,
          first_run: values.firstRun.toISOString(),
          run_at: undefined,
          run_daily: false
        };
      }
      
      // Create task
      createTaskMutation.mutate(taskData);
    }
  });
  
  // Handle task deletion
  const handleDeleteTask = (taskId: string) => {
    setSelectedTaskId(taskId);
    setShowDeleteDialog(true);
  };
  
  // Handle confirm delete
  const handleConfirmDelete = () => {
    if (selectedTaskId) {
      deleteTaskMutation.mutate(selectedTaskId);
      setShowDeleteDialog(false);
    }
  };
  
  // Handle run task now
  const handleRunTaskNow = (taskId: string) => {
    runTaskMutation.mutate(taskId);
  };
  
  return (
    <Box>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <Grid container spacing={3}>
          {/* New Scheduled Backup Form */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Create Scheduled Backup" 
                titleTypographyProps={{ variant: 'h6' }}
              />
              <Divider />
              <CardContent>
                <Box component="form" onSubmit={formik.handleSubmit}>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        id="taskId"
                        name="taskId"
                        label="Task ID"
                        value={formik.values.taskId}
                        onChange={formik.handleChange}
                        error={formik.touched.taskId && Boolean(formik.errors.taskId)}
                        helperText={formik.touched.taskId && formik.errors.taskId}
                        margin="normal"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">backup_</InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <FormControl 
                        fullWidth 
                        margin="normal"
                        error={formik.touched.backupType && Boolean(formik.errors.backupType)}
                      >
                        <InputLabel id="backup-type-label">Backup Type</InputLabel>
                        <Select
                          labelId="backup-type-label"
                          id="backupType"
                          name="backupType"
                          value={formik.values.backupType}
                          onChange={formik.handleChange}
                          label="Backup Type"
                        >
                          <MenuItem value={BackupType.FULL}>Full Backup</MenuItem>
                          <MenuItem value={BackupType.INCREMENTAL}>Incremental Backup</MenuItem>
                        </Select>
                        {formik.touched.backupType && formik.errors.backupType && (
                          <FormHelperText>{formik.errors.backupType}</FormHelperText>
                        )}
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
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
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <FormControl 
                        fullWidth 
                        margin="normal"
                        error={formik.touched.scheduleType && Boolean(formik.errors.scheduleType)}
                      >
                        <InputLabel id="schedule-type-label">Schedule Type</InputLabel>
                        <Select
                          labelId="schedule-type-label"
                          id="scheduleType"
                          name="scheduleType"
                          value={formik.values.scheduleType}
                          onChange={formik.handleChange}
                          label="Schedule Type"
                        >
                          <MenuItem value="interval">Recurring (Interval)</MenuItem>
                          <MenuItem value="daily">Daily (At specific time)</MenuItem>
                          <MenuItem value="once">Once (At specific date/time)</MenuItem>
                        </Select>
                        {formik.touched.scheduleType && formik.errors.scheduleType && (
                          <FormHelperText>{formik.errors.scheduleType}</FormHelperText>
                        )}
                      </FormControl>
                    </Grid>
                    
                    {formik.values.scheduleType === 'interval' && (
                      <>
                        <Grid item xs={12} sm={6}>
                          <TextField
                            fullWidth
                            id="interval"
                            name="interval"
                            label="Interval"
                            type="number"
                            value={formik.values.interval}
                            onChange={formik.handleChange}
                            error={formik.touched.interval && Boolean(formik.errors.interval)}
                            helperText={formik.touched.interval && formik.errors.interval}
                            margin="normal"
                          />
                        </Grid>
                        
                        <Grid item xs={12} sm={6}>
                          <FormControl 
                            fullWidth 
                            margin="normal"
                            error={formik.touched.intervalUnit && Boolean(formik.errors.intervalUnit)}
                          >
                            <InputLabel id="interval-unit-label">Unit</InputLabel>
                            <Select
                              labelId="interval-unit-label"
                              id="intervalUnit"
                              name="intervalUnit"
                              value={formik.values.intervalUnit}
                              onChange={formik.handleChange}
                              label="Unit"
                            >
                              <MenuItem value="hours">Hours</MenuItem>
                              <MenuItem value="minutes">Minutes</MenuItem>
                              <MenuItem value="seconds">Seconds</MenuItem>
                            </Select>
                            {formik.touched.intervalUnit && formik.errors.intervalUnit && (
                              <FormHelperText>{formik.errors.intervalUnit}</FormHelperText>
                            )}
                          </FormControl>
                        </Grid>
                      </>
                    )}
                    
                    {formik.values.scheduleType === 'daily' && (
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          id="runAt"
                          name="runAt"
                          label="Run at (HH:MM)"
                          value={formik.values.runAt}
                          onChange={formik.handleChange}
                          error={formik.touched.runAt && Boolean(formik.errors.runAt)}
                          helperText={
                            (formik.touched.runAt && formik.errors.runAt) ||
                            "Time in 24-hour format (e.g., 14:30 for 2:30 PM)"
                          }
                          margin="normal"
                        />
                      </Grid>
                    )}
                    
                    {formik.values.scheduleType === 'once' && (
                      <Grid item xs={12}>
                        <DateTimePicker
                          label="Run at date/time"
                          value={formik.values.firstRun}
                          onChange={(value) => formik.setFieldValue('firstRun', value)}
                          disablePast
                          slotProps={{
                            textField: {
                              fullWidth: true,
                              margin: 'normal',
                              error: formik.touched.firstRun && Boolean(formik.errors.firstRun),
                              helperText: formik.touched.firstRun && formik.errors.firstRun as string
                            }
                          }}
                        />
                      </Grid>
                    )}
                    
                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            id="includeQueries"
                            name="includeQueries"
                            checked={formik.values.includeQueries}
                            onChange={formik.handleChange}
                          />
                        }
                        label="Include saved queries in backup"
                      />
                      <Tooltip title="When enabled, all saved queries will be included in the backup">
                        <IconButton size="small">
                          <InfoIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Button
                        type="submit"
                        variant="contained"
                        disabled={createTaskMutation.isLoading}
                        fullWidth
                      >
                        {createTaskMutation.isLoading ? (
                          <CircularProgress size={24} />
                        ) : (
                          "Create Scheduled Backup"
                        )}
                      </Button>
                    </Grid>
                  </Grid>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Existing Scheduled Backups */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader 
                title="Existing Scheduled Backups" 
                titleTypographyProps={{ variant: 'h6' }}
              />
              <Divider />
              <CardContent>
                {isLoadingTasks ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <CircularProgress />
                  </Box>
                ) : backupTasks.length === 0 ? (
                  <Alert severity="info">
                    No scheduled backups configured
                  </Alert>
                ) : (
                  <Box>
                    {backupTasks.map((task) => (
                      <Card 
                        key={task.id} 
                        variant="outlined" 
                        sx={{ mb: 2, bgcolor: 'background.default' }}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <Box>
                              <Typography variant="subtitle1">
                                {task.id}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Next run: {task.next_run ? new Date(task.next_run).toLocaleString() : 'Not scheduled'}
                              </Typography>
                              {task.last_run && (
                                <Typography variant="body2" color="text.secondary">
                                  Last run: {new Date(task.last_run).toLocaleString()}
                                </Typography>
                              )}
                              {task.interval && (
                                <Typography variant="body2" color="text.secondary">
                                  Interval: {task.interval}
                                </Typography>
                              )}
                            </Box>
                            
                            <Box>
                              <Tooltip title="Run Now">
                                <Button
                                  size="small"
                                  onClick={() => handleRunTaskNow(task.id)}
                                  sx={{ mr: 1 }}
                                >
                                  Run Now
                                </Button>
                              </Tooltip>
                              
                              <Tooltip title="Delete">
                                <IconButton
                                  size="small"
                                  onClick={() => handleDeleteTask(task.id)}
                                  color="error"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </LocalizationProvider>
      
      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Scheduled Backup"
        content="Are you sure you want to delete this scheduled backup? This action cannot be undone."
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isSubmitting={deleteTaskMutation.isLoading}
      />
    </Box>
  );
};

export default ScheduledBackupForm;

// Son güncelleme: 2025-05-21 05:35:49
// Güncelleyen: Teeksss