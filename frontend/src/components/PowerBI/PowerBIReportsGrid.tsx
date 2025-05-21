/**
 * PowerBI Reports Grid Component
 * 
 * Grid display of PowerBI reports with card layout
 * 
 * Last updated: 2025-05-21 06:28:06
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Grid,
  Box,
  Typography,
  Button,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import { toast } from 'react-toastify';

import { powerbiApi } from '../../services/powerbiService';
import PowerBIReportCard from './PowerBIReportCard';
import PowerBIReportEmbed from './PowerBIReportEmbed';
import CreatePowerBIReportForm from './CreatePowerBIReportForm';
import ConfirmationDialog from '../common/ConfirmationDialog';
import NoDataPlaceholder from '../common/NoDataPlaceholder';

interface PowerBIReportsGridProps {
  workspaceId?: string;
  limit?: number;
}

const PowerBIReportsGrid: React.FC<PowerBIReportsGridProps> = ({
  workspaceId,
  limit
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query for fetching workspaces
  const {
    data: workspaces,
    isLoading: isLoadingWorkspaces
  } = useQuery(
    ['powerbi-workspaces'],
    powerbiApi.getWorkspaces,
    {
      staleTime: 300000, // 5 minutes
      enabled: !workspaceId // Only fetch if workspace is not specified
    }
  );

  // Query for fetching reports
  const {
    data: reports,
    isLoading: isLoadingReports,
    error: reportsError,
    refetch: refetchReports
  } = useQuery(
    ['powerbi-reports', workspaceId || selectedWorkspace],
    () => powerbiApi.getReports(workspaceId || selectedWorkspace || undefined),
    {
      staleTime: 60000 // 1 minute
    }
  );

  // Delete report mutation
  const deleteReportMutation = useMutation(
    (reportId: string) => powerbiApi.deleteReport(reportId),
    {
      onSuccess: () => {
        toast.success('Report deleted successfully');
        queryClient.invalidateQueries(['powerbi-reports']);
        setShowDeleteDialog(false);
      },
      onError: (error: any) => {
        toast.error(`Error deleting report: ${error.message}`);
      }
    }
  );

  // Handle search change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  // Handle workspace change
  const handleWorkspaceChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedWorkspace(event.target.value as string);
  };

  // Handle view report
  const handleViewReport = (reportId: string) => {
    if (limit) {
      // In limited mode, open dialog
      const report = reports?.items.find(r => r.report_id === reportId);
      if (report) {
        setSelectedReport(report);
        setShowViewDialog(true);
      }
    } else {
      // In full mode, navigate to report detail page
      navigate(`/powerbi/reports/${reportId}`);
    }
  };

  // Handle delete report
  const handleDeleteReport = (reportId: string) => {
    const report = reports?.items.find(r => r.report_id === reportId);
    if (report) {
      setSelectedReport(report);
      setShowDeleteDialog(true);
    }
  };

  // Handle export report
  const handleExportReport = (reportId: string) => {
    navigate(`/powerbi/reports/${reportId}?tab=export`);
  };

  // Handle confirm delete
  const handleConfirmDelete = () => {
    if (selectedReport) {
      deleteReportMutation.mutate(selectedReport.report_id);
    }
  };

  // Filter reports by search term
  const filteredReports = React.useMemo(() => {
    if (!reports?.items) return [];
    
    return reports.items.filter(report => 
      searchTerm === '' || 
      report.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (report.description && report.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [reports?.items, searchTerm]);

  // Limit reports if needed
  const displayedReports = React.useMemo(() => {
    return limit ? filteredReports.slice(0, limit) : filteredReports;
  }, [filteredReports, limit]);

  // Create workspace map for faster lookup
  const workspaceMap = React.useMemo(() => {
    if (!workspaces?.items) return {};
    
    return workspaces.items.reduce((acc: Record<string, any>, workspace) => {
      acc[workspace.workspace_id] = workspace;
      return acc;
    }, {});
  }, [workspaces?.items]);

  // Loading state
  const isLoading = isLoadingReports || (isLoadingWorkspaces && !workspaceId);

  // Error state
  if (reportsError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading PowerBI reports: {(reportsError as Error).message}
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {!limit && (
        <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search reports..."
                value={searchTerm}
                onChange={handleSearchChange}
                variant="outlined"
                size="small"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            {!workspaceId && (
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small" variant="outlined">
                  <InputLabel id="workspace-filter-label">Workspace</InputLabel>
                  <Select
                    labelId="workspace-filter-label"
                    id="workspace-filter"
                    value={selectedWorkspace}
                    onChange={handleWorkspaceChange as any}
                    label="Workspace"
                  >
                    <MenuItem value="">All Workspaces</MenuItem>
                    {workspaces?.items?.map((workspace: any) => (
                      <MenuItem key={workspace.workspace_id} value={workspace.workspace_id}>
                        {workspace.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12} md={4} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setShowCreateDialog(true)}
              >
                Create Report
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}
      
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : !displayedReports || displayedReports.length === 0 ? (
        <NoDataPlaceholder 
          message={
            searchTerm ? 
              "No reports match your search criteria" : 
              "No PowerBI reports found"
          }
          actionButton={
            limit ? undefined : (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setShowCreateDialog(true)}
              >
                Create First Report
              </Button>
            )
          }
        />
      ) : (
        <Grid container spacing={3}>
          {displayedReports.map((report) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={report.report_id}>
              <PowerBIReportCard
                report={report}
                workspace={report.workspace_id ? workspaceMap[report.workspace_id] : undefined}
                onView={handleViewReport}
                onDelete={handleDeleteReport}
                onExport={handleExportReport}
              />
            </Grid>
          ))}
          
          {/* Loading skeleton placeholders */}
          {isLoading && [1, 2, 3, 4].map((item) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={`skeleton-${item}`}>
              <PowerBIReportCard
                report={{
                  id: 0,
                  report_id: '',
                  name: '',
                  created_at: ''
                }}
                onView={() => {}}
                onDelete={() => {}}
                onExport={() => {}}
                isLoading={true}
              />
            </Grid>
          ))}
        </Grid>
      )}
      
      {/* Show more button when limited */}
      {limit && filteredReports.length > limit && (
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
          <Button 
            variant="outlined"
            onClick={() => navigate('/powerbi/reports')}
          >
            View All Reports
          </Button>
        </Box>
      )}
      
      {/* Create Report Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create PowerBI Report</DialogTitle>
        <DialogContent>
          <CreatePowerBIReportForm 
            workspaces={workspaces?.items || []}
            onSuccess={() => {
              setShowCreateDialog(false);
              queryClient.invalidateQueries(['powerbi-reports']);
              toast.success('Report created successfully');
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
      
      {/* View Report Dialog */}
      <Dialog
        open={showViewDialog}
        onClose={() => setShowViewDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>{selectedReport?.name}</DialogTitle>
        <DialogContent dividers>
          {selectedReport && (
            <PowerBIReportEmbed 
              reportId={selectedReport.report_id} 
              embedHeight={600}
              onReportError={(error) => {
                toast.error(`Error loading report: ${error.message || 'Unknown error'}`);
              }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            variant="outlined" 
            onClick={() => navigate(`/powerbi/reports/${selectedReport.report_id}`)}
          >
            Open Full Report
          </Button>
          <Button onClick={() => setShowViewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleConfirmDelete}
        title="Delete PowerBI Report"
        content="Are you sure you want to delete this report? This action cannot be undone."
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isSubmitting={deleteReportMutation.isLoading}
      />
    </Box>
  );
};

export default PowerBIReportsGrid;

// Son güncelleme: 2025-05-21 06:28:06
// Güncelleyen: Teeksss