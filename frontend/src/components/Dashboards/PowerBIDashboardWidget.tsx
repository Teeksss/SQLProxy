/**
 * PowerBI Dashboard Widget Component
 * 
 * Widget for displaying PowerBI reports on dashboard pages
 * 
 * Last updated: 2025-05-21 06:28:06
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Typography,
  Alert,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  Divider
} from '@mui/material';
import { useQuery } from 'react-query';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import RefreshIcon from '@mui/icons-material/Refresh';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { useNavigate } from 'react-router-dom';

import { powerbiApi } from '../../services/powerbiService';
import PowerBIReportEmbed from '../PowerBI/PowerBIReportEmbed';
import PowerBIReportsGrid from '../PowerBI/PowerBIReportsGrid';

interface PowerBIDashboardWidgetProps {
  title?: string;
  type: 'single-report' | 'recent-reports';
  reportId?: string;
  limit?: number;
  height?: number | string;
  onEdit?: () => void;
  onRemove?: () => void;
}

const PowerBIDashboardWidget: React.FC<PowerBIDashboardWidgetProps> = ({
  title = 'PowerBI Reports',
  type = 'recent-reports',
  reportId,
  limit = 4,
  height = 400,
  onEdit,
  onRemove
}) => {
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const navigate = useNavigate();

  // Query for fetching report details if in single-report mode
  const {
    data: report,
    isLoading: isLoadingReport,
    error: reportError,
    refetch: refetchReport
  } = useQuery(
    ['powerbi-report', reportId],
    () => powerbiApi.getReport(reportId as string),
    {
      enabled: type === 'single-report' && !!reportId,
      staleTime: 300000 // 5 minutes
    }
  );

  // Handle menu open
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchorEl(event.currentTarget);
  };

  // Handle menu close
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };

  // Handle fullscreen toggle
  const handleToggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    handleMenuClose();
  };

  // Handle navigate to reports page
  const handleNavigateToReports = () => {
    if (type === 'single-report' && reportId) {
      navigate(`/powerbi/reports/${reportId}`);
    } else {
      navigate('/powerbi/reports');
    }
    handleMenuClose();
  };

  // Handle refresh
  const handleRefresh = () => {
    if (type === 'single-report' && reportId) {
      refetchReport();
    }
    handleMenuClose();
  };

  // Handle edit
  const handleEdit = () => {
    if (onEdit) {
      onEdit();
    }
    handleMenuClose();
  };

  // Handle remove
  const handleRemove = () => {
    if (onRemove) {
      onRemove();
    }
    handleMenuClose();
  };

  // Calculate content height
  const contentHeight = 
    typeof height === 'number' 
      ? height - (title ? 64 : 0) // Adjust for header if title is present
      : height;

  // Render fullscreen view
  if (isFullscreen) {
    return (
      <Box sx={{ 
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        bgcolor: 'background.paper',
        zIndex: 1300,
        p: 2,
        boxSizing: 'border-box'
      }}>
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          mb: 2
        }}>
          <Typography variant="h6">{title}</Typography>
          
          <Box>
            <Tooltip title="Exit Fullscreen">
              <IconButton onClick={handleToggleFullscreen}>
                <FullscreenIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Open in New Page">
              <IconButton onClick={handleNavigateToReports}>
                <OpenInNewIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        <Box sx={{ height: 'calc(100% - 64px)' }}>
          {type === 'single-report' && reportId ? (
            <PowerBIReportEmbed
              reportId={reportId}
              embedHeight="100%"
              filterPane={true}
              navPane={true}
            />
          ) : (
            <PowerBIReportsGrid limit={12} />
          )}
        </Box>
      </Box>
    );
  }

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {title && (
        <CardHeader
          title={title}
          action={
            <>
              <Tooltip title="Refresh">
                <IconButton size="small" onClick={handleRefresh}>
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Fullscreen">
                <IconButton size="small" onClick={handleToggleFullscreen}>
                  <FullscreenIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <IconButton size="small" onClick={handleMenuOpen}>
                <MoreVertIcon fontSize="small" />
              </IconButton>
              
              <Menu
                anchorEl={menuAnchorEl}
                open={Boolean(menuAnchorEl)}
                onClose={handleMenuClose}
              >
                <MenuItem onClick={handleNavigateToReports}>
                  Open in New Page
                </MenuItem>
                
                <MenuItem onClick={handleRefresh}>
                  Refresh
                </MenuItem>
                
                {onEdit && (
                  <MenuItem onClick={handleEdit}>
                    Edit Widget
                  </MenuItem>
                )}
                
                {onRemove && (
                  <MenuItem onClick={handleRemove}>
                    Remove Widget
                  </MenuItem>
                )}
              </Menu>
            </>
          }
        />
      )}
      
      <CardContent 
        sx={{ 
          flexGrow: 1, 
          p: 1,
          height: contentHeight,
          overflow: 'hidden'
        }}
      >
        {type === 'single-report' && reportId ? (
          isLoadingReport ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress />
            </Box>
          ) : reportError ? (
            <Alert severity="error">
              {(reportError as Error).message || 'Error loading report'}
            </Alert>
          ) : !report ? (
            <Alert severity="warning">
              Report not found
            </Alert>
          ) : (
            <PowerBIReportEmbed
              reportId={reportId}
              embedHeight="100%"
              filterPane={false}
              navPane={false}
            />
          )
        ) : (
          <PowerBIReportsGrid limit={limit} />
        )}
      </CardContent>
    </Card>
  );
};

export default PowerBIDashboardWidget;

// Son güncelleme: 2025-05-21 06:28:06
// Güncelleyen: Teeksss