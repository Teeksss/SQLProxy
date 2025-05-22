from typing import Dict, Any, List
import sqlparse
from db.connection import DatabaseManager

class QueryService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def execute_query(self, database: str, query: str) -> Dict[str, Any]:
        # Query validation
        if not self._validate_query(query):
            raise ValueError("Invalid query")
            
        connection = self.db_manager.get_connection(database)
        
        with connection.connect() as conn:
            result = conn.execute(query)
            return {
                'columns': result.keys(),
                'rows': [dict(row) for row in result]
            }
    
    def _validate_query(self, query: str) -> bool:
        # Basic SQL injection prevention
        parsed = sqlparse.parse(query)
        if not parsed:
            return False
            
        statement = parsed[0]
        return statement.get_type() in ['SELECT', 'SHOW']
    
    def get_table_schema(self, database: str, table: str) -> List[Dict[str, Any]]:
        query = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table}'
        """
        return self.execute_query(database, query)