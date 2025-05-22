import React, { useState } from 'react';
import styled from 'styled-components';
import {
  RoleList,
  RoleEditor,
  PermissionMatrix,
  AssignmentManager
} from './components';
import { useRoleManager } from '../../hooks/useRoleManager';

const ManagerContainer = styled.div`
  display: grid;
  gap: 2rem;
`;

const EditorGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 1.5rem;
`;

export const RoleManager: React.FC = () => {
  const [selectedRole, setSelectedRole] = useState(null);
  
  const {
    roles,
    permissions,
    assignments,
    createRole,
    updateRole,
    deleteRole,
    assignRole,
    revokeRole
  } = useRoleManager();
  
  return (
    <ManagerContainer>
      <h2>Role Management</h2>
      
      <EditorGrid>
        <div>
          <RoleList
            roles={roles}
            onSelect={setSelectedRole}
            onDelete={deleteRole}
          />
          
          <AssignmentManager
            assignments={assignments}
            roles={roles}
            onAssign={assignRole}
            onRevoke={revokeRole}
          />
        </div>
        
        <div>
          {selectedRole ? (
            <RoleEditor
              role={selectedRole}
              onSave={updateRole}
            />
          ) : (
            <RoleEditor
              onSave={createRole}
            />
          )}
          
          <PermissionMatrix
            role={selectedRole}
            permissions={permissions}
            onChange={(perms) => updateRole({
              ...selectedRole,
              permissions: perms
            })}
          />
        </div>
      </EditorGrid>
    </ManagerContainer>
  );
};