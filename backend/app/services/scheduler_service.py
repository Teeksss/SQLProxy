"""
Scheduler Service for SQL Proxy

This module provides functionality for scheduling and managing recurring
tasks like PowerBI refreshes and automated SQL queries.

Last updated: 2025-05-21 06:54:19
Updated by: Teeksss
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import uuid
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db, engine
from app.models.user import User
from app.core.config import settings
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Service for scheduling and managing tasks
    
    Provides functionality for scheduling recurring and one-time tasks
    like PowerBI dataset refreshes and automated SQL queries.
    """
    
    def __init__(self):
        """Initialize scheduler service"""
        self.scheduler = None
        self.active_jobs = {}
        self.initialize_scheduler()
    
    def initialize_scheduler(self):
        """Initialize APScheduler"""
        try:
            # Create jobstore
            jobstore = SQLAlchemyJobStore(
                url=settings.SQLALCHEMY_DATABASE_URI,
                tablename='scheduler_jobs'
            )
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores={
                    'default': jobstore
                }
            )
            
            # Add error listener
            self.scheduler.add_listener(
                self._handle_job_error,
                mask=(1 << 0)  # EVENT_JOB_ERROR = 1 << 0
            )
            
            logger.info("Scheduler initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing scheduler: {e}", exc_info=True)
            self.scheduler = None
    
    def start(self):
        """Start scheduler"""
        if not self.scheduler:
            self.initialize_scheduler()
        
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")
    
    async def schedule_job(
        self,
        job_func: Callable,
        job_id: Optional[str] = None,
        trigger: Optional[Union[CronTrigger, IntervalTrigger, DateTrigger]] = None,
        trigger_type: Optional[str] = None,
        trigger_args: Optional[Dict[str, Any]] = None,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        replace_existing: bool = True,
        user_id: Optional[int] = None,
        job_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[str]:
        """
        Schedule a job
        
        Args:
            job_func: Function to execute
            job_id: Optional job ID (generated if not provided)
            trigger: Optional APScheduler trigger
            trigger_type: Optional trigger type ('cron', 'interval', or 'date')
            trigger_args: Optional trigger arguments
            args: Optional positional arguments for job_func
            kwargs: Optional keyword arguments for job_func
            replace_existing: Whether to replace existing job with same ID
            user_id: Optional user ID
            job_type: Optional job type (for categorization)
            entity_id: Optional related entity ID
            entity_type: Optional related entity type
            description: Optional job description
            
        Returns:
            Job ID or None if scheduling failed
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return None
        
        try:
            # Generate job ID if not provided
            if not job_id:
                job_id = str(uuid.uuid4())
            
            # Create trigger if not provided
            if not trigger:
                if not trigger_type or not trigger_args:
                    logger.error("Either trigger or trigger_type+trigger_args must be provided")
                    return None
                
                if trigger_type == 'cron':
                    trigger = CronTrigger(**trigger_args)
                elif trigger_type == 'interval':
                    trigger = IntervalTrigger(**trigger_args)
                elif trigger_type == 'date':
                    trigger = DateTrigger(**trigger_args)
                else:
                    logger.error(f"Invalid trigger_type: {trigger_type}")
                    return None
            
            # Prepare job metadata
            job_kwargs = kwargs or {}
            job_kwargs['_job_id'] = job_id
            job_kwargs['_user_id'] = user_id
            job_kwargs['_job_type'] = job_type
            job_kwargs['_entity_id'] = entity_id
            job_kwargs['_entity_type'] = entity_type
            job_kwargs['_description'] = description
            
            # Add job to scheduler
            self.scheduler.add_job(
                job_func,
                trigger=trigger,
                args=args or [],
                kwargs=job_kwargs,
                id=job_id,
                replace_existing=replace_existing
            )
            
            # Store active job
            self.active_jobs[job_id] = {
                'job_id': job_id,
                'user_id': user_id,
                'job_type': job_type,
                'entity_id': entity_id,
                'entity_type': entity_type,
                'description': description,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Job scheduled successfully: {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Error scheduling job: {e}", exc_info=True)
            return None
    
    async def schedule_powerbi_refresh(
        self,
        dataset_id: str,
        dataset_name: str,
        workspace_id: Optional[str] = None,
        schedule_config: Dict[str, Any] = None,
        user_id: int = None
    ) -> Optional[str]:
        """
        Schedule PowerBI dataset refresh
        
        Args:
            dataset_id: PowerBI dataset ID
            dataset_name: Dataset name
            workspace_id: Optional workspace ID
            schedule_config: Refresh schedule configuration
            user_id: User ID
            
        Returns:
            Job ID or None if scheduling failed
        """
        from app.services.powerbi_service import powerbi_service
        
        if not schedule_config:
            logger.error("Schedule configuration is required")
            return None
        
        refresh_type = schedule_config.get('type', 'daily')
        
        # Create job ID
        job_id = f"powerbi_refresh_{dataset_id}"
        
        # Create trigger based on refresh type
        if refresh_type == 'daily':
            time_str = schedule_config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            trigger = CronTrigger(hour=hour, minute=minute)
            description = f"Daily refresh at {time_str}"
        elif refresh_type == 'weekly':
            day_of_week = schedule_config.get('day', 'mon')
            time_str = schedule_config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
            description = f"Weekly refresh on {day_of_week} at {time_str}"
        elif refresh_type == 'monthly':
            day = schedule_config.get('day', 1)
            time_str = schedule_config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            trigger = CronTrigger(day=day, hour=hour, minute=minute)
            description = f"Monthly refresh on day {day} at {time_str}"
        elif refresh_type == 'hourly':
            minute = schedule_config.get('minute', 0)
            trigger = CronTrigger(minute=minute)
            description = f"Hourly refresh at minute {minute}"
        elif refresh_type == 'interval':
            hours = schedule_config.get('hours', 0)
            minutes = schedule_config.get('minutes', 0)
            seconds = hours * 3600 + minutes * 60
            if seconds < 300:  # Minimum 5 minutes
                seconds = 300
            trigger = IntervalTrigger(seconds=seconds)
            description = f"Refresh every {hours}h {minutes}m"
        else:
            logger.error(f"Invalid refresh type: {refresh_type}")
            return None
        
        # Schedule refresh job
        job_id = await self.schedule_job(
            job_func=self._refresh_powerbi_dataset,
            job_id=job_id,
            trigger=trigger,
            args=[dataset_id, dataset_name, workspace_id],
            user_id=user_id,
            job_type='powerbi_refresh',
            entity_id=dataset_id,
            entity_type='powerbi_dataset',
            description=description,
            replace_existing=True
        )
        
        return job_id
    
    async def schedule_sql_query(
        self,
        query_id: str,
        server_id: str,
        schedule_config: Dict[str, Any] = None,
        user_id: int = None,
        save_results: bool = True,
        export_format: Optional[str] = None
    ) -> Optional[str]:
        """
        Schedule SQL query execution
        
        Args:
            query_id: Query ID
            server_id: Server ID
            schedule_config: Schedule configuration
            user_id: User ID
            save_results: Whether to save results
            export_format: Optional export format
            
        Returns:
            Job ID or None if scheduling failed
        """
        from app.services.query_service import query_service
        
        if not schedule_config:
            logger.error("Schedule configuration is required")
            return None
        
        schedule_type = schedule_config.get('type', 'daily')
        
        # Create job ID
        job_id = f"sql_query_{query_id}"
        
        # Create trigger based on schedule type
        if schedule_type == 'daily':
            time_str = schedule_config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            trigger = CronTrigger(hour=hour, minute=minute)
            description = f"Daily query at {time_str}"
        elif schedule_type == 'weekly':
            day_of_week = schedule_config.get('day', 'mon')
            time_str = schedule_config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
            description = f"Weekly query on {day_of_week} at {time_str}"
        elif schedule_type == 'monthly':
            day = schedule_config.get('day', 1)
            time_str = schedule_config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            trigger = CronTrigger(day=day, hour=hour, minute=minute)
            description = f"Monthly query on day {day} at {time_str}"
        elif schedule_type == 'hourly':
            minute = schedule_config.get('minute', 0)
            trigger = CronTrigger(minute=minute)
            description = f"Hourly query at minute {minute}"
        elif schedule_type == 'interval':
            hours = schedule_config.get('hours', 0)
            minutes = schedule_config.get('minutes', 0)
            seconds = hours * 3600 + minutes * 60
            if seconds < 300:  # Minimum 5 minutes
                seconds = 300
            trigger = IntervalTrigger(seconds=seconds)
            description = f"Query every {hours}h {minutes}m"
        else:
            logger.error(f"Invalid schedule type: {schedule_type}")
            return None
        
        # Schedule query job
        job_id = await self.schedule_job(
            job_func=self._execute_sql_query,
            job_id=job_id,
            trigger=trigger,
            args=[query_id, server_id, save_results, export_format],
            user_id=user_id,
            job_type='sql_query',
            entity_id=query_id,
            entity_type='query',
            description=description,
            replace_existing=True
        )
        
        return job_id
    
    async def get_jobs(
        self,
        user_id: Optional[int] = None,
        job_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get scheduled jobs
        
        Args:
            user_id: Optional user ID filter
            job_type: Optional job type filter
            
        Returns:
            List of jobs
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return []
        
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                # Get job details from scheduler and active_jobs
                job_id = job.id
                job_details = self.active_jobs.get(job_id, {})
                job_user_id = job_details.get('user_id')
                job_job_type = job_details.get('job_type')
                
                # Apply filters
                if user_id is not None and job_user_id != user_id:
                    continue
                if job_type is not None and job_job_type != job_type:
                    continue
                
                # Get next run time
                next_run_time = job.next_run_time
                if next_run_time:
                    next_run_time = next_run_time.isoformat()
                
                # Create job info
                job_info = {
                    'job_id': job_id,
                    'user_id': job_user_id,
                    'job_type': job_job_type,
                    'entity_id': job_details.get('entity_id'),
                    'entity_type': job_details.get('entity_type'),
                    'description': job_details.get('description'),
                    'created_at': job_details.get('created_at'),
                    'next_run_time': next_run_time
                }
                
                jobs.append(job_info)
            
            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs: {e}", exc_info=True)
            return []
    
    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a scheduled job
        
        Args:
            job_id: Job ID
            
        Returns:
            Success status
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            return True
        except Exception as e:
            logger.error(f"Error deleting job: {e}", exc_info=True)
            return False
    
    async def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job
        
        Args:
            job_id: Job ID
            
        Returns:
            Success status
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            self.scheduler.pause_job(job_id)
            return True
        except Exception as e:
            logger.error(f"Error pausing job: {e}", exc_info=True)
            return False
    
    async def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job
        
        Args:
            job_id: Job ID
            
        Returns:
            Success status
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False
        
        try:
            self.scheduler.resume_job(job_id)
            return True
        except Exception as e:
            logger.error(f"Error resuming job: {e}", exc_info=True)
            return False
    
    async def _refresh_powerbi_dataset(
        self,
        dataset_id: str,
        dataset_name: str,
        workspace_id: Optional[str] = None,
        _job_id: Optional[str] = None,
        _user_id: Optional[int] = None,
        **kwargs
    ):
        """
        Execute PowerBI dataset refresh
        
        Args:
            dataset_id: PowerBI dataset ID
            dataset_name: Dataset name
            workspace_id: Optional workspace ID
            _job_id: Job ID
            _user_id: User ID
            **kwargs: Additional arguments
        """
        from app.services.powerbi_service import powerbi_service
        
        logger.info(f"Executing scheduled PowerBI refresh for dataset {dataset_id}")
        
        try:
            # Get database session
            from app.db.session import SessionLocal
            db = SessionLocal()
            
            try:
                # Execute refresh
                result = await powerbi_service.refresh_dataset(
                    dataset_id=dataset_id,
                    workspace_id=workspace_id
                )
                
                status = "completed" if result.get('success', False) else "failed"
                
                # Send notification
                if _user_id:
                    await notification_service.notify_refresh_complete(
                        dataset_id=dataset_id,
                        dataset_name=dataset_name,
                        status=status,
                        user_id=_user_id,
                        db=db
                    )
                
                logger.info(f"Scheduled PowerBI refresh {status} for dataset {dataset_id}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error executing scheduled PowerBI refresh: {e}", exc_info=True)
    
    async def _execute_sql_query(
        self,
        query_id: str,
        server_id: str,
        save_results: bool = True,
        export_format: Optional[str] = None,
        _job_id: Optional[str] = None,
        _user_id: Optional[int] = None,
        **kwargs
    ):
        """
        Execute SQL query
        
        Args:
            query_id: Query ID
            server_id: Server ID
            save_results: Whether to save results
            export_format: Optional export format
            _job_id: Job ID
            _user_id: User ID
            **kwargs: Additional arguments
        """
        from app.services.query_service import query_service
        
        logger.info(f"Executing scheduled SQL query {query_id}")
        
        try:
            # Get database session
            from app.db.session import SessionLocal
            db = SessionLocal()
            
            try:
                # Get query
                query = await query_service.get_query(query_id, db)
                if not query:
                    logger.error(f"Query {query_id} not found")
                    return
                
                # Execute query
                result = await query_service.execute_query(
                    server_id=server_id,
                    sql_text=query.sql_text,
                    user_id=_user_id,
                    db=db,
                    save_history=save_results
                )
                
                status = "completed" if result.get('success', False) else "failed"
                
                # Export results if needed
                if status == "completed" and export_format:
                    await query_service.export_results(
                        result.get('result_id'),
                        export_format,
                        db
                    )
                
                # Send notification
                if _user_id:
                    await notification_service.create_notification(
                        notification={
                            "user_id": _user_id,
                            "title": f"Query {status.capitalize()}",
                            "message": f"Scheduled query '{query.name}' has {status}.",
                            "notification_type": "query_complete",
                            "entity_type": "query",
                            "entity_id": query_id
                        },
                        db=db
                    )
                
                logger.info(f"Scheduled SQL query {status} for query {query_id}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error executing scheduled SQL query: {e}", exc_info=True)
    
    def _handle_job_error(self, event):
        """
        Handle job execution error
        
        Args:
            event: Job event
        """
        job_id = event.job_id
        exception = event.exception
        
        logger.error(f"Error executing job {job_id}: {exception}", exc_info=True)
        
        # Get job details
        job_details = self.active_jobs.get(job_id, {})
        user_id = job_details.get('user_id')
        entity_id = job_details.get('entity_id')
        entity_type = job_details.get('entity_type')
        
        # Send error notification
        if user_id:
            asyncio.create_task(self._send_error_notification(
                user_id=user_id,
                job_id=job_id,
                entity_id=entity_id,
                entity_type=entity_type,
                error=str(exception)
            ))
    
    async def _send_error_notification(
        self,
        user_id: int,
        job_id: str,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        error: str = "Unknown error"
    ):
        """
        Send error notification
        
        Args:
            user_id: User ID
            job_id: Job ID
            entity_id: Optional entity ID
            entity_type: Optional entity type
            error: Error message
        """
        try:
            # Get database session
            from app.db.session import SessionLocal
            db = SessionLocal()
            
            try:
                # Send notification
                await notification_service.create_notification(
                    notification={
                        "user_id": user_id,
                        "title": "Scheduled Task Failed",
                        "message": f"Error executing job {job_id}: {error}",
                        "notification_type": "error",
                        "entity_type": entity_type,
                        "entity_id": entity_id
                    },
                    db=db
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error sending error notification: {e}", exc_info=True)

# Initialize scheduler service
scheduler_service = SchedulerService()

# Start scheduler on application startup
def start_scheduler():
    scheduler_service.start()

# Shutdown scheduler on application shutdown
def shutdown_scheduler():
    scheduler_service.shutdown()

# Son güncelleme: 2025-05-21 06:54:19
# Güncelleyen: Teeksss