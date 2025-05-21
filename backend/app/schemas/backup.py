"""
Backup schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
backup data.

Last updated: 2025-05-21 05:21:55
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.backup import BackupStatus, BackupType

class BackupCreate(BaseModel):
    """Schema for creating a backup"""
    backup_type: BackupType = Field(BackupType.FULL, description="Type of backup (FULL or INCREMENTAL)")
    description: str = Field("Automated backup", description="Backup description")
    include_queries: bool = Field(True, description="Whether to include saved queries")

class BackupBase(BaseModel):
    """Base backup schema"""
    backup_id: str = Field(..., description="Unique backup identifier")
    filename: str = Field(..., description="Backup filename")
    backup_type: str = Field(..., description="Type of backup")
    description: str = Field(..., description="Backup description")
    size_bytes: int = Field(..., description="Backup size in bytes")
    storage_type: str = Field(..., description="Storage type (local, s3, gcs, azure)")
    status: str = Field(..., description="Backup status")
    created_at: datetime = Field(..., description="When the backup was created")

    class Config:
        orm_mode = True

class BackupResponse(BaseModel):
    """Schema for backup response"""
    message: str = Field(..., description="Response message")
    backup_type: str = Field(..., description="Type of backup")
    description: str = Field(..., description="Backup description")
    status: str = Field(..., description="Backup status")

class BackupDetailResponse(BackupBase):
    """Schema for detailed backup response"""
    storage_path: str = Field(..., description="Storage path")
    metadata: Dict[str, Any] = Field({}, description="Backup metadata")

class BackupListResponse(BaseModel):
    """Schema for backup list response"""
    items: List[BackupBase] = Field(..., description="List of backups")
    total: int = Field(..., description="Total number of backups")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")

# Son güncelleme: 2025-05-21 05:21:55
# Güncelleyen: Teeksss