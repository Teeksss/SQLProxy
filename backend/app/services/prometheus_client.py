"""
Prometheus Client for SQL Proxy

This module provides functionality for Prometheus metrics collection
and integration with the monitoring system.

Last updated: 2025-05-21 05:17:27
Updated by: Teeksss
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, 
    CollectorRegistry, push_to_gateway,
    generate_latest, CONTENT_TYPE_LATEST
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize registry
registry = (
    CollectorRegistry() 
    if not settings.METRICS_USE_DEFAULT_REGISTRY 
    else None
)

# Define metrics
HTTP_REQUESTS_TOTAL = Counter(
    f"{settings.METRICS_PREFIX}_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry
)

HTTP_REQUEST_DURATION = Histogram(
    f"{settings.METRICS_PREFIX}_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry
)

DB_QUERY_DURATION = Histogram(
    f"{settings.METRICS_PREFIX}_db_query_duration_seconds",
    "Database query duration in seconds",
    ["database", "operation"],
    registry=registry
)

DB_CONNECTIONS_ACTIVE = Gauge(
    f"{settings.METRICS_PREFIX}_db_connections_active",
    "Number of active database connections",
    ["database"],
    registry=registry
)

API_ERRORS_TOTAL = Counter(
    f"{settings.METRICS_PREFIX}_api_errors_total",
    "Total number of API errors",
    ["method", "endpoint", "error_type"],
    registry=registry
)

MEMORY_USAGE = Gauge(
    f"{settings.METRICS_PREFIX}_memory_usage_bytes",
    "Memory usage in bytes",
    registry=registry
)

CPU_USAGE = Gauge(
    f"{settings.METRICS_PREFIX}_cpu_usage_percent",
    "CPU usage in percent",
    registry=registry
)

QUERIES_TOTAL = Counter(
    f"{settings.METRICS_PREFIX}_queries_total",
    "Total number of SQL queries",
    ["database", "status"],
    registry=registry
)

SLOW_QUERIES_TOTAL = Counter(
    f"{settings.METRICS_PREFIX}_slow_queries_total",
    "Total number of slow SQL queries",
    ["database"],
    registry=registry
)

CACHE_HITS_TOTAL = Counter(
    f"{settings.METRICS_PREFIX}_cache_hits_total",
    "Total number of cache hits",
    ["cache_type"],
    registry=registry
)

CACHE_MISSES_TOTAL = Counter(
    f"{settings.METRICS_PREFIX}_cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
    registry=registry
)

def record_request_start(method: str, endpoint: str) -> float:
    """
    Record the start of an HTTP request
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        
    Returns:
        Start timestamp
    """
    if not settings.METRICS_ENABLED:
        return time.time()
    
    return time.time()

def record_request_end(method: str, endpoint: str, status: int, start_time: float) -> None:
    """
    Record the end of an HTTP request
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        status: HTTP status code
        start_time: Start timestamp
    """
    if not settings.METRICS_ENABLED:
        return
    
    duration = time.time() - start_time
    
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
    HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def record_query_start(database: str, operation: str) -> float:
    """
    Record the start of a database query
    
    Args:
        database: Database name
        operation: Query operation type
        
    Returns:
        Start timestamp
    """
    if not settings.METRICS_ENABLED:
        return time.time()
    
    return time.time()

def record_query_end(database: str, operation: str, status: str, start_time: float) -> None:
    """
    Record the end of a database query
    
    Args:
        database: Database name
        operation: Query operation type
        status: Query status
        start_time: Start timestamp
    """
    if not settings.METRICS_ENABLED:
        return
    
    duration = time.time() - start_time
    
    DB_QUERY_DURATION.labels(database=database, operation=operation).observe(duration)
    QUERIES_TOTAL.labels(database=database, status=status).inc()
    
    # Record slow queries
    if duration > settings.SLOW_QUERY_THRESHOLD_MS / 1000:
        SLOW_QUERIES_TOTAL.labels(database=database).inc()

def record_api_error(method: str, endpoint: str, error_type: str) -> None:
    """
    Record an API error
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        error_type: Error type
    """
    if not settings.METRICS_ENABLED:
        return
    
    API_ERRORS_TOTAL.labels(method=method, endpoint=endpoint, error_type=error_type).inc()

def record_db_connection(database: str, connections: int) -> None:
    """
    Record the number of active database connections
    
    Args:
        database: Database name
        connections: Number of active connections
    """
    if not settings.METRICS_ENABLED:
        return
    
    DB_CONNECTIONS_ACTIVE.labels(database=database).set(connections)

def record_system_metrics(memory_bytes: Optional[int] = None, cpu_percent: Optional[float] = None) -> None:
    """
    Record system metrics
    
    Args:
        memory_bytes: Memory usage in bytes
        cpu_percent: CPU usage in percent
    """
    if not settings.METRICS_ENABLED:
        return
    
    # Try to get metrics from psutil if not provided
    if memory_bytes is None or cpu_percent is None:
        try:
            import psutil
            
            if memory_bytes is None:
                memory = psutil.Process().memory_info()
                memory_bytes = memory.rss
            
            if cpu_percent is None:
                cpu_percent = psutil.Process().cpu_percent(interval=0.1)
        except (ImportError, Exception) as e:
            logger.warning(f"Could not get system metrics from psutil: {e}")
            return
    
    if memory_bytes is not None:
        MEMORY_USAGE.set(memory_bytes)
    
    if cpu_percent is not None:
        CPU_USAGE.set(cpu_percent)

def record_cache_access(cache_type: str, hit: bool) -> None:
    """
    Record a cache access
    
    Args:
        cache_type: Cache type
        hit: Whether the access was a hit or miss
    """
    if not settings.METRICS_ENABLED:
        return
    
    if hit:
        CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()

def get_prometheus_metrics() -> Dict[str, Any]:
    """
    Get current Prometheus metrics
    
    Returns:
        Dictionary of metrics
    """
    if not settings.METRICS_ENABLED:
        return {}
    
    try:
        from prometheus_client.parser import text_string_to_metric_families
        
        # Get metrics as text
        if registry:
            metrics_data = generate_latest(registry).decode("utf-8")
        else:
            metrics_data = generate_latest().decode("utf-8")
        
        # Parse metrics
        result = {}
        for family in text_string_to_metric_families(metrics_data):
            family_name = family.name
            result[family_name] = []
            
            for sample in family.samples:
                # Convert to a more readable format
                metric = {
                    "name": sample.name,
                    "value": sample.value,
                    "labels": sample.labels
                }
                result[family_name].append(metric)
        
        return result
    except Exception as e:
        logger.error(f"Error getting Prometheus metrics: {e}", exc_info=True)
        return {}

def push_metrics_to_gateway() -> None:
    """Push metrics to Prometheus push gateway"""
    if not settings.METRICS_ENABLED or not settings.METRICS_PUSH_GATEWAY_ENABLED:
        return
    
    try:
        push_to_gateway(
            settings.METRICS_PUSH_GATEWAY_URL,
            job=settings.METRICS_JOB_NAME,
            registry=registry or None
        )
        logger.debug(f"Pushed metrics to gateway: {settings.METRICS_PUSH_GATEWAY_URL}")
    except Exception as e:
        logger.error(f"Error pushing metrics to gateway: {e}", exc_info=True)

def schedule_metrics_push() -> None:
    """Schedule regular push of metrics to gateway"""
    if not settings.METRICS_ENABLED or not settings.METRICS_PUSH_GATEWAY_ENABLED:
        return
    
    def push_task():
        push_metrics_to_gateway()
        # Schedule next push
        threading.Timer(settings.METRICS_PUSH_INTERVAL_SECONDS, push_task).start()
    
    # Start initial timer
    threading.Timer(settings.METRICS_PUSH_INTERVAL_SECONDS, push_task).start()
    logger.info(f"Scheduled metrics push every {settings.METRICS_PUSH_INTERVAL_SECONDS} seconds")

# Initialize metrics push schedule if enabled
if settings.METRICS_ENABLED and settings.METRICS_PUSH_GATEWAY_ENABLED:
    schedule_metrics_push()

# Son güncelleme: 2025-05-21 05:17:27
# Güncelleyen: Teeksss