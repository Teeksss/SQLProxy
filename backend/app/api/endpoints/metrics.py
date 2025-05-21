"""
Metrics API endpoints for SQL Proxy

This module provides API endpoints for retrieving performance metrics
and system monitoring data.

Last updated: 2025-05-21 05:17:27
Updated by: Teeksss
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
import csv
import io
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_current_user_admin
from app.models.user import User
from app.utils.performance_analyzer import (
    get_performance_summary,
    reset_performance_metrics,
    export_performance_metrics,
    analyze_query_performance
)
from app.services.prometheus_client import get_prometheus_metrics

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/performance")
async def get_performance_metrics(
    timeRange: str = Query("24h", description="Time range for metrics (1h, 6h, 24h, 7d, 30d)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance metrics summary
    
    Args:
        timeRange: Time range for metrics
        
    Returns:
        Performance metrics summary
    """
    try:
        summary = get_performance_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")

@router.post("/performance/reset")
async def reset_metrics(
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Reset performance metrics (admin only)
    
    Returns:
        Success message
    """
    try:
        reset_performance_metrics()
        return {"message": "Performance metrics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error resetting metrics: {str(e)}")

@router.get("/performance/export")
async def export_metrics(
    format: str = Query("csv", description="Export format (csv or json)"),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Export performance metrics as CSV or JSON
    
    Args:
        format: Export format (csv or json)
        
    Returns:
        Metrics file as StreamingResponse
    """
    try:
        summary = get_performance_summary()
        
        if format.lower() == "json":
            # Export as JSON
            json_data = json.dumps(summary, indent=2)
            
            return StreamingResponse(
                iter([json_data]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=performance_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
            )
        else:
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["Type", "Name", "Average (ms)", "Median (ms)", "P95 (ms)", "Min (ms)", "Max (ms)", "Count"])
            
            # Write query metrics
            for db_name, db_metrics in summary.get("queries", {}).items():
                writer.writerow([
                    "Database",
                    db_name,
                    round(db_metrics.get("average", 0) * 1000, 2),
                    round(db_metrics.get("median", 0) * 1000, 2),
                    round(db_metrics.get("p95", 0) * 1000, 2),
                    round(db_metrics.get("min", 0) * 1000, 2),
                    round(db_metrics.get("max", 0) * 1000, 2),
                    db_metrics.get("count", 0)
                ])
                
                # Write endpoint metrics
                for endpoint, endpoint_metrics in db_metrics.get("endpoints", {}).items():
                    writer.writerow([
                        "Endpoint",
                        endpoint,
                        round(endpoint_metrics.get("average", 0) * 1000, 2),
                        round(endpoint_metrics.get("median", 0) * 1000, 2),
                        round(endpoint_metrics.get("p95", 0) * 1000, 2),
                        round(endpoint_metrics.get("min", 0) * 1000, 2),
                        round(endpoint_metrics.get("max", 0) * 1000, 2),
                        endpoint_metrics.get("count", 0)
                    ])
            
            # Write API endpoint metrics
            for method, method_metrics in summary.get("endpoints", {}).items():
                writer.writerow([
                    "API Method",
                    method,
                    round(method_metrics.get("average", 0) * 1000, 2),
                    round(method_metrics.get("median", 0) * 1000, 2),
                    round(method_metrics.get("p95", 0) * 1000, 2),
                    round(method_metrics.get("min", 0) * 1000, 2),
                    round(method_metrics.get("max", 0) * 1000, 2),
                    method_metrics.get("count", 0)
                ])
                
                # Write endpoint metrics
                for endpoint, endpoint_metrics in method_metrics.get("endpoints", {}).items():
                    writer.writerow([
                        "API Endpoint",
                        endpoint,
                        round(endpoint_metrics.get("average", 0) * 1000, 2),
                        round(endpoint_metrics.get("median", 0) * 1000, 2),
                        round(endpoint_metrics.get("p95", 0) * 1000, 2),
                        round(endpoint_metrics.get("min", 0) * 1000, 2),
                        round(endpoint_metrics.get("max", 0) * 1000, 2),
                        endpoint_metrics.get("count", 0)
                    ])
            
            return StreamingResponse(
                io.StringIO(output.getvalue()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=performance_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
    except Exception as e:
        logger.error(f"Error exporting performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")

@router.post("/analyze-query")
async def analyze_query(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze SQL query performance
    
    Body:
        query: SQL query to analyze
        parameters: Query parameters (optional)
        serverId: Server ID (optional)
        iterations: Number of iterations (optional)
        
    Returns:
        Query analysis results
    """
    try:
        query = data.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        parameters = data.get("parameters")
        server_id = data.get("serverId")
        iterations = data.get("iterations", 3)
        
        results = analyze_query_performance(
            query=query,
            parameters=parameters,
            database=server_id or "default",
            iterations=iterations
        )
        
        return results
    except Exception as e:
        logger.error(f"Error analyzing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing query: {str(e)}")

@router.get("/system")
async def get_system_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get system metrics
    
    Returns:
        System metrics
    """
    try:
        metrics = {
            "cpu": {
                "usage_percent": 0,
                "cores": 0
            },
            "memory": {
                "total": 0,
                "used": 0,
                "free": 0,
                "usage_percent": 0
            },
            "disk": {
                "total": 0,
                "used": 0,
                "free": 0,
                "usage_percent": 0
            },
            "network": {
                "sent": 0,
                "received": 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Try to get system metrics from psutil if available
        try:
            import psutil
            
            # CPU metrics
            metrics["cpu"]["usage_percent"] = psutil.cpu_percent(interval=0.1)
            metrics["cpu"]["cores"] = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics["memory"]["total"] = memory.total
            metrics["memory"]["used"] = memory.used
            metrics["memory"]["free"] = memory.available
            metrics["memory"]["usage_percent"] = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage("/")
            metrics["disk"]["total"] = disk.total
            metrics["disk"]["used"] = disk.used
            metrics["disk"]["free"] = disk.free
            metrics["disk"]["usage_percent"] = disk.percent
            
            # Network metrics
            net_io = psutil.net_io_counters()
            metrics["network"]["sent"] = net_io.bytes_sent
            metrics["network"]["received"] = net_io.bytes_recv
        except (ImportError, Exception) as e:
            logger.warning(f"Could not get system metrics from psutil: {e}")
        
        # Get Prometheus metrics if enabled
        if hasattr(get_prometheus_metrics, "__call__"):
            try:
                prom_metrics = get_prometheus_metrics()
                metrics["prometheus"] = prom_metrics
            except Exception as e:
                logger.warning(f"Could not get Prometheus metrics: {e}")
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting system metrics: {str(e)}")

@router.get("/query-analytics")
async def get_query_analytics(
    serverId: Optional[str] = None,
    timeRange: str = Query("24h", description="Time range for analytics (1h, 6h, 24h, 7d, 30d)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get query analytics for a specific server
    
    Args:
        serverId: Server ID (optional)
        timeRange: Time range for analytics
        
    Returns:
        Query analytics
    """
    try:
        # Parse time range
        hours = 24
        if timeRange.endswith("h"):
            hours = int(timeRange[:-1])
        elif timeRange.endswith("d"):
            hours = int(timeRange[:-1]) * 24
        
        # Get performance summary
        summary = get_performance_summary()
        
        # Filter by server if provided
        queries = summary.get("queries", {})
        if serverId and serverId in queries:
            queries = {serverId: queries[serverId]}
        
        # Extract common stats
        total_queries = sum(db.get("count", 0) for db in queries.values())
        avg_query_time = sum(db.get("average", 0) for db in queries.values()) / len(queries) if queries else 0
        max_query_time = max((db.get("max", 0) for db in queries.values()), default=0)
        
        # Identify slow queries (>500ms)
        slow_queries = []
        for db_name, db_metrics in queries.items():
            for endpoint, endpoint_metrics in db_metrics.get("endpoints", {}).items():
                if endpoint_metrics.get("max", 0) * 1000 > 500:
                    slow_queries.append({
                        "database": db_name,
                        "endpoint": endpoint,
                        "max_time": endpoint_metrics.get("max", 0) * 1000,
                        "avg_time": endpoint_metrics.get("average", 0) * 1000,
                        "count": endpoint_metrics.get("count", 0)
                    })
        
        # Sort slow queries by max time
        slow_queries.sort(key=lambda x: x["max_time"], reverse=True)
        
        # Prepare results
        results = {
            "total_queries": total_queries,
            "avg_query_time": avg_query_time * 1000,  # Convert to ms
            "max_query_time": max_query_time * 1000,  # Convert to ms
            "slow_queries": slow_queries,
            "query_stats": queries,
            "time_range": {
                "start": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
                "end": datetime.utcnow().isoformat(),
                "hours": hours
            }
        }
        
        return results
    except Exception as e:
        logger.error(f"Error getting query analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting query analytics: {str(e)}")

@router.post("/performance/export-task")
async def schedule_export_metrics(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Schedule export of performance metrics (admin only)
    
    Returns:
        Success message
    """
    try:
        background_tasks.add_task(export_performance_metrics)
        return {"message": "Performance metrics export scheduled"}
    except Exception as e:
        logger.error(f"Error scheduling metrics export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error scheduling export: {str(e)}")

# Son güncelleme: 2025-05-21 05:17:27
# Güncelleyen: Teeksss