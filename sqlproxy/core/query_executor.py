from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, text

class QueryExecutor:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL query"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), parameters=params or {})
            return [dict(row) for row in result]