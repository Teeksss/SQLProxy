from typing import Dict, Optional
import pyodbc
from contextlib import contextmanager
import threading
from datetime import datetime
import asyncio
from .models import ServerConfig, ConnectionPool

class SQLServerManager:
    def __init__(self):
        self.pools = {}  # server -> pool
        self.configs = {}  # server -> config
        self.lock = threading.Lock()
        self.max_pool_size = 10
        
    async def add_server(self, config: ServerConfig) -> Dict:
        """Yeni SQL Server ekler."""
        try:
            with self.lock:
                server_id = config.server_name
                
                # Test connection
                await self._test_connection(config)
                
                # Initialize pool
                self.pools[server_id] = ConnectionPool(
                    max_size=self.max_pool_size
                )
                
                # Store config
                self.configs[server_id] = config
                
                return {
                    'status': 'success',
                    'server_id': server_id,
                    'message': 'Server added successfully'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    @contextmanager
    async def get_connection(self, server_id: str,
                           database: str) -> pyodbc.Connection:
        """Server bağlantısı alır."""
        pool = self.pools.get(server_id)
        if not pool:
            raise ValueError(f"Unknown server: {server_id}")
            
        try:
            # Get connection from pool
            conn = await pool.acquire()
            
            # Change database if needed
            if database:
                conn.execute(f"USE {database}")
                
            yield conn
            
        finally:
            # Return connection to pool
            await pool.release(conn)
            
    async def _test_connection(self, config: ServerConfig) -> bool:
        """Bağlantı testi yapar."""
        conn_str = self._build_connection_string(config)
        
        try:
            conn = pyodbc.connect(conn_str)
            conn.close()
            return True
            
        except Exception as e:
            raise ConnectionError(
                f"Connection test failed: {str(e)}"
            )
            
    def _build_connection_string(self, config: ServerConfig) -> str:
        """Connection string oluşturur."""
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config.server_name};"
            f"DATABASE={config.default_database};"
            f"UID={config.username};"
            f"PWD={config.password};"
            f"Trusted_Connection={config.trusted_connection};"
        )