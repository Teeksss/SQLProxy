import React, { useState } from 'react';
import styled from 'styled-components';
import {
  UserList,
  UserForm,
  RoleManager,
  PermissionMatrix
} from './components';
import { useUsers } from '../../../../hooks/useUsers';

const UserManagementContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

export const UserManagement: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState(null);
  const {
    users,
    roles,
    permissions,
    createUser,
    updateUser,
    deleteUser,
    updateRole,
    updatePermissions
  } = useUsers();
  
  return (
    <UserManagementContainer>
      <h2>User Management</h2>
      
      <UserList
        users={users}
        onSelect={setSelectedUser}
        onDelete={deleteUser}
      />
      
      {selectedUser ? (
        <UserForm
          user={selectedUser}
          roles={roles}
          onSubmit={updateUser}
        />
      ) : (
        <UserForm
          roles={roles}
          onSubmit={createUser}
        />
      )}
      
      <RoleManager
        roles={roles}
        onUpdate={updateRole}
      />
      
      <PermissionMatrix
        permissions={permissions}
        roles={roles}
        onUpdate={updatePermissions}
      />
    </UserManagementContainer>
  );
};