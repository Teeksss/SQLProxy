"""Prometheus metrics for SQLProxy"""
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

from prometheus_client import Counter, Gauge, Histogram, Summary

# Define metrics
QUERY_COUNT = Counter(
    'sqlproxy_query_total',
    'Total number of SQL queries processed',
    ['status', 'query_type']
)

QUERY_DURATION = Histogram(
    'sqlproxy_query_duration_seconds',
    'SQL query duration in seconds',
    ['query_type'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

CACHE_HIT_RATIO = Gauge(
    'sqlproxy_cache_hit_ratio',
    'Cache hit ratio'
)

ACTIVE_CONNECTIONS = Gauge(
    'sqlproxy_active_connections',
    'Number of active database connections'
)

ERRORS = Counter(
    'sqlproxy_errors_total',
    'Total number of errors',
    ['type']
)

# Function to track query metrics
F = TypeVar('F', bound=Callable[..., Any])

def track_query_metrics(query_type: str) -> Callable[[F], F]:
    """Decorator to track query metrics"""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                ERRORS.labels(type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                QUERY_COUNT.labels(status=status, query_type=query_type).inc()
                QUERY_DURATION.labels(query_type=query_type).observe(duration)
        
        return wrapper  # type: ignore
    
    return decorator

# Update cache metrics
def update_cache_metrics(hits: int, misses: int) -> None:
    """Update cache hit ratio metrics"""
    total = hits + misses
    ratio = hits / total if total > 0 else 0
    CACHE_HIT_RATIO.set(ratio)

# Update connection metrics
def update_connection_metrics(active: int) -> None:
    """Update active connections metrics"""
    ACTIVE_CONNECTIONS.set(active)