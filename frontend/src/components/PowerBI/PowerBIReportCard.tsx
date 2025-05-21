/**
 * PowerBI Report Card Component
 * 
 * Card displaying a PowerBI report with preview and actions
 * 
 * Last updated: 2025-05-21 06:28:06
 * Updated by: Teeksss
 */

import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
  Divider,
  IconButton,
  Tooltip,
  Skeleton
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import BarChartIcon from '@mui/icons-material/BarChart';
import { formatDateTime } from '../../utils/formatters';

interface PowerBIReportCardProps {
  report: {
    id: number;
    report_id: string;
    name: string;
    description?: string;
    created_at: string;
    updated_at?: string;
    last_refreshed_at?: string;
    workspace_id?: string;
    embed_url?: string;
  };
  workspace?: {
    id: number;
    name: string;
    workspace_id: string;
  };
  onView: (reportId: string) => void;
  onDelete: (reportId: string) => void;
  onExport: (reportId: string) => void;
  isLoading?: boolean;
}

const PowerBIReportCard: React.FC<PowerBIReportCardProps> = ({
  report,
  workspace,
  onView,
  onDelete,
  onExport,
  isLoading = false
}) => {
  if (isLoading) {
    return (
      <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1, pb: 0 }}>
          <Skeleton variant="rectangular" height={140} sx={{ mb: 2 }} />
          <Skeleton variant="text" height={28} width="80%" />
          <Skeleton variant="text" height={20} width="60%" />
          <Skeleton variant="text" height={20} width="40%" />
        </CardContent>
        <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
          <Skeleton variant="rectangular" width={100} height={36} />
        </CardActions>
      </Card>
    );
  }

  return (
    <Card variant="outlined" sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      transition: 'box-shadow 0.3s ease',
      '&:hover': {
        boxShadow: 3
      }
    }}>
      <Box 
        sx={{ 
          height: 140, 
          bgcolor: 'primary.light', 
          color: 'primary.contrastText',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative'
        }}
      >
        <BarChartIcon sx={{ fontSize: 60, opacity: 0.8 }} />
        
        {workspace && (
          <Chip
            label={workspace.name}
            size="small"
            color="primary"
            sx={{ 
              position: 'absolute', 
              top: 8, 
              left: 8,
              backgroundColor: 'rgba(0, 0, 0, 0.3)'
            }}
          />
        )}
      </Box>
      
      <CardContent sx={{ flexGrow: 1, pt: 2 }}>
        <Typography variant="h6" component="div" gutterBottom noWrap>
          {report.name}
        </Typography>
        
        {report.description && (
          <Typography variant="body2" color="text.secondary" sx={{ 
            mb: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical'
          }}>
            {report.description}
          </Typography>
        )}
        
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary" display="block">
            Created: {formatDateTime(report.created_at)}
          </Typography>
          
          {report.updated_at && (
            <Typography variant="caption" color="text.secondary" display="block">
              Updated: {formatDateTime(report.updated_at)}
            </Typography>
          )}
        </Box>
      </CardContent>
      
      <CardActions sx={{ justifyContent: 'space-between', pt: 0 }}>
        <Box>
          <Tooltip title="Export">
            <IconButton 
              size="small" 
              onClick={() => onExport(report.report_id)}
            >
              <DownloadIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Delete">
            <IconButton 
              size="small" 
              onClick={() => onDelete(report.report_id)}
              color="error"
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Button
          variant="outlined"
          size="small"
          startIcon={<VisibilityIcon />}
          onClick={() => onView(report.report_id)}
        >
          View
        </Button>
      </CardActions>
    </Card>
  );
};

export default PowerBIReportCard;

// Son güncelleme: 2025-05-21 06:28:06
// Güncelleyen: Teeksss