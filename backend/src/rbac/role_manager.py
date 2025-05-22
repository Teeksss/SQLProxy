from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from .models import Role, Permission, RoleAssignment
from .policy_engine import PolicyEngine
from .audit_logger import AuditLogger

class RoleManager:
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.audit = AuditLogger()
        
    async def create_role(self, role_data: Dict) -> Role:
        """Yeni rol oluşturur."""
        try:
            # Validate role data
            self._validate_role_data(role_data)
            
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                permissions=role_data['permissions'],
                scope=role_data['scope'],
                created_by=role_data['created_by'],
                created_at=datetime.utcnow()
            )
            
            # Policy kontrolü
            await self.policy_engine.validate_role_creation(role)
            
            # Role kaydet
            await role.save()
            
            # Audit log
            await self.audit.log_role_creation(role)
            
            return role
            
        except Exception as e:
            await self.audit.log_error('role_creation', str(e))
            raise
            
    async def assign_role(self, assignment: Dict) -> RoleAssignment:
        """Rol ataması yapar."""
        try:
            # Validate assignment
            self._validate_assignment(assignment)
            
            role_assignment = RoleAssignment(
                user_id=assignment['user_id'],
                role_id=assignment['role_id'],
                assigned_by=assignment['assigned_by'],
                expires_at=assignment.get('expires_at'),
                conditions=assignment.get('conditions', {})
            )
            
            # Policy kontrolü
            await self.policy_engine.validate_role_assignment(
                role_assignment
            )
            
            # Assignment kaydet
            await role_assignment.save()
            
            # Audit log
            await self.audit.log_role_assignment(role_assignment)
            
            return role_assignment
            
        except Exception as e:
            await self.audit.log_error('role_assignment', str(e))
            raise
            
    async def check_permission(self, context: Dict) -> bool:
        """Permission kontrolü yapar."""
        try:
            user_id = context['user_id']
            action = context['action']
            resource = context['resource']
            
            # Get user roles
            roles = await self._get_user_roles(user_id)
            
            # Get effective permissions
            permissions = await self._get_effective_permissions(roles)
            
            # Check conditions
            conditions_met = await self._check_conditions(
                permissions, context
            )
            
            # Check specific permissions
            has_permission = any(
                self._match_permission(p, action, resource)
                for p in permissions
                if conditions_met[p.id]
            )
            
            # Audit log
            await self.audit.log_permission_check(
                context, has_permission
            )
            
            return has_permission
            
        except Exception as e:
            await self.audit.log_error('permission_check', str(e))
            return False