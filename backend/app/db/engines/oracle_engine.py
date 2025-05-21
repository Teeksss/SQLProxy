"""
Oracle Database Engine for SQL Proxy

This module provides Oracle-specific database connection and query functionality.

Last updated: 2025-05-21 07:20:45
Updated by: Teeksss
"""

import logging
import time
import cx_Oracle
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import json
import re
from datetime import date, datetime

from app.models.server import Server
from app.services.security_service import security_service
from app.services.vault_service import vault_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class OracleEngine:
    """
    Oracle database engine for SQL Proxy
    
    Provides Oracle-specific connection and query functionality.
    """
    
    def __init__(self):
        """Initialize Oracle engine"""
        # Configure cx_Oracle
        try:
            # Check if Oracle client is initialized
            cx_Oracle.init_oracle_client()
            logger.info("Oracle client initialized")
        except Exception as e:
            # Already initialized or not available
            logger.warning(f"Oracle client initialization skipped: {e}")
    
    async def connect(
        self,
        server: Server,
        password: Optional[str] = None,
        db: Optional[Any] = None
    ) -> Tuple[Any, str]:
        """
        Connect to Oracle database
        
        Args:
            server: Server configuration
            password: Optional password (if not provided, retrieved from server)
            db: Optional database session
            
        Returns:
            Tuple of (connection, connection DSN)
        """
        start_time = time.time()
        logger.info(f"Connecting to Oracle database: {server.host}:{server.port}/{server.database}")
        
        try:
            # Get password
            if not password:
                if server.use_vault and vault_service.is_enabled() and db:
                    from app.crud.crud_server import server as server_crud
                    password = await server_crud.get_password(db, server)
                elif server.password and server.is_encrypted:
                    password = security_service.decrypt(server.password)
                else:
                    password = server.password
            
            # Determine connection method
            if server.service_name:
                # Connect using service name
                dsn = cx_Oracle.makedsn(
                    host=server.host,
                    port=server.port,
                    service_name=server.service_name
                )
            else:
                # Connect using SID (database name)
                dsn = cx_Oracle.makedsn(
                    host=server.host,
                    port=server.port,
                    sid=server.database
                )
            
            # Configure connection
            connection_params = {}
            
            # Add SSL configuration if enabled
            if server.ssl_enabled:
                if server.ssl_ca or server.ssl_cert or server.ssl_key:
                    connection_params["ssl_ca"] = server.ssl_ca
                    connection_params["ssl_cert"] = server.ssl_cert
                    connection_params["ssl_key"] = server.ssl_key
                else:
                    connection_params["ssl_verify"] = False
            
            # Add custom connection parameters
            if server.connection_params:
                connection_params.update(server.connection_params)
            
            # Create connection
            connection = cx_Oracle.connect(
                user=server.username,
                password=password,
                dsn=dsn,
                encoding="UTF-8",
                nencoding="UTF-8"
            )
            
            # Log successful connection
            elapsed_time = time.time() - start_time
            logger.info(f"Connected to Oracle database in {elapsed_time:.3f}s")
            
            return connection, str(dsn)
        
        except cx_Oracle.Error as e:
            # Log and re-raise
            elapsed_time = time.time() - start_time
            error_message = str(e).strip()
            logger.error(f"Oracle connection error in {elapsed_time:.3f}s: {error_message}")
            
            # Raise appropriate exception
            raise Exception(f"Oracle connection error: {error_message}")
    
    async def execute_query(
        self,
        connection: Any,
        sql_text: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 10000,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Execute SQL query on Oracle database
        
        Args:
            connection: Database connection
            sql_text: SQL query text
            params: Optional query parameters
            max_rows: Maximum number of rows to return
            timeout: Query timeout in seconds
            
        Returns:
            Query results
        """
        start_time = time.time()
        logger.info(f"Executing Oracle query: {sql_text[:200]}{'...' if len(sql_text) > 200 else ''}")
        
        cursor = None
        try:
            # Create cursor
            cursor = connection.cursor()
            
            # Set array size for better performance
            cursor.arraysize = 1000
            
            # Configure query timeout
            if timeout > 0:
                cursor.setoutputsize(timeout)
            
            # Execute query
            if params:
                # Convert parameters to cx_Oracle format
                oracle_params = self._convert_params(params)
                cursor.execute(sql_text, oracle_params)
            else:
                cursor.execute(sql_text)
            
            # Check if query has results
            if cursor.description:
                # Get column names
                columns = [col[0] for col in cursor.description]
                
                # Fetch rows, limited to max_rows
                raw_rows = cursor.fetchmany(max_rows)
                
                # Convert to JSON-serializable types
                rows = []
                for row in raw_rows:
                    converted_row = [self._convert_oracle_type(value) for value in row]
                    rows.append(dict(zip(columns, converted_row)))
                
                # Prepare result with rows
                result = {
                    "success": True,
                    "rows": rows,
                    "columns": columns,
                    "row_count": len(rows),
                    "truncated": cursor.rowcount > len(rows) if cursor.rowcount >= 0 else False,
                    "execution_time": time.time() - start_time
                }
            else:
                # No results, might be INSERT/UPDATE/DELETE
                row_count = cursor.rowcount if cursor.rowcount >= 0 else 0
                
                # Prepare result with row count
                result = {
                    "success": True,
                    "rows": [],
                    "columns": [],
                    "row_count": row_count,
                    "execution_time": time.time() - start_time
                }
            
            # Log success
            elapsed_time = time.time() - start_time
            logger.info(f"Oracle query executed successfully in {elapsed_time:.3f}s")
            
            