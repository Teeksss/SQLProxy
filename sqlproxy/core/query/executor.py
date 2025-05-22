"""
Query Executor Module

Handles SQL query execution, caching, and monitoring.
"""
import time
import logging
from typing import Any, Dict, List, Optional, Union

from sqlproxy.core.database.integration import DatabaseIntegration
from sqlproxy.core.redis.connection import RedisConnection
from sqlproxy.core.query.cache import QueryCache
from sqlproxy.core.query.parser import QueryParser
from sqlproxy.security.query_security import SQLInjectionChecker

logger = logging.getLogger(__name__)

class QueryExecutor:
    """
    Handles SQL query execution with caching, security checks,
    and performance monitoring.
    """
    
    def __init__(
        self,
        db_integration: DatabaseIntegration,
        redis_connection: Optional[RedisConnection] = None,
        enable_cache: bool = True,
        enable_security: bool = True,
        enable_monitoring: bool = True
    ):
        self.db = db_integration
        self.redis = redis_connection
        self.query_cache = QueryCache(redis_connection) if redis_connection and enable_cache else None
        self.security_checker = SQLInjectionChecker() if enable_security else None
        self.query_parser = QueryParser()
        
        # Import here to avoid circular imports
        from sqlproxy.core.performance.analyzer import PerformanceAnalyzer
        self.performance_analyzer = PerformanceAnalyzer() if enable_monitoring else None
        
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query with optional caching, security checks,
        and performance monitoring.
        
        Args:
            query: SQL query string
            params: Query parameters
            use_cache: Whether to use query cache
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            List of result dictionaries
        
        Raises:
            SecurityError: If query fails security checks
            DatabaseError: If query execution fails
        """
        start_time = time.time()
        memory_before = self._get_memory_usage()
        
        # Parse query
        parsed_query = self.query_parser.parse(query)
        query_type = parsed_query.get('type', 'unknown')
        
        # Security check
        if self.security_checker:
            issues = self.security_checker.check_query(query)
            if issues:
                issues_str = "; ".join(issues)
                logger.warning(f"Security issues in query: {issues_str}")
                raise SecurityError(f"Query failed security check: {issues_str}")
        
        # Check cache
        cache_key = None
        if self.query_cache and use_cache and query_type.lower() in ('select', 'show'):
            cache_key = self.query_cache.get_cache_key(query, params)
            cached_result = self.query_cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for query: {query[:100]}...")
                
                # Record performance even for cached queries
                if self.performance_analyzer:
                    end_time = time.time()
                    self.performance_analyzer.record_query(
                        query=query,
                        execution_time=end_time - start_time,
                        query_type=f"{query_type}_cached"
                    )
                
                return cached_result
        
        # Execute query
        try:
            result = self.db.execute_query(query, params)
            
            # Cache result for read-only queries
            if self.query_cache and use_cache and cache_key and query_type.lower() in ('select', 'show'):
                self.query_cache.set(cache_key, result, cache_ttl)
            
            # Record performance
            if self.performance_analyzer:
                end_time = time.time()
                memory_after = self._get_memory_usage()
                self.performance_analyzer.record_query(
                    query=query,
                    execution_time=end_time - start_time,
                    query_type=query_type
                )
                self.performance_analyzer.metrics.add_metric(
                    execution_time=end_time - start_time,
                    query_count=1,
                    memory_usage=memory_after - memory_before
                )
            
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseError(f"Query execution failed: {str(e)}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        try:
            import os
            import psutil
            
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)  # MB
        except ImportError:
            return 0.0  # If psutil not available


class SecurityError(Exception):
    """Raised when a query fails security checks"""
    pass


class DatabaseError(Exception):
    """Raised when query execution fails"""
    pass