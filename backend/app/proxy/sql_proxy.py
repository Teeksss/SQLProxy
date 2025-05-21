import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import sqlparse
import pymssql
import psycopg2
import mysql.connector
from mysql.connector import errorcode

from app.query.parser import SQLAnalyzer

logger = logging.getLogger(__name__)

class SQLProxy:
    """
    SQL Proxy for executing queries on various database servers.
    Supports MS SQL Server, PostgreSQL, and MySQL.
    """
    
    def __init__(self):
        self.sql_analyzer = SQLAnalyzer()
    
    def connect_to_server(
        self, 
        host: str, 
        port: int, 
        database: str, 
        user: str, 
        password: str,
        db_type: str = "mssql"
    ) -> Any:
        """
        Connect to a database server
        
        Args:
            host: Database server hostname/IP
            port: Database server port
            database: Database name
            user: Database username
            password: Database password
            db_type: Database type (mssql, postgres, mysql)
            
        Returns:
            Database connection object
            
        Raises:
            Exception: If connection fails
        """
        try:
            if db_type == "mssql":
                conn = pymssql.connect(
                    server=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
                return conn
                
            elif db_type == "postgres":
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname=database
                )
                return conn
                
            elif db_type == "mysql":
                conn = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
                return conn
                
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
                
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            raise Exception(f"Failed to connect to database: {str(e)}")
    
    def execute_query(
        self, 
        connection: Any, 
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL query on the connected database
        
        Args:
            connection: Database connection object
            query: SQL query to execute
            params: Query parameters (optional)
            
        Returns:
            Dictionary with query results:
            {
                'columns': List of column names,
                'data': List of data rows,
                'rowcount': Number of affected rows,
                'query_type': Type of query (read, write, ddl, procedure)
            }
            
        Raises:
            Exception: If query execution fails
        """
        start_time = time.time()
        cursor = None
        
        try:
            # Parse and analyze the query
            query_info = self.sql_analyzer.parse_query(query)
            query_type = query_info['query_type']
            
            # Create cursor and execute query
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # For read queries, fetch the results
            if query_type == 'read':
                # Get column names
                if hasattr(cursor, 'description') and cursor.description:
                    columns = [col[0] for col in cursor.description]
                else:
                    columns = []
                
                # Fetch data
                data = cursor.fetchall()
                
                # Convert rows to list of dicts
                result_data = []
                for row in data:
                    # Convert row to dict
                    row_dict = {}
                    for i, col in enumerate(columns):
                        # Handle different data types
                        value = row[i]
                        if isinstance(value, (bytes, bytearray)):
                            value = value.hex()
                        row_dict[col] = value
                    result_data.append(row_dict)
                
                return {
                    'columns': columns,
                    'data': result_data,
                    'rowcount': cursor.rowcount,
                    'query_type': query_type,
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                }
            
            # For non-read queries, commit and return affected rows
            else:
                connection.commit()
                return {
                    'columns': [],
                    'data': [],
                    'rowcount': cursor.rowcount,
                    'query_type': query_type,
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                }
                
        except Exception as e:
            # Log the error
            logger.error(f"Query execution error: {str(e)}")
            
            # Rollback transaction
            try:
                if connection:
                    connection.rollback()
            except Exception:
                pass
            
            raise Exception(f"Query execution failed: {str(e)}")
            
        finally:
            # Close cursor
            if cursor:
                cursor.close()

# Last updated: 2025-05-16 13:31:40
# Updated by: Teeksss