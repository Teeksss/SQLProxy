from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from .parser import SQLParser
from .optimizer import QueryOptimizer
from .validator import QueryValidator
from .executor import QueryExecutor

class QueryManager:
    def __init__(self):
        self.parser = SQLParser()
        self.optimizer = QueryOptimizer()
        self.validator = QueryValidator()
        self.executor = QueryExecutor()
        
    async def process_query(self, query: str, context: Dict) -> Dict:
        """Query'yi işler ve yönetir."""
        try:
            # Query parsing
            parsed_query = await self.parser.parse(query)
            
            # Query kategorization
            category = self._categorize_query(parsed_query)
            
            # Access control
            if not await self._check_permissions(category, context):
                raise PermissionError("Insufficient permissions")
                
            # Query optimization
            optimized = await self.optimizer.optimize(parsed_query)
            
            # Query validation
            validation = await self.validator.validate(
                optimized, context
            )
            
            if not validation['is_valid']:
                raise ValidationError(validation['errors'])
                
            # Query execution
            result = await self.executor.execute(
                optimized, context
            )
            
            # Log execution
            await self._log_execution(result, context)
            
            return {
                'status': 'success',
                'result': result,
                'metadata': {
                    'optimization': optimized['metadata'],
                    'execution_time': result['execution_time'],
                    'affected_rows': result.get('affected_rows'),
                    'timestamp': datetime.utcnow()
                }
            }
            
        except Exception as e:
            await self._log_error(str(e), context)
            raise
            
    def _categorize_query(self, parsed_query) -> str:
        """Query'yi kategorize eder."""
        categories = {
            'SELECT': self._analyze_select(parsed_query),
            'INSERT': 'data_modification',
            'UPDATE': 'data_modification',
            'DELETE': 'data_modification',
            'CREATE': 'schema_modification',
            'ALTER': 'schema_modification',
            'DROP': 'schema_modification',
            'GRANT': 'permission_modification',
            'REVOKE': 'permission_modification',
            'EXECUTE': 'procedure_execution'
        }
        
        return categories.get(
            parsed_query.get_type(),
            'unknown'
        )
        
    def _analyze_select(self, parsed_query) -> str:
        """SELECT query'sini analiz eder."""
        if parsed_query.has_aggregation():
            return 'analytical_query'
        elif parsed_query.has_joins():
            return 'complex_query'
        else:
            return 'simple_query'