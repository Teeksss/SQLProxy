"""
Notification Service for SQL Proxy

This module provides functionality for sending notifications to users
about various events and operations in the system.

Last updated: 2025-05-21 06:32:20
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationResponse

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending and managing notifications
    
    Provides functionality for sending email notifications, in-app notifications,
    and tracking notification status.
    """
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        sender: Optional[str] = None
    ) -> bool:
        """
        Send email notification
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            body_html: HTML content of the email
            body_text: Plain text content of the email (optional)
            sender: Email sender (optional, uses default if not provided)
            
        Returns:
            Success status
        """
        try:
            if not settings.SMTP_HOST or not settings.SMTP_PORT:
                logger.warning("SMTP not configured, email notification skipped")
                return False
            
            # Set default sender if not provided
            sender = sender or settings.SMTP_SENDER
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = sender
            message['To'] = ', '.join(recipients)
            
            # Add plain text body if provided
            if body_text:
                message.attach(MIMEText(body_text, 'plain'))
            
            # Add HTML body
            message.attach(MIMEText(body_html, 'html'))
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                server.send_message(message)
            
            logger.info(f"Email notification sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}", exc_info=True)
            return False
    
    async def create_notification(
        self,
        notification: NotificationCreate,
        db: Session
    ) -> NotificationResponse:
        """
        Create a new in-app notification
        
        Args:
            notification: Notification data
            db: Database session
            
        Returns:
            Created notification
        """
        try:
            # Create notification record
            from app.models.notification import Notification
            
            new_notification = Notification(
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                entity_type=notification.entity_type,
                entity_id=notification.entity_id,
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.add(new_notification)
            db.commit()
            db.refresh(new_notification)
            
            logger.info(f"Created notification for user {notification.user_id}")
            
            return NotificationResponse(
                id=new_notification.id,
                user_id=new_notification.user_id,
                title=new_notification.title,
                message=new_notification.message,
                notification_type=new_notification.notification_type,
                entity_type=new_notification.entity_type,
                entity_id=new_notification.entity_id,
                is_read=new_notification.is_read,
                created_at=new_notification.created_at
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating notification: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")
    
    async def mark_notification_read(
        self,
        notification_id: int,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
            user_id: User ID
            db: Database session
            
        Returns:
            Success status
        """
        try:
            from app.models.notification import Notification
            
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if not notification:
                logger.warning(f"Notification {notification_id} not found for user {user_id}")
                return False
            
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Marked notification {notification_id} as read")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking notification as read: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")
    
    async def get_user_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False,
        db: Session = None
    ) -> List[NotificationResponse]:
        """
        Get notifications for a user
        
        Args:
            user_id: User ID
            skip: Number of items to skip (pagination)
            limit: Maximum number of items to return
            unread_only: Whether to return only unread notifications
            db: Database session
            
        Returns:
            List of notifications
        """
        try:
            from app.models.notification import Notification
            
            query = db.query(Notification).filter(Notification.user_id == user_id)
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
            
            notifications = query.all()
            
            return [
                NotificationResponse(
                    id=notification.id,
                    user_id=notification.user_id,
                    title=notification.title,
                    message=notification.message,
                    notification_type=notification.notification_type,
                    entity_type=notification.entity_type,
                    entity_id=notification.entity_id,
                    is_read=notification.is_read,
                    created_at=notification.created_at,
                    read_at=notification.read_at
                )
                for notification in notifications
            ]
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting user notifications: {str(e)}")
    
    async def notify_refresh_complete(
        self,
        dataset_id: str,
        dataset_name: str,
        status: str,
        user_id: int,
        db: Session
    ) -> bool:
        """
        Notify user about completed dataset refresh
        
        Args:
            dataset_id: PowerBI dataset ID
            dataset_name: Dataset name
            status: Refresh status
            user_id: User ID
            db: Database session
            
        Returns:
            Success status
        """
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"User {user_id} not found, notification skipped")
                return False
            
            # Create notification
            notification = NotificationCreate(
                user_id=user_id,
                title=f"PowerBI Dataset Refresh {status.capitalize()}",
                message=f"The refresh operation for dataset '{dataset_name}' has {status.lower()}.",
                notification_type="powerbi_refresh",
                entity_type="powerbi_dataset",
                entity_id=dataset_id
            )
            
            await self.create_notification(notification, db)
            
            # Send email notification if email is available
            if user.email and settings.ENABLE_EMAIL_NOTIFICATIONS:
                status_color = "green" if status.lower() == "completed" else "red"
                html_body = f"""
                <html>
                <body>
                    <h2>PowerBI Dataset Refresh {status.capitalize()}</h2>
                    <p>Hello {user.full_name or user.username},</p>
                    <p>The refresh operation for dataset <strong>{dataset_name}</strong> has <span style="color:{status_color}">{status.lower()}</span>.</p>
                    <p>
                        <a href="{settings.FRONTEND_BASE_URL}/powerbi/datasets/{dataset_id}">View dataset</a>
                    </p>
                    <p>Thank you for using SQL Proxy!</p>
                </body>
                </html>
                """
                
                text_body = f"""
                PowerBI Dataset Refresh {status.capitalize()}
                
                Hello {user.full_name or user.username},
                
                The refresh operation for dataset '{dataset_name}' has {status.lower()}.
                
                View dataset: {settings.FRONTEND_BASE_URL}/powerbi/datasets/{dataset_id}
                
                Thank you for using SQL Proxy!
                """
                
                await self.send_email(
                    recipients=[user.email],
                    subject=f"PowerBI Dataset Refresh {status.capitalize()}: {dataset_name}",
                    body_html=html_body,
                    body_text=text_body
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending refresh notification: {e}", exc_info=True)
            return False

# Initialize notification service
notification_service = NotificationService()

# Son güncelleme: 2025-05-21 06:32:20
# Güncelleyen: Teeksss