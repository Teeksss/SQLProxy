"""
Audit Schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
audit log data.

Last updated: 2025-05-21 07:07:17
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AuditLogBase(BaseModel):
    """Base audit log schema"""
    event_type: str = Field(..., description="Event type (security, data, system)")
    resource_type: str = Field(..., description="Resource type (query, server, user, powerbi)")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    action: str = Field(..., description="Action (create, update, delete, access, etc.)")
    user_id: Optional[int] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    client_ip: Optional[str] = Field(None, description="Client IP address")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    status: str = Field(..., description="Status (success, failure, error)")

class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log"""
    pass

class AuditLogResponse(AuditLogBase):
    """Schema for audit log response"""
    id: str = Field(..., description="Audit log ID")
    timestamp: datetime = Field(..., description="Event timestamp")
    
    class Config:
        orm_mode = True

class AuditLogListResponse(BaseModel):
    """Schema for listing audit logs"""
    items: List[AuditLogResponse] = Field(..., description="Audit logs")
    total: int = Field(..., description="Total number of logs matching filters")

class AuditSummaryResponse(BaseModel):
    """Schema for audit summary"""
    total_events: int = Field(..., description="Total events in the period")
    event_types: Dict[str, int] = Field(..., description="Event counts by type")
    statuses: Dict[str, int] = Field(..., description="Event counts by status")
    active_users: Dict[str, int] = Field(..., description="Most active users")
    days: int = Field(..., description="Number of days in the summary")

# Son güncelleme: 2025-05-21 07:07:17
# Güncelleyen: Teeksss