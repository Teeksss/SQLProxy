"""
Performance Monitoring API endpoints for SQL Proxy

This module provides API endpoints for monitoring and analyzing
SQL Proxy performance metrics.

Last updated: 2025-05-20 11:18:07
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Any, Optional

from app.performance.monitoring import performance_monitor
from app.metrics.prometheus_client import PrometheusClient
from app.auth.jwt import get_current_user_admin, get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter()

@router.get("/overall")
async def get_overall_statistics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get overall performance statistics
    
    Args:
        current_user: Current user (authenticated)
        
    Returns:
        Overall performance statistics
    """
    if not settings.PERFORMANCE_MONITORING_ENABLED:
        raise HTTPException(status_code=503, detail="Performance monitoring is disabled")
    
    return performance_monitor.get_overall_statistics()

@router.get("/endpoints")
async def get_endpoint_stats(
    path: Optional[str] = None,
    method: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 7 days
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get API endpoint performance statistics
    
    Args:
        path: Filter by path (optional)
        method: Filter by HTTP method (optional)
        hours: Time range in hours
        current_user: Current user (authenticated)
        
    Returns:
        Endpoint performance statistics
    """
    if not settings.PERFORMANCE_MONITORING_ENABLED:
        raise HTTPException(status_code=503, detail="Performance monitoring is disabled")
    
    return performance_monitor.get_endpoint_stats(path, method, hours)

@router.get("/queries")
async def get_query_stats(
    query_hash: Optional[str] = None,
    server_alias: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 7 days
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get database query performance statistics
    
    Args:
        query_hash: Filter by query hash (optional)
        server_alias: Filter by server alias (optional)
        hours: Time range in hours
        current_user: Current user (authenticated)
        
    Returns:
        Query performance statistics
    """
    if not settings.PERFORMANCE_MONITORING_ENABLED:
        raise HTTPException(status_code=503, detail="Performance monitoring is disabled")
    
    return performance_monitor.get_query_stats(query_hash, server_alias, hours)

@router.get("/slow-endpoints")
async def get_slow_endpoints(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get slowest API endpoints
    
    Args:
        limit: Maximum number of endpoints to return
        current_user: Current user (authenticated)
        
    Returns:
        List of slow endpoint statistics
    """
    if not settings.PERFORMANCE_MONITORING_ENABLED:
        raise HTTPException(status_code=503, detail="Performance monitoring is disabled")
    
    return performance_monitor.get_slow_endpoints(limit)

@router.get("/slow-queries")
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get slowest database queries
    
    Args:
        limit: Maximum number of queries to return
        current_user: Current user (authenticated)
        
    Returns:
        List of slow query statistics
    """
    if not settings.PERFORMANCE_MONITORING_ENABLED:
        raise HTTPException(status_code=503, detail="Performance monitoring is disabled")
    
    return performance_monitor.get_slow_queries(limit)

@router.get("/metrics")
async def get_prometheus_metrics(
    current_user: User = Depends(get_current_user_admin)
) -> str:
    """
    Get metrics in Prometheus format
    
    Args:
        current_user: Current user (admin only)
        
    Returns:
        Metrics in Prometheus exposition format
    """
    if not settings.PROMETHEUS_ENABLED:
        raise HTTPException(status_code=503, detail="Prometheus metrics are disabled")
    
    prometheus_client = PrometheusClient()
    return prometheus_client.get_metrics()

# Son güncelleme: 2025-05-20 11:18:07
# Güncelleyen: Teeksss