/**
 * Refresh Schedule Form Component
 * 
 * Form for configuring dataset refresh schedules
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
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Alert,
  AlertTitle,
  CircularProgress,
  Paper,
  Divider,
  InputAdornment,
  Tooltip
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useMutation } from 'react-query';
import InfoIcon from '@mui/icons-material/Info';
import ScheduleIcon from '@mui/icons-material/Schedule';
import DeleteIcon from '@mui/icons-material/Delete';

import { powerbiApi } from '../../services/powerbiService';

interface RefreshScheduleFormProps {
  dataset: any;
  onSuccess: () => void;
}

const RefreshScheduleForm: React.FC<RefreshScheduleFormProps> = ({ dataset, onSuccess }) => {
  const [scheduleType, setScheduleType] = useState<string>(
    dataset.refresh_schedule ? 'custom' : 'daily'
  );

  // Mutation for setting up refresh schedule
  const setupScheduleMutation = useMutation(
    (data: { dataset_id: string; schedule: string; workspace_id?: string }) => 
      powerbiApi.setupRefreshSchedule(data.dataset_id, data.schedule, data.workspace_id),
    {
      onSuccess: () => {
        onSuccess();
      }
    }
  );

  // Mutation for cancelling refresh schedule
  const cancelScheduleMutation = useMutation(
    (datasetId: string) => powerbiApi.cancelRefreshSchedule(datasetId),
    {
      onSuccess: () => {
        onSuccess();
      }
    }
  );

  // Initialize form
  const formik = useFormik({
    initialValues: {
      schedule: dataset.refresh_schedule || '0 0 * * *', // Default: daily at midnight
      hours: '0',
      minutes: '0'
    },
    validationSchema: Yup.object({
      schedule: Yup.string().when('scheduleType', {
        is: 'custom',
        then: Yup.string().required('Schedule expression is required')
      }),
      hours: Yup.number().when('scheduleType', {
        is: (val: string) => val !== 'custom',
        then: Yup.number().min(0).max(23).required('Hours are required')
      }),
      minutes: Yup.number().when('scheduleType', {
        is: (val: string) => val !== 'custom',
        then: Yup.number().min(0).max(59).required('Minutes are required')
      })
    }),
    onSubmit: (values) => {
      let schedule: string;
      
      // Generate cron expression based on schedule type
      if (scheduleType === 'custom') {
        schedule = values.schedule;
      } else if (scheduleType === 'daily') {
        schedule = `${values.minutes} ${values.hours} * * *`;
      } else if (scheduleType === 'hourly') {
        schedule = `${values.minutes} * * * *`;
      } else if (scheduleType === 'weekly') {
        schedule = `${values.minutes} ${values.hours} * * 0`; // Sunday
      }
      
      // Set up refresh schedule
      setupScheduleMutation.mutate({
        dataset_id: dataset.dataset_id,
        schedule,
        workspace_id: dataset.workspace_id
      });
    }
  });

  // Handle schedule type change
  const handleScheduleTypeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setScheduleType(event.target.value);
  };

  // Handle cancel schedule
  const handleCancelSchedule = () => {
    cancelScheduleMutation.mutate(dataset.dataset_id);
  };

  return (
    <Box sx={{ p: 2 }}>
      <form onSubmit={formik.handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Alert severity="info">
              <AlertTitle>About Dataset Refresh</AlertTitle>
              Configure when PowerBI should automatically refresh this dataset. 
              The refresh operation will update the dataset with the latest data from the database.
            </Alert>
          </Grid>
          
          <Grid item xs={12}>
            <Typography variant="subtitle1">
              Current Schedule
            </Typography>
            <Paper variant="outlined" sx={{ p: 2, mt: 1 }}>
              {dataset.refresh_schedule ? (
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                      {dataset.refresh_schedule}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Last refreshed: {dataset.last_refreshed_at ? new Date(dataset.last_refreshed_at).toLocaleString() : 'Never'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Status: {dataset.last_refresh_status || 'N/A'}
                    </Typography>
                  </Box>
                  
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={handleCancelSchedule}
                    disabled={cancelScheduleMutation.isLoading}
                  >
                    {cancelScheduleMutation.isLoading ? <CircularProgress size={24} /> : 'Cancel Schedule'}
                  </Button>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No refresh schedule is currently set up for this dataset.
                </Typography>
              )}
            </Paper>
          </Grid>
          
          <Grid item xs={12}>
            <Divider />
          </Grid>
          
          <Grid item xs={12}>
            <Typography variant="subtitle1">
              Set New Schedule
            </Typography>
          </Grid>
          
          <Grid item xs={12}>
            <FormControl component="fieldset">
              <FormLabel component="legend">Schedule Type</FormLabel>
              <RadioGroup
                row
                name="scheduleType"
                value={scheduleType}
                onChange={handleScheduleTypeChange}
              >
                <FormControlLabel value="daily" control={<Radio />} label="Daily" />
                <FormControlLabel value="hourly" control={<Radio />} label="Hourly" />
                <FormControlLabel value="weekly" control={<Radio />} label="Weekly" />
                <FormControlLabel value="custom" control={<Radio />} label="Custom (cron expression)" />
              </RadioGroup>
            </FormControl>
          </Grid>
          
          {scheduleType === 'custom' ? (
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="schedule"
                name="schedule"
                label="Cron Expression"
                value={formik.values.schedule}
                onChange={formik.handleChange}
                error={formik.touched.schedule && Boolean(formik.errors.schedule)}
                helperText={
                  (formik.touched.schedule && formik.errors.schedule) || 
                  'Format: minute hour day month weekday (e.g., "0 0 * * *" for daily at midnight)'
                }
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <Tooltip title="Cron expression format: minute hour day month weekday">
                        <InfoIcon color="action" />
                      </Tooltip>
                    </InputAdornment>
                  )
                }}
              />
            </Grid>
          ) : (
            <Grid item xs={12}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    id="hours"
                    name="hours"
                    label="Hour (0-23)"
                    type="number"
                    value={formik.values.hours}
                    onChange={formik.handleChange}
                    error={formik.touched.hours && Boolean(formik.errors.hours)}
                    helperText={formik.touched.hours && formik.errors.hours}
                    inputProps={{ min: 0, max: 23 }}
                    disabled={scheduleType === 'hourly'}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    id="minutes"
                    name="minutes"
                    label="Minute (0-59)"
                    type="number"
                    value={formik.values.minutes}
                    onChange={formik.handleChange}
                    error={formik.touched.minutes && Boolean(formik.errors.minutes)}
                    helperText={formik.touched.minutes && formik.errors.minutes}
                    inputProps={{ min: 0, max: 59 }}
                  />
                </Grid>
              </Grid>
            </Grid>
          )}
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<ScheduleIcon />}
                disabled={setupScheduleMutation.isLoading}
              >
                {setupScheduleMutation.isLoading ? <CircularProgress size={24} /> : 'Set Schedule'}
              </Button>
            </Box>
          </Grid>
          
          {setupScheduleMutation.isError && (
            <Grid item xs={12}>
              <Alert severity="error">
                {(setupScheduleMutation.error as Error).message}
              </Alert>
            </Grid>
          )}
          
          {cancelScheduleMutation.isError && (
            <Grid item xs={12}>
              <Alert severity="error">
                {(cancelScheduleMutation.error as Error).message}
              </Alert>
            </Grid>
          )}
        </Grid>
      </form>
    </Box>
  );
};

export default RefreshScheduleForm;

// Son güncelleme: 2025-05-21 06:02:47
// Güncelleyen: Teeksss