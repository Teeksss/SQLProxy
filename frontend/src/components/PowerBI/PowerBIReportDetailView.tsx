/**
 * PowerBI Report Detail View Component
 * 
 * Displays detailed information about a PowerBI report with options for embedding,
 * exporting, and managing the report.
 * 
 * Last updated: 2025-05-21 06:23:45
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Divider,
  Button,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  Link
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import RefreshIcon from '@mui/icons-material/Refresh';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import InfoIcon from '@mui/icons-material/Info';
import { toast } from 'react-toastify';

import { powerbiApi } from '../../services/powerbiService';
import PowerBIReportEmbed from './PowerBIReportEmbed';
import PowerBIExportOptions from './PowerBIExportOptions';
import NoDataPlaceholder from '../common/NoDataPlaceholder';
import ConfirmationDialog from '../common/ConfirmationDialog';
import { formatDateTime } from '../../utils/formatters';

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
      id={`report-detail-tabpanel-${index}`}
      aria-labelledby={`report-detail-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
};

const PowerBIReportDetailView: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const [tabIndex, setTabIndex] = useState(0);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [fullscreenView, setFullscreenView] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Query for fetching report details
  const {
    data: report,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['powerbi-report', reportId],
    () => powerbiApi.getReport(reportId as string),
    {
      enabled: !!reportId,
      staleTime: 60000 // 1 minute
    }
  );

  // Query for fetching report pages
  const {
    data: reportPages,
    isLoading: isLoadingPages
  } = useQuery(
    ['powerbi-report-pages', reportId],
    () => powerbiApi.getReportPages(reportId as string, report?.workspace_id),
    {
      enabled: !!reportId && !!report,
      staleTime: 300000 // 5 minutes
    }
  );

  // Mutation for deleting report
  const deleteReportMutation = useMutation(
    () => powerbiApi.deleteReport(reportId as string),
    {
      onSuccess: () => {
        toast.success('Report deleted successfully');
        navigate('/powerbi/reports');
      },
      onError: (error: any) => {
        toast.error(`Error deleting report: ${error.message}`);
      }
    }
  );

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  // Handle delete report
  const handleDeleteReport = () => {
    setShowDeleteDialog(true);
  };

  // Handle confirm delete
  const handleConfirmDelete = () => {
    deleteReportMutation.mutate();
  };

  // Handle fullscreen toggle
  const handleToggleFullscreen = () => {
    setFullscreenView(!fullscreenView);
  };

  // Handle report error
  const handleReportError = (error: any) => {
    toast.error(`Error loading report: ${error.message || 'Unknown error'}`);
  };

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error || !report) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading report: {((error as Error)?.message) || 'Report not found'}
      </Alert>
    );
  }

  return (
    <>
      {fullscreenView ? (
        // Fullscreen view
        <Box sx={{ 
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 9999,
          bgcolor: 'background.paper',
          p: 2
        }}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
            <Button
              variant="outlined"
              onClick={handleToggleFullscreen}
              startIcon={<FullscreenIcon />}
            >
              Exit Fullscreen
            </Button>
          </Box>
          
          <PowerBIReportEmbed
            reportId={reportId as string}
            embedHeight="calc(100vh - 70px)"
            filterPane={true}
            navPane={true}
            onReportError={handleReportError}
          />
        </Box>
      ) : (
        // Normal view
        <Box sx={{ py: 2 }}>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h5" component="h1">
                {report.name}
              </Typography>
              
              {report.description && (
                <Typography variant="body2" color="text.secondary">
                  {report.description}
                </Typography>
              )}
            </Box>
            
            <Box>
              <Tooltip title="Fullscreen">
                <IconButton 
                  onClick={handleToggleFullscreen}
                  color="primary"
                  sx={{ mr: 1 }}
                >
                  <FullscreenIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Refresh">
                <IconButton 
                  onClick={() => refetch()}
                  sx={{ mr: 1 }}
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Delete Report">
                <IconButton 
                  onClick={handleDeleteReport}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={9}>
              <Paper variant="outlined" sx={{ mb: 3 }}>
                <PowerBIReportEmbed
                  reportId={reportId as string}
                  embedHeight={600}
                  filterPane={true}
                  navPane={true}
                  onReportError={handleReportError}
                />
              </Paper>
              
              <Paper variant="outlined">
                <Tabs
                  value={tabIndex}
                  onChange={handleTabChange}
                  aria-label="report details tabs"
                  sx={{ px: 2, pt: 1 }}
                >
                  <Tab label="Export Options" id="report-detail-tab-0" />
                  <Tab label="Report Info" id="report-detail-tab-1" />
                </Tabs>
                <Divider />
                
                <TabPanel value={tabIndex} index={0}>
                  <PowerBIExportOptions
                    reportId={reportId as string}
                    reportName={report.name}
                    workspaceId={report.workspace_id}
                    pages={reportPages?.pages}
                  />
                </TabPanel>
                
                <TabPanel value={tabIndex} index={1}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Report Details
                      </Typography>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" component="span">
                          ID:
                        </Typography>
                        <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                          {report.report_id}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" component="span">
                          Workspace:
                        </Typography>
                        <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                          {report.workspace_id || 'My Workspace'}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" component="span">
                          Created:
                        </Typography>
                        <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                          {formatDateTime(report.created_at)}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" component="span">
                          Last Updated:
                        </Typography>
                        <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                          {report.updated_at ? formatDateTime(report.updated_at) : 'Never'}
                        </Typography>
                      </Box>
                      
                      {report.dataset_id && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" component="span">
                            Dataset:
                          </Typography>
                          <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                            <Link href={`/powerbi/datasets/${report.dataset_id}`}>
                              {report.dataset_id}
                            </Link>
                          </Typography>
                        </Box>
                      )}
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle1" gutterBottom>
                        Pages
                      </Typography>
                      
                      {isLoadingPages ? (
                        <CircularProgress size={24} />
                      ) : reportPages?.pages && reportPages.pages.length > 0 ? (
                        <Box>
                          {reportPages.pages.map((page, index) => (
                            <Chip
                              key={page.name}
                              label={page.displayName}
                              sx={{ m: 0.5 }}
                              color={index === 0 ? 'primary' : 'default'}
                              variant={index === 0 ? 'filled' : 'outlined'}
                            />
                          ))}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No pages information available
                        </Typography>
                      )}
                    </Grid>
                  </Grid>
                </TabPanel>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Card variant="outlined" sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Embed Information
                  </Typography>
                  
                  <Alert severity="info" sx={{ mb: 2 }}>
                    This report is embedded using the PowerBI Embed API. You can share this report with users who have appropriate permissions.
                  </Alert>
                  
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={() => navigator.clipboard.writeText(window.location.href)}
                  >
                    Copy Report Link
                  </Button>
                </CardContent>
              </Card>
              
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Related Resources
                  </Typography>
                  
                  <Box sx={{ mb: 1 }}>
                    <Link href={`/powerbi/workspaces/${report.workspace_id || 'my'}`}>
                      View Workspace
                    </Link>
                  </Box>
                  
                  {report.dataset_id && (
                    <Box sx={{ mb: 1 }}>
                      <Link href={`/powerbi/datasets/${report.dataset_id}`}>
                        View Dataset
                      </Link>
                    </Box>
                  )}
                  
                  <Box>
                    <Link href="/powerbi/reports">
                      All Reports
                    </Link>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          
          {/* Delete Confirmation Dialog */}
          <ConfirmationDialog
            open={showDeleteDialog}
            onClose={() => setShowDeleteDialog(false)}
            onConfirm={handleConfirmDelete}
            title="Delete PowerBI Report"
            content={
              <>
                <Typography variant="body1" gutterBottom>
                  Are you sure you want to delete the report "{report.name}"?
                </Typography>
                <Typography variant="body2" color="error">
                  This action cannot be undone.
                </Typography>
              </>
            }
            confirmButtonText="Delete"
            confirmButtonColor="error"
            isSubmitting={deleteReportMutation.isLoading}
          />
        </Box>
      )}
    </>
  );
};

export default PowerBIReportDetailView;

// Son güncelleme: 2025-05-21 06:23:45
// Güncelleyen: Teeksss