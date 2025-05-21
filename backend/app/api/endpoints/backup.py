"""
Backup API endpoints for SQL Proxy

This module provides API endpoints for managing database backups,
including creating, listing, downloading, and restoring backups.

Last updated: 2025-05-21 05:21:55
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Path
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from datetime import datetime
import os

from app.api.deps import get_current_user, get_current_user_admin
from app.models.user import User
from app.services.backup_service import backup_service
from app.models.backup import BackupStatus, BackupType
from app.schemas.backup import (
    BackupCreate, 
    BackupResponse, 
    BackupListResponse,
    BackupDetailResponse
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=BackupResponse)
async def create_backup(
    data: BackupCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Create a new backup
    
    Args:
        data: Backup creation data
        background_tasks: Background tasks
        current_user: Current authenticated admin user
        
    Returns:
        Backup details
    """
    try:
        # Create backup in background
        background_tasks.add_task(
            backup_service.create_backup,
            backup_type=data.backup_type,
            description=data.description,
            include_queries=data.include_queries
        )
        
        # Return immediate response
        return {
            "message": "Backup started successfully",
            "backup_type": data.backup_type,
            "description": data.description,
            "status": "IN_PROGRESS"
        }
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating backup: {str(e)}")

@router.get("", response_model=BackupListResponse)
async def list_backups(
    page: int = Query(1, gt=0, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Items per page"),
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List backup records with pagination
    
    Args:
        page: Page number
        limit: Items per page
        backup_type: Filter by backup type
        current_user: Current authenticated user
        
    Returns:
        List of backup records
    """
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get backups
        backups = await backup_service.list_backups(
            limit=limit,
            offset=offset,
            backup_type=backup_type
        )
        
        # Get total count
        total_backups = len(backups)  # This should be replaced with a proper count query
        
        return {
            "items": backups,
            "total": total_backups,
            "page": page,
            "limit": limit,
            "pages": (total_backups + limit - 1) // limit  # Ceiling division
        }
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing backups: {str(e)}")

@router.get("/{backup_id}", response_model=BackupDetailResponse)
async def get_backup(
    backup_id: str = Path(..., description="Backup ID"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get backup details
    
    Args:
        backup_id: Backup ID
        current_user: Current authenticated user
        
    Returns:
        Backup details
    """
    try:
        backup = await backup_service.get_backup(backup_id)
        
        if not backup:
            raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")
        
        # Parse metadata JSON
        try:
            import json
            metadata = json.loads(backup.metadata)
        except:
            metadata = {}
        
        return {
            **backup.__dict__,
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backup {backup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting backup: {str(e)}")

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str = Path(..., description="Backup ID"),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Delete a backup
    
    Args:
        backup_id: Backup ID
        current_user: Current authenticated admin user
        
    Returns:
        Success message
    """
    try:
        deleted = await backup_service.delete_backup(backup_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")
        
        return {"message": f"Backup {backup_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup {backup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting backup: {str(e)}")

@router.post("/{backup_id}/restore")
async def restore_backup(
    backup_id: str = Path(..., description="Backup ID"),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Restore a backup
    
    Args:
        backup_id: Backup ID
        current_user: Current authenticated admin user
        
    Returns:
        Success message
    """
    try:
        # Check if backup exists
        backup = await backup_service.get_backup(backup_id)
        
        if not backup:
            raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")
        
        # Check if backup is completed
        if backup.status != BackupStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot restore backup with status {backup.status}"
            )
        
        # Restore backup
        restored = await backup_service.restore_backup(backup_id)
        
        if not restored:
            raise HTTPException(status_code=500, detail=f"Failed to restore backup {backup_id}")
        
        return {"message": f"Backup {backup_id} restored successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup {backup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error restoring backup: {str(e)}")

@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: str = Path(..., description="Backup ID"),
    current_user: User = Depends(get_current_user_admin)
):
    """
    Download a backup file
    
    Args:
        backup_id: Backup ID
        current_user: Current authenticated admin user
        
    Returns:
        Backup file as a download
    """
    try:
        # Check if backup exists
        backup = await backup_service.get_backup(backup_id)
        
        if not backup:
            raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")
        
        # Check if backup is completed
        if backup.status != BackupStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot download backup with status {backup.status}"
            )
        
        # Check if backup is stored locally
        if backup.storage_type == "local":
            backup_path = backup.storage_path
            
            if not os.path.exists(backup_path):
                raise HTTPException(status_code=404, detail=f"Backup file not found")
            
            return FileResponse(
                path=backup_path,
                filename=backup.filename,
                media_type='application/gzip'
            )
        
        # For cloud storage, we need to download to a temporary file first
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Download from cloud storage
            await backup_service._download_backup(backup, temp_path)
            
            return FileResponse(
                path=temp_path,
                filename=backup.filename,
                media_type='application/gzip',
                background=BackgroundTasks.add_task(lambda: os.unlink(temp_path))
            )
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup {backup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading backup: {str(e)}")

@router.post("/cleanup")
async def cleanup_backups(
    retention_days: Optional[int] = Query(None, description="Number of days to retain backups"),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Clean up old backups
    
    Args:
        retention_days: Number of days to retain backups
        current_user: Current authenticated admin user
        
    Returns:
        Cleanup results
    """
    try:
        deleted_count = await backup_service.cleanup_old_backups(retention_days)
        
        return {
            "message": f"Cleaned up {deleted_count} old backups",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error cleaning up backups: {str(e)}")

@router.get("/storage/info")
async def get_storage_info(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get backup storage information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Storage information
    """
    try:
        # Get backup path from settings
        backup_path = settings.BACKUP_STORAGE_PATH
        
        # Get storage type
        storage_type = settings.BACKUP_STORAGE_TYPE
        
        # Calculate local storage usage if applicable
        local_size = 0
        file_count = 0
        
        if storage_type == "local" and os.path.exists(backup_path):
            for dirpath, dirnames, filenames in os.walk(backup_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    local_size += os.path.getsize(file_path)
                    file_count += 1
        
        # Get cloud storage info
        cloud_info = {}
        if storage_type == "s3":
            cloud_info = {
                "bucket": settings.S3_BUCKET,
                "region": settings.S3_REGION
            }
        elif storage_type == "gcs":
            cloud_info = {
                "bucket": settings.GCS_BUCKET
            }
        elif storage_type == "azure":
            cloud_info = {
                "container": settings.AZURE_CONTAINER
            }
        
        return {
            "storage_type": storage_type,
            "local_path": backup_path if storage_type == "local" else None,
            "cloud_info": cloud_info if storage_type != "local" else None,
            "local_size_bytes": local_size,
            "local_size_human": f"{local_size / (1024 * 1024):.2f} MB" if local_size > 0 else "0 MB",
            "file_count": file_count,
            "retention_days": settings.BACKUP_RETENTION_DAYS
        }
    except Exception as e:
        logger.error(f"Error getting storage info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting storage info: {str(e)}")

# Son güncelleme: 2025-05-21 05:21:55
# Güncelleyen: Teeksss