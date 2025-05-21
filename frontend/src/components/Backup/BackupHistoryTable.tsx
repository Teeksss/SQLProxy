/**
 * Backup History Table Component
 * 
 * Displays the history of database backups with filtering and restore options
 * 
 * Last updated: 2025-05-21 05:21:55
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Tooltip,
  Chip,
  Typography,
  Box,
  TextField,
  InputAdornment,
  Button,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import SearchIcon from '@mui/icons-material/Search';
import RestoreIcon from '@mui/icons-material/Restore';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import InfoIcon from '@mui/icons-material/Info';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FilterListIcon from '@mui/icons-material/FilterList';
import { toast } from 'react-toastify';

import { backupApi } from '../../services/backupService';
import { BackupRecord, BackupStatus, BackupType } from '../../types/backup';
import ConfirmationDialog from '../common/ConfirmationDialog';
import BackupDetailsDialog from './BackupDetailsDialog';
import { formatDateTime, formatFileSize } from '../../utils/formatters';

interface BackupHistoryTableProps {
  onRefresh?: () => void;
}

const BackupHistoryTable: React.FC<BackupHistoryTableProps> = ({ onRefresh }) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBackup, setSelectedBackup] = useState<BackupRecord | null>(null);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuBackup, setMenuBackup] = useState<BackupRecord | null>(null);
  
  const queryClient = useQueryClient();
  
  // Fetch backup history
  const { 
    data: backups, 
    isLoading, 
    error, 
    refetch 
  } = useQuery(
    ['backupHistory', page, rowsPerPage, typeFilter],
    () => backupApi.getBackups({
      page: page + 1,
      limit: rowsPerPage,
      backupType: typeFilter !== 'all' ? typeFilter : undefined
    }),
    {
      keepPreviousData: true,
      onError: (error: any) => {
        toast.error(`Error loading backup history: ${error.message}`);
      }
    }
  );
  
  // Restore backup mutation
  const restoreMutation = useMutation(
    (backupId: string) => backupApi.restoreBackup(backupId),
    {
      onSuccess: () => {
        toast.success('Backup restored successfully');
        setShowRestoreDialog(false);
        queryClient.invalidateQueries(['backupHistory']);
        if (onRefresh) onRefresh();
      },
      onError: (error: any) => {
        toast.error(`Error restoring backup: ${error.message}`);
      }
    }
  );
  
  // Delete backup mutation
  const deleteMutation = useMutation(
    (backupId: string) => backupApi.deleteBackup(backupId),
    {
      onSuccess: () => {
        toast.success('Backup deleted successfully');
        setShowDeleteDialog(false);
        queryClient.invalidateQueries(['backupHistory']);
        if (onRefresh) onRefresh();
      },
      onError: (error: any) => {
        toast.error(`Error deleting backup: ${error.message}`);
      }
    }
  );
  
  // Handle page change
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };
  
  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Handle search change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };
  
  // Handle restore backup
  const handleRestoreBackup = () => {
    if (selectedBackup) {
      restoreMutation.mutate(selectedBackup.backup_id);
    }
  };
  
  // Handle delete backup
  const handleDeleteBackup = () => {
    if (selectedBackup) {
      deleteMutation.mutate(selectedBackup.backup_id);
    }
  };
  
  // Handle open restore dialog
  const handleOpenRestoreDialog = (backup: BackupRecord) => {
    setSelectedBackup(backup);
    setShowRestoreDialog(true);
    setAnchorEl(null);
  };
  
  // Handle open delete dialog
  const handleOpenDeleteDialog = (backup: BackupRecord) => {
    setSelectedBackup(backup);
    setShowDeleteDialog(true);
    setAnchorEl(null);
  };
  
  // Handle open details dialog
  const handleOpenDetailsDialog = (backup: BackupRecord) => {
    setSelectedBackup(backup);
    setShowDetailsDialog(true);
    setAnchorEl(null);
  };
  
  // Handle download backup
  const handleDownloadBackup = (backup: BackupRecord) => {
    backupApi.downloadBackup(backup.backup_id);
    setAnchorEl(null);
  };
  
  // Handle menu open
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, backup: BackupRecord) => {
    setAnchorEl(event.currentTarget);
    setMenuBackup(backup);
  };
  
  // Handle menu close
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  
  // Filter backups by search term
  const filteredBackups = React.useMemo(() => {
    if (!backups?.items) return [];
    
    return backups.items.filter(backup => 
      searchTerm === '' || 
      backup.backup_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      backup.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [backups?.items, searchTerm]);
  
  // Get backup status chip color
  const getStatusColor = (status: BackupStatus) => {
    switch (status) {
      case BackupStatus.COMPLETED:
        return 'success';
      case BackupStatus.IN_PROGRESS:
        return 'warning';
      case BackupStatus.FAILED:
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Get backup type chip color
  const getTypeColor = (type: BackupType) => {
    switch (type) {
      case BackupType.FULL:
        return 'primary';
      case BackupType.INCREMENTAL:
        return 'secondary';
      default:
        return 'default';
    }
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
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading backup history: {(error as Error).message}
      </Alert>
    );
  }
  
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Backup History</Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            placeholder="Search backups..."
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
            sx={{ width: 250 }}
          />
          
          <Button
            variant="outlined"
            size="small"
            startIcon={<FilterListIcon />}
            onClick={(e) => setTypeFilter(typeFilter === 'all' ? 'full' : typeFilter === 'full' ? 'incremental' : 'all')}
          >
            {typeFilter === 'all' ? 'All Types' : 
             typeFilter === 'full' ? 'Full Backups' : 'Incremental Backups'}
          </Button>
        </Box>
      </Box>
      
      <Paper variant="outlined">
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Backup ID</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredBackups.map((backup) => (
                <TableRow key={backup.backup_id} hover>
                  <TableCell>{backup.backup_id}</TableCell>
                  <TableCell>{backup.description}</TableCell>
                  <TableCell>
                    <Chip 
                      label={backup.backup_type} 
                      size="small" 
                      color={getTypeColor(backup.backup_type)}
                    />
                  </TableCell>
                  <TableCell>{formatDateTime(backup.created_at)}</TableCell>
                  <TableCell>{formatFileSize(backup.size_bytes)}</TableCell>
                  <TableCell>
                    <Chip 
                      label={backup.status} 
                      size="small" 
                      color={getStatusColor(backup.status)}
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Backup Options">
                      <IconButton 
                        size="small" 
                        onClick={(e) => handleMenuOpen(e, backup)}
                      >
                        <MoreVertIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              
              {filteredBackups.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No backup records found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={backups?.total || 0}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
      
      {/* Backup Options Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => menuBackup && handleOpenDetailsDialog(menuBackup)}>
          <ListItemIcon>
            <InfoIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => menuBackup && handleDownloadBackup(menuBackup)}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download</ListItemText>
        </MenuItem>
        <MenuItem 
          onClick={() => menuBackup && handleOpenRestoreDialog(menuBackup)}
          disabled={menuBackup?.status !== BackupStatus.COMPLETED}
        >
          <ListItemIcon>
            <RestoreIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Restore</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => menuBackup && handleOpenDeleteDialog(menuBackup)}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>
      
      {/* Restore Confirmation Dialog */}
      <ConfirmationDialog
        open={showRestoreDialog}
        onClose={() => setShowRestoreDialog(false)}
        onConfirm={handleRestoreBackup}
        title="Restore Backup"
        content={
          <>
            <Typography variant="body1" gutterBottom>
              Are you sure you want to restore this backup?
            </Typography>
            <Typography variant="body2" color="error">
              Warning: This will overwrite the current database with the backup data.
              All changes made since the backup was created will be lost.
            </Typography>
          </>
        }
        confirmButtonText="Restore"
        confirmButtonColor="warning"
        isSubmitting={restoreMutation.isLoading}
      />
      
      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteBackup}
        title="Delete Backup"
        content="Are you sure you want to delete this backup? This action cannot be undone."
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isSubmitting={deleteMutation.isLoading}
      />
      
      {/* Backup Details Dialog */}
      {selectedBackup && (
        <BackupDetailsDialog
          open={showDetailsDialog}
          onClose={() => setShowDetailsDialog(false)}
          backup={selectedBackup}
        />
      )}
    </Box>
  );
};

export default BackupHistoryTable;

// Son güncelleme: 2025-05-21 05:21:55
// Güncelleyen: Teeksss