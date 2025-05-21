"""
PowerBI Data API endpoints for SQL Proxy

This module provides API endpoints for managing PowerBI datasets,
refreshes, and data operations.

Last updated: 2025-05-21 05:58:00
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_admin, get_db
from app.models.user import User
from app.models.powerbi import PowerBIWorkspace, PowerBIReport, PowerBIDataset
from app.schemas.powerbi import (
    PowerBIDatasetCreate,
    PowerBIDatasetResponse,
    PowerBIDatasetsResponse
)
from app.services.powerbi_service import powerbi_service
from app.services.powerbi_refresh_service import powerbi_refresh_service
from app.services.query_executor import query_executor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/datasets", response_model=PowerBIDatasetsResponse)
async def list_datasets(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List PowerBI datasets
    
    Args:
        workspace_id: Optional workspace ID filter
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of datasets
    """
    try:
        # Get datasets from database
        query = db.query(PowerBIDataset)
        
        # Apply filters
        if workspace_id:
            query = query.filter(PowerBIDataset.workspace_id == workspace_id)
        
        datasets = query.all()
        
        return {
            "items": datasets,
            "total": len(datasets)
        }
    except Exception as e:
        logger.error(f"Error listing PowerBI datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing PowerBI datasets: {str(e)}")

@router.get("/datasets/{dataset_id}", response_model=PowerBIDatasetResponse)
async def get_dataset(
    dataset_id: str = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get PowerBI dataset details
    
    Args:
        dataset_id: Dataset ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dataset details
    """
    try:
        # Get dataset from database
        dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
        
        if not dataset:
            # Try to get from PowerBI service
            try:
                dataset_details = await powerbi_service.get_dataset(dataset_id)
                
                # Create dataset record
                dataset = PowerBIDataset(
                    dataset_id=dataset_id,
                    name=dataset_details.get("name", "Unknown Dataset"),
                    created_by_id=current_user.id
                )
                
                db.add(dataset)
                db.commit()
                db.refresh(dataset)
            except:
                raise HTTPException(status_code=404, detail=f"PowerBI dataset {dataset_id} not found")
        
        return dataset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PowerBI dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting PowerBI dataset: {str(e)}")

@router.post("/datasets", response_model=PowerBIDatasetResponse)
async def create_dataset(
    dataset: PowerBIDatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new PowerBI dataset
    
    Args:
        dataset: Dataset creation parameters
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created dataset
    """
    try:
        # Create dataset in PowerBI
        created_dataset = await powerbi_service.create_push_dataset(
            dataset=dataset,
            workspace_id=dataset.workspace_id
        )
        
        # Save to database
        new_dataset = PowerBIDataset(
            dataset_id=created_dataset.get("id"),
            name=dataset.name,
            description=dataset.description,
            workspace_id=dataset.workspace_id,
            created_by_id=current_user.id
        )
        
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
        
        return new_dataset
    except Exception as e:
        logger.error(f"Error creating PowerBI dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating PowerBI dataset: {str(e)}")

@router.post("/datasets/{dataset_id}/refresh")
async def refresh_dataset(
    dataset_id: str = Path(..., description="Dataset ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    notify_option: str = Query("MailOnCompletion", description="Notification option"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh a PowerBI dataset
    
    Args:
        dataset_id: Dataset ID
        workspace_id: Optional workspace ID
        notify_option: Notification option
        background_tasks: Background tasks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Refresh operation result
    """
    try:
        # Get dataset from database to get workspace ID if not provided
        if not workspace_id:
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            if dataset:
                workspace_id = dataset.workspace_id
        
        # Trigger refresh in background to avoid timeout
        if background_tasks:
            background_tasks.add_task(
                powerbi_refresh_service.refresh_dataset,
                dataset_id=dataset_id,
                workspace_id=workspace_id,
                notify_option=notify_option
            )
            
            return {"message": f"Refresh for dataset {dataset_id} has been scheduled"}
        else:
            # Trigger refresh immediately
            return await powerbi_refresh_service.refresh_dataset(
                dataset_id=dataset_id,
                workspace_id=workspace_id,
                notify_option=notify_option
            )
    except Exception as e:
        logger.error(f"Error refreshing PowerBI dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error refreshing PowerBI dataset: {str(e)}")

@router.get("/datasets/{dataset_id}/refresh-history")
async def get_refresh_history(
    dataset_id: str = Path(..., description="Dataset ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    top: int = Query(10, description="Maximum number of history items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get refresh history for a PowerBI dataset
    
    Args:
        dataset_id: Dataset ID
        workspace_id: Optional workspace ID
        top: Maximum number of history items to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Refresh history
    """
    try:
        # Get dataset from database to get workspace ID if not provided
        if not workspace_id:
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            if dataset:
                workspace_id = dataset.workspace_id
        
        # Get refresh history
        history = await powerbi_refresh_service.get_refresh_history(
            dataset_id=dataset_id,
            workspace_id=workspace_id,
            top=top
        )
        
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting PowerBI refresh history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting PowerBI refresh history: {str(e)}")

@router.post("/datasets/{dataset_id}/schedule")
async def setup_refresh_schedule(
    dataset_id: str = Path(..., description="Dataset ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    schedule: str = Query(..., description="Cron expression for refresh schedule"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set up a refresh schedule for a PowerBI dataset
    
    Args:
        dataset_id: Dataset ID
        workspace_id: Optional workspace ID
        schedule: Cron expression for refresh schedule
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Schedule setup result
    """
    try:
        # Get dataset from database to get workspace ID if not provided
        if not workspace_id:
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            if dataset:
                workspace_id = dataset.workspace_id
        
        # Set up refresh schedule
        return await powerbi_refresh_service.setup_refresh_schedule(
            dataset_id=dataset_id,
            workspace_id=workspace_id,
            schedule=schedule
        )
    except Exception as e:
        logger.error(f"Error setting up PowerBI refresh schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error setting up PowerBI refresh schedule: {str(e)}")

@router.delete("/datasets/{dataset_id}/schedule")
async def cancel_refresh_schedule(
    dataset_id: str = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel a refresh schedule for a PowerBI dataset
    
    Args:
        dataset_id: Dataset ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Cancellation result
    """
    try:
        # Cancel refresh schedule
        return await powerbi_refresh_service.cancel_refresh_schedule(
            dataset_id=dataset_id
        )
    except Exception as e:
        logger.error(f"Error cancelling PowerBI refresh schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error cancelling PowerBI refresh schedule: {str(e)}")

@router.post("/datasets/{dataset_id}/push-data")
async def push_data_to_dataset(
    dataset_id: str = Path(..., description="Dataset ID"),
    table_name: str = Query(..., description="Table name"),
    data: List[Dict[str, Any]] = None,
    query_id: Optional[str] = Query(None, description="Saved query ID"),
    query_text: Optional[str] = Query(None, description="SQL query text"),
    server_id: Optional[str] = Query(None, description="Database server ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Push data to a PowerBI dataset table
    
    Args:
        dataset_id: Dataset ID
        table_name: Table name
        data: Data rows to push
        query_id: Optional saved query ID
        query_text: Optional SQL query text
        server_id: Optional database server ID
        workspace_id: Optional workspace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Push operation result
    """
    try:
        # Get dataset from database to get workspace ID if not provided
        if not workspace_id:
            dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
            if dataset:
                workspace_id = dataset.workspace_id
        
        # Check if we have data or query information
        if not data and not (query_id or (query_text and server_id)):
            raise HTTPException(status_code=400, detail="Either data, query_id, or query_text with server_id must be provided")
        
        # If we have query information, execute the query to get data
        if not data:
            if query_id:
                # Execute saved query
                query_results = await query_executor.execute_saved_query(query_id, server_id, current_user, db)
            else:
                # Execute ad-hoc query
                query_results = await query_executor.execute_query(query_text, server_id, current_user, db)
            
            # Convert query results to PowerBI format
            data = []
            if query_results.get('columns') and query_results.get('data'):
                columns = query_results['columns']
                rows = query_results['data']
                
                for row in rows:
                    row_data = {}
                    for i, col in enumerate(columns):
                        if i < len(row):
                            # Handle date/time values
                            if isinstance(row[i], (datetime.datetime, datetime.date)):
                                row_data[col] = row[i].isoformat()
                            else:
                                row_data[col] = row[i]
                    data.append(row_data)
        
        # Push data to PowerBI
        await powerbi_service.push_rows(
            dataset_id=dataset_id,
            table_name=table_name,
            rows=data,
            workspace_id=workspace_id
        )
        
        return {
            "message": f"Successfully pushed {len(data)} rows to dataset {dataset_id}, table {table_name}"
        }
    except Exception as e:
        logger.error(f"Error pushing data to PowerBI dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error pushing data to PowerBI dataset: {str(e)}")

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str = Path(..., description="Dataset ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a PowerBI dataset
    
    Args:
        dataset_id: Dataset ID
        workspace_id: Optional workspace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion result
    """
    try:
        # Get dataset from database
        dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
        
        if dataset:
            workspace_id = workspace_id or dataset.workspace_id
            
            # Cancel any existing refresh schedule
            try:
                await powerbi_refresh_service.cancel_refresh_schedule(dataset_id)
            except:
                pass
            
            # Delete from PowerBI
            try:
                await powerbi_service.delete_dataset(dataset_id, workspace_id)
            except:
                logger.warning(f"Failed to delete dataset {dataset_id} from PowerBI service")
            
            # Delete from database
            db.delete(dataset)
            db.commit()
        
        return {"message": f"Dataset {dataset_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting PowerBI dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting PowerBI dataset: {str(e)}")

# Son güncelleme: 2025-05-21 05:58:00
# Güncelleyen: Teeksss