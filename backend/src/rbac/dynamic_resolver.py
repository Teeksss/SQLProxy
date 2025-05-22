from typing import Dict, List
from datetime import datetime
import asyncio
from .cache_manager import CacheManager
from .context_builder import ContextBuilder

class DynamicRoleResolver:
    def __init__(self):
        self.cache = CacheManager()
        self.context_builder = ContextBuilder()
        
    async def resolve_roles(self, user_id: str,
                          request_context: Dict) -> List[Dict]:
        """Dinamik rol çözümlemesi yapar."""
        # Build context
        context = await self.context_builder.build_context(
            user_id, request_context
        )
        
        # Get base roles
        base_roles = await self._get_base_roles(user_id)
        
        # Apply dynamic rules
        dynamic_roles = await self._apply_dynamic_rules(
            base_roles, context
        )
        
        # Resolve effective permissions
        effective_permissions = await self._resolve_permissions(
            dynamic_roles, context
        )
        
        return {
            'roles': dynamic_roles,
            'permissions': effective_permissions,
            'context': context,
            'resolution_time': datetime.utcnow()
        }
        
    async def _apply_dynamic_rules(self, roles: List[Dict],
                                 context: Dict) -> List[Dict]:
        """Dinamik rol kurallarını uygular."""
        dynamic_roles = []
        
        for role in roles:
            # Check dynamic conditions
            if await self._evaluate_role_conditions(role, context):
                # Apply dynamic attributes
                dynamic_role = await self._enhance_role(role, context)
                dynamic_roles.append(dynamic_role)
                
                # Check for dynamic child roles
                if child_roles := await self._get_dynamic_child_roles(
                    role, context
                ):
                    dynamic_roles.extend(child_roles)
                    
        return dynamic_roles
        
    async def _enhance_role(self, role: Dict,
                          context: Dict) -> Dict:
        """Role'e dinamik özellikler ekler."""
        enhanced = role.copy()
        
        # Add context-based attributes
        enhanced['attributes'] = {
            **role.get('attributes', {}),
            'context': self._get_relevant_context(context)
        }
        
        # Add dynamic scopes
        if scopes := await self._calculate_dynamic_scopes(
            role, context
        ):
            enhanced['scopes'] = scopes
            
        # Add temporary permissions
        if temp_permissions := await self._get_temporary_permissions(
            role, context
        ):
            enhanced['temporary_permissions'] = temp_permissions
            
        return enhanced