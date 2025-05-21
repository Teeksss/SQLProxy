"""
Notification API endpoints for SQL Proxy

This module provides API endpoints for managing user notifications.

Last updated: 2025-05-21 06:38:34
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationsResponse,
    NotificationPreferences
)
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=NotificationsResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    skip: int = Query(0, description="Number of notifications to skip"),
    limit: int = Query(100, description="Maximum number of notifications to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user notifications
    
    Args:
        unread_only: Whether to return only unread notifications
        skip: Number of items to skip (pagination)
        limit: Maximum number of items to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of notifications
    """
    try:
        # Get notifications
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            db=db
        )
        
        # Count total unread notifications
        unread_query = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        unread_count = unread_query.count()
        
        # Count total notifications
        total_query = db.query(Notification).filter(Notification.user_id == current_user.id)
        if unread_only:
            total_query = total_query.filter(Notification.is_read == False)
        
        total_count = total_query.count()
        
        return {
            "items": notifications,
            "total": total_count,
            "unread_count": unread_count
        }
    except Exception as e:
        logger.error(f"Error getting notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting notifications: {str(e)}")

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int = Path(..., description="Notification ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Mark a notification as read
    
    Args:
        notification_id: Notification ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Mark notification as read
        success = await notification_service.mark_notification_read(
            notification_id=notification_id,
            user_id=current_user.id,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")

@router.post("/read-all")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Mark all notifications as read
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Get unread notifications
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).all()
        
        # Mark all as read
        for notification in unread_notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": f"Marked {len(unread_notifications)} notifications as read"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking all notifications as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error marking all notifications as read: {str(e)}")

@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user notification preferences
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Notification preferences
    """
    try:
        # Get preferences from user settings
        preferences = current_user.settings.get('notification_preferences') if current_user.settings else None
        
        # Use default preferences if not set
        if not preferences:
            preferences = {
                "email_notifications": True,
                "powerbi_refresh_notifications": True,
                "query_complete_notifications": True,
                "system_notifications": True
            }
        
        return preferences
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting notification preferences: {str(e)}")

@router.post("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update user notification preferences
    
    Args:
        preferences: Notification preferences
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated notification preferences
    """
    try:
        # Initialize settings if not set
        if not current_user.settings:
            current_user.settings = {}
        
        # Update notification preferences
        current_user.settings['notification_preferences'] = {
            "email_notifications": preferences.email_notifications,
            "powerbi_refresh_notifications": preferences.powerbi_refresh_notifications,
            "query_complete_notifications": preferences.query_complete_notifications,
            "system_notifications": preferences.system_notifications
        }
        
        # Save to database
        db.commit()
        
        return current_user.settings['notification_preferences']
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating notification preferences: {str(e)}")

@router.post("/create", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new notification (admin only)
    
    Args:
        notification: Notification data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created notification
    """
    try:
        # Check if user is admin or creating for self
        if not current_user.is_admin and notification.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only admins can create notifications for other users")
        
        # Create notification
        new_notification = await notification_service.create_notification(notification, db)
        
        return new_notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int = Path(..., description="Notification ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a notification
    
    Args:
        notification_id: Notification ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Get notification
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Delete notification
        db.delete(notification)
        db.commit()
        
        return {"message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting notification: {str(e)}")

# Son güncelleme: 2025-05-21 06:38:34
# Güncelleyen: Teeksss