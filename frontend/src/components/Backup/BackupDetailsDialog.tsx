/**
 * Backup Details Dialog Component
 * 
 * Displays detailed information about a backup
 * 
 * Last updated: 2025-05-21 05:21:55
 * Updated by: Teeksss
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Divider,
  Box,
  Paper,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText
} from '@mui/material';

import { BackupRecord, BackupStatus, BackupType } from '../../types/backup';
import { formatDateTime, formatFileSize } from '../../utils/formatters';

interface BackupDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  backup: BackupRecord;
}

const BackupDetailsDialog: React.FC<BackupDetailsDialogProps> = ({
  open,
  onClose,
  backup
}) => {
  // Get formatted metadata
  const formatMetadata = (metadata: Record<string, any> | undefined) => {
    if (!metadata) return [];
    
    return Object.entries(metadata).map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value)
    }));
  };
  
  const metadataItems = formatMetadata(backup.metadata);
  
  // Get backup status color
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
  
  // Get backup type color
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
  
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        Backup Details
      </DialogTitle>
      <DialogContent>
        <Box sx={{ p: 1 }}>
          <Typography variant="h6" gutterBottom>
            {backup.description}
          </Typography>
          
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Backup ID
              </Typography>
              <Typography variant="body1">
                {backup.backup_id}
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Created At
              </Typography>
              <Typography variant="body1">
                {formatDateTime(backup.created_at)}
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Type
              </Typography>
              <Chip 
                label={backup.backup_type} 
                size="small" 
                color={getTypeColor(backup.backup_type)}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Status
              </Typography>
              <Chip 
                label={backup.status} 
                size="small" 
                color={getStatusColor(backup.status)}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Size
              </Typography>
              <Typography variant="body1">
                {formatFileSize(backup.size_bytes)}
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Storage Type
              </Typography>
              <Typography variant="body1">
                {backup.storage_type}
              </Typography>
            </Grid>
          </Grid>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Metadata
          </Typography>
          
          {metadataItems.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No metadata available
            </Typography>
          ) : (
            <Paper variant="outlined" sx={{ mt: 1 }}>
              <List dense>
                {metadataItems.map((item, index) => (
                  <ListItem key={index} divider={index < metadataItems.length - 1}>
                    <Grid container>
                      <Grid item xs={4} md={3}>
                        <ListItemText 
                          primary={item.key}
                          primaryTypographyProps={{ 
                            variant: 'body2',
                            color: 'text.secondary',
                            fontWeight: 'medium'
                          }}
                        />
                      </Grid>
                      <Grid item xs={8} md={9}>
                        <ListItemText 
                          primary={item.value}
                          primaryTypographyProps={{ 
                            variant: 'body2',
                            sx: { wordBreak: 'break-all' }
                          }}
                        />
                      </Grid>
                    </Grid>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
          
          {backup.storage_path && (
            <>
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                Storage Information
              </Typography>
              
              <Paper variant="outlined" sx={{ mt: 1, p: 2 }}>
                <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                  {backup.storage_path}
                </Typography>
              </Paper>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default BackupDetailsDialog;

// Son güncelleme: 2025-05-21 05:21:55
// Güncelleyen: Teeksss