"""
Dashboard Schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
dashboard data.

Last updated: 2025-05-21 06:42:20
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DashboardWidget(BaseModel):
    """Dashboard widget schema"""
    id: str = Field(..., description="Widget ID")
    type: str = Field(..., description="Widget type")
    title: str = Field(..., description="Widget title")
    size: str = Field("medium", description="Widget size (small, medium, large)")
    position: int = Field(..., description="Widget position")
    config: dict = Field(default_factory=dict, description="Widget configuration")

class DashboardConfig(BaseModel):
    """Dashboard configuration schema"""
    widgets: List[DashboardWidget] = Field(default_factory=list, description="Dashboard widgets")

class DashboardBase(BaseModel):
    """Base dashboard schema"""
    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    is_default: bool = Field(False, description="Whether this is the default dashboard")
    config: Dict[str, Any] = Field(default_factory=lambda: {"widgets": []}, description="Dashboard configuration")

class DashboardCreate(DashboardBase):
    """Schema for creating a dashboard"""
    pass

class DashboardUpdate(BaseModel):
    """Schema for updating a dashboard"""
    name: Optional[str] = Field(None, description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    is_default: Optional[bool] = Field(None, description="Whether this is the default dashboard")
    config: Optional[Dict[str, Any]] = Field(None, description="Dashboard configuration")

class DashboardResponse(DashboardBase):
    """Schema for dashboard response"""
    id: str = Field(..., description="Dashboard ID")
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation datetime")
    updated_at: Optional[datetime] = Field(None, description="Update datetime")
    
    class Config:
        orm_mode = True

class DashboardsResponse(BaseModel):
    """Schema for listing dashboards"""
    items: List[DashboardResponse] = Field(..., description="Dashboards")
    total: int = Field(..., description="Total number of dashboards")

# Son güncelleme: 2025-05-21 06:42:20
# Güncelleyen: Teeksss