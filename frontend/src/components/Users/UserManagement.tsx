/**
 * User Management Component
 * 
 * Interface for managing users, roles, and permissions
 * 
 * Last updated: 2025-05-21 07:03:15
 * Updated by: Teeksss
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  CircularProgress,
  Alert,
  Tooltip,
  Tabs,
  Tab,
  Divider,
  TablePagination,
  InputAdornment
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import PersonIcon from '@mui/icons-material/Person';
import KeyIcon from '@mui/icons-material/Key';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SearchIcon from '@mui/icons-material/Search';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { toast } from 'react-toastify';

import { userApi } from '../../services/userService';
import ConfirmationDialog from '../common/ConfirmationDialog';

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
      id={`users-tabpanel-${index}`}
      aria-labelledby={`users-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
};

const UserManagement: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showResetPasswordDialog, setShowResetPasswordDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  
  const queryClient = useQueryClient();

  // Query for fetching users
  const {
    data: usersData,
    isLoading: isLoadingUsers,
    error: usersError,
    refetch: refetchUsers
  } = useQuery(
    ['users'],
    userApi.getUsers,
    {
      staleTime: 60000 // 1 minute
    }
  );

  // Query for fetching roles
  const {
    data: rolesData,
    isLoading: isLoadingRoles
  } = useQuery(
    ['roles'],
    userApi.getRoles,
    {
      staleTime: 300000 // 5 minutes
    }
  );

  // Mutation for creating a user
  const createUserMutation = useMutation(
    (userData: any) => userApi.createUser(userData),
    {
      onSuccess: () => {
        toast.success('User created successfully');
        queryClient.invalidateQueries(['users']);
        setShowCreateDialog(false);
      }
    }
  );

  // Mutation for updating a user
  const updateUserMutation = useMutation(
    (userData: any) => userApi.updateUser(userData.id, userData),
    {
      onSuccess: () => {
        toast.success('User updated successfully');
        queryClient.invalidateQueries(['users']);
        setShowEditDialog(false);
      }
    }
  );

  // Mutation for deleting a user
  const deleteUserMutation = useMutation(
    (userId: number) => userApi.deleteUser(userId),
    {
      onSuccess: () => {
        toast.success('User deleted successfully');
        queryClient.invalidateQueries(['users']);
        setShowDeleteDialog(false);
      }
    }
  );

  // Mutation for resetting a user's password
  const resetPasswordMutation = useMutation(
    (data: any) => userApi.resetPassword(data.userId, data.password),
    {
      onSuccess: () => {
        toast.success('Password reset successfully');
        setShowResetPasswordDialog(false);
      }
    }
  );

  // Formik for create/edit user form
  const userFormik = useFormik({
    initialValues: {
      username: '',
      email: '',
      full_name: '',
      password: '',
      is_active: true,
      is_admin: false,
      role_ids: []
    },
    validationSchema: Yup.object({
      username: Yup.string().required('Username is required'),
      email: Yup.string().email('Invalid email address').required('Email is required'),
      full_name: Yup.string(),
      password: Yup.string().when('_action', {
        is: 'create',
        then: Yup.string().required('Password is required').min(8, 'Password must be at least 8 characters')
      }),
      is_active: Yup.boolean(),
      is_admin: Yup.boolean(),
      role_ids: Yup.array()
    }),
    onSubmit: (values) => {
      if (selectedUser) {
        // Update existing user
        updateUserMutation.mutate({
          id: selectedUser.id,
          ...values,
          password: values.password || undefined // Don't send empty password
        });
      } else {
        // Create new user
        createUserMutation.mutate(values);
      }
    }
  });

  // Formik for reset password form
  const resetPasswordFormik = useFormik({
    initialValues: {
      userId: 0,
      password: '',
      confirmPassword: ''
    },
    validationSchema: Yup.object({
      password: Yup.string().required('Password is required').min(8, 'Password must be at least 8 characters'),
      confirmPassword: Yup.string()
        .required('Confirm password is required')
        .oneOf([Yup.ref('password')], 'Passwords must match')
    }),
    onSubmit: (values) => {
      resetPasswordMutation.mutate({
        userId: values.userId,
        password: values.password
      });
    }
  });

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  // Handle search change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0); // Reset to first page on search
  };

  // Handle page change
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Handle create user dialog
  const handleOpenCreateDialog = () => {
    userFormik.resetForm();
    userFormik.setFieldValue('_action', 'create');
    setSelectedUser(null);
    setShowCreateDialog(true);
  };

  // Handle edit user dialog
  const handleOpenEditDialog = (user: any) => {
    setSelectedUser(user);
    userFormik.resetForm();
    userFormik.setValues({
      username: user.username,
      email: user.email,
      full_name: user.full_name || '',
      password: '',
      is_active: user.is_active,
      is_admin: user.is_admin,
      role_ids: user.roles?.map((role: any) => role.id) || [],
      _action: 'edit'
    });
    setShowEditDialog(true);
  };

  // Handle delete user dialog
  const handleOpenDeleteDialog = (user: any) => {
    setSelectedUser(user);
    setShowDeleteDialog(true);
  };

  // Handle reset password dialog
  const handleOpenResetPasswordDialog = (user: any) => {
    setSelectedUser(user);
    resetPasswordFormik.resetForm();
    resetPasswordFormik.setValues({
      userId: user.id,
      password: '',
      confirmPassword: ''
    });
    setShowResetPasswordDialog(true);
  };

  // Filter users by search term
  const filteredUsers = usersData?.filter((user: any) => {
    if (!searchTerm) return true;
    
    const search = searchTerm.toLowerCase();
    return (
      user.username.toLowerCase().includes(search) ||
      user.email.toLowerCase().includes(search) ||
      (user.full_name && user.full_name.toLowerCase().includes(search))
    );
  }) || [];

  // Paginate users
  const paginatedUsers = filteredUsers.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Loading state
  if (isLoadingUsers) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (usersError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error loading users: {(usersError as Error).message}
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabIndex} onChange={handleTabChange} aria-label="user management tabs">
          <Tab label="Users" id="users-tab-0" />
          <Tab label="Roles" id="users-tab-1" />
          <Tab label="Permissions" id="users-tab-2" />
        </Tabs>
      </Box>
      
      <TabPanel value={tabIndex} index={0}>
        {/* Users Tab */}
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
          <TextField
            placeholder="Search users..."
            value={searchTerm}
            onChange={handleSearchChange}
            variant="outlined"
            size="small"
            sx={{ width: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenCreateDialog}
          >
            Create User
          </Button>
        </Box>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Username</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Full Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Roles</TableCell>
                <TableCell width={150}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedUsers.map((user: any) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {user.is_admin ? <AdminPanelSettingsIcon color="primary" sx={{ mr: 1 }} /> : <PersonIcon sx={{ mr: 1 }} />}
                      {user.username}
                    </Box>
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.full_name || '-'}</TableCell>
                  <TableCell>
                    {user.is_active ? (
                      <Chip 
                        icon={<CheckCircleIcon />} 
                        label="Active" 
                        color="success" 
                        size="small" 
                        variant="outlined" 
                      />
                    ) : (
                      <Chip 
                        icon={<BlockIcon />} 
                        label="Inactive" 
                        color="error" 
                        size="small" 
                        variant="outlined" 
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {user.is_admin && (
                        <Chip label="Admin" color="primary" size="small" />
                      )}
                      {user.roles?.map((role: any) => (
                        <Chip key={role.id} label={role.name} size="small" />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Edit User">
                      <IconButton size="small" onClick={() => handleOpenEditDialog(user)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Reset Password">
                      <IconButton size="small" onClick={() => handleOpenResetPasswordDialog(user)}>
                        <KeyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Delete User">
                      <IconButton 
                        size="small" 
                        color="error" 
                        onClick={() => handleOpenDeleteDialog(user)}
                        disabled={user.is_admin} // Prevent deleting admin users
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              
              {filteredUsers.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    No users found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          
          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={filteredUsers.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>
      </TabPanel>
      
      <TabPanel value={tabIndex} index={1}>
        {/* Roles Tab */}
        <RolesPanel roles={rolesData} isLoading={isLoadingRoles} />
      </TabPanel>
      
      <TabPanel value={tabIndex} index={2}>
        {/* Permissions Tab */}
        <PermissionsPanel />
      </TabPanel>
      
      {/* Create User Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={userFormik.handleSubmit}>
          <DialogTitle>Create User</DialogTitle>
          <DialogContent dividers>
            <TextField
              fullWidth
              id="username"
              name="username"
              label="Username"
              value={userFormik.values.username}
              onChange={userFormik.handleChange}
              error={userFormik.touched.username && Boolean(userFormik.errors.username)}
              helperText={userFormik.touched.username && userFormik.errors.username}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="email"
              name="email"
              label="Email"
              type="email"
              value={userFormik.values.email}
              onChange={userFormik.handleChange}
              error={userFormik.touched.email && Boolean(userFormik.errors.email)}
              helperText={userFormik.touched.email && userFormik.errors.email}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="full_name"
              name="full_name"
              label="Full Name"
              value={userFormik.values.full_name}
              onChange={userFormik.handleChange}
              error={userFormik.touched.full_name && Boolean(userFormik.errors.full_name)}
              helperText={userFormik.touched.full_name && userFormik.errors.full_name}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="password"
              name="password"
              label="Password"
              type="password"
              value={userFormik.values.password}
              onChange={userFormik.handleChange}
              error={userFormik.touched.password && Boolean(userFormik.errors.password)}
              helperText={userFormik.touched.password && userFormik.errors.password}
              margin="normal"
            />
            
            <Box sx={{ mt: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    id="is_active"
                    name="is_active"
                    checked={userFormik.values.is_active}
                    onChange={userFormik.handleChange}
                  />
                }
                label="Active"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    id="is_admin"
                    name="is_admin"
                    checked={userFormik.values.is_admin}
                    onChange={userFormik.handleChange}
                  />
                }
                label="Admin"
              />
            </Box>
            
            <FormControl fullWidth margin="normal">
              <InputLabel id="roles-label">Roles</InputLabel>
              <Select
                labelId="roles-label"
                id="role_ids"
                name="role_ids"
                multiple
                value={userFormik.values.role_ids}
                onChange={userFormik.handleChange}
                label="Roles"
              >
                {isLoadingRoles ? (
                  <MenuItem disabled>Loading roles...</MenuItem>
                ) : (
                  rolesData?.map((role: any) => (
                    <MenuItem key={role.id} value={role.id}>
                      {role.name}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={createUserMutation.isLoading}
            >
              {createUserMutation.isLoading ? <CircularProgress size={24} /> : 'Create'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Edit User Dialog */}
      <Dialog
        open={showEditDialog}
        onClose={() => setShowEditDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={userFormik.handleSubmit}>
          <DialogTitle>Edit User: {selectedUser?.username}</DialogTitle>
          <DialogContent dividers>
            <TextField
              fullWidth
              id="username"
              name="username"
              label="Username"
              value={userFormik.values.username}
              onChange={userFormik.handleChange}
              error={userFormik.touched.username && Boolean(userFormik.errors.username)}
              helperText={userFormik.touched.username && userFormik.errors.username}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="email"
              name="email"
              label="Email"
              type="email"
              value={userFormik.values.email}
              onChange={userFormik.handleChange}
              error={userFormik.touched.email && Boolean(userFormik.errors.email)}
              helperText={userFormik.touched.email && userFormik.errors.email}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="full_name"
              name="full_name"
              label="Full Name"
              value={userFormik.values.full_name}
              onChange={userFormik.handleChange}
              error={userFormik.touched.full_name && Boolean(userFormik.errors.full_name)}
              helperText={userFormik.touched.full_name && userFormik.errors.full_name}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="password"
              name="password"
              label="New Password (leave empty to keep current)"
              type="password"
              value={userFormik.values.password}
              onChange={userFormik.handleChange}
              error={userFormik.touched.password && Boolean(userFormik.errors.password)}
              helperText={userFormik.touched.password && userFormik.errors.password}
              margin="normal"
            />
            
            <Box sx={{ mt: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    id="is_active"
                    name="is_active"
                    checked={userFormik.values.is_active}
                    onChange={userFormik.handleChange}
                  />
                }
                label="Active"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    id="is_admin"
                    name="is_admin"
                    checked={userFormik.values.is_admin}
                    onChange={userFormik.handleChange}
                  />
                }
                label="Admin"
              />
            </Box>
            
            <FormControl fullWidth margin="normal">
              <InputLabel id="roles-edit-label">Roles</InputLabel>
              <Select
                labelId="roles-edit-label"
                id="role_ids"
                name="role_ids"
                multiple
                value={userFormik.values.role_ids}
                onChange={userFormik.handleChange}
                label="Roles"
              >
                {isLoadingRoles ? (
                  <MenuItem disabled>Loading roles...</MenuItem>
                ) : (
                  rolesData?.map((role: any) => (
                    <MenuItem key={role.id} value={role.id}>
                      {role.name}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={updateUserMutation.isLoading}
            >
              {updateUserMutation.isLoading ? <CircularProgress size={24} /> : 'Save Changes'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Reset Password Dialog */}
      <Dialog
        open={showResetPasswordDialog}
        onClose={() => setShowResetPasswordDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={resetPasswordFormik.handleSubmit}>
          <DialogTitle>Reset Password: {selectedUser?.username}</DialogTitle>
          <DialogContent dividers>
            <Alert severity="info" sx={{ mb: 2 }}>
              Enter a new password for user {selectedUser?.username}.
            </Alert>
            
            <TextField
              fullWidth
              id="password"
              name="password"
              label="New Password"
              type="password"
              value={resetPasswordFormik.values.password}
              onChange={resetPasswordFormik.handleChange}
              error={resetPasswordFormik.touched.password && Boolean(resetPasswordFormik.errors.password)}
              helperText={resetPasswordFormik.touched.password && resetPasswordFormik.errors.password}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="confirmPassword"
              name="confirmPassword"
              label="Confirm Password"
              type="password"
              value={resetPasswordFormik.values.confirmPassword}
              onChange={resetPasswordFormik.handleChange}
              error={resetPasswordFormik.touched.confirmPassword && Boolean(resetPasswordFormik.errors.confirmPassword)}
              helperText={resetPasswordFormik.touched.confirmPassword && resetPasswordFormik.errors.confirmPassword}
              margin="normal"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowResetPasswordDialog(false)}>Cancel</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={resetPasswordMutation.isLoading}
            >
              {resetPasswordMutation.isLoading ? <CircularProgress size={24} /> : 'Reset Password'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Delete User Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={() => deleteUserMutation.mutate(selectedUser?.id)}
        title="Delete User"
        content={`Are you sure you want to delete the user "${selectedUser?.username}"? This action cannot be undone.`}
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isLoading={deleteUserMutation.isLoading}
      />
    </Box>
  );
};

// Roles Panel Component
const RolesPanel: React.FC<{ roles: any[], isLoading: boolean }> = ({ roles, isLoading }) => {
  const [showCreateRoleDialog, setShowCreateRoleDialog] = useState(false);
  const [showEditRoleDialog, setShowEditRoleDialog] = useState(false);
  const [showDeleteRoleDialog, setShowDeleteRoleDialog] = useState(false);
  const [selectedRole, setSelectedRole] = useState<any>(null);
  
  const queryClient = useQueryClient();

  // Mutation for creating a role
  const createRoleMutation = useMutation(
    (roleData: any) => userApi.createRole(roleData),
    {
      onSuccess: () => {
        toast.success('Role created successfully');
        queryClient.invalidateQueries(['roles']);
        setShowCreateRoleDialog(false);
      }
    }
  );

  // Mutation for updating a role
  const updateRoleMutation = useMutation(
    (roleData: any) => userApi.updateRole(roleData.id, roleData),
    {
      onSuccess: () => {
        toast.success('Role updated successfully');
        queryClient.invalidateQueries(['roles']);
        setShowEditRoleDialog(false);
      }
    }
  );

  // Mutation for deleting a role
  const deleteRoleMutation = useMutation(
    (roleId: number) => userApi.deleteRole(roleId),
    {
      onSuccess: () => {
        toast.success('Role deleted successfully');
        queryClient.invalidateQueries(['roles']);
        setShowDeleteRoleDialog(false);
      }
    }
  );

  // Formik for role form
  const roleFormik = useFormik({
    initialValues: {
      name: '',
      description: '',
      permission_ids: []
    },
    validationSchema: Yup.object({
      name: Yup.string().required('Role name is required'),
      description: Yup.string(),
      permission_ids: Yup.array()
    }),
    onSubmit: (values) => {
      if (selectedRole) {
        // Update existing role
        updateRoleMutation.mutate({
          id: selectedRole.id,
          ...values
        });
      } else {
        // Create new role
        createRoleMutation.mutate(values);
      }
    }
  });

  // Handle create role dialog
  const handleOpenCreateRoleDialog = () => {
    roleFormik.resetForm();
    setSelectedRole(null);
    setShowCreateRoleDialog(true);
  };

  // Handle edit role dialog
  const handleOpenEditRoleDialog = (role: any) => {
    setSelectedRole(role);
    roleFormik.resetForm();
    roleFormik.setValues({
      name: role.name,
      description: role.description || '',
      permission_ids: role.permissions?.map((permission: any) => permission.id) || []
    });
    setShowEditRoleDialog(true);
  };

  // Handle delete role dialog
  const handleOpenDeleteRoleDialog = (role: any) => {
    setSelectedRole(role);
    setShowDeleteRoleDialog(true);
  };

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="h6">Role Management</Typography>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreateRoleDialog}
        >
          Create Role
        </Button>
      </Box>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Permissions</TableCell>
              <TableCell width={120}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {roles?.map((role: any) => (
              <TableRow key={role.id}>
                <TableCell>{role.name}</TableCell>
                <TableCell>{role.description || '-'}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {role.permissions?.slice(0, 3).map((permission: any) => (
                      <Chip key={permission.id} label={permission.name} size="small" />
                    ))}
                    {role.permissions?.length > 3 && (
                      <Chip label={`+${role.permissions.length - 3} more`} size="small" />
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Tooltip title="Edit Role">
                    <IconButton size="small" onClick={() => handleOpenEditRoleDialog(role)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Delete Role">
                    <IconButton 
                      size="small" 
                      color="error" 
                      onClick={() => handleOpenDeleteRoleDialog(role)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            
            {!roles?.length && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  No roles found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Create Role Dialog */}
      <Dialog
        open={showCreateRoleDialog}
        onClose={() => setShowCreateRoleDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={roleFormik.handleSubmit}>
          <DialogTitle>Create Role</DialogTitle>
          <DialogContent dividers>
            <TextField
              fullWidth
              id="name"
              name="name"
              label="Role Name"
              value={roleFormik.values.name}
              onChange={roleFormik.handleChange}
              error={roleFormik.touched.name && Boolean(roleFormik.errors.name)}
              helperText={roleFormik.touched.name && roleFormik.errors.name}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="description"
              name="description"
              label="Description"
              value={roleFormik.values.description}
              onChange={roleFormik.handleChange}
              error={roleFormik.touched.description && Boolean(roleFormik.errors.description)}
              helperText={roleFormik.touched.description && roleFormik.errors.description}
              margin="normal"
              multiline
              rows={2}
            />
            
            {/* Permission selection would go here */}
            {/* This requires fetching available permissions first */}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowCreateRoleDialog(false)}>Cancel</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={createRoleMutation.isLoading}
            >
              {createRoleMutation.isLoading ? <CircularProgress size={24} /> : 'Create Role'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Edit Role Dialog */}
      <Dialog
        open={showEditRoleDialog}
        onClose={() => setShowEditRoleDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <form onSubmit={roleFormik.handleSubmit}>
          <DialogTitle>Edit Role: {selectedRole?.name}</DialogTitle>
          <DialogContent dividers>
            <TextField
              fullWidth
              id="name"
              name="name"
              label="Role Name"
              value={roleFormik.values.name}
              onChange={roleFormik.handleChange}
              error={roleFormik.touched.name && Boolean(roleFormik.errors.name)}
              helperText={roleFormik.touched.name && roleFormik.errors.name}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="description"
              name="description"
              label="Description"
              value={roleFormik.values.description}
              onChange={roleFormik.handleChange}
              error={roleFormik.touched.description && Boolean(roleFormik.errors.description)}
              helperText={roleFormik.touched.description && roleFormik.errors.description}
              margin="normal"
              multiline
              rows={2}
            />
            
            {/* Permission selection would go here */}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowEditRoleDialog(false)}>Cancel</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={updateRoleMutation.isLoading}
            >
              {updateRoleMutation.isLoading ? <CircularProgress size={24} /> : 'Save Changes'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      
      {/* Delete Role Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteRoleDialog}
        onClose={() => setShowDeleteRoleDialog(false)}
        onConfirm={() => deleteRoleMutation.mutate(selectedRole?.id)}
        title="Delete Role"
        content={`Are you sure you want to delete the role "${selectedRole?.name}"? This action cannot be undone.`}
        confirmButtonText="Delete"
        confirmButtonColor="error"
        isLoading={deleteRoleMutation.isLoading}
      />
    </Box>
  );
};

// Permissions Panel Component
const PermissionsPanel: React.FC = () => {
  // For the sake of this component, we'll just show a placeholder
  // A complete implementation would need API endpoints to manage permissions
  
  return (
    <Box>
      <Alert severity="info" sx={{ mb: 3 }}>
        This section allows you to manage system permissions that can be assigned to roles.
      </Alert>
      
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          System Permissions
        </Typography>
        
        <Typography variant="body2" paragraph>
          Permissions define granular access control for system features. Assign permissions to roles, and then assign roles to users.
        </Typography>
        
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Available Permission Categories:
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            <Chip label="User Management" color="primary" />
            <Chip label="Server Management" color="primary" />
            <Chip label="Query Execution" color="primary" />
            <Chip label="PowerBI Integration" color="primary" />
            <Chip label="System Configuration" color="primary" />
            <Chip label="Report Viewing" color="primary" />
            <Chip label="Data Export" color="primary" />
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default UserManagement;

// Son güncelleme: 2025-05-21 07:03:15
// Güncelleyen: Teeksss