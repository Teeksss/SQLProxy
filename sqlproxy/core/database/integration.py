"""
Database integration and connection management
"""
import logging
from typing import Any, Dict, List, Optional, Union

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class DatabaseIntegration:
    """
    Database integration with SQLAlchemy
    """
    
    def __init__(self, connection_string: str, pool_size: int = 5, max_overflow: int = 10):
        """
        Initialize database connection
        
        Args:
            connection_string: Database connection string
            pool_size: Connection pool size
            max_overflow: Max overflow connections
        """
        self.connection_string = connection_string
        self.engine = create_engine(
            connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow
        )
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries containing query results
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return [dict(row) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine"""
        return self.engine
    
    def test_connection(self) -> bool:
        """Public method to test connection"""
        return self._test_connection()