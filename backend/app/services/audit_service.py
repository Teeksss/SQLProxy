"""
Audit Service for SQL Proxy

This module provides functionality for auditing system events and user actions.

Last updated: 2025-05-21 06:54:19
Updated by: Teeksss
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
import uuid

from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db
from app.models.user import User
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    """
    Service for auditing events and actions
    
    Provides functionality for recording and retrieving audit events
    for system monitoring and compliance purposes.
    """
    
    def __init__(self):
        """Initialize audit service"""
        pass
    
    async def log_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        action: str = 'access',
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        client_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        db: Session = None
    ) -> Optional[AuditLog]:
        """
        Log an audit event
        
        Args:
            event_type: Event type (e.g., 'security', 'data', 'system')
            resource_type: Resource type (e.g., 'query', 'server', 'powerbi')
            resource_id: Optional resource ID
            action: Action performed (e.g., 'create', 'update', 'delete', 'access')
            user_id: Optional user ID
            username: Optional username (used if user_id not provided)
            client_ip: Optional client IP address
            details: Optional additional details
            status: Event status ('success', 'failure', 'error')
            db: Database session
            
        Returns:
            Created audit log or None if not created
        """
        # Skip if no database session provided
        if not db:
            return None
        
        try:
            # Create audit log
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                user_id=user_id,
                username=username,
                client_ip=client_ip,
                details=details,
                status=status,
                timestamp=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            return audit_log
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging audit event: {e}", exc_info=True)
            return None
    
    async def log_query_execution(
        self,
        server_id: str,
        sql_text: str,
        user_id: int,
        client_ip: Optional[str] = None,
        status: str = 'success',
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
        row_count: Optional[int] = None,
        db: Session = None
    ) -> Optional[AuditLog]:
        """
        Log SQL query execution
        
        Args:
            server_id: Server ID
            sql_text: SQL query text
            user_id: User ID
            client_ip: Optional client IP address
            status: Execution status ('success', 'failure', 'error')
            error: Optional error message
            execution_time: Optional execution time in seconds
            row_count: Optional number of rows returned/affected
            db: Database session
            
        Returns:
            Created audit log or None if not created
        """
        # Skip if no database session provided
        if not db:
            return None
        
        # Create details
        details = {
            "sql_text": sql_text[:1000],  # Limit length
            "server_id": server_id
        }
        
        if error:
            details["error"] = error
        
        if execution_time is not None:
            details["execution_time"] = execution_time
        
        if row_count is not None:
            details["row_count"] = row_count
        
        # Log event
        return await self.log_event(
            event_type='data',
            resource_type='query',
            action='execute',
            user_id=user_id,
            client_ip=client_ip,
            details=details,
            status=status,
            db=db
        )
    
    async def log_server_access(
        self,
        server_id: str,
        user_id: int,
        action: str = 'connect',
        client_ip: Optional[str] = None,
        status: str = 'success',
        error: Optional[str] = None,
        db: Session = None
    ) -> Optional[AuditLog]:
        """
        Log server access
        
        Args:
            server_id: Server ID
            user_id: User ID
            action: Action ('connect', 'disconnect', 'test')
            client_ip: Optional client IP address
            status: Access status ('success', 'failure', 'error')
            error: Optional error message
            db: Database session
            
        Returns:
            Created audit log or None if not created
        """
        # Skip if no database session provided
        if not db:
            return None
        
        # Create details
        details = {
            "server_id": server_id
        }
        
        if error:
            details["error"] = error
        
        # Log event
        return await self.log_event(
            event_type='security',
            resource_type='server',
            resource_id=server_id,
            action=action,
            user_id=user_id,
            client_ip=client_ip,
            details=details,
            status=status,
            db=db
        )
    
    async def log_powerbi_action(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: int,
        workspace_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        status: str = 'success',
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Optional[AuditLog]:
        """
        Log PowerBI action
        
        Args:
            action: Action performed
            entity_type: Entity type (report, dataset, etc.)
            entity_id: Entity ID
            user_id: User ID
            workspace_id: Optional workspace ID
            client_ip: Optional client IP address
            status: Action status ('success', 'failure', 'error')
            error: Optional error message
            details: Optional additional details
            db: Database session
            
        Returns:
            Created audit log or None if not created
        """
        # Skip if no database session provided
        if not db:
            return None
        
        # Create details
        audit_details = details or {}
        audit_details["entity_type"] = entity_type
        audit_details["entity_id"] = entity_id
        
        if workspace_id:
            audit_details["workspace_id"] = workspace_id
        
        if error:
            audit_details["error"] = error
        
        # Log event
        return await self.log_event(
            event_type='data',
            resource_type='powerbi',
            resource_id=entity_id,
            action=action,
            user_id=user_id,
            client_ip=client_ip,
            details=audit_details,
            status=status,
            db=db
        )
    
    async def log_user_action(
        self,
        action: str,
        user_id: int,
        target_user_id: Optional[int] = None,
        client_ip: Optional[str] = None,
        status: str = 'success',
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Optional[AuditLog]:
        """
        Log user action
        
        Args:
            action: Action performed (login, logout, create, update, etc.)
            user_id: User ID
            target_user_id: Optional target user ID (for admin actions)
            client_ip: Optional client IP address
            status: Action status ('success', 'failure', 'error')
            error: Optional error message
            details: Optional additional details
            db: Database session
            
        Returns:
            Created audit log or None if not created
        """
        # Skip if no database session provided
        if not db:
            return None
        
        # Create details
        audit_details = details or {}
        
        if target_user_id:
            audit_details["target_user_id"] = target_user_id
        
        if error:
            audit_details["error"] = error
        
        # Log event
        return await self.log_event(
            event_type='security',
            resource_type='user',
            resource_id=str(target_user_id or user_id),
            action=action,
            user_id=user_id,
            client_ip=client_ip,
            details=audit_details,
            status=status,
            db=db
        )
    
    async def get_audit_logs(
        self,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        db: Session = None
    ) -> List[AuditLog]:
        """
        Get audit logs with filtering
        
        Args:
            event_type: Optional event type filter
            resource_type: Optional resource type filter
            resource_id: Optional resource ID filter
            action: Optional action filter
            user_id: Optional user ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            status: Optional status filter
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            db: Database session
            
        Returns:
            List of audit logs
        """
        # Skip if no database session provided
        if not db:
            return []
        
        try:
            # Build query
            query = db.query(AuditLog)
            
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            if resource_id:
                query = query.filter(AuditLog.resource_id == resource_id)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            if status:
                query = query.filter(AuditLog.status == status)
            
            # Order by timestamp (newest first)
            query = query.order_by(AuditLog.timestamp.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            return query.all()
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}", exc_info=True)
            return []
    
    async def get_audit_summary(
        self,
        days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get audit log summary
        
        Args:
            days: Number of days to include in summary
            db: Database session
            
        Returns:
            Audit summary
        """
        # Skip if no database session provided
        if not db:
            return {}
        
        try:
            # Calculate start date
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query for total count
            total_query = db.query(AuditLog).filter(AuditLog.timestamp >= start_date)
            total_count = total_query.count()
            
            # Get counts by event type
            event_type_counts = {}
            for event_type in ['security', 'data', 'system']:
                count = db.query(AuditLog).filter(
                    AuditLog.timestamp >= start_date,
                    AuditLog.event_type == event_type
                ).count()
                event_type_counts[event_type] = count
            
            # Get counts by status
            status_counts = {}
            for status in ['success', 'failure', 'error']:
                count = db.query(AuditLog).filter(
                    AuditLog.timestamp >= start_date,
                    AuditLog.status == status
                ).count()
                status_counts[status] = count
            
            # Get most active users
            user_counts = {}
            user_query = db.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.timestamp >= start_date,
                AuditLog.user_id != None
            ).group_by(
                AuditLog.user_id
            ).order_by(
                func.count(AuditLog.id).desc()
            ).limit(10)
            
            for user_id, count in user_query:
                user_counts[str(user_id)] = count
            
            # Return summary
            return {
                "total_events": total_count,
                "event_types": event_type_counts,
                "statuses": status_counts,
                "active_users": user_counts,
                "days": days
            }
        except Exception as e:
            logger.error(f"Error getting audit summary: {e}", exc_info=True)
            return {
                "error": str(e)
            }

# Initialize audit service
audit_service = AuditService()

# Son güncelleme: 2025-05-21 06:54:19
# Güncelleyen: Teeksss