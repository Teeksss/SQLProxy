"""
System API endpoints for SQL Proxy

This module provides API endpoints for monitoring system status and health.

Last updated: 2025-05-21 07:07:17
Updated by: Teeksss
"""

import logging
import os
import platform
import psutil
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
import sqlalchemy
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_current_user_admin, get_db
from app.models.user import User
from app.db.session import engine
from app.services.vault_service import vault_service
from app.services.cache_service import cache_service
from app.services.scheduler_service import scheduler_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get system status and health information
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        System status information
    """
    try:
        # Start time
        start_time = time.time()
        
        # Get service statuses
        services = await get_service_statuses(db)
        
        # Get resource usage
        resources = await get_resource_usage()
        
        # Get recent activity
        recent_activity = await get_recent_activity(db)
        
        # Response time
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if all(s["status"] == "healthy" for s in services) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION if hasattr(settings, 'VERSION') else "1.0.0",
            "services": services,
            "resources": resources,
            "recent_activity": recent_activity,
            "response_time": round(response_time * 1000)  # ms
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

@router.get("/health")
async def get_health_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get system health check
    
    Args:
        db: Database session
        
    Returns:
        System health status
    """
    try:
        # Check database connection
        db_status = "healthy"
        db_error = None
        try:
            # Execute simple query
            db.execute(sqlalchemy.text("SELECT 1"))
        except Exception as e:
            db_status = "error"
            db_error = str(e)
        
        # Check cache connection
        cache_status = "healthy" if cache_service.redis else "error"
        
        # Overall status
        status = "healthy" if db_status == "healthy" and cache_status == "healthy" else "error"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": {
                    "status": db_status,
                    "error": db_error
                },
                "cache": {
                    "status": cache_status
                }
            }
        }
    except Exception as e:
        logger.error(f"Error checking health: {e}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/metrics")
async def get_system_metrics(
    timeframe: str = Query("1h", description="Timeframe for metrics (1h, 24h, 7d)"),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Get system metrics
    
    Args:
        timeframe: Timeframe for metrics
        current_user: Current authenticated admin user
        
    Returns:
        System metrics
    """
    try:
        # Convert timeframe to hours
        hours = 1
        if timeframe == "24h":
            hours = 24
        elif timeframe == "7d":
            hours = 168
        
        # Generate mock time-series data for demo purposes
        # In a real implementation, this would come from a time-series database or monitoring service
        now = datetime.utcnow()
        timestamps = []
        cpu_values = []
        memory_values = []
        disk_values = []
        network_values = []
        
        points = min(hours * 4, 100)  # 4 points per hour, max 100 points
        interval = hours * 3600 / points
        
        for i in range(points):
            point_time = now - timedelta(seconds=interval * (points - i - 1))
            timestamps.append(point_time.isoformat())
            
            # Generate semi-random values with some trend
            cpu = 50 + 30 * ((i / points) ** 2) + (i % 5) * 2
            memory = 40 + 20 * (i / points) + (i % 7) * 1.5
            disk = 45 + 5 * (i / points) + (i % 3)
            network = 30 + 15 * ((i / points) ** 0.5) + (i % 10) * 2
            
            cpu_values.append(min(95, max(10, cpu)))
            memory_values.append(min(90, max(20, memory)))
            disk_values.append(min(80, max(30, disk)))
            network_values.append(min(80, max(10, network)))
        
        # Create resource time series
        resources = []
        for i in range(points):
            resources.append({
                "timestamp": timestamps[i],
                "cpu": cpu_values[i],
                "memory": memory_values[i],
                "disk": disk_values[i],
                "network": network_values[i]
            })
        
        # Get current resource usage
        current_resources = await get_resource_usage()
        
        # Get service statuses
        services = await get_service_statuses(None)
        
        # Get queries metrics
        # In a real implementation, this would come from query history
        queries = {
            "total": 157,
            "succeeded": 143,
            "failed": 14,
            "avgExecutionTime": 1250
        }
        
        # Get storage metrics
        storage = {
            "total": 1024 * 1024 * 1024 * 100,  # 100 GB
            "used": 1024 * 1024 * 1024 * 45,    # 45 GB
            "free": 1024 * 1024 * 1024 * 55     # 55 GB
        }
        
        # Get alerts
        alerts = {
            "critical": 0,
            "warning": 2,
            "info": 5
        }
        
        return {
            "resources": resources,
            "current": current_resources,
            "services": services,
            "queries": queries,
            "storage": storage,
            "alerts": alerts,
            "timeframe": timeframe
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting system metrics: {str(e)}")

@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query(None, description="Log level filter"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Get system logs
    
    Args:
        level: Log level filter
        limit: Maximum number of logs to return
        current_user: Current authenticated admin user
        
    Returns:
        System logs
    """
    try:
        # In a real implementation, this would retrieve logs from log files or a logging service
        # Here we'll return mock data
        logs = []
        
        # Define mock log levels and messages
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        log_messages = [
            "Application started",
            "User login: admin",
            "Database query execution completed",
            "PowerBI refresh scheduled",
            "Connection to server timed out",
            "Invalid authentication attempt",
            "Cache miss for query result",
            "System configuration updated",
            "Periodic maintenance task started",
            "Background job completed"
        ]
        
        # Generate mock logs
        now = datetime.utcnow()
        for i in range(min(limit, 200)):
            timestamp = now - timedelta(minutes=i * 15)
            log_level = log_levels[i % len(log_levels)]
            
            if level and log_level != level.upper():
                continue
            
            log_message = log_messages[i % len(log_messages)]
            
            logs.append({
                "timestamp": timestamp.isoformat(),
                "level": log_level,
                "message": log_message,
                "source": "SQL Proxy Backend",
                "component": ["API", "Database", "Cache", "Scheduler", "Auth"][i % 5]
            })
        
        return {
            "logs": logs,
            "total": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting system logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting system logs: {str(e)}")

async def get_service_statuses(db: Optional[Session]) -> List[Dict[str, Any]]:
    """
    Get status of system services
    
    Args:
        db: Optional database session
        
    Returns:
        List of service statuses
    """
    services = []
    
    # Database service
    db_status = "healthy"
    db_response_time = 0
    if db:
        try:
            start_time = time.time()
            db.execute(sqlalchemy.text("SELECT 1"))
            db_response_time = (time.time() - start_time) * 1000  # ms
        except Exception as e:
            db_status = "error"
            logger.error(f"Database health check failed: {e}", exc_info=True)
    
    services.append({
        "id": "db",
        "name": "Database Service",
        "type": "database",
        "status": db_status,
        "lastChecked": datetime.utcnow().isoformat(),
        "metrics": {
            "responseTime": round(db_response_time, 2)
        }
    })
    
    # Cache service
    cache_status = "unknown"
    cache_response_time = 0
    try:
        start_time = time.time()
        if cache_service.redis:
            await cache_service.redis.ping()
            cache_status = "healthy"
        else:
            cache_status = "error"
        cache_response_time = (time.time() - start_time) * 1000  # ms
    except Exception as e:
        cache_status = "error"
        logger.error(f"Cache health check failed: {e}", exc_info=True)
    
    services.append({
        "id": "cache",
        "name": "Cache Service",
        "type": "cache",
        "status": cache_status,
        "lastChecked": datetime.utcnow().isoformat(),
        "metrics": {
            "responseTime": round(cache_response_time, 2)
        }
    })
    
    # Scheduler service
    scheduler_status = "healthy" if scheduler_service.scheduler and scheduler_service.scheduler.running else "error"
    
    services.append({
        "id": "scheduler",
        "name": "Scheduler Service",
        "type": "scheduler",
        "status": scheduler_status,
        "lastChecked": datetime.utcnow().isoformat(),
        "metrics": {
            "activeJobs": len(scheduler_service.active_jobs) if scheduler_service.scheduler else 0
        }
    })
    
    # Vault service
    vault_status = "healthy" if vault_service.is_enabled() else "warning"
    
    services.append({
        "id": "vault",
        "name": "Vault Service",
        "type": "vault",
        "status": vault_status,
        "lastChecked": datetime.utcnow().isoformat(),
        "details": "Vault integration is not enabled" if not vault_service.is_enabled() else None
    })
    
    # PowerBI API service
    # In a real implementation, this would check the PowerBI API status
    services.append({
        "id": "powerbi",
        "name": "PowerBI Integration",
        "type": "powerbi",
        "status": "healthy",
        "lastChecked": datetime.utcnow().isoformat()
    })
    
    return services

async def get_resource_usage() -> Dict[str, float]:
    """
    Get system resource usage
    
    Returns:
        Resource usage metrics
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network usage (just a placeholder, actual implementation would monitor network)
        network_percent = 50.0
        
        return {
            "cpu": cpu_percent,
            "memory": memory_percent,
            "disk": disk_percent,
            "network": network_percent
        }
    except Exception as e:
        logger.error(f"Error getting resource usage: {e}", exc_info=True)
        return {
            "cpu": 0,
            "memory": 0,
            "disk": 0,
            "network": 0
        }

async def get_recent_activity(db: Session) -> List[Dict[str, Any]]:
    """
    Get recent system activity
    
    Args:
        db: Database session
        
    Returns:
        Recent activity events
    """
    try:
        # In a real implementation, this would query the audit log
        # For now, return mock data
        now = datetime.utcnow()
        
        activities = [
            {
                "title": "PowerBI Dataset Refresh",
                "description": "Sales Analysis dataset was refreshed successfully",
                "type": "powerbi",
                "timestamp": (now - timedelta(minutes=5)).isoformat()
            },
            {
                "title": "Server Connection",
                "description": "Connected to SQL Server 'Production DB'",
                "type": "database",
                "timestamp": (now - timedelta(minutes=15)).isoformat()
            },
            {
                "title": "User Login",
                "description": "User 'admin' logged in successfully",
                "type": "security",
                "timestamp": (now - timedelta(minutes=30)).isoformat()
            },
            {
                "title": "Scheduled Query",
                "description": "Executed scheduled query 'Daily Sales Report'",
                "type": "database",
                "timestamp": (now - timedelta(hours=1)).isoformat()
            },
            {
                "title": "System Configuration",
                "description": "Cache configuration updated",
                "type": "system",
                "timestamp": (now - timedelta(hours=2)).isoformat()
            }
        ]
        
        return activities
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}", exc_info=True)
        return []

# Son güncelleme: 2025-05-21 07:07:17
# Güncelleyen: Teeksss