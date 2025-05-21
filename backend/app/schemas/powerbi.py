"""
PowerBI Schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
PowerBI integration data.

Last updated: 2025-05-21 05:44:49
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Input schemas

class PowerBICredentials(BaseModel):
    """PowerBI credentials for authentication"""
    tenant_id: str = Field(..., description="Azure tenant ID")
    client_id: str = Field(..., description="Azure client (application) ID")
    client_secret: str = Field(..., description="Azure client secret")

class PowerBITableColumn(BaseModel):
    """Column definition for PowerBI table"""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Column data type (e.g., String, Int64, Double, DateTime, Boolean)")

class PowerBITable(BaseModel):
    """Table definition for PowerBI dataset"""
    name: str = Field(..., description="Table name")
    columns: List[PowerBITableColumn] = Field(default_factory=list, description="Table columns")

class PowerBIDatasetCreate(BaseModel):
    """Schema for creating a PowerBI dataset"""
    name: str = Field(..., description="Dataset name")
    default_mode: str = Field("Push", description="Dataset mode (Push, Streaming, PushStreaming)")
    tables: List[PowerBITable] = Field(default_factory=list, description="Dataset tables")

class PowerBIReportCreate(BaseModel):
    """Schema for creating a PowerBI report"""
    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    workspace_id: Optional[str] = Field(None, description="PowerBI workspace ID (if None, uses 'My Workspace')")
    refresh_schedule: Optional[str] = Field(None, description="Refresh schedule (cron expression)")

class PowerBIWorkspaceCreate(BaseModel):
    """Schema for creating a PowerBI workspace"""
    name: str = Field(..., description="Workspace name")
    description: Optional[str] = Field(None, description="Workspace description")

# Response schemas

class PowerBIEmbedToken(BaseModel):
    """PowerBI embed token for report embedding"""
    token: str = Field(..., description="Embed token")
    token_id: str = Field(..., description="Token ID")
    expiration: str = Field(..., description="Token expiration datetime")
    embed_url: str = Field(..., description="Report embed URL")

class PowerBIWorkspaceResponse(BaseModel):
    """Schema for PowerBI workspace response"""
    id: int = Field(..., description="Database record ID")
    workspace_id: str = Field(..., description="PowerBI workspace ID")
    name: str = Field(..., description="Workspace name")
    description: Optional[str] = Field(None, description="Workspace description")
    is_active: bool = Field(..., description="Whether the workspace is active")
    created_at: datetime = Field(..., description="Creation datetime")
    updated_at: Optional[datetime] = Field(None, description="Last update datetime")
    reports_count: Optional[int] = Field(None, description="Number of reports in the workspace")
    datasets_count: Optional[int] = Field(None, description="Number of datasets in the workspace")
    
    class Config:
        orm_mode = True

class PowerBIReportResponse(BaseModel):
    """Schema for PowerBI report response"""
    id: int = Field(..., description="Database record ID")
    report_id: str = Field(..., description="PowerBI report ID")
    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    embed_url: Optional[str] = Field(None, description="Report embed URL")
    dataset_id: Optional[str] = Field(None, description="Associated dataset ID")
    workspace_id: Optional[str] = Field(None, description="PowerBI workspace ID")
    created_at: datetime = Field(..., description="Creation datetime")
    updated_at: Optional[datetime] = Field(None, description="Last update datetime")
    refresh_schedule: Optional[str] = Field(None, description="Refresh schedule (cron expression)")
    last_refreshed_at: Optional[datetime] = Field(None, description="Last refresh datetime")
    last_refresh_status: Optional[str] = Field(None, description="Last refresh status")
    
    class Config:
        orm_mode = True

class PowerBIDatasetResponse(BaseModel):
    """Schema for PowerBI dataset response"""
    id: int = Field(..., description="Database record ID")
    dataset_id: str = Field(..., description="PowerBI dataset ID")
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    workspace_id: Optional[str] = Field(None, description="PowerBI workspace ID")
    created_at: datetime = Field(..., description="Creation datetime")
    updated_at: Optional[datetime] = Field(None, description="Last update datetime")
    refresh_schedule: Optional[str] = Field(None, description="Refresh schedule (cron expression)")
    last_refreshed_at: Optional[datetime] = Field(None, description="Last refresh datetime")
    last_refresh_status: Optional[str] = Field(None, description="Last refresh status")
    
    class Config:
        orm_mode = True

class PowerBIWorkspacesResponse(BaseModel):
    """Schema for listing PowerBI workspaces"""
    items: List[PowerBIWorkspaceResponse] = Field(..., description="Workspaces")
    total: int = Field(..., description="Total number of workspaces")

class PowerBIReportsResponse(BaseModel):
    """Schema for listing PowerBI reports"""
    items: List[PowerBIReportResponse] = Field(..., description="Reports")
    total: int = Field(..., description="Total number of reports")

class PowerBIDatasetsResponse(BaseModel):
    """Schema for listing PowerBI datasets"""
    items: List[PowerBIDatasetResponse] = Field(..., description="Datasets")
    total: int = Field(..., description="Total number of datasets")

# Son güncelleme: 2025-05-21 05:44:49
# Güncelleyen: Teeksss