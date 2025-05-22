from typing import Dict, Optional
import pyodbc
from contextlib import contextmanager
import threading
from datetime import datetime
import logging

class MSSQLConnectionManager:
    def __init__(self, config: Dict):
        self.config = config
        self.pool = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger('mssql_manager')
        
    @contextmanager
    def get_connection(self, database: str) -> pyodbc.Connection:
        """Thread-safe connection manager."""
        connection_key = f"{self.config['server']}_{database}"
        
        try:
            # Get or create connection
            with self.lock:
                if connection_key not in self.pool:
                    self.pool[connection_key] = self._create_connection(database)
                    
                conn = self.pool[connection_key]
                
                # Test connection and recreate if needed
                if not self._is_connection_alive(conn):
                    conn.close()
                    self.pool[connection_key] = self._create_connection(database)
                    conn = self.pool[connection_key]
                    
            yield conn
            
        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}")
            raise
            
    def _create_connection(self, database: str) -> pyodbc.Connection:
        """Create new MS SQL connection."""
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.config['server']};"
            f"DATABASE={database};"
            f"UID={self.config['username']};"
            f"PWD={self.config['password']};"
            "Trusted_Connection=yes;"
        )
        
        return pyodbc.connect(connection_string)
        
    def _is_connection_alive(self, conn: pyodbc.Connection) -> bool:
        """Test if connection is still alive."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
        except:
            return False
        
    def close_all(self):
        """Close all connections in pool."""
        with self.lock:
            for conn in self.pool.values():
                try:
                    conn.close()
                except:
                    pass
            self.pool.clear()