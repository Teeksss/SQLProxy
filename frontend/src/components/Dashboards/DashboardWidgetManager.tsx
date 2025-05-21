/**
 * Dashboard Widget Manager Component
 * 
 * Manages dashboard widgets configuration and layout
 * 
 * Last updated: 2025-05-21 06:38:34
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Grid,
  Paper,
  Divider,
  Switch,
  FormControlLabel,
  IconButton,
  Tooltip
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useMutation, useQueryClient } from 'react-query';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

import { dashboardApi } from '../../services/dashboardService';
import ConfirmationDialog from '../common/ConfirmationDialog';

interface WidgetConfig {
  id: string;
  type: string;
  title: string;
  size: 'small' | 'medium' | 'large';
  position: number;
  config: any;
}

interface DashboardConfig {
  widgets: WidgetConfig[];
}

interface DashboardWidgetManagerProps {
  dashboardId: string;
  config: DashboardConfig;
  onChange: (config: DashboardConfig) => void;
}

const DashboardWidgetManager: React.FC<DashboardWidgetManagerProps> = ({
  dashboardId,
  config,
  onChange
}) => {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<WidgetConfig | null>(null);
  
  const queryClient = useQueryClient();

  // Mutation for updating dashboard config
  const updateDashboardMutation = useMutation(
    (data: any) => dashboardApi.updateDashboard(dashboardId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['dashboard', dashboardId]);
      }
    }
  );

  // Validation schema for widget form
  const validationSchema = Yup.object({
    title: Yup.string().required('Title is required'),
    type: Yup.string().required('Widget type is required'),
    size: Yup.string().required('Size is required')
  });

  // Formik for widget configuration
  const formik = useFormik({
    initialValues: {
      id: '',
      title: '',
      type: 'powerbi-report',
      size: 'medium',
      config: {
        reportId: '',
        limit: 4,
        height: 400,
        showFilterPane: false,
        refreshInterval: 0
      }
    },
    validationSchema,
    onSubmit: (values) => {
      if (selectedWidget) {
        // Edit existing widget
        const updatedWidgets = config.widgets.map(widget => 
          widget.id === selectedWidget.id ? { ...values, position: widget.position } : widget
        );
        
        const newConfig = { ...config, widgets: updatedWidgets };
        onChange(newConfig);
        updateDashboardMutation.mutate({ config: newConfig });
        
        setShowEditDialog(false);
      } else {
        // Add new widget
        const newId = `widget-${Date.now()}`;
        const newWidget = { 
          ...values, 
          id: newId,
          position: config.widgets.length 
        };
        
        const newConfig = { 
          ...config, 
          widgets: [...config.widgets, newWidget] 
        };
        
        onChange(newConfig);
        updateDashboardMutation.mutate({ config: newConfig });
        
        setShowAddDialog(false);
      }
      
      formik.resetForm();
    }
  });

  // Handle opening add dialog
  const handleAddWidget = () => {
    formik.resetForm();
    setSelectedWidget(null);
    setShowAddDialog(true);
  };

  // Handle opening edit dialog
  const handleEditWidget = (widget: WidgetConfig) => {
    setSelectedWidget(widget);
    
    // Set form values
    formik.setValues({
      id: widget.id,
      title: widget.title,
      type: widget.type,
      size: widget.size,
      config: widget.config || {
        reportId: '',
        limit: 4,
        height: 400,
        showFilterPane: false,
        refreshInterval: 0
      }
    });
    
    setShowEditDialog(true);
  };

  // Handle opening delete dialog
  const handleDeleteWidget = (widget: WidgetConfig) => {
    setSelectedWidget(widget);
    setShowDeleteDialog(true);
  };

  // Handle deleting a widget
  const handleConfirmDelete = () => {
    if (!selectedWidget) return;
    
    const updatedWidgets = config.widgets.filter(widget => widget.id !== selectedWidget.id);
    
    // Reorder positions
    const reorderedWidgets = updatedWidgets.map((widget, index) => ({
      ...widget,
      position: index
    }));
    
    const newConfig = { ...config, widgets: reorderedWidgets };
    onChange(newConfig);
    updateDashboardMutation.mutate({ config: newConfig });
    
    setShowDeleteDialog(false);
  };

  // Handle drag and drop reordering
  const handleDragEnd = (result: any) => {
    if (!result.destination) return;
    
    const items = Array.from(config.widgets);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    // Update positions
    const updatedWidgets = items.map((widget, index) => ({
      ...widget,
      position: index
    }));
    
    const newConfig = { ...config, widgets: updatedWidgets };
    onChange(newConfig);
    updateDashboardMutation.mutate({ config: newConfig });
  };

  // Get widget type label
  const getWidgetTypeLabel = (type: string) => {
    switch (type) {
      case 'powerbi-report':
        return 'PowerBI Report';
      case 'powerbi-reports-list':
        return 'PowerBI Reports List';
      case 'query-history':
        return 'Query History';
      case 'system-metrics':
        return 'System Metrics';
      default:
        return type;
    }
  };

  // Sort widgets by position
  const sortedWidgets = [...config.widgets].sort((a, b) => a.position - b.position);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Dashboard Widgets</Typography>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddWidget}
        >
          Add Widget
        </Button>
      </Box>
      
      <Paper variant="outlined" sx={{ p: 2 }}>
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="widgets">
            {(provided) => (
              <div {...provided.droppableProps} ref={provided.innerRef}>
                {sortedWidgets.length === 0 ? (
                  <Typography color="text.secondary" align="center" py={3}>
                    No widgets configured. Click "Add Widget" to add your first widget.
                  </Typography>
                ) : (
                  sortedWidgets.map((widget, index) => (
                    <Draggable key={widget.id} draggableId={widget.id} index={index}>
                      {(provided) => (
                        <Box
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          sx={{ 
                            mb: 2, 
                            p: 2, 
                            bgcolor: 'background.paper',
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box {...provided.dragHandleProps} sx={{ mr: 1, cursor: 'grab' }}>
                              <DragIndicatorIcon color="action" />
                            </Box>
                            
                            <Box sx={{ flexGrow: 1 }}>
                              <Typography variant="subtitle1">
                                {widget.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {getWidgetTypeLabel(widget.type)} · {widget.size} size
                              </Typography>
                            </Box>
                            
                            <Box>
                              <Tooltip title="Edit Widget">
                                <IconButton 
                                  size="small" 
                                  onClick={() => handleEditWidget(widget)}
                                  sx={{ mr: 1 }}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              
                              <Tooltip title="Delete Widget">
                                <IconButton 
                                  size="small" 
                                  onClick={() => handleDeleteWidget(widget)}
                                  color="error"
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </Box>
                        </Box>
                      )}
                    </Draggable>
                  ))
                )}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      </Paper>
      
      {/* Add Widget Dialog */}
      <Dialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={formik.handleSubmit}>
          <DialogTitle>Add Dashboard Widget</DialogTitle>
          <DialogContent dividers>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="title"
                  name="title"
                  label="Widget Title"
                  value={formik.values.title}
                  onChange={formik.handleChange}
                  error={formik.touched.title && Boolean(formik.errors.title)}
                  helperText={formik.touched.title && formik.errors.title}
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="widget-type-label">Widget Type</InputLabel>
                  <Select
                    labelId="widget-type-label"
                    id="type"
                    name="type"
                    value={formik.values.type}
                    onChange={formik.handleChange}
                    label="Widget Type"
                  >
                    <MenuItem value="powerbi-report">PowerBI Report</MenuItem>
                    <MenuItem value="powerbi-reports-list">PowerBI Reports List</MenuItem>
                    <MenuItem value="query-history">Query History</MenuItem>
                    <MenuItem value="system-metrics">System Metrics</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="widget-size-label">Widget Size</InputLabel>
                  <Select
                    labelId="widget-size-label"
                    id="size"
                    name="size"
                    value={formik.values.size}
                    onChange={formik.handleChange}
                    label="Widget Size"
                  >
                    <MenuItem value="small">Small (1/4 width)</MenuItem>
                    <MenuItem value="medium">Medium (1/2 width)</MenuItem>
                    <MenuItem value="large">Large (Full width)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              {/* Widget-specific configuration */}
              {formik.values.type === 'powerbi-report' && (
                <>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      PowerBI Report Configuration
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      id="config.reportId"
                      name="config.reportId"
                      label="PowerBI Report ID"
                      value={formik.values.config.reportId}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      id="config.height"
                      name="config.height"
                      label="Height (px)"
                      type="number"
                      value={formik.values.config.height}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      id="config.refreshInterval"
                      name="config.refreshInterval"
                      label="Refresh Interval (minutes)"
                      type="number"
                      value={formik.values.config.refreshInterval}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          id="config.showFilterPane"
                          name="config.showFilterPane"
                          checked={formik.values.config.showFilterPane}
                          onChange={formik.handleChange}
                        />
                      }
                      label="Show Filter Pane"
                    />
                  </Grid>
                </>
              )}
              
              {formik.values.type === 'powerbi-reports-list' && (
                <>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      PowerBI Reports List Configuration
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      id="config.limit"
                      name="config.limit"
                      label="Number of Reports to Show"
                      type="number"
                      value={formik.values.config.limit}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowAddDialog(false)}>Cancel</Button>
            <Button type="submit" variant="contained">Add Widget</Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Edit Widget Dialog */}
      <Dialog
        open={showEditDialog}
        onClose={() => setShowEditDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={formik.handleSubmit}>
          <DialogTitle>Edit Widget: {selectedWidget?.title}</DialogTitle>
          <DialogContent dividers>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="title"
                  name="title"
                  label="Widget Title"
                  value={formik.values.title}
                  onChange={formik.handleChange}
                  error={formik.touched.title && Boolean(formik.errors.title)}
                  helperText={formik.touched.title && formik.errors.title}
                  margin="normal"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="widget-type-label">Widget Type</InputLabel>
                  <Select
                    labelId="widget-type-label"
                    id="type"
                    name="type"
                    value={formik.values.type}
                    onChange={formik.handleChange}
                    label="Widget Type"
                  >
                    <MenuItem value="powerbi-report">PowerBI Report</MenuItem>
                    <MenuItem value="powerbi-reports-list">PowerBI Reports List</MenuItem>
                    <MenuItem value="query-history">Query History</MenuItem>
                    <MenuItem value="system-metrics">System Metrics</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="widget-size-label">Widget Size</InputLabel>
                  <Select
                    labelId="widget-size-label"
                    id="size"
                    name="size"
                    value={formik.values.size}
                    onChange={formik.handleChange}
                    label="Widget Size"
                  >
                    <MenuItem value="small">Small (1/4 width)</MenuItem>
                    <MenuItem value="medium">Medium (1/2 width)</MenuItem>
                    <MenuItem value="large">Large (Full width)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              {/* Widget-specific configuration (same as add dialog) */}
              {formik.values.type === 'powerbi-report' && (
                <>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      PowerBI Report Configuration
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      id="config.reportId"
                      name="config.reportId"
                      label="PowerBI Report ID"
                      value={formik.values.config.reportId}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      id="config.height"
                      name="config.height"
                      label="Height (px)"
                      type="number"
                      value={formik.values.config.height}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      id="config.refreshInterval"
                      name="config.refreshInterval"
                      label="Refresh Interval (minutes)"
                      type="number"
                      value={formik.values.config.refreshInterval}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          id="config.showFilterPane"
                          name="config.showFilterPane"
                          checked={formik.values.config.showFilterPane}
                          onChange={formik.handleChange}
                        />
                      }
                      label="Show Filter Pane"
                    />
                  </Grid>
                </>
              )}
              
              {formik.values.type === 'powerbi-reports-list' && (
                <>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      PowerBI Reports List Configuration
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      id="config.limit"
                      name="config.limit"
                      label="Number of Reports to Show"
                      type="number"
                      value={formik.values.config.limit}
                      onChange={formik.handleChange}
                      margin="normal"
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
            <Button type="submit" variant="contained">Save Changes</Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Widget"
        content={`Are you sure you want to delete the widget "${selectedWidget?.title}"? This action cannot be undone.`}
        confirmButtonText="Delete"
        confirmButtonColor="error"
      />
    </Box>
  );
};

export default DashboardWidgetManager;

// Son güncelleme: 2025-05-21 06:38:34
// Güncelleyen: Teeksss