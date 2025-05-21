/**
 * Refresh History List Component
 * 
 * Displays the history of dataset refresh operations
 * 
 * Last updated: 2025-05-21 06:02:47
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import { useQuery } from 'react-query';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';

import { powerbiApi } from '../../services/powerbiService';
import NoDataPlaceholder from '../common/NoDataPlaceholder';
import { formatDateTime, formatDuration } from '../../utils/formatters';

interface RefreshHistoryListProps {
  datasetId: string;
  workspaceId?: string;
}

const RefreshHistoryList: React.FC<RefreshHistoryListProps> = ({ datasetId, workspaceId }) => {
  // Query for fetching refresh history
  const {
    data: historyData,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['refresh-history', datasetId, workspaceId],
    () => powerbiApi.getRefreshHistory(datasetId, workspaceId),
    {
      staleTime: 30000 // 30 seconds
    }
  );

  // Get status chip color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed':
        return 'success';
      case 'Failed':
        return 'error';
      case 'InProgress':
      case 'NotStarted':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Calculate refresh duration
  const calculateDuration = (startTime: string, endTime: string) => {
    if (!startTime || !endTime) return 'N/A';
    
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();
    
    if (isNaN(start) || isNaN(end)) return 'N/A';
    
    const durationMs = end - start;
    return formatDuration(durationMs / 1000);
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
  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading refresh history: {(error as Error).message}
      </Alert>
    );
  }

  // No data
  if (!historyData?.history || historyData.history.length === 0) {
    return (
      <NoDataPlaceholder message="No refresh history available for this dataset" />
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="subtitle1">
          Refresh History
        </Typography>
        
        <Tooltip title="Refresh History">
          <IconButton onClick={() => refetch()}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>
      
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Start Time</TableCell>
              <TableCell>End Time</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Service</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {historyData.history.map((item: any, index: number) => (
              <TableRow key={index} hover>
                <TableCell>{formatDateTime(item.startTime)}</TableCell>
                <TableCell>{item.endTime ? formatDateTime(item.endTime) : 'In Progress'}</TableCell>
                <TableCell>{calculateDuration(item.startTime, item.endTime)}</TableCell>
                <TableCell>
                  <Chip 
                    size="small"
                    label={item.status} 
                    color={getStatusColor(item.status)}
                  />
                </TableCell>
                <TableCell>{item.refreshType || 'Manual'}</TableCell>
                <TableCell>
                  {item.serviceExceptionJson && (
                    <Tooltip title={item.serviceExceptionJson}>
                      <IconButton size="small" color="error">
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default RefreshHistoryList;

// Son güncelleme: 2025-05-21 06:02:47
// Güncelleyen: Teeksss