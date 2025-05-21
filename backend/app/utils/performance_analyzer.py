"""
Performance Analyzer for SQL Proxy

This module provides utilities for analyzing and optimizing performance
of SQL queries and API endpoints.

Last updated: 2025-05-21 05:11:29
Updated by: Teeksss
"""

import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
from functools import wraps
from datetime import datetime, timedelta
import threading
import json
from pathlib import Path

import numpy as np
from prometheus_client import Histogram, Counter

from app.core.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)

# Performance metrics storage
_performance_metrics = {
    "queries": {},
    "endpoints": {},
    "database": {}
}

# Lock for thread-safe metrics updates
_metrics_lock = threading.Lock()

# Prometheus metrics
if settings.METRICS_ENABLED:
    QUERY_LATENCY = Histogram(
        f"{settings.METRICS_PREFIX}_query_latency_seconds",
        "SQL query execution time in seconds",
        ["database", "endpoint", "status"]
    )
    
    ENDPOINT_LATENCY = Histogram(
        f"{settings.METRICS_PREFIX}_endpoint_latency_seconds",
        "API endpoint execution time in seconds",
        ["method", "endpoint", "status"]
    )
    
    SLOW_QUERIES = Counter(
        f"{settings.METRICS_PREFIX}_slow_queries_total",
        "Number of slow SQL queries",
        ["database", "endpoint"]
    )
    
    SLOW_ENDPOINTS = Counter(
        f"{settings.METRICS_PREFIX}_slow_endpoints_total",
        "Number of slow API endpoints",
        ["method", "endpoint"]
    )

def measure_query_performance(database: str = "default", endpoint: str = "unknown"):
    """
    Decorator to measure SQL query performance
    
    Args:
        database: Database identifier
        endpoint: Endpoint identifier
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip if performance monitoring is disabled
            if not settings.PERFORMANCE_MONITORING_ENABLED:
                return func(*args, **kwargs)
            
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                execution_time = time.time() - start_time
                
                # Record in internal metrics
                with _metrics_lock:
                    db_metrics = _performance_metrics["queries"].setdefault(database, {"times": [], "endpoints": {}})
                    db_metrics["times"].append(execution_time)
                    
                    endpoint_metrics = db_metrics["endpoints"].setdefault(endpoint, [])
                    endpoint_metrics.append(execution_time)
                
                # Record in Prometheus metrics if enabled
                if settings.METRICS_ENABLED:
                    QUERY_LATENCY.labels(database=database, endpoint=endpoint, status=status).observe(execution_time)
                    
                    # Track slow queries
                    if execution_time > settings.SLOW_QUERY_THRESHOLD_MS / 1000:
                        SLOW_QUERIES.labels(database=database, endpoint=endpoint).inc()
                        logger.warning(f"Slow query detected: {execution_time:.2f}s (db={database}, endpoint={endpoint})")
                
        return wrapper
    return decorator

def measure_endpoint_performance(method: str = "GET", endpoint: str = "unknown"):
    """
    Decorator to measure API endpoint performance
    
    Args:
        method: HTTP method
        endpoint: Endpoint path
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip if performance monitoring is disabled
            if not settings.PERFORMANCE_MONITORING_ENABLED:
                return func(*args, **kwargs)
            
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                execution_time = time.time() - start_time
                
                # Record in internal metrics
                with _metrics_lock:
                    method_metrics = _performance_metrics["endpoints"].setdefault(method, {"times": [], "endpoints": {}})
                    method_metrics["times"].append(execution_time)
                    
                    endpoint_metrics = method_metrics["endpoints"].setdefault(endpoint, [])
                    endpoint_metrics.append(execution_time)
                
                # Record in Prometheus metrics if enabled
                if settings.METRICS_ENABLED:
                    ENDPOINT_LATENCY.labels(method=method, endpoint=endpoint, status=status).observe(execution_time)
                    
                    # Track slow endpoints
                    if execution_time > settings.SLOW_ENDPOINT_THRESHOLD_MS / 1000:
                        SLOW_ENDPOINTS.labels(method=method, endpoint=endpoint).inc()
                        logger.warning(f"Slow endpoint detected: {execution_time:.2f}s (method={method}, endpoint={endpoint})")
                
        return wrapper
    return decorator

def analyze_query_performance(
    query: str, 
    parameters: Optional[Dict[str, Any]] = None,
    database: str = "default",
    iterations: int = 3
) -> Dict[str, Any]:
    """
    Analyze performance of a SQL query
    
    Args:
        query: SQL query to analyze
        parameters: Query parameters
        database: Database identifier
        iterations: Number of iterations for testing
        
    Returns:
        Performance analysis results
    """
    try:
        from sqlalchemy import text
        
        # Initialize results
        execution_times = []
        explain_plan = None
        suggested_indexes = []
        
        # Execute query multiple times
        with engine.connect() as connection:
            # Get explain plan
            if engine.dialect.name in ("postgresql", "mysql", "sqlite"):
                explain_query = f"EXPLAIN {query}" if engine.dialect.name == "sqlite" else f"EXPLAIN ANALYZE {query}"
                with connection.begin():
                    result = connection.execute(text(explain_query), parameters or {})
                    explain_plan = [dict(row) for row in result]
            
            # Execute query multiple times
            for _ in range(iterations):
                start_time = time.time()
                with connection.begin():
                    connection.execute(text(query), parameters or {})
                execution_times.append(time.time() - start_time)
        
        # Analyze execution times
        avg_time = statistics.mean(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        stddev = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        
        # Analyze explain plan for suggestions
        suggestions = _analyze_explain_plan(explain_plan) if explain_plan else []
        
        # Generate results
        results = {
            "execution_times": {
                "average": avg_time,
                "min": min_time,
                "max": max_time,
                "stddev": stddev,
                "iterations": iterations
            },
            "explain_plan": explain_plan,
            "suggestions": suggestions,
            "query": query,
            "parameters": parameters,
            "database": database
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing query performance: {e}", exc_info=True)
        return {
            "error": str(e),
            "query": query,
            "parameters": parameters,
            "database": database
        }

def _analyze_explain_plan(explain_plan: List[Dict[str, Any]]) -> List[str]:
    """
    Analyze explain plan for performance suggestions
    
    Args:
        explain_plan: Query explain plan
        
    Returns:
        List of suggestions
    """
    suggestions = []
    
    # Look for common performance issues in the explain plan
    plan_str = str(explain_plan).lower()
    
    if "seq scan" in plan_str or "table scan" in plan_str:
        suggestions.append("Consider adding an index to avoid sequential scans")
    
    if "temporary" in plan_str or "temp" in plan_str:
        suggestions.append("Query uses temporary tables which may impact performance")
    
    if "filesort" in plan_str:
        suggestions.append("Query requires sorting which may impact performance")
    
    if "join" in plan_str and ("nested loop" in plan_str or "nested-loop" in plan_str):
        suggestions.append("Consider optimizing join conditions or adding indexes for joined tables")
    
    return suggestions

def get_performance_summary() -> Dict[str, Any]:
    """
    Get performance summary for all tracked operations
    
    Returns:
        Performance summary data
    """
    with _metrics_lock:
        # Calculate query performance summaries
        query_summary = {}
        for db, metrics in _performance_metrics["queries"].items():
            if not metrics["times"]:
                continue
                
            times = metrics["times"]
            query_summary[db] = {
                "average": statistics.mean(times),
                "median": statistics.median(times),
                "p95": np.percentile(times, 95) if len(times) >= 20 else max(times),
                "min": min(times),
                "max": max(times),
                "count": len(times),
                "endpoints": {}
            }
            
            # Calculate endpoint-specific metrics
            for endpoint, endpoint_times in metrics["endpoints"].items():
                if not endpoint_times:
                    continue
                    
                query_summary[db]["endpoints"][endpoint] = {
                    "average": statistics.mean(endpoint_times),
                    "median": statistics.median(endpoint_times),
                    "p95": np.percentile(endpoint_times, 95) if len(endpoint_times) >= 20 else max(endpoint_times),
                    "min": min(endpoint_times),
                    "max": max(endpoint_times),
                    "count": len(endpoint_times)
                }
        
        # Calculate endpoint performance summaries
        endpoint_summary = {}
        for method, metrics in _performance_metrics["endpoints"].items():
            if not metrics["times"]:
                continue
                
            times = metrics["times"]
            endpoint_summary[method] = {
                "average": statistics.mean(times),
                "median": statistics.median(times),
                "p95": np.percentile(times, 95) if len(times) >= 20 else max(times),
                "min": min(times),
                "max": max(times),
                "count": len(times),
                "endpoints": {}
            }
            
            # Calculate endpoint-specific metrics
            for endpoint, endpoint_times in metrics["endpoints"].items():
                if not endpoint_times:
                    continue
                    
                endpoint_summary[method]["endpoints"][endpoint] = {
                    "average": statistics.mean(endpoint_times),
                    "median": statistics.median(endpoint_times),
                    "p95": np.percentile(endpoint_times, 95) if len(endpoint_times) >= 20 else max(endpoint_times),
                    "min": min(endpoint_times),
                    "max": max(endpoint_times),
                    "count": len(endpoint_times)
                }
        
        # Build overall summary
        summary = {
            "queries": query_summary,
            "endpoints": endpoint_summary,
            "timestamp": datetime.utcnow().isoformat(),
            "collection_period": {
                "start": (datetime.utcnow() - timedelta(hours=settings.PERFORMANCE_METRICS_RETENTION_HOURS)).isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        }
        
        return summary

def export_performance_metrics() -> None:
    """Export performance metrics to file"""
    if not settings.PERFORMANCE_METRICS_EXPORT_ENABLED:
        return
        
    try:
        # Get summary data
        summary = get_performance_summary()
        
        # Create output directory if needed
        output_path = Path(settings.PERFORMANCE_METRICS_EXPORT_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Performance metrics exported to {output_path}")
        
    except Exception as e:
        logger.error(f"Error exporting performance metrics: {e}", exc_info=True)

def reset_performance_metrics() -> None:
    """Reset all performance metrics"""
    with _metrics_lock:
        _performance_metrics["queries"] = {}
        _performance_metrics["endpoints"] = {}
        _performance_metrics["database"] = {}
        
    logger.info("Performance metrics reset")

def schedule_metrics_export() -> None:
    """Schedule regular export of performance metrics"""
    if not settings.PERFORMANCE_METRICS_EXPORT_ENABLED:
        return
        
    def export_task():
        export_performance_metrics()
        # Schedule next export
        threading.Timer(settings.PERFORMANCE_METRICS_EXPORT_INTERVAL, export_task).start()
    
    # Start initial timer
    threading.Timer(settings.PERFORMANCE_METRICS_EXPORT_INTERVAL, export_task).start()
    logger.info(f"Scheduled performance metrics export every {settings.PERFORMANCE_METRICS_EXPORT_INTERVAL} seconds")

# Initialize metrics export schedule
if settings.PERFORMANCE_METRICS_EXPORT_ENABLED:
    schedule_metrics_export()

# Son güncelleme: 2025-05-21 05:11:29
# Güncelleyen: Teeksss