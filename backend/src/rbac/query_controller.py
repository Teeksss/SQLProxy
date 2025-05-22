from typing import Dict, Optional
from .parser import SQLParser
from .role_manager import RoleManager
from .query_analyzer import QueryAnalyzer

class SQLQueryController:
    def __init__(self):
        self.parser = SQLParser()
        self.role_manager = RoleManager()
        self.query_analyzer = QueryAnalyzer()
        
    async def authorize_query(self, query: str, 
                            context: Dict) -> Dict:
        """Query authorization yapar."""
        # Parse query
        parsed = self.parser.parse_query(query)
        
        # Analyze query for required permissions
        required_permissions = await self._analyze_required_permissions(
            parsed
        )
        
        # Get user's effective permissions
        user_permissions = await self._get_user_permissions(
            context['user_id']
        )
        
        # Check permissions
        authorization = await self._check_permissions(
            required_permissions,
            user_permissions,
            context
        )
        
        if not authorization['authorized']:
            return {
                'authorized': False,
                'reason': authorization['reason'],
                'missing_permissions': authorization['missing']
            }
            
        # Apply row-level security
        modified_query = await self._apply_rls(
            parsed, context
        )
        
        return {
            'authorized': True,
            'modified_query': modified_query,
            'applied_policies': authorization['applied_policies']
        }
        
    async def _analyze_required_permissions(self, 
                                         parsed_query) -> List[str]:
        """Query için gerekli permissionları analiz eder."""
        permissions = set()
        
        # Table permissions
        for table in parsed_query.tables:
            operations = self._get_table_operations(parsed_query, table)
            for operation in operations:
                permissions.add(f"{operation}:{table}")
                
        # Column permissions
        for column in parsed_query.columns:
            permissions.add(f"read:{column.table}.{column.name}")
            
        # Special permissions
        if parsed_query.has_function_calls:
            permissions.add("execute:functions")
            
        return list(permissions)
        
    async def _apply_rls(self, parsed_query, context: Dict) -> str:
        """Row-level security uygular."""
        # Get RLS policies
        policies = await self._get_rls_policies(context)
        
        if not policies:
            return parsed_query.to_sql()
            
        # Apply each policy
        modified = parsed_query
        for policy in policies:
            modified = self._apply_policy(modified, policy)
            
        return modified.to_sql()