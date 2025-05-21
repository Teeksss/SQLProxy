"""
SQL Proxy Python SDK Client

A Python client for interacting with SQL Proxy API.

Last updated: 2025-05-20 11:32:47
Updated by: Teeksss
"""

import os
import json
import time
import logging
import uuid
import gzip
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, TypeVar, Generic, cast
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Type variable for transaction results
T = TypeVar('T')

class SQLProxyError(Exception):
    """Custom exception class for SQL Proxy errors"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 0, 
        error_code: Optional[str] = None,
        query: Optional[str] = None,
        server_alias: Optional[str] = None
    ):
        """
        Initialize SQLProxyError
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Error code from API
            query: SQL query that caused the error
            server_alias: Server alias where the error occurred
        """
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.query = query
        self.server_alias = server_alias
    
    def __str__(self) -> str:
        """String representation of the error"""
        parts = [f"SQLProxyError: {super().__str__()}"]
        
        if self.status_code:
            parts.append(f"Status code: {self.status_code}")
        
        if self.error_code:
            parts.append(f"Error code: {self.error_code}")
        
        if self.server_alias:
            parts.append(f"Server: {self.server_alias}")
        
        return " | ".join(parts)

class Transaction:
    """
    Transaction context manager for SQL Proxy
    
    Used to execute SQL queries within a transaction context.
    """
    
    def __init__(self, client: 'SQLProxyClient', transaction_id: str, server_alias: str):
        """
        Initialize Transaction
        
        Args:
            client: SQLProxyClient instance
            transaction_id: Transaction ID
            server_alias: Server alias for the transaction
        """
        self.client = client
        self.transaction_id = transaction_id
        self.server_alias = server_alias
        self.is_active = True
    
    def query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None, 
        **options
    ) -> Dict[str, Any]:
        """
        Execute a SQL query within the transaction
        
        Args:
            query: SQL query to execute
            params: Query parameters
            options: Additional query options
            
        Returns:
            Query result
        """
        if not self.is_active:
            raise SQLProxyError("Transaction is no longer active", 400, "TRANSACTION_INACTIVE")
        
        return self.client.query(
            query=query,
            params=params or {},
            server_alias=self.server_alias,
            transaction_id=self.transaction_id,
            **options
        )
    
    def commit(self) -> bool:
        """
        Commit the transaction
        
        Returns:
            True if committed successfully
        """
        if not self.is_active:
            raise SQLProxyError("Transaction is no longer active", 400, "TRANSACTION_INACTIVE")
        
        result = self.client.commit_transaction(self.transaction_id)
        self.is_active = False
        return result
    
    def rollback(self) -> bool:
        """
        Rollback the transaction
        
        Returns:
            True if rolled back successfully
        """
        if not self.is_active:
            raise SQLProxyError("Transaction is no longer active", 400, "TRANSACTION_INACTIVE")
        
        result = self.client.rollback_transaction(self.transaction_id)
        self.is_active = False
        return result
    
    def __enter__(self) -> 'Transaction':
        """Enter the transaction context"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the transaction context
        
        Commits the transaction if no exception occurred, otherwise rolls back.
        """
        if not self.is_active:
            return False
        
        if exc_type is not None:
            # Exception occurred, rollback
            try:
                self.rollback()
            except Exception as e:
                logging.error(f"Error rolling back transaction: {e}")
            return False  # Re-raise the exception
        
        # No exception, commit
        self.commit()
        return True

class SQLProxyClient:
    """
    SQL Proxy Client
    
    A Python client for interacting with SQL Proxy API.
    """
    
    def __init__(
        self,
        api_key: str,
        config_path: Optional[str] = None,
        client_config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        retry_non_idempotent: bool = False
    ):
        """
        Initialize SQLProxyClient
        
        Args:
            api_key: API key for authentication
            config_path: Path to client configuration file
            client_config: Client configuration dictionary
            logger: Logger instance
            custom_headers: Custom HTTP headers to include in requests
            retry_non_idempotent: Whether to retry non-idempotent requests
        """
        self.api_key = api_key
        self.logger = logger or logging.getLogger("sqlproxy")
        
        # Load configuration
        if client_config:
            self.client_config = client_config
        elif config_path:
            try:
                with open(config_path, 'r') as f:
                    self.client_config = json.load(f)
            except Exception as e:
                raise SQLProxyError(f"Failed to load client configuration: {str(e)}")
        else:
            raise SQLProxyError("Either client_config or config_path must be provided")
        
        # Set up request session
        self.session = requests.Session()
        
        # Create session headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Client-ID': self.client_config['client_id'],
            'X-SDK-Version': f'python-{self.client_config["api_version"]}',
        })
        
        # Add custom headers
        if custom_headers:
            self.session.headers.update(custom_headers)
        
        # Configure retries
        retry_strategy = Retry(
            total=self.client_config['settings']['max_retries'],
            backoff_factor=self.client_config['settings']['retry_delay_seconds'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS", "PUT", "DELETE"] + (["POST"] if retry_non_idempotent else [])
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Rate limiting
        self.request_count = 0
        self.last_request_timestamp = 0
        self.rate_limit_lock = threading.RLock()
        
        # Query cache
        self.cache = {}
        self.cache_lock = threading.RLock()
        
        # Active transactions
        self.active_transactions = {}
        self.transaction_lock = threading.RLock()
        
        self.logger.info(f"SQLProxyClient initialized for client_id: {self.client_config['client_id']}")
    
    def query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        server_alias: Optional[str] = None,
        transaction_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_rows: Optional[int] = None,
        include_metadata: bool = True,
        stream_results: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a SQL query
        
        Args:
            query: SQL query to execute
            params: Query parameters
            server_alias: Server to execute query on
            transaction_id: Transaction ID for transactional queries
            timeout_seconds: Query timeout in seconds
            max_rows: Maximum number of rows to return
            include_metadata: Whether to include metadata in the response
            stream_results: Whether to stream results
            
        Returns:
            Query result
        """
        self._throttle_requests()
        
        if params is None:
            params = {}
        
        # Check cache
        cache_key = self._get_cache_key(query, params, server_alias, max_rows)
        if self.client_config['settings']['cache_ttl_seconds'] > 0 and server_alias:
            with self.cache_lock:
                if cache_key in self.cache:
                    cached_data, timestamp = self.cache[cache_key]
                    age = time.time() - timestamp
                    if age < self.client_config['settings']['cache_ttl_seconds']:
                        self.logger.debug(f"Cache hit for query: {query[:50]}...")
                        return cached_data
        
        # Find server alias if not provided
        effective_server_alias = server_alias or self._get_default_server_alias()
        
        # Check if server exists
        server = self._get_server_by_alias(effective_server_alias)
        if not server:
            raise SQLProxyError(f"Server not found: {effective_server_alias}", 400, 'SERVER_NOT_FOUND')
        
        # Check transaction
        if transaction_id:
            with self.transaction_lock:
                if transaction_id not in self.active_transactions:
                    raise SQLProxyError(
                        f"Transaction not found or expired: {transaction_id}",
                        400,
                        'TRANSACTION_NOT_FOUND'
                    )
        
        # Check operation permissions
        operation = self._get_operation_type(query)
        if operation not in server['features']['allowed_operations']:
            raise SQLProxyError(
                f"Operation not allowed: {operation} on server {effective_server_alias}",
                403,
                'OPERATION_NOT_ALLOWED'
            )
        
        try:
            # Prepare request
            endpoint = f"{self.client_config['api']['base_url']}{self.client_config['api']['query_endpoint']}"
            request_data = {
                "query": query,
                "params": params,
                "server_alias": effective_server_alias,
                "transaction_id": transaction_id,
                "options": {
                    "timeout_seconds": timeout_seconds or self.client_config['settings']['request_timeout_seconds'],
                    "max_rows": max_rows,
                    "include_metadata": include_metadata,
                    "stream_results": stream_results
                }
            }
            
            # Add request ID for tracing
            headers = {
                'X-Request-ID': str(uuid.uuid4())
            }
            
            # Check if we should use compression
            if self.client_config['settings']['enable_compression'] and len(query) > 1000:
                compressed_data = gzip.compress(json.dumps(request_data).encode())
                headers['Content-Encoding'] = 'gzip'
                
                # Convert to base64 for JSON compatibility
                request_body = {
                    "compressed_data": compressed_data.hex()
                }
            else:
                request_body = request_data
            
            # Execute request
            response = self.session.post(
                endpoint,
                json=request_body,
                headers=headers,
                timeout=request_data['options']['timeout_seconds']
            )
            
            # Handle errors
            if response.status_code >= 400:
                self._handle_error_response(response, query, effective_server_alias)
            
            result = response.json()
            
            # Validate result if enabled
            if self.client_config['settings']['enable_response_validation']:
                self._validate_query_result(result)
            
            # Cache result if cacheable (SELECT queries only)
            if self.client_config['settings']['cache_ttl_seconds'] > 0 and operation == 'SELECT':
                with self.cache_lock:
                    self.cache[cache_key] = (result, time.time())
            
            return result
            
        except SQLProxyError:
            raise
        except Exception as e:
            raise SQLProxyError(
                f"Query execution failed: {str(e)}",
                500,
                'QUERY_EXECUTION_ERROR',
                query,
                effective_server_alias
            )
    
    def batch(
        self,
        queries: List[Dict[str, Any]],
        server_alias: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a batch of SQL queries
        
        Args:
            queries: List of query objects, each containing:
                    - query: SQL query
                    - params: Query parameters (optional)
                    - options: Query options (optional)
            server_alias: Server to execute queries on
            
        Returns:
            Batch query result
        """
        self._throttle_requests()
        
        # Check if batch size is within limits
        if len(queries) > self.client_config['settings']['max_batch_size']:
            raise SQLProxyError(
                f"Batch size exceeds limit: {len(queries)} > {self.client_config['settings']['max_batch_size']}",
                400,
                'BATCH_SIZE_EXCEEDED'
            )
        
        # Find server alias if not provided
        effective_server_alias = server_alias or self._get_default_server_alias()
        
        # Check if server exists
        server = self._get_server_by_alias(effective_server_alias)
        if not server:
            raise SQLProxyError(f"Server not found: {effective_server_alias}", 400, 'SERVER_NOT_FOUND')
        
        # Check if server supports batch operations
        if not server['features']['batch_support']:
            raise SQLProxyError(
                f"Server does not support batch operations: {effective_server_alias}",
                400,
                'BATCH_NOT_SUPPORTED'
            )
        
        # Check operation permissions for all queries
        for i, query_item in enumerate(queries):
            query = query_item.get('query', '')
            operation = self._get_operation_type(query)
            if operation not in server['features']['allowed_operations']:
                raise SQLProxyError(
                    f"Operation not allowed: {operation} on server {effective_server_alias} (query {i+1})",
                    403,
                    'OPERATION_NOT_ALLOWED'
                )
        
        try:
            # Prepare request
            endpoint = f"{self.client_config['api']['base_url']}{self.client_config['api']['batch_endpoint']}"
            request_data = {
                "queries": [
                    {
                        "query": q.get('query', ''),
                        "params": q.get('params', {}),
                        "options": q.get('options', {})
                    }
                    for q in queries
                ],
                "server_alias": effective_server_alias
            }
            
            # Add request ID for tracing
            headers = {
                'X-Request-ID': str(uuid.uuid4())
            }
            
            # Execute request
            response = self.session.post(
                endpoint,
                json=request_data,
                headers=headers,
                timeout=self.client_config['settings']['request_timeout_seconds']
            )
            
            # Handle errors
            if response.status_code >= 400:
                self._handle_error_response(response, "BATCH", effective_server_alias)
            
            result = response.json()
            
            # Validate result if enabled
            if self.client_config['settings']['enable_response_validation']:
                self._validate_batch_result(result)
            
            return result
            
        except SQLProxyError:
            raise
        except Exception as e:
            raise SQLProxyError(
                f"Batch execution failed: {str(e)}",
                500,
                'BATCH_EXECUTION_ERROR',
                None,
                effective_server_alias
            )
    
    def begin_transaction(
        self,
        server_alias: str,
        isolation_level: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> str:
        """
        Begin a new transaction
        
        Args:
            server_alias: Server to start transaction on
            isolation_level: Transaction isolation level
            timeout_seconds: Transaction timeout in seconds
            
        Returns:
            Transaction ID
        """
        self._throttle_requests()
        
        # Check if server exists
        server = self._get_server_by_alias(server_alias)
        if not server:
            raise SQLProxyError(f"Server not found: {server_alias}", 400, 'SERVER_NOT_FOUND')
        
        # Check if server supports transactions
        if not server['features']['transaction_support']:
            raise SQLProxyError(
                f"Server does not support transactions: {server_alias}",
                400,
                'TRANSACTIONS_NOT_SUPPORTED'
            )
        
        try:
            # Prepare request
            endpoint = f"{self.client_config['api']['base_url']}/v1/transaction/begin"
            request_data = {
                "server_alias": server_alias,
                "isolation_level": isolation_level,
                "timeout_seconds": timeout_seconds
            }
            
            # Add request ID for tracing
            headers = {
                'X-Request-ID': str(uuid.uuid4())
            }
            
            # Execute request
            response = self.session.post(
                endpoint,
                json=request_data,
                headers=headers,
                timeout=self.client_config['settings']['request_timeout_seconds']
            )
            
            # Handle errors
            if response.status_code >= 400:
                self._handle_error_response(response, "BEGIN TRANSACTION", server_alias)
            
            result = response.json()
            transaction_id = result['transaction_id']
            
            # Track transaction
            with self.transaction_lock:
                self.active_transactions[transaction_id] = {
                    'server_alias': server_alias,
                    'start_time': time.time()
                }
            
            return transaction_id
            
        except SQLProxyError:
            raise
        except Exception as e:
            raise SQLProxyError(
                f"Failed to begin transaction: {str(e)}",
                500,
                'TRANSACTION_BEGIN_ERROR',
                None,
                server_alias
            )
    
    def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction
        
        Args:
            transaction_id: Transaction ID to commit
            
        Returns:
            True if committed successfully
        """
        self._throttle_requests()
        
        # Check if transaction exists
        with self.transaction_lock:
            if transaction_id not in self.active_transactions:
                raise SQLProxyError(
                    f"Transaction not found or expired: {transaction_id}",
                    400,
                    'TRANSACTION_NOT_FOUND'
                )
            
            server_alias = self.active_transactions[transaction_id]['server_alias']
        
        try:
            # Prepare request
            endpoint = f"{self.client_config['api']['base_url']}/v1/transaction/commit"
            request_data = {
                "transaction_id": transaction_id
            }
            
            # Add request ID for tracing
            headers = {
                'X-Request-ID': str(uuid.uuid4())
            }
            
            # Execute request
            response = self.session.post(
                endpoint,
                json=request_data,
                headers=headers,
                timeout=self.client_config['settings']['request_timeout_seconds']
            )
            
            # Handle errors
            if response.status_code >= 400:
                self._handle_error_response(response, "COMMIT TRANSACTION", server_alias)
            
            result = response.json()
            
            # Remove transaction from tracking
            with self.transaction_lock:
                if transaction_id in self.active_transactions:
                    del self.active_transactions[transaction_id]
            
            return result.get('success', False)
            
        except SQLProxyError:
            raise
        except Exception as e:
            raise SQLProxyError(
                f"Failed to commit transaction: {str(e)}",
                500,
                'TRANSACTION_COMMIT_ERROR',
                None,
                server_alias
            )
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction
        
        Args:
            transaction_id: Transaction ID to rollback
            
        Returns:
            True if rolled back successfully
        """
        self._throttle_requests()
        
        # Check if transaction exists
        with self.transaction_lock:
            if transaction_id not in self.active_transactions:
                raise SQLProxyError(
                    f"Transaction not found or expired: {transaction_id}",
                    400,
                    'TRANSACTION_NOT_FOUND'
                )
            
            server_alias = self.active_transactions[transaction_id]['server_alias']
        
        try:
            # Prepare request
            endpoint = f"{self.client_config['api']['base_url']}/v1/transaction/rollback"
            request_data = {
                "transaction_id": transaction_id
            }
            
            # Add request ID for tracing
            headers = {
                'X-Request-ID': str(uuid.uuid4())
            }
            
            # Execute request
            response = self.session.post(
                endpoint,
                json=request_data,
                headers=headers,
                timeout=self.client_config['settings']['request_timeout_seconds']
            )
            
            # Handle errors
            if response.status_code >= 400:
                self._handle_error_response(response, "ROLLBACK TRANSACTION", server_alias)
            
            result = response.json()
            
            # Remove transaction from tracking
            with self.transaction_lock:
                if transaction_id in self.active_transactions:
                    del self.active_transactions[transaction_id]
            
            return result.get('success', False)
            
        except SQLProxyError:
            raise
        except Exception as e:
            raise SQLProxyError(
                f"Failed to rollback transaction: {str(e)}",
                500,
                'TRANSACTION_ROLLBACK_ERROR',
                None,
                server_alias
            )
    
    def transaction(
        self,
        server_alias: str,
        isolation_level: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> Transaction:
        """
        Create a transaction context manager
        
        Args:
            server_alias: Server to start transaction on
            isolation_level: Transaction isolation level
            timeout_seconds: Transaction timeout in seconds
            
        Returns:
            Transaction context manager
        """
        # Begin transaction
        transaction_id = self.begin_transaction(
            server_alias=server_alias,
            isolation_level=isolation_level,
            timeout_seconds=timeout_seconds
        )
        
        # Create transaction object
        return Transaction(self, transaction_id, server_alias)
    
    def transaction_scope(
        self,
        func: Callable[[Transaction], T],
        server_alias: str,
        isolation_level: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> T:
        """
        Execute function within a transaction scope
        
        Args:
            func: Function to execute with transaction context
            server_alias: Server to start transaction on
            isolation_level: Transaction isolation level
            timeout_seconds: Transaction timeout in seconds
            
        Returns:
            Result of function execution
        """
        # Create transaction
        with self.transaction(
            server_alias=server_alias,
            isolation_level=isolation_level,
            timeout_seconds=timeout_seconds
        ) as tx:
            return func(tx)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get SQL Proxy API status
        
        Returns:
            API status information
        """
        self._throttle_requests()
        
        try:
            # Prepare request
            endpoint = f"{self.client_config['api']['base_url']}{self.client_config['api']['status_endpoint']}"
            
            # Execute request
            response = self.session.get(
                endpoint,
                timeout=self.client_config['settings']['request_timeout_seconds']
            )
            
            # Handle errors
            if response.status_code >= 400:
                self._handle_error_response(response, "GET STATUS", None)
            
            return response.json()
            
        except SQLProxyError:
            raise
        except Exception as e:
            raise SQLProxyError(
                f"Failed to get status: {str(e)}",
                500,
                'STATUS_ERROR'
            )
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """
        Get available servers
        
        Returns:
            List of server configurations
        """
        return self.client_config['servers']
    
    def clear_cache(self) -> None:
        """Clear the query cache"""
        with self.cache_lock:
            self.cache.clear()
        
        self.logger.info("Query cache cleared")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get client configuration
        
        Returns:
            Client configuration
        """
        return self.client_config
    
    def _throttle_requests(self) -> None:
        """
        Throttle requests based on rate limit
        
        Raises:
            SQLProxyError: If rate limit is exceeded
        """
        with self.rate_limit_lock:
            now = time.time()
            elapsed = now - self.last_request_timestamp
            
            # Check if we need to throttle
            if self.request_count >= self.client_config['rate_limit']['requests_per_minute']:
                # Reset counter if a minute has passed
                if elapsed >= 60:
                    self.request_count = 0
                    self.last_request_timestamp = now
                else:
                    # Sleep to respect rate limit
                    sleep_time = 60 - elapsed
                    
                    if sleep_time > 0:
                        self.logger.debug(f"Rate limit reached, sleeping for {sleep_time}s")
                        time.sleep(sleep_time)
                        self.request_count = 0
                        self.last_request_timestamp = time.time()
            
            # Update counter
            self.request_count += 1
            self.last_request_timestamp = now
    
    def _get_default_server_alias(self) -> str:
        """
        Get default server alias
        
        Returns:
            Default server alias
            
        Raises:
            SQLProxyError: If no servers configured
        """
        if not self.client_config['servers']:
            raise SQLProxyError('No servers configured', 400, 'NO_SERVERS_CONFIGURED')
        
        return self.client_config['servers'][0]['server_alias']
    
    def _get_server_by_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        """
        Get server configuration by alias
        
        Args:
            alias: Server alias
            
        Returns:
            Server configuration or None if not found
        """
        for server in self.client_config['servers']:
            if server['server_alias'] == alias:
                return server
        
        return None
    
    def _get_operation_type(self, query: str) -> str:
        """
        Get operation type from SQL query
        
        Args:
            query: SQL query
            
        Returns:
            Operation type (SELECT, INSERT, UPDATE, DELETE, etc.)
        """
        normalized = query.strip().upper()
        
        if normalized.startswith('SELECT'): return 'SELECT'
        if normalized.startswith('INSERT'): return 'INSERT'
        if normalized.startswith('UPDATE'): return 'UPDATE'
        if normalized.startswith('DELETE'): return 'DELETE'
        if normalized.startswith('CREATE'): return 'CREATE'
        if normalized.startswith('ALTER'): return 'ALTER'
        if normalized.startswith('DROP'): return 'DROP'
        if normalized.startswith('TRUNCATE'): return 'TRUNCATE'
        if normalized.startswith('GRANT'): return 'GRANT'
        if normalized.startswith('REVOKE'): return 'REVOKE'
        
        return 'UNKNOWN'
    
    def _get_cache_key(
        self, 
        query: str,
        params: Dict[str, Any],
        server_alias: Optional[str],
        max_rows: Optional[int]
    ) -> str:
        """
        Get cache key for a query
        
        Args:
            query: SQL query
            params: Query parameters
            server_alias: Server alias
            max_rows: Maximum rows
            
        Returns:
            Cache key
        """
        # Create key components
        key = {
            'query': query,
            'params': params,
            'server_alias': server_alias,
            'max_rows': max_rows
        }
        
        # Create JSON string for key
        return json.dumps(key, sort_keys=True)
    
    def _validate_query_result(self, result: Dict[str, Any]) -> None:
        """
        Validate query result
        
        Args:
            result: Query result to validate
            
        Raises:
            SQLProxyError: If result is invalid
        """
        if not result or not isinstance(result, dict):
            raise SQLProxyError(
                'Invalid query result format (not a dictionary)',
                500,
                'INVALID_RESULT_FORMAT'
            )
        
        if 'columns' not in result or not isinstance(result['columns'], list):
            raise SQLProxyError(
                'Invalid query result format (missing or invalid columns)',
                500,
                'INVALID_RESULT_FORMAT'
            )
        
        if 'data' not in result or not isinstance(result['data'], list):
            raise SQLProxyError(
                'Invalid query result format (missing or invalid data)',
                500,
                'INVALID_RESULT_FORMAT'
            )
    
    def _validate_batch_result(self, result: Dict[str, Any]) -> None:
        """
        Validate batch query result
        
        Args:
            result: Batch query result to validate
            
        Raises:
            SQLProxyError: If result is invalid
        """
        if not result or not isinstance(result, dict):
            raise SQLProxyError(
                'Invalid batch result format (not a dictionary)',
                500,
                'INVALID_RESULT_FORMAT'
            )
        
        if 'results' not in result or not isinstance(result['results'], list):
            raise SQLProxyError(
                'Invalid batch result format (missing or invalid results)',
                500,
                'INVALID_RESULT_FORMAT'
            )
        
        # Validate each result
        for i, query_result in enumerate(result['results']):
            try:
                self._validate_query_result(query_result)
            except SQLProxyError as e:
                raise SQLProxyError(
                    f'Invalid result format for query {i+1}: {e}',
                    500,
                    'INVALID_RESULT_FORMAT'
                )
    
    def _handle_error_response(
        self,
        response: requests.Response,
        query: str,
        server_alias: Optional[str]
    ) -> None:
        """
        Handle error response from API
        
        Args:
            response: Error response
            query: SQL query or operation
            server_alias: Server alias
            
        Raises:
            SQLProxyError: With appropriate error details
        """
        try:
            error_data = response.json()
            error_message = error_data.get('detail', error_data.get('message', response.reason))
            error_code = error_data.get('error_code', 'UNKNOWN_ERROR')
        except:
            error_message = response.reason or "Unknown error"
            error_code = "UNKNOWN_ERROR"
        
        raise SQLProxyError(
            error_message,
            response.status_code,
            error_code,
            query,
            server_alias
        )

# Son güncelleme: 2025-05-20 11:32:47
# Güncelleyen: Teeksss