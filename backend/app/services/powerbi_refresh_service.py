"""
PowerBI Refresh Service for SQL Proxy

This module provides functionality for scheduling and managing
PowerBI dataset and report refresh operations.

Last updated: 2025-05-21 05:58:00
Updated by: Teeksss
"""

import logging
import asyncio
import datetime
from typing import Dict, List, Any, Optional, Union
import croniter
import json

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from app.db.session import get_db
from app.models.powerbi import PowerBIWorkspace, PowerBIReport, PowerBIDataset
from app.services.powerbi_service import powerbi_service
from app.core.config import settings
from app.core.scheduled_tasks import schedule_task, remove_task

logger = logging.getLogger(__name__)

class PowerBIRefreshService:
    """
    Service for managing PowerBI dataset and report refresh operations
    
    Provides functionality for scheduling and executing refresh operations
    for PowerBI datasets and reports.
    """
    
    async def refresh_dataset(
        self, 
        dataset_id: str, 
        workspace_id: Optional[str] = None,
        notify_option: str = "MailOnCompletion"
    ) -> Dict[str, Any]:
        """
        Trigger a refresh for a PowerBI dataset
        
        Args:
            dataset_id: PowerBI dataset ID
            workspace_id: Optional workspace ID
            notify_option: Notification option for refresh completion
            
        Returns:
            Refresh operation details
        """
        try:
            token = await powerbi_service.authenticate()
            
            url = f"{powerbi_service.api_url}/datasets/{dataset_id}/refreshes"
            if workspace_id:
                url = f"{powerbi_service.api_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "notifyOption": notify_option
            }
            
            import requests
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # Update dataset refresh status in database
            db = next(get_db())
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            
            if dataset:
                dataset.last_refreshed_at = datetime.datetime.utcnow()
                dataset.last_refresh_status = "In Progress"
                db.commit()
            
            return {"message": f"Refresh triggered for dataset {dataset_id}"}
            
        except Exception as e:
            logger.error(f"Error refreshing PowerBI dataset: {e}", exc_info=True)
            
            # Update dataset refresh status to failed
            try:
                db = next(get_db())
                dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
                
                if dataset:
                    dataset.last_refresh_status = f"Failed: {str(e)[:100]}"
                    db.commit()
            except:
                pass
                
            raise HTTPException(status_code=500, detail=f"Error refreshing PowerBI dataset: {str(e)}")
    
    async def get_refresh_status(
        self, 
        dataset_id: str, 
        refresh_id: str,
        workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the status of a dataset refresh operation
        
        Args:
            dataset_id: PowerBI dataset ID
            refresh_id: Refresh operation ID
            workspace_id: Optional workspace ID
            
        Returns:
            Refresh status details
        """
        try:
            token = await powerbi_service.authenticate()
            
            url = f"{powerbi_service.api_url}/datasets/{dataset_id}/refreshes/{refresh_id}"
            if workspace_id:
                url = f"{powerbi_service.api_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes/{refresh_id}"
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            import requests
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            refresh_data = response.json()
            
            # Update dataset refresh status in database
            db = next(get_db())
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            
            if dataset and refresh_data.get("status") in ["Completed", "Failed"]:
                dataset.last_refresh_status = refresh_data.get("status")
                db.commit()
            
            return refresh_data
            
        except Exception as e:
            logger.error(f"Error getting PowerBI refresh status: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting PowerBI refresh status: {str(e)}")
    
    async def get_refresh_history(
        self, 
        dataset_id: str, 
        workspace_id: Optional[str] = None,
        top: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get refresh history for a PowerBI dataset
        
        Args:
            dataset_id: PowerBI dataset ID
            workspace_id: Optional workspace ID
            top: Maximum number of history items to return
            
        Returns:
            List of refresh history items
        """
        try:
            token = await powerbi_service.authenticate()
            
            url = f"{powerbi_service.api_url}/datasets/{dataset_id}/refreshes?$top={top}"
            if workspace_id:
                url = f"{powerbi_service.api_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top={top}"
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            import requests
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            refresh_history = response.json().get("value", [])
            
            return refresh_history
            
        except Exception as e:
            logger.error(f"Error getting PowerBI refresh history: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting PowerBI refresh history: {str(e)}")
    
    async def setup_refresh_schedule(
        self, 
        dataset_id: str, 
        workspace_id: Optional[str] = None,
        schedule: str = "0 0 * * *"  # Default: daily at midnight
    ) -> Dict[str, Any]:
        """
        Set up a refresh schedule for a PowerBI dataset
        
        Args:
            dataset_id: PowerBI dataset ID
            workspace_id: Optional workspace ID
            schedule: Cron expression for refresh schedule
            
        Returns:
            Schedule setup result
        """
        try:
            # Validate cron expression
            try:
                croniter.croniter(schedule, datetime.datetime.utcnow())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid cron expression for schedule")
            
            # Get dataset details
            db = next(get_db())
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            
            if not dataset:
                # Create dataset record if it doesn't exist
                dataset_details = await powerbi_service.get_dataset(dataset_id, workspace_id)
                dataset = PowerBIDataset(
                    dataset_id=dataset_id,
                    name=dataset_details.get("name", "Unknown Dataset"),
                    workspace_id=workspace_id,
                    refresh_schedule=schedule
                )
                db.add(dataset)
            else:
                # Update existing dataset record
                dataset.refresh_schedule = schedule
            
            db.commit()
            
            # Remove existing schedule if any
            task_id = f"dataset_refresh_{dataset_id}"
            remove_task(task_id)
            
            # Set up new schedule
            from app.core.scheduled_tasks import schedule_task
            
            # Function to run for the schedule
            async def refresh_dataset_task():
                try:
                    await self.refresh_dataset(dataset_id, workspace_id)
                    logger.info(f"Scheduled refresh triggered for dataset {dataset_id}")
                except Exception as e:
                    logger.error(f"Error in scheduled refresh for dataset {dataset_id}: {e}", exc_info=True)
            
            # Schedule task using cron expression
            import time
            from croniter import croniter
            
            # Parse cron expression and get next run time
            cron = croniter(schedule, datetime.datetime.utcnow())
            next_run = cron.get_next(datetime.datetime)
            
            # Schedule the task
            import asyncio
            schedule_task(
                task_id=task_id,
                task_func=lambda: asyncio.run(refresh_dataset_task()),
                run_at=f"{next_run.hour:02d}:{next_run.minute:02d}",
                run_daily="* * *" not in schedule  # If it's not a complex schedule, treat as daily
            )
            
            return {
                "message": f"Refresh schedule set up for dataset {dataset_id}",
                "schedule": schedule,
                "next_run": next_run.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error setting up refresh schedule: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error setting up refresh schedule: {str(e)}")
    
    async def cancel_refresh_schedule(
        self, 
        dataset_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a refresh schedule for a PowerBI dataset
        
        Args:
            dataset_id: PowerBI dataset ID
            
        Returns:
            Cancellation result
        """
        try:
            # Remove schedule
            task_id = f"dataset_refresh_{dataset_id}"
            removed = remove_task(task_id)
            
            if not removed:
                logger.warning(f"No refresh schedule found for dataset {dataset_id}")
            
            # Update dataset record
            db = next(get_db())
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            
            if dataset:
                dataset.refresh_schedule = None
                db.commit()
            
            return {
                "message": f"Refresh schedule cancelled for dataset {dataset_id}"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling refresh schedule: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error cancelling refresh schedule: {str(e)}")
    
    async def initialize_scheduled_refreshes(
        self,
        initial_delay: int = 60  # Wait 60 seconds after server start
    ) -> None:
        """
        Initialize all scheduled refreshes from database
        
        Args:
            initial_delay: Delay in seconds before initializing schedules
        """
        try:
            # Wait for the specified initial delay
            await asyncio.sleep(initial_delay)
            
            logger.info("Initializing scheduled PowerBI dataset refreshes...")
            
            # Get all datasets with refresh schedules
            db = next(get_db())
            datasets = db.query(PowerBIDataset).filter(PowerBIDataset.refresh_schedule.isnot(None)).all()
            
            setup_count = 0
            
            # Set up schedules for each dataset
            for dataset in datasets:
                try:
                    await self.setup_refresh_schedule(
                        dataset_id=dataset.dataset_id,
                        workspace_id=dataset.workspace_id,
                        schedule=dataset.refresh_schedule
                    )
                    setup_count += 1
                except Exception as e:
                    logger.error(f"Error setting up refresh schedule for dataset {dataset.dataset_id}: {e}", exc_info=True)
            
            logger.info(f"Initialized {setup_count}/{len(datasets)} scheduled PowerBI dataset refreshes")
            
        except Exception as e:
            logger.error(f"Error initializing scheduled refreshes: {e}", exc_info=True)

# Initialize PowerBI refresh service
powerbi_refresh_service = PowerBIRefreshService()

# Initialize scheduled refreshes in background (needs to be done after server start)
async def initialize_powerbi_refreshes():
    # Run with a delay to ensure services are ready
    asyncio.create_task(powerbi_refresh_service.initialize_scheduled_refreshes())

# Son güncelleme: 2025-05-21 05:58:00
# Güncelleyen: Teeksss