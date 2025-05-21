"""
Scheduled Tasks for SQL Proxy

This module provides functionality for scheduling and executing
recurring tasks such as backups, metrics collection, and maintenance.

Last updated: 2025-05-21 05:32:06
Updated by: Teeksss
"""

import logging
import threading
import time
import asyncio
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Awaitable

from app.core.config import settings
from app.services.backup_service import backup_service
from app.utils.performance_analyzer import reset_performance_metrics, export_performance_metrics
from app.services.prometheus_client import get_prometheus_metrics, push_metrics_to_gateway

logger = logging.getLogger(__name__)

# Dictionary to track scheduled tasks
_scheduled_tasks = {}

# Thread-safe lock for tasks dictionary
_tasks_lock = threading.Lock()

# Event to signal shutdown
_shutdown_event = threading.Event()

def start_scheduler():
    """Start the scheduler thread"""
    if not settings.SCHEDULED_TASKS_ENABLED:
        logger.info("Scheduled tasks are disabled")
        return
    
    # Create scheduler thread
    scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    scheduler_thread.start()
    
    logger.info("Scheduler started")
    
    # Initialize default scheduled tasks
    _initialize_default_tasks()

def stop_scheduler():
    """Stop the scheduler thread"""
    _shutdown_event.set()
    logger.info("Scheduler stopping...")

def _scheduler_loop():
    """Main scheduler loop"""
    while not _shutdown_event.is_set():
        try:
            # Run pending tasks
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)
        
        # Sleep for a bit to avoid high CPU usage
        time.sleep(1)

def _initialize_default_tasks():
    """Initialize default scheduled tasks"""
    # Schedule automatic backups if enabled
    if settings.AUTOMATIC_BACKUPS_ENABLED:
        # Schedule full backup
        schedule_task(
            "full_backup",
            lambda: asyncio.run(_run_backup("full", "Scheduled full backup")),
            interval_hours=settings.FULL_BACKUP_INTERVAL_HOURS,
            first_run=datetime.utcnow() + timedelta(minutes=5)
        )
        
        # Schedule incremental backup if enabled
        if settings.INCREMENTAL_BACKUPS_ENABLED:
            schedule_task(
                "incremental_backup",
                lambda: asyncio.run(_run_backup("incremental", "Scheduled incremental backup")),
                interval_hours=settings.INCREMENTAL_BACKUP_INTERVAL_HOURS,
                first_run=datetime.utcnow() + timedelta(minutes=30)
            )
        
        # Schedule backup cleanup
        schedule_task(
            "backup_cleanup",
            lambda: asyncio.run(_cleanup_backups()),
            interval_hours=24,
            first_run=datetime.utcnow() + timedelta(hours=1)
        )
    
    # Schedule metrics export if enabled
    if settings.PERFORMANCE_METRICS_EXPORT_ENABLED:
        schedule_task(
            "metrics_export",
            export_performance_metrics,
            interval_hours=settings.PERFORMANCE_METRICS_EXPORT_INTERVAL / 3600
        )
    
    # Schedule metrics reset
    schedule_task(
        "metrics_reset",
        reset_performance_metrics,
        interval_hours=24,
        first_run=datetime.utcnow().replace(hour=0, minute=0, second=0) + timedelta(days=1)
    )
    
    # Schedule Prometheus metrics push if enabled
    if settings.METRICS_ENABLED and settings.METRICS_PUSH_GATEWAY_ENABLED:
        schedule_task(
            "prometheus_push",
            push_metrics_to_gateway,
            interval_minutes=settings.METRICS_PUSH_INTERVAL_SECONDS / 60
        )
    
    logger.info("Default scheduled tasks initialized")

async def _run_backup(backup_type: str, description: str):
    """
    Run a backup
    
    Args:
        backup_type: Type of backup (full or incremental)
        description: Backup description
    """
    try:
        logger.info(f"Starting {backup_type} backup: {description}")
        backup = await backup_service.create_backup(
            backup_type=backup_type,
            description=description,
            include_queries=True
        )
        
        if backup:
            logger.info(f"Backup completed successfully: {backup.backup_id}")
        else:
            logger.error(f"Backup failed: {backup_type} - {description}")
    except Exception as e:
        logger.error(f"Error running backup: {e}", exc_info=True)

async def _cleanup_backups():
    """Clean up old backups"""
    try:
        logger.info("Starting backup cleanup")
        deleted_count = await backup_service.cleanup_old_backups()
        logger.info(f"Backup cleanup completed: {deleted_count} backups deleted")
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}", exc_info=True)

def schedule_task(
    task_id: str,
    task_func: Callable,
    interval_hours: Optional[float] = None,
    interval_minutes: Optional[float] = None,
    interval_seconds: Optional[float] = None,
    first_run: Optional[datetime] = None,
    run_at: Optional[str] = None,
    run_daily: bool = False
) -> bool:
    """
    Schedule a task
    
    Args:
        task_id: Unique identifier for the task
        task_func: Function to call when task runs
        interval_hours: Run task every X hours
        interval_minutes: Run task every X minutes
        interval_seconds: Run task every X seconds
        first_run: When to run the task first
        run_at: Time to run the task daily (HH:MM)
        run_daily: Whether to run the task daily
        
    Returns:
        Success flag
    """
    with _tasks_lock:
        # Remove existing task with the same ID
        if task_id in _scheduled_tasks:
            remove_task(task_id)
        
        # Create the task based on scheduling options
        job = None
        
        if interval_hours is not None:
            job = schedule.every(interval_hours).hours.do(task_func)
        elif interval_minutes is not None:
            job = schedule.every(interval_minutes).minutes.do(task_func)
        elif interval_seconds is not None:
            job = schedule.every(interval_seconds).seconds.do(task_func)
        elif run_daily and run_at:
            hour, minute = map(int, run_at.split(':'))
            job = schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(task_func)
        else:
            logger.error(f"Invalid scheduling options for task {task_id}")
            return False
        
        # Schedule first run if specified
        if first_run:
            job.next_run = first_run
        
        # Store task
        _scheduled_tasks[task_id] = job
        
        logger.info(f"Task scheduled: {task_id}, next run at {job.next_run}")
        return True

def remove_task(task_id: str) -> bool:
    """
    Remove a scheduled task
    
    Args:
        task_id: Unique identifier for the task
        
    Returns:
        Success flag
    """
    with _tasks_lock:
        if task_id in _scheduled_tasks:
            job = _scheduled_tasks[task_id]
            schedule.cancel_job(job)
            del _scheduled_tasks[task_id]
            logger.info(f"Task removed: {task_id}")
            return True
        
        logger.warning(f"Task not found: {task_id}")
        return False

def get_scheduled_tasks() -> List[Dict[str, Any]]:
    """
    Get a list of all scheduled tasks
    
    Returns:
        List of task information
    """
    with _tasks_lock:
        tasks = []
        
        for task_id, job in _scheduled_tasks.items():
            tasks.append({
                "id": task_id,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "interval": str(job.interval) if hasattr(job, 'interval') else None,
                "tags": list(job.tags) if job.tags else []
            })
        
        return tasks

# Initialize scheduler on module import
if settings.AUTOMATIC_STARTUP:
    start_scheduler()

# Son güncelleme: 2025-05-21 05:32:06
# Güncelleyen: Teeksss