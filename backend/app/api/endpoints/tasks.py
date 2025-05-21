"""
Tasks API endpoints for SQL Proxy

This module provides API endpoints for managing scheduled tasks
and background jobs.

Last updated: 2025-05-21 05:32:06
Updated by: Teeksss
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from app.api.deps import get_current_user_admin
from app.models.user import User
from app.core.scheduled_tasks import (
    schedule_task,
    remove_task,
    get_scheduled_tasks
)
from app.schemas.tasks import (
    TaskCreate,
    TaskResponse,
    TaskListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    List all scheduled tasks
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        List of tasks
    """
    try:
        tasks = get_scheduled_tasks()
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error listing tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing tasks: {str(e)}")

@router.post("", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Create a new scheduled task
    
    Args:
        task: Task creation data
        current_user: Current authenticated admin user
        
    Returns:
        Created task details
    """
    try:
        # Parse task function based on task type
        task_func = None
        
        if task.task_type == "backup":
            import asyncio
            from app.services.backup_service import backup_service
            
            async def run_backup():
                await backup_service.create_backup(
                    backup_type=task.parameters.get("backup_type", "full"),
                    description=task.parameters.get("description", "Scheduled backup"),
                    include_queries=task.parameters.get("include_queries", True)
                )
            
            task_func = lambda: asyncio.run(run_backup())
        elif task.task_type == "metrics_export":
            from app.utils.performance_analyzer import export_performance_metrics
            task_func = export_performance_metrics
        elif task.task_type == "metrics_reset":
            from app.utils.performance_analyzer import reset_performance_metrics
            task_func = reset_performance_metrics
        elif task.task_type == "backup_cleanup":
            import asyncio
            from app.services.backup_service import backup_service
            
            async def cleanup_backups():
                await backup_service.cleanup_old_backups(
                    retention_days=task.parameters.get("retention_days")
                )
            
            task_func = lambda: asyncio.run(cleanup_backups())
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported task type: {task.task_type}")
        
        # Determine scheduling parameters
        interval_hours = task.interval_hours
        interval_minutes = task.interval_minutes
        interval_seconds = task.interval_seconds
        first_run = datetime.fromisoformat(task.first_run) if task.first_run else None
        run_at = task.run_at
        run_daily = task.run_daily
        
        # Schedule the task
        success = schedule_task(
            task_id=task.task_id,
            task_func=task_func,
            interval_hours=interval_hours,
            interval_minutes=interval_minutes,
            interval_seconds=interval_seconds,
            first_run=first_run,
            run_at=run_at,
            run_daily=run_daily
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to schedule task")
        
        # Get the scheduled task
        tasks = get_scheduled_tasks()
        for t in tasks:
            if t["id"] == task.task_id:
                return {"task": t}
        
        raise HTTPException(status_code=404, detail="Task not found after scheduling")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Delete a scheduled task
    
    Args:
        task_id: Task ID
        current_user: Current authenticated admin user
        
    Returns:
        Success message
    """
    try:
        success = remove_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
        return {"message": f"Task deleted: {task_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@router.post("/{task_id}/run-now")
async def run_task_now(
    task_id: str,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Run a scheduled task immediately
    
    Args:
        task_id: Task ID
        current_user: Current authenticated admin user
        
    Returns:
        Success message
    """
    try:
        # Get the scheduled tasks
        tasks = get_scheduled_tasks()
        
        # Find the task with the specified ID
        task_found = False
        
        for task in tasks:
            if task["id"] == task_id:
                task_found = True
                break
        
        if not task_found:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
        # Reschedule the task to run immediately
        import schedule
        
        task_jobs = [job for job in schedule.get_jobs() if task_id in job.tags]
        
        if not task_jobs:
            raise HTTPException(status_code=404, detail=f"Task not found in scheduler: {task_id}")
        
        task_job = task_jobs[0]
        
        # Run the job
        task_job.run()
        
        return {"message": f"Task executed: {task_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error running task: {str(e)}")

# Son güncelleme: 2025-05-21 05:32:06
# Güncelleyen: Teeksss