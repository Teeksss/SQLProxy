"""
API Performance Monitoring for SQL Proxy

This module provides API performance monitoring and metrics collection
capabilities for SQL Proxy.

Last updated: 2025-05-20 11:18:07
Updated by: Teeksss
"""

import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import os
import statistics
from functools import wraps

from app.core.config import settings
from app.metrics.prometheus_client import PrometheusClient, MetricType

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Performance monitoring for SQL Proxy API
    
    Collects and analyzes performance metrics for API endpoints and
    database queries.
    """
    
    def __init__(self):
        """Initialize the performance monitor"""
        # Configuration
        self.enabled = settings.PERFORMANCE_MONITORING_ENABLED
        self.retention_hours = settings.PERFORMANCE_METRICS_RETENTION_HOURS
        self.slow_endpoint_threshold_ms = settings.SLOW_ENDPOINT_THRESHOLD_MS
        self.slow_query_threshold_ms = settings.SLOW_QUERY_THRESHOLD_MS
        self.metrics_export_enabled = settings.PERFORMANCE_METRICS_EXPORT_ENABLED
        self.metrics_export_interval = settings.PERFORMANCE_METRICS_EXPORT_INTERVAL
        self.metrics_export_path = settings.PERFORMANCE_METRICS_EXPORT_PATH
        
        # Metrics storage
        self.endpoint_metrics = defaultdict(list)  # path -> list of metrics
        self.query_metrics = defaultdict(list)     # query_hash -> list of metrics
        self.endpoint_stats = {}  # path -> calculated stats
        self.query_stats = {}     # query_hash -> calculated stats
        
        # Current metrics snapshots (last refresh time + data)
        self.endpoint_stats_refresh_time = None
        self.query_stats_refresh_time = None
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Background tasks
        self.export_thread = None
        self.cleanup_thread = None
        self.running = False
        
        # Integration with Prometheus metrics (if enabled)
        self.prometheus_client = PrometheusClient() if settings.PROMETHEUS_ENABLED else None
        
        logger.info("Performance monitor initialized")
        
        # Start background tasks if enabled
        if self.enabled:
            self.start()
    
    def start(self):
        """Start monitoring tasks"""
        if not self.enabled:
            logger.info("Performance monitoring is disabled")
            return
        
        with self.lock:
            if self.running:
                logger.warning("Performance monitor already running")
                return
            
            self.running = True
            
            # Start metrics export thread
            if self.metrics_export_enabled:
                self.export_thread = threading.Thread(
                    target=self._metrics_export_loop,
                    daemon=True
                )
                self.export_thread.start()
            
            # Start cleanup thread
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True
            )
            self.cleanup_thread.start()
            
            logger.info("Performance monitor started")
    
    def stop(self):
        """Stop monitoring tasks"""
        with self.lock:
            if not self.running:
                logger.warning("Performance monitor not running")
                return
            
            self.running = False
            
            # Threads are daemon threads so they'll exit when the main process exits
            # But we'll give them a chance to exit gracefully
            if self.export_thread:
                self.export_thread.join(timeout=5)
            
            if self.cleanup_thread:
                self.cleanup_thread.join(timeout=5)
            
            logger.info("Performance monitor stopped")
    
    def record_endpoint_metrics(
        self,
        path: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record API endpoint metrics
        
        Args:
            path: Endpoint path
            method: HTTP method
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            user_id: User ID (if authenticated)
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        # Normalize path
        path = self._normalize_path(path)
        
        # Create metric
        metric = {
            "timestamp": datetime.utcnow(),
            "path": path,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "metadata": metadata
        }
        
        # Record metric
        with self.lock:
            key = f"{method}:{path}"
            self.endpoint_metrics[key].append(metric)
        
        # Invalidate stats cache
        self.endpoint_stats_refresh_time = None
        
        # Record to Prometheus if enabled
        if self.prometheus_client:
            is_success = 200 <= status_code < 300
            is_error = status_code >= 400
            is_slow = duration_ms > self.slow_endpoint_threshold_ms
            
            labels = {
                "path": path,
                "method": method,
                "status_code": str(status_code),
                "is_slow": "true" if is_slow else "false"
            }
            
            self.prometheus_client.observe(
                name="api_request_duration_milliseconds",
                value=duration_ms,
                labels=labels,
                metric_type=MetricType.HISTOGRAM
            )
            
            self.prometheus_client.increment(
                name="api_requests_total",
                labels=labels,
                metric_type=MetricType.COUNTER
            )
            
            if is_error:
                self.prometheus_client.increment(
                    name="api_errors_total",
                    labels=labels,
                    metric_type=MetricType.COUNTER
                )
            
            if is_slow:
                self.prometheus_client.increment(
                    name="api_slow_requests_total",
                    labels=labels,
                    metric_type=MetricType.COUNTER
                )
    
    def record_query_metrics(
        self,
        query: str,
        query_hash: str,
        duration_ms: float,
        server_alias: str,
        rows_affected: int,
        success: bool,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record database query metrics
        
        Args:
            query: SQL query
            query_hash: Query hash
            duration_ms: Query duration in milliseconds
            server_alias: Database server alias
            rows_affected: Number of rows affected
            success: Whether query was successful
            user_id: User ID (if authenticated)
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        # Create metric
        metric = {
            "timestamp": datetime.utcnow(),
            "query": query,
            "query_hash": query_hash,
            "duration_ms": duration_ms,
            "server_alias": server_alias,
            "rows_affected": rows_affected,
            "success": success,
            "user_id": user_id,
            "metadata": metadata
        }
        
        # Record metric
        with self.lock:
            self.query_metrics[query_hash].append(metric)
        
        # Invalidate stats cache
        self.query_stats_refresh_time = None
        
        # Record to Prometheus if enabled
        if self.prometheus_client:
            is_slow = duration_ms > self.slow_query_threshold_ms
            
            labels = {
                "server_alias": server_alias,
                "success": "true" if success else "false",
                "is_slow": "true" if is_slow else "false"
            }
            
            self.prometheus_client.observe(
                name="sql_query_duration_milliseconds",
                value=duration_ms,
                labels=labels,
                metric_type=MetricType.HISTOGRAM
            )
            
            self.prometheus_client.increment(
                name="sql_queries_total",
                labels=labels,
                metric_type=MetricType.COUNTER
            )
            
            self.prometheus_client.observe(
                name="sql_query_rows_affected",
                value=rows_affected,
                labels=labels,
                metric_type=MetricType.HISTOGRAM
            )
            
            if not success:
                self.prometheus_client.increment(
                    name="sql_query_errors_total",
                    labels=labels,
                    metric_type=MetricType.COUNTER
                )
            
            if is_slow:
                self.prometheus_client.increment(
                    name="sql_slow_queries_total",
                    labels=labels,
                    metric_type=MetricType.COUNTER
                )
    
    def get_endpoint_stats(
        self,
        path: Optional[str] = None,
        method: Optional[str] = None,
        hours: int = 24,
        percentiles: List[float] = None
    ) -> Dict[str, Any]:
        """
        Get API endpoint performance statistics
        
        Args:
            path: Filter by path (optional)
            method: Filter by HTTP method (optional)
            hours: Time range in hours
            percentiles: List of percentiles to calculate
            
        Returns:
            Dictionary of endpoint statistics
        """
        if not self.enabled:
            return {"error": "Performance monitoring is disabled"}
        
        if not percentiles:
            percentiles = [50, 90, 95, 99]
        
        # Check if we need to refresh stats
        current_time = datetime.utcnow()
        refresh_needed = (
            self.endpoint_stats_refresh_time is None or
            (current_time - self.endpoint_stats_refresh_time).total_seconds() > 60
        )
        
        if refresh_needed:
            self._refresh_endpoint_stats(percentiles)
        
        # Filter by path/method if specified
        if path or method:
            filtered_stats = {}
            
            for key, stats in self.endpoint_stats.items():
                endpoint_method, endpoint_path = key.split(":", 1)
                
                if method and endpoint_method != method:
                    continue
                
                if path:
                    normalized_path = self._normalize_path(path)
                    if endpoint_path != normalized_path:
                        continue
                
                filtered_stats[key] = stats
            
            return {
                "stats": filtered_stats,
                "timestamp": self.endpoint_stats_refresh_time.isoformat() if self.endpoint_stats_refresh_time else None
            }
        
        # Return all stats
        return {
            "stats": self.endpoint_stats,
            "timestamp": self.endpoint_stats_refresh_time.isoformat() if self.endpoint_stats_refresh_time else None
        }
    
    def get_query_stats(
        self,
        query_hash: Optional[str] = None,
        server_alias: Optional[str] = None,
        hours: int = 24,
        percentiles: List[float] = None
    ) -> Dict[str, Any]:
        """
        Get database query performance statistics
        
        Args:
            query_hash: Filter by query hash (optional)
            server_alias: Filter by server alias (optional)
            hours: Time range in hours
            percentiles: List of percentiles to calculate
            
        Returns:
            Dictionary of query statistics
        """
        if not self.enabled:
            return {"error": "Performance monitoring is disabled"}
        
        if not percentiles:
            percentiles = [50, 90, 95, 99]
        
        # Check if we need to refresh stats
        current_time = datetime.utcnow()
        refresh_needed = (
            self.query_stats_refresh_time is None or
            (current_time - self.query_stats_refresh_time).total_seconds() > 60
        )
        
        if refresh_needed:
            self._refresh_query_stats(percentiles)
        
        # Filter by query_hash if specified
        if query_hash:
            if query_hash in self.query_stats:
                stats = self.query_stats[query_hash]
                if server_alias:
                    # Further filter by server_alias
                    server_stats = [s for s in stats.get("servers", []) if s["server_alias"] == server_alias]
                    filtered_stats = stats.copy()
                    filtered_stats["servers"] = server_stats
                    return {
                        "stats": {query_hash: filtered_stats},
                        "timestamp": self.query_stats_refresh_time.isoformat() if self.query_stats_refresh_time else None
                    }
                else:
                    return {
                        "stats": {query_hash: stats},
                        "timestamp": self.query_stats_refresh_time.isoformat() if self.query_stats_refresh_time else None
                    }
            else:
                return {
                    "stats": {},
                    "timestamp": self.query_stats_refresh_time.isoformat() if self.query_stats_refresh_time else None
                }
        
        # Filter by server_alias if specified
        if server_alias:
            filtered_stats = {}
            
            for qhash, stats in self.query_stats.items():
                server_stats = [s for s in stats.get("servers", []) if s["server_alias"] == server_alias]
                
                if server_stats:
                    filtered_stat = stats.copy()
                    filtered_stat["servers"] = server_stats
                    filtered_stats[qhash] = filtered_stat
            
            return {
                "stats": filtered_stats,
                "timestamp": self.query_stats_refresh_time.isoformat() if self.query_stats_refresh_time else None
            }
        
        # Return all stats
        return {
            "stats": self.query_stats,
            "timestamp": self.query_stats_refresh_time.isoformat() if self.query_stats_refresh_time else None
        }
    
    def get_slow_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get slowest API endpoints
        
        Args:
            limit: Maximum number of endpoints to return
            
        Returns:
            List of slow endpoint statistics
        """
        if not self.enabled:
            return []
        
        # Ensure stats are fresh
        if (
            self.endpoint_stats_refresh_time is None or
            (datetime.utcnow() - self.endpoint_stats_refresh_time).total_seconds() > 60
        ):
            self._refresh_endpoint_stats()
        
        # Get all endpoint stats
        endpoints = []
        
        for key, stats in self.endpoint_stats.items():
            method, path = key.split(":", 1)
            
            endpoint = {
                "path": path,
                "method": method,
                "avg_duration_ms": stats.get("avg_duration_ms", 0),
                "p95_duration_ms": stats.get("percentiles", {}).get("95", 0),
                "count": stats.get("count", 0),
                "error_rate": stats.get("error_rate", 0),
                "is_slow": stats.get("avg_duration_ms", 0) > self.slow_endpoint_threshold_ms
            }
            
            endpoints.append(endpoint)
        
        # Sort by average duration (descending)
        endpoints.sort(key=lambda x: x["avg_duration_ms"], reverse=True)
        
        # Return top N
        return endpoints[:limit]
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get slowest database queries
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of slow query statistics
        """
        if not self.enabled:
            return []
        
        # Ensure stats are fresh
        if (
            self.query_stats_refresh_time is None or
            (datetime.utcnow() - self.query_stats_refresh_time).total_seconds() > 60
        ):
            self._refresh_query_stats()
        
        # Get all query stats
        queries = []
        
        for query_hash, stats in self.query_stats.items():
            query = {
                "query_hash": query_hash,
                "query_text": stats.get("query_text", ""),
                "avg_duration_ms": stats.get("avg_duration_ms", 0),
                "p95_duration_ms": stats.get("percentiles", {}).get("95", 0),
                "count": stats.get("count", 0),
                "error_rate": stats.get("error_rate", 0),
                "servers": stats.get("servers", []),
                "is_slow": stats.get("avg_duration_ms", 0) > self.slow_query_threshold_ms
            }
            
            queries.append(query)
        
        # Sort by average duration (descending)
        queries.sort(key=lambda x: x["avg_duration_ms"], reverse=True)
        
        # Return top N
        return queries[:limit]
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        Get overall performance statistics
        
        Returns:
            Dictionary of overall statistics
        """
        if not self.enabled:
            return {"error": "Performance monitoring is disabled"}
        
        # Ensure stats are fresh
        if (
            self.endpoint_stats_refresh_time is None or
            (datetime.utcnow() - self.endpoint_stats_refresh_time).total_seconds() > 60
        ):
            self._refresh_endpoint_stats()
        
        if (
            self.query_stats_refresh_time is None or
            (datetime.utcnow() - self.query_stats_refresh_time).total_seconds() > 60
        ):
            self._refresh_query_stats()
        
        # Calculate overall endpoint stats
        total_endpoint_requests = 0
        total_endpoint_errors = 0
        total_endpoint_duration = 0
        slow_endpoints = 0
        
        for stats in self.endpoint_stats.values():
            count = stats.get("count", 0)
            total_endpoint_requests += count
            total_endpoint_errors += stats.get("error_count", 0)
            total_endpoint_duration += stats.get("avg_duration_ms", 0) * count
            
            if stats.get("avg_duration_ms", 0) > self.slow_endpoint_threshold_ms:
                slow_endpoints += 1
        
        avg_endpoint_duration = (
            total_endpoint_duration / total_endpoint_requests
            if total_endpoint_requests > 0 else 0
        )
        
        endpoint_error_rate = (
            (total_endpoint_errors / total_endpoint_requests) * 100
            if total_endpoint_requests > 0 else 0
        )
        
        # Calculate overall query stats
        total_queries = 0
        total_query_errors = 0
        total_query_duration = 0
        slow_queries = 0
        
        for stats in self.query_stats.values():
            count = stats.get("count", 0)
            total_queries += count
            total_query_errors += stats.get("error_count", 0)
            total_query_duration += stats.get("avg_duration_ms", 0) * count
            
            if stats.get("avg_duration_ms", 0) > self.slow_query_threshold_ms:
                slow_queries += 1
        
        avg_query_duration = (
            total_query_duration / total_queries
            if total_queries > 0 else 0
        )
        
        query_error_rate = (
            (total_query_errors / total_queries) * 100
            if total_queries > 0 else 0
        )
        
        # Return overall stats
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "total_endpoints": len(self.endpoint_stats),
                "total_requests": total_endpoint_requests,
                "avg_duration_ms": avg_endpoint_duration,
                "error_rate": endpoint_error_rate,
                "slow_endpoints": slow_endpoints
            },
            "queries": {
                "total_queries": len(self.query_stats),
                "total_executions": total_queries,
                "avg_duration_ms": avg_query_duration,
                "error_rate": query_error_rate,
                "slow_queries": slow_queries
            }
        }
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize API path by removing query parameters and trailing slashes
        
        Args:
            path: Original path
            
        Returns:
            Normalized path
        """
        # Remove query parameters
        path = path.split("?")[0]
        
        # Remove trailing slashes
        path = path.rstrip("/")
        
        # Add leading slash if missing
        if not path.startswith("/"):
            path = "/" + path
        
        return path
    
    def _refresh_endpoint_stats(self, percentiles: List[float] = None) -> None:
        """
        Refresh endpoint statistics
        
        Args:
            percentiles: List of percentiles to calculate
        """
        if not percentiles:
            percentiles = [50, 90, 95, 99]
        
        with self.lock:
            # Calculate cutoff time for metrics retention
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
            
            # Calculate stats for each endpoint
            new_stats = {}
            
            for key, metrics in self.endpoint_metrics.items():
                # Filter out old metrics
                recent_metrics = [m for m in metrics if m["timestamp"] >= cutoff_time]
                
                # Update metrics list (remove old ones)
                self.endpoint_metrics[key] = recent_metrics
                
                # Skip if no metrics
                if not recent_metrics:
                    continue
                
                # Calculate statistics
                durations = [m["duration_ms"] for m in recent_metrics]
                status_codes = [m["status_code"] for m in recent_metrics]
                
                # Basic stats
                count = len(recent_metrics)
                avg_duration = sum(durations) / count if count > 0 else 0
                min_duration = min(durations) if durations else 0
                max_duration = max(durations) if durations else 0
                
                # Error stats
                error_count = sum(1 for code in status_codes if code >= 400)
                error_rate = (error_count / count) * 100 if count > 0 else 0
                
                # Calculate percentiles
                percentile_values = {}
                if durations:
                    sorted_durations = sorted(durations)
                    for p in percentiles:
                        idx = int((p / 100) * count)
                        percentile_values[str(p)] = sorted_durations[min(idx, count - 1)]
                
                # Get method and path
                method, path = key.split(":", 1)
                
                # Create stats object
                stats = {
                    "path": path,
                    "method": method,
                    "count": count,
                    "avg_duration_ms": avg_duration,
                    "min_duration_ms": min_duration,
                    "max_duration_ms": max_duration,
                    "error_count": error_count,
                    "error_rate": error_rate,
                    "percentiles": percentile_values,
                    "is_slow": avg_duration > self.slow_endpoint_threshold_ms
                }
                
                new_stats[key] = stats
            
            # Update stats
            self.endpoint_stats = new_stats
            self.endpoint_stats_refresh_time = datetime.utcnow()
    
    def _refresh_query_stats(self, percentiles: List[float] = None) -> None:
        """
        Refresh query statistics
        
        Args:
            percentiles: List of percentiles to calculate
        """
        if not percentiles:
            percentiles = [50, 90, 95, 99]
        
        with self.lock:
            # Calculate cutoff time for metrics retention
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
            
            # Calculate stats for each query
            new_stats = {}
            
            for query_hash, metrics in self.query_metrics.items():
                # Filter out old metrics
                recent_metrics = [m for m in metrics if m["timestamp"] >= cutoff_time]
                
                # Update metrics list (remove old ones)
                self.query_metrics[query_hash] = recent_metrics
                
                # Skip if no metrics
                if not recent_metrics:
                    continue
                
                # Calculate statistics
                durations = [m["duration_ms"] for m in recent_metrics]
                success_flags = [m["success"] for m in recent_metrics]
                
                # Basic stats
                count = len(recent_metrics)
                avg_duration = sum(durations) / count if count > 0 else 0
                min_duration = min(durations) if durations else 0
                max_duration = max(durations) if durations else 0
                
                # Error stats
                error_count = sum(1 for success in success_flags if not success)
                error_rate = (error_count / count) * 100 if count > 0 else 0
                
                # Calculate percentiles
                percentile_values = {}
                if durations:
                    sorted_durations = sorted(durations)
                    for p in percentiles:
                        idx = int((p / 100) * count)
                        percentile_values[str(p)] = sorted_durations[min(idx, count - 1)]
                
                # Get server-specific stats
                server_stats = defaultdict(list)
                for metric in recent_metrics:
                    server_stats[metric["server_alias"]].append(metric)
                
                servers = []
                for server_alias, server_metrics in server_stats.items():
                    server_durations = [m["duration_ms"] for m in server_metrics]
                    server_success_flags = [m["success"] for m in server_metrics]
                    
                    server_count = len(server_metrics)
                    server_avg_duration = sum(server_durations) / server_count if server_count > 0 else 0
                    server_error_count = sum(1 for success in server_success_flags if not success)
                    server_error_rate = (server_error_count / server_count) * 100 if server_count > 0 else 0
                    
                    servers.append({
                        "server_alias": server_alias,
                        "count": server_count,
                        "avg_duration_ms": server_avg_duration,
                        "error_count": server_error_count,
                        "error_rate": server_error_rate
                    })
                
                # Create stats object
                stats = {
                    "query_hash": query_hash,
                    "query_text": recent_metrics[0]["query"],
                    "count": count,
                    "avg_duration_ms": avg_duration,
                    "min_duration_ms": min_duration,
                    "max_duration_ms": max_duration,
                    "error_count": error_count,
                    "error_rate": error_rate,
                    "percentiles": percentile_values,
                    "servers": servers,
                    "is_slow": avg_duration > self.slow_query_threshold_ms
                }
                
                new_stats[query_hash] = stats
            
            # Update stats
            self.query_stats = new_stats
            self.query_stats_refresh_time = datetime.utcnow()
    
    def _metrics_export_loop(self):
        """Background thread for exporting metrics to disk"""
        while self.running:
            try:
                # Export metrics
                self._export_metrics()
                
                # Sleep until next export
                time.sleep(self.metrics_export_interval)
                
            except Exception as e:
                logger.error(f"Error exporting metrics: {str(e)}")
                time.sleep(60)  # Retry after delay on error
    
    def _cleanup_loop(self):
        """Background thread for cleaning up old metrics"""
        while self.running:
            try:
                # Clean up old metrics
                self._cleanup_old_metrics()
                
                # Sleep for a while (no need to run frequently)
                time.sleep(3600)  # Once per hour
                
            except Exception as e:
                logger.error(f"Error cleaning up metrics: {str(e)}")
                time.sleep(60)  # Retry after delay on error
    
    def _export_metrics(self):
        """Export metrics to disk"""
        if not self.metrics_export_enabled:
            return
        
        # Ensure export directory exists
        export_dir = os.path.dirname(self.metrics_export_path)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        
        # Get latest stats
        self._refresh_endpoint_stats()
        self._refresh_query_stats()
        
        # Create export data
        export_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": self.endpoint_stats,
            "queries": self.query_stats
        }
        
        # Write to file
        try:
            with open(self.metrics_export_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported performance metrics to {self.metrics_export_path}")
        except Exception as e:
            logger.error(f"Error writing metrics export file: {str(e)}")
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics based on retention policy"""
        with self.lock:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
            
            # Clean up endpoint metrics
            for key, metrics in list(self.endpoint_metrics.items()):
                # Filter out old metrics
                self.endpoint_metrics[key] = [m for m in metrics if m["timestamp"] >= cutoff_time]
                
                # Remove empty entries
                if not self.endpoint_metrics[key]:
                    del self.endpoint_metrics[key]
            
            # Clean up query metrics
            for key, metrics in list(self.query_metrics.items()):
                # Filter out old metrics
                self.query_metrics[key] = [m for m in metrics if m["timestamp"] >= cutoff_time]
                
                # Remove empty entries
                if not self.query_metrics[key]:
                    del self.query_metrics[key]
            
            logger.info(f"Cleaned up old metrics (retention: {self.retention_hours} hours)")

def monitor_endpoint(endpoint_function):
    """
    Decorator for monitoring API endpoint performance
    
    Args:
        endpoint_function: The API endpoint function to monitor
        
    Returns:
        Wrapped function with performance monitoring
    """
    @wraps(endpoint_function)
    async def wrapper(*args, **kwargs):
        # Get performance monitor
        monitor = performance_monitor
        
        # Skip if monitoring is disabled
        if not monitor.enabled:
            return await endpoint_function(*args, **kwargs)
        
        # Get request from kwargs or args
        request = kwargs.get("request")
        if request is None:
            for arg in args:
                if hasattr(arg, "method") and hasattr(arg, "url"):
                    request = arg
                    break
        
        # Skip if no request found
        if request is None:
            return await endpoint_function(*args, **kwargs)
        
        # Start timer
        start_time = time.time()
        
        # Extract user ID if available
        user_id = None
        if hasattr(request, "state") and hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            user_id = request.state.user.id
        
        try:
            # Call original endpoint
            response = await endpoint_function(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            monitor.record_endpoint_metrics(
                path=str(request.url.path),
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics (with error)
            monitor.record_endpoint_metrics(
                path=str(request.url.path),
                method=request.method,
                status_code=500,  # Assume 500 for exceptions
                duration_ms=duration_ms,
                user_id=user_id,
                metadata={"error": str(e)}
            )
            
            # Re-raise exception
            raise
    
    return wrapper

# Create singleton instance
performance_monitor = PerformanceMonitor()

# Son güncelleme: 2025-05-20 11:18:07
# Güncelleyen: Teeksss