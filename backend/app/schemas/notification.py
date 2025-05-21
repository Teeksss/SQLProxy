"""
Notification Schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
notification data.

Last updated: 2025-05-21 06:32:20
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class NotificationBase(BaseModel):
    """Base notification schema"""
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    notification_type: str = Field(..., description="Type of notification")
    entity_type: Optional[str] = Field(None, description="Type of related entity")
    entity_id: Optional[str] = Field(None, description="ID of related entity")

class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    user_id: int = Field(..., description="User ID")

class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""
    is_read: Optional[bool] = Field(None, description="Whether the notification has been read")

class NotificationResponse(NotificationBase):
    """Schema for notification response"""
    id: int = Field(..., description="Notification ID")
    user_id: int = Field(..., description="User ID")
    is_read: bool = Field(..., description="Whether the notification has been read")
    created_at: datetime = Field(..., description="Creation datetime")
    read_at: Optional[datetime] = Field(None, description="Read datetime")
    
    class Config:
        orm_mode = True

class NotificationsResponse(BaseModel):
    """Schema for listing notifications"""
    items: List[NotificationResponse] = Field(..., description="Notifications")
    total: int = Field(..., description="Total number of notifications")
    unread_count: int = Field(..., description="Number of unread notifications")

class NotificationPreferences(BaseModel):
    """Schema for notification preferences"""
    email_notifications: bool = Field(True, description="Whether to receive email notifications")
    powerbi_refresh_notifications: bool = Field(True, description="PowerBI refresh notifications")
    query_complete_notifications: bool = Field(True, description="Query completion notifications")
    system_notifications: bool = Field(True, description="System notifications")

# Son güncelleme: 2025-05-21 06:32:20
# Güncelleyen: Teeksss