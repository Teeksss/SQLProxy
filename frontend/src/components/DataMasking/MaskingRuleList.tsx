/**
 * Masking Rules List Component
 * 
 * Displays and manages data masking rules
 * 
 * Last updated: 2025-05-20 14:44:45
 * Updated by: Teeksss
 */

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  CircularProgress,
  Divider,
  Alert
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { toast } from 'react-toastify';

import { maskingApi } from '../../services/maskingService';
import { MaskingRule, MaskingRuleType } from '../../types/masking';
import MaskingRuleForm from './MaskingRuleForm';
import MaskingRuleTestDialog from './MaskingRuleTestDialog';
import { useAuth } from '../../contexts/AuthContext';
import NoDataPlaceholder from '../common/NoDataPlaceholder';
import ConfirmationDialog from '../common/ConfirmationDialog';

interface MaskingRuleListProps {
  onRefresh?: () => void;
}

const MaskingRuleList: React.FC<MaskingRuleListProps> = ({ onRefresh }) => {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<MaskingRule | null>(null);
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  // Query for fetching masking rules
  const { 
    data: rulesData, 
    isLoading, 
    error,
    refetch 
  } = useQuery(
    ['maskingRules'], 
    maskingApi.getMaskingRules,
    {
      enabled: !!user,
      onError: (err: any) => {
        toast.error(`Error loading masking rules: ${err.message}`);
      }
    }
  );
  
  // Mutations for CRUD operations
  const createMutation = useMutation(
    (rule: Partial<MaskingRule>) => maskingApi.createMaskingRule(rule),
    {
      onSuccess: () => {
        toast.success('Masking rule created successfully');
        queryClient.invalidateQueries(['maskingRules']);
        setCreateDialogOpen(false);
        if (onRefresh) onRefresh();
      },
      onError: (err: any) => {
        toast.error(`Error creating masking rule: ${err.message}`);
      }
    }
  );
  
  const updateMutation = useMutation(
    (data: { id: number; rule: Partial<MaskingRule> }) => 
      maskingApi.updateMaskingRule(data.id, data.rule),
    {
      onSuccess: () => {
        toast.success('Masking rule updated successfully');
        queryClient.invalidateQueries(['maskingRules']);
        setEditDialogOpen(false);
        if (onRefresh) onRefresh();
      },
      onError: (err: any) => {
        toast.error(`Error updating masking rule: ${err.message}`);
      }
    }
  );
  
  const deleteMutation = useMutation(
    (id: number) => maskingApi.deleteMaskingRule(id),
    {
      onSuccess: () => {
        toast.success('Masking rule deleted successfully');
        queryClient.invalidateQueries(['maskingRules']);
        setDeleteDialogOpen(false);
        if (onRefresh) onRefresh();
      },
      onError: (err: any) => {
        toast.error(`Error deleting masking rule: ${err.message}`);
      }
    }
  );
  
  const toggleStatusMutation = useMutation(
    (data: { id: number; enabled: boolean }) => 
      maskingApi.updateMaskingRule(data.id, { enabled: data.enabled }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['maskingRules']);
        if (onRefresh) onRefresh();
      },
      onError: (err: any) => {
        toast.error(`Error updating rule status: ${err.message}`);
      }
    }
  );
  
  // Handle create rule
  const handleCreateRule = (rule: Partial<MaskingRule>) => {
    createMutation.mutate(rule);
  };
  
  // Handle edit rule
  const handleEditRule = (rule: Partial<MaskingRule>) => {
    if (!selectedRule) return;
    
    updateMutation.mutate({
      id: selectedRule.id,
      rule
    });
  };
  
  // Handle delete rule
  const handleDeleteRule = () => {
    if (!selectedRule) return;
    
    deleteMutation.mutate(selectedRule.id);
  };
  
  // Handle toggle rule status
  const handleToggleStatus = (rule: MaskingRule, enabled: boolean) => {
    toggleStatusMutation.mutate({
      id: rule.id,
      enabled
    });
  };
  
  // Open edit dialog
  const openEditDialog = (rule: MaskingRule) => {
    setSelectedRule(rule);
    setEditDialogOpen(true);
  };
  
  // Open test dialog
  const openTestDialog = (rule: MaskingRule) => {
    setSelectedRule(rule);
    setTestDialogOpen(true);
  };
  
  // Open delete dialog
  const openDeleteDialog = (rule: MaskingRule) => {
    setSelectedRule(rule);
    setDeleteDialogOpen(true);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Error loading masking rules. Please try again.
      </Alert>
    );
  }

  const globalRules = rulesData?.global_rules || [];
  const columnRules = rulesData?.column_rules || [];
  
  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Data Masking Rules</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Rule
        </Button>
      </Box>
      
      {/* Global Rules */}
      <Typography variant="subtitle1" sx={{ mt: 3, mb: 1 }}>
        Global Pattern Rules
        <Tooltip title="Global rules apply pattern matching to detect and mask sensitive data">
          <span> (Pattern-based detection)</span>
        </Tooltip>
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Pattern</TableCell>
              <TableCell>Masking Method</TableCell>
              <TableCell>Status</TableCell>
              <TableCell width="120">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {globalRules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5}>
                  <NoDataPlaceholder message="No global masking rules defined" />
                </TableCell>
              </TableRow>
            ) : (
              globalRules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell>{rule.name}</TableCell>
                  <TableCell>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        maxWidth: 250, 
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {rule.pattern}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={rule.type}
                      size="small"
                      color={
                        rule.type === 'redact' ? 'error' :
                        rule.type === 'hash' ? 'primary' :
                        rule.type === 'partial' ? 'warning' :
                        'default'
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Switch
                      size="small"
                      checked={rule.enabled}
                      onChange={(e) => handleToggleStatus(rule, e.target.checked)}
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Edit">
                      <IconButton 
                        size="small" 
                        onClick={() => openEditDialog(rule)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Test">
                      <IconButton 
                        size="small" 
                        onClick={() => openTestDialog(rule)}
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton 
                        size="small" 
                        onClick={() => openDeleteDialog(rule)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Column Rules */}
      <Typography variant="subtitle1" sx={{ mt: 3, mb: 1 }}>
        Column Rules
        <Tooltip title="Column rules apply masking to specific database columns">
          <span> (Column-specific masking)</span>
        </Tooltip>
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Column</TableCell>
              <TableCell>Masking Method</TableCell>
              <TableCell>Status</TableCell>
              <TableCell width="120">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {columnRules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5}>
                  <NoDataPlaceholder message="No column masking rules defined" />
                </TableCell>
              </TableRow>
            ) : (
              columnRules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell>{rule.name}</TableCell>
                  <TableCell>{rule.column_name}</TableCell>
                  <TableCell>
                    <Chip
                      label={rule.type}
                      size="small"
                      color={
                        rule.type === 'redact' ? 'error' :
                        rule.type === 'hash' ? 'primary' :
                        rule.type === 'partial' ? 'warning' :
                        'default'
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Switch
                      size="small"
                      checked={rule.enabled}
                      onChange={(e) => handleToggleStatus(rule, e.target.checked)}
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Edit">
                      <IconButton 
                        size="small" 
                        onClick={() => openEditDialog(rule)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Test">
                      <IconButton 
                        size="small" 
                        onClick={() => openTestDialog(rule)}
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton 
                        size="small" 
                        onClick={() => openDeleteDialog(rule)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Create Rule Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create Masking Rule</DialogTitle>
        <DialogContent>
          <MaskingRuleForm 
            onSubmit={handleCreateRule} 
            isSubmitting={createMutation.isLoading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            form="masking-rule-form" 
            type="submit" 
            variant="contained" 
            disabled={createMutation.isLoading}
          >
            {createMutation.isLoading ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Edit Rule Dialog */}
      <Dialog 
        open={editDialogOpen} 
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Masking Rule</DialogTitle>
        <DialogContent>
          {selectedRule && (
            <MaskingRuleForm 
              initialData={selectedRule}
              onSubmit={handleEditRule} 
              isSubmitting={updateMutation.isLoading}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button 
            form="masking-rule-form" 
            type="submit" 
            variant="contained" 
            disabled={updateMutation.isLoading}
          >
            {updateMutation.isLoading ? <CircularProgress size={24} /> : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Test Rule Dialog */}
      <MaskingRuleTestDialog
        open={testDialogOpen}
        onClose={() => setTestDialogOpen(false)}
        rule={selectedRule}
      />
      
      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteRule}
        title="Delete Masking Rule"
        content={`Are you sure you want to delete the masking rule "${selectedRule?.name}"? This action cannot be undone.`}
        confirmButtonText="Delete"
        isSubmitting={deleteMutation.isLoading}
      />
    </Box>
  );
};

export default MaskingRuleList;

// Son güncelleme: 2025-05-20 14:44:45
// Güncelleyen: Teeksss