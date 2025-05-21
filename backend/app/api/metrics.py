"""
Metrics API for SQL Proxy

Provides endpoints for collecting and retrieving metrics data
for monitoring and visualization in Grafana and other tools.

Last updated: 2025-05-20 07:15:16
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, text
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import json

from app.db.session import get_db
from app.auth.jwt import get_current_user, TokenData
from app.models.query import AuditLog
from app.models.anomaly import AnomalyAlert
from app.models.server import ServerConfig
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants for time periods
TIME_PERIODS = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "12h": timedelta(hours=12),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30)
}

@router.get("/query-count", response_model=Dict[str, Any])
async def get_query_count(
    time_period: str = Query("24h", description="Time period (1h, 6h, 12h, 24h, 7d, 30d)"),
    interval: str = Query("1h", description="Interval for data points (1m, 5m, 15m, 1h, 6h, 1d)"),
    server: Optional[str] = Query(None, description="Filter by server"),
    status: Optional[str] = Query(None, description="Filter by status (success, error)"),
    query_type: Optional[str] = Query(None, description="Filter by query type (select, insert, update, delete)"),
    include_totals: bool = Query(True, description="Include total counts"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get query count metrics over time
    
    Returns the number of queries executed over time for visualization in Grafana
    """
    # Validate time period
    if time_period not in TIME_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: {', '.join(TIME_PERIODS.keys())}"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    # Build SQL query for the metrics
    # This uses raw SQL for better performance and flexibility with time series grouping
    
    # Map interval to SQL interval
    sql_interval = {
        "1m": "1 minute",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day"
    }.get(interval, "1 hour")
    
    # Start building the query
    base_query = """
    SELECT
        time_bucket(:interval, created_at) AS time,
        COUNT(*) AS count
    FROM
        audit_logs
    WHERE
        created_at BETWEEN :start_time AND :end_time
    """
    
    # Add filters
    filters = []
    params = {
        "interval": sql_interval,
        "start_time": start_time,
        "end_time": end_time
    }
    
    if server:
        filters.append("target_server = :server")
        params["server"] = server
    
    if status:
        if status.lower() == "success":
            filters.append("execution_status = 'success'")
        elif status.lower() == "error":
            filters.append("execution_status != 'success'")
    
    if query_type:
        filters.append("LOWER(query_type) = :query_type")
        params["query_type"] = query_type.lower()
    
    if filters:
        base_query += " AND " + " AND ".join(filters)
    
    # Add group by and order by
    base_query += """
    GROUP BY
        time
    ORDER BY
        time
    """
    
    # Execute the query
    try:
        result = db.execute(text(base_query), params).fetchall()
        
        # Format the result
        time_series = [
            {
                "time": entry[0].isoformat(),
                "count": entry[1]
            }
            for entry in result
        ]
        
        response = {
            "time_series": time_series,
            "interval": interval,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        # Add totals if requested
        if include_totals:
            # Build total query
            total_query = """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) AS error_count
            FROM
                audit_logs
            WHERE
                created_at BETWEEN :start_time AND :end_time
            """
            
            if filters:
                total_query += " AND " + " AND ".join(filters)
            
            # Execute total query
            total_result = db.execute(text(total_query), params).fetchone()
            
            response["totals"] = {
                "total": total_result[0],
                "success": total_result[1],
                "error": total_result[2],
                "error_rate": round(total_result[2] / total_result[0] * 100, 2) if total_result[0] > 0 else 0
            }
        
        return response
    
    except Exception as e:
        logger.error(f"Error fetching query count metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )

@router.get("/execution-time", response_model=Dict[str, Any])
async def get_execution_time(
    time_period: str = Query("24h", description="Time period (1h, 6h, 12h, 24h, 7d, 30d)"),
    interval: str = Query("1h", description="Interval for data points (1m, 5m, 15m, 1h, 6h, 1d)"),
    server: Optional[str] = Query(None, description="Filter by server"),
    query_type: Optional[str] = Query(None, description="Filter by query type (select, insert, update, delete)"),
    percentile: Optional[int] = Query(95, description="Percentile (50, 75, 90, 95, 99)"),
    include_totals: bool = Query(True, description="Include total stats"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get query execution time metrics over time
    
    Returns execution time statistics over time for visualization in Grafana
    """
    # Validate time period
    if time_period not in TIME_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: {', '.join(TIME_PERIODS.keys())}"
        )
    
    # Validate percentile
    if percentile not in [50, 75, 90, 95, 99]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid percentile: {percentile}. Valid options are: 50, 75, 90, 95, 99"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    # Map interval to SQL interval
    sql_interval = {
        "1m": "1 minute",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day"
    }.get(interval, "1 hour")
    
    # Start building the query
    base_query = f"""
    SELECT
        time_bucket(:interval, created_at) AS time,
        AVG(execution_time_ms) AS avg_time,
        MAX(execution_time_ms) AS max_time,
        MIN(execution_time_ms) AS min_time,
        percentile_cont({percentile/100.0}) WITHIN GROUP (ORDER BY execution_time_ms) AS p{percentile}_time
    FROM
        audit_logs
    WHERE
        created_at BETWEEN :start_time AND :end_time
        AND execution_status = 'success'
        AND execution_time_ms IS NOT NULL
    """
    
    # Add filters
    filters = []
    params = {
        "interval": sql_interval,
        "start_time": start_time,
        "end_time": end_time
    }
    
    if server:
        filters.append("target_server = :server")
        params["server"] = server
    
    if query_type:
        filters.append("LOWER(query_type) = :query_type")
        params["query_type"] = query_type.lower()
    
    if filters:
        base_query += " AND " + " AND ".join(filters)
    
    # Add group by and order by
    base_query += """
    GROUP BY
        time
    ORDER BY
        time
    """
    
    # Execute the query
    try:
        result = db.execute(text(base_query), params).fetchall()
        
        # Format the result
        time_series = [
            {
                "time": entry[0].isoformat(),
                "avg_time": round(entry[1], 2) if entry[1] is not None else None,
                "max_time": entry[2],
                "min_time": entry[3],
                f"p{percentile}_time": round(entry[4], 2) if entry[4] is not None else None
            }
            for entry in result
        ]
        
        response = {
            "time_series": time_series,
            "interval": interval,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "percentile": percentile
        }
        
        # Add totals if requested
        if include_totals:
            # Build total query
            total_query = f"""
            SELECT
                AVG(execution_time_ms) AS avg_time,
                MAX(execution_time_ms) AS max_time,
                MIN(execution_time_ms) AS min_time,
                percentile_cont({percentile/100.0}) WITHIN GROUP (ORDER BY execution_time_ms) AS p{percentile}_time
            FROM
                audit_logs
            WHERE
                created_at BETWEEN :start_time AND :end_time
                AND execution_status = 'success'
                AND execution_time_ms IS NOT NULL
            """
            
            if filters:
                total_query += " AND " + " AND ".join(filters)
            
            # Execute total query
            total_result = db.execute(text(total_query), params).fetchone()
            
            response["totals"] = {
                "avg_time": round(total_result[0], 2) if total_result[0] is not None else None,
                "max_time": total_result[1],
                "min_time": total_result[2],
                f"p{percentile}_time": round(total_result[3], 2) if total_result[3] is not None else None
            }
        
        return response
    
    except Exception as e:
        logger.error(f"Error fetching execution time metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )

@router.get("/query-type-distribution", response_model=Dict[str, Any])
async def get_query_type_distribution(
    time_period: str = Query("24h", description="Time period (1h, 6h, 12h, 24h, 7d, 30d)"),
    server: Optional[str] = Query(None, description="Filter by server"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get query type distribution
    
    Returns the distribution of query types (SELECT, INSERT, UPDATE, DELETE, etc.)
    """
    # Validate time period
    if time_period not in TIME_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: {', '.join(TIME_PERIODS.keys())}"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    # Start building the query
    base_query = """
    SELECT
        LOWER(query_type) AS query_type,
        COUNT(*) AS count
    FROM
        audit_logs
    WHERE
        created_at BETWEEN :start_time AND :end_time
        AND query_type IS NOT NULL
    """
    
    # Add filters
    params = {
        "start_time": start_time,
        "end_time": end_time
    }
    
    if server:
        base_query += " AND target_server = :server"
        params["server"] = server
    
    # Add group by
    base_query += """
    GROUP BY
        LOWER(query_type)
    ORDER BY
        count DESC
    """
    
    # Execute the query
    try:
        result = db.execute(text(base_query), params).fetchall()
        
        # Format the result
        distribution = [
            {
                "query_type": entry[0],
                "count": entry[1]
            }
            for entry in result
        ]
        
        # Calculate percentages
        total_count = sum(item["count"] for item in distribution)
        for item in distribution:
            item["percentage"] = round(item["count"] / total_count * 100, 2) if total_count > 0 else 0
        
        return {
            "distribution": distribution,
            "total_count": total_count,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching query type distribution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )

@router.get("/server-usage", response_model=Dict[str, Any])
async def get_server_usage(
    time_period: str = Query("24h", description="Time period (1h, 6h, 12h, 24h, 7d, 30d)"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get server usage metrics
    
    Returns usage statistics for each server
    """
    # Validate time period
    if time_period not in TIME_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: {', '.join(TIME_PERIODS.keys())}"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    # Start building the query
    base_query = """
    SELECT
        target_server,
        COUNT(*) AS query_count,
        SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) AS success_count,
        SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) AS error_count,
        AVG(execution_time_ms) AS avg_execution_time
    FROM
        audit_logs
    WHERE
        created_at BETWEEN :start_time AND :end_time
        AND target_server IS NOT NULL
    GROUP BY
        target_server
    ORDER BY
        query_count DESC
    """
    
    # Execute the query
    try:
        result = db.execute(
            text(base_query),
            {"start_time": start_time, "end_time": end_time}
        ).fetchall()
        
        # Format the result
        server_usage = [
            {
                "server": entry[0],
                "query_count": entry[1],
                "success_count": entry[2],
                "error_count": entry[3],
                "error_rate": round(entry[3] / entry[1] * 100, 2) if entry[1] > 0 else 0,
                "avg_execution_time": round(entry[4], 2) if entry[4] is not None else None
            }
            for entry in result
        ]
        
        # Calculate percentages
        total_count = sum(item["query_count"] for item in server_usage)
        for item in server_usage:
            item["percentage"] = round(item["query_count"] / total_count * 100, 2) if total_count > 0 else 0
        
        return {
            "server_usage": server_usage,
            "total_count": total_count,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching server usage metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )

@router.get("/user-activity", response_model=Dict[str, Any])
async def get_user_activity(
    time_period: str = Query("24h", description="Time period (1h, 6h, 12h, 24h, 7d, 30d)"),
    limit: int = Query(10, description="Number of users to include"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user activity metrics
    
    Returns activity statistics for top users
    """
    # Only admin users can access this endpoint
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access user activity metrics"
        )
    
    # Validate time period
    if time_period not in TIME_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: {', '.join(TIME_PERIODS.keys())}"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    # Start building the query
    base_query = """
    SELECT
        username,
        user_role,
        COUNT(*) AS query_count,
        SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) AS success_count,
        SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) AS error_count,
        AVG(execution_time_ms) AS avg_execution_time
    FROM
        audit_logs
    WHERE
        created_at BETWEEN :start_time AND :end_time
        AND username IS NOT NULL
    GROUP BY
        username, user_role
    ORDER BY
        query_count DESC
    LIMIT :limit
    """
    
    # Execute the query
    try:
        result = db.execute(
            text(base_query),
            {"start_time": start_time, "end_time": end_time, "limit": limit}
        ).fetchall()
        
        # Format the result
        user_activity = [
            {
                "username": entry[0],
                "role": entry[1],
                "query_count": entry[2],
                "success_count": entry[3],
                "error_count": entry[4],
                "error_rate": round(entry[4] / entry[2] * 100, 2) if entry[2] > 0 else 0,
                "avg_execution_time": round(entry[5], 2) if entry[5] is not None else None
            }
            for entry in result
        ]
        
        # Calculate percentages
        total_count = sum(item["query_count"] for item in user_activity)
        for item in user_activity:
            item["percentage"] = round(item["query_count"] / total_count * 100, 2) if total_count > 0 else 0
        
        return {
            "user_activity": user_activity,
            "total_count": total_count,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching user activity metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )

@router.get("/error-rates", response_model=Dict[str, Any])
async def get_error_rates(
    time_period: str = Query("24h", description="Time period (1h, 6h, 12h, 24h, 7d, 30d)"),
    interval: str = Query("1h", description="Interval for data points (1m, 5m, 15m, 1h, 6h, 1d)"),
    server: Optional[str] = Query(None, description="Filter by server"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get error rate metrics over time
    
    Returns error rates (percentage of failed queries) over time
    """
    # Validate time period
    if time_period not in TIME_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: {', '.join(TIME_PERIODS.keys())}"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    # Map interval to SQL interval
    sql_interval = {
        "1m": "1 minute",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day"
    }.get(interval, "1 hour")
    
    # Start building the query
    base_query = """
    SELECT
        time_bucket(:interval, created_at) AS time,
        COUNT(*) AS total_count,
        SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) AS success_count,
        SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) AS error_count
    FROM
        audit_logs
    WHERE
        created_at BETWEEN :start_time AND :end_time
    """
    
    # Add filters
    params = {
        "interval": sql_interval,
        "start_time": start_time,
        "end_time": end_time
    }
    
    if server:
        base_query += " AND target_server = :server"
        params["server"] = server
    
    # Add group by and order by
    base_query += """
    GROUP BY
        time
    ORDER BY
        time
    """
    
    # Execute the query
    try:
        result = db.execute(text(base_query), params).fetchall()
        
        # Format the result
        time_series = [
            {
                "time": entry[0].isoformat(),
                "total_count": entry[1],
                "success_count": entry[2],
                "error_count": entry[3],
                "error_rate": round(entry[3] / entry[1] * 100, 2) if entry[1] > 0 else 0
            }
            for entry in result
        ]
        
        # Calculate overall error rate
        total_queries = sum(item["total_count"] for item in time_series)
        total_errors = sum(item["error_count"] for item in time_series)
        overall_error_rate = round(total_errors / total_queries * 100, 2) if total_queries > 0 else 0
        
        return {
            "time_series": time_series,
            "interval": interval,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "overall_error_rate": overall_error_rate,
            "total_queries": total_queries,
            "total_errors": total_errors
        }
    
    except Exception as e:
        logger.error(f"Error fetching error rate metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )

@router.get("/anomaly-metrics", response_model=Dict[str, Any])
async def get_anomaly_metrics(
    time_period: str = Query("24h", description="Time period (1h, 6h, 12h, 24h, 7d, 30d)"),
    interval: str = Query("1h", description="Interval for data points (1m, 5m, 15m, 1h, 6h, 1d)"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get anomaly detection metrics
    
    Returns statistics about detected anomalies over time
    """
    # Only admin users can access this endpoint
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access anomaly metrics"
        )
    
    # Validate time period
    if time_period not in TIME_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: {', '.join(TIME_PERIODS.keys())}"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    # Map interval to SQL interval
    sql_interval = {
        "1m": "1 minute",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "1h": "1 hour",
        "6h": "6 hours",
        "1d": "1 day"
    }.get(interval, "1 hour")
    
    # Start building the query
    base_query = """
    SELECT
        time_bucket(:interval, created_at) AS time,
        COUNT(*) AS total_count,
        SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) AS low_count,
        SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) AS medium_count,
        SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) AS high_count,
        SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_count
    FROM
        anomaly_alerts
    WHERE
        created_at BETWEEN :start_time AND :end_time
    GROUP BY
        time
    ORDER BY
        time
    """
    
    # Execute the query
    try:
        result = db.execute(
            text(base_query),
            {
                "interval": sql_interval,
                "start_time": start_time,
                "end_time": end_time
            }
        ).fetchall()
        
        # Format the result
        time_series = [
            {
                "time": entry[0].isoformat(),
                "total": entry[1],
                "low": entry[2],
                "medium": entry[3],
                "high": entry[4],
                "critical": entry[5]
            }
            for entry in result
        ]
        
        # Get anomaly types distribution
        type_query = """
        SELECT
            anomaly_type,
            COUNT(*) AS count
        FROM
            anomaly_alerts
        WHERE
            created_at BETWEEN :start_time AND :end_time
        GROUP BY
            anomaly_type
        ORDER BY
            count DESC
        """
        
        type_result = db.execute(
            text(type_query),
            {"start_time": start_time, "end_time": end_time}
        ).fetchall()
        
        anomaly_types = [
            {
                "type": entry[0],
                "count": entry[1]
            }
            for entry in type_result
        ]
        
        # Calculate totals
        total_anomalies = sum(item["total"] for item in time_series)
        total_by_severity = {
            "low": sum(item["low"] for item in time_series),
            "medium": sum(item["medium"] for item in time_series),
            "high": sum(item["high"] for item in time_series),
            "critical": sum(item["critical"] for item in time_series)
        }
        
        return {
            "time_series": time_series,
            "anomaly_types": anomaly_types,
            "total_anomalies": total_anomalies,
            "total_by_severity": total_by_severity,
            "interval": interval,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching anomaly metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )

@router.get("/performance-dashboard", response_model=Dict[str, Any])
async def get_performance_dashboard(
    time_period: str = Query("1h", description="Time period (1h, 6h, 12h, 24h)"),
    server: Optional[str] = Query(None, description="Filter by server"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time performance dashboard metrics
    
    Returns comprehensive performance metrics for system dashboard
    """
    # Validate time period
    if time_period not in ["1h", "6h", "12h", "24h"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time period: {time_period}. Valid options are: 1h, 6h, 12h, 24h"
        )
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - TIME_PERIODS[time_period]
    
    try:
        # Get query rate (queries per minute)
        query_rate_interval = "1 minute" if time_period == "1h" else "5 minutes"
        query_rate_query = """
        SELECT
            time_bucket(:interval, created_at) AS time,
            COUNT(*) AS count
        FROM
            audit_logs
        WHERE
            created_at BETWEEN :start_time AND :end_time
            {server_filter}
        GROUP BY
            time
        ORDER BY
            time DESC
        LIMIT 30
        """
        
        server_filter = f"AND target_server = :server" if server else ""
        query_rate_query = query_rate_query.format(server_filter=server_filter)
        
        params = {
            "interval": query_rate_interval,
            "start_time": start_time,
            "end_time": end_time
        }
        
        if server:
            params["server"] = server
        
        query_rate_result = db.execute(text(query_rate_query), params).fetchall()
        
        query_rate = [
            {
                "time": entry[0].isoformat(),
                "count": entry[1]
            }
            for entry in query_rate_result
        ]
        
        # Calculate current QPS (queries per second)
        last_minute = end_time - timedelta(minutes=1)
        qps_query = """
        SELECT
            COUNT(*) AS count
        FROM
            audit_logs
        WHERE
            created_at BETWEEN :start_time AND :end_time
            {server_filter}
        """
        
        qps_query = qps_query.format(server_filter=server_filter)
        
        qps_params = {
            "start_time": last_minute,
            "end_time": end_time
        }
        
        if server:
            qps_params["server"] = server
        
        qps_result = db.execute(text(qps_query), qps_params).fetchone()
        current_qps = round(qps_result[0] / 60, 2)
        
        # Get active long-running queries
        long_running_query = """
        SELECT
            id,
            username,
            user_role,
            target_server,
            query_text,
            created_at,
            execution_status
        FROM
            audit_logs
        WHERE
            created_at BETWEEN :start_time AND :end_time
            AND execution_status = 'pending'
            {server_filter}
        ORDER BY
            created_at
        LIMIT 10
        """
        
        long_running_query = long_running_query.format(server_filter=server_filter)
        
        long_running_result = db.execute(text(long_running_query), params).fetchall()
        
        active_queries = [
            {
                "id": entry[0],
                "username": entry[1],
                "role": entry[2],
                "server": entry[3],
                "query": entry[4][:100] + ("..." if len(entry[4]) > 100 else ""),
                "start_time": entry[5].isoformat(),
                "duration_sec": (end_time - entry[5]).total_seconds()
            }
            for entry in long_running_result
        ]
        
        # Get error rate trend
        error_rate_query = """
        SELECT
            time_bucket('5 minutes', created_at) AS time,
            COUNT(*) AS total,
            SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) AS errors,
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    ROUND(SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END)::numeric / COUNT(*)::numeric * 100, 2)
                ELSE 0
            END AS error_rate
        FROM
            audit_logs
        WHERE
            created_at BETWEEN :start_time AND :end_time
            {server_filter}
        GROUP BY
            time
        ORDER BY
            time DESC
        LIMIT 12
        """
        
        error_rate_query = error_rate_query.format(server_filter=server_filter)
        
        error_rate_result = db.execute(text(error_rate_query), params).fetchall()
        
        error_rate_trend = [
            {
                "time": entry[0].isoformat(),
                "total": entry[1],
                "errors": entry[2],
                "error_rate": entry[3]
            }
            for entry in error_rate_result
        ]
        
        # Get recent anomalies
        anomaly_query = """
        SELECT
            id,
            anomaly_type,
            severity,
            username,
            target_server,
            created_at,
            status,
            details
        FROM
            anomaly_alerts
        WHERE
            created_at BETWEEN :start_time AND :end_time
            {server_filter}
        ORDER BY
            created_at DESC
        LIMIT 5
        """
        
        server_anomaly_filter = f"AND target_server = :server" if server else ""
        anomaly_query = anomaly_query.format(server_filter=server_anomaly_filter)
        
        anomaly_params = {
            "start_time": start_time,
            "end_time": end_time
        }
        
        if server:
            anomaly_params["server"] = server
        
        anomaly_result = db.execute(text(anomaly_query), anomaly_params).fetchall()
        
        recent_anomalies = [
            {
                "id": entry[0],
                "type": entry[1],
                "severity": entry[2],
                "username": entry[3],
                "server": entry[4],
                "time": entry[5].isoformat(),
                "status": entry[6],
                "details": entry[7]
            }
            for entry in anomaly_result
        ]
        
        # Return compiled dashboard data
        return {
            "query_rate": query_rate,
            "current_qps": current_qps,
            "active_queries": active_queries,
            "error_rate_trend": error_rate_trend,
            "recent_anomalies": recent_anomalies,
            "time_period": time_period,
            "server": server,
            "timestamp": end_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard metrics: {str(e)}"
        )

# Son güncelleme: 2025-05-20 07:15:16
# Güncelleyen: Teeksss