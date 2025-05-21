"""
Metrics Collector for SQL Proxy

This module provides metrics collection for SQL Proxy,
enabling integration with Prometheus and other monitoring systems.

Last updated: 2025-05-20 11:46:15
Updated by: Teeksss
"""

import time
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from collections import defaultdict
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram, Summary, REGISTRY, CollectorRegistry, push_to_gateway

from app.core.config import settings

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    Metrics collector for SQL Proxy
    
    Collects metrics for API endpoints, database queries, and system stats.
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.enabled = settings.METRICS_ENABLED
        self.prefix = settings.METRICS_PREFIX
        
        # Create registry
        if settings.METRICS_USE_DEFAULT_REGISTRY:
            self.registry = REGISTRY
        else:
            self.registry = CollectorRegistry()
        
        # Create metrics
        self._create_metrics()
        
        # Thread for pushing metrics to gateway
        self.push_thread = None
        self.running = False
        
        # Start push thread if enabled
        if self.enabled and settings.METRICS_PUSH_GATEWAY_ENABLED:
            self.start_push_thread()
        
        logger.info("Metrics collector initialized")
    
    def _create_metrics(self):
        """Create metrics objects"""
        # API metrics
        self.api_requests_total = Counter(
            f"{self.prefix}_api_requests_total",
            "Total count of API requests",
            ["method", "path", "status"],
            registry=self.registry
        )
        
        self.api_request_duration_seconds = Histogram(
            f"{self.prefix}_api_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "path"],
            registry=self.registry,
            buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0)
        )
        
        self.api_requests_in_progress = Gauge(
            f"{self.prefix}_api_requests_in_progress",
            "Number of API requests in progress",
            ["method", "path"],
            registry=self.registry
        )
        
        self.api_requests_failed_total = Counter(
            f"{self.prefix}_api_requests_failed_total",
            "Total count of failed API requests",
            ["method", "path", "error_type"],
            registry=self.registry
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            f"{self.prefix}_db_queries_total",
            "Total count of database queries",
            ["server_alias", "operation", "status"],
            registry=self.registry
        )
        
        self.db_query_duration_seconds = Histogram(
            f"{self.prefix}_db_query_duration_seconds",
            "Database query duration in seconds",
            ["server_alias", "operation"],
            registry=self.registry,
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0, 30.0)
        )
        
        self.db_query_rows_affected = Histogram(
            f"{self.prefix}_db_query_rows_affected",
            "Number of rows affected by database queries",
            ["server_alias", "operation"],
            registry=self.registry,
            buckets=(0, 1, 10, 100, 1000, 10000, 100000, 1000000)
        )
        
        self.db_connections_active = Gauge(
            f"{self.prefix}_db_connections_active",
            "Number of active database connections",
            ["server_alias"],
            registry=self.registry
        )
        
        self.db_connections_idle = Gauge(
            f"{self.prefix}_db_connections_idle",
            "Number of idle database connections",
            ["server_alias"],
            registry=self.registry
        )
        
        self.db_connection_errors_total = Counter(
            f"{self.prefix}_db_connection_errors_total",
            "Total count of database connection errors",
            ["server_alias", "error_type"],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            f"{self.prefix}_cache_hits_total",
            "Total count of cache hits",
            ["cache_type"],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            f"{self.prefix}_cache_misses_total",
            "Total count of cache misses",
            ["cache_type"],
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            f"{self.prefix}_cache_size",
            "Current size of cache",
            ["cache_type"],
            registry=self.registry
        )
        
        # Authentication metrics
        self.auth_success_total = Counter(
            f"{self.prefix}_auth_success_total",
            "Total count of successful authentications",
            ["auth_type"],
            registry=self.registry
        )
        
        self.auth_failure_total = Counter(
            f"{self.prefix}_auth_failure_total",
            "Total count of failed authentications",
            ["auth_type", "reason"],
            registry=self.registry
        )
        
        # System metrics
        self.process_start_time_seconds = Gauge(
            f"{self.prefix}_process_start_time_seconds",
            "Start time of the process since unix epoch in seconds",
            registry=self.registry
        )
        
        # Set start time
        self.process_start_time_seconds.set(time.time())
        
        self.process_cpu_seconds_total = Counter(
            f"{self.prefix}_process_cpu_seconds_total",
            "Total user and system CPU time spent in seconds",
            registry=self.registry
        )
        
        self.process_resident_memory_bytes = Gauge(
            f"{self.prefix}_process_resident_memory_bytes",
            "Resident memory size in bytes",
            registry=self.registry
        )
        
        self.process_open_fds = Gauge(
            f"{self.prefix}_process_open_fds",
            "Number of open file descriptors",
            registry=self.registry
        )
        
        # Version info
        self.info = Gauge(
            f"{self.prefix}_info",
            "SQL Proxy version information",
            ["version", "python_version", "platform"],
            registry=self.registry
        )
        
        # Set version info
        import platform
        import sys
        self.info.labels(
            version=settings.VERSION,
            python_version=platform.python_version(),
            platform=platform.platform()
        ).set(1)
    
    def start_push_thread(self):
        """Start thread for pushing metrics to gateway"""
        if not self.enabled or not settings.METRICS_PUSH_GATEWAY_ENABLED:
            return
        
        with threading.RLock():
            if self.running:
                logger.warning("Push thread already running")
                return
            
            self.running = True
            self.push_thread = threading.Thread(
                target=self._push_metrics_loop,
                daemon=True
            )
            self.push_thread.start()
    
    def stop_push_thread(self):
        """Stop thread for pushing metrics to gateway"""
        with threading.RLock():
            self.running = False
            
            if self.push_thread:
                self.push_thread.join(timeout=5)
    
    def _push_metrics_loop(self):
        """Loop for pushing metrics to gateway"""
        while self.running:
            try:
                # Update system metrics
                self._update_system_metrics()
                
                # Push metrics to gateway
                push_to_gateway(
                    settings.METRICS_PUSH_GATEWAY_URL,
                    job=settings.METRICS_JOB_NAME,
                    registry=self.registry
                )
                
                logger.debug("Metrics pushed to gateway")
                
            except Exception as e:
                logger.error(f"Error pushing metrics to gateway: {e}")
            
            # Sleep until next push
            time.sleep(settings.METRICS_PUSH_INTERVAL_SECONDS)
    
    def _update_system_metrics(self):
        """Update system metrics"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            # Update CPU time
            cpu_time = process.cpu_times()
            total_cpu_seconds = cpu_time.user + cpu_time.system
            self.process_cpu_seconds_total.inc(total_cpu_seconds)
            
            # Update memory usage
            memory_info = process.memory_info()
            self.process_resident_memory_bytes.set(memory_info.rss)
            
            # Update open file descriptors
            self.process_open_fds.set(process.num_fds())
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def observe_api_request(
        self, 
        method: str, 
        path: str, 
        duration: float, 
        status: int
    ):
        """
        Record API request metrics
        
        Args:
            method: HTTP method
            path: Request path
            duration: Request duration in seconds
            status: HTTP status code
        """
        if not self.enabled:
            return
        
        try:
            # Normalize path
            path = self._normalize_path(path)
            
            # Increment request counter
            self.api_requests_total.labels(
                method=method,
                path=path,
                status=str(status)
            ).inc()
            
            # Record request duration
            self.api_request_duration_seconds.labels(
                method=method,
                path=path
            ).observe(duration)
            
            # Record failure if status >= 400
            if status >= 400:
                error_type = "server_error" if status >= 500 else "client_error"
                self.api_requests_failed_total.labels(
                    method=method,
                    path=path,
                    error_type=error_type
                ).inc()
            
        except Exception as e:
            logger.error(f"Error recording API metrics: {e}")
    
    def observe_db_query(
        self, 
        server_alias: str, 
        operation: str, 
        duration: float, 
        rows_affected: int, 
        status: str
    ):
        """
        Record database query metrics
        
        Args:
            server_alias: Database server alias
            operation: Query operation type (SELECT, INSERT, etc.)
            duration: Query duration in seconds
            rows_affected: Number of rows affected
            status: Query status (success, error)
        """
        if not self.enabled:
            return
        
        try:
            # Normalize operation
            operation = operation.upper()
            
            # Increment query counter
            self.db_queries_total.labels(
                server_alias=server_alias,
                operation=operation,
                status=status
            ).inc()
            
            # Record query duration
            self.db_query_duration_seconds.labels(
                server_alias=server_alias,
                operation=operation
            ).observe(duration)
            
            # Record rows affected
            self.db_query_rows_affected.labels(
                server_alias=server_alias,
                operation=operation
            ).observe(rows_affected)
            
        except Exception as e:
            logger.error(f"Error recording DB metrics: {e}")
    
    def set_db_connections(
        self, 
        server_alias: str, 
        active: int, 
        idle: int
    ):
        """
        Set database connection metrics
        
        Args:
            server_alias: Database server alias
            active: Number of active connections
            idle: Number of idle connections
        """
        if not self.enabled:
            return
        
        try:
            # Set connection gauges
            self.db_connections_active.labels(
                server_alias=server_alias
            ).set(active)
            
            self.db_connections_idle.labels(
                server_alias=server_alias
            ).set(idle)
            
        except Exception as e:
            logger.error(f"Error setting DB connection metrics: {e}")
    
    def observe_db_connection_error(
        self, 
        server_alias: str, 
        error_type: str
    ):
        """
        Record database connection error
        
        Args:
            server_alias: Database server alias
            error_type: Type of error
        """
        if not self.enabled:
            return
        
        try:
            # Increment error counter
            self.db_connection_errors_total.labels(
                server_alias=server_alias,
                error_type=error_type
            ).inc()
            
        except Exception as e:
            logger.error(f"Error recording DB connection error: {e}")
    
    def observe_cache_operation(
        self, 
        cache_type: str, 
        hit: bool
    ):
        """
        Record cache operation
        
        Args:
            cache_type: Type of cache
            hit: True if cache hit, False if miss
        """
        if not self.enabled:
            return
        
        try:
            # Increment hit or miss counter
            if hit:
                self.cache_hits_total.labels(
                    cache_type=cache_type
                ).inc()
            else:
                self.cache_misses_total.labels(
                    cache_type=cache_type
                ).inc()
            
        except Exception as e:
            logger.error(f"Error recording cache metrics: {e}")
    
    def set_cache_size(
        self, 
        cache_type: str, 
        size: int
    ):
        """
        Set cache size metric
        
        Args:
            cache_type: Type of cache
            size: Size of cache
        """
        if not self.enabled:
            return
        
        try:
            # Set cache size gauge
            self.cache_size.labels(
                cache_type=cache_type
            ).set(size)
            
        except Exception as e:
            logger.error(f"Error setting cache size metric: {e}")
    
    def observe_auth_result(
        self, 
        auth_type: str, 
        success: bool, 
        reason: Optional[str] = None
    ):
        """
        Record authentication result
        
        Args:
            auth_type: Type of authentication (jwt, api_key, etc.)
            success: Whether authentication was successful
            reason: Reason for failure (if success is False)
        """
        if not self.enabled:
            return
        
        try:
            # Increment success or failure counter
            if success:
                self.auth_success_total.labels(
                    auth_type=auth_type
                ).inc()
            else:
                self.auth_failure_total.labels(
                    auth_type=auth_type,
                    reason=reason or "unknown"
                ).inc()
            
        except Exception as e:
            logger.error(f"Error recording auth metrics: {e}")
    
    def track_api_request_start(
        self, 
        method: str, 
        path: str
    ):
        """
        Track start of API request for in-progress gauge
        
        Args:
            method: HTTP method
            path: Request path
        """
        if not self.enabled:
            return
        
        try:
            # Normalize path
            path = self._normalize_path(path)
            
            # Increment in-progress gauge
            self.api_requests_in_progress.labels(
                method=method,
                path=path
            ).inc()
            
        except Exception as e:
            logger.error(f"Error tracking API request start: {e}")
    
    def track_api_request_end(
        self, 
        method: str, 
        path: str
    ):
        """
        Track end of API request for in-progress gauge
        
        Args:
            method: HTTP method
            path: Request path
        """
        if not self.enabled:
            return
        
        try:
            # Normalize path
            path = self._normalize_path(path)
            
            # Decrement in-progress gauge
            self.api_requests_in_progress.labels(
                method=method,
                path=path
            ).dec()
            
        except Exception as e:
            logger.error(f"Error tracking API request end: {e}")
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for metrics labeling
        
        Args:
            path: Original path
            
        Returns:
            Normalized path
        """
        # Replace numeric IDs with placeholders
        import re
        path = re.sub(r'/\d+', '/:id', path)
        
        # Replace UUIDs with placeholders
        uuid_pattern = r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        path = re.sub(uuid_pattern, '/:uuid', path)
        
        return path

# Create singleton instance
metrics_collector = MetricsCollector()

# Son güncelleme: 2025-05-20 11:46:15
# Güncelleyen: Teeksss